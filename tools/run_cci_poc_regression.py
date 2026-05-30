#!/usr/bin/env python3
"""
CCI Point-of-Contact (POC) Regression Runner

Runs the CCI POC validator against example files and reports results.

Usage:
    python tools/run_cci_poc_regression.py

Exit codes:
    0 - all regressions passed
    1 - one or more regressions failed
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_validator(root: Path, fixture: str, expect_pass: bool, expect_warnings: bool = False) -> bool:
    print("=" * 72)
    label = f"cci_poc_validate on {fixture}"
    print(f"RUNNING: {label}")
    print("-" * 72)

    result = subprocess.run(
        [sys.executable, "src/cci_poc_validate.py", f"examples/{fixture}"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )

    if result.stdout.strip():
        print(result.stdout.rstrip())

    has_warnings = "WARNING:" in result.stdout
    has_fail = "FAIL" in result.stdout
    has_pass = "PASS" in result.stdout and not has_fail

    if expect_warnings and not has_warnings:
        print(f"RESULT: FAIL - expected warnings but none emitted for {fixture}")
        return False

    if expect_pass:
        if has_pass and not has_fail:
            print(f"RESULT: PASS - {fixture} as expected")
            return True
        else:
            print(f"RESULT: FAIL - expected PASS but got failure for {fixture}")
            return False
    else:
        if has_fail:
            print(f"RESULT: PASS - {fixture} correctly failed")
            return True
        else:
            print(f"RESULT: FAIL - expected FAIL but got pass for {fixture}")
            return False


def main() -> int:
    print("=" * 72)
    print("CCI Content Intelligence - Point-of-Contact Regression Tests")
    print("=" * 72)
    print()

    root = repo_root()
    all_ok = True

    # Test 1: valid - complete POC, no warnings expected
    if not run_validator(root, "audit_cci_poc_valid.json", expect_pass=True, expect_warnings=False):
        all_ok = False
    print()

    # Test 2: missing POC - should emit warnings but still PASS (v1 warnings only)
    if not run_validator(root, "audit_cci_poc_invalid_missing_poc.json", expect_pass=True, expect_warnings=True):
        all_ok = False
    print()

    # Test 3: incomplete POC - should emit warnings but still PASS
    if not run_validator(root, "audit_cci_poc_warning_incomplete_poc.json", expect_pass=True, expect_warnings=True):
        all_ok = False
    print()

    print("=" * 72)
    if all_ok:
        print("CCI POC REGRESSION RESULT: PASS")
        return 0
    else:
        print("CCI POC REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
