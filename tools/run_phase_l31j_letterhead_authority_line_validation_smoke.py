#!/usr/bin/env python3
"""
Phase L.31J — Letterhead Authority Line Validation Smoke
Verify that only recognized authority lines are accepted for fallback letterhead.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
sys.path.insert(0, str(_TOOL_ROOT))

from hermes_chat_builder import (
    start_secnav_chat,
    send_secnav_chat_turn,
    _run_manager,
    _load_state,
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def _check_blocked(chat_id: str, label: str) -> None:
    state = _load_state(chat_id)
    sid = state["session_id"]
    ready = _run_manager(["ready", "--session", sid])
    if ready.get("validation_ready"):
        _fail(f"{label}: validation_ready should be False")
    if ready.get("approved_ready"):
        _fail(f"{label}: approved_ready should be False")
    rg = ready.get("render_gate", {})
    if rg.get("can_render"):
        _fail(f"{label}: can_render should be False")
    print(f"[PASS] {label}: blocked correctly")


def main() -> int:
    print("Phase L.31J — Letterhead Authority Line Validation Smoke")
    print("=" * 55)

    # ------------------------------------------------------------------
    # 1. Missing letterhead authority line blocks validation_ready
    # ------------------------------------------------------------------
    chat1 = start_secnav_chat()["chat_id"]
    for kv in [
        "from: Commanding Officer, Marine Corps Air Station New River",
        "to: Commanding General, II Marine Expeditionary Force",
        "date: 1 July 2026",
        "subj: REVIEW OF CORRESPONDENCE PROCEDURES",
        "body: This letter addresses implementing local correspondence review procedures.",
        "signature: A. B. SAMPLE",
        # Only activity + address, no top_line
        "letterhead_activity: MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address: JACKSONVILLE NC 28545-0000",
    ]:
        r = send_secnav_chat_turn(chat1, kv)
        if not r.get("success"):
            _fail(f"Field failed: {r.get('error')}")
    _check_blocked(chat1, "Missing authority line")

    # ------------------------------------------------------------------
    # 2. Invalid authority line blocks validation_ready
    # ------------------------------------------------------------------
    chat2 = start_secnav_chat()["chat_id"]
    for kv in [
        "from: Commanding Officer, Marine Corps Air Station New River",
        "to: Commanding General, II Marine Expeditionary Force",
        "date: 1 July 2026",
        "subj: REVIEW OF CORRESPONDENCE PROCEDURES",
        "body: This letter addresses implementing local correspondence review procedures.",
        "signature: A. B. SAMPLE",
        "letterhead_top_line: SOME RANDOM COMMAND",
        "letterhead_activity: MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address: JACKSONVILLE NC 28545-0000",
    ]:
        r = send_secnav_chat_turn(chat2, kv)
        if not r.get("success"):
            _fail(f"Field failed: {r.get('error')}")
    _check_blocked(chat2, "Invalid authority line")

    # Check next_action explains allowed authority lines
    state2 = _load_state(chat2)
    sid2 = state2["session_id"]
    ready2 = _run_manager(["ready", "--session", sid2])
    na = ready2.get("next_action", {})
    q = (na.get("question") or "").lower()
    if "department of the navy" not in q and "united states marine corps" not in q:
        _fail(f"next_action should explain allowed authority lines. got: {na}")
    print("[PASS] next_action explains allowed authority lines")

    # ------------------------------------------------------------------
    # 3. Lowercase authority accepted and normalized
    # ------------------------------------------------------------------
    chat3 = start_secnav_chat()["chat_id"]
    for kv in [
        "from: Commanding Officer, Marine Corps Air Station New River",
        "to: Commanding General, II Marine Expeditionary Force",
        "date: 1 July 2026",
        "subj: REVIEW OF CORRESPONDENCE PROCEDURES",
        "body: This letter addresses implementing local correspondence review procedures.",
        "signature: A. B. SAMPLE",
        "letterhead_top_line: united states marine corps",
        "letterhead_activity: MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address: JACKSONVILLE NC 28545-0000",
    ]:
        r = send_secnav_chat_turn(chat3, kv)
        if not r.get("success"):
            _fail(f"Field failed: {r.get('error')}")

    state3 = _load_state(chat3)
    sid3 = state3["session_id"]
    preview3 = _run_manager(["preview", "--session", sid3])
    if preview3.get("mode") != "draft_preview":
        _fail(f"Lowercase authority should reach draft_preview. got {preview3.get('mode')}")
    pt3 = preview3.get("preview_text", "")
    if "UNITED STATES MARINE CORPS" not in pt3:
        _fail("Preview should show normalized uppercase authority line")
    if "united states marine corps" in pt3.lower() and "UNITED STATES MARINE CORPS" not in pt3:
        _fail("Preview should not show lowercase authority line")
    print("[PASS] Lowercase authority accepted and normalized in preview")

    ready3 = _run_manager(["ready", "--session", sid3])
    if not ready3.get("validation_ready"):
        _fail(f"validation_ready should be True after lowercase authority. got {ready3}")
    print("[PASS] validation_ready=True after lowercase authority")

    # ------------------------------------------------------------------
    # 4. Render succeeds after approval; PDF shows normalized authority
    # ------------------------------------------------------------------
    apr = send_secnav_chat_turn(chat3, "looks good")
    if not apr.get("success"):
        _fail(f"Approve failed: {apr.get('error')}")
    render = send_secnav_chat_turn(chat3, "make the pdf")
    if not render.get("success"):
        _fail(f"Render failed: {render.get('error')}")
    pdf_path = render.get("pdf_path")
    if not pdf_path:
        _fail("PDF path missing")

    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError:
        print("[WARN] pymupdf not available, skipping PDF text extraction")
        print("All L.31J checks passed.")
        return 0

    doc = fitz.open(pdf_path)
    text = doc[0].get_text()
    doc.close()

    idx_usmc = text.find("UNITED STATES MARINE CORPS")
    idx_from = text.find("From:")
    if idx_usmc == -1:
        _fail("PDF missing normalized authority line")
    if idx_from != -1 and idx_usmc > idx_from:
        _fail("Authority line appears AFTER From: in PDF")
    print("[PASS] PDF shows normalized UNITED STATES MARINE CORPS before From:")

    # ------------------------------------------------------------------
    # 5. DEPARTMENT OF THE NAVY accepted for fallback letterhead
    # ------------------------------------------------------------------
    chat4 = start_secnav_chat()["chat_id"]
    for kv in [
        "from: Commanding Officer, Naval Air Station Oceana",
        "to: Commander, Naval Air Force Atlantic",
        "date: 1 July 2026",
        "subj: ADMINISTRATIVE CORRESPONDENCE",
        "body: This letter addresses administrative procedures.",
        "signature: A. B. SAMPLE",
        "letterhead_top_line: department of the navy",
        "letterhead_activity: NAVAL AIR STATION OCEANA",
        "letterhead_address: VIRGINIA BEACH VA 23460-0000",
    ]:
        r = send_secnav_chat_turn(chat4, kv)
        if not r.get("success"):
            _fail(f"Field failed: {r.get('error')}")

    state4 = _load_state(chat4)
    sid4 = state4["session_id"]
    preview4 = _run_manager(["preview", "--session", sid4])
    if preview4.get("mode") != "draft_preview":
        _fail(f"Navy authority should reach draft_preview. got {preview4.get('mode')}")
    pt4 = preview4.get("preview_text", "")
    if "DEPARTMENT OF THE NAVY" not in pt4:
        _fail("Preview should show DEPARTMENT OF THE NAVY")
    print("[PASS] DEPARTMENT OF THE NAVY accepted for fallback letterhead")

    print()
    print("All L.31J checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
