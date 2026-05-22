#!/usr/bin/env python
# C7 Layout Audit Prototype

import argparse
import json
import sys
from pathlib import Path


def extract_text_spans(pdf_path: str) -> list[dict]:
    """Extract text spans from PDF."""
    import fitz
    doc = fitz.open(pdf_path)
    spans = []
    for page_num, page in enumerate(doc, start=1):
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        bbox = span.get("bbox", [0, 0, 0, 0])
                        spans.append({"page": page_num, "text": text, "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]})
    doc.close()
    return spans


def find_positions(spans, label):
    """Find y positions for label."""
    return [s["y0"] for s in spans if label.lower() in s["text"].lower()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()

    profile_path = Path(args.profile)
    with open(profile_path) as f:
        profile = json.load(f)

    from pprint import pprint
    print("=" * 70)
    print(f"PROFILE: {profile_path}")
    print(f"PDF:     {args.pdf}")
    print("-" * 70)

    spans = extract_text_spans(args.pdf)
    print(f"Extracted {len(spans)} text spans")

    required = profile.get("required_text", [])
    optional = profile.get("optional_text", [])

    # Check required labels
    passed, failed, warnings = [], [], []
    labels = {"from:", "to:", "subj:", "via:", "ref:", "encl:"}
    
    for label in required:
        positions = find_positions(spans, label)
        if positions:
            passed.append(f"{label}: found at y={positions[0]}")
        else:
            failed.append(f"{label}: not found")

    for label in optional:
        positions = find_positions(spans, label)
        if positions:
            passed.append(f"{label}: found at y={positions[0]}")
        else:
            warnings.append(f"{label}: not present (optional)")

    print(f"\nRESULT: {'PASS' if not failed else 'FAIL'}")
    print(f"  profile: {profile_path}")
    print(f"  pdf:     {args.pdf}")
    print(f"  passed:  {len(passed)}")
    print(f"  failed:  {len(failed)}")
    print(f"  warnings: {len(warnings)}")

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
