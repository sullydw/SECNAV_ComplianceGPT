# PDF Layout Audit C8 Prototype

## Overview

This is a **prototype** PDF layout audit tool for checking SECNAV M-5216.5 Chapter 8 multiple-address letter compliance, specifically Figure 8-1 Multiple-Address Letter Using To: Line.

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
- Optional labels if present: `Copy to:`
- Vertical ordering of headers
- Header label-column alignment for `From:` / `To:` / `Subj:` / `Copy to:`
- Label content alignment for `From:` / `To:` / `Subj:`
- Spacing tolerances

### Scope

Currently supports:
- **Figure 8-1 Multiple-Address Letter (To-line Only)** — wired into `tools/run_c8_regression.py`
- **Figure 8-2 Multiple-Address Letter (Distribution-line Only)** — wired into `tools/run_c8_regression.py`
- **Figure 8-3 Multiple-Address Letter (To + Distribution line)** — wired into `tools/run_c8_regression.py`

Future profiles should cover:
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
- `forbidden_text`: List of text strings that must NOT appear in the PDF (e.g., `"To:"` in a Distribution-only letter)
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
- **`To:` is forbidden** — if `"To:"` appears anywhere in the PDF, the audit fails

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
- **Figure 8-3 wired into C8 regression runner** — layout audit now runs in `tools/run_c8_regression.py`
- Audit failure causes C8 regression failure (for all wired profiles)
- Manual review still required for final compliance
