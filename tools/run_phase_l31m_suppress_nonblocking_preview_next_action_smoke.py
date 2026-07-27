#!/usr/bin/env python3
"""
Phase L.31M — Suppress Nonblocking Preview NEXT ACTION Smoke

Verify that when validation_ready=True and approved_ready=False,
the preview NEXT ACTION tells the user to review/approve instead
of asking for originator code or SSIC.
"""

import sys, os
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS_DIR)

from hermes_chat_builder import start_secnav_chat, send_secnav_chat_turn, get_secnav_chat_status

_USER_REQUEST = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, and make the body about implementing local correspondence review procedures.

letterhead_top_line: united states marine corps
letterhead_activity: MARINE CORPS AIR STATION NEW RIVER
letterhead_address: JACKSONVILLE NC 28545-0000"""

errors = []
def fail(msg):
    errors.append(msg)
    print(f"[FAIL] {msg}")

def check(label, cond):
    if cond:
        print(f"[PASS] {label}")
    else:
        fail(label)

print("Phase L.31M — Suppress Nonblocking Preview NEXT ACTION Smoke")
print("=" * 63)

# 1. Start chat
start = start_secnav_chat()
chat_id = start['chat_id']
print(f"[INFO] chat_id: {chat_id}")

# 2. First turn
r1 = send_secnav_chat_turn(chat_id, _USER_REQUEST)
check("turn 1 reached draft_preview", r1.get("phase") == "draft_preview")

# 3. Status before approval
st = get_secnav_chat_status(chat_id)
preview = st.get("preview_text", "")
next_action = st.get("next_action", {})
print(f"[INFO] validation_ready: {st.get('validation_ready')}")
print(f"[INFO] approved_ready: {st.get('approved_ready')}")
print(f"[INFO] status next_action dict: {next_action}")

check("validation_ready=True", st.get("validation_ready") is True)
check("approved_ready=False before approval", st.get("approved_ready") is False)
check("status next_action empty or nonblocking", not next_action.get("field") or next_action.get("field") in ("", None))

# 4. Preview checks
next_action_text = ""
if "NEXT ACTION" in preview:
    parts = preview.split("NEXT ACTION")
    next_action_text = parts[-1].split("=")[0] if len(parts) > 1 else ""

check("preview NEXT ACTION does not contain 'originator'", "originator" not in next_action_text.lower())
check("preview NEXT ACTION does not contain 'ssic'", "ssic" not in next_action_text.lower())
check("preview NEXT ACTION tells user to review/approve", "looks good" in next_action_text.lower() or "approve" in next_action_text.lower())

# 5. Approve
r2 = send_secnav_chat_turn(chat_id, "looks good")
st2 = get_secnav_chat_status(chat_id)
check("approved_ready after approval", st2.get("approved_ready") is True)

# 6. After approval — preview should tell user to render
preview2 = st2.get("preview_text", "")
next_action_text2 = ""
if "NEXT ACTION" in preview2:
    parts2 = preview2.split("NEXT ACTION")
    next_action_text2 = parts2[-1].split("=")[0] if len(parts2) > 1 else ""
check("approved preview points to render", "make the pdf" in next_action_text2.lower() or "render" in next_action_text2.lower())

# 7. Render
r3 = send_secnav_chat_turn(chat_id, "make the PDF")
pdf_path = r3.get("pdf_path")
pdf_size = r3.get("pdf_size")
check("render succeeded", bool(pdf_path))
if pdf_size:
    check("pdf size > 0", pdf_size > 0)
print(f"[INFO] PDF: {pdf_path} ({pdf_size} bytes)")

print("=" * 63)
if errors:
    print(f"Phase L.31M FAILED ({len(errors)} errors)")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("Phase L.31M ALL CHECKS PASSED")
    sys.exit(0)
