# PDF Layout Audit C10 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 10 Memorandum for the Record (MFR) compliance, specifically Figure 10-1 Memorandum for the Record.

## Important Notes

- **This is a prototype only**, not a replacement for manual visual review.
- **Figure comparison is rule/profile-based**, not pixel-image comparison.
- Manual figures contain instructional dots, percent signs, captions, and artifacts, so **raw screenshot comparison is intentionally avoided**.

## Profile-Based Checking

The tool checks:
- Presence of required labels: `MEMORANDUM FOR THE RECORD`, `Subj:`, `1.`
- Vertical ordering of elements
- Header label-column alignment
- Label content alignment for `Subj:`
- Spacing tolerances

### Scope

Currently supports:
- **Figure 10-1 Memorandum for the Record** — wired into C10 regression; audit failure fails C10 regression
- **Figure 10-3 Plain-Paper From-To (Basic)** — wired into C10 regression; audit failure fails C10 regression
- **Figure 10-3 Plain-Paper From-To (With References)** — wired into C10 regression; audit failure fails C10 regression
- **Figure 10-3 Plain-Paper From-To (With Enclosures)** — wired into C10 regression; audit failure fails C10 regression

Future profiles should cover:
- Figure 10-2 (if applicable)
- Additional Chapter 10 variants as needed

## Usage

### Figure 10-1 MFR (Standalone)

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_10_1_mfr.json --pdf output/audit_c10_mfr_with_subject.pdf
```

### Figure 10-3 Plain-Paper From-To With References

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_10_from_to_plain_with_refs.json --pdf output/audit_c10_from_to_plain_with_refs.pdf
```

### Figure 10-3 Plain-Paper From-To With Enclosures

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_10_from_to_plain_with_encls.json --pdf output/audit_c10_from_to_plain_with_encls.pdf
```

### Figure 10-3 Plain-Paper From-To Basic

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_10_from_to_plain_basic.json --pdf output/audit_c10_from_to_plain_basic.pdf
```

## Tolerances

- X tolerance: 3 points
- Y tolerance: 4 points

## Output Format

JSON-like console summary:
```
profile: docs/layout_profiles/figure_10_1_mfr.json
pdf:     output/audit_c10_mfr_with_subject.pdf
passed:  N
failed:  0
warnings: 0
```

## Profile Format

The profile JSON includes:
- `figure_id`: "10-1"
- `manual_reference`: "SECNAV M-5216.5 Figure 10-1"
- `doc_type`: "DT_MEMORANDUM_FOR_THE_RECORD"
- `target_pdf`: The PDF path to audit
- `required_text`: List of required label lines
- `optional_text`: List of optional label lines that may appear
- `order_rules`: Expected vertical ordering of label lines
- `alignment_groups`: Coarse x-coordinate alignment groups for label positions
- `label_content_alignment_groups`: Coarse x-coordinate alignment for text content after labels
- `spacing_tolerances`: X/Y tolerances

### MFR Check

The Figure 10-1 profile verifies that:
- `MEMORANDUM FOR THE RECORD` heading appears at the left margin
- `Subj:` appears after the heading with correct alignment
- Body paragraph `1.` appears after `Subj:`
- Date appears right-aligned in the top-right area

### From-To Plain Check

The Figure 10-3 basic profile verifies that:
- `MEMORANDUM` heading appears at the left margin
- `From:`, `To:`, and `Subj:` labels are vertically ordered
- `From:`, `To:`, `Subj:` labels align in the same label column
- `Subj:` text aligns at the header text column (content alignment is checked only for `Subj:` because `From:` and `To:` render as single-span label+content lines)
- Body paragraph `1.` appears after `Subj:`
- Date appears right-aligned in the top-right area

### From-To Plain with References Check

The Figure 10-3 with references profile verifies that:
- `MEMORANDUM` heading appears at the left margin
- `From:`, `To:`, `Subj:`, and `Ref:` labels are vertically ordered
- `From:`, `To:`, `Subj:`, `Ref:` labels align in the same label column
- `Subj:` and `Ref:` text aligns at the header text column
- Reference continuation markers `(a)` and `(b)` align
- Body paragraph `1.` appears after `Ref:`
- Date appears right-aligned in the top-right area

### From-To Plain with Enclosures Check

The Figure 10-3 with enclosures profile verifies that:
- `MEMORANDUM` heading appears at the left margin
- `From:`, `To:`, `Subj:`, and `Encl:` labels are vertically ordered
- `From:`, `To:`, `Subj:`, `Encl:` labels align in the same label column
- `Subj:` and `Encl:` text aligns at the header text column
- Enclosure continuation markers `(1)` and `(2)` align
- Body paragraph `1.` appears after `Encl:`
- Date appears right-aligned in the top-right area

## Implementation

Uses PyMuPDF (`fitz`) for text extraction:
1. Extract visible text spans/words
2. Get page number, text, x0, y0, x1, y1
3. Profile matching and rule checking

## Status

- **Prototype only**
- **Figure 10-1 and all Figures 10-3 (basic, with references, and with enclosures) wired into C10 regression** — audit failure causes C10 regression failure
- Manual review still required for final compliance
