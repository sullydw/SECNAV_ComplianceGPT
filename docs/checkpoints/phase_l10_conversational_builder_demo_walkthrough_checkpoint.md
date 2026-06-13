# Phase L.10 Conversational Builder Demo Script and Operator Walkthrough Checkpoint

**Date:** 2026-06-13  
**Commit:** `d034b06` (L.9 baseline)  
**Phase:** L.10  
**Purpose:** Create operator-facing demo script and walkthrough for the conversational builder CLI.

---

## Artifacts Created

| Artifact | Path | Type |
|----------|------|------|
| Walkthrough | `docs/demo/conversational_builder_cli_walkthrough.md` | Documentation |
| Demo runner | `tools/run_phase_l10_conversational_builder_demo_script.py` | Test/demo script |

---

## Walkthrough Contents

1. **How to run** — CLI invocation command
2. **Sample input sequence** — 9 key-value lines from `ssic` through `window_envelope`
3. **Expected behavior** — Table showing what happens at each step
4. **Common commands** — `/status`, `/warnings`, `/accept-warnings`, `/revise`, `/finalize`, `/quit`
5. **Structured signature capture** — `signature.name`, `signature.role`, `signature.title` with backward-compat note
6. **Limitations** — Key-value only, no NL parsing, no GUI, no PDF from CLI, warning vs error distinction, no invented official data
7. **Troubleshooting** — Missing required fields, warning pending, signature formatting, PDF dependency limitations, payload review
8. **Demo script** — What to show an operator in a 5-minute walkthrough
9. **Next phase recommendation** — L.11 PDF export command

---

## Demo Script Runner Results

| Check | Result |
|-------|--------|
| Finalized True after accept-warnings | PASS |
| Audit schema CCI_AUDIT_V1 | PASS |
| Payload JSON serializable | PASS |
| Signature is structured dict | PASS |
| signature.name matches input | PASS |
| signature.role matches input | PASS |
| doc_type preserved | PASS |
| subj present | PASS |
| Validation summary has findings count | PASS |
| warning_summary is list | PASS |
| PDF status non-failing | PASS |
| Revise path does not finalize | PASS |
| Revise path action recorded | PASS |
| Revise path returns current payload | PASS |

**Overall: 14/14 PASS**

---

## Builder Version

`_BUILDER_VERSION = "L.9"` (unchanged from L.9; L.10 is documentation/demo only)

---

## Prohibitions Verified

- No renderer/layout changes (`src/pdf_v6_render.py` untouched)
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- No error promotion
- No generated PDFs committed
- No logs or unsanitized material committed

---

## Regression Results

L.10 demo runner: **14/14 PASS**  
L.9 signature regression: **11/11 PASS**  
L.7 CLI regression: **26/26 PASS**  
L.6 dry-run: **7/7 PASS**  
Intake regression: **45/45 PASS**

---

## Recommended Next Phase

`Phase L.11  Conversational Builder Final PDF Export Command`

Goal: Add a `/render` or `--pdf` CLI option that takes a finalized builder payload and passes it to `pdf_v6_render.py`, producing a real SECNAV-compliant letter PDF from the guided builder output.

---

End of Phase L.10 checkpoint.
