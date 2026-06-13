# Phase L.7 — Conversational Builder Interactive CLI Prototype Checkpoint

## Decision

Phase L.7 adds an isolated interactive CLI prototype for the conversational builder workflow.

The implementation remains intentionally narrow:

- key-value input only
- no natural-language parsing
- no GUI
- no production command-layer integration
- no renderer/layout changes
- no CCI config or severity changes
- no validator or catalog changes
- no PDF files committed
- no error promotion

## Files Changed

- `tools/run_phase_l7_conversational_builder_cli.py` — new CLI prototype wrapper around `BuilderSession`
- `tools/run_phase_l7_conversational_builder_cli_regression.py` — new scripted regression runner for CLI/session behavior
- `docs/checkpoints/phase_l7_conversational_builder_interactive_cli_checkpoint.md` — this checkpoint

## CLI Behavior

The CLI starts a `BuilderSession`, prints the next needed question, accepts key-value input, and routes every answer through `BuilderSession.ingest_user_message()`.

Supported interactive commands:

- `/status` — print the current payload JSON
- `/warnings` — print the structured validation summary and plain-English warning details
- `/accept-warnings` — allow the next finalize attempt to accept pending warnings
- `/revise` — keep the session open for corrected key-value input
- `/finalize` — finalize the normalized payload if allowed
- `/quit` — exit

The CLI does not render a PDF. It reports PDF dependency status only:

- `skipped` when `reportlab` or `fitz/PyMuPDF` is unavailable
- `available_not_run` when dependencies are present, because L.7 does not render or write PDFs

## Scripted Regression Coverage

The new L.7 regression runner exercises CLI behavior without manual input.

Covered expectations:

1. CLI script exists.
2. CLI exposes `run_interactive()`.
3. CLI exposes `run_scripted_sample()`.
4. CLI exposes `pdf_dependency_status()`.
5. Scripted accept-warnings path finalizes.
6. Scripted payload is valid JSON.
7. Payload preserves `doc_type=standard_letter`.
8. Audit schema is `CCI_AUDIT_V1`.
9. Validation summary is structured.
10. Warning summary is a list.
11. PDF dependency result is non-failing.
12. Scripted revise path does not finalize.
13. Scripted revise path records `action=revise`.
14. Scripted revise path returns current payload.
15. Scripted revise path returns transcript.
16. Subprocess scripted CLI exits zero with `--accept-warnings`.
17. Subprocess JSON parses successfully.
18. Subprocess payload preserves builder version.
19. PDF dependency status has a reason.
20. Renderer/layout/config protected files remain unchanged.

## Regression Results

Not executed in this GitHub connector session. The files were created directly through GitHub contents operations, so local Python dependencies and the repo-local regression gate were not available here.

Required local runs before declaring full local completion:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l4_conversational_builder_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l5_conversational_builder_validation_summary_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l6_builder_payload_to_pdf_dry_run.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_k3_subject_terminal_punctuation_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h13_config_regression.py
```

Also run the full non-PDF gate through the existing project command if available.

## Known Environment Limitation

The prior L.6 checkpoint reported that PDF render/layout suites C7/C8/C9/C10 fail in the current environment when `reportlab` or `fitz/PyMuPDF` is unavailable. L.7 does not change renderer behavior and does not require PDF dependencies.

## Explicit Non-Changes

- No renderer/layout files changed.
- No CCI config/severity files changed.
- No validators changed.
- No catalogs changed.
- No Phase F/G command-layer files changed.
- No intake policy/question JSON files changed.
- No generated PDF committed.
- No logs or unsanitized material committed.
- No error promotion authorized or performed.
- `docs/BOOTSTRAP.md` was not modified.
- `docs/HERMES_INSTRUCTIONS.md` was not modified.

## Recommended Next Phase

`Phase L.7A — Local Regression Verification for Conversational Builder CLI`

Rationale: L.7 was implemented through direct GitHub contents operations, so local regression execution should be captured separately before moving to L.8 demo-script work.

After L.7A passes, proceed to:

`Phase L.8 — Conversational Builder User-Facing Demo Script`
