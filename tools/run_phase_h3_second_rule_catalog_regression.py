#!/usr/bin/env python3
"""
Phase H.3 Second Rule-Catalog-Only Pilot Regression Runner

Runs verification checks for the CCI-ROUTE-010 office code prefix rule
catalog entry created from approved record agr_20260604_7b5d44a2.

Exit 0 only when all expectations are met.

Checks:
  1.  Routing catalog JSON loads successfully.
  2.  Routing catalog has object schema with "rules" array.
  3.  Rule CCI-ROUTE-010 exists exactly once.
  4.  Rule source equals "SECNAV M-5216.5".
  5.  Rule source_location contains "Chapter 7, paragraph 7-2.7a".
  6.  Rule source_quote contains both required phrases.
  7.  Rule text implies routing.office_code domain.
  8.  Rule has implementation ID agr_20260604_7b5d44a2.
  9.  Rule implementation_target equals "rule_catalog".
 10.  No validator files changed for H.3.
 11.  No renderer/layout files changed for H.3.
 12.  No prompt-contract files changed for H.3.
 13.  No Phase F/G command-layer files changed for H.3.
 14.  Approved/pending logs are not tracked/staged.
 15.  H.2 catalog entry CCI-CH7-SUBJ-006 remains present.
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
    print("PHASE H.3 SECOND RULE-CATALOG-ONLY PILOT REGRESSION RUNNER")
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
    route_010 = [r for r in rules if r.get("rule_id") == "CCI-ROUTE-010"]

    # 3. CCI-ROUTE-010 exists exactly once
    ok = len(route_010) == 1
    results.append(("Check 03: CCI-ROUTE-010 exists exactly once", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    rule = route_010[0] if route_010 else {}

    # 4. Source equals SECNAV M-5216.5
    ok = rule.get("source") == "SECNAV M-5216.5"
    results.append(("Check 04: Rule source is SECNAV M-5216.5", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    # 5. Source location contains Chapter 7, paragraph 7-2.7a
    loc = rule.get("source_location", "")
    ok = "Chapter 7" in loc and "7-2.7a" in loc
    results.append(("Check 05: Source location cites Chapter 7, paragraph 7-2.7a", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # 6. Source quote contains both required phrases
    quote = rule.get("source_quote", "")
    ok = (
        'add the word "Code" before the numbers' in quote
        and 'Do not add the word "Code" before an office code that starts with a letter' in quote
    )
    results.append(("Check 06: Source quote contains both required phrases", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # 7. Rule text implies routing.office_code domain
    summary = rule.get("rule_text_summary", "")
    ok = "office code" in summary.lower() and "Code" in summary
    results.append(("Check 07: Rule text implies routing.office_code domain", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # 8. Added by implementation ID
    ok = rule.get("added_by_implementation_id") == "agr_20260604_7b5d44a2"
    results.append(("Check 08: Rule has implementation ID agr_20260604_7b5d44a2", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # 9. Implementation target is rule_catalog
    ok = rule.get("implementation_target") == "rule_catalog"
    results.append(("Check 09: Rule implementation_target is rule_catalog", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # 10. No unexpected validator files modified beyond cci_routing_validate.py (Phase H.4)
    result10 = run_git(
        ["git", "diff", "--stat", "HEAD", "--"] + [f"src/{m}" for m in [
            "cci_subject_validate.py", "cci_acronym_validate.py", "cci_ref_encl_validate.py",
            "cci_date_time_validate.py", "cci_personnel_validate.py", "cci_poc_validate.py",
        ]],
        root,
    )
    ok = result10 == ""
    results.append(("Check 10: No unexpected validator files modified (cci_routing_validate.py allowed for H.4)", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # 11. No renderer/layout files changed
    result11 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pdf_v6_render.py", "docs/layout_profiles/"],
        root,
    )
    ok = result11 == ""
    results.append(("Check 11: No renderer/layout files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # 12. No prompt-contract files changed
    result12 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/context_resolver.py"],
        root,
    )
    ok = result12 == ""
    results.append(("Check 12: No prompt-contract files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 12")

    # 13. No Phase F/G command-layer files changed
    result13 = run_git(
        ["git", "diff", "--name-only", "HEAD", "--", "src/correction_commands.py", "src/correction_nl_commands.py"],
        root,
    )
    ok = result13 == ""
    results.append(("Check 13: No Phase F/G command-layer files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 13")

    # 14. Approved/pending logs not tracked/staged
    result14 = run_git(
        ["git", "status", "--short", "corrections/"],
        root,
    )
    ok = result14 == ""
    results.append(("Check 14: No approved/pending logs tracked", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 14")

    # 15. H.2 catalog entry still present
    subject_path = root / "rules_v6" / "CCI" / "cci_ch7_subject_rules.json"
    with subject_path.open("r", encoding="utf-8") as f:
        subject_rules = json.load(f)
    ok = any(r.get("rule_id") == "CCI-CH7-SUBJ-006" for r in subject_rules)
    results.append(("Check 15: H.2 catalog entry CCI-CH7-SUBJ-006 remains present", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 15")

    # Summary
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE H.3 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE H.3 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAILED: {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
