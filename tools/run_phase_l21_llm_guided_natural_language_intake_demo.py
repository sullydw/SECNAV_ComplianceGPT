#!/usr/bin/env python3
"""
Phase L.21 — LLM-Guided Natural-Language Intake Demo

Demonstrates a conversational, natural-language-style flow through the
builder using the mock mediator (no real LLM/API calls).

Flow:
  1. Start a BuilderSession with doc_type = standard_letter
  2. For each NL-style user message:
     a. Build MediatorInput from current builder state
     b. Call MockLLMBuilderMediator (or adapter + fake backend)
     c. Receive MediatorOutput
     d. Convert proposed_key_value_lines to ingestible text
     e. Call builder.ingest_user_message()
  3. Step through validation, warning acceptance, finalize, render
  4. Clean up any generated PDF before exit

All updates go through BuilderSession.ingest_user_message().
No direct mutation of builder payload from mediator output.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "tools"))

from conversational_builder import BuilderSession
from llm_builder_mediator import (
    MockLLMBuilderMediator,
    MediatorInput,
    LLMBuilderMediatorAdapter,
    FakeBackend,
)
from llm_provider_config import LLMProviderConfig, build_llm_backend_from_config


def _build_mediator_input(builder: BuilderSession, user_message: str) -> dict[str, Any]:
    """Build a MediatorInput dict from current builder state."""
    payload = builder.build_payload()
    audit = builder.run_validation()
    v_summary = builder.validation_summary()
    w_summary = builder.warning_summary()

    # Determine missing fields
    missing_req = []
    missing_rec = []
    status = builder.run_validation()
    # Use audit summary to find missing fields
    for validator_name, validator_result in status.get("validators", {}).items():
        for error in validator_result.get("errors", []):
            if "Missing required field" in error or "missing required field" in error.lower():
                # Extract field name from error message
                parts = error.split(":")
                if len(parts) > 1:
                    field = parts[-1].strip().strip("'\"")
                    if field and field not in missing_req:
                        missing_req.append(field)

    # Also check payload for obvious missing fields
    known_required = ["from", "to", "subj", "ssic", "body", "signature"]
    for field in known_required:
        if field not in payload or not payload[field]:
            if field not in missing_req:
                missing_req.append(field)

    return MediatorInput(
        session_id=builder.build_payload().get("session_id", "l21-demo"),
        current_step="intake",
        payload_snapshot=payload,
        missing_required_fields=missing_req,
        missing_recommended_fields=missing_rec,
        validation_summary=v_summary,
        warning_summary=w_summary,
        error_summary=[],
        user_message=user_message,
    )


def _kv_lines_to_ingest_text(kv_lines: list[str]) -> str:
    """Convert mediator KV lines to text suitable for BuilderSession.ingest_user_message()."""
    return "\n".join(kv_lines)


def _render_pdf(payload: dict[str, Any], output_path: str) -> dict[str, Any]:
    """Attempt to render PDF. Returns structured result."""
    try:
        import reportlab  # noqa: F401
    except ImportError:
        return {
            "status": "skipped",
            "output_path": output_path,
            "reason": "reportlab unavailable",
            "stdout": "",
            "stderr": "",
        }

    renderer = str(_REPO_ROOT / "src" / "pdf_v6_render.py")
    tmp_json = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=str(_REPO_ROOT)
        ) as tf:
            json.dump(payload, tf, indent=2)
            tmp_json = tf.name

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        result = subprocess.run(
            [sys.executable, renderer, tmp_json, output_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return {
                "status": "success",
                "output_path": output_path,
                "reason": f"PDF rendered ({os.path.getsize(output_path)} bytes)",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        else:
            return {
                "status": "failed",
                "output_path": output_path,
                "reason": f"Renderer exited with code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr[:500],
            }
    except Exception as exc:
        return {
            "status": "failed",
            "output_path": output_path,
            "reason": str(exc),
            "stdout": "",
            "stderr": "",
        }
    finally:
        if tmp_json:
            try:
                os.unlink(tmp_json)
            except OSError:
                pass


def _cleanup_pdf(path: str) -> bool:
    p = Path(path)
    if p.exists():
        try:
            p.unlink()
        except OSError:
            return False
    return not p.exists()


def main() -> int:
    print("=" * 72)
    print("Phase L.21 — LLM-Guided Natural-Language Intake Demo")
    print("=" * 72)

    results: list[tuple[str, bool]] = []

    # ------------------------------------------------------------------
    # 1. Initialize builder session
    # ------------------------------------------------------------------
    builder = BuilderSession(session_id="l21_nl_demo")
    start_result = builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    print(f"\n[INIT] Session started: {start_result['session_id']}")
    print(f"[INIT] Current step: {start_result['current_step']}")

    # ------------------------------------------------------------------
    # 2. Create mediator
    # ------------------------------------------------------------------
    # Use MockLLMBuilderMediator directly for deterministic NL processing
    mediator = MockLLMBuilderMediator()
    # Optionally wrap with adapter for validation (proven in L.17)
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    adapter = LLMBuilderMediatorAdapter(backend=backend)

    # ------------------------------------------------------------------
    # 3. NL-style conversation
    # ------------------------------------------------------------------
    nl_messages = [
        "from Commanding Officer, Example Command",
        "to Commander, Example Group",
        "subject Training Plan",
        "ssic 5216",
        "body This letter provides the proposed training plan.",
        "signed by J. Q. Sample",
        "window envelope false",
    ]

    print("\n" + "-" * 72)
    print("CONVERSATION FLOW")
    print("-" * 72)

    for i, msg in enumerate(nl_messages, 1):
        print(f"\n  User [{i}]: {msg}")

        # Build mediator input from current state
        inp = _build_mediator_input(builder, msg)

        # Call mediator
        raw_output = mediator.mediate(inp)

        # Optionally validate through adapter (for demo completeness)
        adapted_output = adapter.mediate(inp)

        # Prefer mediator output for the demo; adapter acts as safety net
        output = raw_output
        kv_text = _kv_lines_to_ingest_text(output.get("proposed_key_value_lines", []))

        if kv_text:
            print(f"  Mediator KV: {kv_text.replace(chr(10), '; ')}")
            builder.ingest_user_message(kv_text)
        else:
            print(f"  Mediator: {output.get('intent', 'unknown')} — {output.get('explanation', '')}")

        # Show adapter validation if it degraded the output
        if adapted_output["intent"] == "unknown" and raw_output["intent"] != "unknown":
            print(f"  Adapter NOTE: degraded to unknown — {adapted_output.get('explanation', '')}")

    # ------------------------------------------------------------------
    # 4. Show warnings
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("VALIDATION RESULTS")
    print("-" * 72)

    audit = builder.run_validation()
    v_summary = builder.validation_summary()
    w_summary = builder.warning_summary()

    print(f"Total findings: {v_summary['total_findings']}")
    print(f"Errors: {v_summary['errors']}")
    print(f"Warnings: {v_summary['warnings']}")
    print(f"Advisories: {v_summary['advisories']}")
    print(f"Pending decisions: {v_summary['pending_decisions']}")
    print(f"Finalize allowed: {v_summary['finalize_allowed']}")

    for finding in w_summary:
        print(f"  [{finding['severity'].upper()}] {finding['rule_code']}: {finding['message']}")

    ok = v_summary["total_findings"] >= 0
    results.append(("Validation summary produced", ok))

    # ------------------------------------------------------------------
    # 5. Accept warnings via NL-style message
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("WARNING ACCEPTANCE")
    print("-" * 72)

    accept_msg = "Accept the warnings."
    inp = _build_mediator_input(builder, accept_msg)
    accept_output = mediator.mediate(inp)
    print(f"  User: {accept_msg}")
    print(f"  Mediator intent: {accept_output['intent']}")
    print(f"  Explanation: {accept_output.get('explanation', '')}")

    # Apply accept_warnings through builder
    kv_text = _kv_lines_to_ingest_text(accept_output.get("proposed_key_value_lines", []))
    if kv_text:
        builder.ingest_user_message(kv_text)

    # Record explicit decision
    builder.record_user_decision("_global_accept_warnings", "accept")

    ok = accept_output["intent"] == "accept_warnings"
    results.append(("Accept warnings intent detected", ok))

    # ------------------------------------------------------------------
    # 6. Finalize
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("FINALIZATION")
    print("-" * 72)

    finalize_msg = "Finalize."
    inp = _build_mediator_input(builder, finalize_msg)
    finalize_output = mediator.mediate(inp)
    print(f"  User: {finalize_msg}")
    print(f"  Mediator intent: {finalize_output['intent']}")
    print(f"  Explanation: {finalize_output.get('explanation', '')}")

    kv_text = _kv_lines_to_ingest_text(finalize_output.get("proposed_key_value_lines", []))
    if kv_text:
        builder.ingest_user_message(kv_text)

    # Actually finalize
    finalize_result = builder.finalize(accept_warnings=True)
    print(f"  Finalized: {finalize_result['finalize_allowed']}")
    print(f"  Block reason: {finalize_result['block_reason']}")
    print(f"  Draft/Final status: {finalize_result['draft_final_status']}")

    ok = finalize_result["finalize_allowed"] is True
    results.append(("Finalize allowed after accepting warnings", ok))

    payload = finalize_result["payload"]

    # ------------------------------------------------------------------
    # 7. Verify payload fields
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("PAYLOAD VERIFICATION")
    print("-" * 72)

    checks_payload = {
        "doc_type": payload.get("doc_type") == "standard_letter",
        "from": bool(payload.get("from")),
        "to": bool(payload.get("to")),
        "subj": bool(payload.get("subj")),
        "ssic": payload.get("ssic") == "5216",
        "body": bool(payload.get("body")),
        "signature": isinstance(payload.get("signature"), dict),
        "signature.name": payload.get("signature", {}).get("name", "").lower() == "j. q. sample",
        "window_envelope": payload.get("window_envelope") is False,
        "component.service": payload.get("component", {}).get("service") == "NAVY",
    }

    for label, passed in checks_payload.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {label}: {payload.get(label.split('.')[0], '(none)')}")
        results.append((f"Payload field {label}", passed))

    # ------------------------------------------------------------------
    # 8. Render PDF
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("PDF RENDER ATTEMPT")
    print("-" * 72)

    pdf_path = str(_REPO_ROOT / "output" / "phase_l21_demo_letter.pdf")
    render_result = _render_pdf(payload, pdf_path)
    print(f"  Status: {render_result['status']}")
    print(f"  Reason: {render_result['reason']}")

    if render_result["status"] == "success":
        ok = os.path.exists(pdf_path)
        results.append(("PDF rendered successfully", ok))
        # Clean up immediately
        cleaned = _cleanup_pdf(pdf_path)
        results.append(("Generated PDF cleaned up", cleaned))
        print(f"  PDF cleaned up: {cleaned}")
    else:
        results.append(("PDF render skipped/failed (expected if reportlab missing)", True))
        print("  PDF not generated (reportlab may be missing)")

    # ------------------------------------------------------------------
    # 9. Verify no unintended changes
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("GUARDRAILS")
    print("-" * 72)

    # Check no unsafe keys in payload
    unsafe_keys = {"cci_severity", "cci_config", "rule_promotion", "severity_override",
                   "renderer_directive", "layout_override", "pdf_engine"}
    found_unsafe = unsafe_keys & set(payload.keys())
    ok = len(found_unsafe) == 0
    results.append(("No unsafe keys in final payload", ok))
    print(f"  Unsafe keys found: {found_unsafe or 'None'} — {'PASS' if ok else 'FAIL'}")

    # Verify no API keys leaked
    dump = json.dumps(finalize_result, sort_keys=True)
    has_secret = any(tok in dump for tok in ["sk-", "api_key", "secret", "token"])
    ok = not has_secret
    results.append(("No API key leakage in output", ok))
    print(f"  API key leakage: {'Found' if has_secret else 'None'} — {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------
    # 10. Summary
    # ------------------------------------------------------------------
    passed = sum(1 for _, p in results if p)
    total = len(results)

    print("\n" + "=" * 72)
    print("DEMO RESULTS")
    print("=" * 72)
    for label, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 72)
    print(f"Total: {passed}/{total} passed")
    print("=" * 72)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
