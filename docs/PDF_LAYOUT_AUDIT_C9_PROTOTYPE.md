# PDF Layout Audit C9 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 9 endorsement compliance, specifically Figure 9-2 New Page Endorsement.

## Important Notes

- **This is a prototype only**, not a replacement for manual visual review.
- **Figure comparison is rule/profile-based**, not pixel-image comparison.
- Manual figures contain instructional dots, percent signs, captions, and artifacts, so **raw screenshot comparison is intentionally avoided**.

## Profile-Based Checking

The tool checks:
- Presence of required labels: `SECOND ENDORSEMENT`, `From:`, `To:`, `Subj:`, `Encl:`, `1.`, `Copy to:`
- Vertical ordering of headers
- Header label-column alignment for `From:` / `To:` / `Subj:` / `Encl:`
- Label content alignment for `From:` / `To:` / `Subj:` / `Encl:`
- Page number placement (bottom center)
- Spacing tolerances

### Scope

Currently supports:
- **Figure 9-2 New Page Endorsement** — wired into `tools/run_c9_regression.py`

Future profiles should cover:
- Same-page endorsements (deferred)
- Additional C9 endorsement variants as needed

## Usage

### Figure 9-2 New Page Endorsement (Standalone)

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_9_2_new_page_endorsement.json --pdf output/audit_c9_new_page_endorsement.pdf
```

## Tolerances

- X tolerance: 3 points
- Y tolerance: 4 points

## Output Format

JSON-like console summary:
```
profile: docs/layout_profiles/figure_9_2_new_page_endorsement.json
pdf:     output/audit_c9_new_page_endorsement.pdf
passed:  N
failed:  0
warnings: 0
```

## Profile Format

The profile JSON includes:
- `figure_id`: "9-2"
- `manual_reference`: "SECNAV M-5216.5 Figure 9-2"
- `doc_type`: "DT_NEW_PAGE_ENDORSEMENT"
- `target_pdf`: The PDF path to audit
- `required_text`: List of required label lines
- `optional_text`: List of optional label lines that may appear
- `order_rules`: Expected vertical ordering of label lines
- `alignment_groups`: Coarse x-coordinate alignment groups for label positions
- `label_content_alignment_groups`: Coarse x-coordinate alignment for text content after labels
- `page_number_rules`: Page number placement rules (bottom center)
- `spacing_tolerances`: X/Y tolerances

### New-Page Endorsement Check

The Figure 9-2 profile verifies that:
- The endorsement heading (`SECOND ENDORSEMENT on ...`) appears before header labels
- `From:`, `To:`, `Subj:`, `Encl:` labels align to the header label column
- `Encl:` appears before body paragraph `1.`
- Page number `2` appears bottom-centered on the page
- `Copy to:` appears after the signature block

## Implementation

Uses PyMuPDF (`fitz`) for text extraction:
1. Extract visible text spans/words
2. Get page number, text, x0, y0, x1, y1
3. Profile matching and rule checking

## Status

- **Prototype only**
- **Figure 9-2 wired into C9 regression runner** — layout audit now runs in `tools/run_c9_regression.py`
- Audit failure causes C9 regression failure (for wired profiles)
- Manual review still required for final compliance
- Same-page endorsements remain deferred
