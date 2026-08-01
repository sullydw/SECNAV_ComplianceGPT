#!/usr/bin/env python3
"""
Phase L.31N — Unnumbered Body Left Margin Alignment Smoke

Verify that an unnumbered single body paragraph starts at the left margin
(aligned under the Subj line label), NOT at left_margin + 18.
Also verify that numbered paragraphs still indent correctly.
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


def _x0_of_word(words: list, target: str) -> float | None:
    """Return the smallest x0 for any word block matching target."""
    best = None
    for w in words:
        text = w[4] if len(w) > 4 else ""
        if text == target:
            x0 = w[0]
            if best is None or x0 < best:
                best = x0
    return best


def main() -> int:
    print("Phase L.31N — Unnumbered Body Left Margin Alignment Smoke")
    print("=" * 63)

    # Same request as L.31M acceptance rerun (unnumbered body)
    request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, and make the body about implementing local correspondence review procedures.

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
    if first.get("phase") != "draft_preview":
        _fail(f"expected draft_preview, got {first.get('phase')}")
    print("[PASS] first turn reached draft_preview")

    # Approve and render
    approve = send_secnav_chat_turn(chat_id, "looks good")
    if not approve.get("approved_ready"):
        _fail("approval failed")
    print("[PASS] approved_ready=True after approval")

    render = send_secnav_chat_turn(chat_id, "make the PDF")
    if not render.get("success"):
        _fail(f"render failed: {render.get('error')}")
    pdf_path = render.get("pdf_path")
    print(f"[PASS] render succeeds: {pdf_path}")

    # Inspect PDF with fitz
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError:
        print("[WARN] pymupdf not available, skipping coordinate checks")
        print("All L.31N checks passed (no coordinate verification).")
        return 0

    doc = fitz.open(pdf_path)
    page = doc[0]
    words = page.get_text("words")

    # Find x0 of "Subj:" label and "This" (first body word)
    subj_x0 = _x0_of_word(words, "Subj:")
    this_x0 = _x0_of_word(words, "This")

    print(f"[INFO] Subj: label x0 ≈ {subj_x0}")
    print(f"[INFO] body word 'This' x0 ≈ {this_x0}")

    if subj_x0 is None:
        _fail("could not locate 'Subj:' label in PDF")
    if this_x0 is None:
        _fail("could not locate body word 'This' in PDF")

    # Subj: should be near left margin (72 pt)
    if abs(subj_x0 - 72) > 2:
        _fail(f"Subj: x0 {subj_x0} not near left margin 72")
    print("[PASS] Subj: x0 near left margin")

    # Body word must match Subj x0 within 1 pt (aligned under Subj label)
    if abs(this_x0 - subj_x0) > 1:
        _fail(f"body 'This' x0 {this_x0} does not align with Subj x0 {subj_x0}")
    print("[PASS] body word 'This' aligns with Subj: label (within 1 pt)")

    # Body must NOT start at left_margin + 18 (~90 pt)
    if abs(this_x0 - 90) < 2:
        _fail(f"body starts at ~90 pt (left_margin + 18) — regression")
    print("[PASS] body does NOT start at left_margin + 18")

    doc.close()

    # --- Numbered paragraph regression check ---
    print()
    print("--- numbered paragraph regression check ---")

    num_request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject TEST, and make the body:

1. First numbered paragraph about testing.
2. Second numbered paragraph.

letterhead_top_line: united states marine corps
letterhead_activity: MARINE CORPS AIR STATION NEW RIVER
letterhead_address: JACKSONVILLE NC 28545-0000"""

    start2 = start_secnav_chat()
    chat_id2 = start2["chat_id"]
    t1 = send_secnav_chat_turn(chat_id2, num_request)
    if t1.get("phase") != "draft_preview":
        _fail("numbered body chat did not reach draft_preview")
    a2 = send_secnav_chat_turn(chat_id2, "looks good")
    r2 = send_secnav_chat_turn(chat_id2, "make the PDF")
    if not r2.get("success"):
        _fail("numbered body render failed")

    doc2 = fitz.open(r2["pdf_path"])
    page2 = doc2[0]
    words2 = page2.get_text("words")

    # The "1." marker should be at left_margin (72 pt)
    one_marker_x0 = _x0_of_word(words2, "1.")
    # The text after "1." should be at left_margin + 18 (~90 pt)
    first_text_x0 = _x0_of_word(words2, "First")

    print(f"[INFO] numbered '1.' marker x0 ≈ {one_marker_x0}")
    print(f"[INFO] numbered 'First' text x0 ≈ {first_text_x0}")

    if one_marker_x0 is None:
        _fail("could not locate '1.' marker in numbered PDF")
    if first_text_x0 is None:
        _fail("could not locate 'First' text in numbered PDF")

    if abs(one_marker_x0 - 72) > 2:
        _fail(f"numbered marker '1.' x0 {one_marker_x0} not near left margin")
    print("[PASS] numbered marker '1.' at left margin")

    if abs(first_text_x0 - 90) > 3:
        _fail(f"numbered text 'First' x0 {first_text_x0} not near left_margin + 18")
    print("[PASS] numbered text indented correctly (~left_margin + 18)")

    doc2.close()

    print()
    print("All L.31N checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
