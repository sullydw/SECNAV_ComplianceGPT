#!/usr/bin/env python3
"""
C10 Memorandum for the Record (MFR) Validator

Checks:
    C10-001  require `date`, require `title`, and title must equal
             "MEMORANDUM FOR THE RECORD".
    C10-002  require `signer_name` and `signer_org_code`.
    C10-003  `subj` is optional. If missing and `file_copy_mfr` is not true,
             return a warning only. If `file_copy_mfr` is true, no warning.
    C10-004  require non-empty `body` list. Every body entry must be a string
             and must start with one of: "1. ", "a. ", "(1) ", "(a) ".
             Reject nested body objects.
    C10-005  (reserved for future MFR-specific rules)

Public API:
    validate_c10(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings). Warnings alone do not constitute failure.

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


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_c10(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for C10 MFR validation checks."""

    errors: list[str] = []
    warnings: list[str] = []

    # Only validate MFR payloads
    if payload.get("doc_type") != "DT_MEMO_MFR":
        return errors, warnings

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
