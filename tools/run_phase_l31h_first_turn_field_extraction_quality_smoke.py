#!/usr/bin/env python3
"""
Phase L.31H — First-Turn Field Extraction Quality Smoke

Verifies deterministic extraction for common Hermes first-turn SECNAV letter
requests, especially "to [recipient] about [topic]" and explicit subject/body.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "tools"))

from hermes_chat_builder import (  # noqa: E402
    get_secnav_chat_status,
    send_secnav_chat_turn,
    start_secnav_chat,
)

TEST_REQUEST = (
    "I need a standard letter from Commanding Officer, Marine Corps Air Station New River "
    "to Commanding General, II Marine Expeditionary Force about reviewing correspondence procedures. "
    "Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, "
    "and make the body about implementing local correspondence review procedures."
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    checks: list[str] = []

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        start = start_secnav_chat()
    require(stdout.getvalue() == "", "start_secnav_chat printed to stdout")
    require(start.get("success") is True, f"start failed: {start}")
    chat_id = start["chat_id"]
    checks.append("start silent callable")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        first = send_secnav_chat_turn(chat_id, TEST_REQUEST)
    require(stdout.getvalue() == "", "send_secnav_chat_turn printed to stdout")
    require(first.get("success") is True, f"first turn failed: {first}")
    require(first.get("intent") == "say", f"first turn misclassified: {first.get('intent')}")
    require("wasn't able to apply" not in (first.get("assistant_response") or ""), "unsupported revise response returned")
    checks.append("first turn routes as say, not revise")

    extracted = first.get("extracted_kv") or {}
    require(extracted.get("to") == "Commanding General, II Marine Expeditionary Force", f"bad extracted to: {extracted}")
    require(extracted.get("subj") == "REVIEW OF CORRESPONDENCE PROCEDURES", f"bad subject: {extracted}")
    body = extracted.get("body") or ""
    require(body and not body.lower().startswith("about "), f"body starts with about: {body!r}")
    require("implementing local correspondence review procedures" in body.lower(), f"body missing topic: {body!r}")
    checks.append("deterministic extraction quality")

    status = get_secnav_chat_status(chat_id)
    require(status.get("success") is True, f"status failed: {status}")
    # Before L.31I, first-turn alone reached validation_ready. Now letterhead is required.
    # The L.31H test is about extraction quality, not letterhead readiness.
    # Add letterhead fields so we can verify validation_ready still works end-to-end.
    for kv in (
        "letterhead_top_line: UNITED STATES MARINE CORPS",
        "letterhead_activity: MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address: JACKSONVILLE NC 28545-0000",
    ):
        r = send_secnav_chat_turn(chat_id, kv)
        require(r.get("success") is True, f"letterhead field failed: {r}")
    status = get_secnav_chat_status(chat_id)
    require(status.get("success") is True, f"status after letterhead failed: {status}")
    require(status.get("validation_ready") is True, f"validation not ready: {status}")
    require(status.get("approved_ready") is False, "approved_ready should remain false before explicit approval")
    checks.append("validation ready before approval")

    preview = status.get("preview_text") or first.get("preview_text") or ""
    require("To: Commanding General, II Marine Expeditionary Force" in preview, preview)
    require("To: Commanding General, II Marine Expeditionary Force about" not in preview, preview)
    require("REVIEW OF CORRESPONDENCE PROCEDURES" in preview, preview)
    require("about implementing local correspondence" not in preview.lower(), preview)
    require("This letter addresses implementing local correspondence review procedures." in preview, preview)
    checks.append("preview content quality")

    unsupported = send_secnav_chat_turn(chat_id, "reword it in a poetic style")
    require(unsupported.get("intent") == "revise", f"unsupported revision did not route revise: {unsupported}")
    require(unsupported.get("payload_changed") in (False, None), f"unsupported changed payload: {unsupported}")
    checks.append("unsupported revise still safe")

    render = send_secnav_chat_turn(chat_id, "make the PDF")
    require(render.get("success") is False, "render should be blocked before approval")
    checks.append("render blocked before approval")

    print("Phase L.31H first-turn extraction quality smoke: PASS")
    for idx, check in enumerate(checks, start=1):
        print(f"  {idx}. {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
