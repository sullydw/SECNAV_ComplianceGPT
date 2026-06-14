# Phase L.12 — Conversational Builder End-to-End User Demo Checkpoint

## Decision

Phase L.12 artifacts were created to demonstrate the current conversational builder end-to-end path:

blank/session start -> key-value intake -> warning review -> accept warnings -> finalize -> `/render` -> PDF output attempt.

This phase is documentation/demo support only. No renderer, validator, CCI config, catalog, Phase F/G command-layer, or intake policy/question behavior was modified.

## Files Created

- `docs/demo/conversational_builder_end_to_end_demo.md`
- `tools/run_phase_l12_conversational_builder_end_to_end_demo.py`
- `docs/checkpoints/phase_l12_conversational_builder_end_to_end_demo_checkpoint.md`

## Demo Flow

The user-facing demo uses the existing CLI:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli.py
```

Sample key-value fields:

```text
ssic: 5216
date: 13 Jun 26
from: Commanding Officer, Example Command
to: Commander, Example Group
subj: TRAINING PLAN
body: This letter provides the proposed training plan.
signature.name: J. Q. Sample
signature.role: Commanding Officer
window_envelope: no
```

Then:

```text
/status
/warnings
/accept-warnings
/finalize
/render output/demo_builder_letter.pdf
/quit
```

## Expected Behavior

- CLI starts a `BuilderSession`.
- Required fields are captured through key-value input.
- Signature is stored as a structured dict.
- `/warnings` displays validation findings.
- `/accept-warnings` allows warning-pilot findings to be accepted.
- `/finalize` prints normalized payload JSON.
- `/render <output.pdf>` invokes the existing `src/pdf_v6_render.py` subprocess path.
- Generated demo PDFs remain local artifacts and are not committed.

## Scripted Demo Runner

New runner:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l12_conversational_builder_end_to_end_demo.py
```

Runner coverage:

- scripted session finalizes after accepting warnings;
- audit schema is `CCI_AUDIT_V1`;
- finalized payload is JSON serializable;
- structured signature dict is present;
- required sample fields are present;
- validation summary exists;
- warning summary is a list;
- render result returns structured status;
- generated PDF is deleted before exit if created;
- renderer/layout files remain untouched;
- CCI config/severity files remain untouched;
- no generated PDFs/logs remain in git diff.

## Regression Status

Regressions were not executed in this direct GitHub artifact creation pass. They must be run locally in Phase L.12A.

Recommended local commands:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l12_conversational_builder_end_to_end_demo.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l11_builder_pdf_export_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l10_conversational_builder_demo_script.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l9_conversational_builder_question_text_signature_capture_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l6_builder_payload_to_pdf_dry_run.py
```

Also run H.13 config, K.3 subject punctuation, and intake regression if practical.

## Explicit Prohibitions Observed

- No renderer/layout changes.
- No CCI config/severity changes.
- No rule promotion.
- No validator/catalog changes.
- No Phase F/G command-layer changes.
- No intake policy/questions JSON changes.
- No generated PDFs committed.
- No logs or unsanitized material committed.
- `docs/BOOTSTRAP.md` not read or modified.
- `docs/HERMES_INSTRUCTIONS.md` not modified.

## Known Limitations

- Key-value input only.
- No natural-language parsing.
- No GUI.
- The demo uses synthetic command data.
- Generated PDFs are local review artifacts only.

## Recommended Next Phase

`Phase L.12A — Local End-to-End Demo Verification and Tracker Sync`

Purpose:

- pull the direct GitHub L.12 artifacts locally;
- run the L.12 demo runner and related regressions;
- confirm generated PDF cleanup;
- update `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` safely from the local full file contents.

---

End of Phase L.12 checkpoint.
