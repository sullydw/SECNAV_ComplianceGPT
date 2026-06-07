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
# Phase H.4: Office-Code Prefix Advisory Check
# -------------------------------------------------------------------------

def _check_office_code_prefix(addressee: str) -> list[str]:
    """
    CCI-ROUTE-010: Office Code Prefix Rule (advisory/non-blocking).
    Source: SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General.
    Quote: "If the office code is composed of only numbers, add the word
    'Code' before the numbers. Do not add the word 'Code' before an office
    code that starts with a letter (e.g., 'N' or 'SUP')."

    Returns a list of advisory warning strings.  Empty list means no finding.
    """
    findings: list[str] = []
    text = addressee.strip()
    if not text:
        return findings

    candidate: str | None = None
    is_parenthetical: bool = False

    # Parenthetical form: "Commanding Officer (123)" or "Commanding Officer (Code N1)"
    m = re.search(r"\(([^)]*)\)\s*$", text)
    if m:
        candidate = m.group(1).strip()
        is_parenthetical = True
    else:
        # Comma-delimited form: "Commanding Officer, 123" or "Commanding Officer, Code N1"
        if "," in text:
            parts = text.rsplit(",", 1)
            candidate = parts[-1].strip()
        # No comma and no parentheses -> not an office-code candidate

    if not candidate:
        return findings

    # Tokenize candidate on whitespace to isolate the last token as potential office code
    tokens = candidate.split()
    if not tokens:
        return findings

    code_token: str = tokens[-1]

    # Length guard
    if not (1 <= len(code_token) <= 10):
        return findings

    # Determine whether the candidate starts with "Code " (case-insensitive)
    prefix_lower = candidate.lower()
    has_code_prefix: bool = prefix_lower.startswith("code ")

    if has_code_prefix:
        # The code is the second token after "Code"
        code_parts = candidate.split()
        if len(code_parts) >= 2:
            code_token = code_parts[1]
        else:
            return findings

    # Check A: numeric-only office code missing "Code" prefix
    if re.fullmatch(r"\d+", code_token):
        if not has_code_prefix:
            mode = "parenthetical" if is_parenthetical else "comma-delimited"
            findings.append(
                f"CCI-ROUTE-010 (advisory): numeric office code missing 'Code' prefix: "
                f"{code_token!r} in addressee {addressee!r} — SECNAV M-5216.5 Ch7 para 7-2.7a "
                f"[{mode}]"
            )
        return findings

    # Check B: letter-starting office code improperly prefixed with "Code"
    if code_token and code_token[0].isalpha():
        if has_code_prefix:
            mode = "parenthetical" if is_parenthetical else "comma-delimited"
            findings.append(
                f"CCI-ROUTE-010 (advisory): letter-starting office code should not use "
                f"'Code' prefix: {code_token!r} in addressee {addressee!r} — "
                f"SECNAV M-5216.5 Ch7 para 7-2.7a [{mode}]"
            )
        return findings

    return findings


# -------------------------------------------------------------------------
# Phase H.9: From-Line Required Advisory Check
# -------------------------------------------------------------------------

def _check_from_line_required(payload: dict[str, Any]) -> list[str]:
    """
    CCI-ROUTE-011: From-Line Required Rule (advisory/non-blocking).
    Source: SECNAV M-5216.5, Chapter 7, Section 6, "From:" Line, subparagraph a. General.
    Quote: "Every standard letter must have a 'From:' line, except a letter
    that will be used with a window envelope."

    Approved record: agr_20260607_49947aca.
    Implementation target: validator_update (Phase H.9).

    Checks that a standard letter has a non-empty "from" field, unless
    the letter uses a window envelope (window_envelope=true).

    Advisory (non-blocking) until separately promoted.

    H.9 reads window_envelope only if present; does not create, populate,
    or prompt for the key. Full lifecycle support deferred to a later
    separately approved phase.
    """
    findings: list[str] = []

    # Scope: standard letter only
    doc_type = payload.get("doc_type", "")
    if doc_type not in ("DT_STD_LTR", "standard_letter"):
        return findings

    # Window-envelope exception — read-only, key must already exist
    if payload.get("window_envelope", False):
        return findings

    # Check for From line
    from_value = payload.get("from")
    if from_value is None or not str(from_value).strip():
        findings.append(
            'CCI-ROUTE-011 (advisory): standard letter missing "From:" line '
            "— SECNAV M-5216.5 Ch7 Section 6 \"From:\" Line, subparagraph a. General. "
            "If this letter uses a window envelope, set window_envelope=true "
            "or mark the payload appropriately in a future approved workflow "
            "to suppress this advisory."
        )

    return findings


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

    # Phase H.4: Advisory office-code prefix checks for To and Via lines
    to_raw = _get_field(payload, _TO_FIELD_NAMES)
    for addressee in _normalize_list(to_raw):
        for finding in _check_office_code_prefix(addressee):
            warnings.append(finding)

    via_raw = _get_field(payload, _VIA_FIELD_NAMES)
    for addressee in _normalize_list(via_raw):
        for finding in _check_office_code_prefix(addressee):
            warnings.append(finding)

    # Phase H.9: Advisory From-line required check
    for finding in _check_from_line_required(payload):
        warnings.append(finding)

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
