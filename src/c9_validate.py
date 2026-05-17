#!/usr/bin/env python3
"""
C9 Endorsement Reference & Enclosure Validator

Checks C9-004 (References) and C9-005 (Enclosures) continuation rules
against prior-sequence metadata.

C9-004: endorsement references must not repeat prior references and must
        continue the prior reference marker sequence.
C9-005: endorsement enclosures must not repeat prior enclosures and must
        continue the prior enclosure marker sequence.

Public API:
    validate_c9(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).  Warnings alone do not constitute failure.

CLI:
    python src/c9_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1), or PASS
    (exit 0) when there are no errors.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Regex to extract marker + text from a ref/encl entry.
# Ref entries look like "(c) SECNAV M-5216.5"
# Encl entries look like "(2) Updated endorsement routing worksheet"
_MARKER_RE = re.compile(r'^\(([a-z]+|\d+)\)\s+(.+)$')


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_c9(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for C9 reference/enclosure continuation checks."""

    errors: list[str] = []
    warnings: list[str] = []

    # Only validate endorsement payloads
    if payload.get("doc_type") != "DT_ENDORSEMENT":
        return errors, warnings

    # Normalize all fields to clean string lists (string -> list, missing -> empty)
    prior_ref_markers = _normalize_list(payload.get("prior_ref_markers"))
    prior_refs = _normalize_list(payload.get("prior_refs"))
    prior_encl_markers = _normalize_list(payload.get("prior_encl_markers"))
    prior_encls = _normalize_list(payload.get("prior_encls"))
    ref_entries = _normalize_list(payload.get("ref"))
    encl_entries = _normalize_list(payload.get("encl"))

    # --- C9-004: Reference continuation -----------------------------------

    if ref_entries:
        expected_ref_marker = _expected_next_ref_marker(prior_ref_markers)

        for i, entry in enumerate(ref_entries, start=1):
            m = _MARKER_RE.match(entry)
            if not m:
                errors.append(
                    f"C9-004: ref entry {i} {entry!r} does not match "
                    f"expected marker+text format"
                )
                continue

            marker = f"({m.group(1)})"
            text = m.group(2).strip()

            # Check marker continues sequence
            if marker != expected_ref_marker:
                errors.append(
                    f"C9-004: ref entry {i} marker {marker} does not "
                    f"continue prior sequence; expected {expected_ref_marker}"
                )

            # Check text is not a repeated prior reference
            if _matches_prior_text(text, prior_refs):
                errors.append(
                    f"C9-004: ref entry {i} text repeats a prior reference: "
                    f"{text!r}"
                )

            # Advance expected marker for next entry
            expected_ref_marker = _next_ref_marker(marker)

    # --- C9-005: Enclosure continuation -----------------------------------

    if encl_entries:
        expected_encl_marker = _expected_next_encl_marker(prior_encl_markers)

        for i, entry in enumerate(encl_entries, start=1):
            m = _MARKER_RE.match(entry)
            if not m:
                errors.append(
                    f"C9-005: encl entry {i} {entry!r} does not match "
                    f"expected marker+text format"
                )
                continue

            marker = f"({m.group(1)})"
            text = m.group(2).strip()

            # Check marker continues sequence
            if marker != expected_encl_marker:
                errors.append(
                    f"C9-005: encl entry {i} marker {marker} does not "
                    f"continue prior sequence; expected {expected_encl_marker}"
                )

            # Check text is not a repeated prior enclosure
            if _matches_prior_text(text, prior_encls):
                errors.append(
                    f"C9-005: encl entry {i} text repeats a prior enclosure: "
                    f"{text!r}"
                )

            # Advance expected marker for next entry
            expected_encl_marker = _next_encl_marker(marker)

    return errors, warnings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_list(value: Any) -> list[str]:
    """Normalize a field into a clean list of strings.

    - None / missing -> []
    - list -> stripped, non-empty string entries only
    - anything else -> str(value).strip() as single entry (if non-empty)
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _expected_next_ref_marker(prior_markers: list[str]) -> str:
    """Determine the expected next reference marker from prior markers."""
    if not prior_markers:
        return "(a)"
    last = prior_markers[-1].strip("()")
    next_inner = _incr_alpha(last)
    return f"({next_inner})"


def _next_ref_marker(current: str) -> str:
    """Increment a reference marker e.g. (c) -> (d)."""
    inner = current.strip("()")
    return f"({_incr_alpha(inner)})"


def _incr_alpha(s: str) -> str:
    """Increment a lowercase alpha string like a column label: a->b, z->aa."""
    chars = list(s)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] == 'z':
            chars[i] = 'a'
            i -= 1
        else:
            chars[i] = chr(ord(chars[i]) + 1)
            return ''.join(chars)
    return 'a' + ''.join(chars)


def _expected_next_encl_marker(prior_markers: list[str]) -> str:
    """Determine the expected next enclosure marker from prior markers."""
    if not prior_markers:
        return "(1)"
    last = prior_markers[-1].strip("()")
    return f"({int(last) + 1})"


def _next_encl_marker(current: str) -> str:
    """Increment an enclosure marker e.g. (2) -> (3)."""
    inner = current.strip("()")
    return f"({int(inner) + 1})"


def _matches_prior_text(text: str, prior_texts: list[str]) -> bool:
    """Check if text matches any prior text (case-insensitive, normalized)."""
    normalized = ' '.join(text.lower().split())
    for prior in prior_texts:
        prior_normalized = ' '.join(prior.lower().split())
        if normalized == prior_normalized:
            return True
    return False


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/c9_validate.py <payload.json>", file=sys.stderr)
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

    errors, warnings = validate_c9(payload)

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
