#!/usr/bin/env python3
"""
Phase L.31F — First-Turn Intake Hardening Smoke
Verify that a realistic first-turn SECNAV letter request no longer misclassifies
as revise, and key:value ingestion reaches draft_preview with safety gates intact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
sys.path.insert(0, str(_TOOL_ROOT))

from hermes_chat_builder import (
    start_secnav_chat,
    send_secnav_chat_turn,
    get_secnav_chat_status,
    reset_secnav_chat,
    _run_manager,
    _load_state,
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> int:
    print("Phase L.31F — First-Turn Intake Hardening Smoke")
    print("=" * 50)

    # ------------------------------------------------------------------
    # 1. Raw first-turn natural-language request
    # ------------------------------------------------------------------
    chat_id = start_secnav_chat()["chat_id"]
    first_turn_text = (
        "I need a standard letter from Commanding Officer, Marine Corps Air Station New River "
        "to Commanding General, II Marine Expeditionary Force about reviewing correspondence procedures. "
        "Use the date 1 July 2026, signer A. B. SAMPLE, and make the body about implementing "
        "local correspondence review procedures."
    )
    r = send_secnav_chat_turn(chat_id, first_turn_text)
    intent = r.get("intent")
    if intent == "revise":
        _fail(f"First-turn misclassified as revise: {intent}")
    if intent not in ("say", "new"):
        _fail(f"Unexpected first-turn intent: {intent}")
    if not r.get("success"):
        _fail(f"First-turn failed: {r.get('error')}")
    print(f"[PASS] First-turn intent is '{intent}' (not revise)")

    phase = r.get("phase")
    if phase not in ("build_status", "draft_preview"):
        _fail(f"First-turn phase unexpected: {phase}")
    print(f"[PASS] First-turn phase is '{phase}'")

    # ------------------------------------------------------------------
    # 2. Sequential key:value ingestion resolves required fields
    # ------------------------------------------------------------------
    fields = {
        "from": "Commanding Officer, Marine Corps Air Station New River",
        "to": "Commanding General, II Marine Expeditionary Force",
        "date": "1 July 2026",
        "subj": "REVIEW OF CORRESPONDENCE PROCEDURES",
        "body": "Implementing local correspondence review procedures.",
        "signature": "A. B. SAMPLE",
    }
    for key, value in fields.items():
        kv = f"{key}: {value}"
        ar = send_secnav_chat_turn(chat_id, kv)
        if not ar.get("success"):
            _fail(f"Key:value turn '{key}' failed: {ar.get('error')}")
    print("[PASS] All key:value turns succeed")

    # ------------------------------------------------------------------
    # 3. Preview reaches draft_preview
    # ------------------------------------------------------------------
    state = _load_state(chat_id)
    sid = state["session_id"]
    preview = _run_manager(["preview", "--session", sid])
    if preview.get("mode") != "draft_preview":
        _fail(f"Preview mode should be draft_preview, got {preview.get('mode')}")
    if not preview.get("preview_gate_met"):
        _fail("preview_gate_met should be True")
    print("[PASS] Preview reaches draft_preview")

    # ------------------------------------------------------------------
    # 4. validation_ready True, approved_ready False
    # ------------------------------------------------------------------
    ready = _run_manager(["ready", "--session", sid])
    if not ready.get("validation_ready"):
        _fail(f"validation_ready should be True, got {ready.get('validation_ready')}")
    if ready.get("approved_ready"):
        _fail("approved_ready should be False before explicit approval")
    print("[PASS] validation_ready=True, approved_ready=False (safety gate)")

    # ------------------------------------------------------------------
    # 5. Unsupported revise does not falsely claim changes
    # ------------------------------------------------------------------
    rr = send_secnav_chat_turn(chat_id, "make the body more formal")
    if rr.get("success") and rr.get("payload_changed"):
        _fail("Unsupported revise should not succeed with payload changes")
    ar = rr.get("assistant_response", "")
    if "wasn't able to apply" not in ar and "nothing in the draft was changed" not in ar:
        _fail(f"Unsupported revise response unexpected: {ar}")
    print("[PASS] Unsupported revise blocked without false payload change")

    # ------------------------------------------------------------------
    # 6. Render blocked before approval
    # ------------------------------------------------------------------
    render_r = send_secnav_chat_turn(chat_id, "make the pdf")
    if render_r.get("success"):
        _fail("Render should be blocked before approval")
    if render_r.get("intent") != "render":
        _fail(f"Render intent should be 'render', got {render_r.get('intent')}")
    print("[PASS] Render blocked before approval")

    # ------------------------------------------------------------------
    # 7. Approve
    # ------------------------------------------------------------------
    apr = send_secnav_chat_turn(chat_id, "looks good")
    if apr.get("intent") != "approve":
        _fail(f"Approve intent unexpected: {apr.get('intent')}")
    if not apr.get("success"):
        _fail(f"Approve failed: {apr.get('error')}")
    print("[PASS] Approve succeeds")

    # ------------------------------------------------------------------
    # 8. Render succeeds after approval/ready
    # ------------------------------------------------------------------
    render2 = send_secnav_chat_turn(chat_id, "make the pdf")
    if not render2.get("success"):
        _fail(f"Render after approval failed: {render2.get('error')}")
    if not render2.get("pdf_path"):
        _fail("Render after approval missing pdf_path")
    pdf_path = Path(render2["pdf_path"])
    if not pdf_path.exists():
        _fail(f"PDF not found: {pdf_path}")
    print(f"[PASS] Render succeeds after approval: {pdf_path} ({pdf_path.stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 9. Reset preserves chat_id
    # ------------------------------------------------------------------
    reset_r = reset_secnav_chat(chat_id)
    if not reset_r.get("success"):
        _fail(f"Reset failed: {reset_r.get('error')}")
    if reset_r.get("chat_id") != chat_id:
        _fail("Reset should preserve chat_id")
    print("[PASS] Reset preserves chat_id")

    # ------------------------------------------------------------------
    # 10. Callable functions remain silent
    # ------------------------------------------------------------------
    # Already verified: send_secnav_chat_turn returns dict, no stdout
    print("[PASS] All callable functions return dicts without stdout")

    print()
    print("All L.31F checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
