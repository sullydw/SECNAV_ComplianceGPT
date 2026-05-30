#!/usr/bin/env python3
"""
CCI Personnel Identification Regression Runner

Runs the CCI personnel validator against pass, fail, and warning fixtures.

Exit 0 only when all expectations are met.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_validator(root: Path, fixture: str, expected_pass: bool, expect_warnings: bool = False) -> bool:
    print("=" * 72)
    label = f"cci_personnel_validate on {fixture}"
    print(f"RUNNING: {label}")
    print("-" * 72)

    result = subprocess.run(
        [sys.executable, "src/cci_personnel_validate.py", f"examples/{fixture}"],
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
        print(f"RESULT: FAIL — expected warnings but none emitted for {fixture}")
        return False

    if expected_pass:
        if has_pass and not has_fail:
            print(f"RESULT: PASS — {fixture} as expected")
            return True
        else:
            print(f"RESULT: FAIL — expected PASS but got failure for {fixture}")
            return False
    else:
        if has_fail:
            print(f"RESULT: PASS — {fixture} correctly failed")
            return True
        else:
            print(f"RESULT: FAIL — expected FAIL but got pass for {fixture}")
            return False


def main() -> int:
    root = repo_root()
    python = sys.executable
    print("CCI PERSONNEL REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {python}")
    print()

    results = []

    results.append(run_validator(root, "audit_cci_personnel_valid.json", expected_pass=True, expect_warnings=False))
    results.append(run_validator(root, "audit_cci_personnel_invalid_lastname_allcaps.json", expected_pass=False, expect_warnings=False))
    results.append(run_validator(root, "audit_cci_personnel_warning_sailor_marine.json", expected_pass=True, expect_warnings=True))

    print("=" * 72)
    if all(results):
        print("CCI PERSONNEL REGRESSION RESULT: PASS")
        return 0
    else:
        print("CCI PERSONNEL REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
