#!/usr/bin/env python3
"""
CCI Intake Orchestrator — Phase 2: Profile Integration

Public API:
    class IntakeOrchestrator:
        __init__(self, payload=None, user_answers=None, active_profile=None)
        set_active_profile(active_profile) -> None
        get_status() -> dict
        next_questions(limit=None) -> list[dict]
        apply_answers(answers) -> None
        build_payload() -> dict
        run_audit() -> dict

CLI:
    python src/intake_orchestrator.py <payload.json> [answers.json]
    Prints missing required/recommended, next questions, and audit summary.
    Exit 0 on successful run.

Design choices:
    - In-memory only; no persistent sessions or SQLite.
    - Deterministic JSON-driven question generation.
    - No natural-language parsing.
    - No correction apply/capture/reuse.
    - No profile auto-activation.
    - Purely additive; does not modify existing validators, renderers, layout profiles, or examples.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on sys.path when executed as script
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from context_resolver import resolve_context
from validator_runner import run_cci_audit
from local_profile import (
    apply_profile_defaults,
    load_profile,
    validate_profile,
)
from correction_apply import get_path_value, apply_correction as apply_correction_record, undo_correction as undo_correction_record
from correction_capture import capture_correction as capture_correction_record
from correction_store import (
    save_session_correction,
    load_session_corrections,
    set_session_correction_rejected,
)
from correction_pending_log import (
    is_eligible_for_pending_log,
    propose_pending_log,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = "CCI_INTAKE_V2"

_RULES_DIR = _REPO_ROOT / "rules_v6" / "CCI"
_FIELD_POLICY_PATH = _RULES_DIR / "cci_intake_field_policy.json"
_QUESTIONS_PATH = _RULES_DIR / "cci_intake_questions.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_get(mapping: dict[str, Any], dot_path: str) -> Any:
    """Retrieve a nested value via dot-separated path; return None if absent."""
    parts = dot_path.split(".")
    current: Any = mapping
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _deep_set(mapping: dict[str, Any], dot_path: str, value: Any) -> None:
    """Set a nested value via dot-separated path, creating intermediate dicts as needed."""
    parts = dot_path.split(".")
    current = mapping
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _is_field_present(value: Any) -> bool:
    """Treat None, '', [], {} as missing. Non-empty strings, lists, dicts are present."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and not value:
        return False
    if isinstance(value, dict) and not value:
        return False
    return True


def _field_is_present_in_payload(payload: dict[str, Any], field_path: str) -> bool:
    """Check whether a field (dot path) is present and non-empty in payload (or user_answers)."""
    value = _deep_get(payload, field_path)
    return _is_field_present(value)


def _flatten_aliases(answers: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize flat dot-notation keys into nested dictionaries, but do NOT alias-map field names.
    Aliases for field names are already handled by the question registry.
    """
    result: dict[str, Any] = {}
    for key, value in answers.items():
        if "." in key:
            _deep_set(result, key, value)
        else:
            result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_profile(active_profile: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Resolve active_profile into a validated profile dict and warning list.

    Accepts:
      - None -> (None, [])
      - str -> load via local_profile.load_profile(), then validate
      - dict -> validate directly

    Returns (profile_dict_or_None, warnings).
    Load/validation errors are captured as warnings, not raised.
    """
    if active_profile is None:
        return None, []

    profile: dict[str, Any] | None = None
    warnings: list[str] = []

    if isinstance(active_profile, dict):
        profile = copy.deepcopy(active_profile)
    elif isinstance(active_profile, str):
        try:
            profile = load_profile(active_profile)
        except FileNotFoundError as exc:
            warnings.append(f"Profile load failed: {exc}")
            return None, warnings
        except Exception as exc:
            warnings.append(f"Profile load failed unexpectedly: {exc}")
            return None, warnings
    else:
        warnings.append(f"active_profile must be None, str, or dict; got {type(active_profile).__name__}")
        return None, warnings

    if profile is not None:
        errors, validate_warnings = validate_profile(profile)
        if errors:
            warnings.extend(f"Profile validation: {e}" for e in errors)
            # Return profile anyway so caller can decide; but warn
        if validate_warnings:
            warnings.extend(f"Profile validation warning: {w}" for w in validate_warnings)

    return profile, warnings


# ---------------------------------------------------------------------------
# IntakeOrchestrator
# ---------------------------------------------------------------------------

class IntakeOrchestrator:
    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        user_answers: dict[str, Any] | None = None,
        active_profile: Any = None,
        session_id: str | None = None,
    ):
        self._payload: dict[str, Any] = copy.deepcopy(payload) if payload else {}
        self._user_answers: dict[str, Any] = copy.deepcopy(user_answers if user_answers else {})
        # Normalize any flat dot-notation keys immediately into nested dict
        self._user_answers = _flatten_aliases(self._user_answers)

        self._active_profile: dict[str, Any] | None = None
        self._profile_warnings: list[str] = []
        self._merge_report: dict[str, Any] | None = None

        # Correction memory (active-draft only, in-memory)
        self._corrections_applied: list[dict] = []
        self._correction_conflicts: list[dict] = []
        self._last_audit_result: dict | None = None

        # Phase A: session correction persistence (opt-in)
        self._session_id: str | None = session_id
        self._session_notes: list[str] = []

        if active_profile is not None:
            self.set_active_profile(active_profile)

        # Pre-apply session corrections if session_id is set
        if self._session_id is not None:
            self._preapply_session_corrections()

    # -- profile management ---------------------------------------------------

    def set_active_profile(self, active_profile: Any) -> None:
        """Switch or clear the active local command profile.

        Accepts None, str (profile name/path), or dict (loaded profile).
        Revalidates profile and updates internal state.
        Does not mutate payload or user_answers.
        """
        if active_profile is None:
            self._active_profile = None
            self._profile_warnings = []
            self._merge_report = None
            return

        profile, warnings = _resolve_profile(active_profile)
        self._active_profile = profile
        self._profile_warnings = warnings
        self._merge_report = None

    def set_session_id(self, session_id: str | None) -> None:
        """Set or clear the session id for correction persistence."""
        self._session_id = session_id
        self._session_notes = []
        if session_id is not None:
            self._preapply_session_corrections()

    # -- correction memory ----------------------------------------------------

    def _preapply_session_corrections(self) -> None:
        """Pre-apply matching session corrections to the current draft payload.

        Called during __init__ if session_id is provided.
        """
        if self._session_id is None:
            return
        payload = self.build_payload()
        context, _ = resolve_context(payload, self._user_answers)
        doc_type = (context.get("document") or {}).get("doc_type")
        component = (context.get("component") or {}).get("service")

        if not doc_type or doc_type == "unknown":
            self._session_notes.append(
                "Skipping session corrections: doc_type is unknown."
            )
            return
        if not component or component == "unknown":
            self._session_notes.append(
                "Skipping session corrections: component is unknown."
            )
            return

        corrections, warnings = load_session_corrections(
            self._session_id,
            doc_type=doc_type,
            component=component,
            exclude_rejected=True,
        )
        for w in warnings:
            self._session_notes.append(f"Session correction load warning: {w}")

        # De-duplicate by field_path: use latest timestamp
        latest_by_field: dict[str, dict] = {}
        for c in corrections:
            fp = c.get("field_path", "")
            if fp in latest_by_field:
                if c.get("timestamp", "") > latest_by_field[fp].get("timestamp", ""):
                    latest_by_field[fp] = c
            else:
                latest_by_field[fp] = c

        for fp, c in latest_by_field.items():
            if self._correction_already_applied(c):
                continue
            # Skip one_time_wording unless explicitly scoped current_session
            if c.get("correction_type") == "one_time_wording" and c.get("scope") != "current_session":
                self._session_notes.append(
                    f"Skipped session correction for {fp}: one_time_wording."
                )
                continue
            payload = self.build_payload()
            new_payload, apply_warnings = apply_correction_record(payload, c)
            self._payload = new_payload
            if apply_warnings:
                c["apply_warnings"] = apply_warnings
            self._corrections_applied.append(c)
            c["applied_in_draft"] = True
            save_session_correction(self._session_id, c)
            self._session_notes.append(
                f"Applied session correction for field {fp}."
            )

    def _correction_already_applied(self, correction: dict[str, Any]) -> bool:
        """Check whether a correction (by correction_id) is already in _corrections_applied."""
        cid = correction.get("correction_id")
        if not cid:
            return False
        return any(
            c.get("correction_id") == cid for c in self._corrections_applied
        )

    def capture_correction(
        self,
        field_path: str,
        corrected_value,
        reason: str = "",
        correction_type: str = "unknown",
        source: str = "user",
    ) -> dict[str, Any]:
        """Capture a correction record for the current draft payload.  Does not apply it."""
        payload = self.build_payload()
        context, _ = resolve_context(payload, self._user_answers)
        doc_type = (context.get("document") or {}).get("doc_type")
        component = (context.get("component") or {}).get("service")
        record, warnings = capture_correction_record(
            payload,
            field_path,
            corrected_value,
            reason=reason,
            doc_type=doc_type,
            component=component,
            correction_type=correction_type,
            scope="active_draft",
            source=source,
        )
        if warnings:
            record["capture_warnings"] = warnings
        return record

    def apply_correction(self, correction: dict[str, Any]) -> dict[str, Any]:
        """Apply a correction to the current draft payload and update internal state."""
        payload = self.build_payload()
        new_payload, apply_warnings = apply_correction_record(payload, correction)
        self._payload = new_payload
        if apply_warnings:
            correction["apply_warnings"] = apply_warnings
        self._corrections_applied.append(correction)
        # Remove any active conflict that matches this correction
        cid = correction.get("correction_id")
        self._correction_conflicts = [
            c for c in self._correction_conflicts if c.get("correction_id") != cid
        ]
        return self.get_status()

    def apply_user_correction(
        self,
        field_path: str,
        corrected_value,
        reason: str = "",
        correction_type: str = "unknown",
        source: str = "user",
    ) -> dict[str, Any]:
        """Convenience: capture then apply a correction in one call."""
        correction = self.capture_correction(
            field_path, corrected_value, reason=reason, correction_type=correction_type, source=source
        )
        return self.apply_correction(correction)

    def persist_correction(self, correction: dict[str, Any]) -> bool:
        """Persist a correction to session store if session_id is set.

        Returns True if persisted. Does nothing if session_id is None.

        Phase B gates:
          - Block persistence if classification is unknown.
          - Block persistence if classification is one_time_wording unless
            user explicitly overrode (classification_confidence == user_override).
        """
        if self._session_id is None:
            return False
        correction = copy.deepcopy(correction)
        if correction.get("scope") != "current_session":
            correction["scope"] = "current_session"

        ctype = correction.get("correction_type", "unknown")
        cconf = correction.get("classification_confidence", "")

        if ctype == "unknown":
            self._session_notes.append(
                f"Skipped persistence: correction_type is 'unknown' for field {correction.get('field_path', '?')}."
            )
            return False

        if ctype == "one_time_wording" and cconf != "user_override":
            self._session_notes.append(
                f"Skipped persistence: one_time_wording requires explicit user override for field {correction.get('field_path', '?')}."
            )
            return False

        correction["session_id"] = self._session_id
        correction.setdefault("promotion_status", "none")
        save_session_correction(self._session_id, correction)
        return True

    def propose_pending_log(self, correction: dict[str, Any]) -> dict[str, Any]:
        """
        Step 1 for Phase D pending global rule candidate logging.
        Returns a proposal dict with `eligible` flag.

        Does NOT write to disk. The caller must explicitly confirm before
        calling any write operation.

        Phase D gates:
          - Only possible_secnav_manual_rule or bug_validator_gap are eligible.
          - Requires current_session scope.
          - Requires non-rejected, non-conflicted, non-placeholder value.
          - body.* paths are excluded.
        """
        if not correction:
            return {"eligible": False, "reasons": ["No correction provided"]}

        eligible, reasons = is_eligible_for_pending_log(correction)
        if not eligible:
            return {"eligible": False, "reasons": reasons}

        proposal = propose_pending_log(correction)
        return proposal

    def reject_session_correction(self, correction: dict[str, Any]) -> dict[str, Any]:
        """Undo a session correction and mark it rejected.

        Removes it from the in-memory applied list, undoes the change,
        marks user_rejected=True in the session store, and returns status.
        """
        cid = correction.get("correction_id")
        if cid:
            self._corrections_applied = [
                c for c in self._corrections_applied if c.get("correction_id") != cid
            ]
        payload = self.build_payload()
        new_payload, undo_warnings = undo_correction_record(payload, correction)
        self._payload = new_payload
        if undo_warnings:
            correction["undo_warnings"] = undo_warnings
        if self._session_id is not None and cid:
            set_session_correction_rejected(self._session_id, cid, True)
        return self.get_status()

    def undo_correction(self, correction: dict[str, Any]) -> dict[str, Any]:
        """Undo a previously-applied correction and restore the original value."""
        payload = self.build_payload()
        new_payload, undo_warnings = undo_correction_record(payload, correction)
        self._payload = new_payload
        if undo_warnings:
            correction["undo_warnings"] = undo_warnings
        cid = correction.get("correction_id")
        self._corrections_applied = [
            c for c in self._corrections_applied if c.get("correction_id") != cid
        ]
        return self.get_status()

    def rerun_audit_after_correction(self, previous_audit: dict | None = None) -> dict[str, Any]:
        """Re-run the CCI audit after corrections and compare error counts."""
        previous = previous_audit or self._last_audit_result or {}
        audit = self.run_audit()
        self._last_audit_result = audit
        prev_errors = previous.get("summary", {}).get("total_errors", 0) if isinstance(previous, dict) else 0
        new_errors = audit.get("summary", {}).get("total_errors", 0)
        if new_errors > prev_errors:
            self._correction_conflicts.append(
                {
                    "message": "Correction increased validator error count.",
                    "before_errors": prev_errors,
                    "after_errors": new_errors,
                    "correction_count": len(self._corrections_applied),
                }
            )
        return audit

    # -- public methods -------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return intake status including resolved context, audit summary, missing/question fields, and profile state."""
        payload = self.build_payload()
        context, context_warnings = resolve_context(payload, self._user_answers)
        audit = self.run_audit()
        summary = audit.get("summary", {})

        doc_type = (context.get("document") or {}).get("doc_type", "unknown")
        policy = self._load_policy_for_doc_type(doc_type)

        missing_required: list[str] = []
        missing_recommended: list[str] = []
        missing_optional: list[str] = []
        inferred: list[dict[str, Any]] = []

        for field in policy.get("required_fields", []):
            if not _field_is_present_in_payload(payload, field):
                missing_required.append(field)

        for field in policy.get("recommended_fields", []):
            if not _field_is_present_in_payload(payload, field):
                missing_recommended.append(field)

        for field in policy.get("optional_fields", []):
            if not _field_is_present_in_payload(payload, field):
                missing_optional.append(field)

        # Infer warnings describe inferred fields
        for w in context_warnings:
            inferred.append({"warning": w})

        blocking = bool(missing_required)

        # Profile state
        active_profile_id: str | None = None
        prefilled_from_profile: list[str] = []
        profile_warnings = list(self._profile_warnings)
        missing_after_profile: list[str] = []

        if self._active_profile is not None:
            active_profile_id = self._active_profile.get("profile_id")
            if self._merge_report is not None:
                prefilled_from_profile = list(self._merge_report.get("fields_from_profile", []))
                missing_after_profile = list(self._merge_report.get("fields_still_missing", []))
            else:
                # build_payload not called yet; compute from current payload
                missing_after_profile = missing_required + missing_recommended + missing_optional
        else:
            missing_after_profile = missing_required + missing_recommended + missing_optional

        return {
            "schema_version": _SCHEMA_VERSION,
            "resolved_context": context,
            "context_warnings": context_warnings,
            "audit_summary": summary,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "missing_optional": missing_optional,
            "inferred": inferred,
            "blocking": blocking,
            "correction_memory": context.get("correction_memory", {}),
            # Profile integration additions
            "active_profile": active_profile_id,
            "prefilled_from_profile": prefilled_from_profile,
            "profile_warnings": profile_warnings,
            "missing_after_profile": missing_after_profile,
            # Correction memory additions
            "corrections_applied": list(self._corrections_applied),
            "correction_conflicts": list(self._correction_conflicts),
            "correction_count": len(self._corrections_applied),
            # Phase A session correction persistence
            "session_id": self._session_id,
            "session_notes": list(self._session_notes),
        }

    def next_questions(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return prioritized missing-field questions. Required first, then recommended, then optional.

        Fields filled by profile defaults are automatically skipped because
        build_payload() merges the profile before presence checks.
        """
        status = self.get_status()
        missing_required = set(status["missing_required"])
        missing_recommended = set(status["missing_recommended"])
        missing_optional = set(status["missing_optional"])

        doc_type = (status["resolved_context"].get("document") or {}).get("doc_type", "unknown")
        component = (status["resolved_context"].get("component") or {}).get("service", "unknown")

        questions = self._load_questions()
        matched: list[dict[str, Any]] = []

        for q in questions:
            field = q["field_path"]
            # Skip if already present in the merged payload (includes profile fills)
            if _field_is_present_in_payload(self.build_payload(), field):
                continue
            # Skip if explicitly answered by user
            if _field_is_present_in_payload(self._user_answers, field):
                continue
            # Determine bucket
            if field in missing_required:
                bucket = "required"
            elif field in missing_recommended:
                bucket = "recommended"
            elif field in missing_optional:
                bucket = "optional"
            else:
                # Field not in any bucket for this doc_type; skip
                continue
            # Filter by doc_type
            applies_to = q.get("applies_to_doc_types") or []
            if applies_to and doc_type not in applies_to:
                continue
            # Filter by component
            applies_component = q.get("applies_to_component") or []
            if applies_component and component not in applies_component:
                continue
            matched.append({"bucket": bucket, **q})

        # Sort: required first, then recommended, then optional
        def sort_key(entry: tuple[int, dict[str, Any]]) -> tuple[int, int]:
            idx, q = entry
            order = {"required": 0, "recommended": 1, "optional": 2}
            return (order.get(q["bucket"], 3), idx)

        matched = [(i, q) for i, q in enumerate(matched)]
        matched.sort(key=sort_key)
        matched = [q for _, q in matched]

        if limit is not None:
            matched = matched[:limit]

        return matched

    def apply_answers(self, answers: dict[str, Any]) -> None:
        """Merge new answers into the internal user_answers dict, normalizing flat keys."""
        normalized = _flatten_aliases(answers)
        self._merge_answers(normalized, self._user_answers)

    def build_payload(self) -> dict[str, Any]:
        """Return a merged payload.

        Merge priority:
          1. explicit non-empty payload values (always win)
          2. user_answers values (fill missing)
          3. profile defaults (fill remaining missing)
          4. empty remains empty

        If no active profile, preserves legacy behavior (payload + user_answers only).
        """
        if self._active_profile is not None:
            merged, merge_report = apply_profile_defaults(
                self._payload, self._active_profile, self._user_answers
            )
            self._merge_report = merge_report
            return merged

        # Legacy path: no active profile
        merged = copy.deepcopy(self._payload)
        self._merge_answers(self._user_answers, merged, override=False)
        self._merge_report = None
        return merged

    def run_audit(self) -> dict[str, Any]:
        """Run the consolidated CCI audit against the built payload."""
        result = run_cci_audit(self.build_payload(), self._user_answers)
        self._last_audit_result = result
        return result

    # -- internal --------------------------------------------------------------

    def _merge_answers(self, src: dict[str, Any], dst: dict[str, Any], *, override: bool = True) -> None:
        """Recursively merge src into dst. If override=False, only set keys that are missing or empty in dst."""
        for key, value in src.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                self._merge_answers(value, dst[key], override=override)
            else:
                if override or not _is_field_present(dst.get(key)):
                    dst[key] = value

    def _load_policy_for_doc_type(self, doc_type: str) -> dict[str, Any]:
        data = _load_json(_FIELD_POLICY_PATH)
        return data.get("policies", {}).get(doc_type, {})

    def _load_questions(self) -> list[dict[str, Any]]:
        data = _load_json(_QUESTIONS_PATH)
        return data.get("questions", [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_status(status: dict[str, Any]) -> None:
    print("=" * 72)
    print("INTAKE ORCHESTRATOR STATUS")
    print("=" * 72)
    print()
    print(f"  Schema version : {status['schema_version']}")
    doc = status.get("resolved_context", {}).get("document", {})
    print(f"  Document type  : {doc.get('doc_type')}")
    comp = status.get("resolved_context", {}).get("component", {})
    print(f"  Service        : {comp.get('service')}")
    print()

    if status.get("active_profile"):
        print(f"  Active profile : {status['active_profile']}")
        if status.get("prefilled_from_profile"):
            print(f"  Prefilled      : {', '.join(status['prefilled_from_profile'])}")
        if status.get("profile_warnings"):
            for w in status["profile_warnings"]:
                print(f"  Profile WARN   : {w}")
        print()

    print("Missing Required Fields")
    print("-" * 72)
    if status["missing_required"]:
        for f in status["missing_required"]:
            print(f"  [REQUIRED] {f}")
    else:
        print("  (none)")
    print()

    print("Missing Recommended Fields")
    print("-" * 72)
    if status["missing_recommended"]:
        for f in status["missing_recommended"]:
            print(f"  [RECOMMENDED] {f}")
    else:
        print("  (none)")
    print()

    print("Blocking")
    print("-" * 72)
    print(f"  {status['blocking']}")
    print()

    audit = status.get("audit_summary", {})
    print("Audit Summary")
    print("-" * 72)
    print(f"  Overall pass   : {audit.get('overall_pass')}")
    print(f"  Total errors   : {audit.get('total_errors')}")
    print(f"  Total warnings : {audit.get('total_warnings')}")
    print()

    print("Next Questions")
    print("-" * 72)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python src/intake_orchestrator.py <payload.json> [answers.json]", file=sys.stderr)
        return 1

    payload_path = Path(argv[1])
    if not payload_path.exists():
        print(f"ERROR: payload not found: {payload_path}", file=sys.stderr)
        return 1

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    user_answers: dict[str, Any] = {}
    if len(argv) >= 3:
        answers_path = Path(argv[2])
        if answers_path.exists():
            user_answers = json.loads(answers_path.read_text(encoding="utf-8"))

    orchestrator = IntakeOrchestrator(payload, user_answers)
    status = orchestrator.get_status()
    _print_status(status)

    questions = orchestrator.next_questions()
    if questions:
        for q in questions:
            bucket = q["bucket"]
            print(f"  [{bucket.upper()}] {q['field_path']}")
            print(f"          {q['prompt_text']}")
    else:
        print("  (no further questions)")
    print()
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
