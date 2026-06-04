#!/usr/bin/env python3
"""
Phase H.2 Subject-Line Acronym Validator Advisory Regression Runner

Runs the CCI subject-line validator against synthetic fixtures that exercise
the new CCI-CH7-SUBJ-007 prohibited-acronym advisory.

Exit 0 only when all expectations are met.

Checks:
  1.  REQUEST FOR POC UPDATE                ->  SUBJ-007 advisory (positive)
  2.  REQUEST FOR UIC UPDATE                ->  SUBJ-007 advisory (positive)
  3.  REQUEST FROM OIC                    ->  SUBJ-007 advisory (positive)
  4.  REQUEST FOR POINT OF CONTACT UPDATE ->  no SUBJ-007        (negative)
  5.  POLICY UPDATE MEETING               ->  no SUBJ-007        (negative)
  6.  SECNAV POLICY UPDATE                ->  no SUBJ-007        (negative)
  7.  Existing SUBJ-004 unchanged on mixed-case fixture
  8.  Existing SUBJ-001 unchanged on invalid fixture
  9.  Body acronym validator unchanged
 10.  cci_acronym_validate.py not modified
 11.  No renderer/layout files modified
 12.  No approved/pending logs tracked
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_validator(root: Path, fixture: str) -> tuple[list[str], list[str]]:
    """Run cci_subject_validate.py and return (errors, warnings) as lists."""
    result = subprocess.run(
        [sys.executable, "src/cci_subject_validate.py", f"examples/{fixture}"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    errors: list[str] = []
    warnings: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("WARNING: "):
            warnings.append(line.replace("WARNING: ", ""))
        elif line.startswith("  ERROR: "):
            errors.append(line.replace("  ERROR: ", ""))
    return errors, warnings


def check_subj_007_present(warnings: list[str], expected_token: str) -> bool:
    return any(
        "CCI-CH7-SUBJ-007" in w and expected_token in w
        for w in warnings
    )


def check_subj_007_absent(warnings: list[str]) -> bool:
    return not any("CCI-CH7-SUBJ-007" in w for w in warnings)


def check_subj_004_present(warnings: list[str]) -> bool:
    return any("CCI-CH7-SUBJ-004" in w for w in warnings)


def check_subj_001_present(errors: list[str]) -> bool:
    return any("CCI-CH7-SUBJ-001" in e for e in errors)


def main() -> int:
    root = repo_root()
    python = sys.executable
    print("=" * 72)
    print("PHASE H.2 SUBJECT-LINE ACRONYM ADVISORY REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # 1. Positive: POC triggers SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_poc.json")
    ok = check_subj_007_present(warnings, "POC")
    results.append(("Check 01: POC subject triggers SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 01")

    # 2. Positive: UIC triggers SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_uic.json")
    ok = check_subj_007_present(warnings, "UIC")
    results.append(("Check 02: UIC subject triggers SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")

    # 3. Positive: OIC triggers SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_oic.json")
    ok = check_subj_007_present(warnings, "OIC")
    results.append(("Check 03: OIC subject triggers SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    # 4. Negative: Spelled-out POINT OF CONTACT does not trigger SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_no_acronym.json")
    ok = check_subj_007_absent(warnings)
    results.append(("Check 04: Spelled-out subject has no SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    # 5. Negative: Common all-caps words do not trigger SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_policy_update.json")
    ok = check_subj_007_absent(warnings)
    results.append(("Check 05: Common all-caps words have no SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # 6. Negative: Approved acronym SECNAV does not trigger SUBJ-007
    errors, warnings = run_validator(root, "audit_cci_subject_secnav.json")
    ok = check_subj_007_absent(warnings)
    results.append(("Check 06: Approved acronym SECNAV has no SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # 7. Existing SUBJ-004 unchanged on mixed-case fixture with acronym
    errors, warnings = run_validator(root, "audit_cci_subject_mixed_poc.json")
    ok = check_subj_004_present(warnings)
    results.append(("Check 07: Existing SUBJ-004 unchanged on mixed-case", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # 8. Existing SUBJ-001 unchanged on invalid fixture
    errors, warnings = run_validator(root, "audit_cci_subject_invalid.json")
    ok = check_subj_001_present(errors)
    results.append(("Check 08: Existing SUBJ-001 unchanged on invalid", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # 9. Body acronym validator is not imported or modified
    # We verify by running the body acronym validator against a fixture with a body
    # and confirming it still works independently.
    result9 = subprocess.run(
        [sys.executable, "src/cci_acronym_validate.py", "examples/audit_cci_acronym_valid.json"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    ok = "PASS" in result9.stdout and "FAIL" not in result9.stdout
    results.append(("Check 09: Body acronym validator unchanged", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # 10. cci_acronym_validate.py not modified (git diff check)
    result10 = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "src/cci_acronym_validate.py"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    ok = result10.stdout.strip() == ""
    results.append(("Check 10: cci_acronym_validate.py not modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # 11. No renderer/layout files modified (git diff check)
    result11 = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pdf_v6_render.py", "docs/layout_profiles/"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    ok = result11.stdout.strip() == ""
    results.append(("Check 11: No renderer/layout files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # 12. No approved/pending logs tracked or staged (git status check)
    result12 = subprocess.run(
        ["git", "status", "--short", "corrections/"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    ok = result12.stdout.strip() == ""
    results.append(("Check 12: No approved/pending logs tracked", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # Summary
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.2 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.2 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAILED: {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
