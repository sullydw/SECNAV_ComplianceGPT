# Phase G Natural-Language Command Mediation Plan

**Status:** Planning-only — not approved for implementation  
**Current implementation baseline:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`  
**Latest documentation checkpoint:** `f9373ee` — `Docs: Record Phase F command integration checkpoint`  
**Latest project-status correction:** `022aefe` — `Docs: Fix project status after Phase E`  
**Scope:** Natural-language mediation into the existing Phase F slash-command layer  
**Safety rule:** No renderer, validator, rule catalog, automatic enforcement, or direct persistence-file writes

---

## 1. Purpose

Phase G defines a natural-language mediation layer that converts plain user requests into the already-implemented Phase F slash-command structures.

Phase G does **not** create a new correction engine. It does not add new persistence behavior, new promotion behavior, new review behavior, or new compliance rules. It only helps users express existing Phase F commands in natural language and then routes the resulting structured command through the same Phase A-F safety gates.

Examples:

- User says: "Change the subject to POLICY UPDATE."  
  Mediator produces: `/correct subj "POLICY UPDATE"`

- User says: "Remember that for this session."  
  Mediator produces: `/remember session`

- User says: "Promote that as a command preference."  
  Mediator produces: `/promote profile` only if the target is the most recent active-draft correction or a current-session correction, and only after Phase C confirmation gates.

The mediator must never silently execute a persistent or review action.

---

## 2. Relationship to Existing Phases

Phase G sits above Phase F and below any future user interface.

| Layer | Responsibility | Phase G relationship |
|---|---|---|
| Phase A | Active-draft correction and session persistence | Phase G may produce `/correct`, `/undo`, `/remember session`, `/accept`, `/reject` commands that Phase F dispatches. |
| Phase B | Correction classification | Phase G does not classify corrections directly; classification remains in Phase B APIs. |
| Phase C | Local command profile promotion | Phase G may mediate requests like "make this my command preference," but Phase C eligibility and two-step confirmation remain mandatory. |
| Phase D | Pending global rule candidate logging | Phase G may mediate requests like "flag this as a possible manual rule," but Phase D sanitization, duplicate checks, and explicit approval remain mandatory. |
| Phase E | Review/promotion utility | Phase G may mediate review commands, but Phase E evidence validation, reviewer decision logging, and `implementation_status="pending_implementation"` remain mandatory. |
| Phase F | Slash-command dispatcher | Phase G outputs Phase F structured commands; Phase F remains the only command dispatch layer. |

---

## 3. Core Principle

Natural-language input may suggest an intent, but only a structured Phase F command may be dispatched.

Phase G must perform three steps:

1. Interpret the natural-language request into a proposed command intent.
2. Produce a structured slash-command equivalent and confidence rating.
3. Confirm the command with the user before dispatch when the command is persistent, destructive, review-related, or ambiguous.

Phase G is allowed to say, "I think you mean `/correct subj "POLICY UPDATE"`. Confirm?" It is not allowed to silently perform `/promote profile`, `/log candidate`, `/decide approve`, or any other persistent action.

---

## 4. Intent Categories

Phase G must map natural language only to approved Phase F command families.

| Intent category | Example natural-language request | Structured command target | Persistence risk |
|---|---|---|---|
| Correction | "Change the From line to Commanding Officer." | `/correct <field> <value>` | Active draft only by default |
| Undo | "Undo that change." | `/undo` | Reverts current draft state |
| Remember/session | "Remember that for this session." | `/remember session` | Session JSONL write through Phase A gates |
| Session review | "Show me what was reused from this session." | `/session corrections` | Read-only |
| Session accept/reject | "Accept that session correction." / "Reject that reused correction." | `/accept <id>` or `/reject <id>` | Soft-mark or confirm only through Phase A gates |
| Profile promotion | "Make this a command preference." | `/promote profile` | Phase C two-step profile promotion |
| Pending candidate logging | "This might be a SECNAV rule; log it." | `/log candidate` | Phase D pending candidate logging |
| Review queue | "Show pending rule candidates." | `/review pending` | Read-only |
| Review claim | "Claim that candidate." | `/claim <candidate_id>` | Phase E status transition |
| Review decision | "Approve this candidate as a manual rule." | `/decide <candidate_id> approve` | Phase E evidence-gated record creation |
| Approved record listing | "Show approved rule records." | `/approved rules` | Read-only |
| Status | "What corrections are active?" | `/status` | Read-only |

The structured schema splits the combined Session accept/reject category into `session_accept` and `session_reject` sub-intents so each action can be validated and tested independently.

Any request outside these categories must return an unsupported-intent response and suggest the closest slash command only if safe.

---

## 5. Canonical Structured Command Output

Every mediated request must produce the same canonical structured command object before dispatch. This schema is authoritative for Phase G. Examples throughout the plan must use this shape.

Example output:

```json
{
  "raw_input": "Change the subject to POLICY UPDATE",
  "intent": "correction",
  "command_name": "correct",
  "slash_command": "/correct subj \"POLICY UPDATE\"",
  "arguments": {
    "field_path": "subj",
    "corrected_value": "POLICY UPDATE"
  },
  "target": {
    "correction_id": null,
    "candidate_id": null,
    "source": "active_draft"
  },
  "confidence": "high",
  "requires_confirmation": false,
  "requires_clarification": false,
  "clarification_prompt": null,
  "safety_class": "active_draft",
  "persistent_action": false,
  "blocked_reason": null,
  "safety_notes": []
}
```

The `slash_command` string is user-facing. The `arguments` object is what Phase F dispatch should receive after confirmation. If `requires_clarification` is true, `slash_command` may be null or may contain a proposed command that must not be dispatched until clarified.

---

## 6. Field Path Resolution

Phase G may infer common field names only when the mapping is clear.

| Natural-language phrase | Canonical field path |
|---|---|
| subject, subject line, Subj line | `subj` |
| From line, sender line | `from` |
| To line, recipient line | `to` |
| Via line | `via[n]` only when index/context is clear; otherwise clarify |
| reference, ref | `ref[n]` only when index/context is clear; otherwise clarify |
| enclosure, encl | `encl[n]` only when index/context is clear; otherwise clarify |
| body paragraph | `body[n]` only when paragraph number is clear; otherwise clarify |
| point of contact, POC | `point_of_contact` |
| SSIC | `ssic` |
| originator code | `originator_code` |
| signature block | `signature` |

If the natural-language request references a repeated field without an index or clear context, Phase G must ask a clarification question before producing a command.

Examples requiring clarification:

- "Change the reference." → Which reference number?
- "Fix the Via line." → Which Via addressee?
- "Change the body paragraph." → Which paragraph?

---

## 7. Ambiguity Handling

Phase G must not guess when ambiguity could affect persistent state or compliance meaning.

### 7.1 Confidence levels

| Confidence | Meaning | Allowed action |
|---|---|---|
| `high` | Clear command, clear field, clear value, no persistence risk | May dispatch non-persistent commands after showing summary |
| `medium` | Clear intent but missing minor context or target needs confirmation | Ask for confirmation before dispatch |
| `low` | Ambiguous command, unclear field/value, or multiple possible targets | Ask clarification; do not dispatch |
| `unsupported` | Outside Phase F command families | Explain unsupported request; optionally suggest safe slash command |

### 7.2 Required clarification cases

Clarification is required when:

- field path is not clear;
- repeated field index is missing;
- corrected value is missing;
- requested scope is unclear;
- the request could map to profile promotion or pending global candidate logging;
- the target correction is not the most recent active-draft correction and is not a current-session correction;
- the user asks to "make this a rule" without clarifying whether it is local command preference, possible SECNAV rule, or validator gap;
- the user asks to approve/reject/defer a candidate without a candidate ID or active selected candidate.

---

## 8. Confirmation Rules

Phase G must mirror Phase F safety expectations and require confirmation before persistent or review actions.

| Command family | Confirmation requirement |
|---|---|
| `/correct` | No confirmation required if field/value are clear; command result must show audit/conflict summary. |
| `/undo` | No confirmation required for last correction; if undo target is not last correction, clarify. |
| `/remember session` | Confirmation required because it writes session JSONL through Phase A. |
| `/accept` / `/reject` | Confirmation required because it changes reuse behavior. |
| `/promote profile` | Phase C two-step confirmation required; Phase G cannot collapse this into one step. |
| `/log candidate` | Phase D preview and explicit approval required. |
| `/claim` | Confirmation required because it changes candidate status to `under_review`. |
| `/decide approve` | Phase E evidence validation and explicit confirmation required. |
| `/decide reject/defer/supersede` | Confirmation required; rationale required where Phase E requires it. |
| `/approved rules` / `/review pending` / `/status` / `/session corrections` | Read-only; no confirmation required. |

Persistent action confirmation must show the structured slash command before dispatch.

Confirmation vocabulary should align with Phase F behavior: `yes`, `y`, or `confirm` may satisfy an active confirmation prompt. Casual agreement such as "sounds good" must not count unless a future UI layer explicitly normalizes it through the same confirmation validator.

Example:

```text
I interpreted your request as:

/promote profile

This will start the Phase C local profile promotion workflow for the most recent correction. It will not write to your profile until the Phase C two-step confirmation completes.

Confirm? yes/no
```

---

## 9. Persistent Action Safeguards

Phase G must not create any shortcut around existing Phase C, D, or E gates.

### 9.1 Profile promotion

A natural-language request such as "Remember this as our command standard" may map to `/promote profile` only if:

- the referenced correction is the most recent active-draft correction or a current-session correction;
- the correction exists;
- Phase B classified it as `local_command_preference`, or the user explicitly requests review under Phase C and Phase C still validates eligibility;
- the command layer delegates to `correction_promote`;
- Phase C two-step confirmation remains intact.

### 9.2 Pending candidate logging

A natural-language request such as "This should be a SECNAV rule" may map to `/log candidate` only if:

- the referenced correction is the most recent active-draft correction or a current-session correction;
- the correction exists;
- Phase B classified it as `possible_secnav_manual_rule` or `bug_validator_gap`;
- Phase D sanitization and duplicate checks run;
- explicit approval occurs before any JSONL append.

### 9.3 Review/promotion decision

A natural-language request such as "Approve this candidate" may map to `/decide <candidate_id> approve` only if:

- candidate ID or current selected candidate is clear;
- reviewer identity is available;
- required evidence is present;
- manual-rule approval includes `secnav_citation`;
- validator-gap approval includes `validator_evidence`;
- Phase E creates approved records only with `implementation_status="pending_implementation"`.

Phase G should detect review-decision intent from natural language, but it should collect evidence through structured follow-up prompts. It should not attempt to parse `secnav_citation`, `validator_evidence`, or reviewer rationale from free-form natural language as the final evidence record.

---

## 10. Parser Approach Options

Three approaches are possible. Phase G should choose one before implementation.

### Option A — Deterministic pattern matcher

Use regex and phrase dictionaries to identify command intent.

Pros:

- Predictable and regression-testable.
- No AI dependency.
- Lower risk of unexpected command generation.

Cons:

- Limited language flexibility.
- More clarification prompts.

### Option B — AI-assisted intent proposal with deterministic validation

An AI layer may propose a structured command object, but deterministic validation must approve it before dispatch.

Pros:

- More flexible natural-language handling.
- Better user experience for non-technical phrasing.

Cons:

- Higher test complexity.
- Requires strong validation and confirmation gates.
- Must ensure AI proposal cannot bypass command schema.

### Option C — Hybrid staged rollout

Implement deterministic parsing first, then optionally allow AI-assisted proposals that must pass the same schema validator.

Recommendation: **Option C with Phase G implementation starting in deterministic-only mode**. AI-assisted proposals may be planned as a later subphase only after deterministic mediation is regression-protected.

---

## 11. Schema Details

This section expands the canonical schema from Section 5.

### 11.1 Allowed intents

- `correction`
- `undo`
- `remember_session`
- `session_list`
- `session_accept`
- `session_reject`
- `profile_promotion`
- `pending_candidate_log`
- `review_list`
- `review_claim`
- `review_decision`
- `approved_list`
- `status`
- `unsupported`

`session_accept` and `session_reject` are separate structured sub-intents derived from the combined Session accept/reject command family in Section 4.

### 11.2 Allowed confidence values

- `high`
- `medium`
- `low`
- `unsupported`

### 11.3 Allowed safety classes

- `read_only`
- `active_draft`
- `session_persistent`
- `profile_persistent`
- `pending_candidate_persistent`
- `review_status_change`
- `approved_record_creation`
- `unsupported`

### 11.4 Module decision

Phase G implementation should use a separate module:

`src/correction_nl_commands.py`

Do not extend `src/correction_commands.py` for natural-language mediation. Keeping the natural-language mediator separate preserves Phase F's slash-command dispatcher as the stable dispatch authority and keeps parser ambiguity isolated from command execution.

---

## 12. Dispatcher Relationship

Phase G should not directly execute correction logic. It should call the Phase F dispatcher with the resulting slash command after validation and confirmation.

Recommended flow:

```text
natural language input
  -> mediate_natural_language_command()
  -> structured command object
  -> confirmation/clarification gate
  -> CorrectionCommandDispatcher.dispatch(slash_command, confirmed=...)
  -> existing Phase A-E API delegation
```

The Phase G module must not import or write to persistence modules directly except for read-only metadata needed to validate target existence. Preferred behavior is to ask Phase F or existing public APIs for status/target lists.

---

## 13. Error Handling and Clarification Prompts

| Problem | Required response |
|---|---|
| Unsupported intent | Return unsupported with allowed command examples. |
| Ambiguous field | Ask for the exact field or paragraph/reference number. |
| Missing corrected value | Ask for the replacement value. |
| Persistent action without target | Ask whether the user means the most recent correction or a current-session correction. |
| Profile/candidate request for arbitrary ID | Block and explain only most recent/current-session corrections are eligible. |
| Review decision without evidence | Ask for required structured evidence; do not dispatch. |
| Low confidence parse | Return proposed interpretation and ask user to confirm or use slash command. |
| Conflict with validator | Do not hide conflict; display validator advisory from Phase F/Phase A. |

Clarification prompts should be short and operational.

Examples:

```text
Which reference do you want to change? Use a number, such as reference 1 or reference 2.
```

```text
I can log the most recent correction as a pending candidate, but I need confirmation first. This will not enforce a global rule.
```

---

## 14. Preventing Unsafe Automation

Phase G must explicitly prevent:

- automatic profile promotion;
- automatic pending candidate logging;
- automatic review approval;
- automatic global rule enforcement;
- AI-only promotion decisions;
- direct writes to profile, session, pending, or approved-log files;
- background jobs, auto-cleanup, or notifications;
- implied approval from casual language like "sounds good" unless the prompt is currently awaiting confirmation and the expected response is yes/y/confirm.

For persistent actions, confirmation prompts must identify the command that will be run and the safety boundary.

---

## 15. Renderer, Validator, and Rule-Catalog Boundaries

Phase G must not import or modify:

- `src/pdf_v6_render.py`
- C7-C10 validators
- CCI validators
- `rules_v6/` catalogs
- layout profile files
- SECNAV manual extraction/mining logic

Natural-language mediation affects only command selection. It does not determine compliance truth, rendering geometry, rule interpretation, or validator behavior.

---

## 16. Required Regression Coverage

A new regression runner should be added only after implementation approval:

`tools/run_correction_nl_command_regression.py`

Minimum checks: **30+**.

Required coverage:

1. NL correction maps to `/correct subj ...`.
2. NL From-line correction maps to `/correct from ...`.
3. NL undo maps to `/undo`.
4. NL remember-session maps to `/remember session` only after recent correction exists.
5. NL session-list maps to `/session corrections`.
6. NL accept/reject session correction requires clear ID.
7. NL profile-promotion request maps to `/promote profile` only for recent/current-session correction.
8. Arbitrary unattached promotion target is blocked.
9. NL pending-candidate request maps to `/log candidate` only for eligible recent/current-session correction.
10. Arbitrary unattached pending candidate target is blocked.
11. NL review-list maps to `/review pending`.
12. NL claim maps to `/claim <candidate_id>` only with clear ID.
13. NL approve maps to `/decide <id> approve` only with evidence or clarification.
14. Manual-rule approval requires `secnav_citation`.
15. Validator-gap approval requires `validator_evidence`.
16. Review evidence is collected through structured follow-up prompts, not accepted directly from free-form NL as final evidence.
17. NL approved-list maps to `/approved rules`.
18. NL status maps to `/status`.
19. Ambiguous reference field asks clarification.
20. Ambiguous body paragraph asks clarification.
21. Missing corrected value asks clarification.
22. Unsupported intent returns unsupported response.
23. Low-confidence parse requires confirmation.
24. Persistent action requires confirmation.
25. Confirmation dispatches through Phase F dispatcher only.
26. Confirmation accepts yes/y/confirm when an active confirmation prompt exists.
27. No direct JSONL/profile/catalog writes from mediator.
28. No renderer imports.
29. No validator/rule catalog imports.
30. Prompt injection attempt cannot force forbidden command.
31. "Make this a global rule" does not enforce a rule; it can only propose `/log candidate` or review flow.
32. Full regression suite remains green.

All existing 22 regression suites must continue to pass before any Phase G implementation commit.

---

## 17. Files That Would Be Added or Changed in Future Implementation

New files, only after approval:

- `src/correction_nl_commands.py` — natural-language mediation layer that outputs structured Phase F commands.
- `tools/run_correction_nl_command_regression.py` — Phase G regression runner.
- `docs/checkpoints/phase_g_natural_language_command_mediation_checkpoint.md` — post-implementation checkpoint.

Likely unchanged files:

- `src/correction_commands.py` — Phase F dispatcher should remain the dispatch authority; Phase G should call it rather than rewrite it.
- `src/correction_apply.py`
- `src/correction_capture.py`
- `src/correction_classify.py`
- `src/correction_promote.py`
- `src/correction_pending_log.py`
- `src/correction_review.py`
- `src/correction_store.py`
- `src/local_profile.py`
- `src/intake_orchestrator.py`

No renderer, validator, rule catalog, or layout files should be changed.

---

## 18. What Phase G Must NOT Do

Phase G must not:

- modify renderer/layout behavior;
- modify validators or rule catalogs;
- implement automatic global rule enforcement;
- create approved global rules without Phase E review;
- make AI-only rule promotion decisions;
- bypass Phase F slash-command safety gates;
- bypass Phase C profile promotion safeguards;
- bypass Phase D pending candidate safeguards;
- bypass Phase E evidence/review safeguards;
- write directly to profile files, session JSONL files, pending logs, or approved promotion logs;
- commit real command/user data;
- create background automation;
- implement a web UI or menu UI unless separately planned and approved;
- silently treat ambiguous natural language as approval.

---

## 19. Recommended Phase G Implementation Sequence

If approved later, implement in this order:

1. Confirm parser approach: deterministic-only first. AI-assisted proposals require a separate later subphase or plan update.
2. Add `src/correction_nl_commands.py` with schema constants and non-executing mediation functions.
3. Implement deterministic mapping for read-only and active-draft commands first: correction, undo, status, session list.
4. Add clarification handling for ambiguous field paths and missing values.
5. Add persistent-action mediation for session remember, accept, reject with confirmation requirements.
6. Add profile-promotion and pending-candidate mediation, constrained to recent/current-session correction only.
7. Add review-decision mediation, requiring structured evidence follow-up before dispatch.
8. Add prompt-injection and unsafe-automation negative tests.
9. Add `tools/run_correction_nl_command_regression.py` with 30+ checks.
10. Run new regression runner.
11. Run all 22 existing regression suites.
12. Commit implementation only if all pass.
13. Create `docs/checkpoints/phase_g_natural_language_command_mediation_checkpoint.md` and update project status.

---

## 20. Open Questions Needing Approval

1. Should the first Phase G implementation be deterministic-only? Recommendation: yes.
2. Should AI-assisted proposals be planned as a future Phase G subphase or Phase H? Recommendation: future planning after deterministic mediation is regression-protected.
3. Should natural-language input be allowed to dispatch low-risk read-only commands without confirmation? Recommendation: yes, if confidence is high.
4. Should `/correct` natural-language requests require confirmation, or only show the resulting validator/audit summary after applying? Recommendation: no confirmation for high-confidence active-draft corrections; show audit/conflict summary and allow undo.
5. How should the mediator determine the "current selected candidate" for review commands in non-UI contexts?
6. Should evidence fields for review decisions always be collected through structured prompts? Recommendation: yes.
7. Should confirmation accept yes/y/confirm? Recommendation: yes, matching Phase F behavior.
8. Should prompt-injection tests be part of Phase G from the start? Recommendation: yes.

---

## 21. Planning Decision Summary

Recommended safe default for implementation approval:

- Start deterministic-only.
- Use `src/correction_nl_commands.py` as a separate module.
- Output the canonical structured Phase F command schema from Section 5.
- Dispatch only through `CorrectionCommandDispatcher`.
- Require confirmation for all persistent/review actions.
- Ask clarification on ambiguity.
- Collect review evidence through structured follow-up prompts.
- Confirm using yes/y/confirm when an active confirmation prompt exists.
- Reject unsupported intents.
- Add 30+ regression checks.
- Run all 22 existing regressions before committing.

No implementation is approved by this document.
