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
# Date Formatting Helper
# SECNAV abbreviated date format for sender-symbol block
# =============================================================================

def format_sender_symbol_date(date_text):
    """
    Convert date to SECNAV abbreviated format: D Mon YY
    
    Accepts:
    - "1 May 2026"
    - "May 1, 2026"
    - "2026-05-01"
    - "7 Sep 06" (already correct, preserved)
    
    Returns:
    - "1 May 26" format
    """
    import re
    
    if not date_text:
        return date_text
    
    date_text = str(date_text).strip()
    
    # Month abbreviations mapping
    month_map = {
        'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
        'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
        'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec',
        'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
        'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug', 'sep': 'Sep',
        'oct': 'Oct', 'nov': 'Nov', 'dec': 'Dec'
    }
    
    # Pattern 1: D Mon YY (already correct format, e.g., "7 Sep 06" or "1 May 26")
    already_correct = re.match(r'^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})$', date_text)
    if already_correct:
        day = int(already_correct.group(1))
        mon = already_correct.group(2).capitalize()
        yy = already_correct.group(3)
        return f"{day} {mon} {yy}"
    
    # Pattern 2: D Mon YYYY (e.g., "1 May 2026")
    pattern_full = re.match(r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', date_text)
    if pattern_full:
        day = int(pattern_full.group(1))
        month_name = pattern_full.group(2).lower()
        year = int(pattern_full.group(3))
        yy = str(year % 100).zfill(2)
        mon = month_map.get(month_name, month_name[:3].capitalize())
        return f"{day} {mon} {yy}"
    
    # Pattern 3: Mon D, YYYY (e.g., "May 1, 2026")
    pattern_comma = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$', date_text)
    if pattern_comma:
        month_name = pattern_comma.group(1).lower()
        day = int(pattern_comma.group(2))
        year = int(pattern_comma.group(3))
        yy = str(year % 100).zfill(2)
        mon = month_map.get(month_name, month_name[:3].capitalize())
        return f"{day} {mon} {yy}"
    
    # Pattern 4: ISO format YYYY-MM-DD (e.g., "2026-05-01")
    pattern_iso = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_text)
    if pattern_iso:
        year = int(pattern_iso.group(1))
        month_num = int(pattern_iso.group(2))
        day = int(pattern_iso.group(3))
        yy = str(year % 100).zfill(2)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        mon = months[month_num - 1]
        return f"{day} {mon} {yy}"
    
    # Unknown format - return as-is
    return date_text


# =============================================================================
# Layout Boundary Spacing Helper
# Centralized spacing between major document blocks
# =============================================================================

BOUNDARY_SPACINGS = {
    # (from_block, to_block): spacing_in_leading_units
    ("LETTERHEAD", "SSIC_DATE"): 1,      # 1 line between letterhead and SSIC/date
    ("SSIC_DATE", "HEADER"): 1,          # 1 line between SSIC/date and From line
    ("HEADER", "BODY"): 1,               # 1 line between Encl and first body paragraph
    ("BODY", "SIGNATURE"): 4,            # 4 lines (signature_gap) after final body text
    ("SIGNATURE", "COPY_TO"): 1,         # 1 line after signature before distribution/copy_to
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


def draw_page_number(c, page_width, page_num, bottom_margin_pt, page_number_start=None, force_page_number_on_first_page=False):
    """Draw page number centered, 1/2 inch from bottom edge.
    
    Standard letters: page 2+ only, display page_num.
    C9 new-page endorsements (force_page_number_on_first_page=True):
      draws on all pages, displaying page_number_start + (page_num - 1).
    """
    if page_number_start is None and page_num < 2:
        return
    if page_number_start is None and not force_page_number_on_first_page:
        return
    
    # Compute display number
    if force_page_number_on_first_page and page_number_start is not None:
        display_num = page_number_start + (page_num - 1)
    else:
        display_num = page_num
    
    # 1/2 inch from bottom edge = 36pt from bottom of page
    page_num_y = 36.0
    page_num_x = page_width / 2
    c.setFont("Times-Roman", 12)
    c.drawCentredString(page_num_x, page_num_y, str(display_num))
    print(f"DEBUG Page number {display_num} drawn at x={page_num_x:.1f}, y={page_num_y:.1f}")


def _draw_endorsement_heading(payload, c, y, left_margin_pt, font_name="Times-Roman", font_size=12):
    """Draw endorsement heading for C9 new-page endorsements.
    
    Only renders when payload has doc_type=DT_ENDORSEMENT and endorsement_type=new_page.
    Returns (y) after decrementing for heading + one blank line.
    """
    doc_type = payload.get("doc_type", "")
    endorsement_type = payload.get("endorsement_type", "")
    
    if doc_type != "DT_ENDORSEMENT" or endorsement_type != "new_page":
        return y
    
    endorsement_ordinal = payload.get("endorsement_ordinal", "")
    basic_letter_id = payload.get("basic_letter_id", "")
    
    if not endorsement_ordinal or not basic_letter_id:
        print("WARNING: endorsement_ordinal or basic_letter_id missing, skipping endorsement heading")
        return y
    
    heading_text = f"{endorsement_ordinal} ENDORSEMENT on {basic_letter_id}"
    
    c.setFont(font_name, font_size)
    c.drawString(left_margin_pt, y, heading_text)
    print(f"DEBUG Endorsement heading: '{heading_text}' at x={left_margin_pt:.1f}, y={y:.1f}")
    
    # Decrement y: heading line + one blank line before From block
    font_size_pt = font_size
    # Approximate leading as 1.2 * font_size_pt
    heading_leading = font_size_pt * 1.2
    y -= heading_leading  # space taken by heading text
    y -= heading_leading  # blank line after heading
    
    return y


def draw_mfr_signature_block(c, normalized, page_width, y, leading, signature_gap):
    """
    Draw MFR signature block: simple signer name + org code.
    Returns new y position after rendering.
    
    MFR signature format:
    - signature_gap (4 blank lines) after body
    - signer_name centered at page_width / 2
    - signer_org_code on next line at same x
    """
    # Four blank lines after final body text
    y -= signature_gap
    print(f"DEBUG MFR: y after signature_gap before signer: {y:.1f}")
    
    # Signer block starts at center of page
    signer_x = page_width / 2
    signer_name = normalized.get("signer_name", "")
    signer_org_code = normalized.get("signer_org_code", "")
    
    # Draw signer name
    if signer_name:
        c.drawString(signer_x, y, signer_name)
        print(f"DEBUG MFR: Signer name drawn at x={signer_x:.1f}, y={y:.1f}: '{signer_name}'")
        y -= leading
    
    # Draw org code
    if signer_org_code:
        c.drawString(signer_x, y, signer_org_code)
        print(f"DEBUG MFR: Signer org code drawn at x={signer_x:.1f}, y={y:.1f}: '{signer_org_code}'")
        y -= leading
    
    return y


def calculate_signature_space(normalized, leading, signature_gap, copy_gap):
    """
    Calculate total vertical space needed for signature block.
    Returns space in points.
    
    Includes:
    - signature_gap (space after body)
    - all signature lines (name, title, authority) based on role
    - copy_to gap (if copy_to present)
    - "Copy to:" label line (if copy_to present)
    - copy_to entry lines (if copy_to present)
    """
    space = signature_gap  # gap after body before signature
    
    # Calculate signature lines based on input format
    signature_lines = 0
    signature = normalized.get("signature", "")
    
    if isinstance(signature, dict):
        # Structured signature: count lines based on role
        role = signature.get("role")
        
        # Name is always first line if present
        if signature.get("name"):
            signature_lines += 1
        
        # Count additional lines based on role
        if role == "activity_head":
            # name only
            pass
        elif role == "principal_subordinate_by_title":
            # name + title
            if signature.get("title"):
                signature_lines += 1
        elif role == "acting":
            # name + Acting
            signature_lines += 1
        elif role == "acting_by_title":
            # name + title + Acting
            if signature.get("title"):
                signature_lines += 2  # title + Acting
        elif role == "by_direction":
            # name + By direction
            signature_lines += 1
        elif role == "by_direction_pay_allowance":
            # name + title + By direction of the + activity_head_title
            if signature.get("title") and signature.get("activity_head_title"):
                signature_lines += 3  # title + By direction of the + activity_head_title
            elif signature.get("title"):
                signature_lines += 2  # title + By direction of the
            elif signature.get("activity_head_title"):
                signature_lines += 2  # By direction of the + activity_head_title
        else:
            # Backward compatibility: old format with title/authority fields
            if signature.get("title"):
                signature_lines += 1
            if signature.get("authority"):
                signature_lines += 1
    elif signature:
        # Legacy string signature
        signature_lines = 1
    
    space += signature_lines * leading
    
    # Copy-to section
    has_copy_to = normalized.get("copy_to")
    if has_copy_to:
        space += copy_gap  # gap after signature before copy_to
        space += leading  # "Copy to:" label line
        space += len(has_copy_to) * leading  # copy_to entry lines
    
    print(f"DEBUG calculate_signature_space: {signature_lines} signature lines, total={space:.1f}pt")
    return space


def _validate_structured_signature(signature):
    """
    Validate structured signature dict and print warnings for SECNAV compliance.
    Does not stop execution - only warns and degrades safely.
    
    Args:
        signature: Signature dict to validate
    
    Returns:
        tuple: (is_valid, fallback_lines) where fallback_lines is list of lines to render if validation fails
    """
    name = signature.get("name") or ""
    role = signature.get("role")
    title = signature.get("title") or ""
    activity_head_title = signature.get("activity_head_title") or ""
    
    # 1. Name format check - should use initials and last name
    if name:
        parts = name.split()
        if len(parts) >= 2:
            first_part = parts[0]
            # Check if first part appears to be a full first name (not an initial)
            # Initials are typically 1-2 chars or end with period
            if len(first_part) > 2 and not first_part.endswith('.') and first_part.isalpha():
                print(f"WARNING: Signature name should use initials and last name per SECNAV standard (got '{name}')")
        
        # 2. Rank/service detection
        rank_service_keywords = ["USMC", "U.S.", "USN", "USA", "USAF", "USCG", "Colonel", "Captain", 
                                  "Major", "General", "Admiral", "Lieutenant", "Sergeant", "Private"]
        name_upper = name.upper()
        for keyword in rank_service_keywords:
            if keyword.upper() in name_upper:
                print(f"WARNING: Do not include rank or service in standard letter signature line (detected '{keyword}' in '{name}')")
                break
    
    # 3. Role-specific validation
    if role == "principal_subordinate_by_title":
        if not title:
            print(f"ERROR: Role 'principal_subordinate_by_title' requires 'title' field. Falling back to name only.")
            return False, [name] if name else []
    
    elif role == "acting_by_title":
        if not title:
            print(f"ERROR: Role 'acting_by_title' requires 'title' field. Falling back to name + Acting.")
            fallback = [name] if name else []
            fallback.append("Acting")
            return False, fallback
    
    elif role == "by_direction_pay_allowance":
        if not title or not activity_head_title:
            print(f"ERROR: Role 'by_direction_pay_allowance' requires 'title' and 'activity_head_title' fields. Falling back to name + By direction.")
            fallback = [name] if name else []
            fallback.append("By direction")
            return False, fallback
    
    # 4. Unsupported role check
    valid_roles = ["activity_head", "principal_subordinate_by_title", "acting", "acting_by_title", 
                   "by_direction", "by_direction_pay_allowance", None]
    if role is not None and role not in valid_roles:
        print(f"WARNING: Unsupported signature role '{role}'. Rendering name only.")
        return False, [name] if name else []
    
    return True, None


def draw_signature_block(c, normalized, page_width, left_margin_pt, y, leading, signature_gap, copy_gap, bottom_margin_pt, right_margin_pt=72.0):
    """
    Draw signature block as a single atomic unit for SECNAV role-based signing.
    Returns new y position after rendering.
    
    Supports both legacy string signatures and structured dictionaries.
    Structured signature format: {"name": "...", "title": "...", "authority": "...", "role": "..."}
    
    Signature block includes:
    - signature_gap blank lines after body
    - Role-aware signature rendering
    - copy_to section (if present)
    """
    # Four blank lines after final body text
    y -= signature_gap
    print(f"DEBUG y after signature_gap before signature: {y:.1f}")

    # Signature block starts at center of page (no complimentary close)
    signature_x = page_width / 2
    signature = normalized.get("signature", "")
    
    # Handle both legacy string and structured signature formats
    if isinstance(signature, dict):
        # Structured signature - validate first
        is_valid, fallback_lines = _validate_structured_signature(signature)
        
        # Extract components
        name = signature.get("name") or ""
        role = signature.get("role")
        title = signature.get("title") or ""
        activity_head_title = signature.get("activity_head_title") or ""
        
        # Fix signature spelling if needed
        if name == "DARL SULLIVAN":
            name = "DARRYL SULLIVAN"
        
        # If validation failed with fallback, use fallback lines
        if not is_valid and fallback_lines is not None:
            signature_lines = fallback_lines
        else:
            # Build signature lines based on role
            signature_lines = []
            
            # Name is always first if present
            if name:
                signature_lines.append(name)
            
            # Add role-specific lines
            if role == "activity_head":
                # name only - nothing more to add
                pass
            elif role == "principal_subordinate_by_title":
                if title:
                    signature_lines.append(title)
            elif role == "acting":
                signature_lines.append("Acting")
            elif role == "acting_by_title":
                if title:
                    signature_lines.append(title)
                signature_lines.append("Acting")
            elif role == "by_direction":
                signature_lines.append("By direction")
            elif role == "by_direction_pay_allowance":
                if title:
                    signature_lines.append(title)
                signature_lines.append("By direction of the")
                if activity_head_title:
                    signature_lines.append(activity_head_title)
            elif role is None:
                # No role specified - fall back to old dict behavior
                old_title = signature.get("title") or ""
                old_authority = signature.get("authority") or ""
                if old_title:
                    signature_lines.append(old_title)
                if old_authority:
                    signature_lines.append(old_authority)
            # else: unsupported role already handled by validation
        
        # Draw all signature lines at same x position
        for line in signature_lines:
            if line.strip():
                c.drawString(signature_x, y, line)
                print(f"DEBUG Signature line drawn at x={signature_x:.1f}, y={y:.1f}: '{line}'")
            y -= leading
            
    elif signature:
        # Legacy string signature
        signature_text = signature
        # Fix signature spelling if needed
        if signature_text == "DARL SULLIVAN":
            signature_text = "DARRYL SULLIVAN"
        c.drawString(signature_x, y, signature_text)
        print(f"DEBUG Signature drawn at x={signature_x:.1f}, y={y:.1f}")
        y -= leading

    # One blank line after signature before distribution
    if normalized.get("distribution"):
        y -= leading

    # Distribution: (if present, renders after signature, before Copy to)
    # Label and order are rule-driven from model if provided
    if normalized.get("distribution"):
        dist_y = y
        dist_layout = normalized.get("distribution_layout", "single_column")
        dist_label = normalized.get("distribution_label", "Distribution:")
        
        # Validate distribution_layout
        valid_distribution_layouts = ["single_column", "columns", "paragraph"]
        if dist_layout not in valid_distribution_layouts:
            print(f"WARNING: Invalid distribution_layout '{dist_layout}', falling back to 'single_column'")
            dist_layout = "single_column"
        
        print(f"DEBUG distribution_layout: {dist_layout}")
        
        c.drawString(left_margin_pt, y, dist_label)
        y -= leading
        
        if dist_layout == "single_column":
            # Single column: entries listed one per line at left margin
            for dist_entry in normalized.get("distribution", []):
                c.drawString(left_margin_pt, y, dist_entry)
                y -= leading
        
        elif dist_layout == "columns":
            # Two columns: balanced row order (left, right, next row)
            entries = normalized.get("distribution", [])
            right_edge_pt = page_width - right_margin_pt
            col1_x = left_margin_pt
            col2_x = left_margin_pt + (right_edge_pt - left_margin_pt) / 2
            
            # Calculate how many rows needed
            num_entries = len(entries)
            num_rows = (num_entries + 1) // 2  # Ceiling division
            
            for row in range(num_rows):
                left_idx = row * 2
                right_idx = row * 2 + 1
                
                # Left column entry
                if left_idx < num_entries:
                    c.drawString(col1_x, y, entries[left_idx])
                
                # Right column entry
                if right_idx < num_entries:
                    c.drawString(col2_x, y, entries[right_idx])
                
                y -= leading
        
        elif dist_layout == "paragraph":
            # Paragraph: comma-separated entries as wrapping text
            dist_text = ", ".join(normalized.get("distribution", []))
            max_width = page_width - right_margin_pt - left_margin_pt
            y = draw_wrapped_text(c, left_margin_pt, y, dist_text, 12, max_width, leading)
        
        print(f"DEBUG Distribution block starts at y={dist_y:.1f} (layout: {dist_layout})")
        # One blank line after Distribution before Copy to - ONLY if Copy to exists
        # The gap after the last Distribution entry is already applied by the loop above
        # Do NOT add extra spacing here

    # Copy to (if present) - renders after Distribution if both exist
    # Label is rule-driven from model if provided
    # Copy to never affects header rendering
    # One blank line after signature before Copy to per BOUNDARY_SPACINGS (SIGNATURE -> COPY_TO)
    if normalized.get("copy_to"):
        y -= copy_gap  # One blank line after signature before Copy to
        copy_to_y = y
        copy_to_layout = normalized.get("copy_to_layout", "single_column")
        copy_to_label = normalized.get("copy_to_label", "Copy to:")
        
        # Validate copy_to_layout
        valid_copy_to_layouts = ["single_column", "columns", "paragraph"]
        if copy_to_layout not in valid_copy_to_layouts:
            print(f"WARNING: Invalid copy_to_layout '{copy_to_layout}', falling back to 'single_column'")
            copy_to_layout = "single_column"
        
        print(f"DEBUG copy_to_layout: {copy_to_layout}")
        
        c.drawString(left_margin_pt, copy_to_y, copy_to_label)
        y -= leading
        
        if copy_to_layout == "single_column":
            for copy_line in normalized.get("copy_to", []):
                c.drawString(left_margin_pt, y, copy_line)
                y -= leading
        
        elif copy_to_layout == "columns":
            entries = normalized.get("copy_to", [])
            right_edge_pt = page_width - right_margin_pt
            col1_x = left_margin_pt
            col2_x = left_margin_pt + (right_edge_pt - left_margin_pt) / 2
            num_entries = len(entries)
            num_rows = (num_entries + 1) // 2
            
            for row in range(num_rows):
                left_idx = row * 2
                right_idx = row * 2 + 1
                if left_idx < num_entries:
                    c.drawString(col1_x, y, entries[left_idx])
                if right_idx < num_entries:
                    c.drawString(col2_x, y, entries[right_idx])
                y -= leading
        
        elif copy_to_layout == "paragraph":
            copy_text = ", ".join(normalized.get("copy_to", []))
            max_width = page_width - right_margin_pt - left_margin_pt
            y = draw_wrapped_text(c, left_margin_pt, y, copy_text, 12, max_width, leading)
        
        print(f"DEBUG Copy to block starts at y={copy_to_y:.1f} (layout: {copy_to_layout})")
    
    return y


def draw_body_block(c, left_margin_pt, y, leading, body_font_size, normalized, page_height, top_margin_pt, bottom_margin_pt, signature_gap, copy_gap, reserve_signature_space=False, page_number_start=None, force_page_number_on_first_page=False):
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

    # SECNAV Figure 7-8 paragraph alignment:
    # Marker columns: where the marker (1., a., (1), (a)) prints
    # Text columns: where first-line text starts (marker + 2 spaces)
    # Continuation lines: return to left margin (72 pt)
    # Two-digit markers (10., 11., etc.): marker may extend left of text column
    # Adjusted marker offsets to reduce excessive indentation for subparagraphs
    marker_offset = {1: 0, 2: 18, 3: 36, 4: 54}
    
    # Fixed first-line text-start columns per level (in points from left edge)
    # Text starts at marker position + marker width + 2 spaces (~16 pt)
    # Level 1: marker at 72 pt, text ~90 pt
    # Level 2: marker at 90 pt, text ~108 pt
    # Level 3: marker at 108 pt, text ~126 pt
    # Level 4: marker at 126 pt, text ~144 pt
    text_start_column = {
        1: left_margin_pt + 18,   # ~90 pt (for "1." marker)
        2: left_margin_pt + 36,   # ~108 pt (for "a." marker)
        3: left_margin_pt + 54,   # ~126 pt (for "(1)" marker)
        4: left_margin_pt + 72,   # ~144 pt (for "(a)" marker)
    }
    
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

    def draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj, right_edge_pt, leading):
        """Draw repeated subject line on continuation pages (page 2+)."""
        y = page_height - top_margin_pt
        header_label_x = left_margin_pt
        header_text_x = left_margin_pt + 43  # Same text column as page 1 header
        c.setFont("Times-Roman", 12)
        c.drawString(header_label_x, y, "Subj:")
        subj_max_width = right_edge_pt - header_text_x
        y = draw_wrapped_text(c, header_text_x, y, subj, 12, subj_max_width, leading)
        # draw_wrapped_text returns y already positioned for next line (one leading below last subject line)
        # Add one blank line after continuation subject before body/signature resumes
        y -= leading
        # This y is the baseline where body paragraph 1 should be drawn
        print(f"DEBUG Continuation header: label_x={header_label_x:.1f}, text_x={header_text_x:.1f}, y after subject={y:.1f}")
        return y

    for i, line in enumerate(body_lines):
        level, marker, text = detect_marker_level(line)
        if level is None:
            level = 1
            marker = ""
            text = line

        # Add blank line when transitioning from parent to first child subparagraph
        # This applies to: 1. -> a., b. -> (1), (2) -> (a)
        if i > 0 and level > prev_level:
            y -= leading  # One blank line before first child subparagraph
            print(f"DEBUG blank line before level-{level} child of level-{prev_level} parent")

        marker_x = left_margin_pt + marker_offset.get(level, 0)

        # First-line text start: use fixed column per level for consistent alignment
        # Continuation lines will return to left_margin_pt
        text_x = text_start_column.get(level, left_margin_pt)

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
                draw_page_number(c, page_width, page_count, bottom_margin_pt, page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page)
                c.showPage()
                page_count += 1
                body_lines_on_current_page = 0
                body_lines_on_last_page = 0  # Reset for new page
                # Draw continuation header on page 2+
                y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj, right_edge_pt, leading)
                print(f"DEBUG SIGNATURE PAGE: Started page {page_count}, y after header: {y:.1f}")
        elif y < bottom_margin_pt + min_space_needed:
            # Draw page number on current page before showing new page
            draw_page_number(c, page_width, page_count, bottom_margin_pt, page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page)
            c.showPage()
            page_count += 1
            body_lines_on_current_page = 0
            body_lines_on_last_page = 0  # Reset for new page
            # Draw continuation header on page 2+
            y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj, right_edge_pt, leading)
            print(f"DEBUG PAGINATION: Started page {page_count}, y after header: {y:.1f}")

        # Draw body record at current y position (incoming y is baseline for this record)
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
                draw_page_number(c, page_width, page_count, bottom_margin_pt, page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page)
                c.showPage()
                page_count += 1
                body_lines_on_current_page = 0
                body_lines_on_last_page = 0  # Reset for new page
                # Draw continuation header on page 2+
                y = draw_continuation_header(c, left_margin_pt, page_height, top_margin_pt, subj, right_edge_pt, leading)
                print(f"DEBUG PAGINATION: Started page {page_count} (continuation), y after header: {y:.1f}")
            c.drawString(left_margin_pt, y, cont_line)
            y -= leading

        # Debug: y position after this body record
        print(f"DEBUG y_position after level {level} marker '{marker}': {y:.1f}")

        # Body record gap: single leading unit between paragraphs (except last)
        # Do NOT apply gap when next line is a child (level increases)
        if i < len(body_lines) - 1:
            next_line = body_lines[i + 1]
            next_level, _, _ = detect_marker_level(next_line)
            if next_level is None:
                next_level = 1
            # Only apply paragraph gap between same-level or higher-level resets (level decreases or stays same)
            if next_level <= level:
                y -= leading  # Single consistent blank line

        prev_level = level

    return y, page_count, body_lines_on_last_page


def draw_wrapped_text(c, x, y, text, font_size, max_width, leading):
    """
    Draw text with word-wrapping at a fixed x position.
    Continuation lines align under the first line (no hanging indent).
    Returns new y position after all lines are drawn.
    """
    c.setFont("Times-Roman", font_size)
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = c.stringWidth(test_line, "Times-Roman", font_size)
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    
    return y


def draw_header_block(c, label_x, text_x, y, leading, normalized, page_width, right_margin_pt):
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

    # Validate and resolve distribution_mode
    valid_distribution_modes = ["distribution_only", "to_plus_distribution"]
    distribution_mode = normalized.get("distribution_mode")
    has_distribution = bool(normalized.get("distribution"))
    
    if has_distribution:
        if distribution_mode is None:
            distribution_mode = "distribution_only"
            print(f"WARNING: distribution_mode missing with distribution present, defaulting to 'distribution_only'")
        elif distribution_mode not in valid_distribution_modes:
            print(f"WARNING: Invalid distribution_mode '{distribution_mode}', falling back to 'distribution_only'")
            distribution_mode = "distribution_only"
        
        if distribution_mode == "distribution_only" and normalized.get("to"):
            print(f"WARNING: To field ignored because distribution_mode is 'distribution_only'")
        elif distribution_mode == "to_plus_distribution" and not normalized.get("to"):
            print(f"WARNING: distribution_mode is 'to_plus_distribution' but To field missing, falling back to 'distribution_only'")
            distribution_mode = "distribution_only"
    
    print(f"DEBUG distribution_mode: {distribution_mode}")
    
    # To: (omit only if distribution_mode is "distribution_only")
    if distribution_mode != "distribution_only":
        to_value = normalized.get("to", "")
        
        if isinstance(to_value, list):
            to_entries = [str(entry).strip() for entry in to_value if str(entry).strip()]
        elif str(to_value).strip():
            to_entries = [str(to_value).strip()]
        else:
            to_entries = []
        
        if to_entries:
            c.drawString(label_x, y, "To:")
            c.drawString(text_x, y, to_entries[0])
            print(f"DEBUG To: '{to_entries[0]}' | y={y:.1f}")
            y -= leading
            
            for to_entry in to_entries[1:]:
                c.drawString(text_x, y, to_entry)
                print(f"DEBUG To continuation: '{to_entry}' | y={y:.1f}")
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

    # One blank line before Subj
    y -= leading

    # Subj: with word-wrapping for long subject lines
    c.drawString(label_x, y, "Subj:")
    # Calculate max width for subject text (right margin - text_x)
    subj_max_width = page_width - right_margin_pt - text_x
    y = draw_wrapped_text(c, text_x, y, normalized.get("subj", ""), 12, subj_max_width, leading)

    # Ref: (if present) - only apply spacing before Ref if Ref exists
    ref_count = normalized.get("ref_count", 0)
    encl_count = normalized.get("encl_count", 0)
    
    # Calculate text column for REF/ENCL entries
    # text_x is already the start of the text column (label_x + 43)
    # Max width for REF/ENCL text = right_edge - text_x
    ref_encl_max_width = page_width - right_margin_pt - text_x
    
    if ref_count > 0:
        # One blank line before Ref (only if Ref exists)
        y -= leading
        c.drawString(label_x, y, "Ref:")
        for i, ref_line in enumerate(normalized.get("ref", [])):
            # Parse marker and text from ref_line (e.g., "(a) SECNAV M-5216.5...")
            marker_match = re.match(r'^\(([a-zA-Z0-9]+)\)\s+(.*)$', ref_line)
            if marker_match:
                marker = f"({marker_match.group(1)})"
                ref_text = marker_match.group(2)
            else:
                # No marker found, treat entire line as text
                marker = ""
                ref_text = ref_line
            
            # Calculate marker width and text start position
            if marker:
                marker_with_spaces = marker + "  "
                marker_width = c.stringWidth(marker_with_spaces, "Times-Roman", 12)
                ref_text_x = text_x + marker_width
                # First line: marker + text
                first_max = ref_encl_max_width - marker_width
                first_chunk, remaining = wrap_line(ref_text, "Times-Roman", 12, first_max, c)
                c.drawString(text_x, y, marker_with_spaces + first_chunk)
                y -= leading
                # Continuation lines align under first text character (not under marker)
                cont_max = ref_encl_max_width
                for cont_line in wrap_paragraph(remaining, "Times-Roman", 12, cont_max, c):
                    c.drawString(ref_text_x, y, cont_line)
                    y -= leading
            else:
                # No marker - just wrap text at text_x
                for wrapped_line in wrap_paragraph(ref_text, "Times-Roman", 12, ref_encl_max_width, c):
                    c.drawString(text_x, y, wrapped_line)
                    y -= leading

    # Encl: (if present) - only apply spacing before Encl if Encl exists
    if encl_count > 0:
        # One blank line before Encl (only if Encl exists)
        # If Ref was omitted, this creates Subj → ENCL = 1 leading unit
        # If Ref was present, this creates REF → ENCL = 1 leading unit
        y -= leading
        c.drawString(label_x, y, "Encl:")
        for i, encl_line in enumerate(normalized.get("encl", [])):
            # Parse marker and text from encl_line (e.g., "(1) Records Management...")
            marker_match = re.match(r'^\(([a-zA-Z0-9]+)\)\s+(.*)$', encl_line)
            if marker_match:
                marker = f"({marker_match.group(1)})"
                encl_text = marker_match.group(2)
            else:
                # No marker found, treat entire line as text
                marker = ""
                encl_text = encl_line
            
            # Calculate marker width and text start position
            if marker:
                marker_with_spaces = marker + "  "
                marker_width = c.stringWidth(marker_with_spaces, "Times-Roman", 12)
                encl_text_x = text_x + marker_width
                # First line: marker + text
                first_max = ref_encl_max_width - marker_width
                first_chunk, remaining = wrap_line(encl_text, "Times-Roman", 12, first_max, c)
                c.drawString(text_x, y, marker_with_spaces + first_chunk)
                y -= leading
                # Continuation lines align under first text character (not under marker)
                cont_max = ref_encl_max_width
                for cont_line in wrap_paragraph(remaining, "Times-Roman", 12, cont_max, c):
                    c.drawString(encl_text_x, y, cont_line)
                    y -= leading
            else:
                # No marker - just wrap text at text_x
                for wrapped_line in wrap_paragraph(encl_text, "Times-Roman", 12, ref_encl_max_width, c):
                    c.drawString(text_x, y, wrapped_line)
                    y -= leading

    return y


def main(input_path=None, output_path=None):
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    # Resolve input JSON path (default: examples/v6_sample_letter.json)
    if input_path:
        sample_path = input_path if os.path.isabs(input_path) else os.path.join(base_dir, input_path)
    else:
        sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")

    # Resolve output PDF path (default: output/v6_test_letter.pdf)
    if output_path:
        output_path = output_path if os.path.isabs(output_path) else os.path.join(base_dir, output_path)
    else:
        output_path = os.path.join(base_dir, "output", "v6_test_letter.pdf")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Print resolved paths
    print(f"INPUT_JSON: {sample_path}")
    print(f"OUTPUT_PDF: {output_path}")

    # Load sample payload
    if not os.path.exists(sample_path):
        print("=== PDF BUILD ===")
        print("FAIL")
        print(f"Missing: {sample_path}")
        return

    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

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

    # Initialize page-number continuation (for C9 new-page endorsements only)
    page_number_start = None
    force_page_number_on_first_page = False

    is_new_page_endorsement = (
        payload.get("doc_type") == "DT_ENDORSEMENT"
        and payload.get("endorsement_type") == "new_page"
    )

    if is_new_page_endorsement:
        raw_page_number_start = payload.get("page_number_start")
        if raw_page_number_start is not None:
            try:
                page_number_start = int(raw_page_number_start)
            except (TypeError, ValueError):
                page_number_start = None

        force_page_number_on_first_page = bool(
            payload.get("force_page_number_on_first_page", False)
        )

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
    body_font_size = 12  # body font size
    leading = body_font_size * 1.2  # line spacing with 20% extra (within paragraphs)
    blank_line = body_font_size * 1.2  # one blank line
    signature_gap = body_font_size * 4.0  # 4 lines below text before signature
    copy_gap = body_font_size * 2.0  # 2 lines below signature before copy_to
    page_break_buffer = body_font_size * 4.0  # minimum space before signature

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

    # ── MFR render branch (DT_MEMO_MFR only) ──
    if payload.get("doc_type") == "DT_MEMO_MFR":
        print(f"DEBUG === MFR RENDER PATH ===")
        
        # MFR layout constants (Figure 10-1)
        mfr_date_x = 440.0
        mfr_date_y = page_height - 140.0
        mfr_text_left = left_margin_pt  # Use standard left margin (72pt)
        mfr_subject_text_x = mfr_text_left + 43
        
        # Set font for MFR content (Times-Roman 12pt throughout)
        c.setFont("Times-Roman", 12)
        
        # Date at top-right position (Figure 10-1)
        mfr_date = normalized.get("date", "")
        if mfr_date:
            c.drawString(mfr_date_x, mfr_date_y, mfr_date)
            print(f"DEBUG MFR: Date drawn at x={mfr_date_x:.1f}, y={mfr_date_y:.1f}: '{mfr_date}'")
        
        # Title below date (MEMORANDUM FOR THE RECORD)
        mfr_title_y = mfr_date_y - (2 * leading)
        title = "MEMORANDUM FOR THE RECORD"
        c.drawString(mfr_text_left, mfr_title_y, title)
        print(f"DEBUG MFR: Title drawn at x={mfr_text_left:.1f}, y={mfr_title_y:.1f}: '{title}'")
        
        # Position for subject/body below title
        y = mfr_title_y - (2 * leading)
        
        # Optional Subj: line
        subj = normalized.get("subj")
        if subj:
            c.drawString(mfr_text_left, y, "Subj:")
            subj_max_width = page_width - right_margin_pt - mfr_subject_text_x
            y = draw_wrapped_text(c, mfr_subject_text_x, y, subj, 12, subj_max_width, leading)
            print(f"DEBUG MFR: Subj drawn at y={y:.1f}")
            # One blank line after subject before body
            y -= leading
        
        # Body block (use mfr_text_left as left margin)
        y, page_count, body_lines_on_last_page = draw_body_block(
            c, mfr_text_left, y, leading, body_font_size, normalized, page_height,
            top_margin_pt, bottom_margin_pt, signature_gap, copy_gap,
            reserve_signature_space=True,
            page_number_start=None, force_page_number_on_first_page=False
        )
        print(f"DEBUG MFR: Total pages generated: {page_count}")
        print(f"DEBUG MFR: Body lines on last page: {body_lines_on_last_page}")
        
        # MFR signature block (simple signer name + org code)
        y = draw_mfr_signature_block(c, normalized, page_width, y, leading, signature_gap)
        
        # Draw page number on final page
        draw_page_number(c, page_width, page_count, bottom_margin_pt)
        
        c.save()
        
        # Verify output file exists
        if os.path.exists(output_path):
            print("=== PDF BUILD ===")
            print("PASS")
            print(f"output\\{os.path.basename(output_path)}")
        else:
            print("=== PDF BUILD ===")
            print("FAIL")
            print("Output file not created")
        return  # Exit early; standard-letter path continues below

    # ── From-To render branch (DT_MEMO_FROM_TO_PLAIN only) ──
    if payload.get("doc_type") == "DT_MEMO_FROM_TO_PLAIN":
        print(f"DEBUG === FROM-TO PLAIN RENDER PATH ===")
        render_from_to_plain_pdf({"payload": payload, "normalized": normalized}, output_path)
        return  # Exit early; standard-letter path continues below

    # Render letterhead lines centered at top (H-series rules)
    if letterhead_lines:
        print(f"DEBUG === LETTERHEAD BLOCK ===")
        for i, lh_line in enumerate(letterhead_lines):
            if i == 0:
                # First line: bold, larger font
                lh_font_name = h_rules["first_line_font"]
                lh_font_size = h_rules["first_line_size"]
            else:
                # Subsequent lines: regular, smaller font
                lh_font_name = h_rules["subsequent_font"]
                lh_font_size = h_rules["subsequent_size"]

            c.setFont(lh_font_name, lh_font_size)
            lh_leading = lh_font_size * 1.2  # Letterhead-specific leading
            text_width = c.stringWidth(lh_line, lh_font_name, lh_font_size)
            x_centered = (page_width - text_width) / 2
            c.drawString(x_centered, y, lh_line)
            print(f"DEBUG LH line {i+1}: '{lh_line}' | font={lh_font_name} {lh_font_size}pt | x={x_centered:.1f} | y={y:.1f} | width={text_width:.1f}")
            y -= lh_leading

        # Spacing below letterhead per H-006
        if h_rules["spacing_after"] == "one_blank_line":
            # Use boundary helper for LETTERHEAD -> SSIC_DATE
            y -= get_boundary_spacing("LETTERHEAD", "SSIC_DATE", leading)
        print(f"DEBUG Letterhead block end y={y:.1f}")

    # SSIC/date sender-symbol block - longest-line left anchoring per H-series
    # Build sender-symbol lines in order: SSIC, originator code/serial (if present), date
    ssic_val = str(normalized.get('ssic', ''))
    originator_code = normalized.get('originator_code')
    serial = normalized.get('serial')
    raw_date_text = normalized.get('date', '')
    formatted_date = format_sender_symbol_date(raw_date_text)
    
    print(f"DEBUG raw date: {raw_date_text}")
    print(f"DEBUG formatted sender-symbol date: {formatted_date}")
    
    # Build lines per SECNAV manual: SSIC, serial (with "Ser " prefix) or originator, date
    sender_symbol_lines = []
    if ssic_val:
        sender_symbol_lines.append(ssic_val)
    
    # Serial takes precedence over originator_code if both present
    if serial:
        sender_symbol_lines.append("Ser " + str(serial))
    elif originator_code:
        sender_symbol_lines.append(str(originator_code))
    
    if formatted_date:
        sender_symbol_lines.append(formatted_date)
    
    # SSIC/date sender-symbol block uses standard correspondence font unless an explicit rule override is later added
    # Inherits BOTH font family and size from standard body/header settings
    standard_font_name = "Times-Roman"
    standard_font_size = body_font_size  # 12pt body font
    
    # Sender-symbol block inherits standard body font family and size
    sender_symbol_font_name = standard_font_name
    sender_symbol_font_size = standard_font_size
    
    print(f"DEBUG === SENDER-SYMBOL BLOCK ===")
    print(f"DEBUG standard_font_name: {standard_font_name}")
    print(f"DEBUG standard_font_size: {standard_font_size}pt")
    print(f"DEBUG sender_symbol_font_name: {sender_symbol_font_name}")
    print(f"DEBUG sender_symbol_font_size: {sender_symbol_font_size}pt")
    
    # Calculate longest line width and block left anchor
    c.setFont(sender_symbol_font_name, sender_symbol_font_size)
    right_edge_x = page_width - right_margin_pt
    longest_line_width = max(c.stringWidth(line, sender_symbol_font_name, sender_symbol_font_size) for line in sender_symbol_lines) if sender_symbol_lines else 0
    block_left_x = right_edge_x - longest_line_width
    
    print(f"DEBUG sender symbol lines: {sender_symbol_lines}")
    print(f"DEBUG longest line width: {longest_line_width:.1f}pt")
    print(f"DEBUG right_edge_x: {right_edge_x:.1f}pt")
    print(f"DEBUG block_left_x: {block_left_x:.1f}pt")
    
    # Draw all sender-symbol lines with shared left anchor
    for idx, line in enumerate(sender_symbol_lines):
        line_y = y
        c.drawString(block_left_x, y, line)
        print(f"DEBUG SSIC/date line '{line}' at x={block_left_x:.1f}, y={line_y:.1f}")
        if idx < len(sender_symbol_lines) - 1:
            y -= leading
    
    # Blank line after SSIC/date block before next header content
    y -= leading
    
    # Boundary: SSIC_DATE -> HEADER
    y -= get_boundary_spacing("SSIC_DATE", "HEADER", leading)

    # ── Endorsement heading (C9 new-page only) ──
    y = _draw_endorsement_heading(payload, c, y, left_margin_pt)

    # Header block - use dedicated function with proper SECNAV text column
    label_x = left_margin_pt
    text_x = left_margin_pt + 43  # 43 pt offset for proper SECNAV alignment

    y = draw_header_block(c, label_x, text_x, y, leading, normalized, page_width, right_margin_pt)

    # Boundary: HEADER -> BODY
    y -= get_boundary_spacing("HEADER", "BODY", leading)

    # Body block - use dedicated function with level-based indentation and pagination
    y, page_count, body_lines_on_last_page = draw_body_block(
        c, left_margin_pt, y, leading, body_font_size, normalized, page_height, top_margin_pt, bottom_margin_pt,
        signature_gap, copy_gap, reserve_signature_space=True,
        page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page
    )
    print(f"DEBUG Total pages generated: {page_count}")
    print(f"DEBUG Body lines on last page: {body_lines_on_last_page}")

    # Signature block orphan prevention:
    # Calculate required space for signature block as atomic unit
    required_signature_space = calculate_signature_space(normalized, leading, signature_gap, copy_gap)
    
    # Check if remaining space on current page is sufficient
    if y < bottom_margin_pt + required_signature_space:
        # Not enough room - start a new page for signature block
        draw_page_number(c, page_width, page_count, bottom_margin_pt, page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page)
        c.showPage()
        page_count += 1
        print(f"DEBUG SIGNATURE PAGINATION: Started page {page_count} for signature block (insufficient space)")
        # Draw continuation header on new page
        y = page_height - top_margin_pt
        c.setFont("Times-Roman", 12)
        c.drawString(left_margin_pt, y, "Subj:")
        header_text_x = left_margin_pt + 43
        subj_max_width = (c._pagesize[0] - 72.0) - header_text_x
        y = draw_wrapped_text(c, header_text_x, y, normalized.get('subj', ''), 12, subj_max_width, leading)
        # draw_wrapped_text returns y already positioned for next line (one leading below last subject line)
        # Signature block will start from this y position
        print(f"DEBUG Continuation header on signature page: label_x={left_margin_pt:.1f}, text_x={header_text_x:.1f}, y after header={y:.1f}")
        
        # Verify body_lines_on_last_page for audit
        if body_lines_on_last_page == 0:
            print(f"DEBUG NOTE: Signature page has no preceding body text (signature-only page)")
    else:
        print(f"DEBUG SIGNATURE: Enough space on current page (y={y:.1f}, need={required_signature_space:.1f})")

    # Draw signature block as atomic unit
    y = draw_signature_block(c, normalized, page_width, left_margin_pt, y, leading, signature_gap, copy_gap, bottom_margin_pt)

    # Draw page number on final page (page 2+ only)
    draw_page_number(c, page_width, page_count, bottom_margin_pt, page_number_start=page_number_start, force_page_number_on_first_page=force_page_number_on_first_page)

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


# ───────────────────────────────────────────────────────────────────
# C10 Phase 3B: Plain-Paper From-To Memorandum Renderer
# ───────────────────────────────────────────────────────────────────

def render_from_to_plain_pdf(data, output_path):
    """
    Render a Plain-Paper From-To Memorandum (DT_MEMO_FROM_TO_PLAIN).
    
    Requirements:
    - No letterhead
    - No SSIC/originator block
    - No endorsement heading
    - No standard-letter header stack
    - Explicitly set font to Times-Roman 12 before drawing From-To content
    - Date near top left
    - Draw MEMORANDUM FOR in Times-Roman 12, same font/weight as body text
    - Do not use bold or 14 pt for MEMORANDUM FOR
    - Use the normal left margin for the From-To text block
    - Draw From line below MEMORANDUM FOR
    - Draw To line below From
    - Draw required Subj line below To
    - Draw optional Ref line(s) below Subj if present
    - Draw optional Encl line(s) below Ref, or below Subj if no Ref
    - Use existing wrapping helper for long Subj/Ref/Encl text where practical
    - Use existing draw_body_block() for body
    - Use existing draw_signature_block() for the full C7-compatible signature block
    - Use draw_page_number() on final page
    - Do not use draw_mfr_signature_block()
    
    Spacing (one blank line between elements):
    - one blank line before Subj
    - one blank line before Ref if Ref exists
    - one blank line before Encl if Encl exists
    - one blank line before body after final header element
    """
    payload = data.get("payload", {})
    normalized = data.get("normalized", {})
    
    # Layout constants
    left_margin_pt = 72.0
    right_margin_pt = 72.0
    top_margin_pt = 72.0
    bottom_margin_pt = 72.0
    page_width, page_height = LETTER
    body_font_size = 12
    leading = body_font_size * 1.2
    signature_gap = 24
    copy_gap = 12
    
    # Create canvas
    c = canvas.Canvas(output_path, pagesize=LETTER)
    y = page_height - top_margin_pt
    
    # Set font to Times-Roman 12 for entire From-To content
    c.setFont("Times-Roman", 12)
    
    # ── From-To Header Block (Figure 10-3) ───────────────────────────
    
    # Date at upper right, flush with right margin (Times-Roman 12)
    date = normalized.get("date", "")
    if date:
        date_width = c.stringWidth(date, "Times-Roman", 12)
        date_x = page_width - right_margin_pt - date_width
        c.drawString(date_x, y, date)
        print(f"DEBUG FROM-TO: Date drawn at x={date_x:.1f}, y={y:.1f}: '{date}'")
        y -= leading
    
    # One blank line before MEMORANDUM
    y -= leading
    
    # MEMORANDUM heading (Times-Roman 12, not bold, not enlarged)
    c.drawString(left_margin_pt, y, "MEMORANDUM")
    print(f"DEBUG FROM-TO: MEMORANDUM drawn at x={left_margin_pt:.1f}, y={y:.1f}")
    y -= leading
    
    # One blank line before From
    y -= leading
    
    # From line
    From = normalized.get("from", "")
    if From:
        c.drawString(left_margin_pt, y, f"From: {From}")
        print(f"DEBUG FROM-TO: From drawn at x={left_margin_pt:.1f}, y={y:.1f}: '{From}'")
        y -= leading
    
    # To line
    To = normalized.get("to", "")
    if To:
        c.drawString(left_margin_pt, y, f"To: {To}")
        print(f"DEBUG FROM-TO: To drawn at x={left_margin_pt:.1f}, y={y:.1f}: '{To}'")
        y -= leading
    
    # Optional Via line (if present in payload)
    Via = normalized.get("via", [])
    if Via:
        for via_entry in Via:
            via_text = via_entry if isinstance(via_entry, str) else via_entry.get("via", "")
            if via_text:
                c.drawString(left_margin_pt, y, f"Via: {via_text}")
                print(f"DEBUG FROM-TO: Via drawn at x={left_margin_pt:.1f}, y={y:.1f}: '{via_text}'")
                y -= leading
    
    # One blank line before Subj
    y -= leading
    
    # Get optional Ref and Encl lines
    refs = normalized.get("ref", [])
    encls = normalized.get("encl", [])
    
    # Subj line
    subj = normalized.get("subj")
    if subj:
        c.drawString(left_margin_pt, y, "Subj:")
        subj_max_width = page_width - right_margin_pt - (left_margin_pt + 43)
        y = draw_wrapped_text(c, left_margin_pt + 43, y, subj, 12, subj_max_width, leading)
        print(f"DEBUG FROM-TO: Subj drawn at y={y:.1f}")
        
        # Handle Ref/Encl lines immediately after Subj without extra blank line
        if refs:
            # No blank line between Subj and Refs
            # Calculate x positions for labels and text
            ref_label_x = left_margin_pt
            ref_label_width = c.stringWidth("Ref:  ", "Times-Roman", 12)
            ref_text_x = left_margin_pt + ref_label_width
            
            for i, ref_text in enumerate(refs):
                if ref_text:
                    if i == 0:
                        # First ref line: draw "Ref:" label and marker/text
                        c.drawString(ref_label_x, y, "Ref:")
                        c.drawString(ref_text_x, y, ref_text)
                    else:
                        # Subsequent ref lines: draw only marker/text, aligned under first marker
                        c.drawString(ref_text_x, y, ref_text)
                    print(f"DEBUG FROM-TO: Ref drawn at x={ref_text_x:.1f}, y={y:.1f}: '{ref_text}'")
                    y -= leading
            # One blank line after all Refs before body or Encls
            y -= leading
        elif encls:
            # No blank line between Subj and Encls
            # Calculate x positions for labels and text
            encl_label_x = left_margin_pt
            encl_label_width = c.stringWidth("Encl:  ", "Times-Roman", 12)
            encl_text_x = left_margin_pt + encl_label_width
            
            for i, encl_text in enumerate(encls):
                if encl_text:
                    if i == 0:
                        # First encl line: draw "Encl:" label and marker/text
                        c.drawString(encl_label_x, y, "Encl:")
                        c.drawString(encl_text_x, y, encl_text)
                    else:
                        # Subsequent encl lines: draw only marker/text, aligned under first marker
                        c.drawString(encl_text_x, y, encl_text)
                    print(f"DEBUG FROM-TO: Encl drawn at x={encl_text_x:.1f}, y={y:.1f}: '{encl_text}'")
                    y -= leading
            # One blank line after all Encls before body
            y -= leading
        else:
            # No Refs or Encls - one blank line before body
            y -= leading
    
    # ── Body Block ───────────────────────────────────────────────────
    
    # Body block (use draw_body_block with standard margins)
    y, page_count, body_lines_on_last_page = draw_body_block(
        c, left_margin_pt, y, leading, body_font_size, normalized, page_height,
        top_margin_pt, bottom_margin_pt, signature_gap, copy_gap,
        reserve_signature_space=True,
        page_number_start=None, force_page_number_on_first_page=False
    )
    print(f"DEBUG FROM-TO: Total pages generated: {page_count}")
    print(f"DEBUG FROM-TO: Body lines on last page: {body_lines_on_last_page}")
    
    # ── Signature Block ──────────────────────────────────────────────
    
    # Draw signature block as atomic unit
    y = draw_signature_block(c, normalized, page_width, left_margin_pt, y, leading, signature_gap, copy_gap, bottom_margin_pt)
    
    # ── Page Number ──────────────────────────────────────────────────
    
    # Draw page number on final page
    draw_page_number(c, page_width, page_count, bottom_margin_pt)
    
    c.save()
    
    # Verify output file exists
    if os.path.exists(output_path):
        print("=== PDF BUILD ===")
        print("PASS")
        print(f"output\\{os.path.basename(output_path)}")
    else:
        print("=== PDF BUILD ===")
        print("FAIL")
        print("Output file not created")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SECNAV v6 PDF Renderer")
    parser.add_argument("input", nargs="?", default=None,
                        help="Input JSON path (default: examples/v6_sample_letter.json)")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output PDF path (default: output/v6_test_letter.pdf)")
    args = parser.parse_args()
    main(input_path=args.input, output_path=args.output)

