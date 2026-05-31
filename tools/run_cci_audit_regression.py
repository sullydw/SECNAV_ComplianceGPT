#!/usr/bin/env python3
"""
CCI Consolidated Audit Regression Runner

Runs the validator_runner against valid, warning, and invalid fixtures.

Exit 0 only when all expectations are met.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


_Fixture = tuple[str, bool, bool, bool]  # (name, expect_pass, expect_warnings, expect_json_test)

_FIXTURES: list[_Fixture] = [
    ("audit_cci_combined_valid.json", True, False, False),
    ("audit_cci_combined_warning.json", True, True, False),
    ("audit_cci_combined_invalid.json", False, False, False),
]


def _run_command(args: list[str]) -> tuple[int, str, str]:
    """Run a subprocess command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [PYTHON] + args,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        shell=False,
    )
    return result.returncode, result.stdout, result.stderr


def _run_human(fixture: str, expect_pass: bool, expect_warnings: bool) -> bool:
    label = f"validator_runner on {fixture} (human mode)"
    print("=" * 72)
    print(f"RUNNING: {label}")
    print("-" * 72)

    exit_code, stdout, _stderr = _run_command([
        "src/validator_runner.py",
        f"examples/{fixture}",
    ])

    if stdout.strip():
        print(stdout.rstrip())
    print()

    has_fail = "Overall             : FAIL" in stdout
    has_pass = "Overall             : PASS" in stdout
    has_warnings = any(
        line.startswith("      WARNING:")
        for line in stdout.splitlines()
    )

    ok = True

    if expect_pass:
        if not has_pass or has_fail:
            print(f"RESULT: FAIL — expected overall PASS for {fixture}")
            ok = False
        else:
            print(f"RESULT: PASS — {fixture} overall PASS as expected")
    else:
        if not has_fail:
            print(f"RESULT: FAIL — expected overall FAIL for {fixture}")
            ok = False
        else:
            print(f"RESULT: PASS — {fixture} overall FAIL as expected")

    if expect_warnings and not has_warnings:
        print(f"RESULT: FAIL — expected warnings for {fixture} but none found")
        ok = False
    elif expect_warnings:
        print(f"RESULT: PASS — warnings present for {fixture}")

    if expect_pass:
        if exit_code != 0:
            print(f"RESULT: FAIL — expected exit 0, got {exit_code}")
            ok = False
        else:
            print(f"RESULT: PASS — exit code 0")
    else:
        if exit_code != 1:
            print(f"RESULT: FAIL — expected exit 1, got {exit_code}")
            ok = False
        else:
            print(f"RESULT: PASS — exit code 1")

    return ok


def _run_json(fixture: str) -> bool:
    label = f"validator_runner on {fixture} (--json mode)"
    print("=" * 72)
    print(f"RUNNING: {label}")
    print("-" * 72)

    exit_code, stdout, _stderr = _run_command([
        "src/validator_runner.py",
        "--json",
        f"examples/{fixture}",
    ])

    if stdout.strip():
        print(stdout.rstrip())
    print()

    # Validate JSON parses
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        print(f"RESULT: FAIL — JSON parse error: {exc}")
        return False

    # Validate schema version
    if data.get("schema_version") != "CCI_AUDIT_V1":
        print(f"RESULT: FAIL — schema_version mismatch: {data.get('schema_version')}")
        return False
    print("RESULT: PASS — schema_version == CCI_AUDIT_V1")

    # Validate required top-level keys
    required_keys = {"schema_version", "context", "context_warnings", "validators", "summary"}
    missing = required_keys - set(data.keys())
    if missing:
        print(f"RESULT: FAIL — missing keys: {missing}")
        return False
    print("RESULT: PASS — all required top-level keys present")

    # Validate summary
    summary = data.get("summary", {})
    if summary.get("validators_run") != 7:
        print(f"RESULT: FAIL — expected validators_run=7, got {summary.get('validators_run')}")
        return False
    print("RESULT: PASS — validators_run == 7")

    # Validate all 7 validator keys exist
    v_keys = data.get("validators", {})
    expected_v = {"subject", "ref_encl", "acronyms", "date_time", "personnel", "poc", "routing"}
    missing_v = expected_v - set(v_keys.keys())
    if missing_v:
        print(f"RESULT: FAIL — missing validator keys: {missing_v}")
        return False
    print("RESULT: PASS — all 7 validator keys present")

    # Each validator result should have required fields
    for key in expected_v:
        v = v_keys[key]
        v_required = {"errors", "warnings", "error_count", "warning_count", "passed"}
        v_missing = v_required - set(v.keys())
        if v_missing:
            print(f"RESULT: FAIL — {key} missing fields: {v_missing}")
            return False
    print("RESULT: PASS — all validator results have required fields")

    return True


def main() -> int:
    print("CCI CONSOLIDATED AUDIT REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {PYTHON}")
    print()

    results: list[bool] = []

    for fixture, expect_pass, expect_warnings, _ in _FIXTURES:
        results.append(_run_human(fixture, expect_pass, expect_warnings))
        print()

    # JSON mode test on valid fixture
    results.append(_run_json("audit_cci_combined_valid.json"))
    print()

    print("=" * 72)
    if all(results):
        print("CCI CONSOLIDATED AUDIT REGRESSION RESULT: PASS")
        return 0
    else:
        print("CCI CONSOLIDATED AUDIT REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
