# C9 Endorsement Layout Checkpoint

## Scope

- C9 endorsement regression status.
- Figure 9-2 new-page endorsement layout review.
- Figure 9-1 same-page endorsement is recorded as deferred/not implemented.
- Review was measurement/audit only.
- No renderer or profile changes were required.

## Figure 9-1 Status

- Status: deferred / not implemented.
- No Figure 9-1 PDF or layout profile exists yet.
- Same-page endorsement layout should be implemented and measured later as a separate task.

## Figure 9-2 Result

- Audit result: PASS, 11/11 checks.
- No reported layout issues.
- PDF: output/audit_c9_new_page_endorsement.pdf
- Profile: docs/layout_profiles/figure_9_2_new_page_endorsement.json

Key measured positions:
- SECOND ENDORSEMENT x=72.0, y=135.6
- From label x=72.0, y=164.4
- To label x=72.0, y=178.8
- Subj label x=72.0, y=207.6
- Encl label x=72.0, y=236.4
- first body line y=265.2
- signature/name x=306.0, y=399.6
- By direction y=414.0
- Copy to x=72.0, y=452.4

## Validation

- Figure 9-2 audit PASS
- C7 PASS
- C8 PASS
- C9 PASS
- C10 PASS

## Deferred Work

- Implement and audit Figure 9-1 same-page endorsement.
- Add Figure 9-1 fixture, renderer support if needed, and layout profile.
- Run negative/guard tests after Figure 9-1 is implemented.
