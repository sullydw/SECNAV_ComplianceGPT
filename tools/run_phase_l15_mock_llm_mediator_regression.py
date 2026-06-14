#!/usr/bin/env python3
"""
Phase L.15 — Mock LLM Builder Mediator Regression Runner

Validates the MockLLMBuilderMediator against the L.14 contract.
Uses BuilderSession for end-to-end handoff testing.
No real LLM or network calls.

Non-goals:
- no renderer/layout changes
- no CCI config/severity changes
- no rule promotion
- no validator/catalog changes
- no Phase F/G command-layer changes
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from llm_builder_mediator import (
    MockLLMBuilderMediator,
    MediatorInput,
    MediatorOutput,
)


def _ok(label: str) -> None:
    print(f"[PASS] {label}")


def _fail(label: str, msg: str) -> None:
    print(f"[FAIL] {label}: {msg}")


def _check(label: str, condition: bool, msg: str = "") -> bool:
    if condition:
        _ok(label)
    else:
        _fail(label, msg)
    return condition


def run_regression() -> int:
    passed = 0
    failed = 0
    total = 0

    # ------------------------------------------------------------------
    # 1. start_letter intent
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r01",
        current_step="idle",
        payload_snapshot={},
        missing_required_fields=["from"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Start a new standard letter",
    )
    out = mediator.mediate(inp)
    if _check("1. start_letter intent detected", out["intent"] == "start_letter"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 2. direct from/to/subject/body extraction
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r02",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj", "body"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="From Commander Sample. To CNO. Subject Training Plan. Body This letter provides the proposed training plan.",
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    checks = [
        ("from extracted", "from" in updates and "Commander Sample" in str(updates.get("from", "")), "from"),
        ("to extracted", "to" in updates and "CNO" in str(updates.get("to", "")), "to"),
        ("subj extracted", "subj" in updates and "Training Plan" in str(updates.get("subj", "")), "subj"),
        ("body extracted", "body" in updates and "proposed training plan" in str(updates.get("body", "")).lower(), "body"),
    ]
    all_pass = all(c[1] for c in checks)
    if _check("2. Direct field extraction", all_pass, f"Got: {updates}"):
        passed += 1
    else:
        for label, ok, field in checks:
            if not ok:
                print(f"       -> sub-check '{label}' failed for field '{field}'")
        failed += 1

    # ------------------------------------------------------------------
    # 3. structured signature extraction to signature.name
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r03",
        current_step="signature",
        payload_snapshot={},
        missing_required_fields=["signature.name"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Signed by J. Q. Sample",
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    kv_lines = out.get("proposed_key_value_lines", [])
    sig_ok = (
        "signature.name" in updates
        and "j. q. sample" in str(updates.get("signature.name", "")).lower()
        and any("signature.name:" in line for line in kv_lines)
    )
    if _check("3. Structured signature extraction", sig_ok, f"Got: {updates}, KV: {kv_lines}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 4. no invented SSIC when missing
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r04",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj", "ssic"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="From Commander Sample. To CNO. Subject Training Plan.",
    )
    out = mediator.mediate(inp)
    updates = out.get("proposed_payload_update", {})
    # ssic should not be present unless explicitly provided
    ssic_invented = "ssic" in updates
    if _check("4. No invented SSIC", not ssic_invented, f"Got: {updates}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 5. ambiguous official data triggers next_question
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r05",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Help me write a letter",
    )
    out = mediator.mediate(inp)
    next_q = out.get("next_question")
    has_next_q = next_q is not None and "field_path" in next_q
    if _check("5. Missing required triggers next_question", has_next_q, f"Got: {next_q}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 6. accept warnings intent
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r06",
        current_step="review",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[{"rule_id": "CCI-ROUTE-010", "message": "Trailing whitespace"}],
        error_summary=[],
        user_message="Accept the warnings and continue",
    )
    out = mediator.mediate(inp)
    intent_ok = out["intent"] == "accept_warnings"
    req_conf = out.get("requires_user_confirmation", False)
    if _check("6. Accept warnings intent", intent_ok and req_conf, f"intent={out['intent']}, confirm={req_conf}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 7. finalize intent
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r07",
        current_step="body",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Finalize the letter",
    )
    out = mediator.mediate(inp)
    intent_ok = out["intent"] == "finalize"
    req_conf = out.get("requires_user_confirmation", False)
    if _check("7. Finalize intent", intent_ok and req_conf, f"intent={out['intent']}, confirm={req_conf}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 8. render_pdf intent
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r08",
        current_step="finalize",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Generate the PDF",
    )
    out = mediator.mediate(inp)
    intent_ok = out["intent"] == "render_pdf"
    req_conf = out.get("requires_user_confirmation", False)
    if _check("8. Render PDF intent", intent_ok and req_conf, f"intent={out['intent']}, confirm={req_conf}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 9. malformed/unknown message returns unknown
    # ------------------------------------------------------------------
    total += 1
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="r09",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="Banana hammock",
    )
    out = mediator.mediate(inp)
    intent_ok = out["intent"] == "unknown"
    conf_low = out.get("confidence", 1.0) <= 0.5
    if _check("9. Unknown message returns unknown", intent_ok and conf_low, f"intent={out['intent']}, confidence={out.get('confidence')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 10. handoff into BuilderSession through ingest_user_message
    # ------------------------------------------------------------------
    total += 1
    try:
        from conversational_builder import BuilderSession
    except ImportError:
        print("[SKIP] 10. BuilderSession import failed (conversational_builder.py may not be available)")
        failed += 1
    else:
        mediator = MockLLMBuilderMediator()
        builder = BuilderSession(session_id="r10")
        builder.start()

        messages = [
            "From Commanding Officer, Example Command",
            "To Commander, Example Group",
            "Subject training plan",
            "Body this letter provides the proposed training plan",
            "Signed by J. Q. Sample",
        ]
        for msg in messages:
            out = mediator.mediate(MediatorInput(
                session_id="r10",
                current_step="intake",
                payload_snapshot=builder.build_payload(),
                missing_required_fields=[],
                missing_recommended_fields=[],
                validation_summary={},
                warning_summary=[],
                error_summary=[],
                user_message=msg,
            ))
            for line in out.get("proposed_key_value_lines", []):
                builder.ingest_user_message(line)

        payload = builder.build_payload()
        has_from = bool(payload.get("from"))
        has_to = bool(payload.get("to"))
        has_subj = bool(payload.get("subj"))
        has_body = bool(payload.get("body"))
        has_sig = bool(payload.get("signature"))

        if _check("10. Handoff into BuilderSession", has_from and has_to and has_subj and has_body and has_sig, f"payload keys: {list(payload.keys())}, values: {payload}"):
            passed += 1
        else:
            failed += 1

    # ------------------------------------------------------------------
    # 11. end-to-end mock flow reaches finalized payload
    # ------------------------------------------------------------------
    total += 1
    try:
        from conversational_builder import BuilderSession
    except ImportError:
        print("[SKIP] 11. BuilderSession import failed")
        failed += 1
    else:
        mediator = MockLLMBuilderMediator()
        builder = BuilderSession(session_id="r11")
        builder.start()

        # Provide all required fields via mediator
        messages = [
            "From Commanding Officer, Example Command",
            "To Commander, Example Group",
            "Subject training plan",
            "Body this letter provides the proposed training plan",
            "Signed by J. Q. Sample",
        ]
        for msg in messages:
            out = mediator.mediate(MediatorInput(
                session_id="r11",
                current_step="intake",
                payload_snapshot=builder.build_payload(),
                missing_required_fields=[],
                missing_recommended_fields=[],
                validation_summary={},
                warning_summary=[],
                error_summary=[],
                user_message=msg,
            ))
            for line in out.get("proposed_key_value_lines", []):
                builder.ingest_user_message(line)

        summary = builder.validation_summary()
        if summary.get("finalize_allowed", False):
            finalize_result = builder.finalize(accept_warnings=True)
            final_ok = finalize_result.get("finalize_allowed", False)
        else:
            finalize_result = builder.finalize(accept_warnings=True)
            final_ok = finalize_result.get("finalize_allowed", False)

        if _check("11. End-to-end mock flow reaches finalized payload", final_ok, f"finalize_allowed={finalize_result.get('finalize_allowed')}"):
            passed += 1
        else:
            failed += 1

    # ------------------------------------------------------------------
    # 12. no renderer/layout files changed
    # ------------------------------------------------------------------
    total += 1
    renderer_path = REPO_ROOT / "src" / "pdf_v6_render.py"
    renderer_mtime = renderer_path.stat().st_mtime if renderer_path.exists() else 0
    import time
    recent = time.time() - renderer_mtime < 300  # modified in last 5 min?
    if _check("12. Renderer untouched", not recent, f"renderer modified recently"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 13. no CCI config/severity changes
    # ------------------------------------------------------------------
    total += 1
    config_path = REPO_ROOT / "src" / "rules_v6.yaml"
    config_mtime = config_path.stat().st_mtime if config_path.exists() else 0
    recent = time.time() - config_mtime < 300
    if _check("13. CCI config untouched", not recent, f"config modified recently"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 14. no Phase F/G command-layer changes
    # ------------------------------------------------------------------
    total += 1
    # Phase F/G files are correction_commands.py and correction_nl_commands.py
    f_path = REPO_ROOT / "src" / "correction_commands.py"
    g_path = REPO_ROOT / "src" / "correction_nl_commands.py"
    f_mtime = f_path.stat().st_mtime if f_path.exists() else 0
    g_mtime = g_path.stat().st_mtime if g_path.exists() else 0
    recent_f = time.time() - f_mtime < 300
    recent_g = time.time() - g_mtime < 300
    if _check("14. Phase F/G command layer untouched", not (recent_f or recent_g), f"F/G modified recently"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 15. no real LLM/API dependency
    # ------------------------------------------------------------------
    total += 1
    # Check that the mediator module has no network imports
    mediator_source = REPO_ROOT / "src" / "llm_builder_mediator.py"
    source_text = mediator_source.read_text(encoding="utf-8")
    banned = ["requests", "httpx", "urllib", "openai", "anthropic", "google.generativeai"]
    found = [b for b in banned if b in source_text]
    if _check("15. No real LLM/API dependency", not found, f"Found: {found}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*48}")
    print(f"L.15 Mock LLM Mediator Regression Results")
    print(f"{'='*48}")
    print(f"Total : {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"{'='*48}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_regression())
