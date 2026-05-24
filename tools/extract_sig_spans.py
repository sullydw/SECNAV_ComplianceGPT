#!/usr/bin/env python
import fitz
from pathlib import Path

# Use absolute path based on CWD
here = Path.cwd()
pdf_path = here / "output" / "audit_c7_joint_letter.pdf"
print(f"Opening PDF: {pdf_path}")

doc = fitz.open(pdf_path)
page = doc[0]
text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

all_spans = [
    {
        "page": i + 1,
        "text": s["text"],
        "x0": s["x0"],
        "y0": s["y0"]
    }
    for i, block in enumerate(text_dict.get("blocks", []))
    for l in block.get("lines", [])
    for s in l.get("spans", [])
    if s.get("text", "").strip()
]

doc.close()

print("\n=== SIGNATURE SPANS ===")
for s in all_spans:
    if "JANICKI" in s["text"] or "PIDGEON" in s["text"] or "Acting" in s["text"] or "Deputy Commandant" in s["text"]:
        print(f"  {s['text']!r}: x0={s['x0']:.1f}, y0={s['y0']:.1f}")

# Show all spans for reference
print("\n=== ALL RELEVANT SPANS (sorted by y0) ===")
sorted_spans = sorted(all_spans, key=lambda s: (s.get("y0", 0), s.get("x0", 0)))
for s in sorted_spans:
    if "JANICKI" in s["text"] or "PIDGEON" in s["text"] or "Acting" in s["text"] or "Deputy Commandant" in s["text"] or "Copy to" in s["text"]:
        print(f"  {s['text']!r}: x0={s['x0']:.1f}, y0={s['y0']:.1f}")
