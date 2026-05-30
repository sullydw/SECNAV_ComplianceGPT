#!/usr/bin/env python3
"""
CCI Routing / Via / Copy-to Regression Runner

Runs the CCI routing validator against example files and reports results.

Usage:
    python tools/run_cci_routing_regression.py

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
    label = f"cci_routing_validate on {fixture}"
    print(f"RUNNING: {label}")
    print("-" * 72)

    result = subprocess.run(
        [sys.executable, "src/cci_routing_validate.py", f"examples/{fixture}"],
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
    print("CCI Content Intelligence - Routing / Via / Copy-to Regression Tests")
    print("=" * 72)
    print()

    root = repo_root()
    all_ok = True

    # Test 1: valid - single unnumbered Via, reasonable Copy-to
    if not run_validator(root, "audit_cci_routing_valid.json", expect_pass=True, expect_warnings=False):
        all_ok = False
    print()

    # Test 2: warning_via_unnumbered - multiple Via without numbering
    if not run_validator(root, "audit_cci_routing_warning_via_unnumbered.json", expect_pass=True, expect_warnings=True):
        all_ok = False
    print()

    # Test 3: warning_copyto_excess - >6 Copy-to entries
    if not run_validator(root, "audit_cci_routing_warning_copyto_excess.json", expect_pass=True, expect_warnings=True):
        all_ok = False
    print()

    # Test 4: warning_need_to_know - vague Copy-to entries
    if not run_validator(root, "audit_cci_routing_warning_need_to_know.json", expect_pass=True, expect_warnings=True):
        all_ok = False
    print()

    print("=" * 72)
    if all_ok:
        print("CCI ROUTING REGRESSION RESULT: PASS")
        return 0
    else:
        print("CCI ROUTING REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
