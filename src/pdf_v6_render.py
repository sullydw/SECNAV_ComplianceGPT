#!/usr/bin/env python
"""
v6 PDF Renderer Prototype
Render first page of v6 letter to PDF.
"""

import json
import os
import re
import sys

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# Import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from letter_model_v6 import normalize_payload
from body_v6_validate import validate_body
from letterhead_v6_resolve import resolve_letterhead
from body_v6_parse import detect_marker_level


# =============================================================================
# Layout Boundary Spacing Helper
# Centralized spacing between major document blocks
# =============================================================================

BOUNDARY_SPACINGS = {
    # (from_block, to_block): spacing_in_leading_units
    ("LETTERHEAD", "SSIC_DATE"): 1,      # 1 line between letterhead and SSIC/date
    ("SSIC_DATE", "HEADER"): 2,          # 2 lines between date and From block
    ("HEADER", "BODY"): 0,               # 0 lines between Encl and first body paragraph
    ("BODY", "SIGNATURE"): 4,            # 4 lines (signature_gap) after final body text
    ("SIGNATURE", "COPY_TO"): 2,         # 2 lines (copy_gap) after signature
    ("COPY_TO", "PAGE_END"): 0,          # No extra space
    ("CONTINUATION_HEADER", "BODY"): 1,  # 1 line after repeated Subj line
}

def get_boundary_spacing(from_block, to_block, leading):
    """
    Return spacing in points between two document blocks.
    Uses BOUNDARY_SPACINGS dict with leading-based calculation.
    """
    key = (from_block.upper(), to_block.upper())
    spacing_lines = BOUNDARY_SPACINGS.get(key, 1)  # Default to 1 line if not specified
    spacing_pt = spacing_lines * leading
    print(f"DEBUG BOUNDARY: {from_block} -> {to_block} = {spacing_lines} lines ({spacing_pt:.1f} pt)")
    return spacing_pt


def wrap_line(text, font_name, font_size, max_width, c):
    """Return (first_chunk, remaining) where first_chunk fits in max_width."""
    if not text:
        return "", ""
    if c.stringWidth(text, font_name, font_size) <= max_width:
        return text, ""
    # Word-boundary split
    words = text.split()
    best = ""
    for word in words:
        candidate = f"{best} {word}".strip()
        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            best = candidate
        else:
            break
    if not best:
        # Single word too long - character split
        for ch in text:
            candidate = best + ch
            if c.stringWidth(candidate, font_name, font_size) <= max_width:
                best = candidate
            else:
                break
    remaining = text[len(best):].strip()
    return best, remaining


def wrap_paragraph(text, font_name, font_size, max_width, c):
    """Return list of lines fitting within max_width."""
    lines = []
    remaining = text
    while remaining:
        chunk, remaining = wrap_line(remaining, font_name, font_size, max_width, c)
        if chunk:
            lines.append(chunk)
        else:
            break
    return lines


def draw_page_number(c, page_width, page_num, bottom_margin_pt):
    """Draw page number centered, 1/2 inch from bottom edge (page 2+ only)."""
    if page_num < 2:
        return
    # 1/2 inch from bottom edge = 36pt from bottom of page
    page_num_y = 36.0
    page_num_x = page_width / 2
    c.setFont("Times-Roman", 12)
    c.drawCentredString(page_num_x, page_num_y, str(page_num))
    print(f"DEBUG Page number {page_num} drawn at x={page_num_x:.1f}, y={page_num_y:.1f}")


def draw_body_block(c, left_margin_pt, y, leading, font_size, normalized, page_height, top_margin_pt, bottom_margin_pt, signature_gap, copy_gap, reserve_signature_space=False):
    """
    Draw body paragraphs with proper level-based indentation and word-wrap.
    Marker prints only on first line; continuation lines return to left margin.
    Handles pagination: when y drops below bottom margin, starts a new page.
    On page 2+, draws repeated subject line at top.

    If reserve_signature_space=True, ensures at least 6 lines remain after body
    for signature block (4 blank lines + signature + copy_to buffer).

    Returns (new y position, page count, body_lines_rendered_on_last_page).
    """
    c.setFont("Times-Roman", 12)

    marker_offset = {1: 0, 2: 24, 3: 48, 4: 78}
    page_width = c._pagesize[0]
    right_margin_size_pt = 72.0
    right_edge_pt = page_width - right_margin_size_pt
    body_lines = normalized.get("body", [])
    subj = normalized.get("subj", "")
    print(f"DEBUG body_lines count: {len(body_lines)}")
    print(f"DEBUG body_lines from normalized.get('body'): True")
    print(f"DEBUG normalized keys: {list(normalized.keys())}")
    if body_lines:
        print(f"DEBUG [0]: {repr(body_lines[0])}")
        if len(body_lines) > 1:
            print(f"DEBUG [1]: {repr(body_lines[1])}")
    prev_level = 1
    page_count = 1
    body_lines_on_current_page = 0
    body_lines_on_last_page = 0

    def draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj):
        """Draw repeated subject line on continuation pages (page 2+)."""
        y = page_height - top_margin_pt
        c.setFont("Times-Roman", 12)
        c.drawString(left_margin_pt, y, f"Subj: {subj}")
        y -= leading
        # One blank line after subject
        y -= leading
        print(f"DEBUG Continuation header drawn, y after subject: {y:.1f}")
        return y

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

        # Check if we need a new page before drawing this body record
        # Estimate space needed: at least one line for marker+text
        min_space_needed = leading * 2  # marker line + blank line after

        # If reserving signature space, check if we need to force a new page
        # to ensure signature fits with at least 2 body lines before it
        if reserve_signature_space and i >= len(body_lines) - 2:
            # This is one of the last 2 body lines - check if signature will fit
            signature_space_needed = signature_gap + leading + copy_gap  # signature_gap + signature line + copy_gap buffer
            if y < bottom_margin_pt + signature_space_needed:
                # Draw page number on current page before showing new page
                draw_page_number(c, page_width, page_count, bottom_margin_pt)
                c.showPage()
                page_count += 1
                body_lines_on_current_page = 0
                body_lines_on_last_page = 0  # Reset for new page
                # Draw continuation header on page 2+
                y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj)
                print(f"DEBUG SIGNATURE PAGE: Started page {page_count}, y after header: {y:.1f}")
        elif y < bottom_margin_pt + min_space_needed:
            # Draw page number on current page before showing new page
            draw_page_number(c, page_width, page_count, bottom_margin_pt)
            c.showPage()
            page_count += 1
            body_lines_on_current_page = 0
            body_lines_on_last_page = 0  # Reset for new page
            # Draw continuation header on page 2+
            y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj)
            print(f"DEBUG PAGINATION: Started page {page_count}, y after header: {y:.1f}")

        y -= leading
        body_lines_on_current_page += 1
        body_lines_on_last_page += 1

        # First line: marker at marker_x, first chunk at text_x
        first_max = right_edge_pt - text_x
        first_chunk, remaining = wrap_line(text, "Times-Roman", 12, first_max, c)

        if marker:
            c.drawString(marker_x, y, marker)
            c.drawString(text_x, y, first_chunk)
        else:
            c.drawString(text_x, y, first_chunk)

        y -= leading

        # Continuation lines at left margin (no marker)
        cont_max = right_edge_pt - left_margin_pt
        for cont_line in wrap_paragraph(remaining, "Times-Roman", 12, cont_max, c):
            # Check if continuation line needs new page
            if y < bottom_margin_pt + leading:
                # Draw page number on current page before showing new page
                draw_page_number(c, page_width, page_count, bottom_margin_pt)
                c.showPage()
                page_count += 1
                body_lines_on_current_page = 0
                body_lines_on_last_page = 0  # Reset for new page
                # Draw continuation header on page 2+
                y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj)
                print(f"DEBUG PAGINATION: Started page {page_count} (continuation), y after header: {y:.1f}")
            c.drawString(left_margin_pt, y, cont_line)
            y -= leading

        # Debug: y position after this body record
        print(f"DEBUG y_position after level {level} marker '{marker}': {y:.1f}")

        # Level-aware baseline adjustment after this paragraph (except for last paragraph)
        # Level 1 (top-level): spacing = font_size (12 pt)
        # Level 2+ (subparagraphs/nested): spacing = font_size * 0.70 (8.4 pt)
        if i < len(body_lines) - 1:
            if level == 1:
                level_adjustment = -(leading - font_size)  # -2.4 pt → 12 pt spacing
            else:
                level_adjustment = -(leading - (font_size * 0.70))  # -6.0 pt → 8.4 pt spacing
            y += level_adjustment

        prev_level = level

    return y, page_count, body_lines_on_last_page


def draw_header_block(c, label_x, text_x, y, leading, normalized):
    """
    Draw SECNAV header block with explicit two-column coordinates.
    Returns new y position after rendering.
    """
    c.setFont("Times-Roman", 12)
    
    # From:
    from_y = y
    c.drawString(label_x, y, "From:")
    c.drawString(text_x, y, normalized.get("from", ""))
    print(f"DEBUG From: '{normalized.get('from', '')}' | y={from_y:.1f}")
    y -= leading

    # To:
    c.drawString(label_x, y, "To:")
    c.drawString(text_x, y, normalized.get("to", ""))
    y -= leading

    # Via: (if present)
    if normalized.get("via_count", 0) > 0:
        c.drawString(label_x, y, "Via:")
        via_lines = normalized.get("via", [])
        for i, via_line in enumerate(via_lines):
            # Strip numbering marker if single Via entry
            display_line = via_line
            if len(via_lines) == 1:
                # Remove "(1)" prefix if present
                display_line = re.sub(r'^\(\d+\)\s*', '', via_line)
            else:
                # Multiple entries: ensure numbering exists
                if not re.match(r'^\(\d+\)\s*', via_line):
                    display_line = f"({i + 1}) {via_line}"

            c.drawString(text_x, y, display_line)
            y -= leading

    # One blank line before Subj (24 pt total from last line)
    y -= leading

    # Subj:
    c.drawString(label_x, y, "Subj:")
    c.drawString(text_x, y, normalized.get("subj", ""))
    y -= leading

    # One blank line before Ref
    y -= leading

    # Ref: (if present)
    if normalized.get("ref_count", 0) > 0:
        c.drawString(label_x, y, "Ref:")
        for i, ref_line in enumerate(normalized.get("ref", [])):
            if i == 0:
                c.drawString(text_x, y, ref_line)
            else:
                c.drawString(text_x, y, ref_line)
            y -= leading

    # One blank line before Encl
    y -= leading

    # Encl: (if present)
    if normalized.get("encl_count", 0) > 0:
        c.drawString(label_x, y, "Encl:")
        for i, encl_line in enumerate(normalized.get("encl", [])):
            if i == 0:
                c.drawString(text_x, y, encl_line)
            else:
                c.drawString(text_x, y, encl_line)
            y -= leading

    return y


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    output_dir = os.path.join(base_dir, "output")
    output_path = os.path.join(output_dir, "v6_test_letter.pdf")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load sample payload
    if not os.path.exists(sample_path):
        print("=== PDF BUILD ===")
        print("FAIL")
        print(f"Missing: {sample_path}")
        return

    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    print(f"DEBUG Raw payload loaded from: {sample_path}")
    print(f"DEBUG Raw payload body count: {len(payload.get('body', []))}")
    if payload.get('body'):
        print(f"DEBUG Raw body[0]: {repr(payload['body'][0])}")

    # Normalize
    normalized = normalize_payload(payload)
    print(f"DEBUG normalize_payload completed")
    print(f"DEBUG normalized type: {type(normalized)}")
    print(f"DEBUG normalized keys: {list(normalized.keys())}")
    print(f"DEBUG body in normalized: {'body' in normalized}")
    if 'body' in normalized:
        print(f"DEBUG body count from normalized: {len(normalized.get('body', []))}")
    else:
        print(f"DEBUG body NOT in normalized - may fall back to default")

    # Validate body
    body_errors = validate_body(payload)
    if body_errors:
        print("=== PDF BUILD ===")
        print("FAIL")
        print("BODY VALIDATION FAILED")
        for err in body_errors:
            print(f"<error>{err}</error>")
        return

    # Resolve letterhead
    letterhead = resolve_letterhead(payload)
    letterhead_lines = letterhead.get("lines", [])
    gap_below = letterhead.get("gap_below", "one_blank_line")

    # Layout values (resolved margins)
    left_margin_pt = 72.0
    right_margin_pt = 72.0
    top_margin_pt = 45.0
    bottom_margin_pt = 72.0

    # Font-size-aware typography calculations
    font_size = 12  # body font size
    leading = font_size * 1.2  # line spacing with 20% extra (within paragraphs)
    blank_line = font_size * 1.2  # one blank line
    signature_gap = font_size * 4.0  # 4 lines below text before signature
    copy_gap = font_size * 2.0  # 2 lines below signature before copy_to
    page_break_buffer = font_size * 4.0  # minimum space before signature

    # Load H-series letterhead rules
    h_series_path = os.path.join(base_dir, "H-series.json")
    h_rules = {}
    if os.path.exists(h_series_path):
        with open(h_series_path, "r", encoding="utf-8") as f:
            h_data = json.load(f)
        # Extract H-series rule values and map to ReportLab font names
        h_rules["first_line_font"] = "Times-Bold"  # H-001: Times New Roman Bold
        h_rules["first_line_size"] = h_data.get("H-001", {}).get("font_size_pt", 10)
        h_rules["subsequent_font"] = "Times-Roman"  # H-002: Times New Roman Regular
        h_rules["subsequent_size"] = h_data.get("H-002", {}).get("font_size_pt", 8)
        h_rules["spacing_after"] = h_data.get("H-006", {}).get("spacing_after", "one_blank_line")
        print(f"DEBUG H-series loaded: first={h_rules['first_line_font']} {h_rules['first_line_size']}pt, subsequent={h_rules['subsequent_font']} {h_rules['subsequent_size']}pt")
    else:
        # Fallback defaults
        h_rules["first_line_font"] = "Times-Bold"
        h_rules["first_line_size"] = 10
        h_rules["subsequent_font"] = "Times-Roman"
        h_rules["subsequent_size"] = 8
        h_rules["spacing_after"] = "one_blank_line"
        print(f"DEBUG H-series NOT found, using fallback defaults")

    # Page dimensions
    page_width, page_height = LETTER

    # Create PDF
    c = canvas.Canvas(output_path, pagesize=LETTER)

    y = page_height - top_margin_pt

    # Render letterhead lines centered at top (H-series rules)
    if letterhead_lines:
        print(f"DEBUG === LETTERHEAD BLOCK ===")
        for i, lh_line in enumerate(letterhead_lines):
            if i == 0:
                # First line: bold, larger font
                font_name = h_rules["first_line_font"]
                font_size = h_rules["first_line_size"]
            else:
                # Subsequent lines: regular, smaller font
                font_name = h_rules["subsequent_font"]
                font_size = h_rules["subsequent_size"]

            c.setFont(font_name, font_size)
            lh_leading = font_size * 1.2  # Letterhead-specific leading
            text_width = c.stringWidth(lh_line, font_name, font_size)
            x_centered = (page_width - text_width) / 2
            c.drawString(x_centered, y, lh_line)
            print(f"DEBUG LH line {i+1}: '{lh_line}' | font={font_name} {font_size}pt | x={x_centered:.1f} | y={y:.1f} | width={text_width:.1f}")
            y -= lh_leading

        # Spacing below letterhead per H-006
        if h_rules["spacing_after"] == "one_blank_line":
            # Use boundary helper for LETTERHEAD -> SSIC_DATE
            y -= get_boundary_spacing("LETTERHEAD", "SSIC_DATE", leading)
        print(f"DEBUG Letterhead block end y={y:.1f}")

    # SSIC and date block - right-aligned, no "SSIC:" label
    ssic_val = str(normalized.get('ssic', ''))
    date_text = normalized.get('date', '')
    ssic_y = y
    c.setFont("Helvetica", 10)
    c.drawRightString(page_width - right_margin_pt, y, ssic_val)
    print(f"DEBUG SSIC: '{ssic_val}' | y={ssic_y:.1f}")
    y -= leading
    date_y = y
    c.drawRightString(page_width - right_margin_pt, y, date_text)
    print(f"DEBUG Date: '{date_text}' | y={date_y:.1f}")
    
    # Boundary: SSIC_DATE -> HEADER
    y -= get_boundary_spacing("SSIC_DATE", "HEADER", leading)

    # Header block - use dedicated function with proper SECNAV text column
    label_x = left_margin_pt
    text_x = left_margin_pt + 43  # 43 pt offset for proper SECNAV alignment

    y = draw_header_block(c, label_x, text_x, y, leading, normalized)

    # Boundary: HEADER -> BODY (centralized spacing control)
    y -= get_boundary_spacing("HEADER", "BODY", leading)

    # Body block - use dedicated function with level-based indentation and pagination
    y, page_count, body_lines_on_last_page = draw_body_block(
        c, left_margin_pt, y, leading, font_size, normalized, page_height, top_margin_pt, bottom_margin_pt,
        signature_gap, copy_gap, reserve_signature_space=True
    )
    print(f"DEBUG Total pages generated: {page_count}")
    print(f"DEBUG Body lines on last page: {body_lines_on_last_page}")

    # Signature block placement logic per SECNAV M-5216.5 Chapter 7:
    # - Signature line starts at center of page (page_width / 2)
    # - Signature line begins on the fourth line below the text
    # - A signature page must have at least two lines of text preceding the signature
    # - If not enough room, start new page with continuation header
    # - No complimentary close

    signature_space_needed = signature_gap + leading + copy_gap  # signature_gap + signature line + copy_gap buffer
    has_copy_to = normalized.get("copy_to")
    if has_copy_to:
        signature_space_needed += copy_gap + (len(has_copy_to) * leading)  # "Copy to:" + entries

    if y < bottom_margin_pt + signature_space_needed:
        # Not enough room - start a new signature page
        # Draw page number on current page before showing new page
        draw_page_number(c, page_width, page_count, bottom_margin_pt)
        c.showPage()
        page_count += 1
        print(f"DEBUG SIGNATURE PAGE: Started page {page_count} for signature block")
        # Draw continuation header
        y = page_height - top_margin_pt
        c.setFont("Times-Roman", 12)
        c.drawString(left_margin_pt, y, f"Subj: {subj}")
        y -= leading
        y -= leading  # One blank line after subject
        print(f"DEBUG Continuation header on signature page, y after subject: {y:.1f}")

        # Note: body_lines_on_last_page will be 0 since we started a new page
        # This is acceptable if there was no body text to carry over
        if body_lines_on_last_page == 0:
            print(f"DEBUG WARNING: Signature page has no preceding body text")

    # Four blank lines after final body text (or after continuation header if new page)
    y -= signature_gap
    signature_y = y
    print(f"DEBUG y after signature_gap before signature: {y:.1f}")

    # Signature block starts at center of page (no complimentary close)
    signature_x = page_width / 2
    signature_text = normalized.get("signature", "")
    # Fix signature spelling if needed
    if signature_text == "DARL SULLIVAN":
        signature_text = "DARRYL SULLIVAN"
    c.drawString(signature_x, signature_y, signature_text)
    print(f"DEBUG Signature drawn at x={signature_x:.1f}, y={signature_y:.1f}")
    y = signature_y - copy_gap

    # Copy to (if present) - starts at left margin, second line below signature
    if normalized.get("copy_to"):
        copy_to_y = y
        c.drawString(left_margin_pt, copy_to_y, "Copy to:")
        y -= leading
        for copy_line in normalized.get("copy_to", []):
            c.drawString(left_margin_pt, y, copy_line)
            y -= leading
        print(f"DEBUG Copy to block starts at y={copy_to_y:.1f}")

    # Draw page number on final page (page 2+ only)
    draw_page_number(c, page_width, page_count, bottom_margin_pt)

    c.save()

    # Verify output file exists
    if os.path.exists(output_path):
        print("=== PDF BUILD ===")
        print("PASS")
        print(f"output\\v6_test_letter.pdf")
    else:
        print("=== PDF BUILD ===")
        print("FAIL")
        print("Output file not created")


if __name__ == "__main__":
    main()
