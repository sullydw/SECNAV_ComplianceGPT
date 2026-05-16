#!/usr/bin/env python3
"""
C8 Regression Runner

Runs the non-visual regression checks for C8 multiple-address / distribution
baseline. Visual PDF review remains manual per docs/C8_REGRESSION_CHECKLIST.md.
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


def check_pdf(root: Path, relative_path: str) -> bool:
    """Confirm the expected PDF exists and is non-empty."""
    pdf_path = root / relative_path

    print("=" * 72)
    print("CHECKING OUTPUT PDF")
    print(f"PATH: {pdf_path}")

    if not pdf_path.exists():
        print("RESULT: FAIL — PDF does not exist")
        return False

    size = pdf_path.stat().st_size
    print(f"SIZE: {size} bytes")

    if size <= 0:
        print("RESULT: FAIL — PDF is empty")
        return False

    print("RESULT: PASS — PDF exists and is non-empty")
    return True


def main() -> int:
    root = repo_root()
    py = sys.executable

    print("C8 REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {py}")
    print()

    render_checks = [
        (
            [
                py,
                "src/pdf_v6_render.py",
                "examples/audit_c8_to_only_letter.json",
                "output/audit_c8_to_only_letter.pdf",
            ],
            "Render C8 To-line-only fixture",
            "output/audit_c8_to_only_letter.pdf",
        ),
        (
            [
                py,
                "src/pdf_v6_render.py",
                "examples/audit_c8_distribution_only_letter.json",
                "output/audit_c8_distribution_only_letter.pdf",
            ],
            "Render C8 Distribution-only fixture",
            "output/audit_c8_distribution_only_letter.pdf",
        ),
        (
            [
                py,
                "src/pdf_v6_render.py",
                "examples/audit_c8_to_plus_distribution_letter.json",
                "output/audit_c8_to_plus_distribution_letter.pdf",
            ],
            "Render C8 To plus Distribution fixture",
            "output/audit_c8_to_plus_distribution_letter.pdf",
        ),
    ]

    passed = True

    for args, label, pdf_path in render_checks:
        if not run_command(root, args, label):
            passed = False
            continue

        if not check_pdf(root, pdf_path):
            passed = False

    c7_args = [py, "tools/run_c7_phase1_regression.py"]
    if not run_command(root, c7_args, "Run C7 Phase 1 regression guard"):
        passed = False

    print("=" * 72)
    if passed:
        print("C8 REGRESSION RESULT: PASS")
        return 0

    print("C8 REGRESSION RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
