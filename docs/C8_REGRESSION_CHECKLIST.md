# C8 Regression Checklist

## Scope

- C8-002 To-line-only format
- C8-003 Distribution-only format
- C8-004 To + Distribution format
- C8-005 and C8-006 remain advisory/procedural and are not hard renderer requirements yet.

## Commands

```
python src/pdf_v6_render.py examples/audit_c8_to_only_letter.json output/audit_c8_to_only_letter.pdf
python src/pdf_v6_render.py examples/audit_c8_distribution_only_letter.json output/audit_c8_distribution_only_letter.pdf
python src/pdf_v6_render.py examples/audit_c8_to_plus_distribution_letter.json output/audit_c8_to_plus_distribution_letter.pdf
python tools/run_c7_phase1_regression.py
```

## Expected Results

- C8 To-line-only render PASS
- C8 Distribution-only render PASS
- C8 To + Distribution render PASS
- C7 Phase 1 regression runner PASS
- Each C8 fixture PDF is 1 page unless intentional fixture/layout changes are made.

## Visual Checks — C8 To-line-only

- To label appears once.
- First To addressee appears on the same line as To.
- Additional To addressees are stacked below.
- Additional To addressees align under the first To addressee text.
- No Distribution line appears.
- No Via line appears.
- No Python list brackets or quotes appear.
- Copy to appears after signature when present.

## Visual Checks — C8 Distribution-only

- No To line appears.
- From line appears.
- Distribution block appears after signature.
- Distribution label is "Distribution:".
- Distribution addressees are listed in single column.
- Copy quantity notation such as "(4 copies)" is preserved.
- Copy to appears separately after Distribution when present.

## Visual Checks — C8 To + Distribution

- To line appears.
- To line contains the group title.
- Distribution block appears after signature.
- Distribution entries list individual members/addressees.
- Copy to may appear separately after Distribution.
- No unwanted Via, Ref, or Encl placeholders appear.

## Do Not Regress

- Do not remove renderer CLI input/output path support.
- Do not break C7 Phase 1 regression.
- Do not suppress To line except in Distribution-only mode.
- Do not render list values as Python list strings.
- Do not convert C8-005/C8-006 advisory assembly rules into hard renderer requirements yet.
- Do not modify rule files for renderer regression fixes.
