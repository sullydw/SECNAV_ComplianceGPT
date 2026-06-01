#!/usr/bin/env python3
"""
Correction Pending Log — Phase D: Pending Global Rule Candidate Logging

Public API:
    is_eligible_for_pending_log(correction_record: dict) -> tuple[bool, list[str]]
        Check whether a correction record is eligible for pending global rule logging.

    propose_pending_log(correction_record: dict) -> dict
        Step 1: Build a candidate proposal (requires explicit user confirmation before write).

    confirm_and_write_pending_log(proposal: dict, log_path: Path | None = None) -> dict
        Step 2: After explicit user confirmation, append a sanitized candidate record
        to the pending log JSONL file.

    list_pending_candidates(log_path: Path | None = None, **filters) -> list[dict]
        Read pending candidate records from the log with optional filters.

    update_candidate_status(candidate_id: str, new_status: str, review_metadata: dict | None,
                            log_path: Path | None = None) -> dict
        Transition a candidate's status and optionally populate review_metadata.

    _sanitize_value(field_path: str, raw_value: str) -> tuple[str, str, list[str]]
        Internal: Abstract/redact raw values for global rule candidate storage.
        Returns (sanitized_value, confidence, warnings).

    _compute_fingerprint(record: dict) -> str
        Internal: SHA256-based fingerprint for duplicate detection.

Design choices:
    - All file writes are append-only atomic (write temp line + os.replace).
    - No auto-append; two-step confirmation required.
    - Log file is local-only and gitignored (corrections/pending_corrections.jsonl).
    - Sanitization strips PII and command-specific values before writing.
    - Duplicates are surfaced, not silently merged.
    - No global rule promotion implemented here.
    - No validator changes.
    - No renderer changes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_LOG_PATH = _REPO_ROOT / "corrections" / "pending_corrections.jsonl"

_ALLOWED_LOG_TYPES = {"possible_secnav_manual_rule", "bug_validator_gap"}

_ALLOWED_STATUSES = {
    "pending", "under_review", "deferred", "rejected", "promoted", "superseded",
}

# Regex-based sanitization patterns (order matters: more specific first)
_SANITIZE_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # EDIPI (10 digits)
    (re.compile(r"\b\d{10}\b"), "[EDIPI]", "EDIPI pattern"),
    # SSN (123-45-6789 or 123456789)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]", "SSN pattern"),
    (re.compile(r"\b\d{9}\b"), "[SSN]", "SSN pattern (no dashes)"),
    # DoD ID (N followed by digits, or similar patterns)
    (re.compile(r"\b[Nn]\d{7,9}\b"), "[DOD_ID]", "DoD ID pattern"),
    # Emails (must run before UIC to avoid partial matches in local-parts)
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]", "email pattern"),
    # Phone numbers (must run before UIC to avoid digit substrings matching UIC)
    (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]", "phone number pattern"),
    # Building / room numbers (run before UIC to avoid plain words like "Bldg" being eaten by UIC)
    (re.compile(r"\b(Bldg|Building|Bldg\.?)\s*\d+\b", re.IGNORECASE), "[BUILDING]", "building number pattern"),
    (re.compile(r"\b(Rm|Room|Rm\.)\s*\d+\b", re.IGNORECASE), "[ROOM]", "room number pattern"),
    # UIC (N + 4-5 digits, or 4-6 alphanumeric)
    (re.compile(r"(?<!\[)\b[A-Za-z0-9]{4,6}\b(?!\])"), "[UIC]", "UIC pattern"),
    # Hull numbers
    (re.compile(r"\b(SS|DDG|CG|LHD|LPD|LCS|SSN|CVN)\s*-?\s*\d{1,3}\b", re.IGNORECASE), "[HULL_NUMBER]", "hull number pattern"),
    # Tail numbers
    (re.compile(r"\b[A-Za-z]{1,2}\s*-?\s*\d{1,5}\b"), "[TAIL_NUMBER]", "tail number pattern"),
    # Addresses (simple street patterns)
    (re.compile(r"\b\d+\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir)\b", re.IGNORECASE), "[ADDRESS]", "address pattern"),
]

# Additional command-name / person-name patterns (heuristic)
_COMMAND_NAME_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"Commanding Officer,\s+USS?\s+[A-Z]+", re.IGNORECASE), "[COMMAND_NAME]"),
    (re.compile(r"Commanding Officer,\s+[^,]+"), "[COMMAND_NAME]"),
    (re.compile(r"Commander,\s+[^,]+"), "[COMMAND_NAME]"),
    (re.compile(r"CO,\s+[^,]+"), "[COMMAND_NAME]"),
]

_PERSON_NAME_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+\b"), "[PERSON_NAME]"),
    (re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"), "[PERSON_NAME]"),
]

_PLACEHOLDER_VALUES = {"", "tbd", "todo", "placeholder", "<tbd>", "<todo>", "<placeholder>"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_candidate_id() -> str:
    return f"cand_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"


def _sanitize_value(field_path: str, raw_value: Any) -> tuple[str, str, list[str]]:
    """
    Abstract/redact a raw value for pending candidate logging.
    Returns (sanitized_value, confidence, warnings).
    """
    warnings: list[str] = []
    if raw_value is None:
        return "[NULL]", "low", ["original_value was None"]

    text = str(raw_value)
    if not text.strip():
        return "[EMPTY]", "low", ["original_value was empty"]

    sanitized = text
    matched_any = False

    # Run PII / command-specific patterns
    for pattern, replacement, label in _SANITIZE_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub(replacement, sanitized)
            matched_any = True

    # Command name patterns
    for pattern, replacement in _COMMAND_NAME_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub(replacement, sanitized)
            matched_any = True

    # Person name patterns (be conservative: only if field suggests a name)
    name_fields = {"from", "to", "signature", "point_of_contact", "via", "poc"}
    if any(nf in str(field_path).lower() for nf in name_fields):
        for pattern, replacement in _PERSON_NAME_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub(replacement, sanitized)
                matched_any = True

    # If nothing matched and the text looks like it might contain sensitive data,
    # fall back to fully redacted
    if not matched_any:
        # Heuristic: if string is long and contains capitalized words that might be names/commands,
        # redact fully
        if len(text) > 3 and re.search(r"[A-Z][a-z]+", text):
            warnings.append("No specific pattern matched; falling back to [REDACTED_VALUE]")
            sanitized = "[REDACTED_VALUE]"

    # Confidence check
    structural_tokens = {"[COMMAND_NAME]", "[ADDRESSEE]", "[SIGNATORY]", "[POC_NAME]",
                        "[POC_PHONE]", "[ORIGINATOR_CODE]", "[UNIT_IDENTITY]",
                        "[EDIPI]", "[SSN]", "[DOD_ID]", "[UIC]",
                        "[HULL_NUMBER]", "[TAIL_NUMBER]", "[BUILDING]", "[ROOM]",
                        "[EMAIL]", "[PHONE]", "[ADDRESS]", "[PERSON_NAME]"}
    # If we ended up with ONLY structural tokens (no original punctuation/words), that's low confidence
    stripped = re.sub(r"\[\w+\]", "", sanitized)
    stripped = re.sub(r"[^A-Za-z0-9]", "", stripped)
    if not stripped.strip() and matched_any:
        confidence = "low"
        warnings.append(
            "Sanitization removed all structural information. "
            "Consider logging as a local command preference instead."
        )
    elif matched_any:
        confidence = "medium"
    else:
        confidence = "low"

    return sanitized, confidence, warnings


def _compute_fingerprint(record: dict[str, Any]) -> str:
    """
    Compute a deterministic fingerprint for duplicate detection.
    Uses (field_path, sanitized_value, doc_type, component, correction_type).
    """
    payload = {
        "field_path": record.get("field_path", ""),
        "sanitized_value": record.get("sanitized_value", ""),
        "doc_type": record.get("doc_type", ""),
        "component": record.get("component", ""),
        "correction_type": record.get("correction_type", ""),
    }
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return h[:16]


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read a JSONL file. Returns (records, warnings)."""
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not path.exists():
        return records, warnings
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                records.append(rec)
            else:
                warnings.append(f"Line {i} in {path.name} is not a dict; skipped")
        except json.JSONDecodeError as exc:
            warnings.append(f"Line {i} in {path.name} JSON parse error: {exc}")
    return records, warnings


def _append_jsonl(path: Path, record: dict[str, Any]) -> list[str]:
    """Append a single JSON record to a JSONL file atomically (read + append + replace)."""
    warnings: list[str] = []
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)
    records.append(record)
    tmp = path.with_suffix(".tmp")
    try:
        lines = [json.dumps(r, ensure_ascii=False) + "\n" for r in records]
        tmp.write_text("".join(lines), encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception as exc:
        warnings.append(f"Failed writing pending log {path.name}: {exc}")
    return warnings


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> list[str]:
    """Atomically overwrite a JSONL file."""
    warnings: list[str] = []
    tmp = path.with_suffix(".tmp")
    try:
        lines = [json.dumps(r, ensure_ascii=False) + "\n" for r in records]
        tmp.write_text("".join(lines), encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception as exc:
        warnings.append(f"Failed writing pending log {path.name}: {exc}")
    return warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_eligible_for_pending_log(correction_record: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check whether a correction record is eligible for pending global rule candidate logging.
    Returns (eligible, reasons).
    """
    reasons: list[str] = []
    eligible = True

    # 1. Classification
    ctype = correction_record.get("correction_type", "unknown")
    if ctype not in _ALLOWED_LOG_TYPES:
        reasons.append(f"Ineligible classification: {ctype}")
        eligible = False

    # 2. Scope
    scope = correction_record.get("scope", "active_draft")
    if scope != "current_session":
        reasons.append(f"Ineligible scope: {scope} (must be current_session)")
        eligible = False

    # 3. Not user-rejected
    if correction_record.get("user_rejected"):
        reasons.append("Correction was previously rejected by user")
        eligible = False

    # 4. No validator conflict
    if correction_record.get("validator_conflict"):
        reasons.append("validator_conflict=True")
        eligible = False

    # 5. Non-empty, non-placeholder corrected value
    corrected_value = correction_record.get("corrected_value")
    if corrected_value is None or str(corrected_value).strip().lower() in _PLACEHOLDER_VALUES:
        reasons.append("Corrected value is empty or placeholder")
        eligible = False

    # 6. Field path not body.*
    field_path = correction_record.get("field_path", "")
    if str(field_path).lower().startswith("body"):
        reasons.append(f"body.* field path excluded from global candidate logging: {field_path}")
        eligible = False

    return eligible, reasons


def propose_pending_log(correction_record: dict[str, Any]) -> dict[str, Any]:
    """
    Step 1: Build a candidate proposal from a correction record.
    Does NOT write to disk. Returns proposal dict with all fields ready for review.
    If ineligible, returns a proposal with eligible=False and reasons.
    """
    eligible, reasons = is_eligible_for_pending_log(correction_record)
    if not eligible:
        return {
            "eligible": False,
            "reasons": reasons,
            "correction_record_id": correction_record.get("correction_id"),
        }

    field_path = correction_record.get("field_path", "")
    corrected_value = correction_record.get("corrected_value", "")
    original_value = correction_record.get("original_value", "")

    ctype = correction_record.get("correction_type", "unknown")

    sanitized_value, sanitization_confidence, sanitization_warnings = _sanitize_value(
        field_path, corrected_value
    )
    original_value_sanitized, _, original_warnings = _sanitize_value(
        field_path, original_value
    )
    sanitization_warnings.extend(original_warnings)

    # Merge classification metadata from correction record
    classification_confidence = correction_record.get("classification_confidence", "medium")
    classification_method = correction_record.get("classification_method", "field_path_keyword")
    if not classification_method:
        classification_method = "field_path_keyword"

    # If sanitization itself is low-confidence, adjust candidate confidence
    if sanitization_confidence == "low":
        classification_confidence = "low"
        sanitization_warnings.append(
            "Low sanitization confidence: candidate may contain mostly local data."
        )

    proposal = {
        "eligible": True,
        "candidate_id": _generate_candidate_id(),
        "recorded_at": _now_utc_iso(),
        "status": "pending",
        "correction_type": ctype,
        "field_path": field_path,
        "sanitized_value": sanitized_value,
        "original_value_sanitized": original_value_sanitized,
        "doc_type": correction_record.get("doc_type", "unknown"),
        "component": correction_record.get("component", "unknown"),
        "user_reason": str(correction_record.get("reason", ""))[:500],
        "classification_confidence": classification_confidence,
        "classification_method": classification_method,
        "source_correction_id": correction_record.get("correction_id", ""),
        "session_id": correction_record.get("session_id", ""),
        "review_metadata": None,
        "duplicate_of": None,
        "sanitization_warnings": sanitization_warnings,
        "fingerprint": _compute_fingerprint({
            "field_path": field_path,
            "sanitized_value": sanitized_value,
            "doc_type": correction_record.get("doc_type", "unknown"),
            "component": correction_record.get("component", "unknown"),
            "correction_type": ctype,
        }),
    }

    return proposal


def confirm_and_write_pending_log(
    proposal: dict[str, Any],
    log_path: Path | None = None,
) -> dict[str, Any]:
    """
    Step 2: After explicit user confirmation, append a sanitized candidate record
    to the pending log JSONL file.

    Returns dict with keys:
        success: bool
        candidate_id: str
        warnings: list[str]
        action: str ("appended" | "skipped_duplicate" | "error")
    """
    warnings: list[str] = []
    path = log_path or _DEFAULT_LOG_PATH

    if not proposal.get("eligible"):
        warnings.append("Proposal is ineligible; not writing.")
        return {"success": False, "candidate_id": None, "warnings": warnings, "action": "error"}

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing records for duplicate detection
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    fingerprint = proposal.get("fingerprint", "")
    dup_record = None
    for r in records:
        if r.get("fingerprint") == fingerprint:
            dup_record = r
            break

    if dup_record:
        dup_status = dup_record.get("status", "")
        if dup_status in ("pending", "under_review"):
            warnings.append(
                f"Duplicate candidate already exists: {dup_record.get('candidate_id')} ({dup_status}). "
                "Skipped append."
            )
            return {
                "success": False,
                "candidate_id": dup_record.get("candidate_id"),
                "warnings": warnings,
                "action": "skipped_duplicate",
            }
        if dup_status == "rejected":
            warnings.append(
                f"Previous candidate was rejected: {dup_record.get('candidate_id')}. "
                "Re-logging requires explicit override."
            )
            return {
                "success": False,
                "candidate_id": dup_record.get("candidate_id"),
                "warnings": warnings,
                "action": "skipped_duplicate",
            }
        if dup_status == "promoted":
            warnings.append(
                f"This candidate was already promoted: {dup_record.get('candidate_id')}. "
                "Adding note only."
            )
            # Append a note-only entry (rare)
            proposal["duplicate_of"] = dup_record.get("candidate_id")
            # Continue to append below

    # Strip non-serializable fields before writing
    record_to_write = copy.deepcopy(proposal)
    record_to_write.pop("eligible", None)
    record_to_write.pop("sanitization_warnings", None)

    # Actually append
    write_warnings = _append_jsonl(path, record_to_write)
    warnings.extend(write_warnings)

    return {
        "success": True,
        "candidate_id": proposal.get("candidate_id"),
        "warnings": warnings,
        "action": "appended",
    }


def list_pending_candidates(
    log_path: Path | None = None,
    correction_type: str | None = None,
    status: str | None = None,
    field_path: str | None = None,
    component: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Read pending candidate records from the log with optional filters.
    Returns (matching_records, warnings).
    """
    warnings: list[str] = []
    path = log_path or _DEFAULT_LOG_PATH
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    filtered: list[dict[str, Any]] = []
    for r in records:
        if correction_type is not None and r.get("correction_type") != correction_type:
            continue
        if status is not None and r.get("status") != status:
            continue
        if field_path is not None and r.get("field_path") != field_path:
            continue
        if component is not None and r.get("component") != component:
            continue
        filtered.append(r)
    return filtered, warnings


def update_candidate_status(
    candidate_id: str,
    new_status: str,
    review_metadata: dict[str, Any] | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """
    Transition a candidate's status and optionally populate review_metadata.
    Returns dict with success, candidate_id, warnings.
    """
    warnings: list[str] = []
    if new_status not in _ALLOWED_STATUSES:
        warnings.append(f"Invalid status: {new_status}")
        return {"success": False, "candidate_id": candidate_id, "warnings": warnings}

    path = log_path or _DEFAULT_LOG_PATH
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    found = False
    for r in records:
        if r.get("candidate_id") == candidate_id:
            r["status"] = new_status
            if review_metadata is not None:
                r["review_metadata"] = copy.deepcopy(review_metadata)
            found = True
            break

    if not found:
        warnings.append(f"Candidate {candidate_id} not found in pending log.")
        return {"success": False, "candidate_id": candidate_id, "warnings": warnings}

    write_warnings = _write_jsonl(path, records)
    warnings.extend(write_warnings)

    return {"success": True, "candidate_id": candidate_id, "warnings": warnings}
