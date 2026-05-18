#!/usr/bin/env python3
"""
C10 Regression Runner

Runs the non-visual regression checks for C10 Phase 0C (MFR validator and runner).
No renderer checks yet — validator and guard checks only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """Resolve the repository root from this script location."""
    return Path(__file__).resolve().parents[1]


def run_command(root: Path, args: list[str], label: str) -> bool:
    """Run a command from repo root and print a clear result block."""
    print("=" * 72)
    print(f"RUNNING: {label}")
    print("COMMAND:", " ".join(args))
    print("-" * 72)

    result = subprocess.run(
        args,
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )

    if result.stdout.strip():
        print("STDOUT:")
        print(result.stdout.rstrip())

    if result.stderr.strip():
        print("STDERR:")
        print(result.stderr.rstrip())

    if result.returncode == 0:
        print(f"RESULT: PASS — {label}")
        return True

    print(f"RESULT: FAIL — {label} returned {result.returncode}")
    return False


def main() -> int:
    root = repo_root()
    py = sys.executable

    print("C10 REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {py}")
    print()

    passed = True

    # --- C10 validator checks ---

    c10_fixtures: list[tuple[str, bool]] = [
        # (path, expect_pass) — expect_pass=True means exit 0, False means exit nonzero
        ("examples/audit_c10_mfr_with_subject.json", True),
        ("examples/audit_c10_mfr_short_no_subject.json", True),
    ]

    for fixture, expect_pass in c10_fixtures:
        label = f"Validate C10 {Path(fixture).stem}"
        result = run_command(root, [py, "src/c10_validate.py", fixture], label)
        if expect_pass:
            if not result:
                passed = False
        else:
            # Expected FAIL fixture should exit nonzero; if it exits 0, runner fails
            if result:
                print(f"UNEXPECTED PASS — {fixture} should have failed validation")
                passed = False

    # --- Baseline guards ---

    if not run_command(root, [py, "tools/run_c7_phase1_regression.py"], "Run C7 Phase 1 regression guard"):
        passed = False

    if not run_command(root, [py, "tools/run_c8_regression.py"], "Run C8 regression guard"):
        passed = False

    if not run_command(root, [py, "tools/run_c9_regression.py"], "Run C9 regression guard"):
        passed = False

    print("=" * 72)
    if passed:
        print("C10 REGRESSION RESULT: PASS")
        return 0

    print("C10 REGRESSION RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
