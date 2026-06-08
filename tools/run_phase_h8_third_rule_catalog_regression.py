#!/usr/bin/env python3
"""
Phase H.8 Third Rule-Catalog-Only Pilot Regression Runner

Runs verification checks for the CCI-ROUTE-011 From-line-required rule
catalog entry created from approved record agr_20260607_49947aca.

Exit 0 only when all expectations are met.

Checks:
  1.  Routing catalog JSON loads successfully.
  2.  Routing catalog has object schema with "rules" array.
  3.  Rule CCI-ROUTE-011 exists exactly once.
  4.  Rule CCI-ROUTE-010 still exists.
  5.  Rule source equals "SECNAV M-5216.5".
  6.  Rule source_location contains "Chapter 7" and "From:".
  7.  Rule source_quote contains "From:" and "window envelope".
  8.  Rule applies_to is ["standard_letter"] only.
  9.  Rule has implementation ID agr_20260607_49947aca.
 10.  Rule implementation_target equals "rule_catalog".
 11.  No validator files changed for H.8.
 12.  No renderer/layout files changed for H.8.
 13.  No prompt-contract files changed for H.8.
 14.  No Phase F/G command-layer files changed for H.8.
 15.  Approved/pending logs are not tracked/staged.
 16.  H.3 catalog entry CCI-ROUTE-010 remains present.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_git(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, shell=False)
    return result.stdout.strip()


def main() -> int:
    root = repo_root()
    python = sys.executable
    print("=" * 72)
    print("PHASE H.8 THIRD RULE-CATALOG-ONLY PILOT REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # Load catalog
    catalog_path = root / "rules_v6" / "CCI" / "cci_ch2_routing_rules.json"
    with catalog_path.open("r", encoding="utf-8") as f:
        catalog = json.load(f)

    # 1. JSON loads successfully (implicit if we got here)
    results.append(("Check 01: Routing catalog JSON loads successfully", True))
    print("PASS — Check 01")

    # 2. Object schema with "rules" array
    ok = isinstance(catalog, dict) and "rules" in catalog and isinstance(catalog["rules"], list)
    results.append(("Check 02: Catalog has object schema with 'rules' array", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")

    rules = catalog.get("rules", [])
    route_011 = [r for r in rules if r.get("rule_id") == "CCI-ROUTE-011"]
    route_010 = [r for r in rules if r.get("rule_id") == "CCI-ROUTE-010"]

    # 3. CCI-ROUTE-011 exists exactly once
    ok = len(route_011) == 1
    results.append(("Check 03: CCI-ROUTE-011 exists exactly once", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    # 4. CCI-ROUTE-010 still exists
    ok = len(route_010) == 1
    results.append(("Check 04: CCI-ROUTE-010 still exists", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    rule = route_011[0] if route_011 else {}

    # 5. Source equals SECNAV M-5216.5
    ok = rule.get("source") == "SECNAV M-5216.5"
    results.append(("Check 05: Rule source is SECNAV M-5216.5", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # 6. Source location contains Chapter 7 and From:
    loc = rule.get("source_location", "")
    ok = "Chapter 7" in loc and "From:" in loc
    results.append(("Check 06: Source location cites Chapter 7 with From:", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # 7. Source quote contains From: and window envelope
    quote = rule.get("source_quote", "")
    ok = '"From:"' in quote and "window envelope" in quote
    results.append(("Check 07: Source quote contains From: and window envelope", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # 8. applies_to is ["standard_letter"] only
    applies = rule.get("applies_to", [])
    ok = applies == ["standard_letter"]
    results.append(("Check 08: applies_to is ['standard_letter'] only", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # 9. Added by implementation ID
    ok = rule.get("added_by_implementation_id") == "agr_20260607_49947aca"
    results.append(("Check 09: Rule has implementation ID agr_20260607_49947aca", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # 10. Implementation target is rule_catalog
    ok = rule.get("implementation_target") == "rule_catalog"
    results.append(("Check 10: Rule implementation_target is rule_catalog", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # 11. No validator files modified (compare only the H.8 commit itself,
    #     not later phases like H.9 that legitimately modified validators)
    result11 = run_git(
        ["git", "diff", "--stat", "769437d^", "769437d", "--"] + [f"src/{m}" for m in [
            "cci_routing_validate.py", "cci_subject_validate.py", "cci_acronym_validate.py",
            "cci_ref_encl_validate.py", "cci_date_time_validate.py", "cci_personnel_validate.py",
            "cci_poc_validate.py",
        ]],
        root,
    )
    ok = result11 == ""
    results.append(("Check 11: No validator files modified at H.8 baseline", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # 12. No renderer/layout files changed
    result12 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pdf_v6_render.py", "docs/layout_profiles/"],
        root,
    )
    ok = result12 == ""
    results.append(("Check 12: No renderer/layout files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # 13. No prompt-contract files changed
    result13 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/context_resolver.py"],
        root,
    )
    ok = result13 == ""
    results.append(("Check 13: No prompt-contract files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 13")

    # 14. No Phase F/G command-layer files changed
    result14 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/correction_commands.py", "src/correction_nl_commands.py"],
        root,
    )
    ok = result14 == ""
    results.append(("Check 14: No Phase F/G command-layer files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 14")

    # 15. Approved/pending logs not tracked/staged
    result15 = run_git(
        ["git", "status", "--short", "corrections/"],
        root,
    )
    ok = result15 == ""
    results.append(("Check 15: No approved/pending logs tracked", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 15")

    # 16. H.3 catalog entry CCI-ROUTE-010 remains present
    ok = len(route_010) == 1 and route_010[0].get("rule_id") == "CCI-ROUTE-010"
    results.append(("Check 16: H.3 catalog entry CCI-ROUTE-010 remains present", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 16")

    # Summary
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.8 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.8 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAILED: {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
