#!/usr/bin/env python3
"""
Phase L.31I — Standard Letterhead Required Smoke
Verify standard letters cannot reach draft_preview or render without letterhead data.
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


def main() -> int:
    print("Phase L.31I — Standard Letterhead Required Smoke")
    print("=" * 55)

    # ------------------------------------------------------------------
    # 1. Standard letter WITHOUT letterhead fields should NOT reach draft_preview
    # ------------------------------------------------------------------
    chat_id = start_secnav_chat()["chat_id"]
    fields = [
        "from: Commanding Officer, Marine Corps Air Station New River",
        "to: Commanding General, II Marine Expeditionary Force",
        "date: 1 July 2026",
        "subj: REVIEW OF CORRESPONDENCE PROCEDURES",
        "body: This letter addresses implementing local correspondence review procedures.",
        "signature: A. B. SAMPLE",
    ]
    for text in fields:
        send_secnav_chat_turn(chat_id, text)

    state = _load_state(chat_id)
    sid = state["session_id"]
    preview = _run_manager(["preview", "--session", sid])
    ready = _run_manager(["ready", "--session", sid])

    if preview.get("mode") == "draft_preview":
        _fail("Standard letter without letterhead should NOT reach draft_preview")
    if ready.get("validation_ready"):
        _fail("validation_ready should be False when letterhead is missing")
    if ready.get("approved_ready"):
        _fail("approved_ready should be False")
    if "letterhead" not in (preview.get("missing_for_preview") or []):
        # Check build_status preview text for letterhead mention
        pt = preview.get("preview_text", "")
        if "letterhead" not in pt.lower() and "LETTERHEAD" not in pt:
            _fail(f"Missing fields should mention letterhead. missing_for_preview={preview.get('missing_for_preview')}")
    print("[PASS] Standard letter without letterhead stays in build_status")

    # ------------------------------------------------------------------
    # 2. Add fallback letterhead fields via key:value
    # ------------------------------------------------------------------
    lh_fields = [
        "letterhead_top_line: UNITED STATES MARINE CORPS",
        "letterhead_activity: MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address: JACKSONVILLE NC 28545-0000",
    ]
    for text in lh_fields:
        r = send_secnav_chat_turn(chat_id, text)
        if not r.get("success"):
            _fail(f"Letterhead field failed: {r.get('error')}")

    # ------------------------------------------------------------------
    # 3. Preview should now reach draft_preview with letterhead block
    # ------------------------------------------------------------------
    preview2 = _run_manager(["preview", "--session", sid])
    if preview2.get("mode") != "draft_preview":
        _fail(f"Should reach draft_preview after letterhead. Got {preview2.get('mode')}")
    pt2 = preview2.get("preview_text", "")
    if "UNITED STATES MARINE CORPS" not in pt2:
        _fail("Preview should show letterhead top line")
    if "MARINE CORPS AIR STATION NEW RIVER" not in pt2:
        _fail("Preview should show letterhead activity")
    if "JACKSONVILLE NC 28545-0000" not in pt2:
        _fail("Preview should show letterhead address")
    print("[PASS] Preview shows letterhead block after fallback fields added")

    # ------------------------------------------------------------------
    # 4. validation_ready should now be True
    # ------------------------------------------------------------------
    ready2 = _run_manager(["ready", "--session", sid])
    if not ready2.get("validation_ready"):
        _fail(f"validation_ready should be True after letterhead. Got {ready2}")
    if ready2.get("approved_ready"):
        _fail("approved_ready should still be False before explicit approval")
    print("[PASS] validation_ready=True, approved_ready=False")

    # ------------------------------------------------------------------
    # 5. Render blocked before approval
    # ------------------------------------------------------------------
    render_r = send_secnav_chat_turn(chat_id, "make the pdf")
    if render_r.get("success"):
        _fail("Render should be blocked before approval")
    print("[PASS] Render blocked before approval")

    # ------------------------------------------------------------------
    # 6. Approve
    # ------------------------------------------------------------------
    apr = send_secnav_chat_turn(chat_id, "looks good")
    if not apr.get("success"):
        _fail(f"Approve failed: {apr.get('error')}")
    print("[PASS] Approve succeeds")

    # ------------------------------------------------------------------
    # 7. Render succeeds after approval
    # ------------------------------------------------------------------
    render2 = send_secnav_chat_turn(chat_id, "make the pdf")
    if not render2.get("success"):
        _fail(f"Render after approval failed: {render2.get('error')}")
    pdf_path = render2.get("pdf_path")
    if not pdf_path:
        _fail("PDF path missing")
    print(f"[PASS] Render succeeds: {pdf_path}")

    # ------------------------------------------------------------------
    # 8. PDF text contains letterhead before date/from/to/subj
    # ------------------------------------------------------------------
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError:
        print("[WARN] pymupdf not available, skipping PDF text extraction")
        print("All L.31I checks passed.")
        return 0

    doc = fitz.open(pdf_path)
    text = doc[0].get_text()
    doc.close()

    # Verify letterhead lines appear BEFORE "From:" or "Subj:" in the text
    idx_usmc = text.find("UNITED STATES MARINE CORPS")
    idx_activity = text.find("MARINE CORPS AIR STATION NEW RIVER")
    idx_address = text.find("JACKSONVILLE NC 28545-0000")
    idx_from = text.find("From:")
    idx_subj = text.find("Subj:")

    if idx_usmc == -1:
        _fail("PDF missing letterhead top line")
    if idx_activity == -1:
        _fail("PDF missing letterhead activity")
    if idx_address == -1:
        _fail("PDF missing letterhead address")

    # Ensure letterhead appears BEFORE the From/Subj content
    if idx_from != -1 and idx_usmc > idx_from:
        _fail(f"Letterhead top line appears AFTER From: in PDF. usmc_idx={idx_usmc} from_idx={idx_from}")
    if idx_subj != -1 and idx_usmc > idx_subj:
        _fail(f"Letterhead top line appears AFTER Subj: in PDF. usmc_idx={idx_usmc} subj_idx={idx_subj}")

    print("[PASS] PDF contains letterhead before date/from/to/subj")
    print()
    print("All L.31I checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
