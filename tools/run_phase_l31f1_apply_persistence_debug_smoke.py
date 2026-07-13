#!/usr/bin/env python3
"""
Phase L.31F-1 — Apply Persistence Debug Smoke
Verify that key:value turns sent through the apply path persist into the session payload.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
sys.path.insert(0, str(_TOOL_ROOT))

from hermes_chat_builder import start_secnav_chat, _run_manager, _load_state


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> int:
    print("L.31F-1 Apply Persistence Debug Smoke")
    print("=" * 50)

    # 1. Start session
    r = start_secnav_chat()
    if not r.get("success"):
        _fail(f"start_secnav_chat failed: {r.get('error')}")
    chat_id = r["chat_id"]
    state = _load_state(chat_id)
    sid = state["session_id"]
    print(f"Session: {sid}")

    # 2. Apply all required fields via manager apply command
    fields = {
        "from": "Commanding Officer, Marine Corps Air Station New River",
        "to": "Commanding General, II Marine Expeditionary Force",
        "date": "1 July 2026",
        "subj": "REVIEW OF CORRESPONDENCE PROCEDURES",
        "body": "Implementing local correspondence review procedures.",
        "signature": "A. B. SAMPLE",
        # L.31I: letterhead required for standard letters
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address": "JACKSONVILLE NC 28545-0000",
    }

    for key, value in fields.items():
        kv = f"{key}: {value}"
        ar = _run_manager(["apply", "--session", sid, "--kv", kv])
        if not ar.get("success"):
            _fail(f"apply '{key}' failed: {ar.get('error')}")
        payload = ar.get("payload") or {}
        if key not in payload:
            _fail(f"apply '{key}' did not persist into payload. Keys: {list(payload.keys())}")
        if payload[key] != value:
            # body is coerced to a list of strings; signature is coerced to a dict
            if key == "body" and isinstance(payload[key], list):
                if payload[key] != [value]:
                    _fail(f"apply '{key}' value mismatch: expected ['{value}'], got {payload[key]}")
            elif key == "signature" and isinstance(payload[key], dict):
                if payload[key].get("name") != value:
                    _fail(f"apply '{key}' value mismatch: {payload[key]}")
            else:
                _fail(f"apply '{key}' value mismatch: expected '{value}', got '{payload[key]}'")
        print(f"  apply '{key}' persisted correctly")

    # 3. Verify preview shows draft_preview (not build_status)
    preview = _run_manager(["preview", "--session", sid])
    if preview.get("mode") != "draft_preview":
        _fail(f"preview mode should be draft_preview, got {preview.get('mode')}")
    if not preview.get("preview_gate_met"):
        _fail("preview_gate_met should be True")
    print("  preview mode: draft_preview (correct)")

    # 4. Verify ready shows validation_ready
    ready = _run_manager(["ready", "--session", sid])
    if not ready.get("validation_ready"):
        _fail(f"validation_ready should be True, got {ready.get('validation_ready')}")
    rg = ready.get("render_gate", {})
    if not rg.get("can_render"):
        _fail(f"render_gate.can_render should be True, got {rg}")
    print("  ready validation_ready: True (correct)")

    # 5. Verify approval still not ready (safety gate preserved)
    if ready.get("approved_ready"):
        _fail("approved_ready should be False before explicit approval")
    print("  approved_ready: False (safety gate preserved)")

    # 6. Verify unsupported revise still fails (safety gate preserved)
    from hermes_chat_builder import send_secnav_chat_turn
    rr = send_secnav_chat_turn(chat_id, "make the body more formal")
    if rr.get("success") and rr.get("payload_changed"):
        _fail("unsupported revise should not succeed with payload changes")
    ar = rr.get("assistant_response", "")
    if "wasn't able to apply" not in ar and "nothing in the draft was changed" not in ar:
        _fail(f"unsupported revise assistant_response unexpected: {ar}")
    print("  unsupported revise blocked correctly")

    print()
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
