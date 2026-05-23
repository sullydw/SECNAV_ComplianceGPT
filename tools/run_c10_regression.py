#!/usr/bin/env python3
"""
C10 Regression Runner

Runs the regression checks for C10 Phase 2C (MFR and From-To validators, MFR renderer).
Includes validator checks for MFR and From-To fixtures, render checks for MFR, and C7/C8/C9 guard checks.
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
        # MFR fixtures
        ("examples/audit_c10_mfr_with_subject.json", True),
        ("examples/audit_c10_mfr_short_no_subject.json", True),
        # From-To fixtures
        ("examples/audit_c10_from_to_plain_basic.json", True),
        ("examples/audit_c10_from_to_plain_with_refs.json", True),
        ("examples/audit_c10_from_to_plain_with_encls.json", True),
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

    # --- C10 render checks ---

    c10_renders: list[tuple[str, str]] = [
        # (input_json, output_pdf)
        ("examples/audit_c10_mfr_with_subject.json", "output/audit_c10_mfr_with_subject.pdf"),
        ("examples/audit_c10_mfr_short_no_subject.json", "output/audit_c10_mfr_short_no_subject.pdf"),
        ("examples/audit_c10_from_to_plain_basic.json", "output/audit_c10_from_to_plain_basic.pdf"),
        ("examples/audit_c10_from_to_plain_with_refs.json", "output/audit_c10_from_to_plain_with_refs.pdf"),
        ("examples/audit_c10_from_to_plain_with_encls.json", "output/audit_c10_from_to_plain_with_encls.pdf"),
    ]

    for input_json, output_pdf in c10_renders:
        label = f"Render C10 {Path(input_json).stem}"
        if not run_command(root, [py, "src/pdf_v6_render.py", input_json, output_pdf], label):
            passed = False
        
        # Check PDF exists and is non-empty
        pdf_path = root / output_pdf
        if not pdf_path.exists():
            print(f"ERROR: PDF not created: {output_pdf}")
            passed = False
        else:
            size = pdf_path.stat().st_size
            if size == 0:
                print(f"ERROR: PDF is empty: {output_pdf}")
                passed = False
            else:
                print(f"PDF CHECK: {output_pdf} — {size} bytes — PASS")

    # --- C10 layout audit Figure 10-1 MFR ---

    label = "C10 layout audit Figure 10-1 MFR"
    audit_cmd = [
        py, "tools/audit_pdf_layout.py",
        "--profile", "docs/layout_profiles/figure_10_1_mfr.json",
        "--pdf", "output/audit_c10_mfr_with_subject.pdf",
    ]
    if not run_command(root, audit_cmd, label):
        passed = False

    # --- C10 layout audit Figure 10-3 From-To Plain Basic ---

    label = "C10 layout audit Figure 10-3 From-To Plain Basic"
    audit_cmd = [
        py, "tools/audit_pdf_layout.py",
        "--profile", "docs/layout_profiles/figure_10_from_to_plain_basic.json",
        "--pdf", "output/audit_c10_from_to_plain_basic.pdf",
    ]
    if not run_command(root, audit_cmd, label):
        passed = False

    # --- C10 layout audit Figure 10-3 From-To Plain Refs ---

    label = "C10 layout audit Figure 10-3 From-To Plain Refs"
    audit_cmd = [
        py, "tools/audit_pdf_layout.py",
        "--profile", "docs/layout_profiles/figure_10_from_to_plain_with_refs.json",
        "--pdf", "output/audit_c10_from_to_plain_with_refs.pdf",
    ]
    if not run_command(root, audit_cmd, label):
        passed = False

    # --- C10 layout audit Figure 10-3 From-To Plain Encls ---

    label = "C10 layout audit Figure 10-3 From-To Plain Encls"
    audit_cmd = [
        py, "tools/audit_pdf_layout.py",
        "--profile", "docs/layout_profiles/figure_10_from_to_plain_with_encls.json",
        "--pdf", "output/audit_c10_from_to_plain_with_encls.pdf",
    ]
    if not run_command(root, audit_cmd, label):
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
