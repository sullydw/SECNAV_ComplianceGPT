# C9 Regression Checklist

## Scope
- C9 new-page endorsement Phase 1 only.
- Covers new-page endorsement heading rendering.
- Covers explicit page-number continuation for new-page endorsements.
- Covers C9-003 remaining Via behavior (single Via unnumbered, multiple Via numbered).
- Covers C9-004 reference continuation validation.
- Covers C9-005 enclosure continuation validation.
- Covers C9-006 significant Copy to expansion validation.
- Covers C9-007 complete annotation validation.
- Same-page endorsements are deferred.
- Endorsement assembly remains advisory/procedural.

## Commands
```bash
python tools/run_c9_regression.py
```

## Expected Results
- C9 regression runner PASS.
- C9 fixture PDFs render correctly for manual visual review.
- C7 Phase 1 regression runner PASS.
- C8 regression runner PASS.

## Visual Checks — C9 New-Page Endorsement
- Endorsement heading appears after sender-symbol/date block and before From line.
- Heading starts at the left margin.
- Heading reads exactly:
  ```
  SECOND ENDORSEMENT on NAS MERIDIAN ltr 5216 Ser 11/273 of 22 Apr 15
  ```
- One blank line appears after the endorsement heading before From line.
- From line appears.
- To line appears.
- Subject appears in uppercase.
- Enclosure line appears.
- Body renders normally.
- Signature block renders correctly.
- Copy to appears after signature with correct spacing.
- Page number 2 appears centered 1/2 inch from the bottom.
- Page number is shown on the first rendered endorsement page because `force_page_number_on_first_page` is true.

## Do Not Regress
- Do not infer page number from endorsement_ordinal.
  - FIRST/SECOND/THIRD identifies endorsement sequence only, not displayed page number.
- Do not apply endorsement page-number continuation to DT_STD_LTR.
- Do not affect C7/C8 pagination behavior.
- Do not remove renderer CLI input/output path support.
- Do not implement same-page endorsements as part of Phase 1.
- Do not convert C9 advisory assembly guidance into hard renderer requirements.

---

## Chapter 9 Closeout Scope

**Status:** New-page endorsement support is baseline-locked for current scope.

**Covered and protected:**
- C9 new-page endorsement heading
- Explicit page-number continuation for new-page endorsements
- C9-003 remaining Via behavior (single Via unnumbered, multiple Via numbered)
- C9-004 reference continuation validation
- C9-005 enclosure continuation validation
- C9-006 significant Copy to expansion validation
- C9-007 complete annotation validation

**Regression protection:**
- Command: `python tools/run_c9_regression.py`
- Runner includes:
  - C9 validator checks (refs/encls/Copy to)
  - C9 render checks (base new-page, single Via, multiple Via)
  - PDF existence/non-empty checks
  - C7 Phase 1 regression guard
  - C8 regression guard

**Deferred:**
- Same-page endorsements remain deferred and must not be described as implemented.
- Endorsement assembly remains advisory/procedural and is not executable renderer logic.
- Future same-page endorsement work must start as a separate phase with fixtures and checklist updates.

**Manual review:**
- Visual PDF review remains required for rendered PDFs per the visual checks above.
