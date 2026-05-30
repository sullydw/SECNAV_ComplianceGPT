# Correction Memory and Rule Promotion Layer Plan

## 1. Purpose

The system must allow a user to correct an error in the active draft, apply that correction immediately, rerun validators, regenerate output, and store the correction for scoped reuse.

When a user identifies a problem in a generated draft (e.g., wrong wording in the subject line, incorrect From line title, missing Via addressee, improper personnel identification format), they should be able to specify the correction once, see it applied immediately, and have the system remember that correction so that future drafts in similar contexts do not repeat the same mistake — provided it is safe to do so.

The Correction Memory and Rule Promotion Layer is not a replacement for deterministic SECNAV validators. It is a user-driven feedback loop that sits alongside the CCI layer, with strict guardrails preventing unreviewed local preferences from becoming global compliance rules.

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

| Scope | Auto-reuse | Description |
|---|---|---|
| `active_draft` | Yes — immediate | Correction applies only to the draft currently being edited. It is used once, immediately, and discarded afterward unless the user chooses to remember it. |
| `current_session` | Yes — when context matches | Correction persists for the remainder of the current user session. Reused automatically when document type, component, and affected field match. |
| `local_command_profile` | Yes — after explicit user approval | Correction becomes part of a named local command profile (e.g., "USS NEVERSAIL local preferences"). Must be approved by the user before activation. |
| `pending_global_rule_candidate` | No — manual review only | Correction is logged as a candidate for a global SECNAV compliance rule or validator update. It is never auto-applied. A human reviewer must evaluate whether it reflects a real manual requirement, a validator gap, or a local preference. |
| `approved_global_rule` | Yes — enforced | Correction has been reviewed, validated against SECNAV M-5216.5 text, and promoted into the rule catalog, validator code, or AI prompt contract. |

---

## 4. Correction Workflow

When a user issues a correction command or selects a correction in a future UI:

1. **Capture original generated value** — snapshot the field value before modification.
2. **Capture corrected value** — record the user's intended replacement.
3. **Capture field/path affected** — JSON path or canonical field name (e.g., `subj`, `from`, `body[2]`, `via[0]`).
4. **Capture document type** — standard_letter, endorsement, memorandum_for_record, etc.
5. **Capture component context** — navy, marine_corps, joint, don_secretariat, unknown.
6. **Capture user explanation** — free-text reason for the correction, used for classification and audit.
7. **Classify correction type** — one of:
   - `one_time_wording` — stylistic or situational change that should not persist.
   - `local_command_preference` — command-specific convention that is not universal.
   - `possible_secnav_manual_rule` — the correction suggests a rule from the manual that the system is not yet enforcing.
   - `bug_validator_gap` — the correction reveals a bug or missing check in a deterministic validator.
8. **Apply correction to current draft** — mutate the active payload in memory.
9. **Rerun applicable CCI validators** — run validators that inspect the affected field.
10. **Rerender PDF if draft passes** — only if all validators pass or the user explicitly overrides.
11. **Store correction record** — write a structured record to the appropriate scope.

---

## 5. Correction Reuse Behavior

### active_draft
- The correction is applied once to the current payload.
- If the user does not choose to remember it, the record is discarded after rendering.

### current_session
- The correction is stored in an in-memory or lightweight JSONL session store.
- On each new draft generation within the same session, the system checks whether the document type, component, and affected field match a stored correction.
- If all context keys match, the correction is pre-applied before validators run, and a note is emitted: "Applied session correction for field X."
- If the user rejects the pre-applied correction, it is removed from session memory for that context combination.

### local_command_profile
- The user must explicitly approve adding the correction to a named local profile.
- The profile is stored as `corrections/local_command_overrides.json` or similar.
- Corrections in this scope are applied automatically when the active profile is selected.
- Multiple profiles may exist (e.g., one per command, one per department).
- A correction in a local profile can be disabled or edited later.

### pending_global_rule_candidate
- Corrections classified as `possible_secnav_manual_rule` or `bug_validator_gap` are written to `corrections/pending_corrections.jsonl`.
- They are never auto-applied to other users or other sessions.
- A periodic review process (human or AI-assisted) inspects pending candidates, groups duplicates, and decides whether to:
  - promote to an approved global rule,
  - reject as a local preference,
  - convert into a validator improvement ticket.

### approved_global_rule
- Once reviewed and approved, the correction becomes a deterministic rule in `rules_v6/CCI/`, a validator update in `src/cci_*.py`, or a prompt-contract addition.
- It is enforced through the normal CCI pipeline and requires regression tests before release.

---

## 6. Safety Guardrails

- **User correction shall never silently override a deterministic SECNAV validator.** If a correction conflicts with a validator finding, the system must surface the conflict and require user review.
- **If a correction conflicts with a validator, show conflict and require review.** The user may choose to override the validator for this draft only, escalate the correction as a bug/validator gap, or abandon the correction.
- **User correction shall not become a global rule without review.** The `pending_global_rule_candidate` scope ensures every proposed global change is inspected.
- **Local overrides must be scoped to command/profile.** A local command preference cannot leak into the default global behavior.
- **All correction records should be auditable and reversible.** Every record stores original value, corrected value, timestamp, classification, and user explanation. Corrections can be disabled, deleted, or rolled back.
- **Privacy/PII corrections must not store sensitive data unnecessarily.** If a correction touches a field containing PII, the system should store a sanitized or hashed representation of the change, or store the correction rule without storing the actual sensitive value.

---

## 7. Suggested Future Files

### Implementation modules
- `src/correction_apply.py` — apply a single correction to a payload JSON object given a field path and corrected value.
- `src/correction_capture.py` — capture correction metadata from user input and build a structured correction record.
- `src/correction_classify.py` — classify a correction into one of the four types using heuristics and optional AI assistance.
- `src/correction_reuse.py` — query stored corrections by context and pre-apply matching ones to a new draft payload.

### Storage files
- `corrections/pending_corrections.jsonl` — append-only log of pending global rule candidates.
- `corrections/local_command_overrides.json` — per-profile local override dictionary.
- `corrections/approved_rule_promotions.json` — record of corrections promoted to global rules, with reviewer, date, and rationale.

### Rule catalog and regression
- `rules_v6/CCI/cci_correction_feedback_rules.json` — metadata for correction-related feedback rules (e.g., which fields are eligible for correction, which corrections require conflict detection).
- `tools/run_correction_feedback_regression.py` — regression runner that exercises the correction apply/capture/classify/reuse pipeline against test payloads.

---

## 8. Example Scenarios

### 8.1 Subject punctuation correction
- **Original**: `Subj: POLICY UPDATE.`
- **Correction**: remove terminal period.
- **Classification**: `possible_secnav_manual_rule` — the subject-line validator already catches this, so this scenario is more likely a validator miss or user override.
- **Scope**: if validator missed it, `bug_validator_gap` → pending. If user overrode intentionally, `one_time_wording` → active_draft.

### 8.2 From line corrected from individual name to Commanding Officer
- **Original**: `From: John A. Smith`
- **Correction**: `From: Commanding Officer, USS NEVERSAIL`
- **Classification**: `possible_secnav_manual_rule` — command letterhead From lines should contain activity head title and command/activity name, not an individual.
- **Scope**: `pending_global_rule_candidate` if the validator does not already enforce this. If this is a recurring local need, `local_command_preference` after user approval.

### 8.3 Local originator code preference
- **Original**: sender symbol lacks originator code.
- **Correction**: add local originator code `N7`.
- **Classification**: `local_command_preference` — not a universal SECNAV rule.
- **Scope**: `local_command_profile` after user approval.

### 8.4 Navy vs Marine Corps personnel wording correction
- **Original**: body text uses "Marine" lowercase.
- **Correction**: capitalize "Marine".
- **Classification**: `possible_secnav_manual_rule` — the planned personnel validator will catch this, so this scenario mainly exists for validator-gap discovery.
- **Scope**: `bug_validator_gap` if the validator missed it; otherwise `one_time_wording`.

### 8.5 Missing Via routing rule discovered
- **Original**: draft omits an intermediate Via addressee that chain of command requires.
- **Correction**: add the Via addressee.
- **Classification**: `possible_secnav_manual_rule` — routing intelligence is planned but not yet implemented.
- **Scope**: `pending_global_rule_candidate` for the routing/Via validator backlog.

### 8.6 One-time wording change that should not become rule
- **Original**: body paragraph uses a specific example sentence.
- **Correction**: user rewords the example for this particular letter.
- **Classification**: `one_time_wording`.
- **Scope**: `active_draft` only. The system must not store this in session or profile memory unless the user explicitly overrides the classification.

---

## 9. Relationship to AI Drafting

- **AI may propose corrections and ask whether to remember them.** When the AI detects a likely error during drafting, it can suggest a correction and ask the user: "Apply this correction to the current draft? Remember for this session? Add to local profile?"
- **AI may classify likely correction scope.** Using the correction classifier, the AI can suggest a classification and ask the user to confirm.
- **Deterministic validators remain final authority for implemented hard rules.** A user or AI correction that conflicts with a deterministic validator must be surfaced as a conflict, not silently accepted.
- **Unresolved conflicts become human-review items.** If the user insists on a correction that violates a validator, the draft is flagged for human review before release.

---

## 10. Future Implementation Sequence

| Phase | Task | Scope |
|---|---|---|
| 1 | Correction record schema | Define JSON schema for correction records with all required fields. |
| 2 | Active draft correction apply function | Implement `src/correction_apply.py` with JSON path resolution and payload mutation. |
| 3 | Session memory reuse | Implement `src/correction_reuse.py` for `current_session` scoped lookups and pre-application. |
| 4 | Local command override profile | Implement `local_command_overrides.json` structure and user approval workflow. |
| 5 | Pending rule candidate log | Implement `pending_corrections.jsonl` append-only logging with grouping/deduplication. |
| 6 | Review/promotion utility | Implement a human or AI-assisted review tool that inspects pending candidates and promotes or rejects them. |
| 7 | Regression tests | Add `tools/run_correction_feedback_regression.py` and fixtures for apply, capture, classify, reuse, and conflict detection. |
| 8 | Later UI integration | Wire correction commands into any future chat or web interface so users can issue corrections naturally. |

---

## Guardrails for Implementation

- Start from a clean `origin/main` after verifying repo state.
- Do not edit renderer layout or existing C7-C10 validators.
- Add one correction module at a time.
- Add regression tests before expanding scope.
- Run existing C7, C8, C9, C10, and CCI regressions after every new module.
- Verify GitHub Actions remains green before moving to the next phase.
- Keep all correction storage auditable and reversible.
- Never store raw PII in correction logs.

---

*Plan generated 2026-05-29. See commit `1597199f11c1be9b493a48bc28d46bcb390210eb`.*
