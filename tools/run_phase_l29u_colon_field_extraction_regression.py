#!/usr/bin/env python3
"""
Phase L.29U-2 Regression — Colon-labeled field extraction.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from llm_builder_mediator import MockLLMBuilderMediator, MediatorInput


def test_colon_labeled_complete_request():
    """Colon-labeled complete request extracts the expected fields."""
    mediator = MockLLMBuilderMediator()
    msg = (
        "Create a standard naval letter from Commanding Officer, "
        "Marine Corps Air Station New River to Commanding General, "
        "II Marine Expeditionary Force. "
        "Subject: training readiness coordination. "
        "Body: The command requests coordination for upcoming training readiness "
        "reporting requirements and provides the attached summary for review. "
        "Date: 22 June 2026. "
        "Signature: A. B. Example, Colonel, U.S. Marine Corps. "
        "SSIC: 1500. Originator code: CG. "
        "Point of contact: Capt Example, DSN 555-1234, capt.example@usmc.mil."
    )
    inp = MediatorInput(
        session_id="test-1",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj", "body"],
        missing_recommended_fields=["ssic", "signature.name"],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message=msg,
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    kv = out.get("proposed_key_value_lines", [])

    print("\n--- test_colon_labeled_complete_request ---")
    print("KV lines:", kv)
    print("Updates keys:", list(updates.keys()))

    required = {"from", "to", "subj", "body", "date",
                "signature.name", "ssic", "originator_code", "point_of_contact"}
    missing = required - set(updates.keys())
    assert not missing, f"Missing fields: {missing}"
    print("PASS")


def test_non_colon_patterns_still_work():
    """Non-colon subject/body/ssic behavior still works."""
    mediator = MockLLMBuilderMediator()
    for msg, expected_key, expected_sub in [
        ("Subject training readiness coordination", "subj", "training readiness coordination"),
        ("Subject is training readiness coordination.", "subj", "training readiness coordination"),
        ("Body is the command requests coordination.", "body", "the command requests coordination"),
        ("SSIC 1500", "ssic", "1500"),
    ]:
        inp = MediatorInput(
            session_id="test-2",
            current_step="draft",
            payload_snapshot={},
            missing_required_fields=[],
            missing_recommended_fields=[],
            validation_summary={},
            warning_summary=[],
            error_summary=[],
            user_message=msg,
        )
        out = mediator.mediate(inp)
        updates = out.get("proposed_payload_update", {})
        assert expected_key in updates, f"Failed for '{msg}': missing {expected_key}"
        assert expected_sub.lower() in updates[expected_key].lower(), \
            f"Failed for '{msg}': expected '{expected_sub}', got '{updates[expected_key]}'"
        print(f"  PASS: {msg}")
    print("PASS")


def test_signature_followed_by_another_label():
    """Signature followed by another label still extracts correctly."""
    mediator = MockLLMBuilderMediator()
    msg = (
        "Signature: A. B. Example, Colonel, U.S. Marine Corps. "
        "SSIC: 1500."
    )
    inp = MediatorInput(
        session_id="test-3",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message=msg,
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    kv = out.get("proposed_key_value_lines", [])
    print("\n--- test_signature_followed_by_another_label ---")
    print("KV lines:", kv)

    assert "signature.name" in updates, f"Missing signature.name; got {updates.keys()}"
    sig = updates["signature.name"]
    assert "A. B. Example" in sig, f"Bad signature value: {sig}"
    assert "1500" not in sig, f"Signature over-captured SSIC: {sig}"
    assert "ssic" in updates, f"Missing ssic; got {updates.keys()}"
    print("PASS")


def test_date_originator_code_point_of_contact():
    """Date, originator_code, point_of_contact are extracted."""
    mediator = MockLLMBuilderMediator()
    msg = (
        "Date: 22 June 2026. "
        "Originator code: CG. "
        "Point of contact: Capt Example, DSN 555-1234, capt.example@usmc.mil."
    )
    inp = MediatorInput(
        session_id="test-4",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message=msg,
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    kv = out.get("proposed_key_value_lines", [])
    print("\n--- test_date_originator_code_point_of_contact ---")
    print("KV lines:", kv)

    for key in ("date", "originator_code", "point_of_contact"):
        assert key in updates, f"Missing {key}; got {updates.keys()}"
    assert "22 June 2026" in updates["date"]
    assert updates["originator_code"] == "CG"
    assert "Capt Example" in updates["point_of_contact"]
    print("PASS")


if __name__ == "__main__":
    test_colon_labeled_complete_request()
    test_non_colon_patterns_still_work()
    test_signature_followed_by_another_label()
    test_date_originator_code_point_of_contact()
    print("\n=== ALL L.29U-2 REGRESSION TESTS PASSED ===")
