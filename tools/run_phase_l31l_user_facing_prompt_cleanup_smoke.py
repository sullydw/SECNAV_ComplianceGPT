#!/usr/bin/env python3
"""
Phase L.31L — User-Facing Prompt Cleanup Smoke

Verify that when validation_ready=True with a complete standard letter
that lacks SSIC/originator_code, the preview labels those fields as
optional and the next_action does not ask for them.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
sys.path.insert(0, str(_TOOL_ROOT))

from hermes_chat_builder import (  # noqa: E402
    start_secnav_chat,
    send_secnav_chat_turn,
    get_secnav_chat_status,
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def _assert_not_contains(label: str, text: str, needle: str) -> None:
    if needle in text:
        _fail(f"{label}: unexpectedly contains {needle!r}")
    print(f"[PASS] {label}: does not contain {needle}")


def _assert_contains(label: str, text: str, needle: str) -> None:
    if needle not in text:
        _fail(f"{label}: missing {needle!r}")
    print(f"[PASS] {label}: {needle}")


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(f"{label}: expected {expected!r}, got {actual!r}")
    print(f"[PASS] {label}: {actual}")


def main() -> int:
    print("Phase L.31L — User-Facing Prompt Cleanup Smoke")
    print("=" * 63)

    request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, and make the body about implementing local correspondence review procedures.

letterhead_top_line: united states marine corps
letterhead_activity: MARINE CORPS AIR STATION NEW RIVER
letterhead_address: JACKSONVILLE NC 28545-0000"""

    start = start_secnav_chat()
    if not start.get("success"):
        _fail(f"start failed: {start}")
    chat_id = start["chat_id"]
    print(f"[INFO] chat_id: {chat_id}")

    # 1. Mixed first turn
    r1 = send_secnav_chat_turn(chat_id, request)
    print(f"[INFO] turn 1 phase: {r1.get('phase')}")
    print(f"[INFO] turn 1 message: {r1.get('message', '')[:120]}")

    # 2. Provide body if missing
    if r1.get("phase") != "draft_preview":
        r2 = send_secnav_chat_turn(chat_id, "body: This letter addresses implementing local correspondence review procedures.")
        print(f"[INFO] turn 2 phase: {r2.get('phase')}")
    else:
        r2 = r1

    # 3. Ensure draft_preview reached
    if r2.get("phase") != "draft_preview":
        _fail(f"Did not reach draft_preview after follow-up. phase={r2.get('phase')}")

    # 4. Get status
    st = get_secnav_chat_status(chat_id)
    print(f"[INFO] status phase: {st.get('phase')}")
    print(f"[INFO] validation_ready: {st.get('validation_ready')}")
    print(f"[INFO] approved_ready: {st.get('approved_ready')}")

    preview = st.get("preview_text") or ""
    next_action = st.get("next_action") or {}
    next_text = str(next_action.get("question", "")) + " " + str(next_action.get("recommended_action", ""))

    # 5. Assertions
    _assert_equal("validation_ready", st.get("validation_ready"), True)
    _assert_equal("approved_ready before approval", st.get("approved_ready"), False)

    # Preview must show optional labels for SSIC and originator code
    _assert_contains("preview SSIC label", preview, "SSIC: [OPTIONAL / IF USED]")
    _assert_contains("preview originator label", preview, "Originator Code: [OPTIONAL / IF USED]")

    # Preview must not show old NEEDED placeholders for SSIC/originator
    _assert_not_contains("preview SSIC", preview, "[SSIC NEEDED]")
    _assert_not_contains("preview originator", preview, "[ORIGINATOR CODE NEEDED]")

    # Next action must not ask for SSIC or originator code
    _assert_not_contains("next_action SSIC", next_text, "ssic")
    _assert_not_contains("next_action originator", next_text, "originator")

    # Required fields must still appear
    _assert_contains("preview date", preview, "1 July 2026")
    _assert_contains("preview from", preview, "Commanding Officer")
    _assert_contains("preview to", preview, "Commanding General")
    _assert_contains("preview subject", preview, "REVIEW OF CORRESPONDENCE PROCEDURES")
    _assert_contains("preview body", preview, "correspondence review procedures")
    _assert_contains("preview signature", preview, "A. B. SAMPLE")

    # Letterhead lines
    _assert_contains("preview letterhead top", preview, "UNITED STATES MARINE CORPS")
    _assert_contains("preview letterhead activity", preview, "MARINE CORPS AIR STATION NEW RIVER")
    _assert_contains("preview letterhead address", preview, "JACKSONVILLE NC 28545-0000")

    # 6. Approval
    r3 = send_secnav_chat_turn(chat_id, "looks good")
    st2 = get_secnav_chat_status(chat_id)
    _assert_equal("approved_ready after approval", st2.get("approved_ready"), True)

    # 7. Render
    r4 = send_secnav_chat_turn(chat_id, "make the PDF")
    if not r4.get("pdf_path"):
        _fail(f"render failed: {r4}")
    print(f"[PASS] render succeeded: {r4.get('pdf_path')}")
    print(f"[PASS] PDF size: {r4.get('pdf_size')} bytes")

    print("=" * 63)
    print("Phase L.31L ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
