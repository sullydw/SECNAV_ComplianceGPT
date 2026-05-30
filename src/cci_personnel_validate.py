#!/usr/bin/env python3
"""
CCI Personnel Identification Validator

Validates body text for Navy and Marine Corps personnel identification
compliance per SECNAV M-5216.5 Chapter 2.

Public API:
    validate_cci_personnel(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).

CLI:
    python src/cci_personnel_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1),
    or PASS (exit 0) when there are no errors.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Known rank / grade / rate prefixes
# ---------------------------------------------------------------------------

# Navy-like short abbreviations (all-caps or mixed)
NAVY_RANKS_SHORT = frozenset([
    "ADM", "VADM", "RADM", "CAPT", "CDR", "LCDR",
    "LT", "LTJG", "ENS",
    "CWO",
    "SCPO", "CPO", "PO1", "PO2", "PO3", "SN", "SA", "SR",
])

# Marine-like full titles (mixed case)
MARINE_RANKS_FULL = frozenset([
    "General", "Lieutenant General", "Major General", "Brigadier General",
    "Colonel", "Lieutenant Colonel", "Major", "Captain",
    "First Lieutenant", "Second Lieutenant",
    "Sergeant Major", "Master Gunnery Sergeant", "First Sergeant",
    "Master Sergeant", "Gunnery Sergeant", "Staff Sergeant",
    "Sergeant", "Corporal", "Lance Corporal",
    "Private First Class", "Private",
])

# Marine-like abbreviations (mixed case / all-caps)
MARINE_RANKS_SHORT = frozenset([
    "Sgt", "SSgt", "GySgt", "MSgt", "1stSgt", "MGySgt", "SgtMaj",
    "Cpl", "LCpl", "PFC", "Pvt",
])

# Combined for last-name all-caps detection
_ALL_RANK_PREFIXES = frozenset(
    list(NAVY_RANKS_SHORT) + list(MARINE_RANKS_FULL) + list(MARINE_RANKS_SHORT)
)

# For convention-mix detection
_NAVY_INDICATORS = frozenset([
    "ADM", "VADM", "RADM", "CAPT", "CDR", "LCDR", "LT", "LTJG", "ENS",
    "CWO", "SCPO", "CPO", "PO1", "PO2", "PO3", "SN", "SA", "SR",
    "sailor", "sailors", "Sailor", "Sailors",
])

_MARINE_INDICATORS = frozenset([
    "Sgt", "SSgt", "GySgt", "MSgt", "1stSgt", "MGySgt", "SgtMaj",
    "Cpl", "LCpl", "PFC", "Pvt",
    "Sergeant", "Corporal", "Lance Corporal", "Private",
    "marine", "marines", "Marine", "Marines",
])

# Words that disqualify a "marine" token from being a personnel reference
_NON_PERSONNEL_MARINE_PHRASES = frozenset([
    "marine environment", "marine biology", "marine biologist",
    "marine safety", "marine mammals", "marine navigation",
    "marine corps",  # "Marine Corps" is the service name; we still warn lowercase "marine" when standalone
    "marine engineering", "marine corpsman", "marine corpsmen",
])

# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

# SSN pattern (e.g., 123-45-6789, 123456789)
_SSN_RE = re.compile(
    r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    flags=re.IGNORECASE,
)

# EDIPI / DoD ID near-reference heuristic: word boundary digit sequences 10 digits
_EDIPI_RE = re.compile(r"\b\d{10}\b")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_body_text(payload: dict[str, Any]) -> str:
    """Extract body text from payload, joining paragraphs with spaces."""
    body = payload.get("body")
    if body is None:
        body = payload.get("body_paragraphs", [])
    if isinstance(body, list):
        return " ".join(str(p).strip() for p in body)
    if isinstance(body, str):
        return body
    return ""


def _get_component(payload: dict[str, Any]) -> str:
    """Resolve canonical component from payload.

    Accepts component field values:
        navy, marine_corps, joint, unknown
    """
    comp = payload.get("component")
    if comp is None:
        return "unknown"
    comp = str(comp).lower().strip()
    if comp in ("navy", "marine_corps", "joint", "unknown"):
        return comp
    # Light normalization for common synonyms
    if comp in ("usn", "naval"):
        return "navy"
    if comp in ("usmc", "marines"):
        return "marine_corps"
    if comp in ("don_secretariat",):
        return "navy"  # treat as Navy context for personnel
    return "unknown"


def _find_allcaps_last_names(text: str) -> list[str]:
    """Detect last names in ALL CAPS preceded by a known rank/rate/grade.

    Matches both short abbreviations (CDR SMITH) and full titles
    (Captain JONES). Returns a list of match strings.
    """
    found: list[str] = []
    # Pattern: rank prefix (1-3 words) + one or more spaces + ALL-CAPS last name(s)
    # We try two passes: short abbreviations, then full titles.

    # Short abbreviation + all-caps name (1-3 all-caps words)
    short_pattern = re.compile(
        r"\b(" + "|".join(re.escape(r) for r in NAVY_RANKS_SHORT | MARINE_RANKS_SHORT) + r")\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){0,2})\b"
    )
    for match in short_pattern.finditer(text):
        name_part = match.group(2)
        # Heuristic: all-caps last name should not be a common known acronym or rank itself
        tokens = name_part.split()
        bad = False
        for t in tokens:
            if t in _ALL_RANK_PREFIXES:
                bad = True
                break
            if t.isdigit():
                bad = True
                break
        if bad:
            continue
        found.append(match.group(0))

    # Full title + all-caps name (1-3 all-caps words)
    # Full titles may contain spaces; build a lookbehind-like pattern with word boundary logic
    full_titles = sorted(MARINE_RANKS_FULL, key=len, reverse=True)
    full_pattern = re.compile(
        r"\b(" + "|".join(re.escape(r) for r in full_titles) + r")\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){0,2})\b"
    )
    for match in full_pattern.finditer(text):
        name_part = match.group(2)
        tokens = name_part.split()
        bad = False
        for t in tokens:
            if t in _ALL_RANK_PREFIXES:
                bad = True
                break
            if t.isdigit():
                bad = True
                break
        if bad:
            continue
        found.append(match.group(0))

    return found


def _check_lowercase_sailor_marine(text: str) -> list[str]:
    """Detect lowercase 'sailor', 'marine', or 'service member' used as personnel references.

    Skips non-personnel phrases such as 'marine environment', 'marine biology',
    'marine safety', 'marine mammals', 'marine navigation'.
    """
    found: list[str] = []
    # Target tokens that suggest personnel reference
    # sailor, sailors, marine, marines, service member, service members
    pattern = re.compile(
        r"(?i)\b(sailor|sailors|marine|marines)\b",
    )
    for match in pattern.finditer(text):
        token = match.group(1).lower()
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        context_window = text[start:end]
        lower_context = context_window.lower()

        # If the token is lowercase, and context does not contain a non-personnel phrase
        if token in ("sailor", "sailors", "marine", "marines"):
            # Skip if embedded in non-personnel phrase
            skip = False
            for phrase in _NON_PERSONNEL_MARINE_PHRASES:
                if phrase.lower() in lower_context:
                    skip = True
                    break
            # Also skip "marine corps" when talking about the service as an institution
            if not skip and "marine corps" in lower_context:
                # We still flag if the standalone "marine" is lowercase and not part of "Marine Corps" proper capitalization
                pass  # handled above by phrase list if phrase is in list
            if not skip:
                # Do not flag "Marine" when capitalized (that is correct)
                if match.group(0).istitle():
                    # Capitalized is correct; skip
                    continue
                # All-caps MARINE is acceptable when capitalized; skip uppercase
                if match.group(0).isupper():
                    continue
                found.append(match.group(0))
    return found


def _check_convention_mix(text: str, component: str) -> list[str]:
    """Detect possible Navy / Marine Corps convention mix.

    Conservative heuristic: if both Navy and Marine Corps rank indicators appear
    in the same body and component is not 'joint', warn.
    """
    found: list[str] = []
    navy_found = False
    marine_found = False

    # Check for Navy rank indicators
    for indicator in _NAVY_INDICATORS:
        pattern = re.compile(rf"\b{re.escape(indicator)}\b", flags=re.IGNORECASE)
        if pattern.search(text):
            navy_found = True
            break

    # Check for Marine Corps rank indicators
    for indicator in _MARINE_INDICATORS:
        pattern = re.compile(rf"\b{re.escape(indicator)}\b", flags=re.IGNORECASE)
        if pattern.search(text):
            marine_found = True
            break

    if navy_found and marine_found:
        if component not in ("joint",):
            found.append(
                "possible Navy/Marine Corps convention mix detected: "
                "both Navy and Marine Corps rank indicators appear in body text "
                f"but component is '{component}'"
            )
    return found


def _check_ssn(text: str) -> list[tuple[int, int]]:
    """Return list of (start, end) for SSN-like patterns."""
    return [(m.start(), m.end()) for m in _SSN_RE.finditer(text)]


def _check_edipi(text: str) -> list[tuple[int, int]]:
    """Return list of (start, end) for 10-digit number patterns near EDIPI references."""
    found: list[tuple[int, int]] = []
    # Look for 10-digit numbers that appear near words like EDIPI, DOD ID, DoD ID
    for match in _EDIPI_RE.finditer(text):
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        context = text[start:end]
        if re.search(r"(?i)EDIPI|DoD\s*ID|DOD\s*ID|DoD\s*Identification|service\s*number", context):
            found.append((match.start(), match.end()))
    return found


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_cci_personnel(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI personnel identification checks."""
    errors: list[str] = []
    warnings: list[str] = []

    body_text = _get_body_text(payload)
    component = _get_component(payload)

    # --- Hard errors ---------------------------------------------------------

    allcaps_names = _find_allcaps_last_names(body_text)
    if allcaps_names:
        # Deduplicate
        unique = list(dict.fromkeys(allcaps_names))
        errors.append(
            f"CCI-PER-001: last name appears in all caps after known rank/rate/grade "
            f"— {', '.join(repr(u) for u in unique)}"
        )

    # --- Warnings ------------------------------------------------------------

    lower_personnel = _check_lowercase_sailor_marine(body_text)
    if lower_personnel:
        unique = list(dict.fromkeys(lower_personnel))
        warnings.append(
            f"CCI-PER-002: lowercase Sailor/Marine/Service Member detected in body "
            f"— {', '.join(repr(u) for u in unique)}"
        )

    convention_mix = _check_convention_mix(body_text, component)
    if convention_mix:
        warnings.extend(
            f"CCI-PER-003: {msg}" for msg in convention_mix
        )

    ssn_spans = _check_ssn(body_text)
    if ssn_spans:
        # Do not print the actual SSN values; report count and positions
        warnings.append(
            f"CCI-PER-004: possible Social Security Number pattern detected "
            f"in body text ({len(ssn_spans)} occurrence{'s' if len(ssn_spans) > 1 else ''})"
        )

    edipi_spans = _check_edipi(body_text)
    if edipi_spans:
        warnings.append(
            f"CCI-PER-005: possible EDIPI/DoD ID reference detected "
            f"in body text ({len(edipi_spans)} occurrence{'s' if len(edipi_spans) > 1 else ''})"
        )

    # CCI-PER-006: component unknown when personnel context is present
    if component == "unknown":
        # Only warn if we found any personnel-related indicator in the body
        has_personnel_context = bool(
            allcaps_names or lower_personnel or convention_mix or ssn_spans or edipi_spans
        )
        if not has_personnel_context:
            # Also check for any rank/grade mention at all
            for r in _ALL_RANK_PREFIXES:
                if re.search(rf"\b{re.escape(r)}\b", body_text, flags=re.IGNORECASE):
                    has_personnel_context = True
                    break
        if has_personnel_context:
            warnings.append(
                "CCI-PER-006: personnel identification appears present "
                "but component is unknown or missing"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_personnel_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_personnel(payload)

    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        for e in errors:
            print(f"FAIL\n  ERROR: {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
