# C8 Multiple-Address Letter Checkpoint

## Scope

- Figure 8-1 multiple-address letter using To line only.
- Figure 8-2 multiple-address letter using Distribution line only.
- Figure 8-3 multiple-address letter using both To and Distribution lines.
- Review was measurement/audit only.
- No renderer or profile changes were required.

## Figure 8-1 Result

- Audit result: PASS, 7/7 checks.
- No reported layout issues.
- PDF: output/audit_c8_to_only_letter.pdf
- Profile: docs/layout_profiles/figure_8_1_multiple_address_to_line.json

Key measured positions:
- From label x=72.0, y=135.6
- To label x=72.0, y=150.0
- To addressee content x=115.0
- Subj label x=72.0, y=207.6
- first body marker x=72.0, y=236.4
- signature x=306.0
- Copy to x=72.0, y=409.2

## Figure 8-2 Result

- Audit result: PASS, 9/9 checks.
- No reported layout issues.
- PDF: output/audit_c8_distribution_only_letter.pdf
- Profile: docs/layout_profiles/figure_8_2_multiple_address_distribution_line.json

Key measured positions:
- From label x=72.0, y=135.6
- To line present: no
- Subj label x=72.0, y=164.4
- first body marker x=72.0, y=193.2
- signature x=306.0
- Distribution label x=72.0, y=356.4
- Distribution entries x=72.0
- Copy to x=72.0, y=466.8

## Figure 8-3 Result

- Audit result: PASS, 9/9 checks.
- No reported layout issues.
- PDF: output/audit_c8_to_plus_distribution_letter.pdf
- Profile: docs/layout_profiles/figure_8_3_multiple_address_to_distribution.json

Key measured positions:
- From label x=72.0, y=135.6
- To label x=72.0, y=150.0
- To content x=115.0, y=150.0
- Subj label x=72.0, y=178.8
- first body marker x=72.0, y=207.6
- signature x=306.0
- Distribution label x=72.0, y=370.8
- Distribution entries x=72.0
- Copy to x=72.0, y=466.8

## Validation

- Figure 8-1 audit PASS
- Figure 8-2 audit PASS
- Figure 8-3 audit PASS
- C7 PASS
- C8 PASS
- C9 PASS
- C10 PASS
