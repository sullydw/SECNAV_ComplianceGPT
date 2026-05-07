# SECNAV ComplianceGPT - Project Status

**Last Updated:** 2026-05-04  
**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT  
**Renderer:** v6 PDF (ReportLab)

---

## 1. Current Architecture

```
SECNAV_ComplianceGPT/
├── src/
│   ├── pdf_v6_render.py      # Main PDF renderer (ReportLab canvas)
│   ├── letter_model_v6.py    # ILM normalization
│   ├── body_v6_parse.py      # Body marker parsing
│   ├── body_v6_validate.py   # Body validation
│   ├── letterhead_v6_resolve.py
│   ├── layout_v6_resolve.py
│   └── ... (other v6 modules)
├── rules_v6/
│   ├── H-series.json         # Letterhead rules
│   ├── F-series.json         # Font rules
│   ├── P-series.json         # Paragraph rules
│   ├── S-series.json         # Spacing rules
│   ├── V-series.json         # Validation rules
│   └── runtime/              # Compiled JSONL rules
├── examples/
│   └── v6_sample_letter.json
├── output/                   # Generated PDFs (gitignored)
└── docs/
    └── PROJECT_STATUS.md     # This file
```

**Workflow:**
1. Load JSON payload from `examples/`
2. Normalize via `letter_model_v6.py`
3. Validate body via `body_v6_validate.py`
4. Resolve letterhead via `letterhead_v6_resolve.py`
5. Render PDF via `pdf_v6_render.py` (ReportLab)

---

## 2. Current Renderer File

**File:** `src/pdf_v6_render.py`

**Key features:**
- ReportLab canvas-based PDF generation
- Centralized `BOUNDARY_SPACINGS` dict for layout control
- H-series letterhead rendering (bold first line, smaller subsequent)
- Body paragraph rendering with marker detection (1, a, (1), (a))
- Level-based indentation (0, 24, 48, 78 pt offsets)
- Pagination with continuation headers
- Signature block placement logic
- Page numbers (page 2+)

---

## 3. Current Confirmed Boundary Values

**File:** `src/pdf_v6_render.py` - `BOUNDARY_SPACINGS` dict

```python
BOUNDARY_SPACINGS = {
    ("LETTERHEAD", "SSIC_DATE"): 1,      # 1 line (14.4 pt)
    ("SSIC_DATE", "HEADER"): 1,          # 1 line (14.4 pt)
    ("HEADER", "BODY"): 1,               # 1 line (14.4 pt)
    ("BODY", "SIGNATURE"): 4,            # 4 lines (signature_gap)
    ("SIGNATURE", "COPY_TO"): 1,         # 1 line after signature
    ("COPY_TO", "PAGE_END"): 0,
    ("CONTINUATION_HEADER", "BODY"): 1,  # 1 line after repeated Subj
}
```

**Leading calculation:**
- Font size: 12 pt
- Leading: `font_size * 1.2 = 14.4 pt`

**Vertical Spacing Model (Next-Baseline Cursor Semantics):**
- Incoming `y` is always the baseline where the next line should be drawn
- No pre-subtraction before drawing—draw at current `y`, then advance
- All spacing is applied AFTER drawing lines
- All single blank lines = exactly 1 leading unit (14.4 pt)
- Header and body use identical vertical spacing logic
- Prior spacing defects were caused by mixing baseline vs. cursor semantics
- This has been corrected as of 2026-05-07

---

## 4. Current Known PDF Output

**Output path:** `output\v6_test_letter.pdf`

**Test run:** 2026-05-04 08:29 EDT

**Build result:**
- Pages: 2
- File size: ~3.4 KB
- Status: PASS

**Debug output:**
```
DEBUG BOUNDARY: HEADER -> BODY = 0 lines (0.0 pt)
DEBUG Total pages generated: 2
=== PDF BUILD ===
PASS
```

---

## 5. Current Confirmed Behaviors

### Sender-Symbol Block
- Supports SSIC, optional originator code, or serial ("Ser X")
- Date format: D Mon YY
- Uses longest-line anchor alignment (all lines share same left start)
- One blank line between sender-symbol block and "From:" line

### Header System
- Order: From / To or Distribution / Via / Subj / Ref / Encl
- "To:" omitted when "Distribution" is used
- REF and ENCL are optional header blocks; omitted blocks leave no label and no blank placeholder
- Adjacent visible boundaries remain exactly 1 leading unit (14.4 pt): Subj→Body (no REF/ENCL), Subj→REF, Subj→ENCL (no REF), REF→Body (no ENCL), REF→ENCL, ENCL→Body

### Distribution Block
- Used for action addressees when applicable
- Placement: always after signature block
- `distribution_mode` supports:
 - `distribution_only` → replaces To line (To omitted)
 - `to_plus_distribution` → keeps To line as group title
- `distribution_layout` supports:
 - `single_column` (entries listed one per line at left margin)
 - `columns` (two-column balanced row order)
 - `paragraph` (comma-separated wrapping text)
- Label is rule-driven from model (default: "Distribution:")
- Rendering is rule-driven (no hardcoded placement/order logic)
- Validation exists for invalid/missing mode and layout values with safe fallbacks

### Subject System
- Page 1: wraps under subject text column
- Continuation pages:
 - subject repeats
 - same wrapping logic as page 1
 - correct alignment under subject text column
 - one blank line after subject block

### Body System
- Paragraph spacing finalized
- Continuation lines return to left margin
- Marker indentation preserved across levels
- Uses next-baseline cursor semantics (incoming `y` is draw baseline)
- No pre-subtraction before drawing body records
- Spacing between paragraphs = exactly 1 leading unit (14.4 pt)
- Subparagraph transitions match paragraph-to-paragraph spacing

### Signature System
- Role-based rendering supported:
 - standard
 - By direction
 - Acting/title variants
- Signature block protected from orphaning (moves to next page if needed)

### Vertical Spacing Model (Verified)
- All boundaries use next-baseline cursor semantics
- All single-line spacing = 1 leading unit (14.4 pt)
- BODY → SIGNATURE = 4 leading units
- Subj → Body may span multiple lines when Ref/Encl present (expected behavior)

### Resolved Defects
- Date → From double spacing fixed (2.0 → 1.0 leading units)
- Paragraph → subparagraph stacking fixed (3.0 → 1.0 leading units)
- Signature → Distribution stacking fixed (2.0 → 1.0 leading units)
- Distribution → Copy to stacking fixed (2.0 → 1.0 leading units)

### Validation
- Audit Agent measurement confirms baseline-to-baseline accuracy
- All tested boundaries match expected values per BOUNDARY_SPACINGS dict
- Pagination stress test (`audit_pagination_stress.json`) generated 3-page PDF with signature/distribution/copy-to staying together on page 3; no overflow below bottom margin (Y=72 pt) and no orphaning observed. Renderer pagination logic confirmed working; no changes required.

### Distribution vs Copy To
- Distribution = action addressees
- Copy to = informational addressees
- Both render after signature block
- Distribution renders before Copy to when both are present
- Both support layouts:
 - `single_column` (entries listed one per line)
 - `columns` (two-column balanced row order)
 - `paragraph` (comma-separated wrapping text)
- Copy to is informational only
- Copy to NEVER suppresses To, Via, Distribution, or other header fields
- Rendering is rule-driven:
 - placement determined by model
 - ordering determined by model
 - labels from model when provided (defaults: "Distribution:", "Copy to:")
- Model guarantees defaults for:
 - `distribution_mode` → `distribution_only` (when distribution present)
 - `distribution_layout` → `single_column`
 - `copy_to_layout` → `single_column`
- Validation exists for invalid `copy_to_layout` values with safe fallbacks

---

## 6. Output Directory Behavior

- Output path is configurable with the following priority order:
  1. `output_dir` argument (if provided)
  2. `SECNAV_OUTPUT_DIR` environment variable
  3. Default: `./output/` relative to project root
- Output directory is auto-created if missing
- No hardcoded absolute paths
- Note: OpenClaw runs may default to workspace unless overridden; local runs can redirect output via environment variable

---

## Changelog

See `CHANGELOG.md` for version history.
