#!/usr/bin/env python
"""
Baseline-to-Baseline Vertical Spacing Audit
Measures exact baseline-to-baseline gaps between document sections.
"""

import json
import os
import sys

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from letter_model_v6 import normalize_payload
from body_v6_validate import validate_body
from letterhead_v6_resolve import resolve_letterhead
from body_v6_parse import detect_marker_level


BOUNDARY_SPACINGS = {
    ("LETTERHEAD", "SSIC_DATE"): 1,
    ("SSIC_DATE", "HEADER"): 1,
    ("HEADER", "BODY"): 1,
    ("BODY", "SIGNATURE"): 4,
    ("SIGNATURE", "COPY_TO"): 1,
    ("COPY_TO", "PAGE_END"): 0,
    ("CONTINUATION_HEADER", "BODY"): 1,
}

def get_boundary_spacing(from_block, to_block, leading):
    key = (from_block.upper(), to_block.upper())
    spacing_lines = BOUNDARY_SPACINGS.get(key, 1)
    return spacing_lines * leading


def measure_baseline_to_baseline(c, normalized, page_height, top_margin_pt, left_margin_pt, page_width, right_margin_pt=72.0):
    """
    Render document and measure baseline-to-baseline gaps.
    Returns dict of measurements.
    """
    leading = 14.4  # 12pt font * 1.2
    signature_gap = 4 * leading  # 57.6 pt
    copy_gap = 1 * leading  # 14.4 pt
    bottom_margin_pt = 72.0
    
    measurements = {
        "date_to_from": None,
        "via_to_subj": None,
        "subj_to_body": None,
        "para_to_subpara": None,
        "signature_to_distribution": None,
        "distribution_to_copy_to": None,
    }
    
    # Track baselines
    date_baseline_y = None
    from_baseline_y = None
    via_last_baseline_y = None
    subj_first_baseline_y = None
    subj_last_baseline_y = None
    body_first_baseline_y = None
    para1_last_baseline_y = None
    subpara_a_baseline_y = None
    signature_last_baseline_y = None
    distribution_label_baseline_y = None
    distribution_last_entry_baseline_y = None
    copy_to_label_baseline_y = None
    
    y = page_height - top_margin_pt
    
    # === LETTERHEAD ===
    unit_identity = normalized.get("unit_identity", {})
    letterhead_result = resolve_letterhead(normalized)  # Pass full normalized payload, not just family string
    letterhead_lines = letterhead_result.get("lines", [])
    lh_lines = letterhead_lines  # Use resolved lines directly
    
    for i, lh_line in enumerate(lh_lines):
        font_name = "Times-Bold" if i == 0 else "Times-Roman"
        font_size = 10 if i == 0 else 8
        c.setFont(font_name, font_size)
        line_width = c.stringWidth(lh_line, font_name, font_size)
        x = (page_width - line_width) / 2
        c.drawString(x, y, lh_line)
        y -= font_size * 1.2
    
    # LETTERHEAD -> SSIC_DATE: 1 line
    y -= get_boundary_spacing("LETTERHEAD", "SSIC_DATE", leading)
    
    # === SSIC/DATE BLOCK ===
    date_formatted = normalized.get("date", "")
    if len(date_formatted.split()) == 3 and date_formatted.split()[0].isdigit():
        date_formatted = f"{date_formatted.split()[0]} {date_formatted.split()[1]} {str(int(date_formatted.split()[2]) % 100).zfill(2)}"
    
    ssic = normalized.get("ssic", "")
    originator = normalized.get("originator_code", "")
    
    sender_symbol_lines = [str(ssic), originator, date_formatted]
    longest_width = max(c.stringWidth(line, "Times-Roman", 12) for line in sender_symbol_lines)
    right_edge_x = page_width - right_margin_pt
    block_left_x = right_edge_x - longest_width
    
    c.setFont("Times-Roman", 12)
    for line in sender_symbol_lines:
        c.drawString(block_left_x, y, line)
        if line == date_formatted:
            date_baseline_y = y
        y -= leading
    
    # SSIC_DATE -> HEADER: 1 line
    y -= get_boundary_spacing("SSIC_DATE", "HEADER", leading)
    
    # === HEADER BLOCK ===
    # From line
    from_line = f"From: {normalized.get('from', '')}"
    c.drawString(left_margin_pt, y, from_line)
    from_baseline_y = y
    y -= leading
    
    # To line (if not distribution_only mode)
    distribution_mode = normalized.get("distribution_mode", "distribution_only")
    if distribution_mode != "distribution_only" and normalized.get("to"):
        to_line = f"To: {normalized.get('to', '')}"
        c.drawString(left_margin_pt, y, to_line)
        y -= leading
    
    # Via lines
    via_lines = normalized.get("via", [])
    for via_line in via_lines:
        c.drawString(left_margin_pt, y, via_line)
        via_last_baseline_y = y
        y -= leading
    
    # Subj line(s)
    subj = normalized.get("subj", "")
    subj_label_x = left_margin_pt
    subj_text_x = left_margin_pt + 43
    max_width = page_width - right_margin_pt - subj_text_x
    
    c.drawString(subj_label_x, y, "Subj:")
    subj_first_baseline_y = y
    y -= leading
    
    # Wrap subject text
    subj_lines = []
    remaining = subj
    while remaining:
        chunk = ""
        for word in remaining.split():
            test = f"{chunk} {word}".strip()
            if c.stringWidth(test, "Times-Roman", 12) <= max_width:
                chunk = test
            else:
                break
        if chunk:
            subj_lines.append(chunk)
            remaining = remaining[len(chunk):].strip()
        else:
            break
    
    for subj_line in subj_lines:
        c.drawString(subj_text_x, y, subj_line)
        subj_last_baseline_y = y  # Track last subj line baseline
        y -= leading
    
    # Ref lines
    ref_lines = normalized.get("ref", [])
    for ref_line in ref_lines:
        c.drawString(left_margin_pt, y, ref_line)
        y -= leading
    
    # Encl lines
    encl_lines = normalized.get("encl", [])
    for encl_line in encl_lines:
        c.drawString(left_margin_pt, y, encl_line)
        y -= leading
    
    # HEADER -> BODY: 1 line
    y -= get_boundary_spacing("HEADER", "BODY", leading)
    
    # === BODY BLOCK ===
    body_lines = normalized.get("body", [])
    marker_offset = {1: 0, 2: 24, 3: 48, 4: 78}
    
    prev_level = 1
    para1_last_baseline_y = None
    
    for i, line in enumerate(body_lines):
        level, marker, text = detect_marker_level(line)
        if level is None:
            level = 1
            marker = ""
            text = line
        
        marker_x = left_margin_pt + marker_offset.get(level, 0)
        
        if marker:
            marker_with_spaces = marker + "  "
            text_x = marker_x + c.stringWidth(marker_with_spaces, "Times-Roman", 12)
        else:
            text_x = marker_x
        
        if i == 0:
            body_first_baseline_y = y
        
        # Draw wrapped text
        remaining_text = text
        first_line = True
        while remaining_text:
            chunk = ""
            for word in remaining_text.split():
                test = f"{chunk} {word}".strip()
                test_x = text_x if first_line else left_margin_pt
                if c.stringWidth(test, "Times-Roman", 12) <= (page_width - right_margin_pt - test_x):
                    chunk = test
                else:
                    break
            
            if chunk:
                draw_x = text_x if first_line else left_margin_pt
                c.drawString(draw_x, y, chunk)
                if level == 1 and i == 0:
                    para1_last_baseline_y = y
                elif level == 2 and marker == "a.":
                    subpara_a_baseline_y = y
                y -= leading
                remaining_text = remaining_text[len(chunk):].strip()
                first_line = False
            else:
                break
        
        # Blank line after paragraph (not after subparagraph within same parent)
        if level == 1 or (i < len(body_lines) - 1 and detect_marker_level(body_lines[i + 1])[0] == 1):
            y -= leading
    
    # === SIGNATURE BLOCK ===
    # BODY -> SIGNATURE: 4 lines (signature_gap)
    y -= signature_gap
    
    signature = normalized.get("signature", {})
    signature_x = page_width / 2
    
    if isinstance(signature, dict):
        name = signature.get("name", "")
        role = signature.get("role", "")
        
        signature_lines = [name] if name else []
        if role == "by_direction":
            signature_lines.append("By direction")
        
        for sig_line in signature_lines:
            c.drawString(signature_x, y, sig_line)
            signature_last_baseline_y = y
            y -= leading
    
    # Gap after signature (1 leading unit before Distribution/Copy to)
    y -= leading
    
    # === DISTRIBUTION ===
    if normalized.get("distribution"):
        dist_label = normalized.get("distribution_label", "Distribution:")
        c.drawString(left_margin_pt, y, dist_label)
        distribution_label_baseline_y = y
        y -= leading
        
        dist_layout = normalized.get("distribution_layout", "single_column")
        entries = normalized.get("distribution", [])
        
        if dist_layout == "single_column":
            for entry in entries:
                c.drawString(left_margin_pt, y, entry)
                distribution_last_entry_baseline_y = y
                y -= leading
        elif dist_layout == "columns":
            num_rows = (len(entries) + 1) // 2
            col2_x = left_margin_pt + (page_width - right_margin_pt - left_margin_pt) / 2
            for row in range(num_rows):
                left_idx = row * 2
                right_idx = row * 2 + 1
                if left_idx < len(entries):
                    c.drawString(left_margin_pt, y, entries[left_idx])
                    distribution_last_entry_baseline_y = y
                if right_idx < len(entries):
                    c.drawString(col2_x, y, entries[right_idx])
                    distribution_last_entry_baseline_y = y
                y -= leading
        
        # Gap after distribution (1 leading unit before Copy to)
        y -= leading
    
    # === COPY TO ===
    if normalized.get("copy_to"):
        copy_to_label = normalized.get("copy_to_label", "Copy to:")
        c.drawString(left_margin_pt, y, copy_to_label)
        copy_to_label_baseline_y = y
        y -= leading
        
        copy_to_layout = normalized.get("copy_to_layout", "single_column")
        entries = normalized.get("copy_to", [])
        
        if copy_to_layout == "single_column":
            for entry in entries:
                c.drawString(left_margin_pt, y, entry)
                y -= leading
    
    # === RECORD MEASUREMENTS ===
    if date_baseline_y is not None and from_baseline_y is not None:
        measurements["date_to_from"] = {
            "last_line": f"Date: {date_formatted}",
            "y_prior": date_baseline_y,
            "first_line": from_line,
            "y_next": from_baseline_y,
            "gap_pt": date_baseline_y - from_baseline_y,
            "gap_leading": round((date_baseline_y - from_baseline_y) / leading, 2)
        }
    
    if via_last_baseline_y is not None and subj_first_baseline_y is not None:
        measurements["via_to_subj"] = {
            "last_line": via_lines[-1] if via_lines else "N/A",
            "y_prior": via_last_baseline_y,
            "first_line": "Subj:",
            "y_next": subj_first_baseline_y,
            "gap_pt": via_last_baseline_y - subj_first_baseline_y,
            "gap_leading": round((via_last_baseline_y - subj_first_baseline_y) / leading, 2)
        }
    
    if subj_last_baseline_y is not None and body_first_baseline_y is not None:
        measurements["subj_to_body"] = {
            "last_line": f"Subj: ...{subj_lines[-1]}" if len(subj_lines) > 1 else f"Subj: {subj[:50]}..." if len(subj) > 50 else f"Subj: {subj}",
            "y_prior": subj_last_baseline_y,
            "first_line": body_lines[0] if body_lines else "N/A",
            "y_next": body_first_baseline_y,
            "gap_pt": subj_last_baseline_y - body_first_baseline_y,
            "gap_leading": round((subj_last_baseline_y - body_first_baseline_y) / leading, 2)
        }
    
    if para1_last_baseline_y is not None and subpara_a_baseline_y is not None:
        measurements["para_to_subpara"] = {
            "last_line": body_lines[0],
            "y_prior": para1_last_baseline_y,
            "first_line": body_lines[1] if len(body_lines) > 1 else "N/A",
            "y_next": subpara_a_baseline_y,
            "gap_pt": para1_last_baseline_y - subpara_a_baseline_y,
            "gap_leading": round((para1_last_baseline_y - subpara_a_baseline_y) / leading, 2)
        }
    
    if signature_last_baseline_y is not None and distribution_label_baseline_y is not None:
        measurements["signature_to_distribution"] = {
            "last_line": signature_lines[-1] if signature_lines else "N/A",
            "y_prior": signature_last_baseline_y,
            "first_line": "Distribution:",
            "y_next": distribution_label_baseline_y,
            "gap_pt": signature_last_baseline_y - distribution_label_baseline_y,
            "gap_leading": round((signature_last_baseline_y - distribution_label_baseline_y) / leading, 2)
        }
    
    if distribution_last_entry_baseline_y is not None and copy_to_label_baseline_y is not None:
        measurements["distribution_to_copy_to"] = {
            "last_line": entries[-1] if entries else "N/A",
            "y_prior": distribution_last_entry_baseline_y,
            "first_line": "Copy to:",
            "y_next": copy_to_label_baseline_y,
            "gap_pt": distribution_last_entry_baseline_y - copy_to_label_baseline_y,
            "gap_leading": round((distribution_last_entry_baseline_y - copy_to_label_baseline_y) / leading, 2)
        }
    
    return measurements


def run_audit():
    """Run audit on v6_sample_letter.json and report measurements."""
    sample_path = os.path.join(os.path.dirname(__file__), "..", "examples", "v6_sample_letter.json")
    
    with open(sample_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    normalized = normalize_payload(raw)
    
    c = canvas.Canvas("output/audit_baseline_spacing.pdf", pagesize=LETTER)
    page_width, page_height = LETTER
    
    measurements = measure_baseline_to_baseline(
        c, normalized, page_height, 
        top_margin_pt=72.0, 
        left_margin_pt=72.0, 
        page_width=page_width,
        right_margin_pt=72.0
    )
    
    c.showPage()
    c.save()
    
    return measurements


if __name__ == "__main__":
    measurements = run_audit()
    
    print("=" * 80)
    print("BASELINE-TO-BASELINE VERTICAL SPACING AUDIT")
    print("=" * 80)
    print()
    
    for boundary, data in measurements.items():
        print(f"Boundary: {boundary.upper().replace('_', ' -> ')}")
        if data:
            print(f"  Last line of prior block: {data['last_line']}")
            print(f"  Y of prior baseline: {data['y_prior']:.1f} pt")
            print(f"  First line of next block: {data['first_line']}")
            print(f"  Y of next baseline: {data['y_next']:.1f} pt")
            print(f"  Gap: {data['gap_pt']:.1f} pt")
            print(f"  Gap in leading units: {data['gap_leading']} (expected: ~1.0)")
        else:
            print("  MEASUREMENT NOT AVAILABLE")
        print()
    
    print("=" * 80)
