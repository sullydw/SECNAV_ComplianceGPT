#!/usr/bin/env python3
"""
Conversational Builder — Phase L.4 Prototype

Thin multi-turn wrapper around IntakeOrchestrator.
No renderer, validator, config, or command-layer changes.

Public API:
    class BuilderSession:
        start(initial_payload=None) -> dict
        ingest_user_message(text) -> dict
        next_question() -> dict | None
        build_payload() -> dict
        run_validation() -> dict
        warning_summary() -> list[dict]
        finalize(accept_warnings=False) -> dict
        record_user_decision(rule_code, decision)
        set_draft_final_status(status)

CLI:
    python src/conversational_builder.py
    Interactive loop for testing. Type /quit to exit.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure repo root and src/ are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from intake_orchestrator import IntakeOrchestrator
from letter_model_v6 import normalize_payload


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BUILDER_VERSION = "L.9"

# Plain-English warning formatter map for active pilots + generic fallback
_WARNING_MAP = {
    "CCI-ROUTE-010": {
        "severity": "warning",
        "message": (
            "A routing office code appears as numbers only (for example, '123'). "
            "SECNAV M-5216.5 recommends writing it as 'Code 123'."
        ),
        "actions": ["Revise now", "Accept and keep my wording", "Ignore this warning"],
    },
    "CCI-ROUTE-011": {
        "severity": "warning",
        "message": (
            "This standard letter has no 'From:' line. "
            "Add one, or mark it as a window-envelope letter if it will use a window envelope."
        ),
        "actions": ["Revise now", "Accept and keep my wording", "Ignore this warning"],
    },
    "CCI-CH7-SUBJ-002": {
        "severity": "warning",
        "message": (
            "The subject line ends with punctuation (such as a period or question mark). "
            "SECNAV M-5216.5 Chapter 7 recommends no terminal punctuation in the subject line."
        ),
        "actions": ["Revise now", "Accept and keep my wording", "Ignore this warning"],
    },
}

_ADVISORY_FALLBACK = {
    "severity": "advisory",
    "message": "A validator finding may need review. Please verify the content follows SECNAV conventions before finalizing.",
    "actions": ["Dismiss"],
}

# Canonical builder steps
_BUILDER_STEPS = [
    "intake",
    "routing",
    "body",
    "refs_encls",
    "signature",
    "validation",
    "finalize",
]

# Friendly question-text overrides (L.9)
_QUESTION_OVERRIDES = {
    "subj": {
        "prompt_text": "What is the subject of this letter?",
    },
    "from": {
        "prompt_text": "Who is sending this letter (name or office)?",
    },
    "to": {
        "prompt_text": "Who is receiving this letter (name or office)?",
    },
    "body": {
        "prompt_text": "Enter the body text of the letter.",
    },
    "copy_to": {
        "prompt_text": "Who else should receive a copy (optional, e.g., copy_to: CNO)?",
    },
    "distribution": {
        "prompt_text": "Add distribution entries if needed (optional).",
    },
    "window_envelope": {
        "prompt_text": "Will this letter use a window envelope (yes/no)?",
    },
    "signature": {
        "prompt_text": (
            "Provide signer details:\n"
            "  signature.name: J. Q. Sample\n"
            "  signature.role: Commanding Officer (optional)\n"
            "  signature.title: Commanding Officer (optional)"
        ),
    },
}

def _today_military() -> str:
    """Return today's date in military format: '15 May 2026'."""
    d = datetime.now()
    return d.strftime("%d %B %Y")


def _coerce_value(field_path: str, raw: Any, data_type: str | None = None) -> Any:
    """Coerce a raw user input into the expected type for a field."""
    if raw is None:
        return None

    # Structured signature fields (signature.name, signature.role, signature.title)
    if field_path.startswith("signature."):
        if isinstance(raw, str):
            return raw.strip()
        return str(raw).strip() if raw else None

    # Boolean coercion
    if data_type == "boolean" or field_path == "window_envelope":
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            s = raw.strip().lower()
            return s in ("true", "yes", "1", "y")
        return bool(raw)

    # List coercion (signature removed from list_fields — handled as dict below)
    list_fields = {"via", "ref", "encl", "copy_to", "distribution", "body", "commands"}
    if data_type == "list" or field_path in list_fields:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            stripped = raw.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            if field_path == "body":
                return [line for line in stripped.splitlines() if line.strip()]
            return [raw] if raw.strip() else []
        return [str(raw)] if raw else []

    # Dict coercion (signature as a top-level field — plain string maps to dict.name)
    if data_type == "dict" or field_path == "signature":
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, list) and field_path == "signature":
            sig = {
                "name": None,
                "role": None,
                "title": None,
                "authority": None,
                "activity_head_title": None,
                "affects_pay_or_allowances": False,
            }
            if raw:
                sig["name"] = str(raw[0])
            if len(raw) > 1:
                # simplistic: second line treated as role text
                sig["role"] = str(raw[1])
            return sig
        if isinstance(raw, str):
            return {
                "name": raw,
                "role": None,
                "title": None,
                "authority": None,
                "activity_head_title": None,
                "affects_pay_or_allowances": False,
            }
        return raw

    # String default
    if isinstance(raw, str):
        return raw.strip()
    return str(raw)


def _expand_dot_fields(answers: dict[str, Any]) -> dict[str, Any]:
    """
    Expand dotted field names like signature.name into nested dicts.
    For example: {'signature.name': 'J. Q. Sample'} -> {'signature': {'name': 'J. Q. Sample'}}
    """
    expanded: dict[str, Any] = {}
    for key, value in answers.items():
        if "." in key:
            parts = key.split(".")
            target = expanded
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            # Merge with existing if any (e.g., plain 'signature' already created dict)
            if key in expanded and isinstance(expanded[key], dict) and isinstance(value, dict):
                expanded[key].update(value)
            else:
                expanded[key] = value
    return expanded


def _is_signature_field(field_path: str) -> bool:
    """Return True if field_path is a structured signature field."""
    return field_path.startswith("signature.") or field_path == "signature"


def _parse_key_value(text: str) -> dict[str, Any]:
    """Parse simple key:value pairs from text, one per line."""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = value
    return result


def _extract_rule_code(text: str) -> str | None:
    """Extract a CCI rule code from a warning/error string."""
    match = re.search(r"(CCI-[A-Z0-9-]+)", text)
    return match.group(1) if match else None


def _resolve_step(status: dict[str, Any]) -> str:
    """Determine the current builder step from orchestrator status."""
    missing_required = set(status.get("missing_required", []))

    intake_fields = {"doc_type", "from", "date", "subj"}
    if missing_required & intake_fields:
        return "intake"

    if "from" in missing_required:
        return "intake"

    routing_fields = {"to", "via", "copy_to", "distribution", "distribution_mode"}
    if missing_required & routing_fields:
        return "routing"

    if "body" in missing_required:
        return "body"

    if "signature" in missing_required:
        return "signature"

    if not missing_required:
        return "validation"

    return "intake"


# ---------------------------------------------------------------------------
# BuilderSession
# ---------------------------------------------------------------------------

class BuilderSession:
    """
    Multi-turn conversational builder for SECNAV correspondence.
    Delegates to IntakeOrchestrator for policy, questions, and audit.
    """

    def __init__(self, session_id: str | None = None):
        self._session_id = session_id or f"builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._orchestrator = IntakeOrchestrator()
        self._current_step = "intake"
        self._history: list[dict[str, Any]] = []
        self._user_decisions: dict[str, Any] = {}
        self._draft_final_status = "draft"
        self._last_question: dict[str, Any] | None = None
        # Approval state (L.30K-2)
        self._approved_for_finalize = False
        self._approved_at: str | None = None
        self._approved_preview_hash: str | None = None

    # -- public API -----------------------------------------------------------

    def start(self, initial_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Initialize the session and return the first question/status."""
        if initial_payload:
            self._orchestrator = IntakeOrchestrator(payload=initial_payload)

        status = self._orchestrator.get_status()
        self._current_step = _resolve_step(status)

        questions = self._orchestrator.next_questions(limit=1)
        q = questions[0] if questions else None
        if q:
            field = q.get("field_path", "")
            override = _QUESTION_OVERRIDES.get(field)
            if override:
                q = {**q, **override}
        self._last_question = q

        return {
            "session_id": self._session_id,
            "current_step": self._current_step,
            "status": status,
            "next_question": self._last_question,
        }

    def ingest_user_message(self, text: str) -> dict[str, Any]:
        """
        Process a free-text user response.

        Parsing strategy:
          1. Try key:value pairs (e.g., 'from: CO, USS NEVERSAIL').
          2. If no pairs found and a question is active, apply text as answer.
          3. Update orchestrator and return status + next question.
        """
        answers = _parse_key_value(text)

        if not answers and self._last_question:
            field_path = self._last_question["field_path"]
            data_type = self._last_question.get("data_type")
            answers = {field_path: text}

        coerced: dict[str, Any] = {}
        for field_path, raw in answers.items():
            data_type = None
            if self._last_question and self._last_question["field_path"] == field_path:
                data_type = self._last_question.get("data_type")
            coerced[field_path] = _coerce_value(field_path, raw, data_type)

        # Expand dotted fields like signature.name into nested dicts before applying
        coerced = _expand_dot_fields(coerced)

        self._orchestrator.apply_answers(coerced)
        self._history.append({"answers": coerced, "raw_text": text})

        status = self._orchestrator.get_status()
        self._current_step = _resolve_step(status)

        questions = self._orchestrator.next_questions(limit=1)
        q = questions[0] if questions else None
        if q:
            field = q.get("field_path", "")
            override = _QUESTION_OVERRIDES.get(field)
            if override:
                q = {**q, **override}
        self._last_question = q

        return {
            "session_id": self._session_id,
            "current_step": self._current_step,
            "status": status,
            "next_question": self._last_question,
            "applied_answers": coerced,
        }

    def next_question(self) -> dict[str, Any] | None:
        """Return the next missing-field question, or None if all required present."""
        questions = self._orchestrator.next_questions(limit=1)
        q = questions[0] if questions else None
        if q:
            field = q.get("field_path", "")
            override = _QUESTION_OVERRIDES.get(field)
            if override:
                q = {**q, **override}
        self._last_question = q
        return q

    def build_payload(self) -> dict[str, Any]:
        """Return the current merged payload."""
        return self._orchestrator.build_payload()

    def run_validation(self) -> dict[str, Any]:
        """Run CCI audit and return CCI_AUDIT_V1 result."""
        return self._orchestrator.run_audit()

    def warning_summary(self) -> list[dict[str, Any]]:
        """
        Return plain-English warning items with user decision states.
        Maps rule codes from the latest audit to human-readable messages.
        """
        audit = self._orchestrator.run_audit()
        summary: list[dict[str, Any]] = []

        for validator_name, validator_result in audit.get("validators", {}).items():
            for warning in validator_result.get("warnings", []):
                rule_code = _extract_rule_code(warning) if isinstance(warning, str) else None
                mapped = _WARNING_MAP.get(rule_code)
                if mapped:
                    summary.append({
                        "rule_code": rule_code,
                        "severity": mapped["severity"],
                        "message": mapped["message"],
                        "raw_warning": warning,
                        "actions": mapped["actions"],
                        "user_decision": self._user_decisions.get(rule_code),
                    })
                else:
                    summary.append({
                        "rule_code": rule_code or "unknown",
                        "severity": _ADVISORY_FALLBACK["severity"],
                        "message": _ADVISORY_FALLBACK["message"],
                        "raw_warning": warning,
                        "actions": _ADVISORY_FALLBACK["actions"],
                        "user_decision": self._user_decisions.get(rule_code),
                    })

            for error in validator_result.get("errors", []):
                rule_code = _extract_rule_code(error) if isinstance(error, str) else None
                mapped = _WARNING_MAP.get(rule_code)
                if mapped:
                    # Known pilot rule found in errors list: use mapped severity
                    # (validators may emit pilot findings in errors when effective
                    # severity is warning/error; we still present it as the mapped level)
                    summary.append({
                        "rule_code": rule_code,
                        "severity": mapped["severity"],
                        "message": mapped["message"],
                        "raw_warning": error,
                        "actions": mapped["actions"],
                        "user_decision": self._user_decisions.get(rule_code),
                    })
                else:
                    summary.append({
                        "rule_code": rule_code or "unknown",
                        "severity": "error",
                        "message": error,
                        "raw_warning": error,
                        "actions": ["Fix before finalizing"],
                        "user_decision": self._user_decisions.get(rule_code),
                    })

        return summary

    def validation_summary(self) -> dict[str, Any]:
        """
        Return a structured, user-facing validation summary.

        Includes:
          - total_findings, errors, warnings, advisories
          - known_pilot_findings count
          - pending_decisions count
          - finalize_allowed boolean
          - block_reason list (empty if allowed)
          - findings list (from warning_summary)
        """
        findings = self.warning_summary()
        errors = [f for f in findings if f["severity"] == "error"]
        warnings = [f for f in findings if f["severity"] == "warning"]
        advisories = [f for f in findings if f["severity"] == "advisory"]

        known_pilot_codes = {"CCI-ROUTE-010", "CCI-ROUTE-011", "CCI-CH7-SUBJ-002"}
        known_pilot_findings = [f for f in findings if f["rule_code"] in known_pilot_codes]

        pending_decisions = [
            f for f in findings
            if f["severity"] == "warning"
            and f.get("user_decision") not in ("accept", "ignore")
        ]

        block_reason: list[str] = []
        if errors:
            block_reason.append("Errors must be fixed before finalizing.")
        if pending_decisions and not self._user_decisions.get("_global_accept_warnings"):
            block_reason.append("Pending warning decisions must be accepted or revised.")

        finalize_allowed = not block_reason

        return {
            "total_findings": len(findings),
            "errors": len(errors),
            "warnings": len(warnings),
            "advisories": len(advisories),
            "known_pilot_findings": len(known_pilot_findings),
            "pending_decisions": len(pending_decisions),
            "finalize_allowed": finalize_allowed,
            "block_reason": block_reason,
            "findings": findings,
        }

    def finalize(self, accept_warnings: bool = False) -> dict[str, Any]:
        """
        Normalize payload, set draft/final status, return structured output.
        Does not render PDF.

        Parameters:
          accept_warnings: if True, treat all pending warning/advisory findings
                           as accepted for the purpose of allowing finalization.
                           Does NOT modify stored user_decisions.
        """
        payload = self.build_payload()

        payload["window_envelope"] = self._user_decisions.get(
            "window_envelope", payload.get("window_envelope", False)
        )
        payload["draft_final_status"] = self._draft_final_status
        payload["builder_version"] = _BUILDER_VERSION

        normalized = normalize_payload(payload)

        sig = normalized.get("signature")
        sig_has_name = False
        if isinstance(sig, dict):
            sig_has_name = bool(sig.get("name"))
        elif isinstance(sig, list) and sig:
            sig_has_name = bool(str(sig[0]).strip())

        if not sig_has_name:
            self._draft_final_status = "draft"
            normalized["draft_final_status"] = "draft"

        audit = self.run_validation()
        v_summary = self.validation_summary()

        # Honor accept_warnings parameter
        if accept_warnings:
            v_summary["finalize_allowed"] = True
            v_summary["block_reason"] = []
            v_summary["pending_decisions"] = 0
            for f in v_summary["findings"]:
                if f["severity"] in ("warning", "advisory"):
                    f["user_decision"] = f.get("user_decision") or "accepted_via_flag"

        return {
            "session_id": self._session_id,
            "payload": normalized,
            "audit": audit,
            "validation_summary": v_summary,
            "warning_summary": v_summary["findings"],
            "finalize_allowed": v_summary["finalize_allowed"],
            "block_reason": v_summary["block_reason"],
            "draft_final_status": self._draft_final_status,
            "builder_version": _BUILDER_VERSION,
        }

    # -- user decision helpers ------------------------------------------------

    def record_user_decision(self, rule_code: str, decision: str) -> None:
        """Record an explicit user decision for a warning/rule."""
        self._user_decisions[rule_code] = decision

    def set_signature_field(self, field: str, value: str) -> None:
        """
        Set a single key on the structured signature dict.
        Valid fields: name, role, title, authority, activity_head_title.
        """
        payload = self.build_payload()
        sig = payload.get("signature")
        if not isinstance(sig, dict):
            sig = {
                "name": None,
                "role": None,
                "title": None,
                "authority": None,
                "activity_head_title": None,
                "affects_pay_or_allowances": False,
            }
        sig[field] = value
        self._orchestrator.apply_answers({"signature": sig})

    def set_draft_final_status(self, status: str) -> None:
        """Set draft or final status."""
        if status in ("draft", "final"):
            self._draft_final_status = status

    def compute_preview_hash(self) -> str:
        """Compute a stable preview hash from draft-relevant payload content."""
        import hashlib
        payload = self.build_payload()
        keys = [
            "doc_type",
            "ssic",
            "originator_code",
            "date",
            "from",
            "to",
            "via",
            "subj",
            "body",
            "signature",
            "ref",
            "encl",
            "copy_to",
            "distribution",
            "unit_identity",
        ]
        canonical: dict[str, Any] = {}
        for k in keys:
            v = payload.get(k)
            if v is not None:
                canonical[k] = v
        json_bytes = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()

    def record_approval(self) -> dict[str, Any]:
        """Record explicit user approval of the current draft preview."""
        h = self.compute_preview_hash()
        self._approved_for_finalize = True
        self._approved_at = datetime.now().isoformat()
        self._approved_preview_hash = h
        return {
            "approved_for_finalize": True,
            "approved_at": self._approved_at,
            "approved_preview_hash": h,
            "current_preview_hash": h,
            "approval_current": True,
        }

    def approval_state(self) -> dict[str, Any]:
        """Return current approval state with hash comparison."""
        current = self.compute_preview_hash()
        approved = self._approved_for_finalize
        approved_hash = self._approved_preview_hash
        return {
            "approved_for_finalize": approved,
            "approved_at": self._approved_at,
            "approved_preview_hash": approved_hash,
            "current_preview_hash": current,
            "approval_current": approved and (approved_hash == current) if approved else False,
        }

    def clear_approval(self, reason: str | None = None) -> dict[str, Any]:
        """Clear prior approval state after a draft-relevant change."""
        self._approved_for_finalize = False
        self._approved_at = None
        self._approved_preview_hash = None
        return {
            "approved_for_finalize": False,
            "approved_at": None,
            "approved_preview_hash": None,
            "current_preview_hash": self.compute_preview_hash(),
            "approval_current": False,
            "approval_cleared_reason": reason,
        }

    # -- candidate tracking (L.29C) -------------------------------------------

    def record_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """
        Record a candidate for user confirmation. Does NOT apply it.
        Assigns candidate_id if missing. Stores as pending.
        Returns the stored candidate with assigned fields.
        """
        if not hasattr(self, "_candidates"):
            self._candidates: dict[str, dict[str, Any]] = {"pending": {}, "confirmed": {}, "rejected": {}}
        cand = dict(candidate)
        if not cand.get("candidate_id"):
            import uuid
            cand["candidate_id"] = f"cand_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        cand.setdefault("recorded_at", datetime.now().isoformat())
        cand.setdefault("requires_user_confirmation", True)
        self._candidates["pending"][cand["candidate_id"]] = cand
        return cand

    def get_candidates(self) -> dict[str, Any]:
        """Return all candidate buckets: pending, confirmed, rejected."""
        if not hasattr(self, "_candidates"):
            self._candidates = {"pending": {}, "confirmed": {}, "rejected": {}}
        return {
            "pending": list(self._candidates["pending"].values()),
            "confirmed": list(self._candidates["confirmed"].values()),
            "rejected": list(self._candidates["rejected"].values()),
            "counts": {
                "pending": len(self._candidates["pending"]),
                "confirmed": len(self._candidates["confirmed"]),
                "rejected": len(self._candidates["rejected"]),
            },
        }

    def confirm_candidate(self, candidate_id: str) -> dict[str, Any]:
        """
        Move a candidate from pending to confirmed and apply it safely.
        Safe mapping ensures only expected fields are applied per candidate_type.
        """
        if not hasattr(self, "_candidates"):
            return {"success": False, "error": "No candidates tracked."}
        pending = self._candidates["pending"]
        if candidate_id not in pending:
            return {"success": False, "error": f"Candidate {candidate_id} not found in pending."}
        cand = pending.pop(candidate_id)
        cand["confirmed_at"] = datetime.now().isoformat()
        applied: list[str] = []
        errors: list[str] = []

        ctype = cand.get("candidate_type", "")
        resolved = cand.get("resolved_value") or {}
        kv_lines = cand.get("recommended_kv") or []

        # --- safe application mapping ---
        # Helper to apply KV lines through ingest_user_message
        def _apply_kv(lines: list[str]) -> None:
            if lines:
                kv_text = "\n".join(lines)
                self.ingest_user_message(kv_text)

        # Helper to safely set a direct field
        def _set_direct(field_path: str, value: Any) -> None:
            if value is None:
                return
            self._orchestrator.apply_answers({field_path: value})

        try:
            if ctype == "command_expansion":
                # Apply only recommended_kv
                _apply_kv(kv_lines)
                applied.extend([line.split(":", 1)[0].strip() for line in kv_lines if ":" in line])

            elif ctype == "unit_identity":
                # Safe: set unit_identity dict only if it has expected keys
                uid = resolved.get("unit_identity") or resolved
                if uid and isinstance(uid, dict):
                    expected = {"letterhead_family", "UNIT_OR_ACTIVITY_NAME"}
                    if expected & set(uid.keys()):
                        _set_direct("unit_identity", uid)
                        applied.append("unit_identity")
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line:
                        applied.append(line.split(":", 1)[0].strip())

            elif ctype == "ssic_candidate":
                ssic = resolved.get("ssic")
                if ssic:
                    _set_direct("ssic", ssic)
                    applied.append("ssic")
                _apply_kv(kv_lines)

            elif ctype == "routing_interpretation":
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line:
                        applied.append(line.split(":", 1)[0].strip())

            elif ctype == "signature_block":
                sig = resolved.get("signature") or resolved
                if sig and isinstance(sig, dict):
                    # Merge with existing signature
                    payload = self.build_payload()
                    existing = payload.get("signature") or {}
                    if not isinstance(existing, dict):
                        existing = {}
                    merged = {**existing, **sig}
                    # Only safe keys
                    safe_sig = {k: v for k, v in merged.items() if k in {"name", "role", "title", "authority", "activity_head_title", "affects_pay_or_allowances"}}
                    if safe_sig:
                        _set_direct("signature", safe_sig)
                        applied.append("signature")
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line and line.startswith("signature."):
                        applied.append(line.split(":", 1)[0].strip())

            elif ctype == "date_confirmation":
                date_val = resolved.get("date")
                if date_val:
                    _set_direct("date", date_val)
                    applied.append("date")
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line:
                        applied.append(line.split(":", 1)[0].strip())

            elif ctype == "subject_draft":
                subj = resolved.get("subj") or resolved.get("subject")
                if subj:
                    _set_direct("subj", subj)
                    applied.append("subj")
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line and (line.startswith("subj:") or line.startswith("subject:")):
                        applied.append("subj")

            elif ctype == "body_draft":
                body = resolved.get("body")
                if body:
                    if isinstance(body, str):
                        body = [body]
                    if isinstance(body, list):
                        _set_direct("body", body)
                        applied.append("body")
                _apply_kv(kv_lines)
                for line in kv_lines:
                    if ":" in line and line.startswith("body:"):
                        applied.append("body")

            else:
                errors.append(f"Unknown candidate_type: {ctype}")
        except Exception as exc:
            errors.append(f"Application error: {exc}")

        if errors:
            # Put back into pending on error
            self._candidates["pending"][candidate_id] = cand
            return {"success": False, "error": "; ".join(errors), "candidate_id": candidate_id}

        cand["applied_fields"] = applied
        self._candidates["confirmed"][candidate_id] = cand
        return {"success": True, "candidate_id": candidate_id, "applied_fields": applied}

    def reject_candidate(self, candidate_id: str, reason: str = "") -> dict[str, Any]:
        """Move a candidate from pending to rejected. Does not apply."""
        if not hasattr(self, "_candidates"):
            return {"success": False, "error": "No candidates tracked."}
        pending = self._candidates["pending"]
        if candidate_id not in pending:
            return {"success": False, "error": f"Candidate {candidate_id} not found in pending."}
        cand = pending.pop(candidate_id)
        cand["rejected_at"] = datetime.now().isoformat()
        if reason:
            cand["rejection_reason"] = reason
        self._candidates["rejected"][candidate_id] = cand
        return {"success": True, "candidate_id": candidate_id}

    # -- direct field setters (L.29C) ----------------------------------------

    def set_unit_identity(self, unit_identity: dict[str, Any]) -> None:
        """Directly set the unit_identity dict on the orchestrator payload."""
        self._orchestrator.apply_answers({"unit_identity": unit_identity})

    def set_originator_code(self, code: str) -> None:
        """Directly set the originator_code field."""
        self._orchestrator.apply_answers({"originator_code": code})

    def set_ssic(self, ssic: str) -> None:
        """Directly set the ssic field."""
        self._orchestrator.apply_answers({"ssic": ssic})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    print("SECNAV Conversational Builder — Phase L.5 Prototype")
    print("=" * 60)
    print()

    builder = BuilderSession()
    result = builder.start()

    print(f"Session: {result['session_id']}")
    print(f"Step: {result['current_step']}")
    print()

    if result["next_question"]:
        q = result["next_question"]
        print(f"[{q['bucket'].upper()}] {q['field_path']}")
        print(f"  {q['prompt_text']}")
        print()
    else:
        print("No questions needed.")
        return 0

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.lower() in ("/quit", "/exit", "/q"):
            break

        if text.lower() == "/status":
            payload = builder.build_payload()
            print(json.dumps(payload, indent=2))
            continue

        if text.lower() == "/validate":
            audit = builder.run_validation()
            print("AUDIT SUMMARY:")
            print(f"  Errors:   {audit['summary']['total_errors']}")
            print(f"  Warnings: {audit['summary']['total_warnings']}")
            print(f"  Pass:     {audit['summary']['overall_pass']}")
            continue

        if text.lower() == "/warnings":
            v_summary = builder.validation_summary()
            print(f"Findings: {v_summary['total_findings']}  (Errors: {v_summary['errors']}, Warnings: {v_summary['warnings']}, Advisories: {v_summary['advisories']})")
            if v_summary['pending_decisions']:
                print(f"Pending decisions: {v_summary['pending_decisions']}")
            print(f"Finalize allowed: {'Yes' if v_summary['finalize_allowed'] else 'No'}")
            if v_summary['block_reason']:
                for reason in v_summary['block_reason']:
                    print(f"  Block: {reason}")
            print()
            for item in v_summary['findings']:
                print(f"[{item['severity'].upper()}] {item['rule_code']}")
                print(f"  {item['message']}")
                print(f"  Actions: {', '.join(item['actions'])}")
                if item.get("user_decision"):
                    print(f"  Decision: {item['user_decision']}")
                print()
            continue

        if text.lower() == "/finalize":
            result = builder.finalize()
            print(f"Finalize allowed: {'Yes' if result['finalize_allowed'] else 'No'}")
            if result['block_reason']:
                for reason in result['block_reason']:
                    print(f"  Block: {reason}")
            print("FINALIZED PAYLOAD:")
            print(json.dumps(result["payload"], indent=2))
            continue

        result = builder.ingest_user_message(text)

        print(f"Step: {result['current_step']}")
        if result["next_question"]:
            q = result["next_question"]
            print(f"[{q['bucket'].upper()}] {q['field_path']}")
            print(f"  {q['prompt_text']}")
        else:
            print("All required fields provided.")
            print("Commands: /validate, /warnings, /finalize, /status, /quit")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
