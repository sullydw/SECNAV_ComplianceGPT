# SECNAV ComplianceGPT - Project Status

**Last Updated:** 2026-06-05
**GitHub (Active):** https://github.com/sullydw/SECNAV_ComplianceGPT  
**GitHub (Invalid/Nonexistent):** https://github.com/drryl-worqx/SECNAV-ComplianceGPT — DO NOT USE  
**Renderer:** v6 PDF (ReportLab)  
**Branch:** `main`

---

## Current Handoff Summary

This is the main status tracker for SECNAV_ComplianceGPT. A new OpenAI chat or developer agent should read this file after `docs/BOOTSTRAP.md` and before starting new work.

**Latest implementation commit:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Phase H.4 implementation commit:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Phase H.3 implementation commit:** `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`  
**Phase H.2 implementation commit:** `609821e` — `CCI: Add subject acronym advisory validator (Phase H.2)`  
**Phase H.1 pilot implementation commit:** `ef365d3` — `CCI: Implement pilot approved rule (Phase H.1)`  
**Phase H.1 mark-implemented wrapper commit:** `6298dab` — `CCI: Add public mark implemented wrapper`  
**Phase H implementation commit:** `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`  
**Phase G implementation commit:** `cb988bc` — `CCI: Add natural language command mediation (Phase G)`  
**Phase F implementation commit:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`  
**Phase E implementation commit:** `058de87` — `CCI: Add review promotion utility (Phase E)`  
**Phase D implementation commit:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`  
**Phase C implementation commit:** `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`  
**Phase B implementation commit:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Phase A functional baseline:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`  
**Current verified functional baseline:** `1e990a6` — Phase H.4 routing office-code advisory validator implemented; CCI-ROUTE-010 advisories emitted from validator; 28-suite regression set verified PASS  
**Previous functional baseline:** `46edcbd` — Phase H.3 second rule-catalog-only pilot implemented; CCI-ROUTE-010 catalog entry added; 27-suite regression set verified PASS  
**GitHub Actions / regressions:** local 28-suite regression set verified PASS after Phase H.4 using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`; GitHub Actions must be verified manually if needed  
**Expected repository state:** clean and up to date with `origin/main`

### Start Here For New Chat

1. Read `docs/BOOTSTRAP.md`.
2. Read this file: `docs/PROJECT_STATUS.md`.
3. Read `docs/checkpoints/phase_h4_routing_office_code_validator_checkpoint.md` for the latest Phase H.4 status.
4. Read `docs/checkpoints/phase_h3_second_rule_catalog_pilot_checkpoint.md` for Phase H.3 status.
5. Read `docs/checkpoints/phase_h2_subject_acronym_validator_enforcement_checkpoint.md` for Phase H.2 status.
6. Read `docs/checkpoints/phase_h1_pilot_approved_rule_implementation_checkpoint.md` for Phase H.1 status.
7. Read `docs/checkpoints/phase_h_approved_rule_implementation_planner_checkpoint.md` for Phase H Stage 1 planner details if needed.
8. Read `docs/checkpoints/phase_g_natural_language_command_mediation_checkpoint.md` for Phase G details if needed.
9. Read `docs/checkpoints/phase_f_ui_command_integration_checkpoint.md` for Phase F details if needed.
10. Read `docs/checkpoints/phase_e_review_promotion_utility_checkpoint.md` for Phase E details if needed.
11. Read `docs/checkpoints/phase_d_pending_global_rule_candidate_log_checkpoint.md` for Phase D details if needed.
12. Read `docs/checkpoints/phase_c_local_command_profile_promotion_checkpoint.md` for Phase C details if needed.
13. Read `docs/checkpoints/phase_b_correction_classification_checkpoint.md` for Phase B details if needed.
14. Read `docs/checkpoints/phase_a_session_persistence_checkpoint.md` for Phase A details if needed.
15. Read `docs/checkpoints/cci_content_compliance_checkpoint.md` if detailed CCI/intake/correction history is needed.
16. Do not modify renderer/layout unless explicitly asked.
17. Continue from the **Recommended Next Work** section below.
18. Run all regressions before committing implementation changes.

Suggested startup prompt:

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, and `docs/checkpoints/phase_h4_routing_office_code_validator_checkpoint.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs. Run all regressions before committing implementation changes.

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
- `src/intake_orchestrator.py` — missing-field intake, active profile support, CCI audit, active-draft correction integration, opt-in session correction persistence, correction classification gating, and optional pending-candidate proposal.
- `src/local_profile.py` — local command profile loading, default merging, and promoted correction merge priority.
- `src/correction_apply.py` — active-draft correction application and undo primitives.
- `src/correction_capture.py` — correction record capture with `active_draft` and `current_session` scopes; runs automatic classification inside `capture_correction()` when no explicit type is provided.
- `src/correction_store.py` — JSONL session correction persistence store.
- `src/correction_classify.py` — Phase B correction classifier.
- `src/correction_promote.py` — Phase C local command profile promotion.
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging.
- `src/correction_review.py` — Phase E review/promotion utility.
- `src/correction_commands.py` — Phase F slash-command dispatcher.
- `src/correction_nl_commands.py` — Phase G natural-language command mediator.
- `src/correction_implementation_planner.py` — Phase H approved-rule implementation planner and Phase H.1 public `mark_implemented()` wrapper.
- `rules_v6/CCI/cci_ch7_subject_rules.json` — includes Phase H.1 pilot rule catalog entry `CCI-CH7-SUBJ-006`.

---

## Current Correction Memory Limits

Correction memory remains intentionally bounded:

- Session persistence is opt-in only; `session_id=None` preserves prior in-memory-only behavior.
- Session JSONL files are local and gitignored.
- 30-day session retention is advisory only; no automatic cleanup is implemented.
- Automatic correction classification is implemented in Phase B.
- **Local command profile promotion is implemented in Phase C** with mandatory two-step user approval, external profile storage, backup, and atomic writes.
- **Pending global rule candidate logging is implemented in Phase D** with mandatory sanitization, explicit approval required before write, current-session-only scope, and `corrections/pending_corrections.jsonl` is gitignored.
- **Review/promotion utility is implemented in Phase E** with human reviewer claim, evidence validation, append-only review metadata, PII sanitization, and approved-rule record creation only.
- **Command integration layer is implemented in Phase F** with slash-command dispatcher, confirmation-required persistent actions, delegation to Phase A-E APIs only, and no direct persistence writes.
- **Natural-language command mediation is implemented in Phase G** with deterministic keyword/phrase intent classifier, no AI/LLM imports, canonical structured command objects dispatched through Phase F, confirmation-required persistent actions, and clarification on ambiguity.
- **Approved-rule implementation planner is implemented in Phase H Stage 1** with eligibility validation, implementer claim/assignment, implementation target assignment, source verification summary recording, `implementation_planned` record creation, status transition validation, deferral/rejection/superseded handling.
- **Phase H.1 pilot approved-rule implementation is complete** for one rule-catalog-only pilot: `CCI-CH7-SUBJ-006`, derived from approved record `agr_20260604_b69c92d9`. This was a rule-catalog update only, not a validator/runtime enforcement change.
- **Public `mark_implemented()` wrapper is implemented** in `src/correction_implementation_planner.py`. Local approved record `agr_20260604_b69c92d9` was marked `implementation_status="implemented"` locally with implementation commit `ef365d3` recorded. The approved log remains local-only and gitignored.
- No automatic global rule enforcement from approved logs.
- No renderer changes.
- No runtime prompt-contract changes.
- Conflicts remain advisory only.

Do not implement additional approved-rule pilots, validator enforcement, prompt-contract changes, or renderer/layout changes without a separate planning step and user approval.

---

## Local Profile and Correction Store Safety

`profiles/example_local_profile.json` is fake example data only.

Real user or command profiles may contain contact information or local command data. Real profiles should **not** be committed to this public repository. Future real profiles should live outside the repository or be gitignored.

`corrections/pending_corrections.jsonl` is gitignored and may contain sanitized candidate values. Do not commit it.

`corrections/approved_rule_promotions.json` is gitignored and local-only. It may contain review/implementation records and must not be committed.

Session correction JSONL files under `corrections/session/*.jsonl` are gitignored and may contain original/corrected draft values. Do not commit them.

---

## CI / Regression Coverage

GitHub Actions workflow:

- Workflow: `Regression`
- Job: `compliance-regression`
- GitHub Actions status for recent commits must be checked manually if CLI/API access is unavailable.

Use the explicit Pinokio/Miniconda Python for full local regression runs:

```bat
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_pilot_subject_acronym_rule_catalog_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_implementation_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_nl_command_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_command_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_review_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_pending_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_profile_promotion_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_classify_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_intake_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_correction_session_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_profile_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_audit_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_context_schema_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_subject_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_ref_encl_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_acronym_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_date_time_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_personnel_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_poc_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_cci_routing_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c7_phase1_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c8_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c9_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c10_regression.py
```

The current local regression set is **27 suites**:

- Phase H.3 second rule-catalog-only pilot regression (15 checks).
- Phase H.2 subject-line acronym advisory regression (12 checks).
- Phase H.1 pilot subject-acronym rule-catalog regression (11 checks).
- Phase H implementation planner regression (45 checks).
- Phase G natural-language command mediation regression (151 checks).
- Phase F command integration regression (45 checks).
- Phase E review regression (30 checks).
- Phase D pending candidate regression (33 checks).
- Phase C profile promotion regression (33 checks).
- Phase B classification regression.
- Intake, correction, session, profile, audit, context-schema, CCI subject/ref-encl/acronym/date-time/personnel/POC/routing, and C7-C10 layout regressions.

The 27-suite set passed locally after Phase H.3 when run with `C:\Users\drryl\pinokio\bin\miniconda\python.exe`. Earlier C7-C10 failures were environment-only from using the wrong Python interpreter without `fitz`/PyMuPDF, not code defects.

---

## Key Files

- `docs/BOOTSTRAP.md` — first-read guide for new chats/sessions.
- `docs/PROJECT_STATUS.md` — current status and handoff tracker.
- `docs/checkpoints/phase_h1_pilot_approved_rule_implementation_checkpoint.md` — latest Phase H.1 checkpoint.
- `docs/checkpoints/phase_h_approved_rule_implementation_planner_checkpoint.md` — Phase H Stage 1 checkpoint.
- `.github/workflows/regression.yml` — GitHub Actions regression workflow.
- `src/pdf_v6_render.py` — renderer; do not modify casually.
- `src/validator_runner.py` — one-call CCI audit runner.
- `src/intake_orchestrator.py` — intake, profiles, correction memory orchestration, session persistence integration, correction classification gating, and optional pending-candidate proposal.
- `src/context_resolver.py` — CCI context resolver.
- `src/local_profile.py` — local profile support.
- `src/correction_apply.py` and `src/correction_capture.py` — active-draft correction support.
- `src/correction_classify.py` — Phase B correction classifier.
- `src/correction_store.py` — JSONL session correction storage.
- `src/correction_promote.py` — Phase C local command profile promotion.
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging.
- `src/correction_review.py` — Phase E review/promotion utility.
- `src/correction_implementation_planner.py` — Phase H/H.1 approved-rule implementation planner and public `mark_implemented()` wrapper.
- `src/correction_commands.py` — Phase F slash-command dispatcher.
- `src/correction_nl_commands.py` — Phase G natural-language command mediator.
- `rules_v6/CCI/cci_ch7_subject_rules.json` — includes Phase H.1 pilot rule `CCI-CH7-SUBJ-006`.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — includes Phase H.3 pilot rule `CCI-ROUTE-010`.
- `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — Phase H.1 pilot regression runner (11 checks).
- `tools/run_phase_h2_subject_acronym_validator_regression.py` — Phase H.2 targeted regression runner (12 checks).
- `tools/run_phase_h3_second_rule_catalog_regression.py` — Phase H.3 targeted regression runner (15 checks).
- `tools/run_correction_implementation_regression.py` — Phase H/H.1 implementation planner regression runner (45 checks).
- `profiles/README.md` — external profile safety documentation.
- `corrections/README.md` — local-only correction storage safety documentation.

---

## What Not To Do

- Do not edit renderer/layout casually.
- Do not create a parallel renderer.
- Do not implement additional global rule enforcement, validator enforcement, prompt-contract changes, or additional rule-catalog changes without approved planning.
- Do not commit real command profiles, contact data, session JSONL stores, pending candidate logs, or approved promotion logs publicly.
- Do not skip regressions.
- Do not assume Navy and Marine Corps conventions are identical.
- Do not ignore rules hidden inside manual figures, captions, or example text.
- Do not modify rules without preserving/updating provenance.

---

## Recommended Next Work

### Next Phase: Phase H.4 / Phase I.3 Validator Enforcement Planning or Third Catalog-Pilot Planning

Phase H.3 / Phase I.2 second rule-catalog-only pilot is **complete**. No further implementation should occur until a new phase is explicitly planned, approved, and regression-tested.

Phase H.3 summary:
- Catalog entry `CCI-ROUTE-010` added to `rules_v6/CCI/cci_ch2_routing_rules.json`.
- Rule: numeric-only office codes require `Code`; office codes starting with letters must not use `Code`.
- 27-suite regression set verified PASS.
- No validator changes. No renderer/layout changes. No prompt-contract changes. No command-layer changes.

The next planning phase should decide **one** of the following directions:

1. **Plan validator enforcement for `CCI-ROUTE-010`** so the office-code rule is checked by the routing validator, with feature-flag mechanism and targeted regression coverage.
2. **Further refine `CCI-CH7-SUBJ-007`** (expand prohibited list or promote severity), with provenance and fixture coverage.
3. **Add a third low-risk approved-rule pilot** (rule-catalog-only first, then validator if approved), requiring separate planning document and approved record.
4. **Update rule-catalog governance/provenance tooling** (schema validation, rule-dependency tracking, catalog linting).

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 27 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.

No validator, prompt-contract, or renderer changes may occur until Phase H.4 / Phase I.3 is explicitly planned, approved, implemented, reviewed, and regression-tested.

---

## Historical Milestones

### Phase H.1 / Phase I — Pilot Approved-Rule Implementation (Completed)

- Planning document created: `docs/planning/phase_h1_pilot_approved_rule_implementation_plan.md`.
- Pilot implementation commit: `ef365d3` — `CCI: Implement pilot approved rule (Phase H.1)`.
- Public wrapper commit: `6298dab` — `CCI: Add public mark implemented wrapper`.
- First pilot was rule-catalog-only.
- Added catalog entry `CCI-CH7-SUBJ-006` to `rules_v6/CCI/cci_ch7_subject_rules.json`.
- Rule text: `In correspondence, do not use acronyms in the subject line.`
- Source: SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General.
- Approved record: `agr_20260604_b69c92d9`.
- Target: `rule_catalog`.
- Added `tools/run_pilot_subject_acronym_rule_catalog_regression.py` with 11 checks.
- Added public `mark_implemented()` wrapper to `src/correction_implementation_planner.py`.
- Added 5 planner regression checks; `tools/run_correction_implementation_regression.py` now passes 45/45.
- Local approved record `agr_20260604_b69c92d9` was marked `implementation_status="implemented"` with implementation commit `ef365d3`.
- Approved/pending logs remained local/gitignored and were not committed.
- No validator changes.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No automatic enforcement from approved logs.
- No background automation.
- Full 25-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

### Phase H.2 / Phase I.1 — Subject-Line Acronym Validator Advisory Enforcement (Completed)

- Planning document: `docs/planning/phase_h2_subject_acronym_validator_enforcement_plan.md`.
- Implementation commit: `609821e` — `CCI: Add subject acronym advisory validator (Phase H.2)`.
- Added advisory/non-blocking validator behavior for rule `CCI-CH7-SUBJ-006`.
- New advisory validator code: `CCI-CH7-SUBJ-007`.
- Curated prohibited subject acronym list: `POC`, `UIC`, `OIC`.
- Added `_check_prohibited_subject_acronyms()` in `src/cci_subject_validate.py` with token-by-token scan for all-caps subjects; generic acronym regex suppressed on all-caps subjects to prevent false positives.
- Normal all-caps words (`UPDATE`, `POLICY`, `MEETING`, `SECNAV`, etc.) are not flagged.
- Existing `CCI-CH7-SUBJ-004` behavior unchanged.
- `src/cci_acronym_validate.py` untouched.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- New targeted regression runner: `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12 checks, PASS.
- 7 synthetic example fixtures added under `examples/audit_cci_subject_*.json`.
- Full 26-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

### Phase H.3 / Phase I.2 — Second Rule-Catalog-Only Pilot (Completed)

- Planning document: `docs/planning/phase_h3_second_rule_catalog_pilot_plan.md`.
- Implementation commit: `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`.
- Second pilot was rule-catalog-only.
- Added catalog entry `CCI-ROUTE-010` to `rules_v6/CCI/cci_ch2_routing_rules.json`.
- Rule text: `If the office code is composed of only numbers, add the word "Code" before the numbers. Do not add the word "Code" before an office code that starts with a letter (e.g., "N" or "SUP").`
- Source: SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General.
- Approved record: `agr_20260604_7b5d44a2`.
- Source candidate: `cand_20260604_a0f49e2e`.
- Target: `rule_catalog`.
- Added `tools/run_phase_h3_second_rule_catalog_regression.py` with 15 checks.
- Catalog now has 10 routing rules; object schema with `rules` array preserved.
- Local approved record `agr_20260604_7b5d44a2` was marked `implementation_status="implemented"` with implementation commit `46edcbd`.
- Approved/pending logs remained local/gitignored and were not committed.
- No validator changes.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- No background automation.
- Full 27-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

### Phase H — Approved-Rule Implementation Planner (Completed — Stage 1)

- Planning document created: `docs/planning/phase_h_approved_rule_implementation_plan.md`.
- Implementation commit: `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`.
- Added `src/correction_implementation_planner.py` with approved-rule implementation planning utilities.
- Supports statuses: `pending_implementation`, `implementation_planned`, `implemented`, `rejected_for_implementation`, `deferred`, `superseded`.
- Stage 1 is planner/status-workflow only. No validator, rule catalog, prompt-contract, or renderer changes.
- Regression runner created: `tools/run_correction_implementation_regression.py`.
- All 24 regression suites pass at `2588e67`.

### Phase G — Natural-Language Command Mediation (Completed)

- Implementation commit: `cb988bc` — `CCI: Add natural language command mediation (Phase G)`.
- Added `src/correction_nl_commands.py`.
- No AI/LLM imports; dispatches through Phase F.
- Regression runner: `tools/run_correction_nl_command_regression.py` (151 checks).

### Phase F — Command Integration Layer (Completed)

- Implementation commit: `4ba5cd3` — `CCI: Add command integration layer (Phase F)`.
- Added `src/correction_commands.py`.
- Supports correction, session, profile, pending, review, approved-rule, and status slash commands.

### Phase E — Review/Promotion Utility (Completed)

- Implementation commit: `058de87` — `CCI: Add review promotion utility (Phase E)`.
- Added `src/correction_review.py`.
- Creates approved records with `implementation_status="pending_implementation"` only.

### Phase D — Pending Global Rule Candidate Logging (Completed)

- Implementation commit: `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`.
- Added `src/correction_pending_log.py`.

### Phase C — Local Command Profile Promotion (Completed)

- Implementation commit: `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`.

### Phase B — Correction Classification (Completed)

- Implementation commit: `519fad6` — `CCI: Add correction classification (Phase B)`.

### Phase A — Session Correction Persistence (Completed)

- Implementation commit: `71ddf64` — `CCI: Add session correction persistence (Phase A)`.

### Chapters 7, 8, 9, and 10 Rule/Layout Baseline

- C7 candidate rules created and audited.
- C8 candidate rules created and audited.
- C9 new-page endorsement support implemented and guarded by regression.
- C10 MFR and plain-paper From-To memorandum support implemented and guarded by regression.
- Figure 9-1 same-page endorsements remain deferred.
- Additional C10 memorandum types remain outside current scope.

### Manual-and-Figure Source Standard

Every new layout profile and rule interpretation must be grounded in all available manual guidance, including:

1. Chapter/section text surrounding the figure.
2. Figure title/caption.
3. Instructional text inside the figure example itself.
4. Actual visual/layout geometry.
5. Existing project rule files and renderer behavior.

Figures are rule-bearing and must be reviewed when referenced.

---

## Recommended Next Work

**Next recommended phase: Phase H.5 / Phase I.4 validator severity review or third catalog-pilot planning — planning-only until approved.**

Phase H.4 routing office-code advisory validator enforcement is complete. No further implementation should occur until a new phase is explicitly planned, approved, and regression-tested.

The next planning phase should decide **one** of the following directions:

1. **Collect more real/synthetic evidence before increasing `CCI-ROUTE-010` severity**:
   - Current validator is advisory only; catalog severity is `error`.
   - Requires feature-flag or config mechanism for severity override.
   - Must not break existing routing behavior.
   - Requires broader fixture testing across real-world To/Via patterns.

2. **Keep `CCI-ROUTE-010` advisory only**:
   - Do not promote to error/warning.
   - May add more heuristic detection refinements.
   - Must preserve 28-suite regression.

3. **Plan validator severity promotion with feature flag/config**:
   - Add config-driven severity so advisory rules can be promoted without code changes.
   - Requires design document and regression coverage.
   - Must not introduce automatic enforcement from approved logs.

4. **Further refine office-code detection**:
   - Expand to additional delimiters or edge cases.
   - Add more synthetic fixtures and targeted regression checks.
   - Must preserve existing false-positive controls.

5. **Add a third low-risk catalog pilot**:
   - Separate approved record in `rules_v6/CCI/`.
   - Planning document required before implementation.
   - No automatic enforcement from approved logs.

6. **Improve rule-catalog governance/provenance tooling**:
   - Add audit trails for catalog changes.
   - Add catalog schema validation.
   - Add catalog change review workflow.

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 28 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.
