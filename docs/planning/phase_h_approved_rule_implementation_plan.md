# Phase H Approved-Rule Implementation Plan

**Current Verified Baseline:** `cb988bc` — CCI: Add natural language command mediation (Phase G)
**Previous Baseline:** `4ba5cd3` — CCI: Add command integration layer (Phase F)
**Branch:** `main`
**Status:** Planning-only; not approved for implementation.
**Scope:** Define how approved global rule records move from `implementation_status="pending_implementation"` into actual deterministic behavior, without automatic enforcement and without silent AI-only implementation.

---

## 1. What an Approved Global Rule Record Is

An approved global rule record is a structured record produced by `src/correction_review.py` after a human reviewer claimed a pending candidate, validated its evidence (Sec. 5), recorded a decision, and explicitly approved it. It contains:

- `correction_id` — unique identifier of the original correction.
- `field_path` — canonical field path the correction targets.
- `corrected_value` or `rule_description` — the intended rule or corrected content.
- `classification` — `possible_secnav_manual_rule` or `bug_validator_gap`.
- `secnav_citation` — required for manual rules; chapter, section, page, or figure reference in SECNAV M-5216.5.
- `validator_evidence` — required for validator gaps; description of the gap.
- `reviewer` — human reviewer identifier.
- `review_date` — ISO 8601 timestamp of review decision.
- `implementation_status` — lifecycle status string (Sec. 8).
- `implementation_target` — one of: `validator_update`, `rule_catalog`, `prompt_contract`, `documentation_only`, `none_needed` (Sec. 6).
- `implementation_plan_summary` — free-text planning notes, populated during Phase H.

Approved records are stored in `corrections/approved_rule_promotions.json` which is gitignored and local-only.

**Important:** `implementation_status="pending_implementation"` means the record has been approved by a human reviewer but has **not** been turned into any runnable code, rule catalog entry, or prompt contract. It is a human-approved intent only.

---

## 2. What Records Are Eligible for Implementation Planning

Only approved records meeting **all** of the following are eligible:

1. `implementation_status` is `pending_implementation`.
2. `review_decision` is `approved` (not `rejected`, `deferred`, or `superseded`).
3. `secnav_citation` is present and verifiable for `possible_secnav_manual_rule` corrections.
4. `validator_evidence` is present for `bug_validator_gap` corrections.
5. The record is not duplicate or contradictory with an already-implemented rule.
6. The reviewer is still the listed `reviewer`; if a different reviewer takes over, the record must be re-reviewed.

---

## 3. What Records Are Not Eligible

Records are **not eligible** for implementation planning if any of the following is true:

- `review_decision` is `rejected`, `deferred`, or `superseded`.
- Missing required `secnav_citation` for `possible_secnav_manual_rule`.
- Missing required `validator_evidence` for `bug_validator_gap`.
- `classification` is `one_time_wording` or `local_command_preference` (these belong in session/profile scope, not global rules).
- The correction targets renderer output placement, font sizing, or paragraph spacing (renderer changes require separate layout-review).
- The correction is command-specific rather than SECNAV-mandated (e.g., a local routing custom).
- The reviewer reclassified the record during review to a scope other than global rule.

---

## 4. Required Human Review Before Implementation

Every eligible record must pass a **second human gate** before implementation:

1. **Claim step:** A human implementer (who may or may not be the original reviewer) claims the record for implementation planning.
2. **Source verification step:** The implementer confirms `secnav_citation` or `validator_evidence` against the actual SECNAV M-5216.5 manual or the existing validator code.
3. **Scope confirmation step:** The implementer decides whether the rule belongs in the global validator, rule catalog, prompt contract, or documentation only (Sec. 6).
4. **Approval step:** The implementer records an `implementation_approved` decision with a rationale before any code is changed.

No AI or automated process may claim, verify, or approve implementation planning. This gate cannot be bypassed by Phase F or Phase G command mediation.

---

## 5. Required SECNAV M-5216.5 Source Verification

Before any implementation, the following sources must be checked and cited:

1. Chapter/section text surrounding the figure or rule.
2. Figure title and caption.
3. Instructional text inside the figure example itself.
4. Existing project rule files under `rules_v6/CCI/`.
5. Existing validator behavior in `src/cci_*.py`.
6. Existing renderer behavior in `src/pdf_v6_render.py` (read-only for understanding impact).

If `secnav_citation` references a figure, the implementer must review that figure's layout profile in `docs/layout_profiles/` to confirm the rule does not conflict with verified layout audit targets.

Source verification must be recorded in the approved record's `implementation_plan_summary` field.

---

## 6. How to Distinguish Implementation Targets

Every eligible record must be assigned an `implementation_target` before planning is complete:

| Target | Description | Example |
|---|---|---|
| `validator_update` | Add or modify a deterministic CCI validator in `src/cci_*.py`. | Add a validator that flags terminal periods in subject lines. |
| `rule_catalog` | Add a provenance-tracked rule entry under `rules_v6/CCI/`. | Document figure-source evidence for a new multiple-address distribution rule. |
| `prompt_contract` | Add or modify an AI-drafting prompt contract or system instruction. | Update the default drafting prompt to include a new acronym first-use rule. |
| `documentation_only` | Update project docs without changing runtime behavior. | Add a developer note in `docs/planning/` about a discovered convention. |
| `none_needed` | The human reviewer already applied the change elsewhere, or the correction was rendered obsolete by a previous implementation. | A validator gap that was fixed independently. |

A single approved record may have **multiple** targets, but each target must be tracked separately in the implementation plan.

---

## 7. How Approved Records Move Through Statuses

The lifecycle is strictly sequential and gated by human approval:

```
pending_implementation
  -> implementation_planned    (human implementer claims and scopes the record)
  -> implemented                 (human implementer writes code/docs and records completion)
  OR
  -> rejected_for_implementation (human implementer decides record is invalid or unenforceable)
  OR
  -> deferred                    (human implementer decides to postpone without rejecting)
  -> (later may move to implementation_planned or rejected_for_implementation)
  OR
  -> superseded                  (a newer approved record replaces this one)
  -> (record remains archived for audit; never reactivated)
```

**Status transitions:**

- `pending_implementation` -> `implementation_planned`: requires claim + source verification + target assignment.
- `implementation_planned` -> `implemented`: requires code/docs merge, all regressions pass, and human sign-off.
- Any status -> `rejected_for_implementation`: requires human rationale.
- Any status (except superseded) -> `deferred`: requires human rationale and an optional `deferred_until` date.
- Any status -> `superseded`: requires reference to the newer `superseded_by_record_id`.

---

## 8. Required Statuses

| Status | Meaning | Who sets it |
|---|---|---|
| `pending_implementation` | Approved by reviewer; awaiting implementer claim. | Phase E review utility |
| `implementation_planned` | Implementer claimed, verified source, assigned targets, recorded plan. | Phase H implementation planner |
| `implemented` | Code/docs merged; regression verified. | Phase H implementer |
| `rejected_for_implementation` | Record deemed infeasible or invalid after source verification. | Phase H implementer |
| `deferred` | Postponed; may be revisited later. | Phase H implementer |
| `superseded` | Replaced by a newer record; archived. | Phase H implementer or reviewer |

---

## 9. How to Prevent Automatic Enforcement

Phase H must prevent automatic enforcement through these controls:

1. **No runtime auto-loading of approved records:** Approved records are never automatically imported by `src/validator_runner.py`, `src/intake_orchestrator.py`, or `src/pdf_v6_render.py` at runtime.
2. **Explicit registration only:** A rule becomes enforceable only when a human implementer writes the validator code, rule catalog entry, or prompt contract and it is merged to `main`.
3. **No background polling:** No cron process, background task, or CI job may read `corrections/approved_rule_promotions.json` and apply changes without human authorization.
4. **Phase F/G command layer exclusion:** The `/approved rules` command in Phase F lists rules but does not and cannot trigger implementation. Phase G NL mediation cannot issue implementation commands.
5. **Separation of approval and implementation:** Phase E reviewers approve candidate rules. Phase H implementers plan and execute implementation. These are intentionally different roles.
6. **Phase H planning does not approve enforcement:** Phase H may plan implementation targets and statuses, but it must not automatically modify validators, rule catalogs, prompt contracts, or renderer/layout behavior. Approved records remain non-enforcing until a separate implementation task is planned, approved, implemented, reviewed, and regression-tested.

---

## 10. How to Prevent AI-Only Rule Implementation

1. **No AI/LLM imports in implementation tools:** If `src/correction_implementation_planner.py` is created (future), it must not use AI to decide whether a rule is valid, to generate validator logic, or to rewrite rule catalog provenance.
2. **No AI-generated code without human review:** Any code produced with AI assistance must be reviewed by a human implementer before merge.
3. **No AI-only evidence validation:** The `secnav_citation` and `validator_evidence` are verified by the human implementer, not by an AI.
4. **Audit trail:** Every implementation decision must record the human implementer ID and verification timestamp.

---

## 11. How to Preserve Renderer/Layout Behavior

- **Renderer read-only during source verification:** Implementers may read `src/pdf_v6_render.py` to understand impact, but renderer edits require a separate layout-review and cannot be done as a side effect of rule implementation.
- **Layout profiles are truth:** If an approved rule implies a layout change, it must be scoped as a separate layout task, not bundled with validator updates.
- **No new render targets:** Phase H implementation does not modify `src/pdf_v6_render.py`, `src/body_v6_validate.py`, or layout profiles.
- **Regression protection:** All 23 existing regression suites must pass after any implementation. Any layout or render regression failure blocks merge.

---

## 12. How to Preserve Validator/Rule Catalog Provenance

1. **Every new rule catalog entry must include:** `manual_chapter`, `manual_section`, `page_or_figure`, `source_quote`, `effective_date`, and `added_by_implementation_id`.
2. **Every validator update must include:** a docstring citing the SECNAV source and the approved record ID.
3. **No rule catalog deletion without deprecation:** Existing rules may be deprecated but not silently removed. Deprecation requires a new record with `status=deprecated` and a `supersedes` reference.
4. **Version tracking:** The rule catalog or validator module should maintain a `_catalog_version` or `_validator_version` integer bumped per implementation.
5. **Diff review:** All validator/rule catalog changes must be reviewable in git diff with clear citations.

---

## 13. How to Test Validator/Rule Catalog Changes

If later approved for implementation, the following testing requirements apply:

1. **Unit tests for each new validator:** Every new `src/cci_*.py` addition must have a corresponding unit-style test in `tools/run_cci_*_regression.py` and a temporary fixture in `examples/audit_cci_*.json`.
2. **Negative tests:** The new validator must be tested against at least one fixture that should **fail** the new rule.
3. **Existing regression insulation:** All existing C7–C10, CCI intake, correction, and session regression suites must still pass.
4. **Impact audit:** Before merge, run all 23 regression suites and verify no new warnings or failures in any existing layout audit profile.
5. **Rollback test:** If feasible, test reverting the implementation code and confirm existing regressions still pass.

---

## 14. How to Handle Approved Records That Are Actually Local Command Preferences

If during source verification the implementer discovers the approved record is command-specific rather than SECNAV-wide:

1. **Do not implement as a global rule.**
2. **Reclassify the record:** Change `implementation_target` to `none_needed` and add a `reclassification_note`: "This correction reflects a local command preference, not a SECNAV-mandated rule."
3. **Redirect to Phase C:** If the user wants the preference persisted, recommend Phase C local command profile promotion via `/promote profile`.
4. **Status to `rejected_for_implementation`:** Record the rationale and archive.

---

## 15. How to Handle Approved Records That Are Validator Gaps

If the record is classified as `bug_validator_gap`:

1. **Implementer must reproduce the gap** using an existing or new audit fixture.
2. **Two implementation options:**
   - **Validator update:** Add the missing check to the appropriate `src/cci_*.py` validator.
   - **Rule catalog entry:** If the gap reflects a manual rule not yet in the catalog, add a `rules_v6/CCI/` entry first, then consider a validator update in a later Phase H iteration.
3. **Status transition:** After implementation and regression verification, set `implementation_status` to `implemented`.
4. **If unfixable:** If the gap is due to ambiguity in the manual itself, status becomes `rejected_for_implementation` with a note citing the ambiguity.

---

## 16. Required Regression Coverage

Before any Phase H implementation is considered complete, the following must pass:

| Suite | Minimum |
|---|---|
| `run_correction_nl_command_regression.py` | 151/151 |
| `run_correction_command_regression.py` | 45/45 |
| `run_correction_review_regression.py` | 30/30 |
| `run_correction_pending_regression.py` | 33/33 |
| `run_correction_profile_promotion_regression.py` | 33/33 |
| `run_correction_classify_regression.py` | PASS |
| `run_intake_regression.py` | PASS |
| `run_correction_regression.py` | PASS |
| `run_correction_session_regression.py` | PASS |
| `run_profile_regression.py` | PASS |
| `run_cci_audit_regression.py` | PASS |
| `run_context_schema_regression.py` | PASS |
| `run_cci_subject_regression.py` | PASS |
| `run_cci_ref_encl_regression.py` | PASS |
| `run_cci_acronym_regression.py` | PASS |
| `run_cci_date_time_regression.py` | PASS |
| `run_cci_personnel_regression.py` | PASS |
| `run_cci_poc_regression.py` | PASS |
| `run_cci_routing_regression.py` | PASS |
| `run_c7_phase1_regression.py` | PASS |
| `run_c8_regression.py` | PASS |
| `run_c9_regression.py` | PASS |
| `run_c10_regression.py` | PASS |

**Additionally:** Any new validator or rule catalog change must have its own targeted regression runner added to the suite (e.g., `tools/run_new_validator_regression.py`).

---

## 17. Files That Would Be Added or Changed in Future Implementation

### Phase H planner implementation files (require separate approval)

- `src/correction_implementation_planner.py` — implementation planning utility: claim eligible records, assign targets, record planning decisions, enforce status transitions. No AI imports; no renderer/validator imports.
- `tools/run_correction_implementation_regression.py` — Phase H regression runner verifying status transitions, eligibility gating, and record integrity.
- Future checkpoint docs after implementation, such as `docs/checkpoints/phase_h_approved_rule_implementation_checkpoint.md`.

### Pilot rule implementation files (separate later phase, e.g. Phase H.1 or Phase I)

If a pilot rule is later approved for implementation, the following files may be modified or created in that **separate** implementation task:

- `rules_v6/CCI/` — new rule catalog entries if target is `rule_catalog`.
- `src/cci_*.py` — validator updates if target is `validator_update`.
- `src/intake_orchestrator.py` — possible prompt-contract integration if target is `prompt_contract`.
- `docs/` — documentation updates if target is `documentation_only`.
- New validator-specific regression runners.

### Local-only file handling

- `corrections/approved_rule_promotions.json` is gitignored and local-only. The Phase H planner must read it from its local path but must not assume it exists in the repository.
- Tests and regressions must use synthetic or temporary fixtures only. Real approved promotion logs must not be committed.
- Any direct file modification of `corrections/approved_rule_promotions.json` in implementation code must be clearly isolated and not trigger git-tracked changes.

### Files that must NOT be modified

- `src/pdf_v6_render.py` — layout changes require separate approval.
- `docs/layout_profiles/` — layout profile changes require separate approval.
- `src/correction_commands.py` — Phase F remains dispatch authority; no new commands unless separately designed.
- `src/correction_nl_commands.py` — Phase G remains NL mediator; no new intents unless separately designed.

---

## 18. What Phase H Must NOT Do

Phase H implementation must never:

- **No automatic global rule enforcement:** Approved records do not become active without human implementation and merge.
- **No validator/rule catalog modification unless separately approved after planning:** Planning alone does not grant implementation permission.
- **No renderer/layout changes:** Any layout implications require a separate layout-review task.
- **No AI-only rule implementation:** AI may assist drafting but cannot approve, verify sources, or sign off.
- **No real command/user data committed:** No test fixtures may contain real profiles, contact data, or session stores.
- **No silent implementation of approved records:** Every implementation step is logged with human attribution.
- **No background automation:** No cron jobs, watchers, or CI triggers may implement rules automatically.
- **No combined planner and pilot rule commit:** The planner implementation commit must not include any actual validator, rule catalog, prompt contract, or renderer changes.

---

## Recommended Phase H Implementation Sequence

Phase H implementation is split into two distinct, separately approved stages:

### Stage 1: Approved-Rule Implementation Planner (Phase H)

This stage implements only the planning and status workflow. It does **not** implement any actual validator, rule catalog, prompt contract, or renderer change.

1. **Create `src/correction_implementation_planner.py`** with status-transition enforcement, claim/verify/assign-target flow, and audit logging. No AI imports; no renderer/validator imports.
2. **Add Phase H regression runner** (`tools/run_correction_implementation_regression.py`) with at least 30 checks: eligibility gating, status transition correctness, target assignment, reclassification and local-preference rejection, and source verification requirements.
3. **Update `docs/PROJECT_STATUS.md`** and `docs/planning/correction_memory_and_rule_promotion_plan.md` to reflect Phase H completion.
4. **Run all 23 regression suites** and verify no failures.
5. **Commit:** `CCI: Add approved rule implementation planner (Phase H)`.

### Stage 2: Pilot Rule Implementation (Phase H.1 or Phase I)

This stage is a **separate, later approved task** that may implement one or more actual rules into validators, rule catalogs, or prompt contracts. It must not proceed until Stage 1 is complete and separately approved.

1. **Select one pilot rule** for the first implementation (e.g., subject terminal-period validator or ref/encl duplicate validator).
2. **Implement it fully** through the Phase H planner process.
3. **Add the new validator/rule catalog entry-specific regression** to the CI suite.
4. **Run all 23 regression suites** and verify no failures.
5. **Commit separately:** e.g. `CCI: Implement pilot approved rule (Phase H.1)`.

Pilot rule implementation must be planned, approved, and scoped independently from the planner implementation. It is not part of Phase H.

---

## Open Questions Needing Approval

This planning document cannot be finalized until the following are decided:

1. **Pilot rule selection:** Which approved record should be the first pilot implementation to prove the process? (This is a Phase H.1 / Phase I decision, not a Phase H decision.)
2. **Implementer role separation:** Should the Phase H implementer be the same role as the Phase E reviewer, or strictly separate?
3. **Rule catalog versioning:** Should `rules_v6/CCI/` adopt a formal `_catalog_version` integer, or is git history sufficient?
4. **Deprecation policy:** If an implemented rule is later found invalid, should it be fully removed or kept with `status=deprecated` and `superseded_by`?
5. **CI enforcement:** Should GitHub Actions require the new Phase H regression runner before merge, or is 23 existing suites sufficient until the first pilot is implemented?
6. **Prompt contract scope:** Are prompt-contract updates in scope for Phase H, or should they be deferred to a separate drafting-prompts phase?
7. **Multi-target rules:** Can a single approved record spawn both a rule catalog entry and a validator update in the same Phase H iteration, or must they be sequential?

---

End of Phase H Approved-Rule Implementation Plan.
