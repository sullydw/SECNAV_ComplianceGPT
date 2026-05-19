#!/usr/bin/env python3
"""
C10 Memorandum Validator

Checks for DT_MEMO_MFR (Memorandum for the Record):
    C10-001  require `date`, require `title`, and title must equal
             "MEMORANDUM FOR THE RECORD".
    C10-002  require `signer_name` and `signer_org_code`.
    C10-003  `subj` is optional. If missing and `file_copy_mfr` is not true,
             return a warning only. If `file_copy_mfr` is true, no warning.
    C10-004  require non-empty `body` list. Every body entry must be a string
             and must start with one of: "1. ", "a. ", "(1) ", "(a) ".
             Reject nested body objects.
    C10-005  MFR must not include non-empty standard-letter-only fields:
             `from`, `to`, `via`, `ref`, `encl`, `distribution`, `copy_to`,
             `ssic`, `originator_code`, `unit_identity`.

Checks for DT_MEMO_FROM_TO_PLAIN (Plain-Paper From-To Memorandum):
    C10-101  require non-empty `date`, `from`, `to`, and `subj`.
    C10-102  require non-empty `body` list; every body entry must be a string
             and must start with one of: "1. ", "a. ", "(1) ", "(a) ".
    C10-103  require `signature` dict with `name`, `role`, and `title`
             (title required when role is `principal_subordinate_by_title`).
    C10-104  if `ref` exists and is non-empty, every ref entry must be a string
             matching "(a) Text", "(b) Text", etc. (one space after marker).
    C10-105  if `encl` exists and is non-empty, every encl entry must be a string
             matching "(1) Text", "(2) Text", etc. (one space after marker).
    C10-106  From-To plain memo must not include non-empty fields:
             `unit_identity`, `ssic`, `originator_code`, `distribution`,
             `file_copy_mfr`, `title`.

Public API:
    validate_c10(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings). Warnings alone do not constitute failure.
    validate_c10_from_to_plain(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings) for DT_MEMO_FROM_TO_PLAIN validation.

CLI:
    python src/c10_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1), or PASS
    (exit 0) when there are no errors.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Valid body paragraph marker patterns
_BODY_MARKER_PATTERN = re.compile(r'^(\d+\. |[a-z]\. |\(\d+\) |\([a-z]+\) )')

# Reference marker pattern: (a), (b), (c), etc.
_REF_MARKER_PATTERN = re.compile(r'^\([a-z]\) ')

# Enclosure marker pattern: (1), (2), (3), etc.
_ENCL_MARKER_PATTERN = re.compile(r'^\(\d+\) ')

# Standard-letter-only fields that MFR must not include
_MFR_FORBIDDEN_FIELDS = (
    "from",
    "to",
    "via",
    "ref",
    "encl",
    "distribution",
    "copy_to",
    "ssic",
    "originator_code",
    "unit_identity",
)

# From-To forbidden fields (not applicable to plain-paper From-To memos)
_FROM_TO_FORBIDDEN_FIELDS = (
    "unit_identity",
    "ssic",
    "originator_code",
    "distribution",
    "file_copy_mfr",
    "title",
)


def _is_empty(value: Any) -> bool:
    """Check if a field value should be treated as empty.
    
    Empty: missing, None, empty/whitespace string, empty list, empty dict
    Non-empty: non-empty string, non-empty list, non-empty dict, any other non-null value
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    # Any other non-null value is treated as non-empty
    return False


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_c10_from_to_plain(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for C10 From-To plain-paper memo validation checks."""

    errors: list[str] = []
    warnings: list[str] = []

    # --- C10-101: Required fields (date, from, to, subj) ----------------

    date = payload.get("date")
    if not date or not str(date).strip():
        errors.append("C10-101: From-To memo must include a non-empty 'date' field")

    from_line = payload.get("from")
    if not from_line or not str(from_line).strip():
        errors.append("C10-101: From-To memo must include a non-empty 'from' field")

    to_line = payload.get("to")
    if not to_line or not str(to_line).strip():
        errors.append("C10-101: From-To memo must include a non-empty 'to' field")

    subj = payload.get("subj")
    if not subj or not str(subj).strip():
        errors.append("C10-101: From-To memo must include a non-empty 'subj' field")

    # --- C10-102: Body format checks ------------------------------------

    body = payload.get("body")

    if body is None:
        errors.append("C10-102: From-To memo must include a 'body' field")
    elif not isinstance(body, list):
        errors.append(
            f"C10-102: From-To memo 'body' must be a list of strings, "
            f"got {type(body).__name__}"
        )
    elif len(body) == 0:
        errors.append("C10-102: From-To memo 'body' list must not be empty")
    else:
        # Check each body entry is a string with valid marker prefix
        for i, entry in enumerate(body, start=1):
            if not isinstance(entry, str):
                errors.append(
                    f"C10-102: body entry {i} must be a string, "
                    f"got {type(entry).__name__}"
                )
                continue

            if not entry.strip():
                errors.append(f"C10-102: body entry {i} must not be empty")
                continue

            # Check for valid marker prefix using regex pattern
            has_valid_marker = _BODY_MARKER_PATTERN.match(entry)
            if not has_valid_marker:
                errors.append(
                    f"C10-102: body entry {i} must start with a valid marker "
                    f"prefix (e.g., '1. ', 'a. ', '(1) ', '(a) '), "
                    f"got {entry[:40]!r}..."
                )

    # --- C10-103: Signature checks --------------------------------------

    signature = payload.get("signature")

    if signature is None:
        errors.append("C10-103: From-To memo must include a 'signature' field")
    elif not isinstance(signature, dict):
        errors.append(
            f"C10-103: From-To memo 'signature' must be a dict, "
            f"got {type(signature).__name__}"
        )
    else:
        sig_name = signature.get("name")
        if not sig_name or not str(sig_name).strip():
            errors.append("C10-103: signature must include a non-empty 'name' field")

        sig_role = signature.get("role")
        if not sig_role or not str(sig_role).strip():
            errors.append("C10-103: signature must include a non-empty 'role' field")

        sig_title = signature.get("title")
        if sig_role == "principal_subordinate_by_title":
            if not sig_title or not str(sig_title).strip():
                errors.append(
                    "C10-103: signature must include a non-empty 'title' field "
                    "when role is 'principal_subordinate_by_title'"
                )

    # --- C10-104: Reference format checks -------------------------------

    ref = payload.get("ref")
    if ref is not None and not _is_empty(ref):
        if not isinstance(ref, list):
            errors.append(
                f"C10-104: 'ref' must be a list of strings, "
                f"got {type(ref).__name__}"
            )
        elif len(ref) == 0:
            pass  # Empty ref list is acceptable
        else:
            for i, entry in enumerate(ref, start=1):
                if not isinstance(entry, str):
                    errors.append(
                        f"C10-104: ref entry {i} must be a string, "
                        f"got {type(entry).__name__}"
                    )
                    continue

                if not entry.strip():
                    errors.append(f"C10-104: ref entry {i} must not be empty")
                    continue

                # Check for valid ref marker pattern: (a) , (b) , etc.
                if not _REF_MARKER_PATTERN.match(entry):
                    errors.append(
                        f"C10-104: ref entry {i} must start with a valid ref marker "
                        f"(e.g., '(a) ', '(b) '), "
                        f"got {entry[:40]!r}..."
                    )

    # --- C10-105: Enclosure format checks -------------------------------

    encl = payload.get("encl")
    if encl is not None and not _is_empty(encl):
        if not isinstance(encl, list):
            errors.append(
                f"C10-105: 'encl' must be a list of strings, "
                f"got {type(encl).__name__}"
            )
        elif len(encl) == 0:
            pass  # Empty encl list is acceptable
        else:
            for i, entry in enumerate(encl, start=1):
                if not isinstance(entry, str):
                    errors.append(
                        f"C10-105: encl entry {i} must be a string, "
                        f"got {type(entry).__name__}"
                    )
                    continue

                if not entry.strip():
                    errors.append(f"C10-105: encl entry {i} must not be empty")
                    continue

                # Check for valid encl marker pattern: (1) , (2) , etc.
                if not _ENCL_MARKER_PATTERN.match(entry):
                    errors.append(
                        f"C10-105: encl entry {i} must start with a valid encl marker "
                        f"(e.g., '(1) ', '(2) '), "
                        f"got {entry[:40]!r}..."
                    )

    # --- C10-106: From-To must not include forbidden fields -------------

    for field_name in _FROM_TO_FORBIDDEN_FIELDS:
        field_value = payload.get(field_name)
        if not _is_empty(field_value):
            errors.append(
                f"C10-106: From-To memo must not include non-empty '{field_name}' field "
                f"(not applicable to plain-paper From-To memos)"
            )

    return errors, warnings


def validate_c10(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for C10 validation, routing by doc_type."""

    doc_type = payload.get("doc_type")

    if doc_type == "DT_MEMO_MFR":
        # Existing MFR validation logic
        return _validate_c10_mfr(payload)
    elif doc_type == "DT_MEMO_FROM_TO_PLAIN":
        # New From-To plain-paper memo validation
        return validate_c10_from_to_plain(payload)
    else:
        # Unrecognized doc_type: no errors, no warnings
        return [], []


def _validate_c10_mfr(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for C10 MFR validation checks (internal function)."""

    errors: list[str] = []
    warnings: list[str] = []

    # --- C10-001: Date and title checks -----------------------------------

    date = payload.get("date")
    if not date or not str(date).strip():
        errors.append("C10-001: MFR must include a non-empty 'date' field")

    title = payload.get("title")
    if not title or not str(title).strip():
        errors.append("C10-001: MFR must include a non-empty 'title' field")
    elif str(title).strip() != "MEMORANDUM FOR THE RECORD":
        errors.append(
            f"C10-001: MFR title must be 'MEMORANDUM FOR THE RECORD', "
            f"got {str(title).strip()!r}"
        )

    # --- C10-002: Signer checks -------------------------------------------

    signer_name = payload.get("signer_name")
    if not signer_name or not str(signer_name).strip():
        errors.append("C10-002: MFR must include a non-empty 'signer_name' field")

    signer_org_code = payload.get("signer_org_code")
    if not signer_org_code or not str(signer_org_code).strip():
        errors.append("C10-002: MFR must include a non-empty 'signer_org_code' field")

    # --- C10-003: Subject optional with file_copy_mfr check ---------------

    subj = payload.get("subj")
    file_copy_mfr = payload.get("file_copy_mfr")

    has_subj = subj is not None and str(subj).strip()
    is_file_copy = file_copy_mfr is True

    if not has_subj and not is_file_copy:
        warnings.append(
            "C10-003: MFR missing 'subj' field; consider adding subject "
            "unless this is a file copy (file_copy_mfr: true)"
        )

    # --- C10-004: Body format checks --------------------------------------

    body = payload.get("body")

    if body is None:
        errors.append("C10-004: MFR must include a 'body' field")
    elif not isinstance(body, list):
        errors.append(
            f"C10-004: MFR 'body' must be a list of strings, "
            f"got {type(body).__name__}"
        )
    elif len(body) == 0:
        errors.append("C10-004: MFR 'body' list must not be empty")
    else:
        # Check each body entry is a string with valid marker prefix
        for i, entry in enumerate(body, start=1):
            if not isinstance(entry, str):
                errors.append(
                    f"C10-004: body entry {i} must be a string, "
                    f"got {type(entry).__name__}"
                )
                continue

            if not entry.strip():
                errors.append(f"C10-004: body entry {i} must not be empty")
                continue

            # Check for valid marker prefix using regex pattern
            has_valid_marker = _BODY_MARKER_PATTERN.match(entry)
            if not has_valid_marker:
                errors.append(
                    f"C10-004: body entry {i} must start with a valid marker "
                    f"prefix (e.g., '1. ', 'a. ', '(1) ', '(a) '), "
                    f"got {entry[:40]!r}..."
                )

    # --- C10-005: MFR must not include standard-letter-only fields ------

    for field_name in _MFR_FORBIDDEN_FIELDS:
        field_value = payload.get(field_name)
        if not _is_empty(field_value):
            errors.append(
                f"C10-005: MFR must not include non-empty '{field_name}' field "
                f"(standard-letter-only field)"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/c10_validate.py <payload.json>", file=sys.stderr)
        return 2

    input_path = Path(argv[1])
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        return 2

    try:
        with input_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Failed to read payload: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_c10(payload)

    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
