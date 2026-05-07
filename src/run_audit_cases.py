#!/usr/bin/env python
"""
Audit Case Runner
Run all audit JSON files in examples/ and generate PDFs for each.
"""

import json
import os
import glob
import sys

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# Import modules from v6 pipeline
from letter_model_v6 import normalize_payload
from body_v6_validate import validate_body
from letterhead_v6_resolve import resolve_letterhead
from body_v6_parse import detect_marker_level


# =============================================================================
# Import rendering helpers from pdf_v6_render.py by executing it in a controlled way
# Since we can't modify pdf_v6_render.py, we import its functions by adding to path
# =============================================================================

# Add src to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import rendering functions - they're defined at module level in pdf_v6_render.py
# We need to import them without running main()
import importlib.util
spec = importlib.util.spec_from_file_location("pdf_v6_render", os.path.join(script_dir, "pdf_v6_render.py"))
pdf_v6_render = importlib.util.module_from_spec(spec)

# Load the module but prevent main() from executing by checking __name__
# Since pdf_v6_render.py uses if __name__ == "__main__": main(), importing won't run main()
spec.loader.exec_module(pdf_v6_render)

# Now we have access to all the rendering functions
wrap_line = pdf_v6_render.wrap_line
wrap_paragraph = pdf_v6_render.wrap_paragraph
draw_wrapped_text = pdf_v6_render.draw_wrapped_text
draw_page_number = pdf_v6_render.draw_page_number
calculate_signature_space = pdf_v6_render.calculate_signature_space
draw_signature_block = pdf_v6_render.draw_signature_block
draw_body_block = pdf_v6_render.draw_body_block
draw_header_block = pdf_v6_render.draw_header_block
get_boundary_spacing = pdf_v6_render.get_boundary_spacing
format_sender_symbol_date = pdf_v6_render.format_sender_symbol_date


def render_audit_pdf(payload, output_path):
    """Render a single audit payload to PDF using the v6 renderer pipeline."""
    
    # Normalize
    normalized = normalize_payload(payload)
    
    # Validate body
    body_errors = validate_body(payload)
    if body_errors:
        return False, f"BODY VALIDATION FAILED: {body_errors}"
    
    # Resolve letterhead
    letterhead = resolve_letterhead(payload)
    letterhead_lines = letterhead.get("lines", [])
    
    # Layout values
    left_margin_pt = 72.0
    right_margin_pt = 72.0
    top_margin_pt = 45.0
    bottom_margin_pt = 72.0
    
    # Font-size-aware typography
    body_font_size = 12
    leading = body_font_size * 1.2
    signature_gap = body_font_size * 4.0
    copy_gap = body_font_size * 2.0
    
    # Load H-series rules
    base_dir = os.path.dirname(script_dir)
    h_series_path = os.path.join(base_dir, "H-series.json")
    h_rules = {}
    if os.path.exists(h_series_path):
        with open(h_series_path, "r", encoding="utf-8") as f:
            h_data = json.load(f)
        h_rules["first_line_font"] = "Times-Bold"
        h_rules["first_line_size"] = h_data.get("H-001", {}).get("font_size_pt", 10)
        h_rules["subsequent_font"] = "Times-Roman"
        h_rules["subsequent_size"] = h_data.get("H-002", {}).get("font_size_pt", 8)
    else:
        h_rules["first_line_font"] = "Times-Bold"
        h_rules["first_line_size"] = 10
        h_rules["subsequent_font"] = "Times-Roman"
        h_rules["subsequent_size"] = 8
    
    # Page dimensions
    page_width, page_height = LETTER
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=LETTER)
    y = page_height - top_margin_pt
    
    # Render letterhead
    if letterhead_lines:
        for i, lh_line in enumerate(letterhead_lines):
            if i == 0:
                c.setFont(h_rules["first_line_font"], h_rules["first_line_size"])
                lh_leading = h_rules["first_line_size"] * 1.2
            else:
                c.setFont(h_rules["subsequent_font"], h_rules["subsequent_size"])
                lh_leading = h_rules["subsequent_size"] * 1.2
            
            text_width = c.stringWidth(lh_line, h_rules["first_line_font"] if i == 0 else h_rules["subsequent_font"], 
                                       h_rules["first_line_size"] if i == 0 else h_rules["subsequent_size"])
            x_centered = (page_width - text_width) / 2
            c.drawString(x_centered, y, lh_line)
            y -= lh_leading
        
        if h_rules.get("spacing_after") == "one_blank_line":
            y -= get_boundary_spacing("LETTERHEAD", "SSIC_DATE", leading)
    
    # SSIC/date sender-symbol block
    ssic_val = str(normalized.get('ssic', ''))
    originator_code = normalized.get('originator_code')
    serial = normalized.get('serial')
    raw_date_text = normalized.get('date', '')
    formatted_date = format_sender_symbol_date(raw_date_text)
    
    sender_symbol_lines = []
    if ssic_val:
        sender_symbol_lines.append(ssic_val)
    if serial:
        sender_symbol_lines.append("Ser " + str(serial))
    elif originator_code:
        sender_symbol_lines.append(str(originator_code))
    if formatted_date:
        sender_symbol_lines.append(formatted_date)
    
    if sender_symbol_lines:
        c.setFont("Times-Roman", body_font_size)
        right_edge_x = page_width - right_margin_pt
        longest_line_width = max(c.stringWidth(line, "Times-Roman", body_font_size) for line in sender_symbol_lines)
        block_left_x = right_edge_x - longest_line_width
        
        for line in sender_symbol_lines:
            c.drawString(block_left_x, y, line)
            y -= leading
    
    y -= get_boundary_spacing("SSIC_DATE", "HEADER", leading)
    
    # Header block
    label_x = left_margin_pt
    text_x = left_margin_pt + 43
    y = draw_header_block(c, label_x, text_x, y, leading, normalized, page_width, right_margin_pt)
    
    y -= get_boundary_spacing("HEADER", "BODY", leading)
    
    # Body block
    y, page_count, body_lines_on_last_page = draw_body_block(
        c, left_margin_pt, y, leading, body_font_size, normalized, page_height, top_margin_pt, bottom_margin_pt,
        signature_gap, copy_gap, reserve_signature_space=True
    )
    
    # Signature block
    required_signature_space = calculate_signature_space(normalized, leading, signature_gap, copy_gap)
    
    if y < bottom_margin_pt + required_signature_space:
        draw_page_number(c, page_width, page_count, bottom_margin_pt)
        c.showPage()
        page_count += 1
        y = page_height - top_margin_pt
        c.setFont("Times-Roman", 12)
        c.drawString(left_margin_pt, y, "Subj:")
        header_text_x = left_margin_pt + 43
        subj_max_width = (page_width - 72.0) - header_text_x
        y = draw_wrapped_text(c, header_text_x, y, normalized.get('subj', ''), 12, subj_max_width, leading)
    
    y = draw_signature_block(c, normalized, page_width, left_margin_pt, y, leading, signature_gap, copy_gap, bottom_margin_pt, right_margin_pt)
    
    # Page number
    draw_page_number(c, page_width, page_count, bottom_margin_pt)
    
    c.save()
    
    return True, f"Pages: {page_count}"


def main():
    base_dir = os.path.dirname(script_dir)
    examples_dir = os.path.join(base_dir, "examples")
    output_dir = os.path.join(base_dir, "output")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all audit JSON files
    audit_files = glob.glob(os.path.join(examples_dir, "audit_*.json"))
    
    if not audit_files:
        print("No audit files found matching examples/audit_*.json")
        return
    
    print(f"Found {len(audit_files)} audit file(s)")
    print("=" * 60)
    
    results = []
    for audit_file in sorted(audit_files):
        filename = os.path.basename(audit_file)
        filename_no_ext = os.path.splitext(filename)[0]
        output_pdf = os.path.join(output_dir, f"{filename_no_ext}.pdf")
        
        print(f"\nProcessing: {filename}")
        
        try:
            # Load JSON
            with open(audit_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            # Render
            success, message = render_audit_pdf(payload, output_pdf)
            
            if success and os.path.exists(output_pdf):
                print(f"  PASS: {message}")
                print(f"  Output: {output_pdf}")
                results.append((filename, "PASS", message))
            else:
                print(f"  FAIL: {message}")
                results.append((filename, "FAIL", message))
        
        except Exception as e:
            print(f"  FAIL: {str(e)}")
            results.append((filename, "FAIL", str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for filename, status, message in results:
        print(f"{filename}: {status}")
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()
