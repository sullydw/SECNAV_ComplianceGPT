# PDF Layout Audit C7 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Figure 7-1 Standard Letter compliance.

## Important Notes

- **This is a prototype only**, not a replacement for manual visual review.
- **Figure comparison is rule/profile-based**, not pixel-image comparison.
- Manual figures contain instructional dots, percent signs, captions, and artifacts, so **raw screenshot comparison is intentionally avoided**.

## Manual-and-Figure Source Standard

Every new layout profile must be grounded in **all available manual guidance**, not just the visible geometry of the figure. Before creating a profile, review:

1. **The chapter/section text rules surrounding the figure** — the manual prose that defines when the format is used, what fields are required or optional, and any conditional logic (e.g., single vs. multiple addressees, endorsement types).
2. **The figure title/caption** — it often states the exact document type, intended use case, or distinguishing characteristics.
3. **The instructional text inside the figure example itself** — labels, placeholders, and annotations printed within the figure boundary that describe field semantics (e.g., "Distribution:", "Copy to:", "SECOND ENDORSEMENT on ...").
4. **The actual visual/layout geometry of the figure** — x/y positions, alignment columns, vertical gaps, page placement, and spatial relationships between blocks.
5. **Existing project rule files and renderer behavior** — cross-reference `rules_v6/C*/*.json`, renderer source, and already-passing profiles to ensure consistency with established conventions.

### Examples

- **Figure 8-3** — The figure text and surrounding section explain when both `To:` and `Distribution:` are used together (group title + distribution list), which is distinct from Figure 8-1 (To-line only) and Figure 8-2 (Distribution-line only). A profile for Figure 8-3 must encode that both labels are present and ordered correctly.
- **Figure 7-4 Joint Letter** — The figure text and layout explain multiple command blocks and multiple signature placement. A future profile for joint letters must use `layout_regions` to enforce left/right command block boundaries and signature block positioning, derived from the manual's joint-letter instructions rather than inferred from a standard single-signature letter.
- **Figure 10-3 Plain-Paper From-To** — The figure text and layout support three memo variants (basic, with references, with enclosures). Each variant's profile encodes which labels are required, optional, or forbidden, and what vertical gaps apply, all sourced from the figure's own instructional text and geometry.

### Profile encoding

The audit tool remains **profile-based coordinate checking**, not pixel-image comparison. Manual-derived expectations should be encoded in the profile as:

- `required_text` / `forbidden_text` — presence/absence rules from the manual
- `order_rules` — vertical ordering derived from figure layout
- `alignment_groups` — x-coordinate alignment of label columns from figure geometry
- `layout_regions` — bounded areas for complex block placement (e.g., joint-letter command blocks)
- `alignment_rules` — continuation marker alignment from figure annotation
- `page_number_rules` — page placement from figure continuation-page examples
- `vertical_spacing_rules` — measured gaps between adjacent elements from figure geometry

### Manual visual review requirement

Even with thorough manual sourcing, **manual visual review remains required when creating a new profile**. The profile author must render a test PDF, open it alongside the manual figure, and verify that the encoded rules match both the text instructions and the visual layout before wiring the profile into a regression suite.

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
- **Figure 7-2 Standard Letter (Second Page / Continuation)** — wired into C7 Phase 1 regression runner; checks repeated subject placement and bottom-centered page number.

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
- `vertical_spacing_rules`: Profile-driven vertical gap checks between specified text elements. Each rule uses `from_text` / `to_text` to identify two spans, then measures the absolute y-difference between their top-left positions (`y0`). This is a profile-based gap check, not pixel-image comparison. Supports `expected_gap_pt` (preferred) and the legacy alias `expected_delta_pt`. If either text is missing, or the actual gap exceeds tolerance_pt, the check FAILs with the actual value shown.
- `vertical_sequence`: Sequence-aware vertical spacing rules that measure between actually adjacent visible elements, accounting for optional header blocks (Via/Ref/Encl). Supports `adjacent_pairs`, `from_any_previous_visible`, and `from_final_header_entry_before_body` for body-start spacing.
- `alignment_rules`: Ref/Encl continuation marker alignment rules (regex-based marker matching scoped to header block above body `1.`)
- `page_number_rules`: Page number placement checks. Each rule specifies `text` (exact match), optional `text_regex` (regex match), `page_index` (zero-based), `expected_y_from_bottom_pt`, `expected_center_x_pt`, and `tolerance_pt`. Optional `search_y_tolerance_pt` and `search_x_tolerance_pt` restrict the search to a window around the expected position to avoid false matches (e.g., paragraph markers that share the same text). The tool first searches within the window, then falls back to a full-page search if needed. If the page number is not found, the check FAILs rather than warning, because a required page number must be rendered.
- `layout_regions`: Named layout regions for figure-aware coordinate checks. Each region specifies `name`, `text` (case-insensitive match), optional `page_index` (0-based, defaults to `profile.page_index` then all pages), `x_min_pt`/`x_max_pt`/`y_min_pt`/`y_max_pt` bounds, and `required` (default true). If the matched span falls inside the bounds the check passes; if it is outside, the check FAILs and reports actual x/y. If `required` is false and the text is absent, the check is skipped with a warning. This supports future complex formats (e.g., joint letters with left/right command blocks and multiple signature blocks) by allowing profiles to declare where specific labels must appear, not just that they exist. It is still profile-based coordinate checking, not pixel-image comparison.
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

### Vertical Spacing Rules

The tool supports profile-driven vertical gap checks via `vertical_spacing_rules`. Each rule specifies:
- `from_text` and `to_text` to identify two text spans
- `expected_gap_pt` (or the legacy alias `expected_delta_pt`) for the expected y-distance
- `tolerance_pt` for acceptable deviation

The tool measures the absolute y-difference between the top-left positions (`y0`) of the matching spans. This is a **profile-based gap check**, not pixel-image comparison. If either span is missing, or the actual gap exceeds tolerance, the check FAILs and reports the actual value.

Example:
```json
{
  "name": "subj_to_body_gap",
  "from_text": "Subj:",
  "to_text": "1.",
  "expected_gap_pt": 129.6,
  "tolerance_pt": 4
}
```

### Sequence-Aware Spacing

The tool avoids fixed non-adjacent spacing checks (e.g., `To:` -> `Subj:`) because optional sections like `Via:`, `Ref:`, or `Encl:` can intervene and cause false warnings. Instead, it determines which header elements are actually present, sorts them by vertical position, and measures between adjacent rendered elements.

For body-start spacing, `from_final_header_entry_before_body` measures from the **final actual header-entry line** above body paragraph `1.`, not merely the `Ref:` or `Encl:` label line. This includes continuation markers like `(a)` or `(1)` when they represent the last line of the Ref/Encl block. This avoids broad tolerances when multiple Ref/Encl entries are present.

The `vertical_sequence` profile field supports:
- `adjacent_pairs`: check distance between adjacent pairs that are present
- `from_any_previous_visible`: check distance from whatever is immediately above a target element
- `from_final_header_entry_before_body`: check distance from the final header entry line before body paragraph `1.`

### Layout Regions

The tool supports figure-aware coordinate checks via `layout_regions`. Each region declares that a specific text label must appear inside a bounded page area. This prepares the tool for complex future formats (e.g., joint letters with left/right command blocks and multiple signature blocks) by allowing profiles to reason about where labels must be, not merely that they exist.

Each region specifies:
- `name`: descriptive name for the check
- `text`: exact or substring text to match (case-insensitive)
- `page_index`: optional 0-based page index; defaults to `profile.page_index` then falls back to all pages
- `x_min_pt`, `x_max_pt`, `y_min_pt`, `y_max_pt`: optional coordinate bounds
- `required`: default true; optional regions that are missing are skipped with a warning instead of failing

If the matched span falls inside the defined bounds, the check passes and reports the actual x/y. If it is outside, the check FAILs and reports the actual coordinates versus expected bounds. This remains profile-based PDF coordinate checking, not pixel-image comparison.

Example:
```json
{
  "layout_regions": [
    {
      "name": "from_label_region",
      "text": "From:",
      "page_index": 0,
      "x_min_pt": 60,
      "x_max_pt": 90,
      "y_min_pt": 120,
      "y_max_pt": 160,
      "required": true
    }
  ]
}
```

### Layout Relationships

The tool supports figure-aware geometric relationship checks via `layout_relationships`. Each relationship declares a constraint between two detected layout elements (e.g., "From: must be above To:", "Commanding Officer block must be left of another Commanding Officer block", "two signature lines must be on the same row"). This prepares the tool for complex manual-defined figures such as Figure 7-4 Joint Letter, where left/right command blocks and multiple signature blocks must be positioned relative to each other.

Supported relationship types:
- `above` — `first_text` y0 must be above `second_text` y0 by at least `min_delta_pt`
- `left_of` — `first_text` x0 must be left of `second_text` x0 by at least `min_delta_pt`
- `same_row` — `first_text` and `second_text` y0 must be within `tolerance_pt`

Each relationship specifies:
- `name`: descriptive name for the check
- `type`: one of `above`, `left_of`, `same_row`
- `first_text`: the first label to match (case-insensitive substring)
- `second_text`: the second label to match (case-insensitive substring)
- `page_index`: optional 0-based page index; defaults to `profile.page_index` then all pages
- `min_delta_pt`: required for `above` and `left_of` — minimum required delta
- `tolerance_pt`: required for `same_row` — maximum allowed y-difference

If either text is missing, the check FAILs. If the relationship is not satisfied, the check FAILs with actual x/y values. If it passes, the check reports `PASS` with the measured delta.

This remains **profile-based coordinate checking derived from the manual figure**, not unknown-document guessing or pixel-image comparison.

Example:
```json
{
  "layout_relationships": [
    {
      "name": "from_before_to_vertical",
      "type": "above",
      "first_text": "From:",
      "second_text": "To:",
      "page_index": 0,
      "min_delta_pt": 5
    }
  ]
}
```

### Span Dump Diagnostic Mode

The tool supports a `--dump-spans` CLI option that prints a clean table of every extracted text span with its page number and bounding-box coordinates. This is a **diagnostic-only** mode; it does not affect pass/fail results and can be used alongside any profile.

This mode supports manual-and-figure-based profile building by exposing the exact coordinates the tool sees, which is especially useful when constructing:
- `layout_regions` — to determine x_min/x_max and y_min/y_max bounds
- `layout_relationships` — to confirm relative positions before writing rules
- `vertical_spacing_rules` — to measure actual gaps between elements

Output format:

```
SPAN DUMP
page  x0      y0      x1      y1      text
1     72.0    135.6   102.0   149.4   From:
1     72.0    150.0   92.0    163.8   To:
```

Usage:
```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_1_standard_letter.json --pdf output/audit_c7_phase1_standard_letter.pdf --dump-spans
```

Spans are sorted by page, then by y0 (top), then by x0 (left). This remains diagnostic output; the normal audit checks run unchanged after the dump.

## Status

- **Prototype only**
- **Figure 7-1 and Figure 7-2 are both wired into** `tools/run_c7_phase1_regression.py` — layout audit runs automatically after PDF generation and failure on either figure fails C7 Phase 1 regression
- The standalone audit tool can still be run manually:
  ```bash
  python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_1_standard_letter.json --pdf output/audit_c7_phase1_standard_letter.pdf
  python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_2_standard_letter_second_page.json --pdf output/audit_c7_phase1_standard_letter.pdf
  ```
- Manual review still required for final compliance
