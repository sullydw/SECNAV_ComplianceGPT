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
    """Find spans matching label (case-insensitive contains)."""
    return [s for s in spans if label.lower() in s["text"].lower()]


def find_first_span(spans, label):
    """Return first span matching label, or None."""
    for s in spans:
        if label.lower() in s["text"].lower():
            return s
    return None


def check_alignment_groups(spans, alignment_groups, passed, failed):
    """Check x-coordinate alignment across groups of labels."""
    for group in alignment_groups:
        name = group.get("name", "unnamed_group")
        texts = group.get("texts", [])
        x_field = group.get("x_field", "x0")
        tolerance = group.get("tolerance_pt", 3)

        if not texts:
            continue

        values = []
        for text in texts:
            span = find_first_span(spans, text)
            if span is None:
                failed.append(f"alignment_group '{name}': missing '{text}'")
            else:
                values.append((text, span.get(x_field, None)))

        if len(values) < 2:
            continue

        # Compare all to first found value
        first_val = values[0][1]
        all_within = True
        for text, val in values:
            if abs(val - first_val) > tolerance:
                all_within = False
                break

        if all_within:
            vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
            passed.append(f"alignment_group '{name}': aligned within {tolerance}pt ({vals_str})")
        else:
            vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
            failed.append(f"alignment_group '{name}': misaligned ({vals_str})")


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

    for label in required:
        positions = find_positions(spans, label)
        if positions:
            passed.append(f"{label}: found at y={positions[0]['y0']:.1f}")
        else:
            failed.append(f"{label}: not found")

    for label in optional:
        positions = find_positions(spans, label)
        if positions:
            passed.append(f"{label}: found at y={positions[0]['y0']:.1f}")
        else:
            warnings.append(f"{label}: not present (optional)")

    # Check alignment groups
    alignment_groups = profile.get("alignment_groups", [])
    if alignment_groups:
        check_alignment_groups(spans, alignment_groups, passed, failed)

    print(f"\nRESULT: {'PASS' if not failed else 'FAIL'}")
    print(f"  profile: {profile_path}")
    print(f"  pdf:     {args.pdf}")
    print(f"  passed:  {len(passed)}")
    print(f"  failed:  {len(failed)}")
    print(f"  warnings: {len(warnings)}")
    if passed:
        print(f"\n  passed details:")
        for p in passed:
            print(f"    + {p}")
    if failed:
        print(f"\n  failed details:")
        for f in failed:
            print(f"    - {f}")
    if warnings:
        print(f"\n  warnings:")
        for w in warnings:
            print(f"    ! {w}")

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
