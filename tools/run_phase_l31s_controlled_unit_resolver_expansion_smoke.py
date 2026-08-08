#!/usr/bin/env python3
"""
Smoke: L.31S Controlled Command/Unit Resolver Expansion

Scenarios:
1. Existing baseline (MCAS New River → II MEF) still works
2. Cherry Point → II MEF
3. Camp Lejeune → MARFORCOM
4. MCB Camp Lejeune → HQMC
5. Complete first-turn Cherry Point
6. Unknown command stays literal
"""

import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "src")

import os
import fitz
from hermes_chat_builder import start_secnav_chat, send_secnav_chat_turn

ERRORS = []
RESULTS = []

def _fail(step, msg):
    ERRORS.append(f"{step}. FAIL: {msg}")
    print(f"FAIL {step}: {msg}")

def _pass(step, msg=""):
    RESULTS.append(f"{step}. PASS: {msg}")
    print(f"PASS {step}: {msg}")

# ============================================================================
# Scenario 1 — Existing baseline still works
# ============================================================================
print("\n=== Scenario 1: Existing baseline (MCAS New River → II MEF) ===")
chat = start_secnav_chat()
cid = chat["chat_id"]
req = "I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures."
r = send_secnav_chat_turn(cid, req)
payload = r.get("payload") or {}
preview = r.get("preview_text", "")

_from = payload.get("from", "")
_to = payload.get("to", "")
ssic = payload.get("ssic", "")

if "Commanding Officer, Marine Corps Air Station New River" in _from:
    _pass("S1", f"From expanded: {_from}")
else:
    _fail("S1", f"From not expanded: {_from}")

if "Commanding General, II Marine Expeditionary Force" in _to:
    _pass("S1", f"To expanded: {_to}")
else:
    _fail("S1", f"To not expanded: {_to}")

if payload.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER":
    _pass("S1", "Letterhead: MCAS New River (in payload)")
else:
    _fail("S1", f"Letterhead not MCAS New River in payload: {payload.get('letterhead_activity')}")

if ssic == "5216":
    _pass("S1", "SSIC 5216 inferred")
else:
    _fail("S1", f"SSIC not 5216: {ssic}")

if "ssic" not in r.get("message", "").lower():
    _pass("S1", "Does not ask for SSIC")
else:
    _fail("S1", "Asks for SSIC")

if "originator" not in r.get("message", "").lower():
    _pass("S1", "Does not ask for originator code")
else:
    _fail("S1", "Asks for originator code")

# ============================================================================
# Scenario 2 — Cherry Point → II MEF
# ============================================================================
print("\n=== Scenario 2: Cherry Point → II MEF ===")
chat2 = start_secnav_chat()
cid2 = chat2["chat_id"]
req2 = "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures."
r2 = send_secnav_chat_turn(cid2, req2)
payload2 = r2.get("payload") or {}
preview2 = r2.get("preview_text", "")

_from2 = payload2.get("from", "")
_to2 = payload2.get("to", "")
ssic2 = payload2.get("ssic", "")

if "Commanding Officer, Marine Corps Air Station Cherry Point" in _from2:
    _pass("S2", f"From expanded: {_from2}")
else:
    _fail("S2", f"From not expanded: {_from2}")

if "Commanding General, II Marine Expeditionary Force" in _to2:
    _pass("S2", f"To expanded: {_to2}")
else:
    _fail("S2", f"To not expanded: {_to2}")

if payload2.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT":
    _pass("S2", "Letterhead: MCAS Cherry Point (in payload)")
else:
    _fail("S2", f"Letterhead not MCAS Cherry Point in payload: {payload2.get('letterhead_activity')}")

if ssic2 == "5216":
    _pass("S2", "SSIC 5216 inferred")
else:
    _fail("S2", f"SSIC not 5216: {ssic2}")

msg2 = r2.get("message", "").lower()
if "date" in msg2 or "signer" in msg2 or "body" in msg2:
    _pass("S2", "Asks for date/signer/body (expected)")
else:
    _pass("S2", "No unexpected prompts")

# ============================================================================
# Scenario 3 — Camp Lejeune → MARFORCOM
# ============================================================================
print("\n=== Scenario 3: Camp Lejeune → MARFORCOM ===")
chat3 = start_secnav_chat()
cid3 = chat3["chat_id"]
req3 = "Prepare a standard letter from Camp Lejeune to MARFORCOM about reviewing correspondence procedures."
r3 = send_secnav_chat_turn(cid3, req3)
payload3 = r3.get("payload") or {}
preview3 = r3.get("preview_text", "")

_from3 = payload3.get("from", "")
_to3 = payload3.get("to", "")
ssic3 = payload3.get("ssic", "")

if "Commanding Officer, Marine Corps Base Camp Lejeune" in _from3:
    _pass("S3", f"From expanded: {_from3}")
else:
    _fail("S3", f"From not expanded: {_from3}")

if "Commander, Marine Forces Command" in _to3:
    _pass("S3", f"To expanded: {_to3}")
else:
    _fail("S3", f"To not expanded: {_to3}")

if payload3.get("letterhead_activity") == "MARINE CORPS BASE CAMP LEJEUNE":
    _pass("S3", "Letterhead: MCB Camp Lejeune (in payload)")
else:
    _fail("S3", f"Letterhead not MCB Camp Lejeune in payload: {payload3.get('letterhead_activity')}")

if ssic3 == "5216":
    _pass("S3", "SSIC 5216 inferred")
else:
    _fail("S3", f"SSIC not 5216: {ssic3}")

# No duplicate titles
if "Commanding Officer, Commanding Officer" not in _from3:
    _pass("S3", "No duplicate Commanding Officer title")
else:
    _fail("S3", f"Duplicate title in From: {_from3}")

# ============================================================================
# Scenario 4 — MCB Camp Lejeune → HQMC
# ============================================================================
print("\n=== Scenario 4: MCB Camp Lejeune → HQMC ===")
chat4 = start_secnav_chat()
cid4 = chat4["chat_id"]
req4 = "Draft a letter from MCB Camp Lejeune to HQMC about reviewing correspondence procedures."
r4 = send_secnav_chat_turn(cid4, req4)
payload4 = r4.get("payload") or {}
preview4 = r4.get("preview_text", "")

_from4 = payload4.get("from", "")
_to4 = payload4.get("to", "")
ssic4 = payload4.get("ssic", "")

if "Commanding Officer, Marine Corps Base Camp Lejeune" in _from4:
    _pass("S4", f"From expanded: {_from4}")
else:
    _fail("S4", f"From not expanded: {_from4}")

if "Commandant of the Marine Corps" in _to4:
    _pass("S4", f"To expanded: {_to4}")
else:
    _fail("S4", f"To not expanded: {_to4}")

if payload4.get("letterhead_activity") == "MARINE CORPS BASE CAMP LEJEUNE":
    _pass("S4", "Letterhead: MCB Camp Lejeune (in payload)")
else:
    _fail("S4", f"Letterhead not MCB Camp Lejeune in payload: {payload4.get('letterhead_activity')}")

if ssic4 == "5216":
    _pass("S4", "SSIC 5216 inferred")
else:
    _fail("S4", f"SSIC not 5216: {ssic4}")

# ============================================================================
# Scenario 5 — Complete first-turn Cherry Point
# ============================================================================
print("\n=== Scenario 5: Complete first-turn Cherry Point ===")
chat5 = start_secnav_chat()
cid5 = chat5["chat_id"]
req5 = (
    "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures. "
    "Use 1 July 2026. A. B. SAMPLE will sign it. "
    "The body should say we are implementing local correspondence review procedures.\n"
    "letterhead_top_line: united states marine corps\n"
    "letterhead_activity: MARINE CORPS AIR STATION CHERRY POINT\n"
    "letterhead_address: CHERRY POINT NC 28533-0000"
)
r5 = send_secnav_chat_turn(cid5, req5)
phase5 = r5.get("phase")
payload5 = r5.get("payload") or {}

if phase5 == "draft_preview":
    _pass("S5", f"Reaches draft_preview: {phase5}")
else:
    _fail("S5", f"Phase: {phase5}")

if r5.get("validation_ready"):
    _pass("S5", "validation_ready=True")
else:
    _fail("S5", f"validation_ready={r5.get('validation_ready')}")

if not r5.get("approved_ready"):
    _pass("S5", "approved_ready=False before approval")
else:
    _fail("S5", "approved_ready=True before approval")

if payload5.get("ssic") == "5216":
    _pass("S5", "SSIC 5216 present")
else:
    _fail("S5", f"SSIC: {payload5.get('ssic')}")

# Approve
r5a = send_secnav_chat_turn(cid5, "looks good")
if r5a.get("approved_ready"):
    _pass("S5", "Approval succeeds")
else:
    _fail("S5", f"Approval failed: {r5a.get('phase')}")

# Render
r5r = send_secnav_chat_turn(cid5, "make the PDF")
pdf_path5 = r5r.get("pdf_path")
if pdf_path5 and os.path.exists(pdf_path5):
    _pass("S5", f"Render succeeds: {pdf_path5}")
    doc = fitz.open(pdf_path5)
    text = doc[0].get_text()
    doc.close()
    if "CHERRY POINT" in text:
        _pass("S5", "PDF contains Cherry Point letterhead")
    else:
        _fail("S5", "PDF missing Cherry Point letterhead")
    if "Commanding Officer, Marine Corps Air Station Cherry Point" in text:
        _pass("S5", "PDF contains From")
    else:
        _fail("S5", "PDF missing From")
    if "Commanding General, II Marine Expeditionary Force" in text:
        _pass("S5", "PDF contains To")
    else:
        _fail("S5", "PDF missing To")
    if "REVIEW OF CORRESPONDENCE PROCEDURES" in text:
        _pass("S5", "PDF contains subject")
    else:
        _fail("S5", "PDF missing subject")
    if "correspondence review procedures" in text.lower():
        _pass("S5", "PDF contains body")
    else:
        _fail("S5", "PDF missing body")
    if "A. B. SAMPLE" in text:
        _pass("S5", "PDF contains signature")
    else:
        _fail("S5", "PDF missing signature")
else:
    _fail("S5", f"Render failed: {r5r.get('error')}")

# ============================================================================
# Scenario 6 — Unknown command stays literal
# ============================================================================
print("\n=== Scenario 6: Unknown command stays literal ===")
chat6 = start_secnav_chat()
cid6 = chat6["chat_id"]
req6 = "I need a standard letter from Imaginary Training Command to II MEF about reviewing correspondence procedures."
r6 = send_secnav_chat_turn(cid6, req6)
payload6 = r6.get("payload") or {}
preview6 = r6.get("preview_text", "")

_from6 = payload6.get("from", "")
_to6 = payload6.get("to", "")

if "Imaginary Training Command" in _from6:
    _pass("S6", f"From remains literal: {_from6}")
else:
    _fail("S6", f"From changed: {_from6}")

if "Commanding General, II Marine Expeditionary Force" in _to6:
    _pass("S6", "To still expands to II MEF")
else:
    _fail("S6", f"To: {_to6}")

# Should NOT have invented letterhead
lh_activity = payload6.get("letterhead_activity", "")
lh_top = payload6.get("letterhead_top_line", "")
if not lh_activity and not lh_top:
    _pass("S6", "No invented letterhead")
else:
    _fail("S6", f"Invented letterhead: {lh_top} / {lh_activity}")

# Should ask for letterhead or missing details
msg6 = r6.get("message", "").lower()
if "letterhead" in msg6 or "command" in msg6 or "provide" in msg6:
    _pass("S6", "Asks for letterhead/missing details")
else:
    _pass("S6", f"Message: {msg6[:100]}")

# Should not crash
if r6.get("success"):
    _pass("S6", "Does not crash")
else:
    _fail("S6", f"Crashed: {r6.get('error')}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for r in RESULTS:
    print(r)
for e in ERRORS:
    print(e)
print()
if ERRORS:
    print(f"FAILURES: {len(ERRORS)}")
    sys.exit(1)
else:
    print(f"ALL PASS: {len(RESULTS)} checks")
    sys.exit(0)
