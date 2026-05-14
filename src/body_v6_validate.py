#!/usr/bin/env python3
"""SECNAV M-5216.5 — Body v6 Validator (parent-scoped sequencing)

Validates body entries against C7-014 (paragraph/subparagraph numbering)
with parent-scoped sequencing: level-2, 3, 4 markers restart under each
parent rather than being validated globally.

Public API:
    validate_body(payload) -> list[str]
"""

import json
import os
import re
import sys

from body_v6_parse import detect_marker_level


def _parse_marker(marker):
    """Parse a marker string into (level, sequence_value).

    level: 1/2/3/4
    sequence_value: 1-based integer (a=1, b=2, etc.)

    Returns (level, value) or (0, None) if unparseable.
    """
    if not marker:
        return (0, None)

    # Level 1: "1.", "2.", "10.", etc.
    m = re.match(r"^(\d+)\.$", marker)
    if m:
        return (1, int(m.group(1)))

    # Level 2: "a.", "b.", etc.
    m = re.match(r"^([a-z])\.$", marker)
    if m:
        return (2, ord(m.group(1)) - ord("a") + 1)

    # Level 3: "(1)", "(2)", etc.
    m = re.match(r"^\((\d+)\)$", marker)
    if m:
        return (3, int(m.group(1)))

    # Level 4: "(a)", "(b)", etc.
    m = re.match(r"^\(([a-z])\)$", marker)
    if m:
        return (4, ord(m.group(1)) - ord("a") + 1)

    return (0, None)


def _extract_marker(text):
    """Extract the leading marker from a body line, or None."""
    text = text.strip()
    m = re.match(r"^((?:\d+\.|[a-z]\.|\(\d+\)|\([a-z]\)))\s", text)
    if m:
        return m.group(1)
    return None


def _expected_marker(level, index):
    """Return the marker string for a 1-based index at the given level."""
    if level == 1:
        return f"{index}."
    if level == 2:
        return f"{chr(ord('a') + index - 1)}."
    if level == 3:
        return f"({index})"
    if level == 4:
        return f"({chr(ord('a') + index - 1)})"
    return None


def validate_body(payload):
    """Validate body list against C7-014 numbering rules.

    Args:
        payload: dict with 'body' key (list of strings) or list of strings

    Returns:
        list of error strings. Empty list = pass.
    """
    # Extract body list
    if isinstance(payload, dict):
        body = payload.get("body", [])
    elif isinstance(payload, list):
        body = payload
    else:
        return ["Invalid payload type: expected dict or list"]

    if not body:
        return []

    # Parse body entries into (marker, level, sequence_value, text) records
    records = []
    for i, line in enumerate(body):
        marker = _extract_marker(line)
        if marker:
            level, val = _parse_marker(marker)
            records.append((marker, level, val, line, i))
        else:
            # Unmarked line — skip for sequence validation
            records.append((None, 0, None, line, i))

    errors = []

    # ---- Check for skipped levels ----
    prev_level = 0
    for marker, level, val, text, idx in records:
        if level == 0:
            continue
        if level > prev_level + 1:
            errors.append(
                f"Entry {idx}: Skipped level from {prev_level} to {level} "
                f'(marker="{marker}")'
            )
        prev_level = level

    # ---- Parent-scoped sequence validation ----
    # Build groups: level-1 global, level-2 under each L1, level-3 under each L2, etc.
    groups = {}
    record_groups = {}

    current_l1 = None
    current_l2 = None
    current_l3 = None

    for rec in records:
        marker, level, val, text, idx = rec
        if level == 0:
            continue

        if level == 1:
            current_l1 = marker
            current_l2 = None
            current_l3 = None
            gk = ("L1",)
        elif level == 2:
            current_l2 = marker
            current_l3 = None
            gk = ("L2", current_l1)
        elif level == 3:
            current_l3 = marker
            gk = ("L3", current_l1, current_l2)
        elif level == 4:
            gk = ("L4", current_l1, current_l2, current_l3)
        else:
            continue

        groups.setdefault(gk, []).append(rec)
        record_groups[id(rec)] = gk

    # Validate sequence within each group
    for gk, group_recs in groups.items():
        level = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}[gk[0]]
        expected_idx = 1

        for rec in group_recs:
            marker, lvl, val, text, idx = rec
            if val is None:
                errors.append(
                    f'Could not parse marker value "{marker}" at level {level}'
                )
                continue

            if val != expected_idx:
                expected = _expected_marker(level, expected_idx)
                errors.append(
                    f"Sequence error at level {level}, group {gk}: "
                    f'expected "{expected}" but found "{marker}"'
                )
                # Continue from where the marker actually is to avoid cascading errors
                expected_idx = val + 1
            else:
                expected_idx = val + 1

    # ---- Direct child minimum rule ----
    # If a parent has child items at the next level, it must have at least 2 direct children.
    child_groups = {}
    current_l1 = None
    current_l2 = None
    current_l3 = None

    for rec in records:
        marker, level, val, text, idx = rec

        if level == 1:
            current_l1 = marker
            current_l2 = None
            current_l3 = None
        elif level == 2:
            current_l2 = marker
            current_l3 = None
            pk = ("L2_children", current_l1)
            child_groups.setdefault(pk, []).append(rec)
        elif level == 3:
            current_l3 = marker
            pk = ("L3_children", current_l1, current_l2)
            child_groups.setdefault(pk, []).append(rec)
        elif level == 4:
            pk = ("L4_children", current_l1, current_l2, current_l3)
            child_groups.setdefault(pk, []).append(rec)

    for parent_key, children in child_groups.items():
        if len(children) < 2:
            parent_level_label = parent_key[0].replace("_children", "")
            parent_desc = " → ".join(str(k) for k in parent_key[1:] if k)
            child_markers = ", ".join(c[0] for c in children)
            level_num = {"L2": 2, "L3": 3, "L4": 4}[parent_level_label]
            errors.append(
                f'Parent "{parent_desc}" has only {len(children)} direct level-{level_num} child '
                f"({child_markers}): need at least 2 siblings per C7-014"
            )

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python body_v6_validate.py <payload.json>")
        sys.exit(1)

    payload_path = sys.argv[1]
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    errors = validate_body(payload)

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()