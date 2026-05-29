#!/usr/bin/env python3
"""
CCI Date and Military-Time Validator

Validates date formatting and military time usage in body text and the top-level
date field against SECNAV M-5216.5 Chapter 2 rules.

Public API:
    validate_cci_date_time(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).

CLI:
    python src/cci_date_time_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1),
    or PASS (exit 0) when there are no errors.

Scope:
    - Body text only (body / body_paragraphs).
    - Top-level date field (date).
    - Does NOT inspect subject, reference/enclosure titles, From/To/Via lines,
      sender-symbol block, addresses, signatures, or rendered PDF.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Military time: four digits, 0000-2359, no colon
_MILITARY_TIME_RE = re.compile(r"\b(\d{4})\b")
_MILITARY_TIME_COLON_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")

# Standard military date: day Month year, no leading zero, full 4-digit year
# Examples: "5 May 2026", "15 May 2026", "17 April 2015"
_STANDARD_DATE_RE = re.compile(
    r"\b([1-9]|0[1-9]|[12]\d|3[01])\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)

# Civilian date format: Month day, year  (e.g. "January 14, 2014" or "May 5, 2026")
_CIVILIAN_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+([1-9]\d{0,1}),?\s+(\d{4})\b",
    re.IGNORECASE,
)

# Abbreviated year in standard date pattern: day Month yy (e.g. "15 May 26")
_ABBREV_YEAR_DATE_RE = re.compile(
    r"\b([1-9]|0[1-9]|[12]\d|3[01])\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{2})\b",
    re.IGNORECASE,
)

# ISO / numeric date patterns that are never acceptable in military correspondence text
_ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

_MONTHS_FULL = frozenset([
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _body_text(payload: dict[str, Any]) -> str:
    """Extract all body text into a single string for scanning."""
    for key in ("body", "body_paragraphs"):
        val = payload.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            return " ".join(str(item) for item in val if str(item).strip())
        text = str(val).strip()
        if text:
            return text
    return ""


def _get_date(payload: dict[str, Any]) -> str | None:
    """Extract the top-level date field."""
    val = payload.get("date")
    if val is None:
        return None
    text = str(val).strip()
    return text if text else None


def _is_valid_military_time(token: str) -> bool:
    """Return True if token is a valid four-digit military time (0000-2359)."""
    if len(token) != 4 or not token.isdigit():
        return False
    hours = int(token[:2])
    minutes = int(token[2:])
    return 0 <= hours <= 23 and 0 <= minutes <= 59


def _has_leading_zero_day(date_str: str) -> bool:
    """Check if a date string uses a leading zero for a single-digit day."""
    # Look for patterns like "05 May" or "01 April"
    m = re.search(r"\b0(\d)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b", date_str, re.IGNORECASE)
    return bool(m)


def _is_standard_military_date(date_str: str) -> bool:
    """Return True if date_str matches standard military text date format: day Month year."""
    m = _STANDARD_DATE_RE.match(date_str)
    if not m:
        return False
    day_str = m.group(1)
    month = m.group(2)
    year = m.group(3)
    # Ensure no leading zero on day
    if day_str.startswith("0") and len(day_str) == 2:
        return False
    # Ensure full 4-digit year
    if len(year) != 4:
        return False
    return True

# ---------------------------------------------------------------------------
# Core checks
# ---------------------------------------------------------------------------

def _check_military_time(text: str, errors: list[str], warnings: list[str]) -> None:
    """Scan text for military time compliance."""
    # Check for colon usage first
    for m in _MILITARY_TIME_COLON_RE.finditer(text):
        errors.append(
            f"CCI-DTM-001: military time written with colon — "
            f"'{m.group(0)}' at position {m.start()}; use four digits without colon"
        )

    # Check four-digit bare forms
    for m in _MILITARY_TIME_RE.finditer(text):
        token = m.group(1)
        if not _is_valid_military_time(token):
            hours = int(token[:2])
            minutes = int(token[2:])
            if hours > 23 or minutes > 59:
                errors.append(
                    f"CCI-DTM-002: invalid military time '{token}' — "
                    f"must be four digits from 0000 through 2359"
                )


def _check_date_format(text: str, top_date: str | None, errors: list[str], warnings: list[str]) -> None:
    """Scan body text and top-level date for date formatting compliance."""
    # --- Body text checks ---

    # Leading zero on single-digit day in body
    for m in re.finditer(
        r"\b0(\d)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            f"CCI-DTM-003: leading zero on single-digit day — "
            f"'{m.group(0)}'; do not use leading zero for single-digit day"
        )

    # Civilian date format in body
    for m in _CIVILIAN_DATE_RE.finditer(text):
        warnings.append(
            f"CCI-DTM-005: civilian date format detected in body — "
            f"'{m.group(0)}'; standard military correspondence uses 'day Month year'"
        )

    # Abbreviated year in body
    for m in _ABBREV_YEAR_DATE_RE.finditer(text):
        # Skip if it's actually a full 4-digit year (already matched by _STANDARD_DATE_RE)
        # _ABBREV_YEAR_DATE_RE only matches 2-digit year, so it's safe
        year = m.group(3)
        if len(year) == 2:
            warnings.append(
                f"CCI-DTM-006: abbreviated year detected in body date — "
                f"'{m.group(0)}'; body text should use full four-digit year"
            )

    # ISO / numeric dates in body
    for m in _ISO_DATE_RE.finditer(text):
        errors.append(
            f"CCI-DTM-004: non-standard date format detected in body — "
            f"'{m.group(0)}'; use 'day Month year' format"
        )

    # --- Top-level date field checks ---
    if top_date is not None:
        # Leading zero
        if _has_leading_zero_day(top_date):
            errors.append(
                f"CCI-DTM-003: top-level date uses leading zero on single-digit day — "
                f"'{top_date}'; do not use leading zero for single-digit day"
            )

        # Must be standard military format
        if not _is_standard_military_date(top_date):
            # Check if it's civilian format
            if _CIVILIAN_DATE_RE.search(top_date):
                errors.append(
                    f"CCI-DTM-004: top-level date is not standard military text date format — "
                    f"'{top_date}'; use 'day Month year' with no leading zero and full four-digit year"
                )
            elif _ISO_DATE_RE.search(top_date):
                errors.append(
                    f"CCI-DTM-004: top-level date uses non-standard format — "
                    f"'{top_date}'; use 'day Month year' with no leading zero and full four-digit year"
                )
            else:
                # Ambiguous or unrecognized — warn, not error, in v1
                warnings.append(
                    f"CCI-DTM-007: top-level date '{top_date}' does not match expected "
                    f"'day Month year' format; verify format compliance"
                )


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_cci_date_time(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI date and military-time checks."""
    errors: list[str] = []
    warnings: list[str] = []

    text = _body_text(payload)
    top_date = _get_date(payload)

    _check_military_time(text, errors, warnings)
    _check_date_format(text, top_date, errors, warnings)

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_date_time_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_date_time(payload)

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
