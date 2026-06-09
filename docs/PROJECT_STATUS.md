# SECNAV ComplianceGPT - Project Status

**Last Updated:** 2026-06-09
**Latest Checkpoint:** `docs/checkpoints/phase_h21_route011_synthetic_burnin_observation_03.md` — Phase H.21 synthetic burn-in observation checkpoint #3
**H.21 Checkpoint Commit:** See git log for `Docs: Record H.21 synthetic burn-in observation`
**H.20 Checkpoint #2:** `docs/checkpoints/phase_h20_route011_synthetic_burnin_observation_02.md` — Phase H.20 synthetic burn-in observation checkpoint #2
**H.19 Checkpoint #1:** `docs/checkpoints/phase_h19_route011_synthetic_burnin_observation_01.md` — Phase H.19 synthetic burn-in observation checkpoint #1
**H.18 Observation Template:** `docs/planning/phase_h18_route011_burnin_observation_template.md` — Burn-in observation template for manual/staged review
**H.17 Day 0 Checkpoint:** `docs/checkpoints/phase_h17_route011_day0_burnin_checkpoint.md` — Phase H.17 Day 0 burn-in checkpoint
**H.22 Sanitized Realistic Evidence Plan:** `docs/planning/phase_h22_route011_sanitized_realistic_evidence_plan.md` — Planning for sanitized realistic payload evidence; pauses repeated static synthetic checkpoints
**H.22 Handoff Addendum:** `docs/planning/phase_h22_handoff_reference_update.md` — Handoff addendum documenting H.22 planning state
**H.23 Read-Only Review Verdict:** `APPROVE H.23 READ-ONLY PLANNING REVIEW` — Confirmed H.19/H.20/H.21 identical clean results; approved H.22 direction
**H.24 Sanitized Fixture Implementation Plan:** `docs/planning/phase_h24_route011_sanitized_fixture_implementation_plan.md` — Future fixture/runner implementation plan; does not create artifacts
**H.25 Read-Only Review Verdict:** `APPROVE H.25 READ-ONLY PLANNING REVIEW` — Confirmed H.24 plan is bounded and safe
**H.26 Sanitized Fixture and Runner Implementation Plan:** `docs/planning/phase_h26_route011_sanitized_fixture_runner_plan.md` — Exact future implementation design: 32 fixtures, naming convention, manifest schema, runner behavior, regression integration, and approval gates; no fixtures or runner created; planning-only.
**H.28 Sanitized Fixture and Runner Implementation Checkpoint:** `docs/checkpoints/phase_h28_route011_sanitized_fixture_runner_checkpoint.md` — Implementation checkpoint: 32 fixtures, `manifest.json`, `tools/run_phase_h24_route011_sanitized_fixture_regression.py` (35th suite); full 35-suite gate PASS; config/severity/catalog/validator/renderer/prompt/command untouched.
**GitHub (Active):** https://github.com/sullydw/SECNAV_ComplianceGPT  
**GitHub (Invalid/Nonexistent):** https://github.com/drryl-worqx/SECNAV-ComplianceGPT — DO NOT USE  
**Renderer:** v6 PDF (ReportLab)  
**Branch:** `main`

---

## Current Handoff Summary

This is the main status tracker for SECNAV_ComplianceGPT. A new OpenAI chat or developer agent should read this file after `docs/BOOTSTRAP.md` and before starting new work.

**Latest planning checkpoint commit:** `575c2aa` — `Docs: Record Phase H.15 plan review checkpoint`  
**Latest implementation commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**Phase H.16 burn-in review checkpoint:** `Docs: Record H.16 burn-in review approval`  
**Phase H.13 implementation review checkpoint:** `fcb1d4c` — `Docs: Record Phase H.13 implementation review checkpoint`  
**Phase H.13 planning commits:** `dd1989e` — `Docs: Add Phase H.13 feature flag config plan`; `115f4e0` — `Docs: Refine Phase H.13 config plan`; `1759c9f` — `Docs: Fix markdown table formatting in Phase H.13 config plan`  
**Phase H.14 review checkpoint:** `fcb1d4c` — `Docs: Phase H.14 controlled promotion readiness review (read-only; no files modified)`  
**Phase H.15 planning document:** `docs/planning/phase_h15_route011_warning_pilot_plan.md` — `Docs: Add Phase H.15 warning pilot plan`  
**Phase H.15 plan review checkpoint:** `575c2aa` — `Docs: Record Phase H.15 plan review checkpoint`  
**Phase H.15 warning pilot checkpoint:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**Phase H.16 burn-in regression commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**Phase H.16 review verdict:** `APPROVE H.16 BURN-IN REGRESSION AS STABLE 34-SUITE BASELINE`
**Phase H.11 approved planning checkpoint commit:** `4c3cdb8` — `Docs: Add Phase H.11 From line evidence review plan`
**Phase H.11 evidence review checkpoint commit:** `52076a1` — `Docs: Record Phase H.11 evidence review checkpoint`  
**Phase H.10 implementation commit:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`
**Phase H.9 implementation commit:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`
**Phase H.8 implementation commit:** `769437d` — `CCI: Add From line catalog rule (Phase H.8)`
**Phase H.7 planning checkpoint commit:** `1e16493` — `Docs: Record Phase H.7 evidence review checkpoint`
**Phase H.6 implementation commit:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`
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
**Current verified functional baseline:** `d808cb8` — Phase H.10 From-line evidence collection and regression hardening complete; 20 negative + 10 positive fixtures + 50 corpus patterns + 39-check H.10 runner added; CCI-ROUTE-011 remains advisory-only; 32-suite regression set verified PASS  
**H.13 stable baseline:** `084ce64` — Phase H.13 severity config support implemented and reviewed; `cci_severity_mapper.py` + `config/cci_enforcement_config.json` + severity branching in `cci_routing_validate.py`; default config preserves advisory for CCI-ROUTE-010/011; safe fallback on all error paths; `validator_runner.py` untouched; 33-suite regression set verified PASS  
**Previous functional baseline:** `6f320af` — Phase H.9 From-line advisory validator enforcement complete; 31-suite regression set verified PASS  
**GitHub Actions / regressions:** local 33-suite regression set verified PASS after Phase H.13 review using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`; GitHub Actions must be verified manually if needed  
**Expected repository state:** clean and up to date with `origin/main`; H.13 implementation reviewed and approved as stable baseline

### Start Here For New Chat

1. Read `docs/BOOTSTRAP.md`.
2. Read this file: `docs/PROJECT_STATUS.md`.
3. Read `docs/checkpoints/phase_h11_from_line_evidence_review_checkpoint.md` for the latest Phase H.11 evidence review checkpoint status.
4. Read `docs/checkpoints/phase_h10_from_line_evidence_checkpoint.md` for the Phase H.10 implementation checkpoint status.
5. Read `docs/planning/phase_h11_from_line_evidence_review_plan.md` for the Phase H.11 approved planning document.
6. Read `docs/planning/phase_h10_from_line_evidence_hardening_plan.md` for the Phase H.10 / Phase I.9 From-line evidence plan.
7. Read `docs/checkpoints/phase_h9_from_line_validator_checkpoint.md` for Phase H.9 implementation checkpoint status.
8. Read `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` for Phase H.8 implementation checkpoint status.
9. Read `docs/checkpoints/phase_h7_routing_office_code_evidence_review_checkpoint.md` for Phase H.7 planning checkpoint status.
10. Read `docs/checkpoints/phase_h6_routing_office_code_evidence_checkpoint.md` for Phase H.6 implementation status.
11. Read `docs/checkpoints/phase_h5_routing_office_code_severity_review_checkpoint.md` for Phase H.5 planning status.
12. Read `docs/checkpoints/phase_h4_routing_office_code_validator_checkpoint.md` for Phase H.4 status.
13. Read `docs/checkpoints/phase_h3_second_rule_catalog_pilot_checkpoint.md` for Phase H.3 status.
14. Read `docs/checkpoints/phase_h2_subject_acronym_validator_enforcement_checkpoint.md` for Phase H.2 status.
15. Read `docs/checkpoints/phase_h1_pilot_approved_rule_implementation_checkpoint.md` for Phase H.1 status.
16. Read `docs/checkpoints/phase_h_approved_rule_implementation_planner_checkpoint.md` for Phase H Stage 1 planner details if needed.
17. Read `docs/checkpoints/phase_g_natural_language_command_mediation_checkpoint.md` for Phase G details if needed.
18. Read `docs/checkpoints/phase_f_ui_command_integration_checkpoint.md` for Phase F details if needed.
19. Read `docs/checkpoints/phase_e_review_promotion_utility_checkpoint.md` for Phase E details if needed.
20. Read `docs/checkpoints/phase_d_pending_global_rule_candidate_log_checkpoint.md` for Phase D details if needed.
21. Read `docs/checkpoints/phase_c_local_command_profile_promotion_checkpoint.md` for Phase C details if needed.
22. Read `docs/checkpoints/phase_b_correction_classification_checkpoint.md` for Phase B details if needed.
23. Read `docs/checkpoints/phase_a_session_persistence_checkpoint.md` for Phase A details if needed.
24. Read `docs/checkpoints/cci_content_compliance_checkpoint.md` if detailed CCI/intake/correction history is needed.
25. Do not modify renderer/layout unless explicitly asked.
26. Continue from the **Recommended Next Work** section below.
27. Run all regressions before committing implementation changes.

Suggested startup prompt:

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, `docs/checkpoints/phase_h12_fourth_catalog_pilot_search_checkpoint.md`, and `docs/planning/phase_h12_fourth_catalog_pilot_plan.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs. Run all regressions before committing implementation changes.

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
- `rules_v6/CCI/cci_ch7_subject_rules.json` — includes Phase H.1 pilot rule `CCI-CH7-SUBJ-006`.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — includes Phase H.3 pilot rule `CCI-ROUTE-010` and Phase H.8 pilot rule `CCI-ROUTE-011`.

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
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h10_from_line_evidence_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h9_from_line_validator_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h8_third_rule_catalog_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h6_routing_office_code_evidence_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h4_routing_office_code_validator_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h3_second_rule_catalog_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h2_subject_acronym_validator_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_pilot_subject_acronym_rule_catalog_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c7_phase1_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c8_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c9_regression.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_c10_regression.py
```

The current local regression set is **34 suites**:

- Phase H.16 ROUTE-011 warning pilot burn-in regression (96 checks).
- Phase H.13 severity config support regression (27 checks).
- Phase H.10 From-line evidence collection and regression hardening (39 checks).
- Phase H.9 From-line advisory validator regression (18 checks).
- Phase H.8 third catalog-pilot rule-catalog regression (16 checks).
- Phase H.6 routing office-code evidence regression (15 checks).
- Phase H.4 routing office-code advisory validator regression (18 checks).
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

The 34-suite set passed locally after Phase H.16 burn-in regression when run with `C:\Users\drryl\pinokio\bin\miniconda\python.exe`. Earlier C7-C10 failures were environment-only from using the wrong Python interpreter without `fitz`/PyMuPDF, not code defects.

## Key Files

- `docs/BOOTSTRAP.md` — first-read guide for new chats/sessions.
- `docs/PROJECT_STATUS.md` — current status and handoff tracker.
- `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` — latest Phase H.8 checkpoint.
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
- `rules_v6/CCI/cci_ch2_routing_rules.json` — includes Phase H.3 pilot rule `CCI-ROUTE-010` and Phase H.8 pilot rule `CCI-ROUTE-011` (advisory validator enforcement added in Phase H.9).
- `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — Phase H.1 pilot regression runner (11 checks).
- `tools/run_phase_h2_subject_acronym_validator_regression.py` — Phase H.2 targeted regression runner (12 checks).
- `tools/run_phase_h3_second_rule_catalog_regression.py` — Phase H.3 targeted regression runner (15 checks).
- `tools/run_phase_h4_routing_office_code_validator_regression.py` — Phase H.4 targeted regression runner (18 checks).
- `tools/run_phase_h6_routing_office_code_evidence_regression.py` — Phase H.6 targeted evidence regression runner (15 checks).
- `tools/run_phase_h8_third_rule_catalog_regression.py` — Phase H.8 targeted regression runner (16 checks).
- `tools/run_phase_h9_from_line_validator_regression.py` — Phase H.9 targeted regression runner (18 checks).
- `docs/guidance/window_envelope_payload_guidance.md` — operator guidance for `window_envelope` tagging during active H.15/H.16 warning pilot.
- `tools/run_phase_h16_route011_burnin_regression.py` — Phase H.16 warning pilot burn-in regression runner (96 checks).
- `tools/run_phase_h13_config_regression.py` — Phase H.13 severity config support regression runner (27 checks).
- `tools/run_correction_implementation_regression.py` — Phase H/H.1 planner regression runner (45 checks).
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

### Phase H.15 / Phase I.14 — Controlled Warning Pilot for CCI-ROUTE-011 (Active)

**Status:** Warning pilot active. `CCI-ROUTE-011.effective_severity` = `warning` in default config.

**Implementation commit:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`.  
**Warning pilot checkpoint commit:** `c12e904` — `Docs: Update H.15 checkpoint commit hash`.  
**H.16 burn-in regression commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`.  
**H.16 review verdict:** `APPROVE H.16 BURN-IN REGRESSION AS STABLE 34-SUITE BASELINE`.  
**Full regression gate:** 34/34 PASS.

Phase H.15 changed `CCI-ROUTE-011.effective_severity` from `advisory` to `warning` in `config/cci_enforcement_config.json`. No validator, catalog, renderer, prompt-contract, or command-layer changes were needed because the validator already branches on `effective_severity()`. Rollback is immediate by restoring `CCI-ROUTE-011.effective_severity` to `"advisory"`.

Phase H.16 added 90 synthetic burn-in fixtures under `examples/burnin_h16_route011/` and a 96-check runner (`tools/run_phase_h16_route011_burnin_regression.py`) to stress-test the warning pilot. Fixture coverage includes valid standard letters, missing/empty/null/whitespace From, non-standard document exclusions, window-envelope suppressions, window-envelope-like without tag, and realistic Navy/Marine Corps mixed payloads.

**Operator guidance:** `docs/guidance/window_envelope_payload_guidance.md` provides payload examples and tagging instructions for operators using window-envelope letters during the warning pilot.

**Burn-in clock:** The 30-day observation period starts from the H.15 activation commit (`18fc9bf`), not from H.16. H.16 is regression hardening / burn-in evidence, not pilot activation.

**Known limitations (non-blocking for warning pilot):**
- Exotic whitespace (zero-width space `\u200B`, BOM `\uFEFF`) does not trigger `CCI-ROUTE-011` because `str.strip()` does not strip them. Acceptable for warning pilot. Consider validator hardening before any future error promotion.
- Window-envelope-like letters without `window_envelope: true` block as expected. This is operator/data-quality risk, not a false positive.

**CCI-ROUTE-010 status:** Remains `advisory`. No error-level promotion exists for any rule.

**Current functional baseline:** `7e42f64`. Regression set: 34 suites. H.13 stable baseline: `084ce64`.

**Recommended next phase:** Continue H.16 burn-in observation. After the observation period, possible future phase:
- **H.17 / I.16 — Error Promotion Readiness Review** (requires separate user approval; planning-only until authorized).

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 34 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.
- No validator, prompt-contract, or renderer changes may occur until explicitly planned, approved, implemented, reviewed, and regression-tested.

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

### Phase H.4 / Phase I.3 — Routing Office-Code Advisory Validator Enforcement (Completed)

- Planning document: `docs/planning/phase_h4_routing_office_code_validator_enforcement_plan.md`.
- Implementation commit: `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`.
- Added advisory/non-blocking validator behavior for existing catalog rule `CCI-ROUTE-010`.
- Added `_check_office_code_prefix(...)` helper in `src/cci_routing_validate.py`.
- Scope: `to` and `via` routing lines only; `copy_to` not checked in Phase H.4.
- False-positive controls: candidate office codes require comma delimiter or parenthetical enclosure.
- Catalog severity remains `error`; validator enforcement is interim advisory/non-blocking only.
- Added `tools/run_phase_h4_routing_office_code_validator_regression.py` with 18 checks.
- 13 synthetic `examples/routing_*.json` fixtures added for edge-case coverage.
- Full 28-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.

### Phase H.6 / Phase I.5 — Routing Office-Code Evidence Collection and Regression Hardening (Completed)

- Planning document: `docs/planning/phase_h6_routing_office_code_evidence_hardening_plan.md`.
- Planning commits: `84c349e` — `Docs: Add Phase H.6 routing office code evidence plan`; `04148ba` — `Docs: Fix Phase H.6 advisory format expectation`.
- Implementation commit: `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`.
- Added 20 negative-control fixtures (`examples/routing_h6_negative_01.json` through `routing_h6_negative_20.json`) and 10 positive-control fixtures (`examples/routing_h6_positive_01.json` through `routing_h6_positive_10.json`).
- Added `tools/run_phase_h6_routing_office_code_evidence_regression.py` with 15 checks covering fixture existence, false-positive/negative controls, `(advisory):` format verification, `errors`-list emptiness, copy-to exclusion, H.4 runner still passes, local corpus gitignored, no validator changes, no forbidden files changed.
- Added local corpus `corrections/evidence/routing_office_code_patterns.jsonl` with 50 synthetic-realistic To/Via patterns; corpus remains gitignored (`corrections/evidence/` in `.gitignore`) and was not committed.
- **No severity promotion.** `CCI-ROUTE-010` remains advisory-only.
- **No validator logic changes.** `src/cci_routing_validate.py` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No approved/pending/session logs committed.** All correction storage remains local/gitignored.
- Full 29-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

### Phase H.7 / Phase I.6 — Routing Office-Code Evidence Review and Planning Decision (Completed)

- Planning document: `docs/planning/phase_h7_routing_office_code_evidence_review_plan.md`.
- Planning commit: `532993d` — `Docs: Add Phase H.7 routing office code evidence review plan`.
- **Approved verdict: keep `CCI-ROUTE-010` advisory-only by default; severity promotion remains deferred.**
- **No implementation authorized.** No validator changes. No renderer/layout changes. No prompt-contract changes. No command-layer changes. No rule catalog changes. No approved/pending/session logs committed. No real data committed.
- H.7 reviewed the 30 synthetic fixtures (20 negative + 10 positive) and 50 local corpus patterns.
- H.7 confirmed existing H.6 evidence is sufficient to maintain advisory status.
- Missing evidence documented: real-world Navy/Marine Corps To/Via patterns, joint-letter stress testing, implemented feature flag/config support.
- Feature flag/config support remains conceptual only; must be planned separately before any severity promotion.
- Copy-to remains out of scope for office-code validation.
- Productive alternative path identified: third low-risk catalog pilot.
- Full 29-suite local regression set passed after H.7 planning commit using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline remains `662afbb`. Regression set remains 29 suites.
- Latest planning checkpoint commit: `532993d`.

### Phase H.8 / Phase I.7 — Third Catalog-Pilot Implementation (Completed)

- Planning document: `docs/planning/phase_h8_third_catalog_pilot_plan.md`.
- Planning checkpoint commit: `f0c5abe` — `Docs: Verify Phase H.8 candidate provenance`.
- Implementation commit: `769437d` — `CCI: Add From line catalog rule (Phase H.8)`.
- Third pilot was rule-catalog-only.
- Added catalog entry `CCI-ROUTE-011` to `rules_v6/CCI/cci_ch2_routing_rules.json`.
- Rule text: `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.`
- Source: SECNAV M-5216.5, Chapter 7, Section 6, `"From:" Line`, subparagraph a. General (PDF page 50).
- Approved record: `agr_20260607_49947aca`.
- Source candidate: `cand_20260607_5dcc97cf`.
- Target: `rule_catalog`.
- Added `tools/run_phase_h8_third_rule_catalog_regression.py` with 16 checks.
- Catalog now has 11 routing rules; object schema with `rules` array preserved.
- Local approved record `agr_20260607_49947aca` was marked `implementation_status="implemented"` with implementation commit `769437d`.
- Approved/pending logs remained local/gitignored and were not committed.
- No validator changes — `src/cci_routing_validate.py` untouched.
- No renderer/layout changes — `src/pdf_v6_render.py` untouched.
- No runtime prompt-contract changes — `src/context_resolver.py` untouched.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- No background automation.
- Full 30-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline: `769437d`. Regression set: 30 suites (29 existing + 1 new H.8 runner).

### Phase H.9 / Phase I.8 — From-Line Advisory Validator Enforcement (Completed)

- Planning document: `docs/planning/phase_h9_from_line_validator_enforcement_plan.md`.
- Planning commits: `427ff43` — `Docs: Add Phase H.9 From line validator plan`; `17bae2f` — `Docs: Refine Phase H.9 window-envelope boundary`.
- Implementation commit: `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`.
- Added advisory/non-blocking validator behavior for existing catalog rule `CCI-ROUTE-011`.
- Advisory code: `CCI-ROUTE-011`.
- Rule: Every standard letter must have a `From:` line, except a letter that will be used with a window envelope.
- Source: SECNAV M-5216.5, Chapter 7, Section 6, `"From:" Line`, subparagraph a. General (PDF page 50).
- Added `_check_from_line_required()` helper in `src/cci_routing_validate.py`.
- Scope: `DT_STD_LTR` and `"standard_letter"` document types only; missing `doc_type` skips; memorandum, endorsement, joint_letter, and multiple_address_letter excluded.
- `window_envelope: true` suppresses the advisory.
- Catalog severity remains `error`; validator enforcement is interim advisory/non-blocking only.
- Added `tools/run_phase_h9_from_line_validator_regression.py` with 18 checks.
- 8 synthetic `examples/routing_from_*.json` fixtures added for edge-case coverage.
- Full 31-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- CCI-ROUTE-010 remains advisory-only. No severity promotion occurred.
- Current functional baseline: `6f320af`. Regression set: 31 suites (30 existing + 1 new H.9 runner).

### Phase H.11 / Phase I.10 — From-Line Evidence Review (Completed — Approved)

- Planning document: `docs/planning/phase_h11_from_line_evidence_review_plan.md`.
- Planning commit: `4c3cdb8` — `Docs: Add Phase H.11 From line evidence review plan`.
- Evidence review checkpoint commit: `52076a1` — `Docs: Record Phase H.11 evidence review checkpoint`.
- **H.11 plan approved as planning documentation source of truth.**
- **`CCI-ROUTE-011` remains advisory-only.**
- **H.10 evidence sufficient for advisory maintenance; insufficient for warning/error promotion.**
- **Severity promotion remains deferred.**
- **Feature flag/config planning required before any future promotion.**
- **`window_envelope` remains read-only unless separately approved.**
- **No validator changes.** `src/cci_routing_validate.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No approved/pending/session logs committed.**
- **No real data committed.**
- Current functional baseline remains `d808cb8`. Regression set remains 32 suites.

### Phase H.10 / Phase I.9 — From-Line Evidence Collection and Regression Hardening (Completed)

- Planning document: `docs/planning/phase_h10_from_line_evidence_hardening_plan.md`.
- Planning commits: `8735461` — `Docs: Add Phase H.10 From line evidence plan`; `310fd3a` — `Docs: Refine Phase H.10 From line evidence plan`.
- Infrastructure fix commit: `49577d9` — `Test: Fix H.8 runner baseline comparison` (H.8 and H.6 diff-range false-positives corrected).
- Implementation commit: `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`.
- Added 20 negative-control fixtures (`examples/routing_from_h10_neg_01.json` through `routing_from_h10_neg_20.json`) and 10 positive-control fixtures (`examples/routing_from_h10_pos_01.json` through `routing_from_h10_pos_10.json`).
- Added local corpus `corrections/evidence/from_line_patterns.jsonl` with 50 synthetic From-line patterns; corpus remains gitignored (`corrections/evidence/` in `.gitignore`) and was not committed.
- Added `tools/run_phase_h10_from_line_evidence_regression.py` with 39 checks covering fixture existence, negative/positive control validation, `errors`-list emptiness, `warnings`-only findings, window-envelope truthiness suppression, missing-doc_type skip, non-standard-doc_type skip, dual-rule trigger, H.9 and H.8 runner preservation, corpus gitignored, no validator/catalog/renderer/prompt/command changes.
- **No severity promotion.** `CCI-ROUTE-011` remains advisory-only.
- **No validator logic changes.** `src/cci_routing_validate.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No approved/pending/session logs committed.** All correction storage remains local/gitignored.
- **No real data committed.**
- Full 32-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline: `d808cb8`. Regression set: 32 suites (31 existing + 1 new H.10 runner).

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

### Phase H.15 / Phase I.14 — Controlled Warning Pilot for CCI-ROUTE-011 (Active)

**Status:** Warning pilot active. `CCI-ROUTE-011.effective_severity` = `warning` in default config.

**Implementation commit:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**Follow-up commit:** `c12e904` — `Docs: Update H.15 checkpoint commit hash`  
**Plan review checkpoint:** `575c2aa` — `Docs: Record Phase H.15 plan review checkpoint`  
**Warning pilot checkpoint:** `docs/checkpoints/phase_h15_route011_warning_pilot_checkpoint.md`  
**H.16 burn-in plan:** `docs/planning/phase_h16_route011_warning_burnin_plan.md`

- `CCI-ROUTE-011` now produces warning-level (blocking) enforcement by default.
- `CCI-ROUTE-010` remains advisory.
- Rollback is immediate by restoring `CCI-ROUTE-011.effective_severity` to `advisory` in `config/cci_enforcement_config.json`.
- Full 33-suite regression gate passed after activation.
- Mandatory burn-in observation period required before any error-level promotion discussion.

### Phase H.16 / Phase I.15 — Burn-In Observation and Regression (Completed)

**Implementation commit:** `[TBD]` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**Burn-in checkpoint:** `docs/checkpoints/phase_h16_route011_burnin_regression_checkpoint.md`

- 90 synthetic burn-in fixtures added under `examples/burnin_h16_route011/`.
- New 34th regression suite: `tools/run_phase_h16_route011_burnin_regression.py` (96 checks).
- Full 34-suite regression gate verified PASS.
- Known limitation: exotic whitespace (zero-width space, BOM) not caught by `str.strip()`; documented as operator/data-quality edge case.
- `CCI-ROUTE-010` remains advisory. No error-level promotion exists.
- No temp config files remain.
- No validator, catalog, renderer, prompt, or command-layer changes.

**Recommended next phase:** Phase H.18 / Phase I.17 — Burn-in observation continues. Use `docs/planning/phase_h18_route011_burnin_observation_template.md` for manual/staged observation recording. Day 0 checkpoint recorded at `docs/checkpoints/phase_h17_route011_day0_burnin_checkpoint.md`.

**H.19 / H.20 / H.21 Observation Summary:**
- Repeated synthetic checkpoints produced identical clean results: 90 payloads, 45 expected triggers, 0 false positives, 0 false negatives, 34/34 regression PASS.
- Static synthetic checkpoints paused due to diminishing returns.

**H.22 / H.23 / H.24 / H.25 Planning Summary:**
- H.22 defined sanitized realistic evidence plan: `docs/planning/phase_h22_route011_sanitized_realistic_evidence_plan.md`.
- H.23 read-only review approved H.22 direction.
- H.24 defined sanitized fixture/runner implementation plan: `docs/planning/phase_h24_route011_sanitized_fixture_implementation_plan.md`.
- H.25 read-only review confirmed H.24 plan is bounded and safe.
- No fixtures created. No runner created. No config changes. No severity changes.

**H.28 Implementation Summary:**
- 32 sanitized fixtures created in `examples/burnin_h24_route011_sanitized/`.
- `manifest.json` and `README.md` added to fixture directory.
- `tools/run_phase_h24_route011_sanitized_fixture_regression.py` created as 35th suite.
- Full 35-suite regression gate verified PASS.
- Config/severity/catalog/validator/renderer/prompt/command untouched.

**Burn-in status:**
- Burn-in clock started: `18fc9bf` (H.15 activation).
- Day 0 checkpoint: `0b4c669` recorded.
- H.18 observation template: created for structured manual observation.
- 30-day observation period ends approximately 2026-07-08.
- H.16 burn-in regression (`7e42f64`) remains stable baseline.
- Full 34-suite regression gate verified PASS at Day 0.
- Operator guidance: `docs/guidance/window_envelope_payload_guidance.md` (unchanged).
- Future error promotion: unauthorized. Separate planning + explicit user approval required.
- Future sanitized fixture implementation: unauthorized without separate approval.

**Constraints:**
- No validator changes.
- No catalog changes.
- No renderer/layout changes.
- No prompt-contract changes.
- No command-layer changes.
- No error-level promotion without separate future phase and burn-in evidence.
- No real data committed.
- All 34 regression suites must continue to pass before any future commit.
- Implementation (fixtures, runner) requires explicit approval before any code change.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.
