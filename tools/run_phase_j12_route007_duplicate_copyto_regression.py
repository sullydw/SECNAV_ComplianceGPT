#!/usr/bin/env python3
"""
CCI-ROUTE-007 Duplicate Copy-to Regression Runner

Phase J.12 / Phase K.4 — Dedicated deterministic regression runner for
CCI-ROUTE-007 exact duplicate Copy-to detection.

Uses the existing validator entry point (validate_cci_routing) with inline
sanitized/synthetic payloads. No external fixture files required.

Safety:
- No config changes.
- No severity changes.
- No allowlist changes.
- No validator changes.
- No catalog changes.
- Sanitized/synthetic payloads only.

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cci_routing_validate import validate_cci_routing

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _has_rule(findings: list[str], rule_id: str) -> bool:
    return any(rule_id in f for f in findings)


def _count_rule(findings: list[str], rule_id: str) -> int:
    return sum(1 for f in findings if rule_id in f)


def _has_to_duplicate(warnings: list[str]) -> bool:
    return any("duplicates To line" in w for w in warnings)


def _has_via_duplicate(warnings: list[str]) -> bool:
    return any("duplicates Via line" in w for w in warnings)


# -------------------------------------------------------------------------
# Test payloads (sanitized / synthetic)
# -------------------------------------------------------------------------

# 1. Positive: Copy-to duplicates To exactly
PAYLOAD_COPYTO_DUPLICATES_TO = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["Chief of Naval Operations", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 COPY-TO DUPLICATES TO",
    "date": "15 May 2026",
}

# 2. Positive: Copy-to duplicates Via exactly
PAYLOAD_COPYTO_DUPLICATES_VIA = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "via": ["Commander, Naval Surface Force Atlantic", "Commander, U.S. Pacific Fleet"],
    "copy_to": ["Commander, Naval Surface Force Atlantic", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 COPY-TO DUPLICATES VIA",
    "date": "15 May 2026",
}

# 3. Positive: Multiple Copy-to entries with one duplicate
PAYLOAD_MULTIPLE_COPYTO_ONE_DUP = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": [
        "Commander, Fleet Cyber Command",
        "Chief of Naval Operations",  # duplicate
        "Commander, Navy Installations Command",
    ],
    "subj": "TEST FIXTURE ROUTE-007 MULTIPLE COPY-TO ONE DUPLICATE",
    "date": "15 May 2026",
}

# 4. Positive: Multiple Via entries; Copy-to duplicates one Via
PAYLOAD_MULTIPLE_VIA_ONE_DUP = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "via": [
        "Commander, Naval Surface Force Atlantic",
        "Commander, U.S. Pacific Fleet",
        "Commander, Navy Installations Command",
    ],
    "copy_to": ["Commander, U.S. Pacific Fleet", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 MULTIPLE VIA ONE DUPLICATE",
    "date": "15 May 2026",
}

# 5. Positive: Duplicate appears after case/spacing normalization
PAYLOAD_NORMALIZED_DUPLICATE = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["chief of naval  operations", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 NORMALIZED DUPLICATE",
    "date": "15 May 2026",
}

# 6. Positive/Cross-rule: Combined payload preserving ROUTE-010/011 while triggering ROUTE-007
PAYLOAD_COMBINED_007_010_011 = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Commanding Officer, 12345",  # numeric office code after comma → ROUTE-010
    # Missing "from" line → ROUTE-011
    "via": ["Commander, Naval Surface Force Atlantic"],
    "copy_to": ["Commander, Naval Surface Force Atlantic"],  # duplicates Via → ROUTE-007
    "subj": "TEST FIXTURE ROUTE-007 COMBINED WITH 010 AND 011",
    "date": "15 May 2026",
}

# 7. Negative: No duplicate Copy-to
PAYLOAD_NO_DUPLICATE = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["Commander, Fleet Cyber Command", "Commander, Navy Installations Command"],
    "subj": "TEST FIXTURE ROUTE-007 NO DUPLICATE",
    "date": "15 May 2026",
}

# 8. Negative: Near-duplicate should not trigger
PAYLOAD_NEAR_DUPLICATE = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Commanding Officer, USS NIMITZ",
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["CO, USS NIMITZ", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 NEAR DUPLICATE",
    "date": "15 May 2026",
}

# 9. Negative: Abbreviation should not trigger unless exact normalized match
PAYLOAD_ABBREVIATION = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Commander, U.S. Pacific Fleet",
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["COMPACFLT", "Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-007 ABBREVIATION",
    "date": "15 May 2026",
}

# 10. Negative: Empty Copy-to list should not trigger
PAYLOAD_EMPTY_COPYTO = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": [],
    "subj": "TEST FIXTURE ROUTE-007 EMPTY COPY-TO",
    "date": "15 May 2026",
}

# 11. Negative: Copy-to duplicates another Copy-to only; should not trigger ROUTE-007
PAYLOAD_COPYTO_SELF_DUPLICATE = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    "from": "Commanding Officer, Example Unit",
    "copy_to": [
        "Commander, Fleet Cyber Command",
        "Commander, Fleet Cyber Command",  # duplicate copy-to entry
        "Commander, Navy Installations Command",
    ],
    "subj": "TEST FIXTURE ROUTE-007 COPY-TO SELF DUPLICATE",
    "date": "15 May 2026",
}

# 12. Cross-rule preservation: ROUTE-010 warning behavior unchanged
PAYLOAD_ROUTE010_UNCHANGED = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Commanding Officer, 12345",  # numeric-only office code after comma → ROUTE-010
    "from": "Commanding Officer, Example Unit",
    "copy_to": ["Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-010 UNCHANGED",
    "date": "15 May 2026",
}

# 13. Cross-rule preservation: ROUTE-011 warning behavior unchanged
PAYLOAD_ROUTE011_UNCHANGED = {
    "doc_type": "standard_letter",
    "component": "navy",
    "to": "Chief of Naval Operations",
    # Missing "from" line → ROUTE-011
    "copy_to": ["Commander, Fleet Cyber Command"],
    "subj": "TEST FIXTURE ROUTE-011 UNCHANGED",
    "date": "15 May 2026",
}


# -------------------------------------------------------------------------
# Test runner
# -------------------------------------------------------------------------

def _run_test(name: str, payload: dict, *, expect_route007: bool = False,
              expected_route007_count: int = 0, expect_route010: bool = False,
              expect_route011: bool = False) -> bool:
    """Run validator on payload and assert expectations."""
    errors, warnings = validate_cci_routing(payload)
    all_findings = errors + warnings

    has_007 = _has_rule(warnings, "CCI-ROUTE-007")
    count_007 = _count_rule(warnings, "CCI-ROUTE-007")
    has_010 = _has_rule(all_findings, "CCI-ROUTE-010")
    has_011 = _has_rule(all_findings, "CCI-ROUTE-011")

    ok = True

    # ROUTE-007 assertions
    if expect_route007:
        if not has_007:
            print(f"  FAIL: {name} — expected CCI-ROUTE-007 but none found")
            ok = False
        if count_007 != expected_route007_count:
            print(f"  FAIL: {name} — expected {expected_route007_count} ROUTE-007 findings, got {count_007}")
            ok = False
    else:
        if has_007:
            print(f"  FAIL: {name} — unexpected CCI-ROUTE-007 found ({count_007} occurrence(s))")
            ok = False

    # ROUTE-010 assertions
    if expect_route010:
        if not has_010:
            print(f"  FAIL: {name} — expected CCI-ROUTE-010 but none found")
            ok = False
    else:
        if has_010:
            print(f"  FAIL: {name} — unexpected CCI-ROUTE-010 found")
            ok = False

    # ROUTE-011 assertions
    if expect_route011:
        if not has_011:
            print(f"  FAIL: {name} — expected CCI-ROUTE-011 but none found")
            ok = False
    else:
        if has_011:
            print(f"  FAIL: {name} — unexpected CCI-ROUTE-011 found")
            ok = False

    # Severity: ROUTE-007 should never appear in errors (not allowlisted)
    if _has_rule(errors, "CCI-ROUTE-007"):
        print(f"  FAIL: {name} — CCI-ROUTE-007 found in errors list (should be advisory/warnings only)")
        ok = False

    if ok:
        print(f"  PASS: {name}")
    return ok


def main() -> int:
    print("=" * 72)
    print("CCI-ROUTE-007 Duplicate Copy-to Regression Runner")
    print("Phase J.12 / Phase K.4")
    print("=" * 72)
    print()

    all_ok = True

    # Positive cases
    if not _run_test("Copy-to duplicates To exactly",
                     PAYLOAD_COPYTO_DUPLICATES_TO,
                     expect_route007=True, expected_route007_count=1):
        all_ok = False

    if not _run_test("Copy-to duplicates Via exactly",
                     PAYLOAD_COPYTO_DUPLICATES_VIA,
                     expect_route007=True, expected_route007_count=1):
        all_ok = False

    if not _run_test("Multiple Copy-to entries with one duplicate",
                     PAYLOAD_MULTIPLE_COPYTO_ONE_DUP,
                     expect_route007=True, expected_route007_count=1):
        all_ok = False

    if not _run_test("Multiple Via entries; Copy-to duplicates one Via",
                     PAYLOAD_MULTIPLE_VIA_ONE_DUP,
                     expect_route007=True, expected_route007_count=1):
        all_ok = False

    if not _run_test("Duplicate after case/spacing normalization",
                     PAYLOAD_NORMALIZED_DUPLICATE,
                     expect_route007=True, expected_route007_count=1):
        all_ok = False

    # Cross-rule combined case
    if not _run_test("Combined payload preserving ROUTE-010/011 while triggering ROUTE-007",
                     PAYLOAD_COMBINED_007_010_011,
                     expect_route007=True, expected_route007_count=1,
                     expect_route010=True, expect_route011=True):
        all_ok = False

    # Negative cases
    if not _run_test("No duplicate Copy-to",
                     PAYLOAD_NO_DUPLICATE,
                     expect_route007=False):
        all_ok = False

    if not _run_test("Near-duplicate should not trigger",
                     PAYLOAD_NEAR_DUPLICATE,
                     expect_route007=False):
        all_ok = False

    if not _run_test("Abbreviation should not trigger unless exact match",
                     PAYLOAD_ABBREVIATION,
                     expect_route007=False):
        all_ok = False

    if not _run_test("Empty Copy-to list should not trigger",
                     PAYLOAD_EMPTY_COPYTO,
                     expect_route007=False):
        all_ok = False

    if not _run_test("Copy-to self-duplicate only should not trigger ROUTE-007",
                     PAYLOAD_COPYTO_SELF_DUPLICATE,
                     expect_route007=False):
        all_ok = False

    # Cross-rule preservation cases
    if not _run_test("ROUTE-010 warning behavior unchanged",
                     PAYLOAD_ROUTE010_UNCHANGED,
                     expect_route007=False, expect_route010=True):
        all_ok = False

    if not _run_test("ROUTE-011 warning behavior unchanged",
                     PAYLOAD_ROUTE011_UNCHANGED,
                     expect_route007=False, expect_route011=True):
        all_ok = False

    print()
    print("=" * 72)
    if all_ok:
        print("CCI-ROUTE-007 REGRESSION RESULT: PASS (13/13 checks)")
        return 0
    else:
        print("CCI-ROUTE-007 REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
