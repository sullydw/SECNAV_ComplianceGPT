# Correction Memory and Rule Promotion Layer Plan

**Current Verified Baseline:** `058de87` — CCI: Add review promotion utility (Phase E)
**Phase E Implementation:** `058de87` — CCI: Add review promotion utility (Phase E)
**Phase D Implementation:** `2e31892` — CCI: Add pending global rule candidate logging (Phase D)
**Phase C Implementation:** `8b8a95c` — CCI: Add local command profile promotion (Phase C)
**Phase B Implementation:** `519fad6` — CCI: Add correction classification (Phase B)
**Previous Verified Baseline:** `2e31892` — CCI: Add pending global rule candidate logging (Phase D)
**Phase A Implementation:** `71ddf64` — CCI: Add session correction persistence (Phase A)
**Latest Checkpoint:** `058de87` — Phase E review/promotion utility checkpoint (immediately after this update)
**Next Phase:** Phase F UI/command integration planning (planning-only until approved)
---

## 1. Purpose

The system must allow a user to correct an error in the active draft, apply that correction immediately, rerun validators, regenerate output, and store the correction for scoped reuse.

When a user identifies a problem in a generated draft (e.g., wrong wording in the subject line, incorrect From line title, missing Via addressee, improper personnel identification format), they should be able to specify the correction once, see it applied immediately, and have the system remember that correction so that future drafts in similar contexts do not repeat the same mistake — provided it is safe to do so.

The Correction Memory and Rule Promotion Layer is not a replacement for deterministic SECNAV validators. It is a user-driven feedback loop that sits alongside the CCI layer, with strict guardrails preventing unreviewed local preferences from becoming global compliance rules.

---

## 1a. What Is Already Implemented

The following items are complete and regression-protected.

### Baseline `2e643db` — Active-Draft Correction + Intake Integration

- **Active-draft correction apply:** `src/correction_apply.py` — apply a single correction to a payload JSON object given a field path and corrected value; supports undo.
- **Active-draft correction capture:** `src/correction_capture.py` — capture correction metadata from user input and build a structured correction record.
- **Intake orchestrator integration:** `src/intake_orchestrator.py` — captures corrections via `capture_correction()`, applies them via `apply_correction()`, supports undo via `undo_correction()`, reruns audit via `rerun_audit_after_correction()`.
- **Conflict detection:** If a correction increases the audit error count, the system surfaces a `correction_conflict` advisory without blocking the draft.
- **In-memory tracking:** `corrections_applied` and `correction_conflicts` are tracked inside `IntakeOrchestrator` and exposed through `get_status()`.
- **Regression coverage:**
  - `tools/run_correction_regression.py` — tests capture, apply, undo, conflict detection.
  - `tools/run_intake_regression.py` — tests before/after audit with correction, undo restoration, and conflict surfacing.

### Baseline `71ddf64` — Phase A Session Correction Persistence

- **Session JSONL store:** `src/correction_store.py` stores opt-in session corrections under `corrections/session/`.
- **Gitignore safety:** `.gitignore` excludes `corrections/session/*.jsonl`, `corrections/pending_corrections.jsonl`, and `corrections/approved_rule_promotions.json`.
- **Session directory:** `corrections/session/.gitkeep` and `corrections/session/README.md` document local-only session storage.
- **Current-session scope:** `src/correction_capture.py` allows `current_session` scope.
- **Intake support:** `src/intake_orchestrator.py` supports optional `session_id`, `set_session_id()`, `_preapply_session_corrections()`, `persist_correction()`, `reject_session_correction()`, and `session_notes` in `get_status()`.
- **Session rejection:** rejected corrections are soft-marked with `user_rejected=True` and excluded from future matching.
- **One-time wording safety:** `one_time_wording` corrections are not persisted unless explicitly scoped to `current_session`.
- **Regression coverage:** `tools/run_correction_session_regression.py` passed 30/30 checks.

### Current Limits (by design)

- Session persistence is opt-in only; `session_id=None` preserves in-memory-only behavior.
- Session JSONL files are local and gitignored.
- 30-day session retention is advisory only; no automatic cleanup is implemented.
- Automatic correction classification is implemented (Phase B) but does not promote; it gates persistence only.
- Local command profile promotion is implemented (Phase C) with mandatory two-step approval, external profile storage, backup, and atomic writes.
- **Pending global rule candidate logging is implemented (Phase D)** with mandatory sanitization, explicit approval required before write, current-session-only scope, and `corrections/pending_corrections.jsonl` is gitignored.
- **Review/promotion utility is implemented in Phase E** with human reviewer claim, evidence validation, append-only review metadata, PII sanitization, and approved-rule record creation only (no validator/catalog/renderer changes).
- No automatic global rule enforcement.
- No natural-language correction command UI.

These remaining limits are intentional and are planned for future phases only after separate review and approval.

### Implemented storage safety files

- `.gitignore` — excludes session JSONL, pending candidate log, and future approved rule promotion files.
- `corrections/session/.gitkeep` — keeps the local session directory structure.
- `corrections/session/README.md` — explains local-only session correction storage.
- `corrections/README.md` — explains local-only pending candidate log and session storage.

### Future modules (require approval before implementation)

- `src/correction_reuse.py` — optional future separation if reuse logic grows beyond `IntakeOrchestrator`.

---

## 2. Core Principle

Apply corrections immediately to the active draft.
Reuse corrections within safe scope.
Do not allow unreviewed user corrections to become global SECNAV compliance rules automatically.

The layer operates on three principles:

1. **Immediate application**: every correction is applied to the current draft payload before rerunning validators or regenerating output.
2. **Scoped reuse**: corrections are tagged with scope and context so the system knows when it is safe to reuse them automatically.
3. **Manual promotion**: only corrections that pass review can be promoted to local command profiles or global rule candidates. No correction is ever promoted silently.

---

## 3. Correction Scopes

| Scope | Auto-reuse | Status | Description |
|---|---|---|---|
| `active_draft` | Yes — immediate | Implemented | Correction applies only to the draft currently being edited. It is used once, immediately, and tracked in memory. |
| `current_session` | Yes — when context matches | Implemented in Phase A | Correction persists to a local, gitignored JSONL session store when `session_id` is provided and scope is explicitly `current_session`. Reused when document type, component, and affected field match. |
| `local_command_profile` | Yes — after explicit user approval | Completed in Phase C | Correction becomes part of a named local command profile. Must be approved by the user before activation. |
| `pending_global_rule_candidate` | No — manual review only | Completed in Phase D | Correction is logged as a candidate for a global SECNAV compliance rule or validator update. It is never auto-applied. |
| `approved_global_rule` | Yes — enforced | Future Phase F+ | Correction has been reviewed, validated against SECNAV M-5216.5 text, and promoted into the rule catalog, validator code, or AI prompt contract. Phase E creates `approved_global_rule` records with `implementation_status="pending_implementation"` only; actual enforcement requires future validator/catalog changes. |

---

## 4. Correction Workflow

When a user issues a correction command or selects a correction in a future UI:

1. **Capture original generated value** — snapshot the field value before modification.
2. **Capture corrected value** — record the user's intended replacement.
3. **Capture field/path affected** — JSON path or canonical field name (e.g., `subj`, `from`, `body[2]`, `via[0]`).
4. **Capture document type** — standard_letter, endorsement, memorandum_for_record, etc.
5. **Capture component context** — navy, marine_corps, joint, don_secretariat, unknown.
6. **Capture user explanation** — free-text reason for the correction, used later for classification and audit.
7. **Apply correction to current draft** — mutate the active payload in memory.
8. **Rerun applicable CCI validators** — run validators that inspect the affected field.
9. **Track conflict status** — surface advisory conflict if audit error count increases.
10. **Persist only when safe and explicit** — store as `current_session` only when a caller provides `session_id` and the correction is explicitly session-scoped.
11. **Defer promotion** — do not promote to profile or global rules without future approved workflow.

Automatic classification is not yet implemented. It is the next planning phase.

---

## 5. Correction Reuse Behavior

### `active_draft`

- The correction is applied once to the current payload.
- The correction is tracked inside `IntakeOrchestrator` memory and exposed through `get_status()`.
- Undo is supported.

### `current_session`

- The correction is stored in a local JSONL session store only when `session_id` is provided and scope is explicitly `current_session`.
- `session_id=None` preserves prior in-memory-only behavior.
- On a new draft in the same session, the system checks whether document type, component, and field path match a stored correction.
- If all context keys match, the correction may be pre-applied before validators run.
- If the user rejects the pre-applied correction, it is soft-marked with `user_rejected=True` and excluded from future matching.
- Session retention is advisory only; there is no automatic cleanup in Phase A.

### `local_command_profile`

- Completed in Phase C.
- The user must explicitly approve adding the correction to a named local profile.
- Corrections in this scope must not leak into default global behavior.
- Real profile data must not be committed to the public repository.

### `pending_global_rule_candidate`

- Completed in Phase D.
- Corrections classified as `possible_secnav_manual_rule` or `bug_validator_gap` are written to `corrections/pending_corrections.jsonl` only after explicit user approval.
- They must never be auto-applied to other users or other sessions.
- Candidate logs must remain gitignored and subject to review.

### `approved_global_rule`

- Future Phase F or later.
- Phase E creates approved-rule records with `implementation_status="pending_implementation"` only; actual enforcement requires future validator/catalog changes.
- Once reviewed and approved, a correction may become a deterministic rule in `rules_v6/CCI/`, a validator update in `src/cci_*.py`, or a prompt-contract addition.
- Never auto-applied.

---

## 6. Safety Guardrails

- **User correction shall never silently override a deterministic SECNAV validator.** If a correction conflicts with a validator finding, the system must surface the conflict and require review.
- **If a correction conflicts with a validator, show conflict and require review.** The user may choose to override the validator for this draft only, escalate the correction as a bug/validator gap, or abandon the correction.
- **User correction shall not become a global rule without review.** The `pending_global_rule_candidate` scope ensures every proposed global change is inspected.
- **Local overrides must be scoped to command/profile.** A local command preference cannot leak into the default global behavior.
- **All correction records should be auditable and reversible.** Every record stores original value, corrected value, timestamp, classification or classification candidate, and user explanation where available.
- **Session JSONL stores may contain sensitive draft values.** They are local-only and gitignored.
- **Do not log raw original/corrected values at INFO level.** Future logging should prefer field paths and correction IDs.
- **Do not commit real session stores, command profiles, contact data, or correction logs.**

---

## 7. Files Status

### Implemented modules

- `src/correction_apply.py` — apply a single correction to a payload JSON object given a field path and corrected value; supports undo via `undo_correction()`.
- `src/correction_capture.py` — capture correction metadata from user input and build a structured correction record; supports `active_draft` and `current_session` scopes.
- `src/correction_classify.py` — classify a correction into one of `one_time_wording`, `local_command_preference`, `possible_secnav_manual_rule`, or `bug_validator_gap` using deterministic heuristics based on field path and reason text. Phase B complete.
- `src/correction_promote.py` — Phase C local command profile promotion. Two-step approval, eligibility gating, backup, atomic write, disable/remove/edit support.
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging. Eligibility gating, full PII sanitization, candidate record schema, JSONL append/read/update helpers, duplicate fingerprinting, and status transition helpers.
- `src/correction_store.py` — save, load, update, reject, and delete session correction JSONL records.
- `src/intake_orchestrator.py` — orchestrates correction capture, apply, undo, audit rerun, opt-in session persistence, session pre-application, rejection, and correction classification gating.

### Implemented storage safety files

- `.gitignore` — excludes session JSONL and future correction log files.
- `corrections/session/.gitkeep` — keeps the local session directory structure.
- `corrections/session/README.md` — explains local-only session correction storage.

### Future modules (require approval before implementation)

- `src/correction_reuse.py` — optional future separation if reuse logic grows beyond `IntakeOrchestrator`.

### Future storage files (require approval before implementation)

- `corrections/pending_corrections.jsonl` — append-only log of pending global rule candidates. Phase D implemented.
- `corrections/approved_rule_promotions.json` — record of corrections promoted to global rules, with reviewer, date, and rationale. (Future Phase E)

### Regression files

- `tools/run_correction_regression.py` — active-draft correction regression.
- `tools/run_intake_regression.py` — intake and correction integration regression.
- `tools/run_correction_session_regression.py` — Phase A session persistence regression.
- `tools/run_correction_classify_regression.py` — Phase B classification regression.
- `tools/run_correction_profile_promotion_regression.py` — Phase C local command profile promotion regression.
- `tools/run_correction_pending_regression.py` — Phase D pending global rule candidate logging regression.

---

## 8. Example Scenarios

### 8.1 Subject punctuation correction

- **Original**: `Subj: POLICY UPDATE.`
- **Correction**: remove terminal period.
- **Classification candidate**: `possible_secnav_manual_rule` or `bug_validator_gap` if the validator missed it.
- **Current safe scope**: `active_draft` unless explicitly persisted to `current_session`.

### 8.2 From line corrected from individual name to Commanding Officer

- **Original**: `From: John A. Smith`
- **Correction**: `From: Commanding Officer, USS NEVERSAIL`
- **Classification candidate**: `possible_secnav_manual_rule` or `local_command_preference` depending on context.
- **Current safe scope**: `active_draft` or explicit `current_session` only.

### 8.3 Local originator code preference

- **Original**: sender symbol lacks originator code.
- **Correction**: add local originator code `N7`.
- **Classification candidate**: `local_command_preference`.
- **Future scope**: `local_command_profile` only after explicit approval.

### 8.4 Navy vs Marine Corps personnel wording correction

- **Original**: body text uses "Marine" lowercase.
- **Correction**: capitalize "Marine".
- **Classification candidate**: `possible_secnav_manual_rule` or `bug_validator_gap` if a validator missed it.
- **Current safe scope**: `active_draft` or explicit `current_session` only.

### 8.5 Missing Via routing rule discovered

- **Original**: draft omits an intermediate Via addressee that chain of command requires.
- **Correction**: add the Via addressee.
- **Classification candidate**: `local_command_preference`, `possible_secnav_manual_rule`, or `bug_validator_gap` depending on whether the requirement is command-specific or manual-based.
- **Future scope**: profile or pending global candidate only after review.

### 8.6 One-time wording change that should not become rule

- **Original**: body paragraph uses a specific example sentence.
- **Correction**: user rewords the example for this particular letter.
- **Classification candidate**: `one_time_wording`.
- **Current safe scope**: `active_draft` only by default. It must not persist unless explicitly scoped to `current_session`.

---

## 9. Relationship to AI Drafting

- **AI may propose corrections and ask whether to remember them.** When the AI detects a likely error during drafting, it can suggest a correction and ask the user: "Apply this correction to the current draft? Remember for this session? Add to local profile?"
- **AI may classify likely correction scope only after Phase B is designed and approved.** Until then, classification is not automatic.
- **Deterministic validators remain final authority for implemented hard rules.** A user or AI correction that conflicts with a deterministic validator must be surfaced as a conflict, not silently accepted.
- **Unresolved conflicts become human-review items.** If the user insists on a correction that violates a validator, the draft is flagged for human review before release.

---

## 10. Future Implementation Phases (Require Approval)

| # | Phase | Task | Scope | Status | Approval Required |
|---|---|---|---|---|---|
| A | **Session persistence** | Lightweight JSONL session store (`corrections/session/`). Corrections from a session are available to the next draft in the same session if document type, component, and field match. | Complete at `71ddf64` | Completed |
| B | **Correction classification** | `src/correction_classify.py` — classify a correction into one of the four types using heuristics (field path + reason). Gates session persistence; does not promote. | Complete at `519fad6`; regression isolation fix at `a7f9aeb` | Completed |
| C | **Local command profile promotion** | User approval workflow. Writing approved corrections to external profile `override_rules` as local overrides. Only for `local_command_preference` classifications. | **Complete at `8b8a95c`** | Completed |
| D | **Pending global rule candidate log** | `corrections/pending_corrections.jsonl` append-only log. For `possible_secnav_manual_rule` and `bug_validator_gap` classifications. Never auto-applied. | **Complete at `2e31892`** | Completed |
| E | **Review/promotion utility** | `src/correction_review.py` — human reviewer claim, evidence validation, append-only review metadata, PII sanitization, approved-rule record creation (`implementation_status="pending_implementation"`). No validator/catalog/renderer changes. | **Complete at `058de87`** | Completed |
| F | **UI/command integration** | Natural user commands for issuing corrections (not raw JSON path editing). Future chat or web interface integration. | Future | Yes |

---

## 11. Next Phase Planning Target

The next planning-only phase is **Phase E review/promotion utility**.

Phase E should define:

- A human or AI-assisted review workflow for pending global rule candidates.
- How candidates transition from `pending` to `under_review`, `rejected`, `promoted`, or `deferred`.
- Criteria for promoting a candidate to an `approved_global_rule` (validator update, rule catalog change, or prompt contract addition).
- Safety: never auto-apply; no global rule promotion without explicit approval.
- UI/command integration considerations (optional; may remain CLI-only).
- Regression requirements before implementation.

Keep automatic promotion out of Phase E planning unless explicitly scoped and approved. Phase E is review/promotion utility planning only, not automatic global rule activation.

---

## Guardrails for Implementation

- Start from a clean `origin/main` after verifying repo state.
- Do not edit renderer layout or existing C7-C10 validators.
- Add one correction module at a time.
- Add regression tests before expanding scope.
- Run existing C7, C8, C9, C10, CCI, intake, correction, and session correction regressions after every new module.
- Verify GitHub Actions remains green before moving to the next phase.
- Keep all correction storage auditable and reversible.
- Never store raw PII in global or review logs.
- Never commit session JSONL stores.

---

**Original plan:** commit `84a1b2e`.  
**Phase A completed:** commit `71ddf64`.  
**Latest checkpoint:** `8c863ff` — Docs: Add Phase A session persistence checkpoint.  
**Next phase:** Phase B correction classification planning.
