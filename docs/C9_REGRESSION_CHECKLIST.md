# C9 Regression Checklist

## Scope
- C9 new-page endorsement Phase 1 only.
- Covers new-page endorsement heading rendering.
- Covers explicit page-number continuation for new-page endorsements.
- Same-page endorsements are not implemented yet.
- C9 reference/enclosure sequence validation is not implemented yet.
- C9 copy-to significance/complete annotation logic is not implemented yet.
- C9 assembly remains advisory/procedural.

## Commands
```bash
python src/pdf_v6_render.py examples/audit_c9_new_page_endorsement.json output/audit_c9_new_page_endorsement.pdf
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
```

## Expected Results
- C9 new-page endorsement render PASS.
- C7 Phase 1 regression runner PASS.
- C8 regression runner PASS.
- C9 fixture PDF is 1 generated page unless intentional fixture/layout changes are made.

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
