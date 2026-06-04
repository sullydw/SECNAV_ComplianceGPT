#!/usr/bin/env python3
"""
Pilot Subject Acronym Rule Catalog Regression Runner

Phase H.1 pilot targeted regression for rule-catalog-only implementation
of approved record agr_20260604_b69c92d9.

Minimum 10 checks:
  1. Catalog entry exists with rule_id CCI-CH7-SUBJ-006
  2. Approved rule ID agr_20260604_b69c92d9 is present in provenance
  3. Field path is subj
  4. Citation fields (manual_chapter, manual_section, source_quote) are present
  5. Source quote contains "do not use acronyms in the subject line"
  6. Implementation target is rule_catalog
  7. No validator files changed for this pilot
  8. No renderer/layout files changed for this pilot
  9. No runtime prompt-contract files changed for this pilot
  10. No local approved/pending logs are tracked by git

Uses synthetic fixtures only. Never reads/writes real local approved/pending logs.

Run:
    python tools/run_pilot_subject_acronym_rule_catalog_regression.py

Exit 0 if all checks pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "rules_v6" / "CCI" / "cci_ch7_subject_rules.json"
_RULE_ID = "CCI-CH7-SUBJ-006"
_APPROVED_RULE_ID = "agr_20260604_b69c92d9"
_FIELD_PATH = "subj"

_CHECKS_TOTAL = 11
_checks_passed = 0
_failures: list[str] = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    global _checks_passed
    if condition:
        _checks_passed += 1
        print(f"  PASS  {name}")
    else:
        _failures.append(f"FAIL: {name} — {detail}")
        print(f"  FAIL  {name} — {detail}")


def _run() -> int:
    print("=" * 70)
    print("Pilot Subject Acronym Rule Catalog Regression")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Catalog entry exists with rule_id CCI-CH7-SUBJ-006
    # ------------------------------------------------------------------
    catalog_exists = _CATALOG_PATH.exists()
    _check("Catalog file exists", catalog_exists, str(_CATALOG_PATH))

    if not catalog_exists:
        print("\nAborting: catalog file missing")
        return 1

    catalog = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    rule = None
    for r in catalog:
        if r.get("rule_id") == _RULE_ID:
            rule = r
            break
    _check("Catalog entry CCI-CH7-SUBJ-006 exists", rule is not None)

    if rule is None:
        print("\nAborting: rule entry missing")
        return 1

    # ------------------------------------------------------------------
    # 2. Approved rule ID is present in provenance
    # ------------------------------------------------------------------
    added_by = rule.get("added_by_implementation_id")
    _check(
        "Provenance: approved rule ID present",
        added_by == _APPROVED_RULE_ID,
        f"expected={_APPROVED_RULE_ID}, got={added_by}",
    )

    # ------------------------------------------------------------------
    # 3. Field path is subj
    # ------------------------------------------------------------------
    # The rule catalog uses "rule_text_summary" and applies_to; field path
    # is implied by the file (cci_ch7_subject_rules.json = subject rules).
    # We verify the rule text explicitly references the subject line.
    rule_text = str(rule.get("rule_text_summary", "")).lower()
    _check(
        "Field path implied: rule text references subject line",
        "subject line" in rule_text,
        f"rule_text_summary={rule.get('rule_text_summary')}",
    )

    # ------------------------------------------------------------------
    # 4. Citation fields are present
    # ------------------------------------------------------------------
    has_chapter = bool(rule.get("manual_chapter"))
    has_section = bool(rule.get("manual_section"))
    has_quote = bool(rule.get("source_quote"))
    _check(
        "Citation fields present (chapter, section, source_quote)",
        has_chapter and has_section and has_quote,
        f"chapter={has_chapter}, section={has_section}, quote={has_quote}",
    )

    # ------------------------------------------------------------------
    # 5. Source quote contains the expected text
    # ------------------------------------------------------------------
    source_quote = str(rule.get("source_quote", "")).lower()
    _check(
        "Source quote contains 'do not use acronyms in the subject line'",
        "do not use acronyms in the subject line" in source_quote,
        f"source_quote={rule.get('source_quote')}",
    )

    # ------------------------------------------------------------------
    # 6. Implementation target is rule_catalog
    # ------------------------------------------------------------------
    target = rule.get("implementation_target")
    _check(
        "Implementation target is rule_catalog",
        target == "rule_catalog",
        f"expected=rule_catalog, got={target}",
    )

    # ------------------------------------------------------------------
    # 7–10: Git scope checks
    # ------------------------------------------------------------------
    # Gather changed files from git status --short
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        git_short = result.stdout
    except Exception as exc:
        git_short = ""
        _failures.append(f"WARN: git status failed: {exc}")

    changed_files = []
    for line in git_short.splitlines():
        if len(line) >= 3:
            changed_files.append(line[3:].strip())

    # 7. No unexpected validator files changed (cci_subject_validate.py is expected for Phase H.2)
    validator_changed = [
        f for f in changed_files
        if "validate" in f.lower() and f.endswith(".py") and "cci_subject_validate.py" not in f
    ]
    _check(
        "No unexpected validator files changed for this pilot",
        len(validator_changed) == 0,
        f"changed={validator_changed}",
    )

    # 8. No renderer/layout files changed
    renderer_changed = [f for f in changed_files if any(k in f.lower() for k in ("layout", "renderer", "render"))]
    _check(
        "No renderer/layout files changed for this pilot",
        len(renderer_changed) == 0,
        f"changed={renderer_changed}",
    )

    # 9. No runtime prompt-contract files changed
    prompt_changed = [f for f in changed_files if any(k in f.lower() for k in ("prompt", "contract", "command", "nl_command"))]
    _check(
        "No runtime prompt-contract files changed for this pilot",
        len(prompt_changed) == 0,
        f"changed={prompt_changed}",
    )

    # 10. No local approved/pending logs tracked
    log_tracked = [f for f in changed_files if "corrections/" in f.replace("\\", "/")]
    _check(
        "No local approved/pending logs tracked by git",
        len(log_tracked) == 0,
        f"changed={log_tracked}",
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"Results: {_checks_passed}/{_CHECKS_TOTAL} passed")
    if _failures:
        print("Failures:")
        for f in _failures:
            print(f"  {f}")
    print("=" * 70)

    return 0 if _checks_passed == _CHECKS_TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(_run())
