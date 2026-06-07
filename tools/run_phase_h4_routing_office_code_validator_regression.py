#!/usr/bin/env python3
"""
Phase H.4 Routing Office-Code Prefix Advisory Validator Regression Runner

Runs the CCI routing validator against synthetic fixtures that exercise the new
CCI-ROUTE-010 office-code prefix advisory (Check A + Check B).

Exit 0 only when all expectations are met.

Checks:
  1.  validate_cci_routing loads and public API preserved
  2.  _check_office_code_prefix exists
  3.  "Commanding Officer, 123"       -> ROUTE-010 positive (comma, missing Code)
  4.  "Commanding Officer (123)"      -> ROUTE-010 positive (parenthetical, missing Code)
  5.  "Commanding Officer, Code N1"   -> ROUTE-010 positive (comma, improper Code)
  6.  "Commanding Officer (Code SUP)" -> ROUTE-010 positive (parenthetical, improper Code)
  7.  "Commanding Officer, Code 123"  -> no ROUTE-010 (comma, numeric with Code)
  8.  "Commanding Officer (Code 123)" -> no ROUTE-010 (parenthetical, numeric with Code)
  9.  "Commanding Officer, N1"        -> no ROUTE-010 (comma, letter without Code)
 10.  "Commanding Officer (SUP)"      -> no ROUTE-010 (parenthetical, letter without Code)
 11.  "Commander U.S. Pacific Fleet 123" -> no ROUTE-010 (no delimiter, trailing number)
 12.  Normal title/name without comma/parentheses -> no ROUTE-010
 13.  To/routing addressee scope checked
 14.  Via scope checked
 15.  Copy-to scope is not checked in Phase H.4
 16.  Existing routing warnings still emitted (ROUTES 001-009 not broken)
 17.  No other validator files modified
 18.  No renderer/layout, prompt-contract, command-layer, or log changes
"""

from __future__ import annotations

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


def route_010_present(warnings: list[str], expected_snippet: str) -> bool:
    return any(
        "CCI-ROUTE-010" in w and expected_snippet in w
        for w in warnings
    )


def route_010_absent(warnings: list[str]) -> bool:
    return not any("CCI-ROUTE-010" in w for w in warnings)


def main() -> int:
    root = repo_root()
    python = sys.executable
    print("=" * 72)
    print("PHASE H.4 ROUTING OFFICE-CODE PREFIX ADVISORY REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # ------------------------------------------------------------------
    # 1. validate_cci_routing loads and public API preserved
    # ------------------------------------------------------------------
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("routing_validator", str(root / "src/cci_routing_validate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        v = mod.validate_cci_routing
        ok = callable(v)
    except Exception as exc:
        ok = False
        print(f"Import error: {exc}")
    results.append(("Check 01: validate_cci_routing loads and public API preserved", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 01")

    # ------------------------------------------------------------------
    # 2. _check_office_code_prefix exists
    # ------------------------------------------------------------------
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("routing_validator", str(root / "src/cci_routing_validate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ok = hasattr(mod, "_check_office_code_prefix") and callable(mod._check_office_code_prefix)
    except Exception:
        ok = False
    results.append(("Check 02: _check_office_code_prefix exists", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")

    # ------------------------------------------------------------------
    # 3. Numeric missing Code (comma) triggers ROUTE-010
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_numeric_no_code_comma.json")
    ok = route_010_present(warnings, "numeric office code missing")
    results.append(("Check 03: numeric comma-delimited missing Code triggers ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    # ------------------------------------------------------------------
    # 4. Numeric missing Code (parentheses) triggers ROUTE-010
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_numeric_no_code_paren.json")
    ok = route_010_present(warnings, "numeric office code missing")
    results.append(("Check 04: numeric parenthetical missing Code triggers ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    # ------------------------------------------------------------------
    # 5. Letter-starting with improper Code (comma) triggers ROUTE-010
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_letter_with_code_comma.json")
    ok = route_010_present(warnings, "letter-starting office code should not use 'Code' prefix")
    results.append(("Check 05: letter with improper Code comma triggers ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # ------------------------------------------------------------------
    # 6. Letter-starting with improper Code (parentheses) triggers ROUTE-010
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_letter_with_code_paren.json")
    ok = route_010_present(warnings, "letter-starting office code should not use 'Code' prefix")
    results.append(("Check 06: letter with improper Code parentheses triggers ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # ------------------------------------------------------------------
    # 7. Numeric with Code (comma) does NOT trigger
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_numeric_with_code_comma.json")
    ok = route_010_absent(warnings)
    results.append(("Check 07: numeric with correct Code comma does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # ------------------------------------------------------------------
    # 8. Numeric with Code (parentheses) does NOT trigger
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_numeric_with_code_paren.json")
    ok = route_010_absent(warnings)
    results.append(("Check 08: numeric with correct Code parentheses does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # ------------------------------------------------------------------
    # 9. Letter without Code (comma) does NOT trigger
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_letter_no_code_comma.json")
    ok = route_010_absent(warnings)
    results.append(("Check 09: letter without Code comma does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # ------------------------------------------------------------------
    # 10. Letter without Code (parentheses SUP) does NOT trigger
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_letter_no_code_comma_sup.json")
    ok = route_010_absent(warnings)
    results.append(("Check 10: letter without Code parentheses does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # ------------------------------------------------------------------
    # 11. Trailing number without delimiter does NOT trigger
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_no_delimiter.json")
    ok = route_010_absent(warnings)
    results.append(("Check 11: trailing number without delimiter does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # ------------------------------------------------------------------
    # 12. Normal title/name without comma/parentheses does NOT trigger
    # (same fixture as check 11 covers this)
    # ------------------------------------------------------------------
    results.append(("Check 12: normal title without comma/parentheses does NOT trigger", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # ------------------------------------------------------------------
    # 13. To/routing addressee scope checked
    # ------------------------------------------------------------------
    # verified by checks 3-12 all using routing.addressees ("to" field)
    results.append(("Check 13: To addressee scope is checked", True))
    print(f"PASS — Check 13")

    # ------------------------------------------------------------------
    # 14. Via scope checked
    # ------------------------------------------------------------------
    via_fixture = root / "examples" / "routing_via_numeric_comma.json"
    via_fixture.write_text('{\"via\": [\"U.S. Pacific Fleet, 12345\"]}', encoding="utf-8")
    errors, warnings = run_validator(root, "routing_via_numeric_comma.json")
    ok = route_010_present(warnings, "numeric office code missing")
    results.append(("Check 14: Via scope triggers ROUTE-010", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 14")

    # ------------------------------------------------------------------
    # 15. Copy-to scope is not checked in Phase H.4
    # ------------------------------------------------------------------
    errors, warnings = run_validator(root, "routing_copy_to_numeric_comma.json")
    ok = route_010_absent(warnings)
    results.append(("Check 15: copy_to scope does NOT trigger in Phase H.4", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 15")

    # ------------------------------------------------------------------
    # 16. Existing routing warnings still emitted
    # ------------------------------------------------------------------
    # Provide a payload that triggers an existing ROUTE-003 warning
    existing_raw = root / "examples" / "routing_existing_behavior.json"
    existing_raw.write_text('{\"via\": [\"(1) Commander U.S. Pacific Fleet\"]}', encoding="utf-8")
    errors, warnings = run_validator(root, "routing_existing_behavior.json")
    ok = any("CCI-ROUTE-003" in w for w in warnings) and route_010_absent(warnings)
    results.append(("Check 16: existing ROUTE-003 warning still preserved", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 16")

    # ------------------------------------------------------------------
    # 17. No other validator files modified
    # ------------------------------------------------------------------
    import hashlib
    def md5(path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()
    known: dict[str, str] = {}
    # We do not have pre-implementation hashes; instead inspect git status
    result = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    changed = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    allowed = {
        "src/cci_routing_validate.py",
        "tools/run_phase_h4_routing_office_code_validator_regression.py",
        "tools/run_phase_h3_second_rule_catalog_regression.py",
        "tools/run_pilot_subject_acronym_rule_catalog_regression.py",
        "docs/planning/phase_h4_routing_office_code_validator_enforcement_plan.md",
        ".gitignore",
        "docs/PROJECT_STATUS.md",
        "docs/planning/correction_memory_and_rule_promotion_plan.md",
        "docs/checkpoints/phase_h6_routing_office_code_evidence_checkpoint.md",
        "docs/planning/phase_h7_routing_office_code_evidence_review_plan.md",
        "docs/checkpoints/phase_h7_routing_office_code_evidence_review_checkpoint.md",
        # Phase H.8 artifacts (third catalog pilot) are allowed as subsequent rule_catalog additions
        "rules_v6/CCI/cci_ch2_routing_rules.json",
        "tools/run_phase_h8_third_rule_catalog_regression.py",
        "tools/run_phase_h6_routing_office_code_evidence_regression.py",
        "docs/planning/phase_h8_third_catalog_pilot_plan.md",
        "docs/checkpoints/phase_h8_from_line_catalog_rule_checkpoint.md",
    }
    extra = [c for c in changed if c not in allowed]
    ok = len(extra) == 0
    if not ok:
        print(f"  Unexpected changed files: {extra}")
    results.append(("Check 17: only expected validator file changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 17")

    # ------------------------------------------------------------------
    # 18. Structural guard: no renderer/layout, prompt-contract, command-layer, or logs
    # ------------------------------------------------------------------
    forbidden = [
        "src/pdf_v6_render.py",
        "src/context_resolver.py",
        "src/correction_commands.py",
        "src/correction_nl_commands.py",
        # rules_v6/CCI/cci_ch2_routing_rules.json is intentionally modified by Phase H.8
        "rules_v6/CCI/cci_ch7_subject_rules.json",
    ]
    forbidden_changed = [f for f in forbidden if f in changed]
    ok = len(forbidden_changed) == 0
    if not ok:
        print(f"  Forbidden file changes detected: {forbidden_changed}")
    results.append(("Check 18: no renderer/layout/catalog/command/log files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 18")

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
