# PDF Layout Audit C9 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 9 endorsement compliance, specifically Figure 9-2 New Page Endorsement.

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
