# Conversational Builder End-to-End Demo

**Phase L.12** — End-to-End User Demo  
**Purpose:** Show the current conversational builder flow from a blank session to finalized payload and PDF render.  
**Audience:** Operators, reviewers, and stakeholders evaluating the prototype.

---

## 1. Scope

This demo uses the existing conversational builder CLI and the `/render <output.pdf>` command added in Phase L.11B.

The current prototype is still key-value based. It does not perform natural-language parsing, does not invent official command data, and does not replace final human review.

The demo proves this complete path:

1. Start a builder session.
2. Enter required letter fields.
3. Review validation/warnings.
4. Accept warnings when appropriate.
5. Finalize the normalized payload.
6. Render a PDF using the existing `src/pdf_v6_render.py` renderer.
7. Confirm generated demo artifacts are not committed.

---

## 2. How to Run the Interactive Demo

Open PowerShell:

```powershell
cd C:\Users\drryl\SECNAV_ComplianceGPT
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli.py
```

The CLI will print a session banner and the first question.

---

## 3. Sample Input Sequence

Paste or type the following key-value lines:

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

Then run:

```text
/status
/warnings
/accept-warnings
/finalize
/render output/demo_builder_letter.pdf
/quit
```

---

## 4. Expected Behavior

| Step | Expected Result |
|------|-----------------|
| Start CLI | New `BuilderSession` starts with default standard-letter context. |
| Enter fields | Builder stores key-value fields in the accumulated payload. |
| `signature.name` / `signature.role` | Builder creates renderer-compatible structured `signature` dict. |
| `/status` | CLI prints current payload JSON. |
| `/warnings` | CLI prints structured validation summary and warning/advisory findings. |
| `/accept-warnings` | CLI allows warning findings to be accepted for finalize/render. |
| `/finalize` | CLI prints normalized payload JSON. |
| `/render output/demo_builder_letter.pdf` | CLI writes temp JSON, calls `src/pdf_v6_render.py`, and reports PDF result. |
| `/quit` | CLI exits cleanly. |

If `reportlab` is unavailable, `/render` reports a dependency skip/failure clearly. That is an environment issue, not a builder behavior failure.

---

## 5. Scripted Demo Runner

Use the scripted runner for repeatable operator review:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l12_conversational_builder_end_to_end_demo.py
```

The runner checks that:

- the scripted session finalizes;
- payload JSON is valid;
- signature is structured;
- validation summary is present;
- render returns a structured result;
- a generated PDF is deleted before completion;
- renderer/layout and CCI config files are not modified.

---

## 6. Generated-File Policy

Do not commit generated PDFs, temporary JSON payloads, logs, or screenshots from the demo.

The recommended demo output path is:

```text
output/demo_builder_letter.pdf
```

This file is for local review only. Delete it before committing, or rely on the L.12 runner to delete the generated PDF automatically.

---

## 7. What to Show in a Walkthrough

A five-minute demo should show:

1. Starting the CLI.
2. Entering the sample key-value fields.
3. Showing `/status` output.
4. Showing `/warnings` and explaining warning versus error behavior.
5. Running `/accept-warnings` and `/finalize`.
6. Showing the structured `signature` dict in the finalized payload.
7. Running `/render output/demo_builder_letter.pdf`.
8. Confirming the PDF result.
9. Explaining that generated PDFs are not committed.

---

## 8. Current Limitations

- Key-value input only.
- No natural-language parsing.
- No GUI.
- No automatic official command lookup.
- User remains responsible for correct command names, addressees, SSIC, and final wording.
- Warnings are not errors. They can be accepted; true errors block finalization.

---

## 9. Recommended Next Phase

**Phase L.13 — Conversational Builder End-to-End Demo Local Verification and Tracker Sync**

Because this L.12 artifact set was created directly through GitHub, the next local pass should pull the commit, run the scripted demo runner and related regressions, update long tracker files if needed, and confirm no generated PDF remains in git status.

---

End of Phase L.12 End-to-End Demo.
