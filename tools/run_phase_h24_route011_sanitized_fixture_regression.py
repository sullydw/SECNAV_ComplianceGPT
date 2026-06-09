#!/usr/bin/env python3
"""
Phase H.24 / Phase I.23 — ROUTE-011 Sanitized Fixture Regression Runner

Validates 32 sanitized/synthetic fixtures against the active warning-pilot config.

Exit 0 only when all expectations are met.

Checks:
  1–32:  Fixture expectations match actual validator output.
  33:    Fixture count matches manifest _total_fixtures.
  34:    All fixtures have synthetic/sanitized marker.
  35:    No false positives.
  36:    No false negatives.
  37:    Severity matches expectations.
  38:    Window-envelope suppression works.
  39:    Non-standard documents do not trigger CCI-ROUTE-011.
  40:    H.13 config regression still passes.
  41:    H.16 burn-in regression still passes.
  42:    H.9 From-line validator regression still passes.
  43:    H.10 From-line evidence regression still passes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.cci_routing_validate import validate_cci_routing

FIXTURE_DIR = REPO_ROOT / "examples" / "burnin_h24_route011_sanitized"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_route_011(warnings: list[str], errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in t for t in warnings + errors)


def has_route_011_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in e for e in errors)


def run_sub_runner(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        shell=False,
        timeout=120,
    )
    return result.returncode == 0


def main() -> int:
    python = sys.executable
    print("=" * 72)
    print("PHASE H.24 ROUTE-011 SANITIZED FIXTURE REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {python}")
    print(f"FIXTURE DIR: {FIXTURE_DIR}")
    print("=" * 72)

    if not FIXTURE_DIR.exists():
        print(f"FAIL: fixture directory does not exist: {FIXTURE_DIR}")
        return 1

    # Load manifest
    try:
        manifest = load_manifest()
    except Exception as exc:
        print(f"FAIL: manifest.json does not parse: {exc}")
        return 1

    expected_total = manifest.get("_total_fixtures", 0)
    fixtures_meta = manifest.get("fixtures", [])
    actual_fixtures = [f for f in FIXTURE_DIR.iterdir() if f.suffix == ".json" and f.name != "manifest.json"]
    actual_count = len(actual_fixtures)

    print(f"INFO: manifest declares {expected_total} fixtures")
    print(f"INFO: found {actual_count} fixture JSON files")

    if expected_total != actual_count:
        print(f"FAIL: fixture count mismatch — manifest={expected_total}, actual={actual_count}")
        return 1

    passed = 0
    failed = 0
    results: list[tuple[str, str, str]] = []

    for meta in fixtures_meta:
        fname = meta["fixture_filename"]
        fid = meta["fixture_id"]
        cat = meta["category"]
        exp_present = meta["expected_route011_present"]
        exp_severity = meta["expected_severity"]
        exp_count = meta["expected_finding_count"]
        tests_we = meta["tests_window_envelope"]
        marker = meta.get("marker", "")

        # Check marker
        if marker not in ("synthetic", "sanitized"):
            print(f"FAIL [{fid}] {fname}: missing synthetic/sanitized marker")
            failed += 1
            results.append((fid, "FAIL", "missing marker"))
            continue

        # Load payload
        try:
            payload = load_fixture(fname)
        except Exception as exc:
            print(f"FAIL [{fid}] {fname}: payload does not parse: {exc}")
            failed += 1
            results.append((fid, "FAIL", "parse error"))
            continue

        # Validate
        errors, warnings = validate_cci_routing(payload)
        actual_present = has_route_011(warnings, errors)
        actual_in_errors = has_route_011_in_errors(errors)

        # Determine actual severity placement
        if actual_in_errors:
            actual_sev = "warning"  # because config is warning
        elif any("CCI-ROUTE-011" in w for w in warnings):
            actual_sev = "advisory"
        else:
            actual_sev = "none"

        # Count findings
        actual_count = sum(1 for t in errors + warnings if "CCI-ROUTE-011" in t)

        ok = True
        reasons: list[str] = []

        # Check expected presence
        if exp_present and not actual_present:
            ok = False
            reasons.append("false negative — CCI-ROUTE-011 absent but expected")
        if not exp_present and actual_present:
            ok = False
            reasons.append("false positive — CCI-ROUTE-011 present but not expected")

        # Check severity
        if exp_severity != actual_sev:
            ok = False
            reasons.append(f"severity mismatch — expected={exp_severity}, actual={actual_sev}")

        # Check finding count
        if exp_count != actual_count:
            ok = False
            reasons.append(f"finding count mismatch — expected={exp_count}, actual={actual_count}")

        # Window-envelope specific checks
        if tests_we:
            if payload.get("window_envelope", False) and actual_present:
                ok = False
                reasons.append("window_envelope=true did not suppress CCI-ROUTE-011")
            # Additional check: if window_envelope missing flag but expected to trigger
            # This is already covered by presence checks above

        # Non-standard doc check
        doc_type = payload.get("doc_type", "")
        if doc_type not in ("DT_STD_LTR", "standard_letter") and actual_present:
            ok = False
            reasons.append(f"non-standard doc_type={doc_type} triggered CCI-ROUTE-011")

        if ok:
            passed += 1
            results.append((fid, "PASS", ""))
        else:
            failed += 1
            results.append((fid, "FAIL", "; ".join(reasons)))

    # Print per-fixture results
    print("-" * 72)
    print(f"{'ID':<12} {'Result':<6} {'Details'}")
    print("-" * 72)
    for fid, status, detail in results:
        if detail:
            print(f"{fid:<12} {status:<6} {detail}")
        else:
            print(f"{fid:<12} {status:<6}")

    print("-" * 72)
    print(f"Fixture results: {passed}/{len(fixtures_meta)} PASS, {failed} FAIL")

    if failed > 0:
        return 1

    # Run sub-runners
    sub_runners = [
        ("H.13 config regression", REPO_ROOT / "tools" / "run_phase_h13_config_regression.py"),
        ("H.16 burn-in regression", REPO_ROOT / "tools" / "run_phase_h16_route011_burnin_regression.py"),
        ("H.9 From-line validator", REPO_ROOT / "tools" / "run_phase_h9_from_line_validator_regression.py"),
        ("H.10 From-line evidence", REPO_ROOT / "tools" / "run_phase_h10_from_line_evidence_regression.py"),
    ]

    print("=" * 72)
    print("RUNNING SUB-RUNNERS")
    print("=" * 72)

    sub_passed = 0
    sub_failed = 0
    for name, path in sub_runners:
        if not path.exists():
            print(f"SKIP [{name}] runner not found: {path}")
            sub_failed += 1
            continue
        try:
            ok = run_sub_runner(path)
        except Exception as exc:
            print(f"FAIL [{name}] exception: {exc}")
            sub_failed += 1
            continue
        if ok:
            print(f"PASS [{name}]")
            sub_passed += 1
        else:
            print(f"FAIL [{name}]")
            sub_failed += 1

    print("-" * 72)
    print(f"Sub-runner results: {sub_passed}/{len(sub_runners)} PASS, {sub_failed} FAIL")
    print("=" * 72)

    total_passed = passed + sub_passed
    total_failed = failed + sub_failed
    print(f"OVERALL: {total_passed}/{total_passed + total_failed} PASS, {total_failed} FAIL")

    if total_failed > 0:
        return 1

    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
