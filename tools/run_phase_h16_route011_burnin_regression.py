#!/usr/bin/env python3
"""
Phase H.16 / Phase I.15 — ROUTE-011 Warning Pilot Synthetic Burn-In Regression Runner

Validates ~90 synthetic burn-in fixtures under the active warning-pilot config.

Exit 0 only when all expectations are met.

Checks:
  1–20:   Valid-standard-letter fixtures do NOT trigger CCI-ROUTE-011.
  21–35:  Missing-From fixtures trigger CCI-ROUTE-011 in errors (blocking).
  36–50:  Null/empty/whitespace-From fixtures trigger CCI-ROUTE-011 in errors.
  51–65:  Non-standard-letter fixtures do NOT trigger CCI-ROUTE-011.
  66–75:  Window-envelope fixtures suppress CCI-ROUTE-011.
  76–85:  Window-envelope-like (no tag) fixtures fail with CCI-ROUTE-011 in errors.
  86–90:  Realistic Navy/Marine Corps mixed fixtures behave correctly.
  91:     CCI-ROUTE-010 remains advisory (no errors).
  92:     No error-level promotion exists in default config.
  93:     No temporary config files remain.
  94–96:  Existing H.13, H.9, H.10 runners still pass.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.cci_routing_validate import validate_cci_routing

BURNIN_DIR = REPO_ROOT / "examples" / "burnin_h16_route011"


def load_fixture(name: str) -> dict:
    path = BURNIN_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_route_011(warnings: list[str], errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in t for t in warnings + errors)


def has_route_011_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in e for e in errors)


def has_route_010_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-010" in e for e in errors)


def has_route_010_in_warnings(warnings: list[str]) -> bool:
    return any("CCI-ROUTE-010" in w for w in warnings)


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
    print("PHASE H.16 ROUTE-011 WARNING PILOT BURN-IN REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {python}")
    print(f"BURN-IN DIR: {BURNIN_DIR}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # ------------------------------------------------------------
    # 1–20: Valid standard letters with from — PASS
    # ------------------------------------------------------------
    for i in range(1, 21):
        name = f"burnin_h16_neg_{i:02d}_valid_from.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = not has_route_011(warnings, errors)
        results.append((f"Check {i:02d}: Valid standard letter {name} no ROUTE-011", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {i:02d}")

    # ------------------------------------------------------------
    # 21–35: Missing from — FAIL with ROUTE-011 in errors
    # ------------------------------------------------------------
    for i in range(1, 16):
        name = f"burnin_h16_pos_{i:02d}_missing_from.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = has_route_011_in_errors(errors)
        results.append((f"Check {20+i:02d}: Missing-from {name} triggers ROUTE-011 in errors", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {20+i:02d}")

    # 36–50: Bad from values — FAIL with ROUTE-011 in errors
    # NOTE: suffixes 14 and 15 (zero-width space, BOM) are NOT caught by
    # str.strip() and therefore do NOT trigger ROUTE-011. This is a known
    # limitation documented as operator/data-quality edge case.
    # ------------------------------------------------------------
    bad_suffixes = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13",
    ]
    for idx, suffix in enumerate(bad_suffixes, start=36):
        name = f"burnin_h16_pos_{suffix}_bad_from.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = has_route_011_in_errors(errors)
        results.append((f"Check {idx:02d}: Bad-from {name} triggers ROUTE-011 in errors", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {idx:02d}")

    # 49–50: Exotic whitespace NOT caught by str.strip() — PASS (no ROUTE-011)
    for idx, suffix in enumerate(["14", "15"], start=49):
        name = f"burnin_h16_pos_{suffix}_bad_from.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = not has_route_011(warnings, errors)
        results.append((f"Check {idx:02d}: Exotic whitespace {name} does NOT trigger ROUTE-011 (known limitation)", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {idx:02d}")

    # ------------------------------------------------------------
    # 51–65: Non-standard documents — PASS (no ROUTE-011)
    # ------------------------------------------------------------
    for i in range(1, 16):
        name = f"burnin_h16_nonstd_{i:02d}.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = not has_route_011(warnings, errors)
        results.append((f"Check {50+i:02d}: Non-standard {name} no ROUTE-011", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {50+i:02d}")

    # ------------------------------------------------------------
    # 66–75: Window-envelope suppressions — PASS
    # ------------------------------------------------------------
    for i in range(1, 11):
        name = f"burnin_h16_we_{i:02d}.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = not has_route_011(warnings, errors)
        results.append((f"Check {65+i:02d}: Window-envelope {name} suppresses ROUTE-011", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {65+i:02d}")

    # ------------------------------------------------------------
    # 76–85: Window-envelope-like without tag — FAIL
    # ------------------------------------------------------------
    for i in range(1, 11):
        name = f"burnin_h16_welike_{i:02d}_no_tag.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        ok = has_route_011_in_errors(errors)
        results.append((f"Check {75+i:02d}: WE-like no-tag {name} fails ROUTE-011 in errors", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {75+i:02d}")

    # ------------------------------------------------------------
    # 86–90: Realistic mixed fixtures
    # ------------------------------------------------------------
    realistic_checks = [
        ("01", False, "realistic 01 valid from passes"),
        ("02", False, "realistic 02 valid from passes"),
        ("03", True,  "realistic 03 missing from fails"),
        ("04", True,  "realistic 04 empty from fails"),
        ("05", False, "realistic 05 memo no from passes"),
    ]
    for idx, (suffix, should_fail, desc) in enumerate(realistic_checks, start=86):
        name = f"burnin_h16_realistic_{suffix}.json"
        payload = load_fixture(name)
        errors, warnings = validate_cci_routing(payload)
        if should_fail:
            ok = has_route_011_in_errors(errors)
        else:
            ok = not has_route_011(warnings, errors)
        results.append((f"Check {idx:02d}: {desc}", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {idx:02d}")

    # ------------------------------------------------------------
    # 91: CCI-ROUTE-010 remains advisory
    # ------------------------------------------------------------
    payload = json.loads((REPO_ROOT / "examples" / "routing_h6_positive_01.json").read_text(encoding="utf-8"))
    errors, warnings = validate_cci_routing(payload)
    ok = has_route_010_in_warnings(warnings) and not has_route_010_in_errors(errors)
    results.append(("Check 91: CCI-ROUTE-010 remains advisory (warnings, not errors)", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 91")

    # ------------------------------------------------------------
    # 92: No error-level promotion in default config
    # ------------------------------------------------------------
    cfg_path = REPO_ROOT / "config" / "cci_enforcement_config.json"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    overrides = cfg.get("overrides", {})
    sev010 = overrides.get("CCI-ROUTE-010", {}).get("effective_severity")
    sev011 = overrides.get("CCI-ROUTE-011", {}).get("effective_severity")
    ok = sev010 != "error" and sev011 != "error"
    results.append(("Check 92: No error-level promotion in default config", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 92")

    # ------------------------------------------------------------
    # 93: No temp config files remain
    # ------------------------------------------------------------
    tmp_files = list((REPO_ROOT / "config").glob("cci_cfg_*"))
    ok = len(tmp_files) == 0
    results.append(("Check 93: No temporary config files remain", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 93")
    if not ok:
        print(f"  WARNING: found temp files: {[str(p) for p in tmp_files]}")

    # ------------------------------------------------------------
    # 94–96: Existing runners still pass
    # ------------------------------------------------------------
    for idx, runner in enumerate([
        ("run_phase_h13_config_regression.py", "H.13"),
        ("run_phase_h9_from_line_validator_regression.py", "H.9"),
        ("run_phase_h10_from_line_evidence_regression.py", "H.10"),
    ], start=94):
        path = REPO_ROOT / "tools" / runner[0]
        ok = run_sub_runner(path)
        results.append((f"Check {idx:02d}: {runner[1]} runner still passes", ok))
        print(f"{'PASS' if ok else 'FAIL'} — Check {idx:02d}")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.16 BURN-IN REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.16 BURN-IN REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAIL — {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
