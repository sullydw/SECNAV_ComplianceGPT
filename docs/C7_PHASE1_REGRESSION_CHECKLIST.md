# C7 Phase 1 Regression Checklist

Created: 2026-05-15  
Repo: https://github.com/sullydw/SECNAV_ComplianceGPT  
Fixture: `examples/audit_c7_phase1_standard_letter.json`

---

## Commands

Run these commands to verify C7 Phase 1 baseline integrity:

```bash
python src/body_v6_validate.py examples/audit_c7_phase1_standard_letter.json
python src/pdf_v6_render.py examples/audit_c7_phase1_standard_letter.json output/audit_c7_phase1_standard_letter.pdf
python src/pdf_v6_render.py
```

---

## Expected Results

- Body validation: PASS
- C7 fixture render: PASS
- Default render: PASS
- C7 fixture PDF: 3 pages (unless intentional fixture/layout changes are made)

---

## Visual Checks

After rendering `output/audit_c7_phase1_standard_letter.pdf`:

### Header Content
- [ ] `From` line appears
- [ ] `To` line uses activity/title addressee (not bare name)
- [ ] `Via` line uses activity/title addressee (not bare name)
- [ ] `Subj` line appears
- [ ] `Ref` entries appear (if present)
- [ ] `Encl` entries appear (if present)

### Subject Formatting
- [ ] Subject is uppercase on page 1
- [ ] Subject repeats on continuation pages (page 2+)
- [ ] One blank line between continuation subject and resumed content

### Ref/Encl Markers
- [ ] Ref entries are marked (a), (b)
- [ ] Encl entries are marked (1), (2)

### SSIC/Sender-Symbol Block
- [ ] SSIC/sender-symbol block alignment is correct
- [ ] One blank line between SSIC/date block and `From` line

### Paragraph/Subparagraph Alignment
- [ ] One blank line between parent paragraph and child subparagraph
- [ ] Subparagraph markers are not too far right
- [ ] Marker-to-text gap remains correct (~2 spaces)
- [ ] Wrapped body continuation lines return to left margin

### Pagination
- [ ] Page numbers begin on page 2
- [ ] Page numbers are centered near bottom

### Signature/Copy To
- [ ] Signature block has correct spacing
- [ ] `Copy to` appears after signature with correct spacing

---

## Do Not Regress

When making renderer changes, ensure you do NOT:

- [ ] Remove renderer CLI input/output path support
- [ ] Reintroduce global paragraph sequence validation
- [ ] Suppress To line in standard-letter fixture
- [ ] Treat debug-output-only audit as final visual proof
- [ ] Modify rule files for renderer regression fixes

---

## Notes

- C7 Phase 1 is a **visual smoke audit baseline** for the renderer
- Visual proof via PDF review is required; do not skip actual PDF inspection
- This checklist prevents future changes from breaking C7 Phase 1 rendering behavior
