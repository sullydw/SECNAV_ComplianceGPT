# PDF Layout Audit C7 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Figure 7-1 Standard Letter compliance.

## Important Notes

- **This is a prototype only**, not a replacement for manual visual review.
- **Figure comparison is rule/profile-based**, not pixel-image comparison.
- Manual figures contain instructional dots, percent signs, captions, and artifacts, so **raw screenshot comparison is intentionally avoided**.

## Profile-Based Checking

The tool checks:
- Presence of required labels: `From:`, `To:`, `Subj:`, `1.`
- Optional labels if present: `Via:`, `Ref:`, `Encl:`
- Vertical ordering of headers
- Header label-column alignment for `From:` / `To:` / `Subj:`
- Header text-column alignment for text content after `From:` / `To:` / `Subj:`
- Sequence-aware vertical spacing between adjacent visible header/body elements
- Body paragraph placement below final header entry line (not just the label line)
- **Ref/Encl continuation marker alignment** — e.g., `(a)`/`(b)` and `(1)`/`(2)` x-positions aligned within tolerance (scored to header block above body `1.` when possible)

### Scope

Currently supports:
- **Figure 7-1 Standard Letter (First Page)** — wired into C7 Phase 1 regression runner.
- **Figure 7-2 Standard Letter (Second Page / Continuation)** — standalone profile for second-page validation; checks repeated subject placement and bottom-centered page number.

Future profiles can be added for:
- Figure 8-1/8-2/8-3
- Figure 9-2
- Figure 10-1
- Figure 10-3

## Usage

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_1_standard_letter.json --pdf output/audit_c7_phase1_standard_letter.pdf
```

## Tolerances

- X tolerance: 3 points
- Y tolerance: 4 points

## Output Format

JSON-like console summary:
```
profile: docs/layout_profiles/figure_7_1_standard_letter.json
pdf:     output/audit_c7_phase1_standard_letter.pdf
passed:  8
failed:  0
warnings: 1
Extracted key positions:
  'From:' @ x=(72.0, 662.4) - x=(507.6, 662.4)
  'To:'  @ x=(72.0, 648.0) - x=(442.1, 648.0)
  ...
```

## Profile Format

The profile JSON includes:
- `figure_id`: "7-1"
- `manual_reference`: "SECNAV M-5216.5 Figure 7-1"
- `doc_type`: "DT_STANDARD_LETTER"
- `target_pdf`: "output/audit_c7_phase1_standard_letter.pdf"
- `page_index`: Optional zero-based page index. When present, required text, ordering, alignment, and page-number checks are scoped to that page only. If the page does not exist, the audit fails immediately.
- `required_text`: ["From:", "To:", "Subj:", "1."]
- `optional_text`: ["Via:", "Ref:", "Encl:"]
- `order_rules`: Expected vertical ordering
- `alignment_groups`: Coarse x-coordinate alignment groups (e.g., `header_label_column` for `From:` / `To:` / `Subj:`). May include `expected_x_pt` to compare each text to an absolute expected position instead of comparing to the first found item.
- `label_content_alignment_groups`: Coarse x-coordinate alignment for text content after labels (e.g., `header_text_column`)
- `vertical_spacing_rules`: Legacy fixed-pair vertical spacing rules (e.g., `from_to_normal_line`)
- `vertical_sequence`: Sequence-aware vertical spacing rules that measure between actually adjacent visible elements, accounting for optional header blocks (Via/Ref/Encl). Supports `adjacent_pairs`, `from_any_previous_visible`, and `from_final_header_entry_before_body` for body-start spacing.
- `alignment_rules`: Ref/Encl continuation marker alignment rules (regex-based marker matching scoped to header block above body `1.`)
- `page_number_rules`: Page number placement checks. Each rule specifies `text`, `page_index` (zero-based), `expected_y_from_bottom_pt`, `expected_center_x_pt`, and `tolerance_pt`. The tool calculates center_x and y_from_bottom and compares to expected values.
- `spacing_tolerances`: X/Y tolerances

## Implementation

Uses PyMuPDF (`fitz`) for text extraction:
1. Extract visible text spans/words
2. Get page number, text, x0, y0, x1, y1
3. Profile matching and rule checking

### Continuation Marker Alignment

The tool checks that Ref continuation markers (e.g., `(a)`, `(b)`) and Encl continuation markers (e.g., `(1)`, `(2)`) are horizontally aligned within their respective groups.

For each `alignment_rules` entry:
- Apply the `marker_regex` to all spans
- Restrict to markers in the header block above body paragraph `1.` (same page, strictly above `1.`)
- Skip with a warning if fewer than 2 markers are found
- Compare marker x0 values to the first marker x0
- PASS if all markers are within tolerance_pt; FAIL if any are outside

This prevents body-level paragraph markers (like `(1)` in subdivisions) from interfering with header-level Ref/Encl marker alignment checks.

### Sequence-Aware Spacing

The tool avoids fixed non-adjacent spacing checks (e.g., `To:` -> `Subj:`) because optional sections like `Via:`, `Ref:`, or `Encl:` can intervene and cause false warnings. Instead, it determines which header elements are actually present, sorts them by vertical position, and measures between adjacent rendered elements.

For body-start spacing, `from_final_header_entry_before_body` measures from the **final actual header-entry line** above body paragraph `1.`, not merely the `Ref:` or `Encl:` label line. This includes continuation markers like `(a)` or `(1)` when they represent the last line of the Ref/Encl block. This avoids broad tolerances when multiple Ref/Encl entries are present.

The `vertical_sequence` profile field supports:
- `adjacent_pairs`: check distance between adjacent pairs that are present
- `from_any_previous_visible`: check distance from whatever is immediately above a target element
- `from_final_header_entry_before_body`: check distance from the final header entry line before body paragraph `1.`

## Status

- **Prototype only**
- **Wired into** `tools/run_c7_phase1_regression.py` — layout audit runs automatically after PDF generation and failure fails C7 Phase 1 regression
- The standalone audit tool can still be run manually:
  ```bash
  python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_1_standard_letter.json --pdf output/audit_c7_phase1_standard_letter.pdf
  ```
- Manual review still required for final compliance
