# Phase L.8 — Conversational Builder Usability Review and Question-Coverage Audit

**Status:** Complete  
**Phase Type:** Review/planning only  
**Commit:** `[TBD]` — `Docs: Audit conversational builder usability coverage`  
**Input Baseline:** `bfa24f5` — `Tests: Triage builder PDF dry-run signature payload`  
**Builder Track State:** L.4/L.5/L.6/L.7/L.7A/L.7B complete  
**Active Warning Pilots:** `CCI-ROUTE-010 = warning`, `CCI-ROUTE-011 = warning`, `CCI-CH7-SUBJ-002 = warning`  
**Global Default:** `advisory`  
**Error Promotion:** Unauthorized

---

## 1. Files Reviewed

- `src/conversational_builder.py`
- `tools/run_phase_l7_conversational_builder_cli.py`
- `tools/run_phase_l7_conversational_builder_cli_regression.py`
- `tools/run_phase_l6_builder_payload_to_pdf_dry_run.py`
- `docs/planning/phase_l3_conversational_builder_payload_schema_question_flow.md`
- prior L.4–L.7B checkpoint/report context

This audit did not modify code, renderer/layout files, validators, catalogs, configuration, prompt contracts, or Phase F/G command-layer files.

---

## 2. Current CLI User Flow

The L.7 CLI is a small key-value wrapper around `BuilderSession`.

Current visible flow:

1. Start a `BuilderSession` with `doc_type = standard_letter` and `component.service = NAVY`.
2. Print the next orchestrator-supplied question.
3. Accept key-value input such as `from: ...`, `to: ...`, `subj: ...`.
4. Use `BuilderSession.ingest_user_message()` to apply the answer.
5. Repeat until the orchestrator reports required fields are complete.
6. Allow the operator to view status and warnings.
7. Allow `/accept-warnings`, `/revise`, and `/finalize`.
8. Print normalized payload JSON at finalize.
9. Report PDF dependency status but do not render PDFs.

Supported L.7 CLI commands:

- `/status`
- `/warnings`
- `/accept-warnings`
- `/revise`
- `/finalize`
- `/quit`, `/exit`, `/q`

### Observations

- The CLI is suitable as a developer/operator prototype.
- It is not yet friendly for a non-technical end user because it requires key-value syntax.
- It prints raw-ish field names such as `subj`, `copy_to`, and `window_envelope` rather than fully user-facing labels.
- It correctly avoids PDF rendering, Phase F/G command integration, and natural-language parsing.
- It currently has no persistent session state; restarting the CLI loses the draft.

---

## 3. Question Coverage Audit

### Covered or Partially Covered

| Area | Current Coverage | Notes |
|---|---|---|
| `doc_type` | Seeded by CLI | CLI starts as `standard_letter`; user does not choose document type yet. |
| `component` | Seeded by CLI | CLI seeds NAVY only; no user choice yet. |
| `from` | Covered | Orchestrator can ask; key-value input works. |
| `to` | Covered | Orchestrator can ask; key-value input works. |
| `subj` | Covered | CLI accepts subject; warning summary catches terminal punctuation. |
| `body` | Covered | Key-value single-line body works; multi-paragraph UX remains weak. |
| `signature` | Partially covered | Basic string input works for builder finalization, but renderer-compatible structured capture is not user-friendly yet. |
| `window_envelope` | Partially covered | Pass-through key-value works; formal intake policy/questions alignment remains deferred. |
| validation/warnings | Covered | `/warnings` prints structured plain-English summary. |
| finalize | Covered | `/finalize` prints normalized payload JSON; `/accept-warnings` allows warning acceptance. |

### Missing or Weak Coverage

| Area | Gap | Impact |
|---|---|---|
| Document type selection | CLI assumes `standard_letter` | User cannot yet choose other correspondence types. |
| Component/service selection | CLI assumes NAVY | Marine Corps / mixed component use is not guided. |
| SSIC | Accepted if entered, but not strongly guided | User may not know whether to enter it or how to format it. |
| Date | Accepted if entered | User-facing default/confirmation flow is not implemented. |
| Via | Accepted as key-value/list | User may not understand when to use Via. |
| References/enclosures | Accepted as list fields | Formatting help is not yet user-facing. |
| Copy-to/distribution | Accepted, but not explained well | Distribution modes/layouts are implemented elsewhere but not guided here. |
| Signature | Needs structured capture | L.7B proved string signature can become list-shaped in some paths; user-friendly structured prompt needed. |
| Window envelope | Pass-through only | User is unlikely to know what to type without a clear question. |
| Warning decision granularity | `/accept-warnings` is global | User cannot yet accept one warning and revise another. |
| Revise loop | `/revise` only resets accept flag | It does not route to the specific field tied to the warning. |
| Final PDF | Not run in L.7 | Appropriate for L.7, but next demo needs clear dry-run/render boundary. |

---

## 4. User Friction Points

### Highest Friction

1. **Key-value syntax is unnatural.**
   - A normal user will type answers in conversational form.
   - L.7 intentionally avoids NL parsing, but the CLI should show examples for every field.

2. **Signature capture is not user-safe yet.**
   - The L.6/L.7B triage showed renderer compatibility depends on structured signature shape.
   - A user should not have to know JSON structure.
   - The CLI should ask signature as separate values: name, role/title, authority.

3. **Warning decisions are too global.**
   - `/accept-warnings` accepts all pending warnings for one finalize attempt.
   - That is useful for testing, but user-facing workflow should support per-warning accept/revise/ignore.

4. **Question labels are too technical.**
   - `subj`, `ref`, `encl`, `copy_to`, and `window_envelope` should be displayed as friendly labels.

5. **Distribution/copy-to guidance is absent.**
   - The system supports multiple distribution modes and layouts, but the CLI does not explain when to use them.

6. **No demo transcript exists yet.**
   - We need a stable scripted walkthrough showing the operator exactly what to enter and what output to expect.

---

## 5. Safety and Compliance Review

The current builder track remains compliant with project constraints:

- It does not invent official command data.
- It does not promote advisories or warnings to errors.
- It preserves the user’s responsibility to revise, accept, or ignore warning-level findings.
- It does not change renderer/layout behavior.
- It does not alter CCI config/severity.
- It does not touch validator/catalog logic.
- It does not modify Phase F/G command-layer files.
- It does not commit generated PDFs or logs.

Known compliance-sensitive behaviors to preserve:

- Warning findings should remain blocking only until the user explicitly accepts or revises.
- Advisory findings should not block finalization.
- Error findings should block finalization if present, but no new error promotion is authorized.
- Generated text should not pretend to know official routing, SSICs, command names, or office codes unless user provided them.

---

## 6. Implementation Recommendations

### Recommended L.9 Track

**Phase L.9 — Conversational Builder Question Text and Signature Capture Improvements**

This is the better next phase than a demo script because L.7B exposed a real UX/data-shape issue in signature capture. Before demoing to users, the CLI should capture signature fields in a renderer-compatible structure.

### Scope for L.9

Allowed implementation should be narrow:

1. Improve CLI question display labels.
2. Add explicit signature-field capture helper:
   - `signature.name`
   - `signature.role`
   - `signature.title`
   - optional authority/activity-head fields only if needed.
3. Preserve `signature` as a renderer-compatible dict.
4. Improve `window_envelope` question/help text.
5. Improve warning decision text in `/warnings`.
6. Keep input key-value only.
7. Add L.9 regression coverage.

### Likely Files to Touch

- `tools/run_phase_l7_conversational_builder_cli.py`
- `tools/run_phase_l7_conversational_builder_cli_regression.py` or a new L.9 runner
- possibly `src/conversational_builder.py` only if signature dict ingestion needs a small helper
- new checkpoint under `docs/checkpoints/`
- status/planning trackers

### Tests Needed

- Signature entered through CLI produces dict, not list.
- Finalized payload signature matches renderer-compatible shape.
- Existing L.4/L.5/L.6/L.7 regressions still pass.
- `/warnings` still displays known warning-pilot messages.
- `/revise` does not finalize.
- `/accept-warnings` finalizes when warnings are pending.
- No renderer/config/validator/catalog files mutate.

---

## 7. Non-Goals

The following remain out of scope for L.8 and recommended L.9 unless separately approved:

- No renderer/layout changes.
- No CCI config/severity changes.
- No rule promotion.
- No validator/catalog changes.
- No Phase F/G command-layer changes.
- No natural-language parsing.
- No GUI.
- No committed PDFs.
- No logs or unsanitized material.
- Do not read or modify `docs/BOOTSTRAP.md`.
- Do not modify `docs/HERMES_INSTRUCTIONS.md`.

---

## 8. Decision

The L.7 CLI prototype is viable as a developer/operator prototype, but it is not ready for end-user demo without one usability-focused cleanup pass.

**Decision:** Continue builder track. Do not expand to NL parsing or production UI yet.

**Recommended Next Phase:** `Phase L.9 — Conversational Builder Question Text and Signature Capture Improvements`

Rationale:

- Signature capture is the highest-risk user-facing gap because renderer compatibility depends on structured signature shape.
- Question labels and field help need one pass before a useful demo script.
- This phase can remain isolated and low-risk.

---

## 9. Local Verification Expectations for L.9

Run after L.9 implementation:

```powershell
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l4_conversational_builder_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l5_conversational_builder_validation_summary_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l6_builder_payload_to_pdf_dry_run.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l7_conversational_builder_cli_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_k3_subject_terminal_punctuation_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h13_config_regression.py
```

Also run the full non-PDF gate if available.
