#!/usr/bin/env python3
"""
C7 Phase 1 Regression Runner

Runs the non-visual regression checks for the C7 Phase 1 standard-letter
baseline. Visual PDF review remains manual per docs/C7_PHASE1_REGRESSION_CHECKLIST.md.
"""

from __future__ import annotations

import os
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

    print("C7 PHASE 1 REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {py}")
    print()

    checks = [
        (
            [py, "src/body_v6_validate.py", "examples/audit_c7_phase1_standard_letter.json"],
            "Body validator on C7 Phase 1 fixture",
        ),
        (
            [
                py,
                "src/pdf_v6_render.py",
                "examples/audit_c7_phase1_standard_letter.json",
                "output/audit_c7_phase1_standard_letter.pdf",
            ],
            "Render C7 Phase 1 fixture",
        ),
        (
            [py, "src/pdf_v6_render.py"],
            "Default renderer smoke test",
        ),
        (
            [py, "src/joint_letter_validate.py", "examples/audit_c7_joint_letter.json"],
            "Joint letter validator on C7 joint letter fixture",
        ),
        (
            [
                py,
                "src/pdf_v6_render.py",
                "examples/audit_c7_joint_letter.json",
                "output/audit_c7_joint_letter.pdf",
            ],
            "Render C7 joint letter fixture",
        ),
    ]

    passed = True

    for args, label in checks:
        if not run_command(root, args, label):
            passed = False

    if not check_pdf(root, "output/audit_c7_phase1_standard_letter.pdf"):
        passed = False

    if not check_pdf(root, "output/audit_c7_joint_letter.pdf"):
        passed = False

    # Standalone layout audit (now wired into regression)
    layout_audit_args = [
        py,
        "tools/audit_pdf_layout.py",
        "--profile",
        "docs/layout_profiles/figure_7_1_standard_letter.json",
        "--pdf",
        "output/audit_c7_phase1_standard_letter.pdf",
    ]
    if not run_command(root, layout_audit_args, "C7 layout audit Figure 7-1"):
        passed = False

    layout_audit_args_2 = [
        py,
        "tools/audit_pdf_layout.py",
        "--profile",
        "docs/layout_profiles/figure_7_2_standard_letter_second_page.json",
        "--pdf",
        "output/audit_c7_phase1_standard_letter.pdf",
    ]
    if not run_command(root, layout_audit_args_2, "C7 layout audit Figure 7-2"):
        passed = False

    layout_audit_args_joint = [
        py,
        "tools/audit_pdf_layout.py",
        "--profile",
        "docs/layout_profiles/figure_7_4_joint_letter.json",
        "--pdf",
        "output/audit_c7_joint_letter.pdf",
    ]
    if not run_command(root, layout_audit_args_joint, "C7 layout audit Figure 7-4"):
        passed = False

    print("=" * 72)
    if passed:
        print("C7 PHASE 1 REGRESSION RESULT: PASS")
        return 0

    print("C7 PHASE 1 REGRESSION RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())