# Phase L.7A — Conversational Builder CLI Local Verification Checkpoint

## Date
2026-06-12

## Baseline
Latest GitHub commit: `3961e153 Docs: Add L.7 CLI prototype checkpoint`
Local after pull: `3961e153`

## Files Verified Present
- `tools/run_phase_l7_conversational_builder_cli.py`
- `tools/run_phase_l7_conversational_builder_cli_regression.py`
- `docs/checkpoints/phase_l7_conversational_builder_interactive_cli_checkpoint.md`

## Regression Results

| Runner | Result |
|--------|--------|
| L.4 conversational builder | 41/41 PASS |
| L.5 validation summary | 36/36 PASS |
| L.6 payload-to-PDF dry run | 6/7 PASS (PDF generated but renderer hit pre-existing signature-block error with sanitized payload; not a new regression) |
| L.7 CLI regression | 26/26 PASS |
| K.3 SUBJ-002 terminal punctuation | 11/11 PASS |
| H.13 config regression | 27/27 PASS |
| H.4 routing office-code validator | 18/18 PASS |
| H.6 routing office-code evidence | 15/15 PASS |
| H.16 ROUTE-011 burn-in | 96/96 PASS |
| H.24 ROUTE-011 sanitized fixtures | 36/36 PASS (32 fixtures + 4 sub-runners) |
| Intake regression | All PASS |

## L.7 CLI Regression Checks
- `cli_file_exists` — module spec loads, exposes `run_interactive()`, `run_scripted_sample()`, `pdf_dependency_status()`
- `scripted_accept_path` — accept-warnings path finalizes, payload JSON valid, doc_type preserved, audit CCI_AUDIT_V1, validation summary structured, warning summary list, PDF status non-failing
- `scripted_revise_path` — revise path does not finalize, revise action recorded, payload and transcript returned
- `subprocess_scripted_json` — subprocess exit 0 with accept-warnings, finalized true, builder version preserved, PDF status non-failing
- `pdf_dependency_status` — status does not fail, has reason
- `no_renderer_or_config_mutation` — renderer/layout/config files unchanged relative to HEAD

## Constraints Verified
- No renderer/layout files changed
- No CCI config/severity changed
- No validator/catalog changed
- No Phase F/G command-layer changed
- No intake policy/questions JSON modified
- No error promotion authorized
- No generated PDFs committed
- No logs or unsanitized material committed
- `docs/BOOTSTRAP.md` untouched
- `docs/HERMES_INSTRUCTIONS.md` untouched

## Decision
L.7A local verification PASS. L.7 CLI prototype is confirmed stable on local environment. Recommended next phase: `Phase L.8 Conversational Builder Usability Review and Question-Coverage Audit`.
