# SECNAV ComplianceGPT - Project Status

**Last Updated:** 2026-06-03  
**GitHub (Active):** https://github.com/sullydw/SECNAV_ComplianceGPT  
**GitHub (Invalid/Nonexistent):** https://github.com/drryl-worqx/SECNAV-ComplianceGPT — DO NOT USE  
**Renderer:** v6 PDF (ReportLab)  
**Branch:** `main`

---

## Current Handoff Summary

This is the main status tracker for SECNAV_ComplianceGPT. A new OpenAI chat or developer agent should read this file after `docs/BOOTSTRAP.md` and before starting new work.

**Latest implementation commit:** `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`
**Phase H implementation commit:** `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`
**Phase G implementation commit:** `cb988bc` — `CCI: Add natural language command mediation (Phase G)`
**Phase F implementation commit:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`
**Phase E implementation commit:** `058de87` — `CCI: Add review promotion utility (Phase E)`
**Phase D implementation commit:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`
**Phase C implementation commit:** `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`
**Phase B implementation commit:** `519fad6` — `CCI: Add correction classification (Phase B)`
**Current verified functional baseline:** `2588e67` — Phase H approved-rule implementation planner implemented and regression-protected
**Previous functional baseline:** `cb988bc` — Phase G natural-language command mediation implemented and regression-protected
**Phase A functional baseline:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`
**GitHub Actions / regressions:** all 24 regression suites verified PASS at `2588e67`
**Expected repository state:** clean and up to date with `origin/main`

### Start Here For New Chat

1. Read `docs/BOOTSTRAP.md`.
2. Read this file: `docs/PROJECT_STATUS.md`.
3. Read `docs/checkpoints/phase_h_approved_rule_implementation_planner_checkpoint.md` for the latest Phase H status.
4. Read `docs/checkpoints/phase_g_natural_language_command_mediation_checkpoint.md` for Phase G details if needed.
5. Read `docs/checkpoints/phase_f_ui_command_integration_checkpoint.md` for Phase F details if needed.
6. Read `docs/checkpoints/phase_e_review_promotion_utility_checkpoint.md` for Phase E details if needed.
7. Read `docs/checkpoints/phase_d_pending_global_rule_candidate_log_checkpoint.md` for Phase D details if needed.
8. Read `docs/checkpoints/phase_c_local_command_profile_promotion_checkpoint.md` for Phase C details if needed.
9. Read `docs/checkpoints/phase_b_correction_classification_checkpoint.md` for Phase B details if needed.
10. Read `docs/checkpoints/phase_a_session_persistence_checkpoint.md` for Phase A details if needed.
11. Read `docs/checkpoints/cci_content_compliance_checkpoint.md` if detailed CCI/intake/correction history is needed.
12. Do not modify renderer/layout unless explicitly asked.
13. Continue from the **Recommended Next Work** section below.
14. Run all regressions before committing implementation changes.

Suggested startup prompt:

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, and `docs/checkpoints/phase_h_approved_rule_implementation_planner_checkpoint.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Run all regressions before committing.

---

## Current Implemented Architecture

### Protected Renderer/Layout Baseline

Chapters 7-10 of SECNAV M-5216.5 are implemented and regression-protected for the current project scope:

- C7 standard letters, continuation pages, and joint letters.
- C8 multiple-address letters using To-line, Distribution, and To-plus-Distribution formats.
- C9 new-page endorsements.
- C10 Memorandums for the Record and plain-paper From-To memorandums.

Figure 9-1 same-page endorsements and additional C10 memorandum types remain deferred or outside the current scope unless explicitly reopened.

### Correspondence Content Intelligence Layer

The CCI layer is a deterministic and heuristic content-compliance layer above the renderer. It validates the JSON payload before rendering and does not change layout behavior.

Implemented CCI validators:

1. Subject-line validator.
2. Reference/enclosure validator.
3. Acronym first-use validator.
4. Date and military-time validator.
5. Personnel identification validator.
6. Point-of-contact expectation validator.
7. Routing / Via / Copy-to intelligence validator.

### Context, Audit, Intake, Profiles, and Correction Memory

Implemented support now includes:

- `src/context_resolver.py` — canonical CCI context object.
- `src/validator_runner.py` — consolidated CCI audit entry point.
- `src/intake_orchestrator.py` — missing-field intake, active profile support, CCI audit, active-draft correction integration, opt-in session correction persistence, and correction classification gating.
- `src/local_profile.py` — local command profile loading, default merging, and promoted correction merge priority.
- `src/correction_apply.py` — active-draft correction application and undo primitives.
- `src/correction_capture.py` — correction record capture with `active_draft` and `current_session` scopes; now runs automatic classification inside `capture_correction()` when no explicit type is provided.
- `src/correction_store.py` — JSONL session correction persistence store.
- `src/correction_classify.py` — Phase B correction classifier.
- `src/correction_promote.py` — Phase C local command profile promotion (two-step approval, eligibility, backup, atomic write, disable/remove/edit).
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging.
- `src/correction_review.py` — Phase E review/promotion utility (human claim, evidence validation, append-only metadata, PII sanitization, approved-rule record creation).
- `src/correction_commands.py` — Phase F slash-command dispatcher (`/correct`, `/undo`, `/remember`, `/accept`, `/reject`, `/promote profile`, `/log candidate`, `/review pending`, `/claim`, `/decide`, `/approved rules`, `/status`).
- `src/correction_nl_commands.py` — Phase G natural-language command mediator (deterministic keyword/phrase classification, canonical structured commands, Phase F delegation).
- `src/correction_implementation_planner.py` — Phase H approved-rule implementation planner (eligibility validation, implementer claim, implementation target assignment, source verification summary, `implementation_planned` record creation, status transitions, deferral/rejection/superseded handling). Planner/status-workflow only; no validator, rule catalog, prompt-contract, or renderer changes.

Current intake capabilities:

- Identifies missing required/recommended/optional fields.
- Asks only for missing information.
- Uses active local profile defaults.
- Suppresses questions for fields filled by profile defaults.
- Runs the consolidated CCI audit.
- Captures active-draft corrections.
- Applies active-draft corrections.
- Undoes corrections.
- Reruns audit after correction.
- Tracks conflicts as advisory only.
- Persists corrections to session JSONL when `session_id` is provided and the correction is scoped to `current_session`.
- Pre-applies matching session corrections when `doc_type`, `component`, and `field_path` match.
- Soft-marks rejected session corrections with `user_rejected=True` and excludes them from future matching.

---

## Current Correction Memory Limits

Correction memory remains intentionally bounded:

- Session persistence is opt-in only; `session_id=None` preserves prior in-memory-only behavior.
- Session JSONL files are local and gitignored.
- 30-day session retention is advisory only; no automatic cleanup is implemented.
- Automatic correction classification is implemented in Phase B.
- **Local command profile promotion is implemented in Phase C** with mandatory two-step user approval, external profile storage, backup, and atomic writes.
- **Pending global rule candidate logging is implemented in Phase D** with mandatory sanitization, explicit approval required before write, current-session-only scope, and `corrections/pending_corrections.jsonl` is gitignored.
- **Review/promotion utility is implemented in Phase E** with human reviewer claim, evidence validation, append-only review metadata, PII sanitization, and approved-rule record creation only (no validator/catalog/renderer changes).
- **Command integration layer is implemented in Phase F** with slash-command dispatcher (`src/correction_commands.py`), confirmation-required persistent actions, delegation to Phase A-E APIs only, and no direct persistence writes.
- **Natural-language command mediation is implemented in Phase G** with deterministic keyword/phrase intent classifier (`src/correction_nl_commands.py`), no AI/LLM imports, canonical structured command objects dispatched through Phase F `CorrectionCommandDispatcher`, confirmation-required persistent actions, and clarification on ambiguity.
- **Approved-rule implementation planner is implemented in Phase H Stage 1** with eligibility validation, implementer claim/assignment, implementation target assignment, source verification summary recording, `implementation_planned` record creation, status transition validation, deferral/rejection/superseded handling. Stage 1 is planner/status-workflow only; no validator, rule catalog, prompt-contract, or renderer changes. No real approved record is set to `implemented`. Synthetic fixture-safe regression only.
- No automatic global rule enforcement.
- No renderer changes.
- Conflicts remain advisory only.

Do not implement global rule enforcement, validator/rule catalog modification, natural-language parsing, or UI/command integration without a separate planning step and user approval.

Do not implement approved-rule pilot implementation or validator/catalog changes without explicit Phase H.1 / Phase I planning and approval.

---

## Local Profile and Session Store Safety

`profiles/example_local_profile.json` is fake example data only.

Real user or command profiles may contain contact information or local command data. Real profiles should **not** be committed to this public repository. Future real profiles should live outside the repository or be gitignored.

`corrections/pending_corrections.jsonl` is gitignored and may contain sanitized candidate values. Do not commit it.

Session correction JSONL files under `corrections/session/*.jsonl` are gitignored and may contain original/corrected draft values. Do not commit them.

---

## CI / Regression Coverage

GitHub Actions workflow:

- Workflow: `Regression`
- Job: `compliance-regression`
- Verified PASS for current functional baseline commit `4ba5cd3` using all 22 regression suites.

Run the full current regression suite before committing implementation changes:

```bash
python tools/run_correction_nl_command_regression.py
python tools/run_correction_command_regression.py
python tools/run_correction_review_regression.py
python tools/run_correction_pending_regression.py
python tools/run_correction_profile_promotion_regression.py
python tools/run_correction_classify_regression.py
python tools/run_intake_regression.py
python tools/run_correction_regression.py
python tools/run_correction_session_regression.py
python tools/run_profile_regression.py
python tools/run_cci_audit_regression.py
python tools/run_context_schema_regression.py
python tools/run_cci_subject_regression.py
python tools/run_cci_ref_encl_regression.py
python tools/run_cci_acronym_regression.py
python tools/run_cci_date_time_regression.py
python tools/run_cci_personnel_regression.py
python tools/run_cci_poc_regression.py
python tools/run_cci_routing_regression.py
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
python tools/run_c9_regression.py
python tools/run_c10_regression.py
```

The CI suite covers:

- 7 CCI validator regressions.
- Context schema regression.
- Consolidated CCI audit regression.
- Intake regression.
- Local profile regression.
- Active-draft correction memory regression.
- Session correction persistence regression.
- Correction classification regression (Phase B).
- Profile promotion regression (Phase C).
- C7-C10 layout/render regressions.
- Pending candidate log regression (Phase D).
- Review/promotion utility regression (Phase E).
- Command integration regression (Phase F).
- Natural-language command mediation regression (Phase G).
- Approved-rule implementation planner regression (Phase H).

---

## Key Files

- `docs/BOOTSTRAP.md` — first-read guide for new chats/sessions.
- `docs/PROJECT_STATUS.md` — current status and handoff tracker.
- `docs/checkpoints/phase_b_correction_classification_checkpoint.md` — latest Phase B correction classification checkpoint.
- `docs/checkpoints/phase_a_session_persistence_checkpoint.md` — Phase A session persistence checkpoint.
- `docs/checkpoints/cci_content_compliance_checkpoint.md` — detailed CCI/intake/correction history checkpoint.
- `.github/workflows/regression.yml` — GitHub Actions regression workflow.
- `src/pdf_v6_render.py` — renderer; do not modify casually.
- `src/validator_runner.py` — one-call CCI audit runner.
- `src/intake_orchestrator.py` — intake, profiles, correction memory orchestration, session persistence integration, correction classification gating, and optional pending-candidate proposal (`propose_pending_log`).
- `src/context_resolver.py` — CCI context resolver.
- `src/local_profile.py` — local profile support.
- `src/correction_apply.py` and `src/correction_capture.py` — active-draft correction support.
- `src/correction_classify.py` — Phase B correction classifier.
- `src/correction_store.py` — JSONL session correction storage.
- `src/correction_promote.py` — Phase C local command profile promotion.
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging (eligibility, sanitization, candidate records, status transitions, duplicate detection).
- `src/correction_review.py` — Phase E review/promotion utility (list candidates, claim, record decision, approve/reject/defer/supersede, evidence validation, PII sanitization, Phase C redirect, approved record creation).
- `src/correction_implementation_planner.py` — Phase H approved-rule implementation planner. Eligibility validation, implementer claim/assignment, target assignment, source verification summary, `implementation_planned` records, status transitions. Planner only; no validator/catalog/renderer changes.
- `src/correction_commands.py` — Phase F slash-command dispatcher. Parses `/correct`, `/undo`, `/remember`, `/accept`, `/reject`, `/promote profile`, `/log candidate`, `/review pending`, `/claim`, `/decide`, `/approved rules`, `/status`. Delegates to Phase A-E APIs only; no direct persistence writes.
- `src/correction_nl_commands.py` — Phase G natural-language command mediator. Deterministic keyword/phrase intent classification, canonical structured command object generation, and dispatcher delegation to Phase F.
- `profiles/README.md` — external profile safety documentation.
- `corrections/README.md` — local-only correction storage safety documentation.
- `tools/run_correction_profile_promotion_regression.py` — Phase C regression runner.
- `tools/run_correction_session_regression.py` — Phase A session persistence regression runner.
- `tools/run_correction_pending_regression.py` — Phase D pending candidate log regression runner.
- `tools/run_correction_review_regression.py` — Phase E review/promotion utility regression runner.
- `tools/run_correction_nl_command_regression.py` — Phase G natural-language command mediation regression runner (151 checks).
- `tools/run_correction_command_regression.py` — Phase F command integration regression runner (45 checks).
- `tools/run_correction_implementation_regression.py` — Phase H approved-rule implementation planner regression runner (30+ checks, synthetic fixtures only).
- `profiles/example_local_profile.json` — fake/template profile only.

---

## What Not To Do

- Do not edit renderer/layout casually.
- Do not create a parallel renderer.
- Do not implement global rule enforcement, validator/rule catalog modification, or UI/command integration without approved planning.
- Do not commit real command profiles, contact data, session JSONL stores, pending candidate logs, or approved promotion logs publicly.
- Do not skip regressions.
- Do not assume Navy and Marine Corps conventions are identical.
- Do not ignore rules hidden inside manual figures, captions, or example text.
- Do not modify rules without preserving/updating provenance.

---

## Recommended Next Work

### Next Phase: Phase H.1 / Phase I Pilot Approved-Rule Implementation Planning

Phase H.1 / Phase I is **planning-only until reviewed and approved**. It must not automatically enforce approved global records without explicit planning and review.

Phase H.1 / Phase I planning should address:

- Select **one pilot approved record** for actual implementation into validator code, rule catalog files, or prompt contracts.
- Determine whether the selected rule is safe to implement deterministically or requires human-in-the-loop testing.
- Define the exact validator, rule catalog, or prompt-contract change required.
- Impact on existing C7--C10 layout regressions and CCI validator regressions.
- Rollback strategy if the implemented rule causes false positives.
- Regression requirements before any validator or rule catalog changes are committed.
- `prompt_contract` implementation that changes runtime prompt behavior must be a separate approved task.

Keep automatic enforcement and silent global rule activation out of Phase H.1 / Phase I planning unless explicitly scoped and approved. Phase H.1 / Phase I is pilot approved-rule implementation planning only, not automatic global rule activation.

No validator, rule catalog, prompt-contract, or renderer changes may occur until Phase H.1 / Phase I is explicitly planned, approved, implemented, reviewed, and regression-tested.

**Planning document:** `docs/planning/phase_h1_pilot_approved_rule_implementation_plan.md`

---

## Historical Milestones

### Phase B — Correction Classification (Completed)

- Planning document created: `docs/planning/phase_b_correction_classification_plan.md`.
- Implementation commit: `519fad6` — `CCI: Add correction classification (Phase B)`.
- Added `src/correction_classify.py` with deterministic heuristics.
- Integrated classification into `src/correction_capture.py` via `capture_correction()`.
- Updated `src/intake_orchestrator.py` to gate session persistence based on classification.
- Regression runner created: `tools/run_correction_classify_regression.py`.
- Regression isolation fix: `a7f9aeb` — fixed temp-only fixture usage and removed accidental real artifact (`corrections/session/test_session_phase_b.jsonl`).
- All 18 regression suites pass at `a7f9aeb`.
- No profile promotion implemented.
- No global rule promotion implemented.
- No pending global rule candidate log implemented.
- No UI override implementation.
- No renderer/layout behavior changed.

### Phase C — Local Command Profile Promotion (Completed)

- Planning document created: `docs/planning/phase_c_local_command_profile_promotion_plan.md`.
- Implementation commit: `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`.
- Added `src/correction_promote.py` with two-step approval workflow, eligibility gating, backup, atomic write, disable/remove/edit.
- Extended `src/local_profile.py` `apply_profile_defaults()` to consume `override_rules` at priority 3 in merge stack.
- Added `profiles/README.md` with external profile safety instructions.
- Added `.gitignore` `profiles/user/` defense-in-depth.
- Regression runner created: `tools/run_correction_profile_promotion_regression.py` (33 checks).
- All 19 regression suites pass at `8b8a95c`.
- No pending global rule candidate log implemented.
- No global rule promotion implemented.
- No UI implementation.
- No renderer/layout behavior changed.
- No real profile data committed.

### Phase D — Pending Global Rule Candidate Logging (Completed)

- Planning document created: `docs/planning/phase_d_pending_global_rule_candidate_log_plan.md`.
- Implementation commit: `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`.
- Added `src/correction_pending_log.py` with eligibility gating, full sanitization (EDIPI, SSN, DoD ID, UIC, hull/tail/building/room numbers, emails, phones, addresses, command and person names), candidate record schema, JSONL append/read/update helpers, duplicate fingerprinting, and status transition helpers.
- Added `corrections/README.md` documenting pending candidate log purpose, gitignored status, and local-only policy.
- Added `propose_pending_log()` to `src/intake_orchestrator.py` as an opt-in hook that does not write to disk without explicit caller confirmation.
- Regression runner created: `tools/run_correction_pending_regression.py` (33 checks).
- All 20 regression suites pass at `2e31892`.
- No global rule promotion implemented.
- No validator/rule catalog changes.
- No renderer/layout behavior changed.
- No real command/user data or pending candidate logs committed.
- No UI/review utility implementation.

### Phase E — Review/Promotion Utility (Completed)

- Planning document created: `docs/planning/phase_e_review_promotion_utility_plan.md`.
- Implementation commit: `058de87` — `CCI: Add review promotion utility (Phase E)`.
- Added `src/correction_review.py` with public API: `list_candidates_for_review`, `claim_candidate`, `review_candidate`, `propose_phase_c_redirect`, `load_approved_promotions`, `get_approved_promotion`, `export_approved_promotions`.
- Evidence validation enforces `secnav_citation` for `manual_rule` and `validator_evidence` for `validator_gap`.
- Promotion creates approved-rule records with `implementation_status="pending_implementation"` only; no validator/rule catalog changes.
- No automatic global rule enforcement.
- No renderer/layout changes.
- PII sanitizer covers names, emails, phone numbers, EDIPI, SSN, DoD ID, UIC, hull/tail, building/room numbers.
- Review metadata is append-only (reopening appends new entries).
- `corrections/approved_rule_promotions.json` is gitignored and local-only.
- Regression runner created: `tools/run_correction_review_regression.py` (30 checks).
- All 21 regression suites pass at `058de87`.
- No UI implementation.
- No real command/user data or approved promotion logs committed.

### Phase G — Natural-Language Command Mediation (Completed)

- Planning document created: `docs/planning/phase_g_natural_language_command_mediation_plan.md`.
- Implementation commit: `cb988bc` — `CCI: Add natural language command mediation (Phase G)`.
- Added `src/correction_nl_commands.py` with deterministic keyword/phrase intent classification and canonical structured command object generation.
- No AI/LLM imports; no renderer imports; no validator imports; no direct file writes.
- Dispatches through Phase F `CorrectionCommandDispatcher`; Phase F remains the dispatch authority.
- Supports 15 canonical intents: correction, undo, remember/session, session_list, session_accept, session_reject, profile_promotion, pending_candidate_log, review_list, review_claim, review_decision, approved_list, status, unsupported.
- Persistent actions require confirmation (`yes`/`y`/`confirm` vs `no`/`n`/`cancel`).
- Clarifies on ambiguous field paths, body/reference targets, and low-confidence parses.
- `/promote profile` and `/log candidate` constrained to most recent active-draft or current-session correction.
- Manual-rule approvals require `secnav_citation`; validator-gap approvals require `validator_evidence`.
- Approved global rule records remain `implementation_status="pending_implementation"`.
- Regression runner created: `tools/run_correction_nl_command_regression.py` (151 checks).
- All 23 regression suites pass at `cb988bc`.
- No validator/rule catalog changes.
- No renderer/layout changes.
- No real command/user data committed.

### Phase H — Approved-Rule Implementation Planner (Completed — Stage 1)

- Planning document created: `docs/planning/phase_h_approved_rule_implementation_plan.md`.
- Implementation commit: `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`.
- Added `src/correction_implementation_planner.py` with approved-rule implementation planning utilities.
- Supports statuses: `pending_implementation`, `implementation_planned`, `implemented`, `rejected_for_implementation`, `deferred`, `superseded`.
- Stage 1 is planner/status-workflow only. No validator, rule catalog, prompt-contract, or renderer changes.
- Eligibility validation, implementer claim/assignment, implementation target assignment, source verification summary recording.
- `implementation_planned` records require `source_verification_summary`, `implementation_target`, `implementer`, `planned_at`.
- Real approved records must not be set to `implemented` by Stage 1. `implemented` status is reserved for separately approved Phase H.1 / Phase I.
- No pilot rule implementation. No automatic enforcement.
- No real approved promotion logs committed. `corrections/approved_rule_promotions.json` remains gitignored and local-only.
- Regression runner created: `tools/run_correction_implementation_regression.py` (30+ checks, synthetic/temp fixtures only).
- All 24 regression suites pass at `2588e67`.
- No validator/rule catalog changes.
- No renderer/layout changes.
- No runtime prompt-contract changes.

### Phase F — Command Integration Layer (Completed)

- Planning document created: `docs/planning/phase_f_ui_command_integration_plan.md`.
- Implementation commit: `4ba5cd3` — `CCI: Add command integration layer (Phase F)`.
- Added `src/correction_commands.py` with `CorrectionCommandDispatcher` — slash-command parser, confirmation prompt builder, user-facing message formatter, and dispatcher to Phase A-E APIs.
- Supported commands: `/correct`, `/undo`, `/remember session`, `/session corrections`, `/accept`, `/reject`, `/promote profile`, `/log candidate`, `/review pending`, `/claim`, `/decide`, `/approved rules`, `/status`.
- No natural-language parsing (deferred to Phase G).
- `/promote profile` and `/log candidate` constrained to most recent active-draft correction or current-session correction only.
- `/decide approve` calls `correction_review.review_candidate()`.
- Approved global rule records remain `implementation_status="pending_implementation"`.
- No direct persistence writes from command layer.
- No validator/rule catalog changes.
- No renderer/layout changes.
- No automatic global rule enforcement.
- No AI-only promotion decisions.
- No silent profile/global promotion.
- No background automation.
- No real command/user data committed.
- Regression runner created: `tools/run_correction_command_regression.py` (45 checks).
- All 22 regression suites pass at `4ba5cd3`.

---

## Historical Milestones

### Chapters 7, 8, 9, and 10 Rule/Layout Baseline

- C7 candidate rules created and audited.
- C8 candidate rules created and audited.
- C9 new-page endorsement support implemented and guarded by regression.
- C10 MFR and plain-paper From-To memorandum support implemented and guarded by regression.
- Figure 9-1 same-page endorsements remain deferred.
- Additional C10 memorandum types remain outside current scope.

### Automated Layout Audit Coverage

The project has automated PDF layout audits wired into each chapter regression suite. These are profile-based coordinate checks, not pixel-image comparisons. Manual visual review remains required for final compliance.

Covered figures include:

- C7: Figure 7-1 Standard Letter, Figure 7-2 Continuation Page, Figure 7-4 Joint Letter.
- C8: Figure 8-1 Multiple-Address To-line, Figure 8-2 Distribution-line, Figure 8-3 To + Distribution.
- C9: Figure 9-2 New Page Endorsement.
- C10: Figure 10-1 MFR and Figure 10-3 Plain-Paper From-To variants.

### Correction Memory Milestones

- `2e643db` — correction memory integrated with intake.
- `aa57b96` — correction memory plan updated against verified baseline.
- `71ddf64` — Phase A session correction persistence implemented and all 18 regressions passed.
- `8c863ff` — Phase A session persistence checkpoint added.
- `519fad6` — Phase B correction classification implemented (`src/correction_classify.py` added, integrated into `capture_correction()` and `intake_orchestrator.py`).
- `a7f9aeb` — Phase B regression isolation fix; all 18 regression suites pass.

### Manual-and-Figure Source Standard

Every new layout profile and rule interpretation must be grounded in all available manual guidance, including:

1. Chapter/section text surrounding the figure.
2. Figure title/caption.
3. Instructional text inside the figure example itself.
4. Actual visual/layout geometry.
5. Existing project rule files and renderer behavior.

Figures are rule-bearing and must be reviewed when referenced.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.
