#!/usr/bin/env python3
"""Generate H.16 burn-in fixtures. Run from repo root."""
import json, os
from pathlib import Path

DIR = Path(__file__).parent

def write(name, payload):
    with open(DIR / name, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

# ------------------------------------------------------------------
# 1. Standard letters with valid from (20) — PASS
# ------------------------------------------------------------------
valid_froms = [
    "Commanding Officer, USS EXAMPLE",
    "Commanding Officer, Naval Air Station Example",
    "Commander, Naval Surface Force Atlantic",
    "Commanding Officer, Marine Corps Base Example",
    "Commanding Officer, Navy Recruiting District Example",
    "Commander, Navy Expeditionary Combat Command",
    "Commanding Officer, Naval Support Activity Example",
    "Commander, Naval Air Systems Command",
    "Commanding Officer, Submarine Squadron Example",
    "Commander, Patrol and Reconnaissance Wing Example",
    "Commanding Officer, Naval Hospital Example",
    "Commanding Officer, Fleet Readiness Center Example",
    "Commander, Naval Supply Systems Command",
    "Commanding Officer, Navy Operational Support Center Example",
    "Commander, Naval Facilities Engineering Systems Command",
    "Commanding Officer, Defense Logistics Agency Distribution Example",
    "Commander, Space and Naval Warfare Systems Center Pacific",
    "Commanding Officer, Naval Research Laboratory",
    "Commander, Naval Meteorology and Oceanography Command",
    "Commanding Officer, Naval Criminal Investigative Service Field Office Example",
]

for i, frm in enumerate(valid_froms, 1):
    write(f"burnin_h16_neg_{i:02d}_valid_from.json", {
        "doc_type": "DT_STD_LTR",
        "from": frm,
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in neg {i:02d} — valid From",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in negative control — valid From line present ({i})."
    })

# ------------------------------------------------------------------
# 2. Standard letters missing from (15) — FAIL with ROUTE-011 in errors
# ------------------------------------------------------------------
for i in range(1, 16):
    extra = {}
    if i == 6:
        extra["via"] = ["(1) Chief of Naval Operations"]
    elif i == 7:
        extra["copy_to"] = ["Information Warfare Commander"]
    elif i == 8:
        extra["distribution"] = ["Distribution One"]
    elif i == 9:
        extra["via"] = ["(1) Via One", "(2) Via Two"]
        extra["copy_to"] = ["Copy One"]
    elif i == 10:
        extra["to"] = ["Commanding Officer, 12345"]  # also triggers ROUTE-010 advisory
    elif i == 11:
        extra["subject"] = "VERY LONG SUBJECT LINE " * 5
    elif i == 12:
        extra["body"] = "1. First paragraph.\n2. Second paragraph.\n3. Third paragraph."
    elif i == 13:
        extra["date"] = "08 June 2026"
    elif i == 14:
        extra["classification"] = "UNCLASSIFIED"
    elif i == 15:
        extra["via"] = ["(1) Via"]
        extra["copy_to"] = ["Copy"]
        extra["distribution"] = ["Dist"]
        extra["encl"] = ["Enclosure (1)"]

    payload = {
        "doc_type": "DT_STD_LTR",
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in pos {i:02d} — missing From",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in positive control — missing From line ({i})."
    }
    payload.update(extra)
    write(f"burnin_h16_pos_{i:02d}_missing_from.json", payload)

# ------------------------------------------------------------------
# 3. Standard letters with null/empty/whitespace from (15) — FAIL
# ------------------------------------------------------------------
bad_froms = [
    ("01", None, "null from"),
    ("02", "", "empty string from"),
    ("03", "   ", "spaces from"),
    ("04", "\t", "tab from"),
    ("05", "\n", "newline from"),
    ("06", " \t\n \t", "mixed whitespace from"),
    ("07", "  \n\t  ", "dense whitespace from"),
    ("08", "\u2003", "em space from"),
    ("09", "\u00A0", "non-breaking space from"),
    ("10", "\u2000\u2001\u2002", "various spaces from"),
    ("11", "  \t\n  ", "tab-newline-space from"),
    ("12", "\r\n", "CRLF from"),
    ("13", " \r \n \t ", "all whitespace chars from"),
    ("14", "\u200B", "zero-width space from"),
    ("15", "\uFEFF", "BOM from"),
]

for suffix, frm, desc in bad_froms:
    write(f"burnin_h16_pos_{suffix}_bad_from.json", {
        "doc_type": "DT_STD_LTR",
        "from": frm,
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in pos {suffix} — {desc}",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in positive control — {desc} ({suffix})."
    })

# ------------------------------------------------------------------
# 4. Non-standard documents that must not trigger (15) — PASS
# ------------------------------------------------------------------
non_std = [
    ("01", "DT_MEMO_FROM_TO_PLAIN", "memo without from"),
    ("02", "DT_MEMO_FROM_TO_MEMORANDUM", "memo2 without from"),
    ("03", "DT_MFR", "MFR without from"),
    ("04", "endorsement", "endorsement without from"),
    ("05", "joint_letter", "joint letter without from"),
    ("06", "multiple_address_letter", "multiple address without from"),
    ("07", "DT_STD_LTR", "missing doc_type", True),
    ("08", "memo", "memo string without from"),
    ("09", "DT_MEMO_FROM_TO_PLAIN", "memo with from present", False, "Commanding Officer, Example"),
    ("10", "endorsement", "endorsement with from present", False, "Commanding Officer, Example"),
    ("11", "DT_MFR", "MFR with empty from", False, ""),
    ("12", "joint_letter", "joint letter with whitespace from", False, "   "),
    ("13", "DT_MEMO_FROM_TO_PLAIN", "memo with via no from", False, None, ["(1) Via"]),
    ("14", "DT_STD_LTR", None, True, None, [], ["Copy"]),  # missing doc_type key
    ("15", "DT_STD_LTR", "unknown doc_type variant", True),  # doc_type="DT_STD_LTR" but missing key entirely? No, use explicit missing
]

# Rebuild non_std cleanly:
for i in range(1, 16):
    if i == 1:
        dt, desc, miss = "DT_MEMO_FROM_TO_PLAIN", "memo without from", False
        frm = None
    elif i == 2:
        dt, desc, miss = "DT_MEMO_FROM_TO_MEMORANDUM", "memo2 without from", False
        frm = None
    elif i == 3:
        dt, desc, miss = "DT_MFR", "MFR without from", False
        frm = None
    elif i == 4:
        dt, desc, miss = "endorsement", "endorsement without from", False
        frm = None
    elif i == 5:
        dt, desc, miss = "joint_letter", "joint letter without from", False
        frm = None
    elif i == 6:
        dt, desc, miss = "multiple_address_letter", "multiple address without from", False
        frm = None
    elif i == 7:
        dt, desc, miss = None, "missing doc_type key entirely", True
        frm = None
    elif i == 8:
        dt, desc, miss = "memo", "memo string doc_type without from", False
        frm = None
    elif i == 9:
        dt, desc, miss = "DT_MEMO_FROM_TO_PLAIN", "memo with from present", False
        frm = "Commanding Officer, Example"
    elif i == 10:
        dt, desc, miss = "endorsement", "endorsement with from present", False
        frm = "Commanding Officer, Example"
    elif i == 11:
        dt, desc, miss = "DT_MFR", "MFR with empty from", False
        frm = ""
    elif i == 12:
        dt, desc, miss = "joint_letter", "joint letter with whitespace from", False
        frm = "   "
    elif i == 13:
        dt, desc, miss = "DT_MEMO_FROM_TO_PLAIN", "memo with via no from", False
        frm = None
    elif i == 14:
        dt, desc, miss = None, "no doc_type key at all", True
        frm = None
    elif i == 15:
        dt, desc, miss = "DT_MEMO_FROM_TO_PLAIN", "memo with distribution no from", False
        frm = None

    payload = {
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in non-std {i:02d} — {desc}",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in non-standard control — {desc} ({i})."
    }
    if not miss:
        payload["doc_type"] = dt
    if frm is not None:
        payload["from"] = frm
    if i == 13:
        payload["via"] = ["(1) Via One"]
    if i == 14:
        payload["copy_to"] = ["Copy Recipient"]
    if i == 15:
        payload["distribution"] = ["Distribution One"]

    write(f"burnin_h16_nonstd_{i:02d}.json", payload)

# ------------------------------------------------------------------
# 5. Window-envelope letters with window_envelope=true (10) — PASS
# ------------------------------------------------------------------
we_vals = [
    ("01", True, "no from, bool true"),
    ("02", "yes", "no from, string yes"),
    ("03", 1, "no from, int 1"),
    ("04", "true", "no from, string true"),
    ("05", True, "with from, bool true"),
    ("06", "yes", "with from, string yes"),
    ("07", 1, "with from, int 1"),
    ("08", "True", "no from, string True"),
    ("09", "1", "no from, string 1"),
    ("10", True, "null from, bool true"),
]

for suffix, val, desc in we_vals:
    payload = {
        "doc_type": "DT_STD_LTR",
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in WE {suffix} — {desc}",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in window-envelope control — {desc}.",
        "window_envelope": val,
    }
    if "with from" in desc:
        payload["from"] = "Commanding Officer, Example"
    if "null from" in desc:
        payload["from"] = None
    write(f"burnin_h16_we_{suffix}.json", payload)

# ------------------------------------------------------------------
# 6. Window-envelope-like letters WITHOUT window_envelope field (10) — FAIL
# ------------------------------------------------------------------
for i in range(1, 11):
    payload = {
        "doc_type": "DT_STD_LTR",
        "to": ["Commanding Officer, Recipient Activity"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": f"H.16 burn-in WE-like {i:02d} — no window_envelope tag",
        "date": "2026-06-08",
        "body": f"Synthetic burn-in window-envelope-like — missing From, no window_envelope tag ({i}). Operator/data-quality risk."
    }
    if i == 5:
        payload["to"] = ["Commanding Officer, 12345"]
    if i == 6:
        payload["via"] = ["(1) Chief of Naval Operations"]
    if i == 7:
        payload["copy_to"] = ["Information Warfare Commander"]
    if i == 8:
        payload["distribution"] = ["Distribution One"]
    if i == 9:
        payload["body"] = "1. Paragraph one.\n2. Paragraph two.\n3. Paragraph three."
    if i == 10:
        payload["subject"] = "WE-LIKE COMPLEX " * 3
    write(f"burnin_h16_welike_{i:02d}_no_tag.json", payload)

# ------------------------------------------------------------------
# 7. Realistic Navy/Marine Corps substitutes (5) — mixed
# ------------------------------------------------------------------
realistic = [
    ("01", {
        "doc_type": "DT_STD_LTR",
        "from": "Commanding Officer, USS NIMITZ (CVN 68)",
        "to": ["Chief of Naval Operations (N00)"],
        "via": ["(1) Commander, U.S. Pacific Fleet", "(2) Commander, Naval Air Forces"],
        "copy_to": ["Director, Naval Intelligence"],
        "distribution": [],
        "subject": "H.16 realistic 01 — operational report",
        "date": "2026-06-08",
        "body": "1. Submit operational report for Period 1-7 June 2026.\n2. All systems nominal."
    }),
    ("02", {
        "doc_type": "DT_STD_LTR",
        "from": "Commanding Officer, 1st Marine Division",
        "to": ["Commandant of the Marine Corps"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": "H.16 realistic 02 — personnel status",
        "date": "2026-06-08",
        "body": "1. Personnel status report as of 0800Z 08 June 2026.\n2. Strength: 95 percent."
    }),
    ("03", {
        "doc_type": "DT_STD_LTR",
        "to": ["Commander, Naval Sea Systems Command"],
        "via": ["(1) Commander, Navy Regional Maintenance Center"],
        "copy_to": ["Technical Director"],
        "distribution": ["Fleet Maintenance Officer"],
        "subject": "H.16 realistic 03 — missing From (should fail)",
        "date": "2026-06-08",
        "body": "1. Request maintenance support for Main Propulsion Diesel Engine."
    }),
    ("04", {
        "doc_type": "DT_STD_LTR",
        "from": "",
        "to": ["Commanding Officer, Naval Air Station Fallon"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": "H.16 realistic 04 — empty From (should fail)",
        "date": "2026-06-08",
        "body": "1. Request flight training schedule coordination."
    }),
    ("05", {
        "doc_type": "DT_MEMO_FROM_TO_PLAIN",
        "to": ["All Hands"],
        "via": [], "copy_to": [], "distribution": [],
        "subject": "H.16 realistic 05 — memo no From (should pass)",
        "date": "2026-06-08",
        "body": "1. Routine administrative notice. No action required."
    }),
]

for suffix, payload in realistic:
    write(f"burnin_h16_realistic_{suffix}.json", payload)

print(f"Generated {len(list(DIR.glob('*.json')))} fixtures in {DIR}")
