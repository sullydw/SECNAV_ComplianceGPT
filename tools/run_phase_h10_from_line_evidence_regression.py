#!/usr/bin/env python3
"""
Phase H.10 / Phase I.9 — From-Line Evidence Collection and Regression Hardening Runner

Validates evidence fixtures, corpus, and cross-phase compatibility for CCI-ROUTE-011.

Exit 0 only when all expectations are met.

Checks:
  1–20: Negative-control fixtures exist and do not trigger CCI-ROUTE-011.
  21–30: Positive-control fixtures exist and trigger CCI-ROUTE-011.
  31–32: window_envelope truthy values suppress (bool, string, int).
  33:    Missing doc_type skips.
  34:    Non-standard doc types skip.
  35:    CCI-ROUTE-010 behavior preserved.
  36:    H.9 runner still passes.
  37:    H.8 runner still passes.
  38:    Corpus path is gitignored and untracked.
  39:    No forbidden files changed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.cci_routing_validate import validate_cci_routing


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


def run_sub_runner(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        shell=False,
        timeout=120,
    )
    return result.returncode == 0


def main() -> int:
    python = sys.executable
    print("=" * 72)
    print("PHASE H.10 FROM-LINE EVIDENCE REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # Negative controls: existence + no trigger
    neg_fixtures = [
        "routing_from_h10_neg_01_standard_pass.json",
        "routing_from_h10_neg_02_window_envelope_true.json",
        "routing_from_h10_neg_03_missing_doctype.json",
        "routing_from_h10_neg_04_memo.json",
        "routing_from_h10_neg_05_mfr.json",
        "routing_from_h10_neg_06_endorsement.json",
        "routing_from_h10_neg_07_joint_letter.json",
        "routing_from_h10_neg_08_multiple_address.json",
        "routing_from_h10_neg_09_from_comma.json",
        "routing_from_h10_neg_10_from_parenthesis.json",
        "routing_from_h10_neg_11_window_envelope_yes.json",
        "routing_from_h10_neg_12_window_envelope_one.json",
        "routing_from_h10_neg_13_null_from_window.json",
        "routing_from_h10_neg_14_empty_from_window.json",
        "routing_from_h10_neg_15_whitespace_from_window.json",
        "routing_from_h10_neg_16_standard_letter.json",
        "routing_from_h10_neg_17_minimal_from.json",
        "routing_from_h10_neg_18_numeric_from.json",
        "routing_from_h10_neg_19_full_payload.json",
        "routing_from_h10_neg_20_explicit_false.json",
    ]

    for i, name in enumerate(neg_fixtures, start=1):
        path = REPO_ROOT / "examples" / name
        exists = path.exists()
        if exists:
            payload = load_fixture(name)
            errors, warnings = validate_cci_routing(payload)
            no_trigger = not has_route_011(warnings, errors)
        else:
            no_trigger = False
        ok = exists and no_trigger
        results.append((f"Check {i:02d}: Negative control {name} exists and no ROUTE-011", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {i:02d}")

    # Positive controls: existence + trigger
    pos_fixtures = [
        "routing_from_h10_pos_01_missing_from.json",
        "routing_from_h10_pos_02_empty_from.json",
        "routing_from_h10_pos_03_whitespace_from.json",
        "routing_from_h10_pos_04_tab_newline_from.json",
        "routing_from_h10_pos_05_standard_letter.json",
        "routing_from_h10_pos_06_null_from.json",
        "routing_from_h10_pos_07_dual_rule.json",
        "routing_from_h10_pos_08_complex_via.json",
        "routing_from_h10_pos_09_complex_copy_to.json",
        "routing_from_h10_pos_10_complex_distribution.json",
    ]

    for i, name in enumerate(pos_fixtures, start=21):
        path = REPO_ROOT / "examples" / name
        exists = path.exists()
        if exists:
            payload = load_fixture(name)
            errors, warnings = validate_cci_routing(payload)
            triggers = has_route_011(warnings, errors)
        else:
            triggers = False
        ok = exists and triggers
        results.append((f"Check {i:02d}: Positive control {name} exists and triggers ROUTE-011", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {i:02d}")

    # 31: window_envelope true suppresses
    payload = load_fixture("routing_from_h10_neg_02_window_envelope_true.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors)
    results.append(("Check 31: window_envelope=true suppresses advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 31")

    # 32: window_envelope truthy values suppress (string yes + int 1)
    payload = load_fixture("routing_from_h10_neg_11_window_envelope_yes.json")
    errors, warnings = validate_cci_routing(payload)
    ok_yes = not has_route_011(warnings, errors)

    payload = load_fixture("routing_from_h10_neg_12_window_envelope_one.json")
    errors, warnings = validate_cci_routing(payload)
    ok_one = not has_route_011(warnings, errors)

    ok = ok_yes and ok_one
    results.append(("Check 32: window_envelope truthy string/int suppresses advisory", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 32")

    # 33: missing doc_type skips
    payload = load_fixture("routing_from_h10_neg_03_missing_doctype.json")
    errors, warnings = validate_cci_routing(payload)
    ok = not has_route_011(warnings, errors) and len(errors) == 0
    results.append(("Check 33: Missing doc_type skips with empty errors", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 33")

    # 34: non-standard doc types skip
    for name in ["routing_from_h10_neg_04_memo.json", "routing_from_h10_neg_06_endorsement.json"]:
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = not has_route_011(warnings, errors) and len(errors) == 0
        if not ok:
            break
    results.append(("Check 34: Non-standard doc types skip with empty errors", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 34")

    # 35: CCI-ROUTE-010 preserved alongside ROUTE-011 under default warning config
    payload = load_fixture("routing_from_h10_pos_07_dual_rule.json")
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_010(warnings) and has_route_011(warnings, errors)
    results.append(("Check 35: CCI-ROUTE-010 preserved alongside ROUTE-011 (warning config)", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 35")

    # 36: H.9 runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_phase_h9_from_line_validator_regression.py")
    results.append(("Check 36: H.9 targeted runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 36")

    # 37: H.8 runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_phase_h8_third_rule_catalog_regression.py")
    results.append(("Check 37: H.8 targeted runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 37")

    # 38: Corpus path is gitignored and untracked
    result38 = run_git(["git", "status", "--short", "corrections/evidence/from_line_patterns.jsonl"])
    # Should be empty (ignored) or start with ?? (untracked)
    is_untracked = result38.startswith("??")
    is_ignored = result38 == ""
    ok = is_ignored or is_untracked
    results.append(("Check 38: Corpus file is untracked or ignored", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 38")
    if result38:
        print(f"  git status: {result38}")

    # 39: No forbidden files changed
    forbidden = [
        "src/pdf_v6_render.py", "src/context_resolver.py", "src/intake_orchestrator.py",
        "src/correction_commands.py", "src/correction_nl_commands.py",
        "rules_v6/CCI/cci_ch2_routing_rules.json",
    ]
    result39 = run_git(["git", "diff", "--stat", "HEAD", "--"] + forbidden)
    ok = result39 == ""
    results.append(("Check 39: No forbidden files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 39")

    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.10 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.10 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAIL — {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
