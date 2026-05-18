# SECNAV ComplianceGPT - Bootstrap Guide

**For New Chats / Session Continuity**

---

## Quick Start

**Project:** SECNAV M-5216.5 compliant letter generator (v6 PDF renderer)

**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT

**Local Path:** `C:\Projects\SECNAV_ComplianceGPT`

---

## Source of Current Behavior

For all current rendering behavior and confirmed compliance decisions, see:
docs/PROJECT_STATUS.md

This file (BOOTSTRAP.md) provides architecture and setup only.

---

## Current Architecture

### Core Components

1. **PDF Renderer:** `src/pdf_v6_render.py`
   - ReportLab canvas-based PDF generation
   - Centralized `BOUNDARY_SPACINGS` dict for layout control
   - H-series letterhead, body paragraphs, signature block, pagination

2. **Rule System:** `rules_v6/`
   - H-series: Letterhead rules
   - F-series: Font rules
   - P-series: Page number rules
   - S-series: Signature block rules
   - V-series: Validation rules
   - Runtime: Compiled JSONL for production

3. **Supporting Modules:** `src/`
   - `letter_model_v6.py` - ILM normalization
   - `body_v6_parse.py` - Marker detection
   - `body_v6_validate.py` - Body validation
   - `letterhead_v6_resolve.py` - Letterhead resolution
   - `layout_v6_resolve.py` - Layout calculations

### Typography System

**Leading formula:**
```python
font_size = 12  # body font size
leading = font_size * 1.2  # line spacing with 20% extra
```

**Boundary spacings (in leading units):**
```python
BOUNDARY_SPACINGS = {
    ("LETTERHEAD", "SSIC_DATE"): 1,
    ("SSIC_DATE", "HEADER"): 2,
    ("HEADER", "BODY"): 0,
    ("BODY", "SIGNATURE"): 4,
    ("SIGNATURE", "COPY_TO"): 2,
    ("COPY_TO", "PAGE_END"): 0,
    ("CONTINUATION_HEADER", "BODY"): 1,
}
```

**Paragraph spacing:**
- Controlled by renderer logic
- Refer to docs/PROJECT_STATUS.md for current behavior

---

## Build & Test

```bash
# Run PDF generator
cd C:\Projects\SECNAV_ComplianceGPT
python src/pdf_v6_render.py

# Output: output\v6_test_letter.pdf
```

**Expected output:**
```
=== PDF BUILD ===
PASS
output\v6_test_letter.pdf
```

---

## Git Workflow

```bash
# Pull latest
git pull origin main

# Make changes, then:
git add -A
git commit -m "descriptive message"
git push origin main
```

**Current branch:** `main`

**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT

---

## Key Design Decisions

1. **Font-size-aware spacing:** All spacing uses `leading = font_size * 1.2` for scalability

2. **Centralized boundary system:** `BOUNDARY_SPACINGS` dict controls all major layout transitions

3. **No hardcoded points:** Spacing calculated from font size, not magic numbers

4. **Signature placement:** 4 lines below final body text per SECNAV M-5216.5 Ch 7

5. **Continuation pages:** Repeat subject line, omit letterhead/SSIC/header blocks

---

## Known Issues / Open Questions

1. **Rule validation:** Some rules provisional pending SECNAV M-5216.5 verification

---

## Compliance Reference

**Primary Source:** SECNAV M-5216.5 (April 2023)

**Key Chapters:**
- Chapter 2: Format and Preparation
- Chapter 7: Signature Blocks

**Rule Provenance:** All rules in `rules_v6/` include `source` and `confidence` fields

---

## Session Startup Checklist

For new chat sessions:

1. ✅ Read `docs/PROJECT_STATUS.md` for current state
2. ✅ Read `docs/BOOTSTRAP.md` (this file) for architecture overview
3. ✅ Pull latest from GitHub: `git pull origin main`
4. ✅ Verify build: `python src/pdf_v6_render.py`
5. ✅ Check `git status` for clean working tree

---

## DO NOT

- ❌ Redesign the architecture without explicit direction
- ❌ Create parallel renderers
- ❌ Hardcode spacing values (use font-size-aware math)
- ❌ Work outside `C:\Projects\SECNAV_ComplianceGPT`
- ❌ Modify rules without updating provenance

---

**Last Updated:** 2026-05-04  
**Commit:** See `git log` for latest
