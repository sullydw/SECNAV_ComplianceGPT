#!/usr/bin/env python3
"""
Phase L.31K — Mixed Prose + Key:Value Intake Merge Smoke

Verify that a first-turn message containing natural prose plus key:value
letterhead fields is merged into one deterministic apply payload.
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


def _assert_contains(label: str, text: str, needle: str) -> None:
    if needle not in text:
        _fail(f"{label}: missing {needle!r}")
    print(f"[PASS] {label}: {needle}")


def _assert_order(text: str, ordered: list[str]) -> None:
    pos = -1
    for item in ordered:
        idx = text.find(item)
        if idx == -1:
            _fail(f"PDF/order proof missing {item!r}")
        if idx < pos:
            _fail(f"PDF/order proof out of order at {item!r}")
        pos = idx
    print("[PASS] PDF text order proof")


def main() -> int:
    print("Phase L.31K — Mixed Prose + Key:Value Intake Merge Smoke")
    print("=" * 63)

    request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, SSIC 5216, originator code S-1, subject REVIEW OF CORRESPONDENCE PROCEDURES, and make the body about implementing local correspondence review procedures.

letterhead_top_line: united states marine corps
letterhead_activity: MARINE CORPS AIR STATION NEW RIVER
letterhead_address: JACKSONVILLE NC 28545-0000"""

    start = start_secnav_chat()
    if not start.get("success"):
        _fail(f"start failed: {start}")
    chat_id = start["chat_id"]
    print(f"[INFO] chat_id: {chat_id}")

    first = send_secnav_chat_turn(chat_id, request)
    if not first.get("success"):
        _fail(f"first turn failed: {first.get('error')}")
    if first.get("intent") != "say":
        _fail(f"expected intent=say, got {first.get('intent')}")
    if first.get("phase") != "draft_preview":
        _fail(f"first mixed turn should reach draft_preview, got {first.get('phase')}")
    if not first.get("validation_ready"):
        _fail("validation_ready should be True after mixed first turn")
    if first.get("approved_ready"):
        _fail("approved_ready should be False before approval")
    print("[PASS] mixed first turn reached draft_preview with validation_ready=True")

    extracted = first.get("extracted_kv") or {}
    expected_fields = {
        "letterhead_top_line": "united states marine corps",
        "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address": "JACKSONVILLE NC 28545-0000",
        "ssic": "5216",
        "originator_code": "S-1",
        "from": "Commanding Officer, Marine Corps Air Station New River",
        "to": "Commanding General, II Marine Expeditionary Force",
        "date": "1 July 2026",
        "subj": "REVIEW OF CORRESPONDENCE PROCEDURES",
        "body": "This letter addresses implementing local correspondence review procedures.",
        "signature": "A. B. SAMPLE",
    }
    for key, expected in expected_fields.items():
        got = extracted.get(key)
        if got != expected:
            _fail(f"extracted {key!r}: expected {expected!r}, got {got!r}")
    print("[PASS] extracted_kv includes prose + explicit key:value fields")

    preview = first.get("preview_text") or ""
    preview_checks = [
        "LETTERHEAD",
        "UNITED STATES MARINE CORPS",
        "MARINE CORPS AIR STATION NEW RIVER",
        "JACKSONVILLE NC 28545-0000",
        "SSIC: 5216",
        "Originator Code: S-1",
        "Date: 1 July 2026",
        "From: Commanding Officer, Marine Corps Air Station New River",
        "To: Commanding General, II Marine Expeditionary Force",
        "REVIEW OF CORRESPONDENCE PROCEDURES",
        "This letter addresses implementing local correspondence review procedures.",
        "Name:  A. B. SAMPLE",
    ]
    for item in preview_checks:
        _assert_contains("preview", preview, item)

    early_render = send_secnav_chat_turn(chat_id, "make the PDF")
    if early_render.get("success"):
        _fail("render should be blocked before approval")
    print("[PASS] render blocked before approval")

    approve = send_secnav_chat_turn(chat_id, "looks good")
    if not approve.get("success"):
        _fail(f"approve failed: {approve.get('error')}")
    if not approve.get("approved_ready"):
        _fail(f"approved_ready should be True after approval, got {approve}")
    print("[PASS] approval succeeds and approved_ready=True")

    render = send_secnav_chat_turn(chat_id, "make the PDF")
    if not render.get("success"):
        _fail(f"render failed: {render.get('error')}")
    pdf_path = render.get("pdf_path")
    pdf_size = render.get("pdf_size")
    if not pdf_path or not pdf_size:
        _fail(f"render missing pdf_path/pdf_size: {render}")
    print(f"[PASS] render succeeds: {pdf_path} ({pdf_size} bytes)")

    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError:
        print("[WARN] pymupdf not available, skipping PDF text extraction")
        print("All L.31K checks passed.")
        return 0

    doc = fitz.open(pdf_path)
    text = doc[0].get_text()
    doc.close()
    _assert_order(text, [
        "UNITED STATES MARINE CORPS",
        "MARINE CORPS AIR STATION NEW RIVER",
        "JACKSONVILLE NC 28545-0000",
        "5216",
        "S-1",
        "1 Jul 26",
        "From:",
        "To:",
        "Subj:",
        "This letter addresses implementing local correspondence review procedures.",
        "A. B. SAMPLE",
    ])

    status = get_secnav_chat_status(chat_id)
    if not status.get("approved_ready") or not status.get("validation_ready"):
        _fail(f"final status should be validation_ready and approved_ready: {status}")
    print("[PASS] final status ready gates remain true")

    print()
    print("All L.31K checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
