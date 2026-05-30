#!/usr/bin/env python3
"""
CCI Routing / Via / Copy-to Intelligence Validator

Validates routing metadata against Correspondence Content Intelligence rules
for SECNAV M-5216.5 Via numbering, Copy-to need-to-know, and Distribution
format intelligence.

Public API:
    validate_cci_routing(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).  This v1 validator is warnings-only.

CLI:
    python src/cci_routing_validate.py <payload.json>

    Prints any WARNING lines first, then PASS (exit 0).
    Warnings alone never cause exit 1 in v1.

Scope:
    - Read-only. Does not modify payload.
    - Body-agnostic routing metadata checks only.
    - Does NOT inspect rendered PDF layout.
    - Does NOT validate C8 structural field correctness (c8_validate.py owns that).
    - Does NOT validate C9 endorsement-specific copy_to completeness
      (c9_validate.py owns that).
    - Does NOT perform real chain-of-command validation.

Field normalization:
    - via: accepts string or list, normalizes to list
    - copy_to / copyto / copy: accepts string or list, normalizes to list
    - distribution: accepts string or list, normalizes to list
    - to: accepts string or list, normalizes to list
    - distribution_mode: used if present
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

_VAGUE_COPY_TO_PHRASES = frozenset([
    "all hands",
    "distribution",
    "all concerned",
    "interested parties",
    "file",
    "anyone concerned",
    "as required",
    "as needed",
    "concerned parties",
    "all parties",
])

_VAGUE_VIA_PHRASES = frozenset([
    "through appropriate channels",
    "via appropriate channels",
    "through chain of command",
    "via chain of command",
    "as required",
    "as needed",
    "through proper channels",
    "via proper channels",
    "routine routing",
    "standard routing",
])

# Field aliases
_VIA_FIELD_NAMES = frozenset(["via"])
_COPY_TO_FIELD_NAMES = frozenset(["copy_to", "copyto", "copy"])
_DISTRIBUTION_FIELD_NAMES = frozenset(["distribution"])
_TO_FIELD_NAMES = frozenset(["to"])

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _normalize_list(value: Any) -> list[str]:
    """Normalize a field into a clean list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _get_field(payload: dict[str, Any], names: frozenset[str]) -> Any:
    """Return the first encountered field value from the given name set."""
    for name in names:
        val = payload.get(name)
        if val is not None:
            return val
    return None


def _normalize_for_match(text: str) -> str:
    """Normalize text for case-insensitive, whitespace-collapsed comparison."""
    return " ".join(str(text).lower().split())


# -------------------------------------------------------------------------
# Via checks
# -------------------------------------------------------------------------

def _check_via(payload: dict[str, Any], warnings: list[str]) -> None:
    """Check Via numbering and specificity."""
    via_raw = _get_field(payload, _VIA_FIELD_NAMES)
    via_entries = _normalize_list(via_raw)

    if not via_entries:
        return

    # Rule 003: single Via should not be numbered
    if len(via_entries) == 1:
        entry = via_entries[0]
        if re.search(r"^\s*\(\s*\d+\s*\)", entry):
            warnings.append(
                f"CCI-ROUTE-003: single Via addressee is numbered {entry!r}; "
                f"a single Via line normally should not be numbered"
            )
        _check_via_vague(entry, warnings)
        return

    # Multiple Via entries: check numbering
    numbers_found: list[tuple[int, int, str]] = []  # (number, index, entry)
    for i, entry in enumerate(via_entries, start=1):
        m = re.search(r"^\s*\(\s*(\d+)\s*\)", entry)
        if m:
            numbers_found.append((int(m.group(1)), i, entry))
        _check_via_vague(entry, warnings)

    if not numbers_found:
        # Rule 001: multiple Via entries but no numbering at all
        warnings.append(
            "CCI-ROUTE-001: multiple Via addressees exist but none are numbered; "
            "number Via entries in routing order beginning with (1)"
        )
        return

    if len(numbers_found) < len(via_entries):
        # Some entries numbered, some not
        unnumbered = [e for e in via_entries if not re.search(r"^\s*\(\s*\d+\s*\)", e)]
        warnings.append(
            f"CCI-ROUTE-001: {len(unnumbered)} of {len(via_entries)} Via addressees "
            f"are not numbered; all Via entries must be numbered when multiple exist"
        )

    # Rule 002: numbering should start at (1) and be consecutive
    expected = 1
    for num, idx, entry in numbers_found:
        if num != expected:
            warnings.append(
                f"CCI-ROUTE-002: Via numbering at entry {idx} is ({num}) but "
                f"expected ({expected}); numbering must start at (1) and be consecutive"
            )
        expected = num + 1


def _check_via_vague(entry: str, warnings: list[str]) -> None:
    """Check if Via text contains vague routing phrases."""
    lower = _normalize_for_match(entry)
    for phrase in _VAGUE_VIA_PHRASES:
        if phrase in lower:
            warnings.append(
                f"CCI-ROUTE-004: Via entry {entry!r} contains vague routing phrase "
                f"{phrase!r}; name specific addressees rather than generic routing"
            )
            break  # Only warn once per entry


# -------------------------------------------------------------------------
# Copy-to checks
# -------------------------------------------------------------------------

def _check_copy_to(payload: dict[str, Any], warnings: list[str]) -> None:
    """Check Copy-to list size, specificity, and duplication with To/Via."""
    copy_raw = _get_field(payload, _COPY_TO_FIELD_NAMES)
    copy_entries = _normalize_list(copy_raw)

    if not copy_entries:
        return

    # Rule 005: excessive copy-to list
    if len(copy_entries) > 6:
        warnings.append(
            f"CCI-ROUTE-005: Copy-to list has {len(copy_entries)} entries; "
            f"verify all recipients have a need to know"
        )

    # Rule 006: vague entries
    for i, entry in enumerate(copy_entries, start=1):
        lower = _normalize_for_match(entry)
        for phrase in _VAGUE_COPY_TO_PHRASES:
            if phrase in lower:
                warnings.append(
                    f"CCI-ROUTE-006: Copy-to entry {i} {entry!r} is vague or overly broad "
                    f"({phrase!r}); use specific addressees"
                )
                break

    # Rule 007: duplication with To or Via
    to_entries = _normalize_list(_get_field(payload, _TO_FIELD_NAMES))
    via_entries = _normalize_list(_get_field(payload, _VIA_FIELD_NAMES))

    for i, entry in enumerate(copy_entries, start=1):
        entry_norm = _normalize_for_match(entry)
        for to_entry in to_entries:
            if _normalize_for_match(to_entry) == entry_norm:
                warnings.append(
                    f"CCI-ROUTE-007: Copy-to entry {i} {entry!r} duplicates To line "
                    f"addressee {to_entry!r}; verify role is not duplicated"
                )
                break
        for via_entry in via_entries:
            if _normalize_for_match(via_entry) == entry_norm:
                warnings.append(
                    f"CCI-ROUTE-007: Copy-to entry {i} {entry!r} duplicates Via line "
                    f"addressee {via_entry!r}; verify role is not duplicated"
                )
                break


# -------------------------------------------------------------------------
# Distribution checks
# -------------------------------------------------------------------------

def _check_distribution(payload: dict[str, Any], warnings: list[str]) -> None:
    """Check Distribution format intelligence (not C8 structural correctness)."""
    dist_mode = payload.get("distribution_mode")
    dist_raw = _get_field(payload, _DISTRIBUTION_FIELD_NAMES)
    dist_entries = _normalize_list(dist_raw)

    if dist_mode == "distribution_only":
        # Rule 008: distribution_only with <=4 entries is unusual
        if 1 <= len(dist_entries) <= 4:
            warnings.append(
                f"CCI-ROUTE-008: distribution_only mode with {len(dist_entries)} "
                f"entries is unusual; consider To-line format unless copy variation "
                f"or other reason exists"
            )

    elif dist_mode == "to_plus_distribution":
        # Rule 009: check for group title in To and individuals in Distribution
        to_raw = _get_field(payload, _TO_FIELD_NAMES)
        to_entries = _normalize_list(to_raw)

        if not to_entries:
            warnings.append(
                "CCI-ROUTE-009: to_plus_distribution mode but no To line present; "
                "a group title should appear in the To line"
            )
        elif len(to_entries) > 1:
            # To is a list with multiple entries in to_plus_distribution — unusual
            warnings.append(
                "CCI-ROUTE-009: to_plus_distribution mode but To line contains "
                "multiple entries; To should contain a single group title"
            )

        if not dist_entries:
            warnings.append(
                "CCI-ROUTE-009: to_plus_distribution mode but Distribution line is "
                "missing or empty; individual members should be listed in Distribution"
            )


# -------------------------------------------------------------------------
# Public function
# -------------------------------------------------------------------------

def validate_cci_routing(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI routing/Via/Copy-to checks.

    v1 is warnings-only; errors list is always empty.
    """
    errors: list[str] = []
    warnings: list[str] = []

    _check_via(payload, warnings)
    _check_copy_to(payload, warnings)
    _check_distribution(payload, warnings)

    return errors, warnings


# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_routing_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_routing(payload)

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
