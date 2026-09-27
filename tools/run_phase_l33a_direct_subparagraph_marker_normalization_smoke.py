#!/usr/bin/env python3
"""
Phase L.33A — Direct Subparagraph Marker Normalization Smoke

Proves that when a user types level-4 style markers ``(a)`` and ``(b)``
directly under a level-1 numbered paragraph, the intake layer normalizes
them to level-2 ``a.`` / ``b.`` so the body validates against SECNAV
M-5216.5 paragraph numbering (C7-014) and renders at the correct
indentation.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from conversational_builder import _normalize_body_markers, _coerce_value
from body_v6_validate import validate_body


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS: {name}" + (f" -- {detail}" if detail else ""))
    else:
        print(f"FAIL: {name}" + (f" -- {detail}" if detail else ""))
        sys.exit(1)


def test_normalize_direct_subparagraphs() -> None:
    raw = [
        "1. Main paragraph.",
        "(a) First sub.",
        "(b) Second sub.",
    ]
    normalized = _normalize_body_markers(raw)
    check("L33A direct (a) -> a.", normalized[1].startswith("a."), normalized[1])
    check("L33A direct (b) -> b.", normalized[2].startswith("b."), normalized[2])


def test_keep_proper_deep_hierarchy() -> None:
    raw = [
        "1. Main.",
        "a. Sub.",
        "(1) Sub-sub.",
        "(a) deepest.",
    ]
    normalized = _normalize_body_markers(raw)
    check("L33A keep proper (a) under (1)", normalized[3].startswith("(a)"), normalized[3])


def test_body_validation_passes_after_normalization() -> None:
    raw = [
        "1. Request one quota.",
        "2. Training rationale. Per reference (a).",
        "3. Point of contact.",
        "(a) Phone: (850) 555-0123.",
        "(b) Email: alex.sample.mil@us.navy.mil.",
    ]
    normalized = _normalize_body_markers(raw)
    errors = validate_body({"body": normalized})
    check("L33A C7-014 passes after normalization", not errors, str(errors))


def test_coerce_value_json_array_normalizes() -> None:
    raw = [
        "1. Main.",
        "(a) Sub one.",
        "(b) Sub two.",
    ]
    result = _coerce_value("body", raw)
    check("L33A coerce list normalizes (a)", result[1].startswith("a."), result[1])
    check("L33A coerce list normalizes (b)", result[2].startswith("b."), result[2])


def test_coerce_value_string_json_normalizes() -> None:
    text = '["1. Main.", "(a) Sub one.", "(b) Sub two."]'
    result = _coerce_value("body", text)
    check("L33A coerce JSON string normalizes (a)", result[1].startswith("a."), str(result))
    check("L33A coerce JSON string normalizes (b)", result[2].startswith("b."), str(result))


if __name__ == "__main__":
    test_normalize_direct_subparagraphs()
    test_keep_proper_deep_hierarchy()
    test_body_validation_passes_after_normalization()
    test_coerce_value_json_array_normalizes()
    test_coerce_value_string_json_normalizes()
    print("\nL.33A direct subparagraph marker normalization smoke: all checks passed")
