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

## 5. Current Known Issue: Body Paragraph Spacing

**Issue:** Paragraphs still appear visually too far apart despite code fix.

**What was done (2026-05-04):**
- Changed from "spacing after paragraph" to "spacing before paragraph"
- Applied `y -= leading` only when `i > 0` (skip first paragraph)
- Removed duplicate spacing that was applied both before AND after

**Current code:**
```python
# Add one blank line before this paragraph (except for first paragraph)
if i > 0:
    y -= leading
```

**Suspected causes:**
1. Leading value (14.4 pt) may be too large for visual single-spacing
2. Each body record may still be drawing extra `y -= leading` after continuation lines
3. Font-size vs leading ratio needs adjustment (currently 12pt font, 14.4pt leading = 20% extra)

**Next debugging step:**
- Verify actual rendered line spacing in PDF viewer
- Consider reducing leading to `font_size * 1.0` for true single-spacing
- Check if continuation lines add extra spacing

---

## 6. Next Strategic Direction

**Consideration:** HTML/CSS renderer as alternative to ReportLab PDF

**Rationale:**
- CSS provides more intuitive spacing control (`line-height`, `margin`, `padding`)
- Easier visual debugging via browser dev tools
- Can still export to PDF via headless browser (Playwright, Puppeteer)
- Better support for complex layouts, tables, responsive design

**Decision:**
- Do NOT replace current `pdf_v6_render.py` yet
- Continue debugging spacing issues in ReportLab renderer
- If spacing issues persist, prototype HTML/CSS renderer in parallel
- Maintain both renderers until HTML approach is proven

**If HTML renderer is pursued:**
- Create `src/html_v6_render.py`
- Use same `letter_model_v6.py` normalization
- Output to `output/v6_test_letter.html`
- Optional: PDF export via Playwright

---

## 7. OpenClaw Workflow Rule

**Standard operating procedure:**

1. **Edit:** OpenClaw edits files in `C:\Projects\SECNAV_ComplianceGPT` only
2. **Build/Test:** Run `python src/pdf_v6_render.py` to verify
3. **Commit:** `git add -A && git commit -m "descriptive message"`
4. **Push:** `git push origin main`
5. **Report:** Return commit hash, build output, any errors

**Do NOT:**
- Work in `.openclaw` workspace for this project
- Create parallel replacement projects
- Edit files outside `C:\Projects\SECNAV_ComplianceGPT` unless instructed
- Restart architecture without explicit direction

---

## Changelog

See `CHANGELOG.md` for version history.
