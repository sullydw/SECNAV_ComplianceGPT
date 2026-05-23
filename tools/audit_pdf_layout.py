#!/usr/bin/env python
# C7 Layout Audit Prototype

import argparse
import json
import re
import sys
from pathlib import Path


def extract_text_spans(pdf_path: str) -> tuple[list[dict], list[dict]]:
    """Extract text spans from PDF and return (spans, page_dimensions).
    page_dimensions is a list of dicts with 'width' and 'height' per page.
    """
    import fitz
    doc = fitz.open(pdf_path)
    spans = []
    page_dimensions = []
    for page_num, page in enumerate(doc, start=1):
        rect = page.rect
        page_dimensions.append({"width": rect.width, "height": rect.height})
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        bbox = span.get("bbox", [0, 0, 0, 0])
                        spans.append({"page": page_num, "text": text, "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]})
    doc.close()
    return spans, page_dimensions


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
    """Check vertical spacing (y-gap) between labeled elements.

    Supports both legacy 'expected_delta_pt' and preferred 'expected_gap_pt'.
    Uses absolute y-difference between the top-left y0 of each element.
    """
    for rule in rules:
        name = rule.get("name", "unnamed_rule")
        from_text = rule.get("from_text", "")
        to_text = rule.get("to_text", "")
        expected = rule.get("expected_gap_pt", rule.get("expected_delta_pt", 0))
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
            passed.append(f"vertical_spacing '{name}': gap={actual:.1f}pt (expected={expected}pt, tolerance=±{tolerance}pt)")
        else:
            failed.append(
                f"vertical_spacing '{name}': gap={actual:.1f}pt vs expected={expected}pt (outside ±{tolerance}pt)"
            )


def check_vertical_sequence(spans, vertical_sequence, passed, failed, warnings_list):
    """Sequence-aware vertical spacing: measure between actual adjacent visible elements."""
    elements = vertical_sequence.get("elements", [])
    rules = vertical_sequence.get("rules", [])

    if not elements:
        return

    # Determine which elements are present, sorted by y position (top to bottom; y0 is larger at top in PDF)
    present = []
    for elem in elements:
        span = find_first_span(spans, elem)
        if span is not None:
            present.append((elem, span))

    if len(present) < 2:
        return

    # Sort by y position ascending: smaller y0 = higher on page (PDF coords)
    present.sort(key=lambda item: item[1].get("y0", 0))

    for rule in rules:
        name = rule.get("name", "unnamed_rule")
        rule_type = None

        if "pairs" in rule:
            rule_type = "adjacent_pairs"
        elif rule.get("from_any_previous_visible", False):
            rule_type = "from_any_previous_visible"
        elif rule.get("from_final_header_entry_before_body"):
            rule_type = "from_final_header_entry_before_body"
        else:
            # Check if from_text/to_text exist for backward compatibility with simple rules
            from_text = rule.get("from_text")
            to_text = rule.get("to_text")
            if from_text and to_text:
                expected = rule.get("expected_delta_pt", 0)
                tolerance = rule.get("tolerance_pt", 2.5)
                from_span = find_first_span(spans, from_text)
                to_span = find_first_span(spans, to_text)
                if from_span is None or to_span is None:
                    continue
                actual = abs(to_span.get("y0", 0) - from_span.get("y0", 0))
                diff = abs(actual - expected)
                if diff <= tolerance:
                    passed.append(f"vertical_seq '{name}': delta={actual:.1f}pt within tol")
                else:
                    warnings_list.append(f"vertical_seq '{name}': delta={actual:.1f}pt outside tol")
            continue

        if rule_type == "adjacent_pairs":
            pairs = rule.get("pairs", [])
            expected = rule.get("expected_delta_pt", 14.4)
            tolerance = rule.get("tolerance_pt", 2.5)

            for a_text, b_text in pairs:
                # Find indices in present list
                a_idx = None
                b_idx = None
                for i, (text, _) in enumerate(present):
                    if text == a_text:
                        a_idx = i
                    if text == b_text:
                        b_idx = i
                if a_idx is None or b_idx is None:
                    continue
                if abs(a_idx - b_idx) != 1:
                    # Not adjacent in rendered output; skip this check
                    continue
                a_span = present[a_idx][1]
                b_span = present[b_idx][1]
                actual = abs(b_span.get("y0", 0) - a_span.get("y0", 0))
                diff = abs(actual - expected)
                if diff <= tolerance:
                    passed.append(f"vertical_seq '{name}': {a_text} -> {b_text} delta={actual:.1f}pt (ok)")
                else:
                    warnings_list.append(
                        f"vertical_seq '{name}': {a_text} -> {b_text} delta={actual:.1f}pt vs exp={expected}pt"
                    )

        elif rule_type == "from_any_previous_visible":
            to_text = rule.get("to_text", "")
            expected = rule.get("expected_delta_pt", 28.8)
            tolerance = rule.get("tolerance_pt", 3.0)

            target_idx = None
            for i, (text, _) in enumerate(present):
                if text == to_text:
                    target_idx = i
                    break
            if target_idx is None or target_idx == 0:
                continue
            # Previous visible element
            prev_span = present[target_idx - 1][1]
            target_span = present[target_idx][1]
            actual = abs(target_span.get("y0", 0) - prev_span.get("y0", 0))
            diff = abs(actual - expected)
            prev_label = present[target_idx - 1][0]
            if diff <= tolerance:
                passed.append(
                    f"vertical_seq '{name}': {prev_label} -> {to_text} delta={actual:.1f}pt (ok)"
                )
            else:
                warnings_list.append(
                    f"vertical_seq '{name}': {prev_label} -> {to_text} delta={actual:.1f}pt vs exp={expected}pt"
                )

        elif rule_type == "from_final_header_entry_before_body":
            to_text = rule.get("to_text", "1.")
            expected = rule.get("expected_delta_pt", 28.8)
            tolerance = rule.get("tolerance_pt", 3.0)

            body_span = None
            for s in spans:
                if to_text.lower() in s.get("text", "").lower():
                    body_span = s
                    break

            if body_span is None:
                warnings_list.append(f"vertical_seq '{name}': body '{to_text}' not found")
                continue

            body_page = body_span.get("page", 1)
            body_y = body_span.get("y0", 0)

            # Find header entry candidates on same page above body
            header_label_re = re.compile(r"^(Subj:|Ref:|Encl:)", re.IGNORECASE)
            ref_cont_re = re.compile(r"^\([a-z]+\)")
            encl_cont_re = re.compile(r"^\([0-9]+\)")

            candidates = []
            for s in spans:
                text = s.get("text", "")
                if s.get("page", 1) != body_page:
                    continue
                if s.get("y0", 0) >= body_y:
                    continue
                if header_label_re.search(text) or ref_cont_re.search(text) or encl_cont_re.search(text):
                    candidates.append((text, s))

            if not candidates:
                warnings_list.append(
                    f"vertical_seq '{name}': no header-entry candidate found above '{to_text}'"
                )
                continue

            # Choose lowest on page (highest y0)
            candidates.sort(key=lambda item: item[1].get("y0", 0), reverse=True)
            final_text, final_span = candidates[0]

            actual = abs(body_y - final_span.get("y0", 0))
            diff = abs(actual - expected)
            if diff <= tolerance:
                passed.append(
                    f"vertical_seq '{name}': '{final_text}' -> '{to_text}' delta={actual:.1f}pt (ok)"
                )
            else:
                warnings_list.append(
                    f"vertical_seq '{name}': '{final_text}' -> '{to_text}' delta={actual:.1f}pt vs exp={expected}pt"
                )


def check_continuation_marker_alignment(spans, alignment_rules, passed, failed, warnings_list):
    """Check x-alignment of Ref/Encl continuation markers, scoped to header block above body."""
    # Determine body start position for scoping
    body_span = None
    for s in spans:
        if s.get("text", "").strip() == "1.":
            body_span = s
            break

    body_page = body_span.get("page", 1) if body_span else None
    body_y = body_span.get("y0", 0) if body_span else float('inf')

    for rule in alignment_rules:
        name = rule.get("name", "unnamed_rule")
        pattern = rule.get("marker_regex", "")
        tolerance = rule.get("tolerance_pt", 3)

        if not pattern:
            continue

        try:
            regex = re.compile(pattern)
        except re.error as e:
            warnings_list.append(f"marker_alignment '{name}': invalid regex '{pattern}': {e}")
            continue

        # Find matching markers, scoped to header area above body
        matches = []
        for s in spans:
            text = s.get("text", "")
            if regex.match(text):
                if body_span is not None:
                    if s.get("page", 1) != body_page:
                        continue
                    if s.get("y0", 0) >= body_y:
                        continue
                matches.append((text, s.get("x0", 0)))

        if len(matches) < 2:
            if len(matches) == 1:
                warnings_list.append(
                    f"marker_alignment '{name}': only 1 marker found ('{matches[0][0]}' at x={matches[0][1]:.1f}pt); alignment check skipped"
                )
            else:
                warnings_list.append(f"marker_alignment '{name}': no markers found; alignment check skipped")
            continue

        first_x = matches[0][1]
        all_within = True
        for text, x in matches:
            if abs(x - first_x) > tolerance:
                all_within = False
                break

        vals_str = ", ".join(f"'{t}'={x:.1f}" for t, x in matches)
        if all_within:
            passed.append(f"marker_alignment '{name}': aligned within {tolerance}pt ({vals_str})")
        else:
            failed.append(f"marker_alignment '{name}': misaligned ({vals_str})")


def check_forbidden_text(spans, forbidden_text, passed, failed):
    """Check that forbidden text does not appear anywhere in the PDF."""
    for text in forbidden_text:
        matches = [s for s in spans if s.get("text", "").strip().lower() == text.lower()]
        if matches:
            locations = ", ".join(
                f"page {m['page']} y={m['y0']:.1f}" for m in matches[:3]
            )
            if len(matches) > 3:
                locations += f", ... ({len(matches)} total)"
            failed.append(f"forbidden '{text}': found ({locations})")
        else:
            passed.append(f"forbidden '{text}': absent (ok)")


def check_alignment_groups(spans, alignment_groups, passed, failed):
    """Check x-coordinate alignment across groups of label x positions."""
    for group in alignment_groups:
        name = group.get("name", "unnamed_group")
        texts = group.get("texts", [])
        x_field = group.get("x_field", "x0")
        tolerance = group.get("tolerance_pt", 3)
        expected_x = group.get("expected_x_pt")

        if not texts:
            continue

        values = []
        for text in texts:
            span = find_first_span(spans, text)
            if span is None:
                failed.append(f"alignment_group '{name}': missing '{text}'")
            else:
                values.append((text, span.get(x_field, None)))

        if len(values) < 1:
            continue

        if expected_x is not None:
            # Compare each text to expected_x
            all_within = True
            for text, val in values:
                if val is not None and abs(val - expected_x) > tolerance:
                    all_within = False
                    break
            if all_within:
                vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
                passed.append(f"alignment_group '{name}': aligned within {tolerance}pt to expected {expected_x}pt ({vals_str})")
            else:
                vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
                failed.append(f"alignment_group '{name}': misaligned vs expected {expected_x}pt ({vals_str})")
        else:
            # Compare all to first found value
            if len(values) < 2:
                continue
            first_val = values[0][1]
            all_within = True
            for text, val in values:
                if val is not None and abs(val - first_val) > tolerance:
                    all_within = False
                    break
            if all_within:
                vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
                passed.append(f"alignment_group '{name}': aligned within {tolerance}pt ({vals_str})")
            else:
                vals_str = ", ".join(f"{t}={v:.1f}" for t, v in values)
                failed.append(f"alignment_group '{name}': misaligned ({vals_str})")


def check_page_number_rules(spans, page_dimensions, rules, passed, failed, warnings):
    """Check page number placement: horizontal center and vertical distance from bottom.

    Supports robust detection via:
    - exact standalone span match (text field)
    - regex match (text_regex field)
    - vertical/horizontal search window filtering (search_y_tolerance_pt, search_x_tolerance_pt)
    Falls back to full-page search if scoped search yields no match.
    """
    for rule in rules:
        name = rule.get("name", "unnamed_rule")
        text = rule.get("text", "")
        text_regex = rule.get("text_regex", "")
        page_index = rule.get("page_index", 0)
        expected_y_from_bottom = rule.get("expected_y_from_bottom_pt", 0)
        expected_center_x = rule.get("expected_center_x_pt", 0)
        tolerance = rule.get("tolerance_pt", 6)
        search_y_tolerance = rule.get("search_y_tolerance_pt", tolerance)
        search_x_tolerance = rule.get("search_x_tolerance_pt", tolerance)

        if not text and not text_regex:
            continue

        # Verify page exists
        if page_index < 0 or page_index >= len(page_dimensions):
            failed.append(f"page_number '{name}': page_index {page_index} out of range (pdf has {len(page_dimensions)} pages)")
            continue

        page_height = page_dimensions[page_index].get("height", 0)
        target_page = page_index + 1

        def _match_text(span_text):
            """Return True if span text matches the rule's text or text_regex."""
            if text and span_text.strip() == text:
                return True
            if text_regex and re.search(text_regex, span_text):
                return True
            return False

        def _within_search_window(s):
            """Return True if span center is within optional x/y search tolerances."""
            if expected_y_from_bottom > 0 and page_height:
                center_y = (s.get("y0", 0) + s.get("y1", 0)) / 2.0
                y_from_bottom = page_height - center_y
                if abs(y_from_bottom - expected_y_from_bottom) > search_y_tolerance:
                    return False
            if expected_center_x > 0 and search_x_tolerance is not None:
                center_x = (s.get("x0", 0) + s.get("x1", 0)) / 2.0
                if abs(center_x - expected_center_x) > search_x_tolerance:
                    return False
            return True

        # 1. Try scoped search (window + exact/text_regex match)
        matches = [s for s in spans if s.get("page") == target_page and _within_search_window(s) and _match_text(s.get("text", ""))]

        # 2. Broaden to all spans on target page with same text/regex
        if not matches:
            matches = [s for s in spans if s.get("page") == target_page and _match_text(s.get("text", ""))]

        if not matches:
            failed.append(
                f"page_number '{name}': text '{text}' (regex: {text_regex!r}) not found on page {target_page} "
                f"(searched y_from_bottom={expected_y_from_bottom}pt ±{search_y_tolerance}pt); expected page number required by profile"
            )
            continue

        # Use first match
        match = matches[0]
        x0 = match.get("x0", 0)
        x1 = match.get("x1", 0)
        y0 = match.get("y0", 0)
        y1 = match.get("y1", 0)
        center_x = (x0 + x1) / 2.0
        center_y = (y0 + y1) / 2.0
        y_from_bottom = page_height - center_y if page_height else 0

        x_diff = abs(center_x - expected_center_x)
        y_diff = abs(y_from_bottom - expected_y_from_bottom)

        if x_diff <= tolerance and y_diff <= tolerance:
            passed.append(
                f"page_number '{name}': center_x={center_x:.1f}pt, y_from_bottom={y_from_bottom:.1f}pt (expected center_x={expected_center_x}pt, y_from_bottom={expected_y_from_bottom}pt, tolerance=±{tolerance}pt)"
            )
        else:
            failed.append(
                f"page_number '{name}': center_x={center_x:.1f}pt (diff={x_diff:.1f}pt), y_from_bottom={y_from_bottom:.1f}pt (diff={y_diff:.1f}pt) vs expected center_x={expected_center_x}pt, y_from_bottom={expected_y_from_bottom}pt (tolerance=±{tolerance}pt)"
            )


def check_layout_regions(spans, regions, passed, failed, warnings_list, profile_page_index=None):
    """Check that labeled text spans fall within expected page regions.

    Each region dict may contain:
      - name: str (required)
      - text: str (required) — case-insensitive match against span text
      - page_index: int (optional, 0-based; defaults to profile_page_index then all pages)
      - x_min_pt, x_max_pt, y_min_pt, y_max_pt: float bounds
      - required: bool (default True)
    """
    for region in regions:
        name = region.get("name", "unnamed_region")
        text = region.get("text", "")
        if not text:
            warnings_list.append(f"layout_region '{name}': no 'text' specified; skipped")
            continue

        target_page = region.get("page_index")
        if target_page is None:
            target_page = profile_page_index
        if target_page is not None:
            target_page_1based = target_page + 1  # spans are 1-based
            search_spans = [s for s in spans if s.get("page") == target_page_1based]
        else:
            search_spans = spans

        match = None
        for s in search_spans:
            if text.lower() in s.get("text", "").lower():
                match = s
                break

        required = region.get("required", True)
        x_min = region.get("x_min_pt")
        x_max = region.get("x_max_pt")
        y_min = region.get("y_min_pt")
        y_max = region.get("y_max_pt")

        if match is None:
            if required:
                failed.append(f"layout_region '{name}': missing required text '{text}'")
            else:
                warnings_list.append(f"layout_region '{name}': skipped optional missing")
            continue

        x0 = match.get("x0", 0)
        y0 = match.get("y0", 0)
        page = match.get("page", 1)
        page_desc = f" page={page}" if target_page is None else ""

        in_x = (x_min is None or x0 >= x_min) and (x_max is None or x0 <= x_max)
        in_y = (y_min is None or y0 >= y_min) and (y_max is None or y0 <= y_max)

        if in_x and in_y:
            bounds_parts = []
            if x_min is not None or x_max is not None:
                bounds_parts.append(f"x={x0:.1f}")
            if y_min is not None or y_max is not None:
                bounds_parts.append(f"y={y0:.1f}")
            detail = ", ".join(bounds_parts) + page_desc
            passed.append(f"layout_region '{name}': PASS {detail}")
        else:
            fail_parts = [f"x={x0:.1f}", f"y={y0:.1f}{page_desc}"]
            if not in_x:
                fail_parts.append("outside x bounds")
            if not in_y:
                fail_parts.append("outside y bounds")
            failed.append(f"layout_region '{name}': FAIL {' '.join(fail_parts)} (expected x in [{x_min}, {x_max}], y in [{y_min}, {y_max}])")


def check_layout_relationships(spans, relationships, passed, failed, profile_page_index=None):
    """Check geometric relationships between two detected layout elements.

    Supported types:
      - "above": first_text y0 must be above second_text y0 by at least min_delta_pt
      - "left_of": first_text x0 must be left of second_text x0 by at least min_delta_pt
      - "same_row": first_text and second_text y0 must be within tolerance_pt

    Each relationship dict may contain:
      - name: str (required)
      - type: str (required) — one of above, left_of, same_row
      - first_text: str (required)
      - second_text: str (required)
      - page_index: int (optional, 0-based; defaults to profile_page_index then all pages)
      - min_delta_pt: float (required for above/left_of)
      - tolerance_pt: float (required for same_row)
    """
    for rel in relationships:
        name = rel.get("name", "unnamed_relationship")
        rel_type = rel.get("type", "")
        first_text = rel.get("first_text", "")
        second_text = rel.get("second_text", "")
        page_index = rel.get("page_index")
        min_delta_pt = rel.get("min_delta_pt", 0)
        tolerance_pt = rel.get("tolerance_pt", 4)

        if not first_text or not second_text or not rel_type:
            failed.append(f"layout_relationship '{name}': missing required fields (type, first_text, second_text)")
            continue

        target_page = page_index if page_index is not None else profile_page_index
        if target_page is not None:
            target_page_1based = target_page + 1
            search_spans = [s for s in spans if s.get("page") == target_page_1based]
        else:
            search_spans = spans

        first_span = None
        second_span = None
        for s in search_spans:
            if first_span is None and first_text.lower() in s.get("text", "").lower():
                first_span = s
            if second_span is None and second_text.lower() in s.get("text", "").lower():
                second_span = s
            if first_span is not None and second_span is not None:
                break

        if first_span is None:
            failed.append(f"layout_relationship '{name}': missing '{first_text}'")
            continue
        if second_span is None:
            failed.append(f"layout_relationship '{name}': missing '{second_text}'")
            continue

        x0_first = first_span.get("x0", 0)
        y0_first = first_span.get("y0", 0)
        x0_second = second_span.get("x0", 0)
        y0_second = second_span.get("y0", 0)

        if rel_type == "above":
            delta = y0_second - y0_first
            if delta >= min_delta_pt:
                passed.append(f"layout_relationship '{name}': PASS (first y={y0_first:.1f}, second y={y0_second:.1f}, delta={delta:.1f}pt)")
            else:
                failed.append(f"layout_relationship '{name}': FAIL '{first_text}' y={y0_first:.1f} not above '{second_text}' y={y0_second:.1f} by >= {min_delta_pt}pt (actual delta={delta:.1f}pt)")

        elif rel_type == "left_of":
            delta = x0_second - x0_first
            if delta >= min_delta_pt:
                passed.append(f"layout_relationship '{name}': PASS (first x={x0_first:.1f}, second x={x0_second:.1f}, delta={delta:.1f}pt)")
            else:
                failed.append(f"layout_relationship '{name}': FAIL '{first_text}' x={x0_first:.1f} not left of '{second_text}' x={x0_second:.1f} by >= {min_delta_pt}pt (actual delta={delta:.1f}pt)")

        elif rel_type == "same_row":
            delta = abs(y0_first - y0_second)
            if delta <= tolerance_pt:
                passed.append(f"layout_relationship '{name}': PASS (first y={y0_first:.1f}, second y={y0_second:.1f}, delta={delta:.1f}pt within ±{tolerance_pt}pt)")
            else:
                failed.append(f"layout_relationship '{name}': FAIL '{first_text}' y={y0_first:.1f} and '{second_text}' y={y0_second:.1f} not same row (delta={delta:.1f}pt > ±{tolerance_pt}pt)")

        else:
            failed.append(f"layout_relationship '{name}': unsupported type '{rel_type}'")


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

    spans, page_dimensions = extract_text_spans(args.pdf)
    print(f"Extracted {len(spans)} text spans across {len(page_dimensions)} page(s)")

    page_index = profile.get("page_index")
    if page_index is not None:
        target_page = page_index + 1  # spans are 1-based
        if target_page > len(page_dimensions) or target_page < 1:
            print(f"\nRESULT: FAIL")
            print(f"  profile specifies page_index={page_index} (page {target_page}), but PDF only has {len(page_dimensions)} page(s)")
            sys.exit(1)
        spans = [s for s in spans if s.get("page") == target_page]
        print(f"Filtered to page_index={page_index} (page {target_page}): {len(spans)} spans")

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

    # Check vertical spacing rules (legacy, kept for compatibility)
    vertical_spacing_rules = profile.get("vertical_spacing_rules", [])
    if vertical_spacing_rules:
        check_vertical_spacing_rules(spans, vertical_spacing_rules, passed, failed, warnings)

    # Check vertical spacing sequence-aware
    vertical_sequence = profile.get("vertical_sequence", {})
    if vertical_sequence:
        check_vertical_sequence(spans, vertical_sequence, passed, failed, warnings)

    # Check layout regions
    layout_regions = profile.get("layout_regions", [])
    if layout_regions:
        check_layout_regions(spans, layout_regions, passed, failed, warnings, profile_page_index=page_index)

    # Check layout relationships
    layout_relationships = profile.get("layout_relationships", [])
    if layout_relationships:
        check_layout_relationships(spans, layout_relationships, passed, failed, profile_page_index=page_index)

    # Check continuation marker alignment
    alignment_rules = profile.get("alignment_rules", [])
    if alignment_rules:
        check_continuation_marker_alignment(spans, alignment_rules, passed, failed, warnings)

    # Check page number rules
    page_number_rules = profile.get("page_number_rules", [])
    if page_number_rules:
        check_page_number_rules(spans, page_dimensions, page_number_rules, passed, failed, warnings)

    # Check forbidden text
    forbidden = profile.get("forbidden_text", [])
    if forbidden:
        check_forbidden_text(spans, forbidden, passed, failed)

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
