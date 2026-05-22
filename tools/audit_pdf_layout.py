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


def check_label_content_alignment_groups(spans, groups, passed, failed, warnings_list):
    """Check x-coordinate of text content after labels (e.g., From text, To text, Subj text)."""
    for group in groups:
        name = group.get("name", "unnamed_group")
        labels = group.get("labels", [])
        tolerance = group.get("tolerance_pt", 3)
        y_tol = 1.5  # same-line tolerance in points

        if not labels:
            continue

        values = []
        unreliable = []

        for label in labels:
            label_span = find_first_span(spans, label)
            if label_span is None:
                warnings_list.append(f"label_content_group '{name}': missing '{label}'")
                continue

            page = label_span.get("page", 1)
            y0 = label_span.get("y0", 0)

            # Collect all spans on the same line (same page, same y within y_tol)
            same_line = [
                s for s in spans
                if s.get("page", 1) == page and abs(s.get("y0", 0) - y0) <= y_tol
            ]
            same_line.sort(key=lambda s: s.get("x0", 0))

            # Locate the label span in the sorted line
            label_idx = None
            for i, s in enumerate(same_line):
                if label.lower() in s.get("text", "").lower():
                    label_idx = i
                    break

            if label_idx is not None and label_idx + 1 < len(same_line):
                content_span = same_line[label_idx + 1]
                values.append((label, content_span.get("x0", 0)))
            else:
                unreliable.append(label)

        if unreliable:
            for lbl in unreliable:
                warnings_list.append(
                    f"label_content_group '{name}': '{lbl}' content_x could not be reliably extracted (single-span line or ambiguous); check skipped"
                )

        if len(values) < 2:
            continue

        first_val = values[0][1]
        all_within = True
        for label, val in values:
            if abs(val - first_val) > tolerance:
                all_within = False
                break

        vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
        if all_within:
            passed.append(f"label_content_group '{name}': aligned within {tolerance}pt ({vals_str})")
        else:
            warnings_list.append(f"label_content_group '{name}': probable misalignment ({vals_str}) -- verify visually")


def check_vertical_spacing_rules(spans, rules, passed, failed, warnings_list):
    """Check vertical spacing (y-delta) between labeled elements."""
    for rule in rules:
        name = rule.get("name", "unnamed_rule")
        from_text = rule.get("from_text", "")
        to_text = rule.get("to_text", "")
        expected = rule.get("expected_delta_pt", 0)
        tolerance = rule.get("tolerance_pt", 2.5)

        if not from_text or not to_text:
            continue

        from_span = find_first_span(spans, from_text)
        to_span = find_first_span(spans, to_text)

        if from_span is None:
            failed.append(f"vertical_spacing '{name}': missing '{from_text}'")
            continue
        if to_span is None:
            failed.append(f"vertical_spacing '{name}': missing '{to_text}'")
            continue

        actual = abs(to_span.get("y0", 0) - from_span.get("y0", 0))
        diff = abs(actual - expected)

        if diff <= tolerance:
            passed.append(f"vertical_spacing '{name}': delta={actual:.1f}pt (expected={expected}pt, tolerance=±{tolerance}pt)")
        else:
            warnings_list.append(
                f"vertical_spacing '{name}': delta={actual:.1f}pt vs expected={expected}pt (outside ±{tolerance}pt) -- verify visually"
            )


def check_alignment_groups(spans, alignment_groups, passed, failed):
    """Check x-coordinate alignment across groups of label x positions."""
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

    # Check label content alignment groups
    label_content_groups = profile.get("label_content_alignment_groups", [])
    if label_content_groups:
        check_label_content_alignment_groups(spans, label_content_groups, passed, failed, warnings)

    # Check vertical spacing rules
    vertical_spacing_rules = profile.get("vertical_spacing_rules", [])
    if vertical_spacing_rules:
        check_vertical_spacing_rules(spans, vertical_spacing_rules, passed, failed, warnings)

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
