# C10 MFR Visual Review Checklist

**Phase:** 1D (Visual Review)  
**Date:** 2026-05-18  
**Status:** Manual Review Required

---

## Purpose

This checklist documents the visual review criteria for Memorandum for the Record (MFR) rendering. Manual visual inspection of rendered PDFs is required before C10 MFR rendering is considered baseline-locked.

---

## Fixtures Under Review

| Fixture | Output PDF | Subject |
|---------|------------|---------|
| `examples/audit_c10_mfr_with_subject.json` | `output/audit_c10_mfr_with_subject.pdf` | Present |
| `examples/audit_c10_mfr_short_no_subject.json` | `output/audit_c10_mfr_short_no_subject.pdf` | Omitted |

---

## Visual Checks

### Structure Checks (Both Fixtures)

- [ ] **No letterhead appears** — MFR is plain-paper format; no H-series letterhead block at top
- [ ] **No SSIC/originator block appears** — No right-aligned SSIC, serial, or originator code block
- [ ] **No From/To/Via/Ref/Encl stack appears** — MFR bypasses standard letter header entirely
- [ ] **Date appears near top left** — Date line at left margin (x=72pt), near top of page
- [ ] **`MEMORANDUM FOR THE RECORD` is centered** — Title centered horizontally on page
- [ ] **Body paragraphs render with normal paragraph markers** — Markers like "1. ", "2. ", "a. " appear correctly
- [ ] **Signer name appears at center-start** — Signer name centered horizontally (x=page_width/2)
- [ ] **Signer org code appears below signer name** — Org code on line immediately below signer name
- [ ] **No Copy to or Distribution block appears** — MFR has no distribution or copy-to addressees
- [ ] **Page number behavior is acceptable** — Page number appears on final page (if multi-page) or omitted for single-page MFR

### With-Subject Fixture Only

- [ ] **Subject appears below title** — `Subj:` line present with subject text
- [ ] **Subject text wraps correctly** — Long subjects wrap to continuation lines aligned under first text character

### Short No-Subject Fixture Only

- [ ] **No subject line appears** — `Subj:` line completely omitted
- [ ] **No blank `Subj:` placeholder appears** — No empty subject line or placeholder text

---

## Spacing Checks

- [ ] **One blank line between date and title** — Proper vertical spacing
- [ ] **One blank line between title and subject (if present)** — Proper vertical spacing
- [ ] **One blank line between subject (or title) and body** — Proper vertical spacing before body
- [ ] **Four blank lines (signature_gap) between final body text and signer** — Proper signature spacing
- [ ] **One blank line between signer name and org code** — Proper signer block spacing

---

## Font Checks

- [ ] **Title uses 14pt Times-Bold** — `MEMORANDUM FOR THE RECORD` in bold, larger font
- [ ] **Body uses 12pt Times-Roman** — Standard body font
- [ ] **Signer name and org code use 12pt Times-Roman** — Consistent with body font

---

## Known Limitations (Phase 1D)

- [ ] **Continuation page handling not yet tested** — Multi-page MFR with body overflow not yet validated
- [ ] **Subj: repetition on page 2** — If body overflows to page 2, `Subj:` may repeat (acceptable for Phase 1D)
- [ ] **No endorsement support** — MFR endorsements are out of scope for Phase 1D

---

## Review Status

| Check Category | Status | Notes |
|----------------|--------|-------|
| Structure | ⏳ Pending | Manual review required |
| Spacing | ⏳ Pending | Manual review required |
| Fonts | ⏳ Pending | Manual review required |
| With-Subject Fixture | ⏳ Pending | Manual review required |
| No-Subject Fixture | ⏳ Pending | Manual review required |

---

## Next Phase (1E)

After visual review passes:

1. Document any spacing or layout adjustments needed
2. Implement fixes in `src/pdf_v6_render.py`
3. Re-run regression and visual review
4. Lock C10 MFR rendering baseline

---

## Manual Review Instructions

1. Open `output/audit_c10_mfr_with_subject.pdf` in PDF viewer
2. Open `output/audit_c10_mfr_short_no_subject.pdf` in PDF viewer
3. Check each item in this checklist
4. Mark status table above with results
5. Report any discrepancies for Phase 1E fixes

---

**Note:** This checklist is for manual visual review only. Automated checks are limited to PDF existence and non-empty validation in `tools/run_c10_regression.py`.
