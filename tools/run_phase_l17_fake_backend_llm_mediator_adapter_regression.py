#!/usr/bin/env python3
"""
Phase L.17 — Fake-Backend LLM Mediator Adapter Regression Runner

Validates the LLMBuilderMediatorAdapter + FakeBackend against the L.16 contract.
Tests strict output validation, safety filters, safe degradation, and BuilderSession handoff.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from llm_builder_mediator import (
    LLMBuilderMediatorAdapter,
    FakeBackend,
    MediatorInput,
    MockLLMBuilderMediator,
)


def _check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"[PASS] {label}")
        return True
    else:
        print(f"[FAIL] {label}: {detail}")
        return False


def main():
    passed = 0
    failed = 0
    total = 0

    # ------------------------------------------------------------------
    # 1. valid backend output passes through
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("valid"))
    inp = MediatorInput(
        session_id="r01", current_step="intake", payload_snapshot={},
        missing_required_fields=[], missing_recommended_fields=[],
        validation_summary={}, warning_summary=[], error_summary=[],
        user_message="From Commander Example",
    )
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "provide_field"
        and out["confidence"] == 0.9
        and out["proposed_payload_update"].get("from") == "Commander Example"
        and "from: Commander Example" in out["proposed_key_value_lines"]
    )
    if _check("1. Valid backend output passes through", ok, f"intent={out['intent']}, confidence={out['confidence']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 2. malformed JSON degrades safely
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("malformed"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "unknown"
        and "invalid json" in out.get("explanation", "").lower()
        and "invalid json" in str(out.get("safety_notes", [])).lower()
    )
    if _check("2. Malformed JSON degrades safely", ok, f"intent={out['intent']}, explanation={out.get('explanation')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 3. missing required keys degrades safely
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("missing_keys"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "unknown"
        and "missing required keys" in str(out.get("safety_notes", [])).lower()
    )
    if _check("3. Missing required keys degrades safely", ok, f"intent={out['intent']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 4. unsupported intent degrades safely
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("unsupported_intent"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "unknown"
        and "delete_everything" in str(out.get("safety_notes", []))
    )
    if _check("4. Unsupported intent degrades safely", ok, f"intent={out['intent']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 5. confidence below threshold degrades safely
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("low_confidence"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "unknown"
        and out["confidence"] == 0.3  # clamped to min
        and "0.3" in str(out.get("safety_notes", []))
    )
    if _check("5. Low confidence degrades safely", ok, f"intent={out['intent']}, confidence={out['confidence']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 6. confidence above 1.0 clamps to max
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("high_confidence"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "provide_field"
        and out["confidence"] == 1.0
    )
    if _check("6. High confidence clamps to max", ok, f"confidence={out['confidence']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 7. unsafe CCI severity field rejected
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("cci_tamper"))
    out = adapter.mediate(inp)
    ok = (
        "cci_severity" not in out["proposed_payload_update"]
        and "cci_severity" in str(out.get("safety_notes", []))
    )
    if _check("7. CCI severity tamper rejected", ok, f"payload={out['proposed_payload_update']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 8. renderer/layout directive rejected
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("renderer_directive"))
    out = adapter.mediate(inp)
    ok = (
        "layout_override" not in out["proposed_payload_update"]
        and "layout_override" in str(out.get("safety_notes", []))
    )
    if _check("8. Renderer directive rejected", ok, f"payload={out['proposed_payload_update']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 9. invented official data (SSIC) flagged
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("invented_ssic"))
    out = adapter.mediate(inp)
    ok = (
        "ssic" in out["proposed_payload_update"]  # kept but flagged
        and "Invented official data" in str(out.get("safety_notes", []))
    )
    if _check("9. Invented SSIC flagged", ok, f"payload={out['proposed_payload_update']}, safety_notes={out.get('safety_notes')}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 10. finalize intent requires confirmation
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("finalize_no_confirm"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "finalize"
        and out["requires_user_confirmation"] is True
    )
    if _check("10. Finalize requires confirmation", ok, f"confirmation={out['requires_user_confirmation']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 11. render_pdf intent requires confirmation
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("render_no_confirm"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "render_pdf"
        and out["requires_user_confirmation"] is True
    )
    if _check("11. Render PDF requires confirmation", ok, f"confirmation={out['requires_user_confirmation']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 12. accept_warnings requires confirmation
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("accept_warnings_silent"))
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "accept_warnings"
        and out["requires_user_confirmation"] is True
    )
    if _check("12. Accept warnings requires confirmation", ok, f"confirmation={out['requires_user_confirmation']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 13. proposed key-value lines can be handed to BuilderSession
    # ------------------------------------------------------------------
    total += 1
    try:
        from conversational_builder import BuilderSession
    except ImportError:
        print("[SKIP] 13. BuilderSession import failed")
        failed += 1
    else:
        adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("valid"))
        builder = BuilderSession(session_id="r13")
        builder.start()
        out = adapter.mediate(inp)
        for line in out.get("proposed_key_value_lines", []):
            builder.ingest_user_message(line)
        payload = builder.build_payload()
        ok = payload.get("from") == "Commander Example"
        if _check("13. KV lines handed to BuilderSession", ok, f"payload={payload}"):
            passed += 1
        else:
            failed += 1

    # ------------------------------------------------------------------
    # 14. adapter does not mutate BuilderSession directly
    # ------------------------------------------------------------------
    total += 1
    adapter = LLMBuilderMediatorAdapter(backend=FakeBackend("valid"))
    builder = BuilderSession(session_id="r14")
    builder.start()
    pre_keys = set(builder.build_payload().keys())
    out = adapter.mediate(inp)
    post_keys = set(builder.build_payload().keys())
    ok = pre_keys == post_keys  # adapter never touched builder directly
    if _check("14. Adapter does not mutate BuilderSession directly", ok, f"pre={pre_keys}, post={post_keys}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 15. no real network/API dependency
    # ------------------------------------------------------------------
    total += 1
    import inspect
    src_file = inspect.getsourcefile(LLMBuilderMediatorAdapter)
    with open(src_file or "src/llm_builder_mediator.py", "r", encoding="utf-8") as f:
        src_text = f.read().lower()
    forbidden = ["openai", "anthropic", "requests", "httpx", "urllib", "aiohttp"]
    found = [name for name in forbidden if name in src_text]
    ok = not found
    if _check("15. No real LLM/API dependency", ok, f"found imports: {found}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 48)
    print("L.17 Fake-Backend LLM Mediator Adapter Results")
    print("=" * 48)
    print(f"Total : {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 48)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
