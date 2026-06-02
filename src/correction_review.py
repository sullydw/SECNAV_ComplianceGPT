#!/usr/bin/env python3
"""
Correction Review — Phase E: Review/Promotion Utility

Public API:
    list_candidates_for_review(
        log_path: Path | None = None,
        correction_type: str | None = None,
        component: str | None = None,
        doc_type: str | None = None,
    ) -> tuple[list[dict], list[str]]
        Return candidates eligible for review (pending or under_review only).

    claim_candidate(
        candidate_id: str,
        reviewer_id: str,
        log_path: Path | None = None,
    ) -> dict
        Set status to under_review and record reviewer_id.

    review_candidate(
        candidate_id: str,
        reviewer_id: str,
        decision: str,
        review_metadata: dict,
        log_path: Path | None = None,
        approved_rule_path: Path | None = None,
    ) -> dict
        Core reviewer action: reject, defer, promote, or supersede.
        Appends review_metadata. For promote, creates approved_global_rule record.

    supersede_candidate(
        candidate_id: str,
        reviewer_id: str,
        reason: str,
        superseded_by_rule_id: str | None = None,
        log_path: Path | None = None,
    ) -> dict
        Mark candidate superseded (explicit reviewer action only in Phase E).

    propose_phase_c_redirect(
        candidate: dict,
        profile_path: str,
    ) -> dict
        Build a Phase C promotion proposal from a rejected global candidate.

Design choices:
    - Local-only, single reviewer at a time. No multi-user locking.
    - All review_metadata is append-only within the candidate record.
    - Approved rule records are local-only and gitignored.
    - Promotion means record-creation only; no validator/catalog/renderer changes.
    - Reviewer-entered text is sanitized before storage.
    - Phase E does not auto-supersede based on external implementation.
"""

from __future__ import annotations

import copy
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure sibling imports work
_SRC_DIR = Path(__file__).resolve().parent
import sys
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

try:
    from correction_pending_log import (
        _read_jsonl,
        _write_jsonl,
        _sanitize_value,
        _DEFAULT_LOG_PATH,
        _ALLOWED_STATUSES,
    )
except Exception:
    # Minimal fallback for isolated testing
    def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
        if not path.exists():
            return [], []
        text = path.read_text(encoding="utf-8")
        records: list[dict[str, Any]] = []
        warnings: list[str] = []
        for i, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if isinstance(rec, dict):
                    records.append(rec)
                else:
                    warnings.append(f"Line {i} is not a dict")
            except json.JSONDecodeError as exc:
                warnings.append(f"Line {i} JSON parse error: {exc}")
        return records, warnings

    def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> list[str]:
        warnings: list[str] = []
        tmp = path.with_suffix(".tmp")
        try:
            lines = [json.dumps(r, ensure_ascii=False) + "\n" for r in records]
            tmp.write_text("".join(lines), encoding="utf-8")
            os.replace(str(tmp), str(path))
        except Exception as exc:
            warnings.append(f"Failed writing {path.name}: {exc}")
        return warnings

    def _sanitize_value(field_path: str, raw_value: Any) -> tuple[str, str, list[str]]:
        text = str(raw_value) if raw_value is not None else ""
        return text, "low", []

    _DEFAULT_LOG_PATH = Path("corrections/pending_corrections.jsonl")
    _ALLOWED_STATUSES = {
        "pending", "under_review", "deferred", "rejected", "promoted", "superseded",
    }


try:
    from correction_promote import propose_promotion, is_eligible_for_promotion
except Exception:
    propose_promotion = None  # type: ignore
    is_eligible_for_promotion = None  # type: ignore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_APPROVED_PATH = _REPO_ROOT / "corrections" / "approved_rule_promotions.json"

_ALLOWED_REVIEW_DECISIONS = {"reject", "defer", "promote", "supersede"}
_ALLOWED_REVIEW_TYPES = {"possible_secnav_manual_rule", "bug_validator_gap"}

# Reviewer-entered text fields that must be scanned for PII
_REVIEWER_TEXT_FIELDS = {
    "review_notes", "rationale", "secnav_citation_quote",
    "expected_behavior", "actual_behavior",
}

# Maximum length for free-text fields
_MAX_TEXT_LEN = 2000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_rule_id() -> str:
    return f"agr_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"


def _validate_status_transition(current: str, new: str) -> tuple[bool, str]:
    """Validate a status transition."""
    allowed = {
        "pending": {"under_review", "rejected"},
        "under_review": {"deferred", "rejected", "promoted", "superseded"},
        "deferred": {"under_review", "rejected", "superseded"},
        "rejected": {"under_review"},
        "promoted": {"superseded"},
        "superseded": set(),
    }
    if new not in allowed.get(current, set()):
        return False, f"Invalid transition: {current} -> {new}"
    return True, ""


def _sanitize_reviewer_text(text: str, field_path: str = "") -> tuple[str, list[str]]:
    """Sanitize reviewer-entered free text before storage."""
    warnings: list[str] = []
    if not text:
        return text, warnings
    # Truncate
    if len(text) > _MAX_TEXT_LEN:
        text = text[:_MAX_TEXT_LEN]
        warnings.append(f"Reviewer text truncated to {_MAX_TEXT_LEN} chars")
    # Use correction_pending_log sanitization if available
    try:
        sanitized, confidence, san_warnings = _sanitize_value(field_path or "reviewer_text", text)
        warnings.extend(san_warnings)
        if confidence == "low":
            warnings.append("Reviewer text sanitization confidence is low; review output for PII")
        return sanitized, warnings
    except Exception:
        # Fallback: simple PII patterns
        sanitized = text
        for pattern, token in [
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
            (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]"),
            (r"\b\d{10}\b", "[EDIPI]"),
        ]:
            sanitized = re.sub(pattern, token, sanitized)
        return sanitized, warnings


def _validate_evidence(
    review_metadata: dict[str, Any],
    correction_type: str,
) -> tuple[bool, list[str]]:
    """Validate that required evidence is present for promotion."""
    errors: list[str] = []
    rule_category = review_metadata.get("rule_category", "")

    if correction_type == "possible_secnav_manual_rule" or rule_category == "manual_rule":
        secnav = review_metadata.get("secnav_citation", {})
        if not isinstance(secnav, dict):
            errors.append("secnav_citation must be an object")
        elif not any(secnav.get(k) for k in ("chapter", "paragraph", "figure", "quote")):
            errors.append(
                "Promotion of manual_rule requires at least one of: "
                "chapter, paragraph, figure, or quote in secnav_citation"
            )

    if correction_type == "bug_validator_gap" or rule_category == "validator_gap":
        validator = review_metadata.get("validator_evidence", {})
        if not isinstance(validator, dict):
            errors.append("validator_evidence must be an object")
        else:
            required_validator_fields = [
                "validator_name", "expected_behavior", "actual_behavior"
            ]
            for f in required_validator_fields:
                if not validator.get(f):
                    errors.append(f"validator_evidence.{f} is required for validator_gap")

    # Rationale always required
    rationale = str(review_metadata.get("rationale", "")).strip()
    if not rationale:
        errors.append("rationale is required for all promotion decisions")

    reviewer_id = str(review_metadata.get("reviewed_by", "")).strip()
    if not reviewer_id:
        errors.append("reviewed_by (reviewer ID) is required")

    return len(errors) == 0, errors


def _check_candidate_eligible_for_review(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check whether a single candidate record is eligible for review."""
    reasons: list[str] = []
    status = record.get("status", "")
    if status not in ("pending", "under_review"):
        reasons.append(f"status={status} not reviewable")

    ctype = record.get("correction_type", "")
    if ctype not in _ALLOWED_REVIEW_TYPES:
        reasons.append(f"correction_type={ctype} not reviewable")

    if record.get("duplicate_of"):
        reasons.append("marked as duplicate_of another candidate")

    return len(reasons) == 0, reasons


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_candidates_for_review(
    log_path: Path | None = None,
    correction_type: str | None = None,
    component: str | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    exclude_superseded_duplicates: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Return candidates eligible for review.
    Only includes records with status pending or under_review,
    correction_type in allowed set, and not marked as duplicate.
    """
    warnings: list[str] = []
    path = log_path or _DEFAULT_LOG_PATH
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    # Collect promoted fingerprints to exclude superseded duplicates
    promoted_fps: set[str] = set()
    if exclude_superseded_duplicates:
        for r in records:
            if r.get("status") == "promoted":
                promoted_fps.add(r.get("fingerprint", ""))

    eligible: list[dict[str, Any]] = []
    for r in records:
        is_elig, reasons = _check_candidate_eligible_for_review(r)
        if not is_elig:
            continue
        if correction_type is not None and r.get("correction_type") != correction_type:
            continue
        if component is not None and r.get("component") != component:
            continue
        if doc_type is not None and r.get("doc_type") != doc_type:
            continue
        if status is not None and r.get("status") != status:
            continue
        if exclude_superseded_duplicates:
            fp = r.get("fingerprint", "")
            if fp and fp in promoted_fps:
                continue
        eligible.append(copy.deepcopy(r))

    return eligible, warnings


def claim_candidate(
    candidate_id: str,
    reviewer_id: str,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """
    Claim a candidate for review by a single reviewer.
    Sets status to under_review and records reviewed_by.
    Returns dict with success, warnings.
    """
    warnings: list[str] = []
    path = log_path or _DEFAULT_LOG_PATH
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    found = False
    for r in records:
        if r.get("candidate_id") == candidate_id:
            found = True
            current_status = r.get("status", "")
            valid, msg = _validate_status_transition(current_status, "under_review")
            if not valid:
                warnings.append(msg)
                return {"success": False, "candidate_id": candidate_id, "warnings": warnings}
            r["status"] = "under_review"
            # Initialize review_metadata as a list if not present
            if "review_metadata" not in r or r["review_metadata"] is None:
                r["review_metadata"] = []
            if not isinstance(r["review_metadata"], list):
                r["review_metadata"] = [r["review_metadata"]]
            r["review_metadata"].append({
                "reviewed_at": _now_utc_iso(),
                "reviewed_by": str(reviewer_id)[:200],
                "review_action": "claimed",
                "previous_status": current_status,
                "new_status": "under_review",
            })
            break

    if not found:
        warnings.append(f"Candidate {candidate_id} not found")
        return {"success": False, "candidate_id": candidate_id, "warnings": warnings}

    write_warnings = _write_jsonl(path, records)
    warnings.extend(write_warnings)
    return {"success": True, "candidate_id": candidate_id, "warnings": warnings}


def review_candidate(
    candidate_id: str,
    reviewer_id: str,
    decision: str,
    review_metadata: dict[str, Any],
    log_path: Path | None = None,
    approved_rule_path: Path | None = None,
) -> dict[str, Any]:
    """
    Core reviewer action.

    Parameters:
        decision: one of "reject", "defer", "promote", "supersede"
        review_metadata: dict with evidence and rationale. Key fields:
            - rationale (required)
            - secnav_citation: {chapter, paragraph, figure, quote} (manual_rule)
            - validator_evidence: {validator_name, expected_behavior, actual_behavior, reproduction_payload} (validator_gap)
            - rule_category: "manual_rule" or "validator_gap"
            - ai_assisted: bool
            - ai_suggested_citation: str or null
    Returns:
        dict with success, candidate_id, warnings, approved_rule_record (if promoted)
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "candidate_id": candidate_id,
        "warnings": warnings,
        "approved_rule_record": None,
    }

    if decision not in _ALLOWED_REVIEW_DECISIONS:
        warnings.append(f"Invalid decision: {decision}. Must be one of {_ALLOWED_REVIEW_DECISIONS}")
        return result

    path = log_path or _DEFAULT_LOG_PATH
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    candidate: dict[str, Any] | None = None
    for r in records:
        if r.get("candidate_id") == candidate_id:
            candidate = r
            break

    if candidate is None:
        warnings.append(f"Candidate {candidate_id} not found")
        return result

    current_status = candidate.get("status", "")
    target_status = {
        "reject": "rejected",
        "defer": "deferred",
        "promote": "promoted",
        "supersede": "superseded",
    }[decision]

    valid, msg = _validate_status_transition(current_status, target_status)
    if not valid:
        warnings.append(msg)
        return result

    # Sanitize reviewer text fields
    sanitized_meta = copy.deepcopy(review_metadata)
    for field in _REVIEWER_TEXT_FIELDS:
        if field in sanitized_meta and isinstance(sanitized_meta[field], str):
            sanitized_val, san_warnings = _sanitize_reviewer_text(sanitized_meta[field], field)
            sanitized_meta[field] = sanitized_val
            warnings.extend(san_warnings)

    # Validate evidence for promotion
    if decision == "promote":
        ctype = candidate.get("correction_type", "")
        # Inject reviewer_id into sanitized_meta for validation
        sanitized_meta["reviewed_by"] = str(reviewer_id)[:200]
        ok, evidence_errors = _validate_evidence(sanitized_meta, ctype)
        if not ok:
            warnings.extend(evidence_errors)
            return result

    # Build review metadata entry
    entry: dict[str, Any] = {
        "reviewed_at": _now_utc_iso(),
        "reviewed_by": str(reviewer_id)[:200],
        "review_action": decision,
        "previous_status": current_status,
        "new_status": target_status,
        "rationale": str(sanitized_meta.get("rationale", ""))[:_MAX_TEXT_LEN],
        "ai_assisted": bool(sanitized_meta.get("ai_assisted", False)),
        "ai_suggested_citation": sanitized_meta.get("ai_suggested_citation"),
    }

    if decision == "promote":
        entry["secnav_citation"] = sanitized_meta.get("secnav_citation")
        entry["validator_evidence"] = sanitized_meta.get("validator_evidence")
        entry["rule_category"] = sanitized_meta.get("rule_category", "")
        entry["evidence_quality"] = sanitized_meta.get("evidence_quality", "moderate")

    if decision == "reject":
        entry["rejection_reason"] = sanitized_meta.get("rejection_reason", "")
        entry["redirected_to_phase_c"] = bool(sanitized_meta.get("redirected_to_phase_c", False))
        entry["phase_c_profile_name"] = sanitized_meta.get("phase_c_profile_name", "")

    if decision == "supersede":
        entry["superseded_by_rule_id"] = sanitized_meta.get("superseded_by_rule_id", "")
        entry["superseded_by_candidate_id"] = sanitized_meta.get("superseded_by_candidate_id", "")

    # Append to candidate review_metadata
    if "review_metadata" not in candidate or candidate["review_metadata"] is None:
        candidate["review_metadata"] = []
    if not isinstance(candidate["review_metadata"], list):
        # If Phase D wrote a single dict, convert to list
        candidate["review_metadata"] = [candidate["review_metadata"]]
    candidate["review_metadata"].append(entry)

    # Update status
    candidate["status"] = target_status

    # For promotion, create approved_global_rule record
    approved_record: dict[str, Any] | None = None
    if decision == "promote":
        approved_record = _create_approved_rule_record(candidate, entry)
        write_result = _write_approved_rule_record(approved_record, approved_rule_path)
        if not write_result.get("success"):
            warnings.extend(write_result.get("warnings", []))
            return result
        result["approved_rule_record"] = approved_record

    # Write updated pending log
    write_warnings = _write_jsonl(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    return result


def supersede_candidate(
    candidate_id: str,
    reviewer_id: str,
    reason: str,
    superseded_by_rule_id: str | None = None,
    superseded_by_candidate_id: str | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """
    Explicit reviewer action to mark a candidate as superseded.
    In Phase E, this is the only way a candidate becomes superseded.
    """
    review_metadata = {
        "rationale": reason,
        "superseded_by_rule_id": superseded_by_rule_id or "",
        "superseded_by_candidate_id": superseded_by_candidate_id or "",
    }
    return review_candidate(
        candidate_id=candidate_id,
        reviewer_id=reviewer_id,
        decision="supersede",
        review_metadata=review_metadata,
        log_path=log_path,
    )


def propose_phase_c_redirect(
    candidate: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    """
    Build a Phase C promotion proposal from a rejected global candidate.
    Returns a proposal dict ready for Phase C confirm_and_write_promotion().

    Safety:
        - Only works if the originating correction still exists in session store.
        - No automatic write; Phase C two-step approval still applies.
        - Returns error if propose_promotion is not available.
    """
    result: dict[str, Any] = {
        "success": False,
        "proposal": None,
        "warnings": [],
    }

    if propose_promotion is None:
        result["warnings"].append(
            "Phase C correction_promote module not available; manual profile entry required."
        )
        return result

    source_correction_id = candidate.get("source_correction_id", "")
    session_id = candidate.get("session_id", "")

    # Try to load the original correction from session store if possible
    original_correction: dict[str, Any] | None = None
    if session_id and source_correction_id:
        try:
            from correction_store import load_session_corrections
            session_cors = load_session_corrections(session_id)
            for c in session_cors:
                if c.get("correction_id") == source_correction_id:
                    original_correction = c
                    break
        except Exception:
            pass

    if original_correction is None:
        # Build a synthetic record from candidate data
        original_correction = {
            "correction_id": source_correction_id or candidate.get("candidate_id", ""),
            "field_path": candidate.get("field_path", ""),
            "corrected_value": candidate.get("sanitized_value", ""),
            "original_value": candidate.get("original_value_sanitized", ""),
            "reason": candidate.get("user_reason", ""),
            "doc_type": candidate.get("doc_type", "unknown"),
            "component": candidate.get("component", "unknown"),
            "scope": "current_session",
            "correction_type": "local_command_preference",
            "session_id": session_id,
            "user_rejected": False,
            "validator_conflict": False,
        }
        result["warnings"].append(
            "Original session correction not found; using synthetic record from candidate. "
            "Phase C approval gates still apply."
        )

    # Override type to local_command_preference
    original_correction["correction_type"] = "local_command_preference"

    # Run Phase C eligibility
    if is_eligible_for_promotion is not None:
        eligible, reasons = is_eligible_for_promotion(original_correction)
        if not eligible:
            result["warnings"].extend(reasons)
            return result

    try:
        proposal = propose_promotion(original_correction, profile_path)
    except Exception as exc:
        result["warnings"].append(f"propose_promotion failed: {exc}")
        return result

    result["success"] = True
    result["proposal"] = proposal
    return result


# ---------------------------------------------------------------------------
# Approved rule record helpers
# ---------------------------------------------------------------------------


def _create_approved_rule_record(
    candidate: dict[str, Any],
    review_entry: dict[str, Any],
) -> dict[str, Any]:
    """Build an approved_global_rule record from a promoted candidate."""
    rule_id = _generate_rule_id()
    rule_category = review_entry.get("rule_category", "")
    if not rule_category:
        # Infer from correction_type if missing
        ctype = candidate.get("correction_type", "")
        if ctype == "possible_secnav_manual_rule":
            rule_category = "manual_rule"
        elif ctype == "bug_validator_gap":
            rule_category = "validator_gap"
        else:
            rule_category = "unknown"

    record: dict[str, Any] = {
        "rule_id": rule_id,
        "promoted_from_candidate_id": candidate.get("candidate_id", ""),
        "promoted_at": _now_utc_iso(),
        "promoted_by": review_entry.get("reviewed_by", ""),
        "rule_category": rule_category,
        "field_path": candidate.get("field_path", ""),
        "doc_type_filter": [candidate.get("doc_type", "")] if candidate.get("doc_type") else [],
        "component_filter": [candidate.get("component", "")] if candidate.get("component") else [],
        "sanitized_value": candidate.get("sanitized_value", ""),
        "original_value_sanitized": candidate.get("original_value_sanitized", ""),
        "secnav_citation": review_entry.get("secnav_citation") if rule_category == "manual_rule" else None,
        "validator_evidence": review_entry.get("validator_evidence") if rule_category == "validator_gap" else None,
        "rationale": review_entry.get("rationale", ""),
        "evidence_quality": review_entry.get("evidence_quality", "moderate"),
        "implementation_status": "pending_implementation",
        "linked_validator_update": None,
        "linked_rule_file": None,
        "review_metadata": review_entry,
    }
    return record


def _write_approved_rule_record(
    record: dict[str, Any],
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """Append an approved rule record to the local gitignored JSON store."""
    warnings: list[str] = []
    path = approved_path or _DEFAULT_APPROVED_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                existing = json.loads(text)
                if not isinstance(existing, list):
                    existing = [existing]
        except Exception as exc:
            warnings.append(f"Failed to parse existing approved rules: {exc}")
            existing = []

    existing.append(record)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception as exc:
        warnings.append(f"Failed to write approved rule record: {exc}")
        return {"success": False, "rule_id": record.get("rule_id"), "warnings": warnings}

    return {"success": True, "rule_id": record.get("rule_id"), "warnings": warnings}


# ---------------------------------------------------------------------------
# CLI (minimal)
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    print("correction_review.py is a library module. Import it, do not run directly.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
