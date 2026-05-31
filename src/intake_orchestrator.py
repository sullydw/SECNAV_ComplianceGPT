#!/usr/bin/env python3
"""
CCI Intake Orchestrator — Phase 1 Foundation

Public API:
    class IntakeOrchestrator:
        __init__(self, payload=None, user_answers=None)
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = "CCI_INTAKE_V1"

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


# ---------------------------------------------------------------------------
# IntakeOrchestrator
# ---------------------------------------------------------------------------

class IntakeOrchestrator:
    def __init__(self, payload: dict[str, Any] | None = None, user_answers: dict[str, Any] | None = None):
        self._payload: dict[str, Any] = copy.deepcopy(payload) if payload else {}
        self._user_answers: dict[str, Any] = copy.deepcopy(user_answers if user_answers else {})
        # Normalize any flat dot-notation keys immediately into nested dict
        self._user_answers = _flatten_aliases(self._user_answers)

    # -- public methods -------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return intake status including resolved context, audit summary, and missing/question fields."""
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
        }

    def next_questions(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return prioritized missing-field questions. Required first, then recommended, then optional."""
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
            # Skip if already present in payload or user_answers
            if _field_is_present_in_payload(self._payload, field):
                continue
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
        """Return a merged payload: payload explicit values take priority over user_answers."""
        merged = copy.deepcopy(self._payload)
        self._merge_answers(self._user_answers, merged, override=False)
        return merged

    def run_audit(self) -> dict[str, Any]:
        """Run the consolidated CCI audit against the built payload."""
        return run_cci_audit(self.build_payload(), self._user_answers)

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
