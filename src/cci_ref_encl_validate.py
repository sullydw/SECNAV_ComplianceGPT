#!/usr/bin/env python3
"""
CCI Reference and Enclosure Content Validator

Validates references and enclosures against Correspondence Content Intelligence
rules for SECNAV M-5216.5 reference/enclosure handling.

Public API:
    validate_cci_ref_encl(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).  Errors denote hard non-compliance;
        warnings flag items for human review.

CLI:
    python src/cci_ref_encl_validate.py <payload.json>

    Prints WARNING lines first, then FAIL + errors (if any, exit 1), or PASS
    (exit 0) when there are no errors.

Scope boundary with C9:
    For doc_type == "DT_ENDORSEMENT":
      - universal checks run (body citation, duplicate detection, warnings)
      - marker sequence/order checks are SKIPPED
      - prior_ref_markers, prior_refs, prior_encl_markers, prior_encls are
        NOT inspected — c9_validate.py owns endorsement-specific continuation
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

_SEP_COVER_PHRASES = frozenset([
    "sep cover",
    "separate cover",
    "under separate cover",
    "provided separately",
])

# Marker patterns for refs and encls
_REF_MARKER_RE = re.compile(r'^\(([a-z]+)\)\s+(.*)$')
_ENCL_MARKER_RE = re.compile(r'^\((\d+)\)\s+(.*)$')

# Citation detection patterns
_REF_CITE_SEARCH = re.compile(r'reference\s*\(?([a-z]+)\)?', re.IGNORECASE)
_ENCL_CITE_SEARCH = re.compile(r'enclosur...?\s*\(?([a-z]+)\)?', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_doc_type(payload: dict[str, Any]) -> str:
    """Resolve canonical document type."""
    dt = payload.get("doc_type")
    if dt is not None:
        dt = str(dt).lower().strip()
        _DT_MAP = {
            "dt_std_ltr": "standard_letter",
            "dt_joint_ltr": "joint_letter",
            "dt_endorsement": "endorsement",
            "dt_memo_mfr": "memorandum_for_record",
            "dt_memo_from_to_plain": "from_to_memo",
            "dt_memo_plain": "plain_paper_memo",
            "dt_memo_lh": "letterhead_memo",
        }
        if dt in _DT_MAP:
            return _DT_MAP[dt]
        return dt

    ct = payload.get("correspondence_type")
    if ct is not None:
        return str(ct).lower().strip()

    return "standard_letter"


def _normalize_list(value: Any) -> list[str]:
    """Normalize a field into a list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalize_text(text: str) -> str:
    """Normalize text for duplicate comparison."""
    return " ".join(str(text).lower().split())


def _extract_text(text: str) -> str:
    """Extract substantive content from a ref/encl entry, stripping parens."""
    # Try to strip leading marker
    for pattern in (_REF_MARKER_RE, _ENCL_MARKER_RE):
        m = pattern.match(text)
        if m:
            body_text = m.group(2).strip()
            # Also strip any remaining trailing marker notation
            return _normalize_text(body_text)
    # No marker found, just normalize
    return _normalize_text(text)


def _parse_ref_entry(entry: str) -> tuple[str | None, str]:
    """Parse a reference entry into (marker, text_content)."""
    m = _REF_MARKER_RE.match(entry)
    if m:
        return f"({m.group(1)})", m.group(2).strip()
    return None, entry.strip()


def _parse_encl_entry(entry: str) -> tuple[str | None, str]:
    """Parse an enclosure entry into (marker, text_content)."""
    m = _ENCL_MARKER_RE.match(entry)
    if m:
        return f"({m.group(1)})", m.group(2).strip()
    return None, entry.strip()


def _body_text(payload: dict[str, Any]) -> str:
    """Extract all body text into a single string for full-text scanning."""
    for key in ("body", "body_paragraphs"):
        val = payload.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            return "\n".join(str(item) for item in val if str(item).strip())
        text = str(val).strip()
        if text:
            return text
    return ""


def _body_paragraphs(payload: dict[str, Any]) -> list[str]:
    """Extract body as a list of paragraph strings in order."""
    for key in ("body", "body_paragraphs"):
        val = payload.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            return [str(item) for item in val]
        text = str(val).strip()
        if text:
            return [text]
    return []


# ---------------------------------------------------------------------------
# Core checks
# ---------------------------------------------------------------------------

def _check_ref_citations(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Check that every listed reference is cited in the body.

    Accepts:
      - Marker-based citations like "reference (a)", "ref (a)", "(a)"
      - Text substring match on normalized ref text
    """
    refs = _normalize_list(payload.get("ref")) or _normalize_list(payload.get("refs")) or _normalize_list(payload.get("references"))
    if not refs:
        return

    body_text_lower = _body_text(payload).lower()
    paragraphs = _body_paragraphs(payload)

    for i, entry in enumerate(refs, start=1):
        marker, text_content = _parse_ref_entry(entry)
        text_lower = text_content.lower()

        # Try marker citation
        marker_found = False
        if marker:
            inner = marker.strip("()").lower()
            # Look for "reference (a)", "ref (a)", etc.
            pattern = re.compile(rf'reference\s*\(?{re.escape(inner)}\)?', re.IGNORECASE)
            if pattern.search(body_text_lower):
                marker_found = True

        # Try text match
        text_found = False
        if text_lower and text_lower in body_text_lower:
            text_found = True

        if not marker_found and not text_found:
            errors.append(
                f"CCI-REF-001: reference entry {i} has no body citation: {entry!r}"
            )


        # WARNING: bare marker citation without substantive text nearby
        if marker_found and not text_found:
            warnings.append(
                f"CCI-REF-010: reference entry {i} cited by marker only "
                f"without substantive text near citation: {entry!r}"
            )


def _check_encl_mentions(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Check that every listed enclosure is mentioned in the body.

    Accepts:
      - Marker-based mentions like "enclosure (1)", "encl (1)", "(1)"
      - Text substring match on normalized encl text
    """
    encls = _normalize_list(payload.get("encl")) or _normalize_list(payload.get("encls")) or _normalize_list(payload.get("enclosures"))
    if not encls:
        return

    body_text_lower = _body_text(payload).lower()
    paragraphs = _body_paragraphs(payload)

    for i, entry in enumerate(encls, start=1):
        marker, text_content = _parse_encl_entry(entry)
        text_lower = text_content.lower()

        # Try marker mention
        marker_found = False
        if marker:
            inner = marker.strip("()").lower()
            pattern = re.compile(rf'enclosur...?\s*\(?{re.escape(inner)}\)?', re.IGNORECASE)
            if pattern.search(body_text_lower):
                marker_found = True
            if f"({inner})" in body_text_lower:
                marker_found = True

        # Try text match
        text_found = False
        if text_lower and text_lower in body_text_lower:
            text_found = True

        if not marker_found and not text_found:
            errors.append(
                f"CCI-REF-002: enclosure entry {i} has no body mention: {entry!r}"
            )


def _check_ref_order(payload: dict[str, Any], errors: list[str]) -> None:
    """Check references are listed in order of first appearance in body.

    Scans body paragraphs in order. For each ref, look for first body paragraph
    that mentions that ref (marker or text). The ref list order must match the
    first-mention paragraph order.
    """
    refs = _normalize_list(payload.get("ref")) or _normalize_list(payload.get("refs")) or _normalize_list(payload.get("references"))
    if not refs:
        return

    paragraphs = _body_paragraphs(payload)
    if not paragraphs:
        return

    first_mention_positions: dict[int, int] = {}  # ref_index (1-based) -> first body paragraph index

    for para_idx, para in enumerate(paragraphs):
        para_lower = para.lower()
        for ref_idx, entry in enumerate(refs, start=1):
            if ref_idx in first_mention_positions:
                continue

            marker, text_content = _parse_ref_entry(entry)
            found = False

            # Marker citation check
            if marker:
                inner = marker.strip("()").lower()
                pattern = re.compile(rf'reference\s*\(?{re.escape(inner)}\)?', re.IGNORECASE)
                if pattern.search(para_lower):
                    found = True
                if f"({inner})" in para_lower:
                    found = True

            # Text match
            text_lower = text_content.lower()
            if text_lower and text_lower in para_lower:
                found = True

            if found:
                first_mention_positions[ref_idx] = para_idx

    # Verify every ref was cited
    for ref_idx in range(1, len(refs) + 1):
        if ref_idx not in first_mention_positions:
            # Already caught as error in _check_ref_citations; skip here
            continue

    # Build ordered list of ref indices by first mention
    ordered_by_mention = sorted(
        first_mention_positions.keys(),
        key=lambda k: first_mention_positions[k]
    )

    # Compare to ref list order (1, 2, 3, ...)
    expected_order = list(range(1, len(refs) + 1))
    if ordered_by_mention != expected_order:
        errors.append(
            f"CCI-REF-003: references not in body-appearance order. "
            f"Reference list order: {expected_order}, "
            f"first-mention body order: {ordered_by_mention}"
        )


def _check_encl_order(payload: dict[str, Any], errors: list[str]) -> None:
    """Check enclosures are listed in order of first appearance in body.

    Same logic as _check_ref_order but for enclosures.
    """
    encls = _normalize_list(payload.get("encl")) or _normalize_list(payload.get("encls")) or _normalize_list(payload.get("enclosures"))
    if not encls:
        return

    paragraphs = _body_paragraphs(payload)
    if not paragraphs:
        return

    first_mention_positions: dict[int, int] = {}

    for para_idx, para in enumerate(paragraphs):
        para_lower = para.lower()
        for encl_idx, entry in enumerate(encls, start=1):
            if encl_idx in first_mention_positions:
                continue

            marker, text_content = _parse_encl_entry(entry)
            found = False

            # Marker mention check
            if marker:
                inner = marker.strip("()").lower()
                pattern = re.compile(rf'enclosur...?\s*\(?{re.escape(inner)}\)?', re.IGNORECASE)
                if pattern.search(para_lower):
                    found = True
                if f"({inner})" in para_lower:
                    found = True

            # Text match
            text_lower = text_content.lower()
            if text_lower and text_lower in para_lower:
                found = True

            if found:
                first_mention_positions[encl_idx] = para_idx

    ordered_by_mention = sorted(
        first_mention_positions.keys(),
        key=lambda k: first_mention_positions[k]
    )

    expected_order = list(range(1, len(encls) + 1))
    if ordered_by_mention != expected_order:
        errors.append(
            f"CCI-REF-004: enclosures not in body-appearance order. "
            f"Enclosure list order: {expected_order}, "
            f"first-mention body order: {ordered_by_mention}"
        )


def _check_duplicate_ref_encl(payload: dict[str, Any], errors: list[str]) -> None:
    """Check same item does not appear in both ref and encl lists."""
    refs = _normalize_list(payload.get("ref")) or _normalize_list(payload.get("refs")) or _normalize_list(payload.get("references"))
    encls = _normalize_list(payload.get("encl")) or _normalize_list(payload.get("encls")) or _normalize_list(payload.get("enclosures"))

    if not refs or not encls:
        return

    ref_texts = {(_extract_text(r), i) for i, r in enumerate(refs, start=1)}
    encl_texts = {(_extract_text(e), i) for i, e in enumerate(encls, start=1)}

    for ref_norm, ref_idx in ref_texts:
        for encl_norm, encl_idx in encl_texts:
            if ref_norm == encl_norm and ref_norm:
                errors.append(
                    f"CCI-REF-005: same item appears in both references and enclosures "
                    f"(ref entry {ref_idx}: {refs[ref_idx - 1]!r}, "
                    f"encl entry {encl_idx}: {encls[encl_idx - 1]!r})"
                )


def _check_ref_sequence(payload: dict[str, Any], errors: list[str]) -> None:
    """Check reference markers are in valid alphabetical sequence.

    Skipped for endorsements.
    """
    doc_type = _get_doc_type(payload)
    if doc_type == "endorsement":
        return

    refs = _normalize_list(payload.get("ref")) or _normalize_list(payload.get("refs")) or _normalize_list(payload.get("references"))
    if not refs:
        return

    expected_marker = "a"
    for i, entry in enumerate(refs, start=1):
        marker, _ = _parse_ref_entry(entry)
        if marker is None:
            # No marker present — infer (a), (b), ... from list order
            inferred = f"({expected_marker})"
            expected_marker = _next_alpha(expected_marker)
            continue

        inner = marker.strip("()")
        if inner != expected_marker:
            # Check if it's a duplicate or skip
            already_seen = any(
                _parse_ref_entry(r)[0] == marker for r in refs[:i-1]
            )
            if already_seen:
                errors.append(
                    f"CCI-REF-006: duplicate reference marker {marker} "
                    f"at ref entry {i}"
                )
            else:
                errors.append(
                    f"CCI-REF-006: reference marker {marker} at entry {i} "
                    f"does not continue expected sequence; expected ({expected_marker})"
                )

        expected_marker = _next_alpha(expected_marker)


def _check_encl_sequence(payload: dict[str, Any], errors: list[str]) -> None:
    """Check enclosure markers are in valid numeric sequence.

    Skipped for endorsements.
    """
    doc_type = _get_doc_type(payload)
    if doc_type == "endorsement":
        return

    encls = _normalize_list(payload.get("encl")) or _normalize_list(payload.get("encls")) or _normalize_list(payload.get("enclosures"))
    if not encls:
        return

    expected_num = 1
    for i, entry in enumerate(encls, start=1):
        marker, _ = _parse_encl_entry(entry)
        if marker is None:
            # No marker present — infer (1), (2), ... from list order
            expected_num += 1
            continue

        inner = marker.strip("()")
        try:
            num = int(inner)
        except ValueError:
            errors.append(
                f"CCI-REF-007: enclosure marker {marker} at entry {i} "
                f"is not a valid number"
            )
            expected_num = num + 1 if isinstance(expected_num, int) else expected_num + 1
            continue

        if num != expected_num:
            already_seen = any(
                _parse_encl_entry(e)[0] == marker for e in encls[:i-1]
            )
            if already_seen:
                errors.append(
                    f"CCI-REF-007: duplicate enclosure marker {marker} "
                    f"at encl entry {i}"
                )
            else:
                errors.append(
                    f"CCI-REF-007: enclosure marker {marker} at entry {i} "
                    f"does not continue expected sequence; expected ({expected_num})"
                )

        expected_num = num + 1


def _next_alpha(s: str) -> str:
    """Increment a lowercase alpha string."""
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


def _check_warnings(payload: dict[str, Any], warnings: list[str]) -> None:
    """Check sep cover and short/vague warnings for ref/encl entries."""
    refs = _normalize_list(payload.get("ref")) or _normalize_list(payload.get("refs")) or _normalize_list(payload.get("references"))
    encls = _normalize_list(payload.get("encl")) or _normalize_list(payload.get("encls")) or _normalize_list(payload.get("enclosures"))

    # Sep cover warnings for enclosures
    for i, entry in enumerate(encls, start=1):
        lower = entry.lower()
        for phrase in _SEP_COVER_PHRASES:
            if phrase in lower:
                warnings.append(
                    f"CCI-REF-008: enclosure entry {i} contains "
                    f"'{phrase}' notation: {entry!r}"
                )
                break

    # Short/vague warnings
    for i, entry in enumerate(refs, start=1):
        _, text = _parse_ref_entry(entry)
        tokens = len([t for t in _normalize_text(text).split() if t])
        if tokens < 3:
            warnings.append(
                f"CCI-REF-009: reference entry {i} appears vague "
                f"({tokens} meaningful tokens): {entry!r}"
            )

    for i, entry in enumerate(encls, start=1):
        _, text = _parse_encl_entry(entry)
        tokens = len([t for t in _normalize_text(text).split() if t])
        if tokens < 3:
            warnings.append(
                f"CCI-REF-009: enclosure entry {i} appears vague "
                f"({tokens} meaningful tokens): {entry!r}"
            )


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_cci_ref_encl(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI reference and enclosure checks."""
    errors: list[str] = []
    warnings: list[str] = []

    _check_ref_citations(payload, errors, warnings)
    _check_encl_mentions(payload, errors, warnings)
    _check_encl_order(payload, errors)
    _check_ref_order(payload, errors)
    _check_duplicate_ref_encl(payload, errors)
    _check_ref_sequence(payload, errors)
    _check_encl_sequence(payload, errors)
    _check_warnings(payload, warnings)

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_ref_encl_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_ref_encl(payload)

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
