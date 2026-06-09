#!/usr/bin/env python3
"""
Phase H.9 / Phase I.8 — From-Line Advisory Validator Enforcement Regression Runner

Validates the CCI-ROUTE-011 From-line-required advisory/non-blocking check
implemented in src/cci_routing_validate.py.

Exit 0 only when all expectations are met.

Checks:
  1. Validator module loads successfully.
  2. _check_from_line_required helper exists and is callable.
  3. Missing From line on DT_STD_LTR triggers advisory ROUTE-011.
  4. Empty From line on DT_STD_LTR triggers advisory ROUTE-011.
  5. Whitespace-only From line on DT_STD_LTR triggers advisory ROUTE-011.
  6. Present From line on DT_STD_LTR produces no ROUTE-011 finding.
  7. window_envelope=true suppresses advisory even without From line.
  8. window_envelope=true with From line still produces no finding.
  9. Memorandum (DT_MEMO_FROM_TO_PLAIN) is skipped — no ROUTE-011.
 10. Endorsement is skipped — no ROUTE-011.
 11. Joint letter is skipped — no ROUTE-011.
 12. Multiple-address letter is skipped — no ROUTE-011.
 13. Both ROUTE-010 and ROUTE-011 trigger independently on same payload.
 14. Missing doc_type causes skip — no ROUTE-011.
 15. Existing CCI-ROUTE-010 behavior preserved on its own.
 16. Existing routing warnings (Via, Copy-to, Distribution) still work.
 17. No renderer/layout files changed.
 18. No prompt-contract files changed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Ensure repo root on sys.path so import works
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.cci_routing_validate import validate_cci_routing, _check_from_line_required


def load_fixture(name: str) -> dict:
    path = REPO_ROOT / "examples" / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_route_011(warnings: list[str], errors: list[str] | None = None) -> bool:
    targets = warnings if errors is None else warnings + errors
    return any("CCI-ROUTE-011" in t for t in targets)


def has_route_011_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in e for e in errors)


def has_route_010(warnings: list[str]) -> bool:
    return any("CCI-ROUTE-010" in w for w in warnings)


def run_git(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, shell=False)
    return result.stdout.strip()


def main() -> int:
    python = sys.executable
    print("=" * 72)
    print("PHASE H.9 FROM-LINE ADVISORY VALIDATOR REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # 01: Module loads
    results.append(("Check 01: Validator module loads successfully", True))
    print("PASS — Check 01")

    # 02: Helper exists
    ok = callable(_check_from_line_required)
    results.append(("Check 02: _check_from_line_required helper is callable", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")

    # 03: Missing From line triggers advisory
    payload = load_fixture("routing_from_missing.json")
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_011(warnings, errors)
    results.append(("Check 03: Missing From line triggers CCI-ROUTE-011 advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    # 04: Empty From line triggers advisory
    payload = load_fixture("routing_from_empty.json")
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_011(warnings, errors)
    results.append(("Check 04: Empty From line triggers CCI-ROUTE-011 advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    # 05: Whitespace-only From line triggers advisory
    payload = load_fixture("routing_from_empty.json")
    payload["from"] = "   "
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_011(warnings, errors)
    results.append(("Check 05: Whitespace-only From line triggers CCI-ROUTE-011 advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # 06: Present From line passes
    payload = load_fixture("routing_from_present.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 06: Present From line produces no CCI-ROUTE-011 finding", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # 07: window_envelope=true suppresses advisory
    payload = load_fixture("routing_from_window_envelope.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 07: window_envelope=true suppresses CCI-ROUTE-011 advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # 08: window_envelope=true with From line still passes
    payload = load_fixture("routing_from_present.json")
    payload["window_envelope"] = True
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 08: window_envelope=true with From line still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # 09: Memorandum skipped
    payload = load_fixture("routing_from_memo_skipped.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 09: Memorandum skipped — no CCI-ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # 10: Endorsement skipped
    payload = load_fixture("routing_from_endorsement_skipped.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 10: Endorsement skipped — no CCI-ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # 11: Joint letter skipped
    payload = load_fixture("routing_from_endorsement_skipped.json")
    payload["doc_type"] = "joint_letter"
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 11: Joint letter skipped — no CCI-ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # 12: Multiple-address letter skipped
    payload = load_fixture("routing_from_endorsement_skipped.json")
    payload["doc_type"] = "multiple_address_letter"
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 12: Multiple-address letter skipped — no CCI-ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # 13: Both ROUTE-010 and ROUTE-011 trigger independently
    payload = load_fixture("routing_from_both_rules.json")
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_011(warnings, errors) and has_route_010(warnings)
    results.append(("Check 13: Both ROUTE-010 and ROUTE-011 trigger independently on same payload", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 13")

    # 14: Missing doc_type skips From-line check
    payload = load_fixture("routing_from_no_doctype.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 14: Missing doc_type skips From-line check — no CCI-ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 14")

    # 15: Existing CCI-ROUTE-010 behavior preserved
    payload = load_fixture("routing_from_both_rules.json")
    payload["from"] = "Commanding Officer, Example Activity"
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors) and has_route_010(warnings)
    results.append(("Check 15: Existing ROUTE-010 preserved when ROUTE-011 not triggered", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 15")

    # 16: Existing routing warnings still work (Via numbering)
    payload = {
        "doc_type": "DT_STD_LTR",
        "from": "Commanding Officer, Example Activity",
        "to": ["Commanding Officer, Recipient Activity"],
        "via": ["(1) First Intermediate", "(2) Second Intermediate", "(4) Third Intermediate"],
    }
    errors, warnings = validate_cci_routing(payload)
    ok = any("CCI-ROUTE-002" in w for w in warnings) or any("CCI-ROUTE-002" in e for e in errors)
    results.append(("Check 16: Existing routing warnings (Via numbering) still appear", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 16")

    # 17: No renderer/layout files changed
    result17 = run_git(
        ["git", "diff", "--stat", "HEAD", "--", "src/pdf_v6_render.py"]
    )
    ok = result17 == ""
    results.append(("Check 17: No renderer/layout files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 17")

    # 18: No prompt-contract files changed
    result18 = run_git(
        ["git", "diff", "--stat", "HEAD", "--", "src/context_resolver.py"]
    )
    ok = result18 == ""
    results.append(("Check 18: No prompt-contract files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 18")

    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.9 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.9 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAIL — {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
