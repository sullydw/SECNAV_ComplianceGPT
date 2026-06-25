#!/usr/bin/env python3
"""
Phase L.29V — Subject normalization regression
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from llm_builder_mediator import MockLLMBuilderMediator, MediatorInput


def run():
    m = MockLLMBuilderMediator()

    # 1. Colon-labeled Subject normalization
    inp1 = MediatorInput(
        session_id="test1",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=["subj"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Subject: Training Readiness Coordination Update.",
    )
    out1 = m.mediate(inp1)
    subj1 = out1["proposed_payload_update"].get("subj", "")
    assert subj1 == "TRAINING READINESS COORDINATION UPDATE", f"colon-labeled subject mismatch: {subj1!r}"
    print("PASS: colon-labeled subject -> TRAINING READINESS COORDINATION UPDATE")

    # 2. Non-colon subject normalization
    inp2 = MediatorInput(
        session_id="test2",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=["subj"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Subject training readiness coordination.",
    )
    out2 = m.mediate(inp2)
    subj2 = out2["proposed_payload_update"].get("subj", "")
    assert subj2 == "TRAINING READINESS COORDINATION", f"non-colon subject mismatch: {subj2!r}"
    print("PASS: non-colon subject -> TRAINING READINESS COORDINATION")

    # 3. Body text NOT uppercased
    inp3 = MediatorInput(
        session_id="test3",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=["body"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Body: The command requests coordination for upcoming training readiness reporting requirements.",
    )
    out3 = m.mediate(inp3)
    body3 = out3["proposed_payload_update"].get("body", "")
    assert "The command" in body3 and "The Command" not in body3.upper(), f"body casing altered: {body3!r}"
    print("PASS: body remains sentence case")

    # 4. Point of contact NOT uppercased
    inp4 = MediatorInput(
        session_id="test4",
        current_step="draft",
        payload_snapshot={},
        missing_required_fields=["point_of_contact"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Point of contact: Capt Example, DSN 555-1234, capt.example@usmc.mil.",
    )
    out4 = m.mediate(inp4)
    poc4 = out4["proposed_payload_update"].get("point_of_contact", "")
    assert poc4 == "Capt Example, DSN 555-1234, capt.example@usmc.mil.", f"poc casing altered: {poc4!r}"
    print("PASS: point_of_contact remains normal case")

    print("\nAll L.29V regressions passed.")


if __name__ == "__main__":
    run()
