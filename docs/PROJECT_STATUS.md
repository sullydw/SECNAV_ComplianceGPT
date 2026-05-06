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
    ("SSIC_DATE", "HEADER"): 2,          # 2 lines (28.8 pt)
    ("HEADER", "BODY"): 0,               # 0 lines (0.0 pt) ← Reduced 2026-05-04
    ("BODY", "SIGNATURE"): 4,            # 4 lines (signature_gap)
    ("SIGNATURE", "COPY_TO"): 2,         # 2 lines (copy_gap)
    ("COPY_TO", "PAGE_END"): 0,
    ("CONTINUATION_HEADER", "BODY"): 1,
}
```

**Leading calculation:**
- Font size: 12 pt
- Leading: `font_size * 1.2 = 14.4 pt`

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

### Distribution Block
- Used for action addressees when applicable
- Renders after signature block and before "Copy to:"
- Label and entries aligned at left margin
- Single-column format

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

### Signature System
- Role-based rendering supported:
 - standard
 - By direction
 - Acting/title variants
- Signature block protected from orphaning (moves to next page if needed)

### Distribution vs Copy To
- Distribution = action addressees
- Copy to = informational addressees
- Distribution appears before Copy to when both are present

---

## Changelog

See `CHANGELOG.md` for version history.
