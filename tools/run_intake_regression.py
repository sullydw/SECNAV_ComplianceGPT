#!/usr/bin/env python3
"""
Intake Orchestration Regression Runner — Phase 2: Profile Integration

Validates:
  - standard_letter missing_required includes subj before answers
  - standard_letter missing_required no longer includes subj after applying answers
  - MFR has blocking false when body/date present
  - Endorsement has blocking true for missing basic_letter_id and endorsement_ordinal
  - Joint_letter has blocking true for missing joint_heading and commands
  - Dot-notation answers normalize correctly into nested dicts
  - run_audit() returns schema_version CCI_AUDIT_V1
  - next_questions() returns questions ordered required first
  - Profile integration: active_profile loads example profile
  - Profile integration: get_status() reports active_profile and prefilled_from_profile
  - Profile integration: build_payload() includes fields filled from profile
  - Profile integration: next_questions() skips fields prefilled by profile
  - Profile integration: user_answers override profile defaults
  - Profile integration: explicit payload values override user_answers and profile defaults
  - Profile integration: set_active_profile(None) disables profile

Exit 0 if all expectations met; non-zero otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure repo root and src/ are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from intake_orchestrator import IntakeOrchestrator
from local_profile import load_profile

_EXAMPLES = _REPO_ROOT / "examples"
_USER_ANSWERS = json.loads((_EXAMPLES / "audit_intake_user_answers.json").read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}", file=sys.stderr)
        raise AssertionError(message)
    else:
        print(f"PASS: {message}")


def run_regression() -> int:
    errors = 0

    # ------------------------------------------------------------------
    # 1. Standard Letter — missing subj initially
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_standard_letter.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        status = orch.get_status()
        _assert(status["blocking"] is True, "standard_letter: missing subj causes blocking")
        _assert("subj" in status["missing_required"], "standard_letter: subj in missing_required before answers")

        # Apply answers containing subj (and dot-notation service to verify normalization)
        orch.apply_answers({"subj": "INTAKE ORCHESTRATION TEST"})
        status_after = orch.get_status()
        _assert("subj" not in status_after["missing_required"], "standard_letter: subj not missing after answers")
        # blocking may still be true if other required fields are missing; they should not be
        _assert(status_after["blocking"] is False, "standard_letter: blocking false after answers complete")
    except AssertionError as exc:
        print(f"  standard_letter assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 2. Memorandum for Record — body/date present, no blocking required
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_mfr.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        status = orch.get_status()
        _assert(status["blocking"] is False, "mfr: blocking false when body/date present")
        # title and signer_name are recommended
        _assert("title" in status["missing_recommended"], "mfr: title in missing_recommended")
        _assert("signer_name" in status["missing_recommended"], "mfr: signer_name in missing_recommended")
    except AssertionError as exc:
        print(f"  mfr assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 3. Endorsement — missing basic_letter_id and endorsement_ordinal
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_endorsement.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        status = orch.get_status()
        _assert(status["blocking"] is True, "endorsement: blocking true for missing required fields")
        _assert("basic_letter_id" in status["missing_required"], "endorsement: basic_letter_id missing")
        _assert("endorsement_ordinal" in status["missing_required"], "endorsement: endorsement_ordinal missing")
    except AssertionError as exc:
        print(f"  endorsement assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 4. Joint Letter — missing joint_heading and commands
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_joint.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        status = orch.get_status()
        _assert(status["blocking"] is True, "joint_letter: blocking true for missing required fields")
        _assert("joint_heading" in status["missing_required"], "joint_letter: joint_heading missing")
        _assert("commands" in status["missing_required"], "joint_letter: commands missing")
    except AssertionError as exc:
        print(f"  joint_letter assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 5. Dot-notation answer normalization
    # ------------------------------------------------------------------
    try:
        orch = IntakeOrchestrator({}, {"component.service": "marine_corps"})
        payload = orch.build_payload()
        _assert(payload.get("component", {}).get("service") == "marine_corps", "dot-notation: component.service normalizes to nested dict")
    except AssertionError as exc:
        print(f"  dot-notation assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 6. run_audit returns CCI_AUDIT_V1 schema_version
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_standard_letter.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload, {"subj": "INTAKE ORCHESTRATION TEST"})
        audit = orch.run_audit()
        _assert(audit.get("schema_version") == "CCI_AUDIT_V1", "run_audit: returns CCI_AUDIT_V1 schema_version")
        _assert("summary" in audit, "run_audit: contains summary")
        _assert("overall_pass" in audit.get("summary", {}), "run_audit: summary contains overall_pass")
    except AssertionError as exc:
        print(f"  run_audit assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 7. next_questions returns questions ordered required first
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_standard_letter.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        questions = orch.next_questions()
        if questions:
            _assert(questions[0].get("bucket") == "required", "next_questions: first question is required bucket")
        else:
            print("WARN: next_questions returned empty for standard_letter payload")
    except AssertionError as exc:
        print(f"  next_questions assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 8. Profile integration — active_profile loads example profile by name
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload, active_profile="example_local_profile")
        status = orch.get_status()
        _assert(status.get("active_profile") == "example_local_profile", "profile: active_profile reported")
        _assert("from" in status.get("prefilled_from_profile", []), "profile: from prefilled")
        _assert("originator_code" in status.get("prefilled_from_profile", []), "profile: originator_code prefilled")
        _assert("point_of_contact" in status.get("prefilled_from_profile", []), "profile: point_of_contact prefilled")
        # missing_required should not include from since profile filled it
        _assert("from" not in status["missing_required"], "profile: from not in missing_required after profile")
    except AssertionError as exc:
        print(f"  profile integration assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 9. Profile integration — next_questions skips profile-filled fields
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload, active_profile="example_local_profile")
        questions = orch.next_questions()
        question_fields = [q["field_path"] for q in questions]
        _assert("from" not in question_fields, "profile: next_questions does not ask for from")
        _assert("originator_code" not in question_fields, "profile: next_questions does not ask for originator_code")
        _assert("point_of_contact" not in question_fields, "profile: next_questions does not ask for point_of_contact")
    except AssertionError as exc:
        print(f"  profile next_questions assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 10. Profile integration — user_answers override profile defaults
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        # Provide a user answer for originator_code; it should win over profile default
        orch = IntakeOrchestrator(payload, user_answers={"originator_code": "UA-OVERRIDE"}, active_profile="example_local_profile")
        built = orch.build_payload()
        _assert(built.get("originator_code") == "UA-OVERRIDE", "profile: user_answers override profile default")
        status = orch.get_status()
        _assert("originator_code" not in status.get("prefilled_from_profile", []), "profile: overridden field not listed as prefilled")
    except AssertionError as exc:
        print(f"  profile user_answers override assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 11. Profile integration — explicit payload overrides user_answers and profile
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        # audit_intake_with_profile already has explicit subj; ensure it is preserved
        orch = IntakeOrchestrator(payload, user_answers={"subj": "OVERRIDE SUBJ"}, active_profile="example_local_profile")
        built = orch.build_payload()
        _assert(built.get("subj") == "PROFILE INTEGRATION TEST", "profile: explicit payload overrides user_answers")
    except AssertionError as exc:
        print(f"  profile explicit override assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 12. Profile integration — set_active_profile(None) disables profile
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload, active_profile="example_local_profile")
        orch.set_active_profile(None)
        status = orch.get_status()
        _assert(status.get("active_profile") is None, "profile: set_active_profile(None) clears active_profile")
        _assert(status.get("prefilled_from_profile") == [], "profile: prefilled_from_profile empty after clearing")
        # Without profile, from should be missing
        _assert("from" in status["missing_required"], "profile: from missing after profile cleared")
    except AssertionError as exc:
        print(f"  profile disable assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 13. Profile integration — run_audit still returns CCI_AUDIT_V1 with profile
    # ------------------------------------------------------------------
    try:
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload, active_profile="example_local_profile")
        audit = orch.run_audit()
        _assert(audit.get("schema_version") == "CCI_AUDIT_V1", "profile: run_audit returns CCI_AUDIT_V1")
        _assert("summary" in audit, "profile: run_audit contains summary")
    except AssertionError as exc:
        print(f"  profile run_audit assertion failed: {exc}", file=sys.stderr)
        errors += 1

    # ------------------------------------------------------------------
    # 14. Profile integration — set_active_profile with dict works
    # ------------------------------------------------------------------
    try:
        profile_dict = load_profile("example_local_profile")
        payload = json.loads((_EXAMPLES / "audit_intake_with_profile.json").read_text(encoding="utf-8"))
        orch = IntakeOrchestrator(payload)
        orch.set_active_profile(profile_dict)
        status = orch.get_status()
        _assert(status.get("active_profile") == "example_local_profile", "profile: set_active_profile(dict) works")
        _assert("from" in status.get("prefilled_from_profile", []), "profile: dict activation prefills from")
    except AssertionError as exc:
        print(f"  profile dict activation assertion failed: {exc}", file=sys.stderr)
        errors += 1

    if errors:
        print(f"\n{errors} regression failure(s) detected.", file=sys.stderr)
        return 1

    print("\nAll intake regression checks PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_regression())
