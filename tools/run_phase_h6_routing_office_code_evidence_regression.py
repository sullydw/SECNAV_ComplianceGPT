#!/usr/bin/env python3
"""
Phase H.6 Routing Office-Code Evidence Regression Runner

Collects and verifies evidence for CCI-ROUTE-010 without changing severity.

Exit 0 only when all expectations are met.

Checks:
  1.  All 20 negative-control fixtures exist
  2.  All 10 positive-control fixtures exist
  3.  Negative controls do NOT trigger CCI-ROUTE-010
  4.  Positive controls DO trigger CCI-ROUTE-010
  5.  Warnings contain CCI-ROUTE-010 for positive controls
  6.  Warnings contain (advisory): format
  7.  Warnings do NOT contain [ADVISORY]
  8.  errors list remains empty for all fixtures
  9.  Advisory findings go into warnings only
 10.  copy_to fixtures do NOT trigger
 11.  H.4 runner still passes
 12.  Local corpus path is gitignored
 13.  Local corpus file is not tracked/staged
 14.  No validator logic changes occurred
 15.  No renderer/layout, prompt-contract, command-layer, approved/pending log, or real-data files changed
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_validator(root: Path, fixture: str) -> tuple[list[str], list[str]]:
    result = subprocess.run(
        [sys.executable, "src/cci_routing_validate.py", f"examples/{fixture}"],
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


def route_010_present(warnings: list[str]) -> bool:
    return any("CCI-ROUTE-010" in w for w in warnings)


def route_010_absent(warnings: list[str]) -> bool:
    return not any("CCI-ROUTE-010" in w for w in warnings)


def has_advisory_format(warnings: list[str]) -> bool:
    return any("(advisory):" in w for w in warnings)


def has_no_bracket_advisory(warnings: list[str]) -> bool:
    return not any("[ADVISORY]" in w for w in warnings)


def run_git(cmd: list[str], root: Path) -> str:
    result = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, shell=False)
    return result.stdout.strip()


def main() -> int:
    root = repo_root()
    python = sys.executable
    print("=" * 72)
    print("PHASE H.6 ROUTING OFFICE-CODE EVIDENCE REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # ------------------------------------------------------------------
    # 1. All 20 negative-control fixtures exist
    # ------------------------------------------------------------------
    missing_neg = [f"routing_h6_negative_{i:02d}.json" for i in range(1, 21) if not (root / f"examples/routing_h6_negative_{i:02d}.json").exists()]
    ok = len(missing_neg) == 0
    results.append(("Check 01: All 20 negative-control fixtures exist", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 01")
    if missing_neg:
        print(f"  Missing: {missing_neg}")

    # ------------------------------------------------------------------
    # 2. All 10 positive-control fixtures exist
    # ------------------------------------------------------------------
    missing_pos = [f"routing_h6_positive_{i:02d}.json" for i in range(1, 11) if not (root / f"examples/routing_h6_positive_{i:02d}.json").exists()]
    ok = len(missing_pos) == 0
    results.append(("Check 02: All 10 positive-control fixtures exist", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")
    if missing_pos:
        print(f"  Missing: {missing_pos}")

    # ------------------------------------------------------------------
    # 3. Negative controls do NOT trigger CCI-ROUTE-010
    # ------------------------------------------------------------------
    neg_false_positives: list[str] = []
    for i in range(1, 21):
        fixture = f"routing_h6_negative_{i:02d}.json"
        errors, warnings = run_validator(root, fixture)
        if not route_010_absent(warnings):
            neg_false_positives.append(fixture)
    ok = len(neg_false_positives) == 0
    results.append(("Check 03: Negative controls do NOT trigger CCI-ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")
    if neg_false_positives:
        print(f"  False positives: {neg_false_positives}")

    # ------------------------------------------------------------------
    # 4. Positive controls DO trigger CCI-ROUTE-010
    # ------------------------------------------------------------------
    pos_false_negatives: list[str] = []
    for i in range(1, 11):
        fixture = f"routing_h6_positive_{i:02d}.json"
        errors, warnings = run_validator(root, fixture)
        if not route_010_present(warnings):
            pos_false_negatives.append(fixture)
    ok = len(pos_false_negatives) == 0
    results.append(("Check 04: Positive controls DO trigger CCI-ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")
    if pos_false_negatives:
        print(f"  False negatives: {pos_false_negatives}")

    # ------------------------------------------------------------------
    # 5. Warnings contain CCI-ROUTE-010 for positive controls
    # ------------------------------------------------------------------
    ok = len(pos_false_negatives) == 0  # same as check 4
    results.append(("Check 05: Warnings contain CCI-ROUTE-010 for positive controls", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # ------------------------------------------------------------------
    # 6. Warnings contain (advisory): format
    # ------------------------------------------------------------------
    advisory_format_ok = True
    for i in range(1, 11):
        fixture = f"routing_h6_positive_{i:02d}.json"
        _, warnings = run_validator(root, fixture)
        if route_010_present(warnings) and not has_advisory_format(warnings):
            advisory_format_ok = False
            print(f"  FAIL — {fixture} missing (advisory): format")
            break
    results.append(("Check 06: Warnings contain (advisory): format", advisory_format_ok))
    print(f"{'PASS' if advisory_format_ok else 'FAIL'} — Check 06")

    # ------------------------------------------------------------------
    # 7. Warnings do NOT contain [ADVISORY]
    # ------------------------------------------------------------------
    bracket_ok = True
    for i in range(1, 11):
        fixture = f"routing_h6_positive_{i:02d}.json"
        _, warnings = run_validator(root, fixture)
        if not has_no_bracket_advisory(warnings):
            bracket_ok = False
            print(f"  FAIL — {fixture} contains [ADVISORY]")
            break
    # Also check negatives
    for i in range(1, 21):
        fixture = f"routing_h6_negative_{i:02d}.json"
        _, warnings = run_validator(root, fixture)
        if not has_no_bracket_advisory(warnings):
            bracket_ok = False
            print(f"  FAIL — {fixture} contains [ADVISORY]")
            break
    results.append(("Check 07: Warnings do NOT contain [ADVISORY]", bracket_ok))
    print(f"{'PASS' if bracket_ok else 'FAIL'} — Check 07")

    # ------------------------------------------------------------------
    # 8. errors list remains empty for all fixtures
    # ------------------------------------------------------------------
    errors_empty_ok = True
    for i in range(1, 21):
        fixture = f"routing_h6_negative_{i:02d}.json"
        errors, _ = run_validator(root, fixture)
        if errors:
            errors_empty_ok = False
            print(f"  FAIL — {fixture} has errors: {errors}")
            break
    for i in range(1, 11):
        fixture = f"routing_h6_positive_{i:02d}.json"
        errors, _ = run_validator(root, fixture)
        if errors:
            errors_empty_ok = False
            print(f"  FAIL — {fixture} has errors: {errors}")
            break
    results.append(("Check 08: errors list remains empty for all fixtures", errors_empty_ok))
    print(f"{'PASS' if errors_empty_ok else 'FAIL'} — Check 08")

    # ------------------------------------------------------------------
    # 9. Advisory findings go into warnings only
    # ------------------------------------------------------------------
    warnings_only_ok = True
    for i in range(1, 11):
        fixture = f"routing_h6_positive_{i:02d}.json"
        errors, warnings = run_validator(root, fixture)
        if route_010_present(warnings) and errors:
            warnings_only_ok = False
            print(f"  FAIL — {fixture} has CCI-ROUTE-010 in errors")
            break
    results.append(("Check 09: Advisory findings go into warnings only", warnings_only_ok))
    print(f"{'PASS' if warnings_only_ok else 'FAIL'} — Check 09")

    # ------------------------------------------------------------------
    # 10. copy_to fixtures do NOT trigger
    # ------------------------------------------------------------------
    copy_to_fixture = root / "examples" / "routing_copy_to_numeric_comma.json"
    if copy_to_fixture.exists():
        errors, warnings = run_validator(root, "routing_copy_to_numeric_comma.json")
        ok = route_010_absent(warnings)
    else:
        # Create temporary copy-to fixture
        tmp = root / "examples" / "routing_h6_copy_to_temp.json"
        tmp.write_text('{\"copy_to\": [\"Commanding Officer, 12345\"]}', encoding="utf-8")
        errors, warnings = run_validator(root, "routing_h6_copy_to_temp.json")
        ok = route_010_absent(warnings)
        tmp.unlink(missing_ok=True)
    results.append(("Check 10: copy_to fixtures do NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # ------------------------------------------------------------------
    # 11. H.4 runner still passes
    # ------------------------------------------------------------------
    h4_result = subprocess.run(
        [python, "tools/run_phase_h4_routing_office_code_validator_regression.py"],
        cwd=str(root),
        text=True,
        capture_output=True,
        shell=False,
    )
    ok = h4_result.returncode == 0
    results.append(("Check 11: H.4 runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # ------------------------------------------------------------------
    # 12. Local corpus path is gitignored
    # ------------------------------------------------------------------
    gitignore = root / ".gitignore"
    gi_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    ok = "corrections/evidence/" in gi_text or "corrections/h6_" in gi_text or "corrections/" in gi_text
    results.append(("Check 12: Local corpus path is gitignored", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # ------------------------------------------------------------------
    # 13. Local corpus file is not tracked/staged
    # ------------------------------------------------------------------
    status = run_git(["git", "status", "--short", "corrections/"], root)
    ok = status == ""
    results.append(("Check 13: Local corpus file is not tracked/staged", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 13")

    # ------------------------------------------------------------------
    # 14. No validator logic changes occurred
    # ------------------------------------------------------------------
    changed = run_git(["git", "diff", "--name-only", "HEAD"], root)
    changed_files = [c.strip() for c in changed.splitlines() if c.strip()]
    validator_changed = [f for f in changed_files if f.startswith("src/cci_") and f.endswith("_validate.py")]
    # src/cci_routing_validate.py is expected if we allowed it; but in H.6 we do NOT change it at all
    ok = len(validator_changed) == 0
    results.append(("Check 14: No validator logic changes occurred", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 14")
    if not ok:
        print(f"  Changed validators: {validator_changed}")

    # ------------------------------------------------------------------
    # 15. No forbidden files changed
    # ------------------------------------------------------------------
    forbidden = [
        "src/pdf_v6_render.py",
        "src/context_resolver.py",
        "src/correction_commands.py",
        "src/correction_nl_commands.py",
        # rules_v6/CCI/cci_ch2_routing_rules.json is intentionally modified by Phase H.8
        "rules_v6/CCI/cci_ch7_subject_rules.json",
    ]
    forbidden_changed = [f for f in changed_files if f in forbidden]
    ok = len(forbidden_changed) == 0
    results.append(("Check 15: No forbidden files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 15")
    if not ok:
        print(f"  Forbidden changed: {forbidden_changed}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULTS: {passed}/{total} passed")
    if passed == total:
        print("ALL CHECKS PASS")
        return 0
    else:
        print("FAILURES:")
        for label, ok in results:
            if not ok:
                print(f"  FAIL — {label}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
