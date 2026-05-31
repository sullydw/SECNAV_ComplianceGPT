#!/usr/bin/env python3
"""
Local Command Profile Regression Runner

Exercises list_profiles, load_profile, validate_profile, and apply_profile_defaults.

Usage:
    python tools/run_profile_regression.py

Exit 0 if all expectations are met.
Exit 1 if any expectation fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from local_profile import (
    list_profiles,
    load_profile,
    validate_profile,
    apply_profile_defaults,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PROFILE_NAME = "example_local_profile"
_MERGE_PAYLOAD_PATH = _REPO_ROOT / "examples" / "audit_profile_merge.json"
_USER_ANSWERS_PATH = _REPO_ROOT / "examples" / "audit_profile_user_answers.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        raise AssertionError(message)
    else:
        print(f"PASS: {message}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _test_list() -> None:
    print("=" * 72)
    print("TEST: list_profiles")
    print("=" * 72)
    profiles = list_profiles()
    _assert(_PROFILE_NAME + ".json" in profiles, f"'{_PROFILE_NAME}.json' should be in profiles list")
    print()


def _test_load_by_name_and_path() -> None:
    print("=" * 72)
    print("TEST: load_profile by name and by path")
    print("=" * 72)
    by_name = load_profile(_PROFILE_NAME)
    profile_path = _REPO_ROOT / "profiles" / f"{_PROFILE_NAME}.json"
    by_path = load_profile(str(profile_path))
    _assert(by_name == by_path, "load by name and by path should produce identical profiles")
    _assert(by_name.get("schema_version") == "LOCAL_PROFILE_V1", "profile schema_version should be LOCAL_PROFILE_V1")
    print()


def _test_validate() -> None:
    print("=" * 72)
    print("TEST: validate_profile on example_local_profile")
    print("=" * 72)
    profile = load_profile(_PROFILE_NAME)
    errors, warnings = validate_profile(profile)
    _assert(len(errors) == 0, f"validation should have no errors, got: {errors}")
    print("  warnings:", warnings)
    print()


def _test_apply_defaults_empty_user_answers() -> None:
    print("=" * 72)
    print("TEST: apply_profile_defaults (no user answers)")
    print("=" * 72)
    profile = load_profile(_PROFILE_NAME)
    payload = _load_json(_MERGE_PAYLOAD_PATH)

    merged, report = apply_profile_defaults(payload, profile)

    # Payload explicit values preserved
    _assert(merged["to"] == payload["to"], "payload explicit 'to' preserved")
    _assert(merged["ssic"] == "1111", "payload explicit 'ssic' preserved")
    _assert(merged.get("signature") == payload["signature"], "payload explicit 'signature' preserved")

    # Profile defaults filled missing fields
    _assert(merged.get("from") == "Commanding Officer, Example Activity", "profile default 'from' applied")
    _assert(merged.get("originator_code") == "EX-1", "profile default 'originator_code' applied")
    _assert(merged.get("point_of_contact", {}).get("name") == "J. Doe", "profile poc_defaults applied")
    _assert(report["fields_from_profile"], "merge report should list fields_from_profile")

    # Still missing should not include fields we filled
    _assert("from" not in report["fields_still_missing"], "'from' should not be in still_missing")
    _assert("ssic" not in report["fields_still_missing"], "'ssic' should not be in still_missing")

    print("  merge report:", json.dumps(report, indent=2))
    print()


def _test_apply_defaults_with_user_answers() -> None:
    print("=" * 72)
    print("TEST: apply_profile_defaults (with user answers)")
    print("=" * 72)
    profile = load_profile(_PROFILE_NAME)
    payload = _load_json(_MERGE_PAYLOAD_PATH)
    user_answers = _load_json(_USER_ANSWERS_PATH)

    merged, report = apply_profile_defaults(payload, profile, user_answers)

    # Payload explicit values preserved
    _assert(merged["to"] == payload["to"], "payload explicit 'to' preserved")
    _assert(merged["ssic"] == "1111", "payload explicit 'ssic' preserved over user_answers 'ssic'='9999'")

    # User answers fill missing fields
    _assert(merged.get("originator_code") == "UA-1", "user answer 'originator_code' applied")
    _assert(merged.get("point_of_contact", {}).get("name") == "User Poc", "user answer dot-notated 'point_of_contact.name' applied")

    # Profile still fills fields neither payload nor user_answers covered
    _assert(merged.get("from") == "Commanding Officer, Example Activity", "profile default 'from' applied")

    _assert("from" in report["fields_from_profile"], "'from' should appear in fields_from_profile")
    _assert("originator_code" in report["fields_from_user_answers"], "'originator_code' should appear in fields_from_user_answers")
    _assert("point_of_contact" in report["fields_from_user_answers"], "'point_of_contact' should appear in fields_from_user_answers")

    print("  merge report:", json.dumps(report, indent=2))
    print()


def _test_missing_profile() -> None:
    print("=" * 72)
    print("TEST: missing profile name fails gracefully")
    print("=" * 72)
    try:
        load_profile("nonexistent_profile_xyz")
        _assert(False, "should have raised FileNotFoundError")
    except FileNotFoundError as exc:
        _assert("nonexistent_profile_xyz" in str(exc), "error message should mention profile name")
        print(f"  Expected FileNotFoundError: {exc}")
    print()


def _test_signature_block_from_profile() -> None:
    print("=" * 72)
    print("TEST: signature block from profile when payload lacks signature")
    print("=" * 72)
    profile = load_profile(_PROFILE_NAME)
    # Payload without signature
    payload = {
        "doc_type": "standard_letter",
        "to": "Test",
        "body": ["test"],
    }
    merged, report = apply_profile_defaults(payload, profile)
    # Payload has no signature but profile offers standard_letter signature
    _assert(merged.get("signature") == ["J. DOE", "By direction"], "profile signature block for standard_letter applied")
    _assert("signature" in report["fields_from_profile"], "'signature' should appear in fields_from_profile")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("LOCAL COMMAND PROFILE REGRESSION RUNNER")
    print("=" * 72)
    print()

    try:
        _test_list()
        _test_load_by_name_and_path()
        _test_validate()
        _test_apply_defaults_empty_user_answers()
        _test_apply_defaults_with_user_answers()
        _test_missing_profile()
        _test_signature_block_from_profile()
    except AssertionError as exc:
        print()
        print(f"REGRESSION FAILED: {exc}")
        return 1

    print("=" * 72)
    print("ALL PROFILE REGRESSION TESTS PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
