#!/usr/bin/env python3
"""
CCI Acronym First-Use Validator

Validates acronym usage in body text against Correspondence Content Intelligence
rules for SECNAV M-5216.5 abbreviation and acronym handling.

Public API:
    validate_cci_acronyms(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).

CLI:
    python src/cci_acronym_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1),
    or PASS (exit 0) when there are no errors.

Scope:
    - Body text only (body / body_paragraphs).
    - Does NOT inspect subject, reference titles, enclosure titles,
      From/To/Via lines, addresses, or signatures.
    - Approved acronyms may be used without definition but generate a warning.
    - Non-approved acronyms must be defined on first use: "Full Name (ACR)".
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

APPROVED_ACRONYMS = frozenset([
    "SECNAV",
    "DON",
    "USN",
    "USMC",
    "DoD",
    "NATO",
    "SSIC",
    "MCO",
    "OPNAV",
    "NAVMC",
    "CNO",
    "CMC",
    "FOIA",
    "PII",
    "CUI",
    "FOUO",
])

# Match probable acronyms: all-caps tokens of 2+ letters
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")

# Common English words that appear in all-caps text but are not acronyms
_COMMON_UPPER_WORDS = frozenset([
    "AND", "THE", "FOR", "WITH", "FROM", "TO", "OF", "IN", "ON", "AT", "BY",
    "OR", "NOT", "BUT", "AN", "A", "AS", "IS", "IT", "BE", "ARE", "WAS",
    "WERE", "BEEN", "HAVE", "HAS", "HAD", "DO", "DOES", "DID", "WILL",
    "WOULD", "SHOULD", "COULD", "MAY", "MIGHT", "CAN", "THIS", "THAT",
    "THESE", "THOSE", "UPON", "OVER", "UNDER", "INTO", "THROUGH", "DURING",
    "BEFORE", "AFTER", "ABOVE", "BELOW", "BETWEEN", "WITHIN", "WITHOUT",
])

# Header/label tokens to ignore when scanning body text
_LABEL_WORDS = frozenset([
    "REF", "ENCL", "SUBJ", "VIA", "FROM", "TO", "COPY", "DISTRIBUTION",
    "MEMORANDUM", "RECORD",
])

# Regex to detect a definition pattern like "Full Words (ACRONYM)"
_DEFINITION_RE_TEMPLATE = r"\b[A-Za-z][A-Za-z\s,\-&\.]+\s+\(" + re.escape("{token}") + r"\)"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _body_text(payload: dict[str, Any]) -> str:
    """Extract all body text into a single string for full-text scanning."""
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


def _candidate_acronyms(text: str) -> list[tuple[str, int]]:
    """Return list of (token, position) for candidate acronyms in text.

    Excludes common English words, header labels, and approved acronyms.
    Position is character offset of the match start.
    """
    found: list[tuple[str, int]] = []
    for match in _ACRONYM_RE.finditer(text):
        token = match.group(0)
        if token in _COMMON_UPPER_WORDS:
            continue
        if token in _LABEL_WORDS:
            continue
        found.append((token, match.start()))
    return found


def _is_defined_before(text: str, token: str, position: int) -> bool:
    """Check whether a definition pattern like 'Full Name (TOKEN)' appears
    anywhere in the text before the given character position."""
    prefix = text[:position]
    # Simple case-insensitive search for "... (TOKEN)" in prefix
    pattern = re.compile(
        r"\b[A-Za-z][A-Za-z\s,\-&\.]{1,80}\s+\(" + re.escape(token) + r"\)",
        re.IGNORECASE,
    )
    return bool(pattern.search(prefix))


def _all_standalone_positions(text: str, token: str) -> list[int]:
    """Return character positions of standalone uses of token that are
    NOT inside a definition pattern like "... (TOKEN)".
    """
    positions: list[int] = []
    # Find all occurrences
    for m in re.finditer(rf"\b{re.escape(token)}\b", text):
        pos = m.start()
        # Check if this occurrence is inside a definition pattern
        # Look back up to 120 chars for a '(' before this token
        lookback_start = max(0, pos - 120)
        lookback = text[lookback_start:pos]
        # If the immediately preceding chars are " (" then this is the acronym
        # inside a definition — skip it.
        if lookback.endswith(" ") and pos > 0 and text[pos - 1] == " ":
            # Check for opening paren before the space
            # Actually simpler: check if there is a '(' within the last few chars
            # before the token that isn't closed
            pass
        # Robust check: see if this token sits inside "... (TOKEN)"
        # by scanning backwards for '(' and forwards for ')'
        paren_open = text.rfind("(", lookback_start, pos)
        if paren_open != -1:
            paren_close = text.find(")", paren_open, pos + len(token) + 2)
            if paren_close != -1 and pos < paren_close:
                # This token is inside parentheses — could be a definition
                # But we only want to skip if the prefix before '(' looks like a definition
                prefix_before_paren = text[max(0, paren_open - 80):paren_open]
                # Require at least one word character before the paren
                if re.search(r"[A-Za-z]", prefix_before_paren):
                    continue  # skip — this is inside a definition
        positions.append(pos)
    return positions


# ---------------------------------------------------------------------------
# Core checks
# ---------------------------------------------------------------------------

def _check_undefined_acronyms(text: str, errors: list[str], warnings: list[str]) -> None:
    """Detect acronyms used without prior definition in body text."""
    candidates = _candidate_acronyms(text)

    # Track first standalone occurrence per token
    seen_first: dict[str, int] = {}
    for token, pos in candidates:
        if token in seen_first:
            continue
        # Skip if this token is inside a definition pattern itself
        lookback_start = max(0, pos - 120)
        paren_open = text.rfind("(", lookback_start, pos)
        if paren_open != -1:
            paren_close = text.find(")", paren_open, pos + len(token) + 2)
            if paren_close != -1 and pos < paren_close:
                prefix_before_paren = text[max(0, paren_open - 80):paren_open]
                if re.search(r"[A-Za-z]", prefix_before_paren):
                    continue  # inside a definition

        seen_first[token] = pos

    for token, pos in seen_first.items():
        # Check if defined anywhere in the body (for approved-list check)
        has_definition_anywhere = bool(re.search(
            r"\b[A-Za-z][A-Za-z\s,\-\&\.]+\s+\(" + re.escape(token) + r"\)",
            text,
            re.IGNORECASE,
        ))

        if token in APPROVED_ACRONYMS:
            if not has_definition_anywhere:
                warnings.append(
                    f"CCI-ACR-002: approved acronym '{token}' used without explicit "
                    f"definition in body text"
                )
            continue

        # Non-approved — must have definition before first use
        if not _is_defined_before(text, token, pos):
            errors.append(
                f"CCI-ACR-001: acronym '{token}' used in body without prior "
                f"definition; spell out with parenthetical on first use"
            )


def _check_defined_but_unused(text: str, warnings: list[str]) -> None:
    """Detect acronyms defined in body but never used afterward."""
    # Find all definition patterns "... (TOKEN)"
    defined: dict[str, int] = {}
    for m in re.finditer(r"\b([A-Za-z][A-Za-z\s,\-&\.]+)\s+\(([A-Z]{2,})\)", text):
        token = m.group(2)
        defined[token] = m.end()

    for token, def_end in defined.items():
        # Skip common words / labels
        if token in _COMMON_UPPER_WORDS or token in _LABEL_WORDS:
            continue
        # Search for standalone use after definition
        suffix = text[def_end:]
        if not re.search(rf"\b{re.escape(token)}\b", suffix):
            warnings.append(
                f"CCI-ACR-003: acronym '{token}' defined in body but never used afterward"
            )


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_cci_acronyms(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI acronym first-use checks."""
    errors: list[str] = []
    warnings: list[str] = []

    text = _body_text(payload)
    if not text:
        return errors, warnings

    _check_undefined_acronyms(text, errors, warnings)
    _check_defined_but_unused(text, warnings)

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_acronym_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_acronyms(payload)

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
