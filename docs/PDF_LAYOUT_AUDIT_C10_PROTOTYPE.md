# PDF Layout Audit C10 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 10 Memorandum for the Record (MFR) compliance, specifically Figure 10-1 Memorandum for the Record.

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
- Vertical spacing between `MEMORANDUM` and `From:` is approximately 28.8pt (tolerance 4pt)
- Vertical spacing between `Subj:` and `1.` is approximately 28.8pt (tolerance 4pt)
- Date appears right-aligned in the top-right area

### From-To Plain with References Check

The Figure 10-3 with references profile verifies that:
- `MEMORANDUM` heading appears at the left margin
- `From:`, `To:`, `Subj:`, and `Ref:` labels are vertically ordered
- `From:`, `To:`, `Subj:`, `Ref:` labels align in the same label column
- `Subj:` and `Ref:` text aligns at the header text column
- Reference continuation markers `(a)` and `(b)` align
- Body paragraph `1.` appears after `Ref:`
- Vertical spacing between `MEMORANDUM` and `From:` is approximately 28.8pt (tolerance 4pt)
- Vertical spacing between `Subj:` and `Ref:` is approximately 28.8pt (tolerance 4pt)
- Vertical spacing between `Ref:` and `1.` is approximately 43.2pt (tolerance 4pt)
- Date appears right-aligned in the top-right area

### From-To Plain with Enclosures Check

The Figure 10-3 with enclosures profile verifies that:
- `MEMORANDUM` heading appears at the left margin
- `From:`, `To:`, `Subj:`, and `Encl:` labels are vertically ordered
- `From:`, `To:`, `Subj:`, `Encl:` labels align in the same label column
- `Subj:` and `Encl:` text aligns at the header text column
- Enclosure continuation markers `(1)` and `(2)` align
- Body paragraph `1.` appears after `Encl:`
- Vertical spacing between `MEMORANDUM` and `From:` is approximately 28.8pt (tolerance 4pt)
- Vertical spacing between `Subj:` and `Encl:` is approximately 28.8pt (tolerance 4pt)
- Vertical spacing between `Encl:` and `1.` is approximately 43.2pt (tolerance 4pt)
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
