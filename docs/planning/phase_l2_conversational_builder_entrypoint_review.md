# Phase L.2 — Conversational Builder Entry-Point Review

**Status:** Read-only review. No code changes.  
**Commit:** `[TBD]` — `Docs: Review conversational builder entry points`  
**Latest Verified Baseline:** `2e8e920` — Current HEAD  
**Active Warning Pilots:** `CCI-ROUTE-010 = warning`, `CCI-ROUTE-011 = warning`, `CCI-CH7-SUBJ-002 = warning`  
**Global Default:** `advisory`  
**Error Promotion:** Unauthorized  
**Regression Gate:** 37 suites PASS at `2e8e920`

---

## Files Reviewed

| File | Role | Key Finding |
|---|---|---|
| `src/intake_orchestrator.py` | Core intake orchestrator | Already implements `next_questions()`, `build_payload()`, `run_audit()`, `apply_answers()`, and correction memory hooks. Reads deterministic policy/questions from JSON. |
| `src/correction_nl_commands.py` | NL command mediator | Deterministic intent detection for corrections, undo, session, profile, pending, review, status. **No builder/create intent exists.** Dispatches to `CommandDispatcher`. |
| `src/validator_runner.py` | CCI audit entry point | `run_cci_audit(payload, user_answers=None)` returns structured `CCI_AUDIT_V1` with `errors`, `warnings`, `summary`. |
| `src/pdf_v6_render.py` | v6 PDF renderer | Takes a normalized payload and generates PDF. Stable, regression-protected. |
| `src/letter_model_v6.py` | Payload normalizer | Ensures optional list fields, body-to-list conversion, and derived booleans (`has_via`, `has_ref`, etc.). |
| `src/context_resolver.py` | Context resolver | Infers doc_type, component, routing counts, reply/action/POC requirements from payload. |
| `rules_v6/CCI/cci_intake_field_policy.json` | Field policy | Defines `required`/`recommended`/`optional` per doc_type (8 types). |
| `rules_v6/CCI/cci_intake_questions.json` | Question registry | Defines 24 questions with `field_path`, `prompt_text`, `applies_to_doc_types`, `aliases`. |
| `docs/planning/phase_l1_conversational_builder_workflow_plan.md` | Parent plan | Source of requirements for this review. |
| `docs/PROJECT_STATUS.md` | Status tracker | Updated after this review. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Rule promotion plan | Updated after this review. |

---

## 1. Current User-Facing Entry Points

There is **no dedicated conversational builder** today. The existing entry points are:

1. **`src/intake_orchestrator.py` CLI** — `python src/intake_orchestrator.py <payload.json> [answers.json]`
   - Prints missing fields and next questions in batch.
   - Not interactive; no multi-turn state machine.

2. **`src/correction_nl_commands.py` CLI** — `python -m correction_nl_commands "<natural language request>"`
   - Converts NL to structured Phase F slash commands.
   - Intents: correction, undo, remember, session, promote, log, review, status.
   - No "build letter" or "create correspondence" intent.

3. **`src/validator_runner.py` CLI** — `python src/validator_runner.py <payload.json>`
   - One-shot CCI audit. Human-readable or JSON output.

4. **`src/pdf_v6_render.py`** — No direct CLI; consumed by regression runners and manual scripts.

5. **No web server, chat bot, TUI, or API endpoint exists** for interactive builder use.

---

## 2. How Intake Currently Works

`IntakeOrchestrator` (lines 183–675 of `intake_orchestrator.py`):

1. Accepts `payload`, `user_answers`, optional `active_profile`, optional `session_id`.
2. Merges profile defaults via `apply_profile_defaults()` if profile is active.
3. `build_payload()` returns merged dict with priority: payload > user_answers > profile.
4. `get_status()` resolves context, runs audit, classifies missing fields into required/recommended/optional using `cci_intake_field_policy.json`.
5. `next_questions()` loads `cci_intake_questions.json`, filters by doc_type/component, skips fields already present, sorts by bucket (required → recommended → optional).
6. `apply_answers()` merges new answers into `user_answers`.
7. `run_audit()` calls `validator_runner.run_cci_audit()`.

**This is 80% of what a conversational builder needs.** The missing 20% is:
- Multi-turn state machine (ask one question, wait for answer, recompute next question).
- Plain-English audit summary formatter.
- A builder-specific entry point / wrapper that hosts the turn loop.

---

## 3. Does a Conversational Builder Already Partly Exist?

**Yes — the IntakeOrchestrator is the foundational layer.**

It already:
- Knows required vs recommended vs optional per doc_type.
- Already has question prompts, aliases, and doc_type filters.
- Already runs CCI audit and exposes missing fields + audit summary.
- Already supports profile prefill and session correction reuse.

It does **not** yet:
- Run in a conversational loop (batch-only).
- Skip already-answered fields across multiple turns (it does skip them within one `next_questions()` call, but there is no session state between turns).
- Present audit findings in plain English for an end user.
- Wire into PDF generation.

---

## 4. Current Structured Payload Shape

From `src/letter_model_v6.py` and example `audit_c7_phase1_standard_letter.json`:

Top-level fields consumed by renderer:
- `doc_type` (string, e.g., `DT_STD_LTR`)
- `ssic` (int or string)
- `originator_code` (string)
- `date` (string, e.g., `01 May 2026`)
- `unit_identity` (object with letterhead lines)
- `from` (string)
- `to` (string)
- `via` (list of strings)
- `subj` (string)
- `ref` (list of strings)
- `encl` (list of strings)
- `body` (list of strings)
- `signature` (object: `name`, `role`, `title`, `authority`, `activity_head_title`, `affects_pay_or_allowances`)
- `copy_to` (list of strings)

Derived fields added by `letter_model_v6.normalize_payload()`:
- `has_via`, `has_ref`, `has_encl`, `has_copy_to`, `has_distribution`
- `via_count`, `ref_count`, `encl_count`, `distribution_count`, `body_count`
- `distribution_mode`, `distribution_layout`, `copy_to_layout`, `distribution_label`, `copy_to_label`

**Gap:** `window_envelope` (boolean) is not in the policy/questions or normalizer, but the renderer and `CCI-ROUTE-011` validator reference it. Adding it to the intake schema is safe and does not change renderer behavior.

---

## 5. How Validation/CCI Audit Can Run Before Final PDF

Current path:
1. `orchestrator.build_payload()` → merged payload dict.
2. `orchestrator.run_audit()` → calls `validator_runner.run_cci_audit(payload, user_answers)`.
3. Result structure (`CCI_AUDIT_V1`):
   - `validators.{subject,ref_encl,acronyms,date_time,personnel,poc,routing}.errors`
   - `validators.{...}.warnings`
   - `summary.total_errors`, `summary.total_warnings`, `summary.overall_pass`

**Hook point:** A builder wrapper can call `run_audit()` after each answer batch or once at the end. Calling it once at the end is sufficient for Phase L.3–L.6.

---

## 6. Proposed Builder Hook Points

### Guided Question Flow
- **Hook:** Wrap `IntakeOrchestrator.next_questions(limit=1)` in a loop.
- **State:** A small `BuilderSession` class tracks which fields have been asked and answered so far, so the orchestrator's existing skip logic works.
- **Entry:** New module `src/conversational_builder.py` that imports `IntakeOrchestrator` and hosts the loop.

### Field Completion
- **Hook:** Reuse `orchestrator.apply_answers()`.
- **No schema change needed** for standard fields; `cci_intake_questions.json` already covers them.
- **One addition needed:** `window_envelope` question/policy entry so the builder can suppress `From` and `CCI-ROUTE-011` correctly.

### Validation Summary
- **Hook:** New `format_audit_summary(audit_result) -> str` function.
- **Location:** `src/conversational_builder.py` or a small `src/builder_format.py`.
- **Behavior:** Map rule codes to plain-English sentences (per L.1 Section 6). No changes to `validator_runner.py`.

### User Revise/Accept Loop
- **Hook:** After audit, present warnings. If user says "accept," record an explicit override flag in the builder session (not in the payload). If user says "revise," route back to the relevant question.
- **No correction memory reuse needed here** — the builder is a collector, not a corrector. Correction memory applies to post-render fixes, not pre-render intake.

### Final PDF Generation
- **Hook:** `build_payload()` → `letter_model_v6.normalize_payload()` → `pdf_v6_render.py` render function.
- **No renderer change needed.**

---

## 7. Missing Pieces

| Missing Piece | Impact | Mitigation / Plan |
|---|---|---|
| Multi-turn state machine wrapper | Builder cannot hold a conversation | Add thin `BuilderSession` wrapper in L.4 |
| Plain-English audit formatter | Audit output is structured/technical | Add `format_audit_summary()` in L.5 |
| `window_envelope` in intake policy/questions | Builder cannot suppress `From` requirement | Add one question + policy entry in L.3 |
| Builder intent in NL mediator | User cannot say "build me a letter" | Evaluate in L.3; may defer to explicit `/build` command or CLI flag |
| No persistent draft state | Session interruption = restart | Accept for L.2–L.6; no persistent state planned |
| No preview/HTML output | User cannot see layout before PDF | Defer; PDF is the only preview in L.6 |

---

## 8. Risks to Renderer Stability

| Risk | Assessment |
|---|---|
| Builder passes malformed payload to renderer | Mitigated by `letter_model_v6.normalize_payload()` and existing `pre_render_v6_audit.py` |
| Builder adds new top-level fields renderer does not expect | Safe — renderer ignores unknown keys; but we will not add new renderer-facing fields |
| Builder changes `doc_type` mid-session | Allowed; orchestrator re-computes questions on next turn. Risk: already-collected fields may become irrelevant. Mitigation: warn user before switching doc_type. |
| Active warning pilots block generation | Expected behavior; builder surfaces warnings and asks user to accept or fix. |

---

## 9. Compatibility with Existing NL Correction Command Flow

The existing `NLCommandMediator` has no "builder" intent. Two integration options:

1. **Separate entry point** — `python -m conversational_builder` or `/build` slash command. No NL mediator changes.
2. **Add a `builder` intent** to `_INTENT_PHRASES` (e.g., "build a letter", "create correspondence"). This would dispatch to the new builder wrapper. Requires Phase F dispatcher awareness.

**Recommendation:** Option 1 for L.3–L.6. Option 2 can be evaluated in a later phase after the builder prototype is stable. This avoids touching `correction_nl_commands.py` or `correction_commands.py` now.

---

## 10. Recommended Smallest Safe Implementation Phase

**Phase L.3 — Conversational Builder Payload Schema and Question Flow**

Scope:
1. Add `window_envelope` to `cci_intake_field_policy.json` (optional) and `cci_intake_questions.json`.
2. Define `BuilderSession` state machine schema (a JSON/YAML plan, not code yet):
   - phases: intake → routing → body → refs/encls → signature → validation → generate.
   - transition rules based on `doc_type`.
   - skip logic: if field already present, skip the question.
3. Define plain-English mapping for the three active warning pilots (`ROUTE-010`, `ROUTE-011`, `SUBJ-002`).
4. Define how `BuilderSession` outputs a final payload ready for `letter_model_v6.normalize_payload()`.

No code changes to renderer, validator, config, NL mediator, or command dispatcher.

---

## Explicit Non-Goals

- **No renderer or layout changes.** `src/pdf_v6_render.py` remains read-only.
- **No CCI severity or config changes.** `config/cci_enforcement_config.json` untouched.
- **No rule promotion.** No rule may be promoted to `warning` or `error`.
- **No Phase F or Phase G command-layer changes.** `correction_commands.py` and `correction_nl_commands.py` remain read-only for this review.
- **No logs or unsanitized material committed.**
- **Do not read or modify `docs/BOOTSTRAP.md`.**
- **Do not modify `docs/HERMES_INSTRUCTIONS.md`.**

---

## Recommended Next Phase

**Phase L.3 — Conversational Builder Payload Schema and Question Flow**

Read this review document, then produce a lean schema definition that specifies:
- `BuilderSession` state transitions.
- Updated `cci_intake_questions.json` and `cci_intake_field_policy.json` with `window_envelope`.
- Plain-English warning message map.
- Prototype module interface (`src/conversational_builder.py` stub plan).

Planning-only; no implementation code.

---

End of Phase L.2 Conversational Builder Entry-Point Review.
