# Phase H.1 / Phase I Pilot Approved-Rule Implementation Plan

**Current Verified Baseline:** `2588e67` — CCI: Add approved rule implementation planner (Phase H)  
**Previous Baseline:** `cb988bc` — CCI: Add natural language command mediation (Phase G)  
**Branch:** `main`  
**Status:** Planning-only; not approved for implementation.  
**Scope:** Define how the first approved global rule record is selected, verified, implemented, and regression-protected as a pilot. No broad validator rewrites. No renderer/layout changes. No automatic enforcement. No AI-only implementation.

---

## 1. Purpose

Phase H Stage 1 (`src/correction_implementation_planner.py`) provides the planning and status-workflow infrastructure for approved-rule implementation. Phase H.1 / Phase I is the **first actual pilot implementation** of one approved record into deterministic behavior (validator, rule catalog, prompt contract, or documentation).

This plan defines:
- How to select a single pilot record safely.
- What evidence is required before selection.
- How to verify the record through the Phase H planner.
- How to decide the implementation target and keep scope small.
- How to prevent premature enforcement, AI-only implementation, and silent activation.
- How to preserve renderer/layout behavior and validator/rule catalog provenance.
- How to test, regress, and sign off before the approved record status becomes `implemented`.

**Phase H.1 / Phase I is planning-only until reviewed and approved.** No code may be written under this plan without separate user approval.

---

## 2. How to Select One Pilot Approved Record

### 2.1 Eligibility

The pilot must be **one** approved record that satisfies all of the following:

1. `implementation_status` is `pending_implementation` or `implementation_planned`.
2. `review_decision` is `approved`.
3. `secnav_citation` is present and verifiable (for `possible_secnav_manual_rule`).
4. `validator_evidence` is present (for `bug_validator_gap`).
5. The record is not `deferred`, `rejected_for_implementation`, or `superseded`.
6. The record is not duplicate or contradictory with an already-implemented rule.
7. The record's `field_path` does **not** target renderer output placement, font sizing, or paragraph spacing.
8. The record is **not** command-specific (e.g., local routing custom, command-specific originator code).
9. The record has been claimed and scoped through the Phase H planner (`claim_record_for_implementation` + `plan_implementation`).

### 2.2 Recommended Pilot Selection Criteria

| Criterion | Why |
|---|---|
| **Low blast radius** | The rule touches a narrow, well-understood field (e.g., `subj` punctuation, `ref` duplicate detection, single-line `from` title format). |
| **Deterministic** | The rule can be expressed as a deterministic check, not a heuristic or AI judgment. |
| **SECNAV M-5216.5 figure text is explicit** | The manual figure or chapter text directly supports the rule; no interpretation required. |
| **Existing validator exists nearby** | A related validator already exists in `src/cci_*.py`, so the pattern is established. |
| **No layout implication** | The rule does not affect x/y coordinates, margins, font metrics, or paragraph spacing. |
| **No prompt-contract ambiguity** | The rule is not better solved by changing the AI drafting prompt; it belongs in deterministic validation. |
| **Reversible** | If the rule causes false positives, it can be disabled by reverting one validator or one catalog entry. |

### 2.3 Preferred Pilot Categories (in order of preference)

For the first pilot, prefer the lowest-risk implementation target that still proves the Phase H.1 process:

1. **Documentation-only improvement** — a record that only requires adding a developer note or manual reference to project docs. No runtime change.
2. **Missing rule catalog entry** — a `possible_secnav_manual_rule` where the rule is real but not yet tracked in `rules_v6/CCI/`.
3. **Very narrow validator gap fix** — a `bug_validator_gap` record where the validator simply misses a clear SECNAV rule, the change is low-blast-radius, and a related validator already exists.
4. **Prompt-contract update** — deferred to a separate approved task; see Sec. 12.

A validator pilot is acceptable only if a very narrow candidate is already available, the SECNAV source is explicit, and the implementation can be regression-protected without broad validator rewrites.

**Avoid as first pilot:**
- Rules that affect body paragraph structure or multi-line formatting.
- Rules that require new layout profile bounds or render target changes.
- Rules that depend on command-specific data not present in the generic SECNAV manual.
- Rules with ambiguous manual text or conflicting figure examples.

---

## 3. Evidence Required Before Selecting the Pilot

Before any record is selected as the pilot, the implementer must collect and record the following evidence in the Phase H planner's `source_verification_summary`:

1. **SECNAV M-5216.5 direct citation** — chapter, section, page, or figure reference.
2. **Figure text** — the exact wording inside the figure that supports the rule.
3. **Existing validator behavior** — output of the relevant `src/cci_*.py` validator on a fixture that demonstrates the gap.
4. **Existing rule catalog state** — whether `rules_v6/CCI/` already has a related entry.
5. **Renderer impact assessment** — a note confirming the rule does **not** imply layout or render changes.
6. **Rollback feasibility** — a one-sentence description of how to revert the change.

Evidence must be recorded in the approved record's `implementation_plan_summary` before the pilot is formally selected.

---

## 4. How to Verify the Approved Record Through the Phase H Planner

### 4.1 Claim the record

Use `correction_implementation_planner.claim_record_for_implementation(rule_id=my_rule_id, implementer_id="my_name", approved_path=None)`.

- `approved_path` is optional; when omitted, the planner uses the default local path.
- If the record is already claimed by another implementer, the planner returns a warning.
- If the record is `deferred`, it may be reclaimed.

### 4.2 Validate eligibility

Call `correction_implementation_planner.validate_eligibility(record)`.

- Must return `eligible=True`.
- Must include `secnav_citation` or `validator_evidence` in the summary.

### 4.3 Assign implementation target

Call `correction_implementation_planner.plan_implementation(...)` with:

- `rule_id` — the approved record ID.
- `implementer_id` — human identifier.
- `implementation_target` — one of `validator_update`, `rule_catalog`, `prompt_contract`, `documentation_only`, `none_needed`.
- `source_verification_summary` — the six evidence items from Sec. 3.
- `implementation_plan_summary` — optional; scope documentation from Sec. 4.4.
- `approved_path` — optional; when omitted, the planner uses the default local path.

This transitions the record to `implementation_planned`.

### 4.4 Scope the implementation work

Before writing code, document the exact change:

- Which file(s) will be modified.
- Which function(s) or catalog entry/ies will be added or changed.
- What the new behavior is.
- What fixtures will be added for testing.
- Estimated blast radius (number of existing fixtures that might be affected).

---

## 5. How to Decide the Implementation Target

Every pilot must be assigned **one** primary target. A record may have secondary targets, but each secondary target requires a separate planning and approval step.

| Target | When to choose | Files that may change | Files that must NOT change |
|---|---|---|---|
| `validator_update` | The approved rule describes a deterministic check that can be added to an existing `src/cci_*.py` validator. | One or more `src/cci_*.py` files. Corresponding `tools/run_cci_*_regression.py` or new runner. | `src/pdf_v6_render.py`, `docs/layout_profiles/`, `src/correction_commands.py`, `src/correction_nl_commands.py` |
| `rule_catalog` | The rule is real in SECNAV M-5216.5 but not yet tracked in `rules_v6/CCI/`. | Add a new `.json` or `.yaml` entry under `rules_v6/CCI/`. | Any validator, renderer, or prompt-contract file. |
| `prompt_contract` | The rule is better enforced by changing the AI drafting prompt (e.g., new system instruction or example). | Separate approved task only; may modify prompt template files. | Deterministic validators must remain unchanged. |
| `documentation_only` | The rule is already implemented elsewhere, or only needs a developer note. | `docs/planning/`, `docs/checkpoints/`, `README.md`. | No runtime files. |
| `none_needed` | The approved record is obsolete, already fixed, or describes a local preference. | None. | None. |

### 5.1 Target Decision Checklist

- [ ] Does the rule describe something that can be checked deterministically at validation time? -> `validator_update`
- [ ] Is the rule a manual requirement not yet tracked in the project? -> `rule_catalog`
- [ ] Is the rule about drafting guidance rather than post-generation validation? -> `prompt_contract` (separate task)
- [ ] Is the rule already satisfied by existing code? -> `documentation_only` or `none_needed`
- [ ] Does the rule imply layout, spacing, or formatting changes? -> STOP. Requires separate layout-review task.

---

## 6. How to Keep Pilot Scope Small and Reversible

### 6.1 One rule, one file (ideally)

The first pilot should touch **at most one** of the following per commit:
- One `src/cci_*.py` validator file.
- One `rules_v6/CCI/` catalog entry.
- One docs file.

If a rule requires both a validator update and a rule catalog entry, implement the catalog entry first (Phase H.1) and the validator update second (Phase I), or bundle them in a single commit only if both are small and independently testable.

### 6.2 Feature flag or conditional

Feature flagging depends on target type:

- **Documentation-only pilot:** no feature flag is needed.
- **Rule-catalog-only pilot:** no runtime feature flag is needed unless runtime loading is also changed, which should not happen in the first pilot.
- **Validator pilot:** readiness review must explicitly decide whether feature flagging is required. If there is any false-positive risk, wrap the new validator check in an `if pilot_rule_enabled:` guard or equivalent opt-in mechanism.

### 6.3 Rollback plan

Before implementation, document:
- The exact git command to revert the change (`git revert <commit>` or manual file restore).
- The expected regression result after rollback (all existing suites pass).
- The expected behavior change after rollback (the new check no longer fires, or the new catalog/docs entry is removed).

### 6.4 No cascading refactors

Do not refactor existing validators, restructure `rules_v6/CCI/`, or rename files as part of the pilot. The pilot must be additive or minimally invasive.

---

## 7. How to Prevent Automatic Enforcement Before Implementation Approval

1. **No runtime auto-loading:** `src/validator_runner.py`, `src/intake_orchestrator.py`, and `src/pdf_v6_render.py` do not import or read `corrections/approved_rule_promotions.json`.
2. **No Phase F/G command can trigger implementation:** The `/approved rules` command lists statuses but cannot write validators or catalogs. Phase G NL mediation cannot express implementation commands.
3. **Status gate:** A record cannot move from `implementation_planned` to `implemented` until:
   - Code/docs are written.
   - Targeted regression for the pilot passes.
   - The full existing regression suite passes.
   - A human implementer explicitly updates the record status to `implemented` through the Phase H planner.
4. **No CI auto-implementation:** GitHub Actions does not read approved promotion logs and does not generate or merge code.
5. **No background polling:** No daemon or watcher monitors `corrections/approved_rule_promotions.json`.

---

## 8. How to Prevent AI-Only Rule Implementation

1. **Human implementer claim required:** `claim_record_for_implementation()` requires a human `implementer_id`.
2. **Human source verification required:** `source_verification_summary` must be human-authored evidence, not AI-generated citations.
3. **Human target assignment required:** `implementation_target` is chosen by the human implementer.
4. **AI may assist drafting but not approve:** AI-generated validator code or catalog entries must be reviewed by the human implementer before merge.
5. **Audit trail:** Every `implementation_planned` and `implemented` transition records the human `implementer_id` and `planned_at` timestamp.
6. **No AI/LLM imports in implementation code:** If helper tools are created for Phase H.1 / Phase I, they must not import AI/LLM libraries to generate, evaluate, or sign off on rules.

---

## 9. How to Preserve Renderer/Layout Behavior

1. **Read-only renderer inspection:** Implementers may read `src/pdf_v6_render.py` to understand impact, but must not modify it.
2. **Layout profiles are immutable for Phase H.1 / Phase I:** `docs/layout_profiles/` must not be modified. If a rule implies a layout change, it is out of scope for the pilot.
3. **No new render targets:** `src/pdf_v6_render.py`, `src/body_v6_validate.py`, and layout profiles are off-limits.
4. **Regression gate:** If any C7–C10 layout regression fails after the pilot implementation, the pilot is blocked from merge until the failure is understood and resolved or the pilot is abandoned.
5. **Render-agnostic rules preferred:** Select pilots that affect text content (subject, ref, encl, acronym, routing) rather than spatial positioning.

---

## 10. How to Preserve Validator/Rule Catalog Provenance

1. **Every new rule catalog entry must include:** `manual_chapter`, `manual_section`, `page_or_figure`, `source_quote`, `effective_date`, `added_by_implementation_id`.
2. **Every validator update must include:** a docstring citing the SECNAV source and the approved record ID.
3. **No silent deletion:** Existing rules may be deprecated but not removed. Deprecation requires a new record with `status=deprecated` and `supersedes`.
4. **Version tracking:** Bump `_catalog_version` or `_validator_version` if the module already has one; otherwise, git history is sufficient for the pilot.
5. **Diff review:** All changes must be reviewable in git diff with clear citations.

---

## 11. How to Write Targeted Regression Tests for the Selected Pilot

### 11.1 New regression runner

Create a new runner for the pilot when the target is `validator_update` or `rule_catalog`:

- Name: `tools/run_pilot_<rule_name>_regression.py`
- Checks: minimum 10 (positive + negative + edge cases).
- Fixtures: synthetic/temp JSON fixtures only.
- Must not read/write/modify real local files.
- Must not include real command/user data, contact information, real names, real session data, or real approved-promotion records.

### 11.2 Required test categories

| Category | Minimum | Description |
|---|---|---|
| Positive (rule fires) | 3 | Fixtures that fail the new check. |
| Negative (rule does not fire) | 3 | Fixtures that are compliant and must pass. |
| Edge / boundary | 2 | Boundary values (e.g., empty field, exact length limit, Unicode). |
| Regression insulation | 2 | Existing fixtures re-run to confirm no new failures. |

### 11.3 Example test structure

```python
# tools/run_pilot_subject_terminal_period_regression.py
# Synthetic fixtures only; do not use real command/user data.

def test_subj_with_terminal_period_fails():
    payload = {"subj": "POLICY UPDATE."}
    result = run_cci_subject_validator(payload)
    assert "terminal period" in result["errors"][0].lower()

def test_subj_without_terminal_period_passes():
    payload = {"subj": "POLICY UPDATE"}
    result = run_cci_subject_validator(payload)
    assert result["errors"] == []

def test_existing_fixture_not_broken():
    # Load an obviously synthetic known-good compliance fixture from examples/.
    payload = load_fixture("examples/audit_cci_subject.json")
    result = run_cci_subject_validator(payload)
    assert result["errors"] == []
```

---

## 12. How to Run the Full Regression Set Before Commit

Before any pilot implementation is committed, run the complete existing 24-suite set in order:

1. `python tools/run_correction_implementation_regression.py`
2. `python tools/run_correction_nl_command_regression.py`
3. `python tools/run_correction_command_regression.py`
4. `python tools/run_correction_review_regression.py`
5. `python tools/run_correction_pending_regression.py`
6. `python tools/run_correction_profile_promotion_regression.py`
7. `python tools/run_correction_classify_regression.py`
8. `python tools/run_intake_regression.py`
9. `python tools/run_correction_regression.py`
10. `python tools/run_correction_session_regression.py`
11. `python tools/run_profile_regression.py`
12. `python tools/run_cci_audit_regression.py`
13. `python tools/run_context_schema_regression.py`
14. `python tools/run_cci_subject_regression.py`
15. `python tools/run_cci_ref_encl_regression.py`
16. `python tools/run_cci_acronym_regression.py`
17. `python tools/run_cci_date_time_regression.py`
18. `python tools/run_cci_personnel_regression.py`
19. `python tools/run_cci_poc_regression.py`
20. `python tools/run_cci_routing_regression.py`
21. `python tools/run_c7_phase1_regression.py`
22. `python tools/run_c8_regression.py`
23. `python tools/run_c9_regression.py`
24. `python tools/run_c10_regression.py`

If a new targeted pilot regression runner is added, it becomes the 25th suite for the pilot implementation. Run it in addition to the existing 24 suites and report the final regression set as **25 suites total**:

25. `python tools/run_pilot_<rule_name>_regression.py`

**All 25 must PASS** when a targeted pilot runner is added. Any failure blocks the implementation commit.

---

## 13. How to Update Approved-Record Status After Implementation and Regression Pass

1. After code/docs are written and all suites pass, the human implementer updates the record status to `implemented`.

2. **Required before Phase H.1 can complete Step 2:** Add a public wrapper (e.g., `mark_implemented()`) in `src/correction_implementation_planner.py` that:
   - Accepts `rule_id`, `implementer_id`, and optional `approved_path`.
   - Validates the record is currently `implementation_planned`.
   - Validates the caller is the same `implementer_id` who claimed it.
   - Validates the transition `implementation_planned` -> `implemented` is allowed.
   - Updates the record, appends metadata, writes back locally, and returns the updated record.

3. The internal `_mark_implemented_internal()` exists for synthetic fixture testing only and must not be called directly by implementers. The public wrapper must be added and reviewed before any real record is moved to `implemented`.

4. The implementer records the commit hash where the rule was merged in a `notes` field.

5. **The `corrections/approved_rule_promotions.json` file must not be committed to git.** It remains local-only and gitignored.

---

## 14. What Files May Be Modified Depending on Target

### Target: `validator_update`

**May be modified:**
- One `src/cci_*.py` validator file.
- One new or existing `tools/run_cci_*_regression.py` runner.
- `examples/audit_cci_*.json` synthetic fixtures (if needed).
- `docs/planning/` for planning updates only, not checkpoint handoff.

Any fixture added under `examples/` must be obviously synthetic and must not contain real command/user data, contact information, real names, real session data, or real approved-promotion records.

**Must NOT be modified:**
- `src/pdf_v6_render.py`
- `docs/layout_profiles/`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`
- `src/correction_implementation_planner.py` (unless fixing a planner bug)
- `corrections/approved_rule_promotions.json` (must remain local-only)

### Target: `rule_catalog`

**May be modified:**
- Add one file under `rules_v6/CCI/`.
- Add one regression runner for the new catalog entry.

**Must NOT be modified:**
- Any validator file.
- Any renderer file.
- Any layout profile.

### Target: `documentation_only`

**May be modified:**
- `docs/planning/`
- `README.md`

Checkpoint docs should be reserved for the separate documentation handoff commit after the implementation commit.

**Must NOT be modified:**
- Any runtime file (`src/`, `rules_v6/`).

### Target: `prompt_contract`

**Must be a separate approved task.** See Sec. 12.

---

## 15. What Phase H.1 / Phase I Must NOT Do

Phase H.1 / Phase I pilot implementation must never:

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **No broad validator rewrites** | The pilot must be additive or minimally invasive. Refactoring existing validators is out of scope. |
| 2 | **No renderer/layout changes unless separately planned** | Layout changes require separate profile review and regression. They cannot be bundled with a validator pilot. |
| 3 | **No automatic global rule enforcement from approved logs** | Approved records do not become active without human implementation, merge, and explicit status transition. |
| 4 | **No AI-only implementation** | AI may assist drafting but cannot claim, verify, approve, or sign off. |
| 5 | **No real command/user data committed** | All test fixtures must be synthetic. No real profiles, contact data, session stores, real names, or real approved-promotion records in commits. |
| 6 | **No silent implementation of approved records** | Every implementation step is logged with human attribution and recorded in the planner. |
| 7 | **No background automation** | No cron jobs, watchers, or CI triggers may implement rules automatically. |
| 8 | **No multi-record batch implementation** | The pilot is one record only. Additional records require separate planning and approval. |
| 9 | **No combined planner and pilot commit** | The planner (Phase H Stage 1) and the pilot (Phase H.1 / Phase I) must be separate commits. |
| 10 | **No changes to Phase F/G command layer without separate design** | New commands or intents require their own planning phase. |
| 11 | **No combined implementation and docs-handoff commit** | Implementation and checkpoint documentation must be separate commits. |

---

## 16. Recommended Pilot Implementation Sequence

### Step 0: Planning and Approval (this document)

- Review this plan.
- Select the pilot record using Sec. 2 criteria.
- Collect evidence per Sec. 3.
- Verify eligibility through the Phase H planner per Sec. 4.
- Assign target per Sec. 5.
- Confirm no renderer/layout implication per Sec. 9.
- Decide whether feature flagging is required if the pilot is a validator update.
- Approve this plan before writing code.

### Step 1: Implement the Pilot

- Write the validator, catalog entry, or docs change.
- Add synthetic fixtures, if needed.
- Add targeted regression runner when the target is `validator_update` or `rule_catalog` (Sec. 11).
- Run the new runner and confirm PASS.
- Run all 24 existing suites and confirm PASS (Sec. 12).
- If a new targeted runner was added, report the final regression set as 25 total suites and confirm all 25 PASS.
- Document rollback plan.
- Commit implementation only with: `CCI: Implement pilot approved rule (Phase H.1)`.

### Step 2: Update Implementation Status

- Add the public `mark_implemented()` wrapper in `src/correction_implementation_planner.py` (Sec. 13).
- Use the new public wrapper after the implementation commit and regression pass.
- Record the implementation commit hash in the approved record's local notes.
- Keep `corrections/approved_rule_promotions.json` local-only and uncommitted.

### Step 3: Documentation Handoff

After the implementation commit is pushed and the approved-record local status is updated, perform a separate docs-only handoff:

- Update `docs/PROJECT_STATUS.md`.
- Update `docs/planning/correction_memory_and_rule_promotion_plan.md`.
- Add checkpoint: `docs/checkpoints/phase_h1_pilot_approved_rule_implementation_checkpoint.md`.
- Commit docs separately with: `Docs: Record Phase H.1 pilot approved rule checkpoint`.

---

## 17. Open Questions Needing Approval

1. **Pilot rule selection:** Which approved record should be the first pilot? The implementer must select one from the existing `corrections/approved_rule_promotions.json` (local-only) and justify it against Sec. 2 criteria. **This must be resolved before any pilot implementation begins.**
2. **Implementer role separation:** Should the Phase H.1 / Phase I implementer be required to be different from the Phase E reviewer and Phase H Stage 1 planner?
3. **Prompt contract scope:** Should prompt-contract updates be allowed in Phase H.1, or deferred to a separate "Phase I" task?
4. **Feature flagging:** If the pilot is a validator update, should it use an explicit enable/disable flag, or is unconditional addition acceptable for a single narrow rule? **This must be resolved before any validator-target pilot implementation begins.**
5. **Catalog versioning:** Should `rules_v6/CCI/` adopt a formal `_catalog_version` integer for the pilot, or is git history sufficient?
6. **Deprecation policy:** If the pilot rule causes false positives, should it be reverted, deprecated-in-place, or moved to `rejected_for_implementation`?
7. **Multi-target sequencing:** If a single approved record requires both a catalog entry and a validator update, should they be in one commit or two sequential commits?
8. **CI enforcement:** Should GitHub Actions require the pilot's targeted regression runner before merge?

---

End of Phase H.1 / Phase I Pilot Approved-Rule Implementation Plan.
