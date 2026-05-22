#!/usr/bin/env python3
"""
C9 Regression Runner

Runs the non-visual regression checks for C9 new-page endorsement Phase 1.
Visual PDF review remains manual per docs/C9_REGRESSION_CHECKLIST.md.
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

    print("C9 REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {py}")
    print()

    passed = True

    # --- C9 validator checks (before render) ---

    c9_valid_fixtures: list[tuple[str, bool]] = [
        # (path, expect_pass) — expect_pass=True means exit 0, False means exit nonzero
        ("examples/audit_c9_new_page_endorsement_refs_encls_valid.json", True),
        ("examples/audit_c9_invalid_repeated_reference.json", False),
        ("examples/audit_c9_invalid_repeated_enclosure.json", False),
        ("examples/audit_c9_invalid_ref_encl_sequence.json", False),
    ]

    for fixture, expect_pass in c9_valid_fixtures:
        label = f"Validate C9 {Path(fixture).stem}"
        result = run_command(root, [py, "src/c9_validate.py", fixture], label)
        if expect_pass:
            if not result:
                passed = False
        else:
            # Expected FAIL fixture should exit nonzero; if it exits 0, runner fails
            if result:
                print(f"UNEXPECTED PASS — {fixture} should have failed validation")
                passed = False

    # --- C9 Copy to validator checks ---

    c9_copy_to_fixtures: list[tuple[str, bool]] = [
        ("examples/audit_c9_copy_to_significant_valid.json", True),
        ("examples/audit_c9_copy_to_routine_valid.json", True),
        ("examples/audit_c9_copy_to_missing_prior_endorser.json", False),
        ("examples/audit_c9_copy_to_missing_originator.json", False),
        ("examples/audit_c9_copy_to_missing_complete_annotation.json", False),
    ]

    for fixture, expect_pass in c9_copy_to_fixtures:
        label = f"Validate C9 {Path(fixture).stem}"
        result = run_command(root, [py, "src/c9_validate.py", fixture], label)
        if expect_pass:
            if not result:
                passed = False
        else:
            if result:
                print(f"UNEXPECTED PASS — {fixture} should have failed validation")
                passed = False

    # --- C9 render checks ---

    c9_render = [
        py,
        "src/pdf_v6_render.py",
        "examples/audit_c9_new_page_endorsement.json",
        "output/audit_c9_new_page_endorsement.pdf",
    ]

    if run_command(root, c9_render, "Render C9 new-page endorsement fixture"):
        if not check_pdf(root, "output/audit_c9_new_page_endorsement.pdf"):
            passed = False
    else:
        passed = False

    # --- C9 Via fixtures ---

    c9_single_via_render = [
        py,
        "src/pdf_v6_render.py",
        "examples/audit_c9_new_page_endorsement_single_via.json",
        "output/audit_c9_new_page_endorsement_single_via.pdf",
    ]

    if run_command(root, c9_single_via_render, "Render C9 single-Via new-page endorsement fixture"):
        if not check_pdf(root, "output/audit_c9_new_page_endorsement_single_via.pdf"):
            passed = False
    else:
        passed = False

    c9_multi_via_render = [
        py,
        "src/pdf_v6_render.py",
        "examples/audit_c9_new_page_endorsement_multiple_via.json",
        "output/audit_c9_new_page_endorsement_multiple_via.pdf",
    ]

    if run_command(root, c9_multi_via_render, "Render C9 multiple-Via new-page endorsement fixture"):
        if not check_pdf(root, "output/audit_c9_new_page_endorsement_multiple_via.pdf"):
            passed = False
    else:
        passed = False

    # ── C9 layout audit checks ──
    layout_audit_figure_9_2_args = [
        py,
        "tools/audit_pdf_layout.py",
        "--profile",
        "docs/layout_profiles/figure_9_2_new_page_endorsement.json",
        "--pdf",
        "output/audit_c9_new_page_endorsement.pdf",
    ]
    if not run_command(root, layout_audit_figure_9_2_args, "C9 layout audit Figure 9-2"):
        passed = False

    if not run_command(root, [py, "tools/run_c7_phase1_regression.py"], "Run C7 Phase 1 regression guard"):
        passed = False

    if not run_command(root, [py, "tools/run_c8_regression.py"], "Run C8 regression guard"):
        passed = False

    print("=" * 72)
    if passed:
        print("C9 REGRESSION RESULT: PASS")
        return 0

    print("C9 REGRESSION RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
