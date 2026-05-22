# PDF Layout Audit C8 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 8 multiple-address letter compliance, specifically Figure 8-1 Multiple-Address Letter Using To: Line.

## Important Notes

- **This is a prototype only**, not a replacement for manual visual review.
- **Figure comparison is rule/profile-based**, not pixel-image comparison.
- Manual figures contain instructional dots, percent signs, captions, and artifacts, so **raw screenshot comparison is intentionally avoided**.

## Profile-Based Checking

The tool checks:
- Presence of required labels: `From:`, `To:`, `Subj:`, `1.`
- Optional labels if present: `Copy to:`
- Vertical ordering of headers
- Header label-column alignment for `From:` / `To:` / `Subj:` / `Copy to:`
- Label content alignment for `From:` / `To:` / `Subj:`
- Spacing tolerances

### Scope

Currently supports:
- **Figure 8-1 Multiple-Address Letter (To-line Only)** — wired into `tools/run_c8_regression.py`
- **Figure 8-2 Multiple-Address Letter (Distribution-line Only)** — wired into `tools/run_c8_regression.py`

Future profiles should cover:
- Figure 8-3 To + Distribution line
- Additional Chapter 8 letter variants as needed

## Usage

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_8_1_multiple_address_to_line.json --pdf output/audit_c8_to_only_letter.pdf
```

### Figure 8-2 Distribution-line Only

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_8_2_multiple_address_distribution_line.json --pdf output/audit_c8_distribution_only_letter.pdf
```

## Tolerances

- X tolerance: 3 points
- Y tolerance: 4 points

## Output Format

JSON-like console summary:
```
profile: docs/layout_profiles/figure_8_1_multiple_address_to_line.json
pdf:     output/audit_c8_to_only_letter.pdf
passed:  7
failed:  0
warnings: 0
```

## Profile Format

The profile JSON includes:
- `figure_id`: "8-1"
- `manual_reference`: "SECNAV M-5216.5 Figure 8-1"
- `doc_type`: "DT_MULTIPLE_ADDRESS_LETTER_TO_LINE"
- `target_pdf`: The PDF path to audit
- `required_text`: List of required label lines
- `optional_text`: List of optional label lines that may appear
- `order_rules`: Expected vertical ordering of label lines
- `alignment_groups`: Coarse x-coordinate alignment groups for label positions
- `label_content_alignment_groups`: Coarse x-coordinate alignment for text content after labels (not checked for Copy to lines)
- `spacing_tolerances`: X/Y tolerances

### Multi-Address To-Line Check

The profile verifies that multiple To addressees (e.g., "Commanding Officer, Example Receiving Activity Alpha", "Commanding Officer, Example Receiving Activity Bravo") are vertically stacked below/near the To block and aligned to the same label column as the first To line. The alignment check groups `From:`, `To:`, `Copy to:`, and `Subj:` labels together to verify consistent left-edge alignment.

Note: Copy to lines are typically single-item lists without rich text content. Content extraction may be unreliable for these lines in single-span structure.

### Multi-Address Distribution-Line Check

The Figure 8-2 profile verifies that:
- `To:` is **omitted** — action addressees are listed in the `Distribution:` block instead
- `Distribution:` appears after the signature block, not in the header area
- `Distribution:` entries appear below the `Distribution:` label
- `Distribution:` and `Copy to:` labels align to the left margin (expected ~72pt)
- `Distribution:` and `Copy to:` labels align with each other in the `distribution_label_left_margin` group
- `From:` and `Subj:` labels maintain normal header-column alignment

The `header_text_column` check only includes `From:` and `Subj:` (no `To:` because Figure 8-2 omits To line).

### Continuation Entries

If present, Figure 8-1 may include multiple To entries for addressees. The audit currently checks that all `To:` labels align with the header_label_column. Content verification for individual To entries is not performed.

If present, Figure 8-2 may include multiple `Distribution:` entries for action addressees. The audit checks that `Distribution:` and `Copy to:` labels align to the left margin and with each other. Individual distribution-entry content alignment is not checked.

## Implementation

Uses PyMuPDF (`fitz`) for text extraction:
1. Extract visible text spans/words
2. Get page number, text, x0, y0, x1, y1
3. Profile matching and rule checking

### Multi-Address Alignment

The tool checks that multiple `To:` entries (when present) are horizontally aligned within their respective groups. For each `alignment_groups` entry:
- Apply the `texts` list to extract labels from all spans
- Compare label x0 values to the first found label x0
- PASS if all labels are within `tolerance_pt`; FAIL if any are outside

This prevents body-level markers from interfering with header-level alignment checks.

## Status

- **Prototype only**
- **Figure 8-1 wired into C8 regression runner** — layout audit now runs in `tools/run_c8_regression.py`
- **Figure 8-2 wired into C8 regression runner** — layout audit now runs in `tools/run_c8_regression.py`
- **Figure 8-3 remains future work**
- Audit failure causes C8 regression failure (for wired profiles)
- Manual review still required for final compliance
- Future C8 profiles will expand coverage to Figure 8-3
