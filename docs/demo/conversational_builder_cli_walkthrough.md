# SECNAV Conversational Builder CLI Walkthrough

**Phase L.10** — Operator/Developer Demo Documentation  
**Purpose:** Demonstrate current builder CLI from start to finalized payload.  
**Audience:** Operators and developers evaluating the prototype.  
**Scope:** Key-value input only; no natural language parsing; no GUI; no PDF generation from the CLI yet.

---

## 1. How to Run

Open PowerShell and run:

```powershell
cd C:\Users\drryl\SECNAV_ComplianceGPT
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli.py
```

The CLI prints a banner and asks the first required question.

---

## 2. Sample Input Sequence

Enter each line exactly as shown (key-value format):

```
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

After the last field, check status:

```
/status
```

Review warnings:

```
/warnings
```

Accept warnings to allow finalization:

```
/accept-warnings
```

Finalize the letter:

```
/finalize
```

Exit the CLI:

```
/quit
```

---

## 3. Expected Behavior

| Step | What Happens |
|------|--------------|
| `ssic` | Stored as string; no coercion |
| `date` | Stored as provided |
| `from` | Stored as provided; prefilled if profile is active |
| `to` | Stored as provided |
| `subj` | Stored; SUBJ-002 may trigger a warning if punctuation is present |
| `body` | Stored as string |
| `signature.name` | Stored inside structured `signature` dict as `{"name": "J. Q. Sample"}` |
| `signature.role` | Added to same dict as `{"role": "Commanding Officer"}` |
| `window_envelope` | Coerced to boolean (`no` → `False`) |
| `/warnings` | Prints validation summary with severity, message, and actions per finding |
| `/accept-warnings` | Records global acceptance; allows finalize despite pending warnings |
| `/finalize` | Returns normalized payload JSON, audit schema, and validation summary |

**PDF generation:** Not performed by the interactive CLI. The prototype produces structured JSON only. PDF export is a future phase.

---

## 4. Common Commands

| Command | Purpose |
|---------|---------|
| `/status` | Print current payload as formatted JSON |
| `/warnings` | Show validation summary: findings, severities, pending decisions |
| `/accept-warnings` | Accept all pending warnings so `/finalize` can proceed |
| `/revise` | Clear the accept-warnings flag; continue editing fields |
| `/finalize` | Produce normalized payload JSON; prints validation summary |
| `/quit` | Exit the CLI cleanly |

---

## 5. Structured Signature Capture

As of Phase L.9, the builder supports structured signature input:

| Input Form | Result in Payload |
|-----------|-------------------|
| `signature.name: J. Q. Sample` | `signature.name` = `"J. Q. Sample"` |
| `signature.role: Commanding Officer` | `signature.role` = `"Commanding Officer"` |
| `signature.title: Commanding Officer` | `signature.title` = `"Commanding Officer"` |
| Plain `signature: J. Q. Sample` | Maps to `signature.name` for backward compatibility |

The renderer expects `signature` as a dict with optional `name`, `role`, and `title` keys. The builder now produces that shape directly.

---

## 6. Limitations

- **Key-value input only.** No natural language parsing (e.g., "Set the subject to Training Plan" does not work).
- **No GUI.** This is a terminal prototype.
- **No PDF from CLI yet.** The interactive loop produces JSON only. PDF generation requires a separate render step.
- **Warning vs Error.** Warnings (ROUTE-010, ROUTE-011, SUBJ-002) do not block finalization after `/accept-warnings`. Advisories never block. Errors block and cannot be bypassed.
- **Do not invent official data.** All names, SSICs, office codes, and addressees should be real or explicitly marked as synthetic.

---

## 7. Troubleshooting

### Missing required fields
If `/finalize` says "Finalize allowed: no", check `/status` for missing `from`, `to`, `subj`, `body`, `date`, or `signature`. Fill them before finalizing.

### Warning pending
If `/finalize` says "Block: pending decisions", run `/accept-warnings` first, or revise the flagged field and re-run validation.

### Signature formatting
If the renderer later rejects the signature, verify you used `signature.name:` (with dot) or the plain `signature:` form. Do not pass a raw list like `['name', 'role']`.

### PDF dependency limitations
The CLI reports PDF status at finalize time. If dependencies are missing, it prints a skip message. This is expected in environments without `reportlab`/`fitz`. It is not a failure.

### Payload review
Always review the normalized JSON before assuming it is correct. The builder does not invent content, but it does coerce types (boolean, list) and expand dotted keys.

---

## 8. What to Demo

1. Start the CLI.
2. Paste the sample sequence above.
3. Run `/warnings` to show pilot warning findings in plain English.
4. Run `/accept-warnings` to demonstrate user control.
5. Run `/finalize` to show structured JSON output.
6. Point out the `signature` dict in the payload.
7. Explain that PDF generation is a separate future step.

---

## 9. Next Implementation Phase

**Recommended:** `Phase L.11  Conversational Builder Final PDF Export Command`

Goal: Add a `/render` or `--pdf` CLI option that takes a finalized builder payload and passes it to `pdf_v6_render.py`, producing a real SECNAV-compliant letter PDF from the guided builder output.

---

End of Phase L.10 Walkthrough.
