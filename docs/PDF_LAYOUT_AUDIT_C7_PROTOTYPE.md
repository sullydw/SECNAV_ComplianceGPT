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
- Coarse vertical spacing between header/body elements
- Body paragraph placement below final header block
- Continuation-marker alignment when applicable (Ref / Encl)

### Scope

Currently supports:
- **Figure 7-1 Standard Letter (First Page)**

Future profiles can be added for:
- Figure 7-2
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
- `required_text`: ["From:", "To:", "Subj:", "1."]
- `optional_text`: ["Via:", "Ref:", "Encl:"]
- `order_rules`: Expected vertical ordering
- `alignment_groups`: Coarse x-coordinate alignment groups (e.g., `header_label_column` for `From:` / `To:` / `Subj:`)
- `label_content_alignment_groups`: Coarse x-coordinate alignment for text content after labels (e.g., `header_text_column`)
- `vertical_spacing_rules`: Coarse vertical spacing rules between header/body elements (e.g., `from_to_normal_line`, `to_subj_blank_line`)
- `alignment_rules`: Continuation marker alignment rules
- `spacing_tolerances`: X/Y tolerances

## Implementation

Uses PyMuPDF (`fitz`) for text extraction:
1. Extract visible text spans/words
2. Get page number, text, x0, y0, x1, y1
3. Profile matching and rule checking

## Status

- **Prototype only**
- Not wired into `run_c7_phase1_regression.py` yet
- Manual review still required for final compliance
