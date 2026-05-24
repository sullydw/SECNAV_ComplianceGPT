#!/usr/bin/env python
"""Extract signature spans from Joint Letter PDF using PyMuFit."""

import fitz
import json
import os

# Use absolute path from CWD
this_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(this_dir, '..', 'SECNAV_ComplianceGPT', 'output', 'audit_c7_joint_letter.pdf')

# Alternative: if running from SECNAV_ComplianceGPT root
pdf_path_alt = os.path.join(this_dir, 'SECNAV_ComplianceGPT', 'output', 'audit_c7_joint_letter.pdf')

# Check CWD
cwd = os.getcwd()
pdf_path = os.path.join(cwd, 'output', 'audit_c7_joint_letter.pdf')

if not os.path.exists(pdf_path):
    pdf_path = pdf_path_alt

if not os.path.exists(pdf_path):
    print(f"PDF not found at: {pdf_path}")
    print(f"Trying: {pdf_path_alt}")
    pdf_path = pdf_path_alt

print(f"Opening PDF: {pdf_path}")

doc = fitz.open(pdf_path)
page = doc[0]
text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

spans = []
for i, block in enumerate(text_dict.get("blocks", [])):
    for l in block.get("lines", []):
        for s in l.get("spans", []):
            text = s.get("text", "").strip()
            if text:
                bbox = s.get("bbox", [0, 0, 0, 0])
                spans.append({
                    "page": i + 1,
                    "text": text,
                    "x0": bbox[0],
                    "y0": bbox[1],
                    "x1": bbox[2],
                    "y1": bbox[3]
                })

doc.close()

# Filter signature-related spans
sig_spans = [s for s in spans if any(x in s["text"] for x in ["JANICKI", "PIDGEON", "Acting", "Deputy Commandant", "Copy to"])]
sig_spans.sort(key=lambda s: s["y0"])

print("\n=== SIGNATURE SPANS ===")
print(f"{'Span':<35}{'x':<6}{'y':<6}{'x1':<6}{'y1':<6}")
print("-" * 60)
for s in sig_spans:
    print(f"{s['text']!r:<35}{s['x0']:7.1f}{s['y0']:6.1f}{s['x1']:6.1f}{s['y1']:6.1f}")

# Find positions we need
positions = {}
for s in spans:
    text = s["text"]
    if text.startswith("JOINT LETTER"):
        positions["JOINT LETTER"] = s
    elif text == "From:":
        positions["From:"] = s
    elif text == "To:":
        positions["To:"] = s
    elif text.startswith("Subj:"):
        positions["Subj:"] = s
    elif "J. K. JANICKI" in text:
        positions["J. K. JANICKI"] = s
    elif "A. N. PIDGEON" in text:
        positions["A. N. PIDGEON"] = s
    elif "Acting" in text:
        positions["Acting"] = s
    elif "Deputy Commandant" in text:
        positions["Deputy Commandant"] = s
    elif text.startswith("Copy to"):
        positions["Copy to"] = s

print("\n=== MEASURED Y POSITIONS ===")
for name, pos in sorted(positions.items(), key=lambda x: x[1]["y0"]):
    print(f"- {name}: y={pos['y0']:.1f}")

print("\n=== MEASURED GAPS ===")
joil_y = positions.get("JOINT LETTER", {})["y0"]
from_y = positions.get("From:", {}).get("y0", 0)
to_y = positions.get("To:", {}).get("y0", 0)
subj_y = positions.get("Subj:", {}).get("y0", 0)
janicky_y = positions.get("J. K. JANICKI", {}).get("y0", 0)
pidgeon_y = positions.get("A. N. PIDGEON", {}).get("y0", 0)
acting_y = positions.get("Acting", {}).get("y0", 0)
deputy_y = positions.get("Deputy Commandant", {}).get("y0", 0)
copy_to_y = positions.get("Copy to", {}).get("y0", 0)

gaps = [
    ("JOINT LETTER to From:", from_y - joil_y),
    ("second From entry to To:", to_y - from_y),
    ("To to Subj:", subj_y - to_y),
    ("Subj to 1.:", janicky_y - subj_y),
    ("paragraph 4 to J. K. JANICKI:", janicky_y - pidgeon_y),
    ("Acting to Copy to:", copy_to_y - acting_y),
]

for name, gap in gaps:
    print(f"- {name}: {gap:.1f}pt")
