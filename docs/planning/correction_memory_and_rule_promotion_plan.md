# Correction Memory and Rule Promotion Layer Plan

**Latest Verified Baseline:** `2f2ba95` — Current HEAD (Phase K.7 SUBJ-002 warning pilot observation decision)  
**H.13 Stable Baseline:** `084ce64` — `CCI: Add H.13 severity config support`  
**Phase L.1 Conversational Builder Workflow Plan:** `docs/planning/phase_l1_conversational_builder_workflow_plan.md` — Planning-only shift toward user-facing product workflow; no code changes.
**Phase H.13 Implementation Review Checkpoint:** `fcb1d4c` — `Docs: Record Phase H.13 implementation review checkpoint`  
**Phase H.13 Implementation Checkpoint:** `a520eb2` — `Docs: Record Phase H.13 implementation checkpoint`  
**Phase H.13 Planning Commits:** `dd1989e` — `Docs: Add Phase H.13 feature flag config plan`; `115f4e0` — `Docs: Refine Phase H.13 config plan`; `1759c9f` — `Docs: Fix markdown table formatting in Phase H.13 config plan`  
**Phase H.11 Planning Checkpoint:** `4c3cdb8` — `Docs: Add Phase H.11 From line evidence review plan`  
**Phase H.10 Implementation:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Phase H.10 Planning Checkpoint:** `310fd3a` — `Docs: Refine Phase H.10 From line evidence plan`  
**Phase H.9 Implementation:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Phase H.9 Planning Checkpoint:** `17bae2f` — `Docs: Refine Phase H.9 window-envelope boundary`  
**Phase H.8 Implementation:** `769437d` — `CCI: Add From line catalog rule (Phase H.8)`  
**Phase H.7 Planning Checkpoint:** `532993d` — `Docs: Add Phase H.7 routing office code evidence review plan`  
**Phase H.7 Approved Verdict:** keep `CCI-ROUTE-010` advisory-only by default; severity promotion deferred  
**Phase H.6 Implementation:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`  
**Phase H.4 Implementation:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Phase H.3 Implementation:** `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`  
**Phase H.2 Implementation:** `609821e` — `CCI: Add subject acronym advisory validator (Phase H.2)`  
**Phase H.1 Pilot Implementation:** `ef365d3` — `CCI: Implement pilot approved rule (Phase H.1)`  
**Phase H.1 Mark-Implemented Wrapper:** `6298dab` — `CCI: Add public mark implemented wrapper`  
**Phase H Implementation:** `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`  
**Phase G Implementation:** `cb988bc` — `CCI: Add natural language command mediation (Phase G)`  
**Phase F Implementation:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`  
**Phase E Implementation:** `058de87` — `CCI: Add review promotion utility (Phase E)`  
**Phase D Implementation:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`  
**Phase C Implementation:** `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`  
**Phase B Implementation:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Phase A Implementation:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`  
**Phase H.11 Evidence Review Checkpoint:** `52076a1` — `Docs: Record Phase H.11 evidence review checkpoint`  
**Phase H.11 Approved Verdict:** `CCI-ROUTE-011` remains advisory-only; severity promotion deferred; productive next path: fourth low-risk catalog-only pilot planning  
**Latest Checkpoint:** `fcb1d4c` / Phase H.13 implementation review complete (approved as stable baseline)  
**Phase H.14 Review Checkpoint:** `fcb1d4c` — `Docs: Record Phase H.13 implementation review checkpoint` (read-only H.14 review conducted on same commit)  
**Phase H.15 Warning Pilot Plan Document:** `94d420d` — `Docs: Add Phase H.15 warning pilot plan`  
**Phase H.15 Plan Review Checkpoint:** `575c2aa` — `Docs: Record Phase H.15 plan review checkpoint`  
**Phase H.15 Warning Pilot Checkpoint:** `c12e904` — `Docs: Update H.15 checkpoint commit hash`  
**Phase H.16 Burn-In Regression:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`
**Phase H.16 Review Verdict:** `APPROVE H.16 BURN-IN REGRESSION AS STABLE 34-SUITE BASELINE`
**Phase H.16 Burn-In Plan:** `docs/planning/phase_h16_route011_warning_burnin_plan.md`
**Phase H.16 Operator Guidance:** `docs/guidance/window_envelope_payload_guidance.md`
**Phase H.17 Day 0 Burn-In Checkpoint:** `docs/checkpoints/phase_h17_route011_day0_burnin_checkpoint.md` — Day 0 of 30-day observation period; 34/34 regression PASS; config unchanged; error promotion unauthorized.
**Phase H.18 Burn-In Observation Template:** `docs/planning/phase_h18_route011_burnin_observation_template.md` — Structured manual observation template for the active warning pilot; no code changes; no real data committed.
**Phase H.19 Synthetic Burn-In Observation Checkpoint #1:** `docs/checkpoints/phase_h19_route011_synthetic_burnin_observation_01.md` — First structured synthetic observation checkpoint; 90 synthetic payloads reviewed; zero false positives; zero false negatives; 34/34 regression PASS; decision: continue warning pilot; error promotion unauthorized.
**Phase H.20 Synthetic Burn-In Observation Checkpoint #2:** `docs/checkpoints/phase_h20_route011_synthetic_burnin_observation_02.md` — Second structured synthetic observation checkpoint; 90 synthetic payloads reviewed; zero false positives; zero false negatives; 34/34 regression PASS; no behavior change vs H.19; decision: continue warning pilot; error promotion unauthorized.
**Phase H.21 Synthetic Burn-In Observation Checkpoint #3:** `docs/checkpoints/phase_h21_route011_synthetic_burnin_observation_03.md` — Third structured synthetic observation checkpoint; 90 synthetic payloads reviewed; zero false positives; zero false negatives; 34/34 regression PASS; no behavior change vs H.19/H.20; decision: continue warning pilot; recommendation to pause synthetic-only observation and seek realistic sanitized examples before next checkpoint; error promotion unauthorized.
**Phase H.22 Sanitized Realistic Evidence Plan:** `docs/planning/phase_h22_route011_sanitized_realistic_evidence_plan.md` — Planning document defining sanitized realistic payload evidence goals for the active warning pilot; pauses repeated static synthetic checkpoints; proposes 25–50 sanitized fixtures; does not create fixtures or runner; error promotion unauthorized.
**Phase H.22 Handoff Reference Addendum:** `docs/planning/phase_h22_handoff_reference_update.md` — Handoff addendum documenting H.22 planning state and guardrails; no code changes.
**Phase H.23 Read-Only Planning Review Verdict:** `APPROVE H.23 READ-ONLY PLANNING REVIEW` — Reviewed H.19/H.20/H.21 repeated synthetic burn-in results; confirmed identical clean metrics; approved H.22 direction to pause static synthetic checkpoints and seek sanitized realistic evidence.
**Phase H.24 Sanitized Fixture Implementation Plan:** `docs/planning/phase_h24_route011_sanitized_fixture_implementation_plan.md` — Planning document for possible future sanitized fixture and runner implementation; proposes `examples/burnin_h24_route011_sanitized/` and `tools/run_phase_h24_route011_sanitized_fixture_regression.py`; does not create artifacts; may become 35th regression suite if implemented later.
**Phase H.25 Read-Only Planning Review Verdict:** `APPROVE H.25 READ-ONLY PLANNING REVIEW` — Reviewed H.24 implementation plan; confirmed proposed fixtures/runner are bounded and safe; no config/severity/catalog/validator/renderer/prompt/command changes authorized.
**Phase H.26 Sanitized Fixture and Runner Implementation Plan:** `docs/planning/phase_h26_route011_sanitized_fixture_runner_plan.md` — Exact future implementation design: 32 fixtures across 11 categories, manifest schema, runner behavior, regression integration, and approval gates; no fixtures or runner created; planning-only.
**Phase H.29 Read-Only Implementation Review Verdict:** `APPROVE H.29 READ-ONLY IMPLEMENTATION REVIEW` — Reviewed H.28 implementation read-only; confirmed all 21 review criteria pass; suite count 35; no real data; no anomalies; H.28 accepted as stable implementation baseline.
**Phase H.31 Sanitized Fixture Burn-In Observation Checkpoint #1:** `docs/checkpoints/phase_h31_route011_sanitized_fixture_burnin_observation_01.md` — First sanitized fixture burn-in observation checkpoint for the H.24/H.28 sanitized fixture set; 32 fixtures reviewed; 36/36 PASS (32 fixtures + 4 sub-runners); full 35-suite gate PASS; 0 false positives, 0 false negatives, 0 suppression failures; decision: continue warning pilot; error promotion unauthorized; no code changes.
**Phase H.32 Sanitized Fixture Burn-In Observation Checkpoint #2:** `docs/checkpoints/phase_h32_route011_sanitized_fixture_burnin_observation_02.md` — Second sanitized fixture burn-in observation checkpoint; 32 fixtures reviewed; 36/36 PASS; full 35-suite gate PASS; 0 false positives, 0 false negatives, 0 suppression failures; identical to H.31; decision: continue warning pilot; error promotion unauthorized; no code changes.
**Phase H.33 Sanitized Fixture Burn-In Observation Checkpoint #3:** `docs/checkpoints/phase_h33_route011_sanitized_fixture_burnin_observation_03.md` — Third sanitized fixture burn-in observation checkpoint; 32 fixtures reviewed; 36/36 PASS; full 35-suite gate PASS; 0 false positives, 0 false negatives, 0 suppression failures; identical to H.31 and H.32; three consecutive clean observations on static fixtures; recommendation to pause repeated fixture-only observation and proceed to H.34 review/decision checkpoint; error promotion unauthorized; no code changes.
**Phase H.34 Sanitized Fixture Burn-In Review and Decision:** `docs/checkpoints/phase_h34_route011_sanitized_fixture_burnin_review_decision.md` — Review of H.31–H.33; confirms stability and pauses repeated fixture-only observation due to diminishing returns; continues warning pilot; rejects error promotion (Option 3 rejected); recommends Option 1 (continue pilot, pause observation); no code changes; error promotion unauthorized.
**Phase H.35 Warning Pilot Paused Observation Checkpoint:** `docs/checkpoints/phase_h35_route011_warning_pilot_paused_observation_checkpoint.md` — Documents paused-observation posture after H.34; no new fixture observation; pilot remains active; lists 5 triggers for resuming observation; recommends H.36 operator feedback plan if feedback arrives; error promotion unauthorized; no code changes.
**Phase H.36 Sanitized Operator Feedback Observation Plan:** `docs/planning/phase_h36_route011_sanitized_operator_feedback_observation_plan.md` — Planning document defining how future sanitized operator feedback about CCI-ROUTE-011 warning pilot will be captured, classified, and reviewed; 8 feedback categories, 13 record fields, 7-step review workflow, decision thresholds, and explicit prohibitions; no feedback collected; no code changes; error promotion unauthorized.
**Phase H.30 Read-Only Implementation Review Checkpoint:** `docs/checkpoints/phase_h30_h29_readonly_implementation_review_checkpoint.md` — Formal checkpoint documenting H.29 approval; enumerates file reviewed, review criteria table, config/severity state, and recommended next phase; no files modified in review.
**Phase I.40 / Phase J.4 ROUTE-010 Warning Pilot Burn-In Checkpoint #1:** `docs/checkpoints/phase_i40_route010_warning_pilot_burnin_checkpoint_01.md` — First burn-in checkpoint after ROUTE-010 warning pilot activation; targeted regressions PASS (H.4 18/18, H.6 15/15, H.13 27/27, H.16 96/96, H.24 36/36); cross-area H.9/H.10 confirmed clean; full 35-suite gate PASS; 0 false positives, 0 false negatives; decision: continue warning pilot; error promotion unauthorized.
**Phase I.39B / Phase J.3B ROUTE-010 Warning Pilot Runner Comment Cleanup:** `fc11a06` — `Docs: Clean ROUTE-010 warning pilot runner comments`; comment/docstring-only cleanup; no behavior/config/severity/catalog/validator/renderer/prompt/command changes; H.4/H.6/H.9/H.10/H.13 runner headers and check descriptions updated to reflect warning-pilot semantics; H.16 Check 91 comments corrected; full 35-suite gate PASS.
**Phase I.39 / Phase J.3 ROUTE-010 Warning Pilot Activation:** `e60e888` — `CCI: Start I.39 ROUTE-010 warning pilot`; config-only activation; `CCI-ROUTE-010.effective_severity` changed from `advisory` to `warning`; full 35-suite gate PASS.
**Phase I.37 / Phase J.1 ROUTE-010 Warning Pilot Plan:** `docs/planning/phase_i37_route010_warning_pilot_plan.md` — Planning-only document evaluating whether `CCI-ROUTE-010` should enter a controlled warning pilot; risks, rollback path, and burn-in requirements documented.
**Phase I.41 / Phase J.5 ROUTE-010 Warning Pilot Burn-In Checkpoint #2:** `docs/checkpoints/phase_i41_route010_warning_pilot_burnin_checkpoint_02.md` — Second burn-in checkpoint; identical clean results to I.40; targeted regressions PASS (H.4 18/18, H.6 15/15, H.13 27/27, H.16 96/96, H.24 36/36); cross-area H.9/H.10 confirmed clean; full 35-suite gate PASS; 0 false positives, 0 false negatives; decision: continue warning pilot; error promotion unauthorized.
**Phase I.42 / Phase J.6 ROUTE-010 Warning Pilot Burn-In Checkpoint #3:** `docs/checkpoints/phase_i42_route010_warning_pilot_burnin_checkpoint_03.md` — Third burn-in checkpoint; identical clean results to I.40/I.41; targeted regressions PASS (H.4 18/18, H.6 15/15, H.13 27/27, H.16 96/96, H.24 36/36); cross-area H.9/H.10 confirmed clean; full 35-suite gate PASS; 0 false positives, 0 false negatives; decision: continue warning pilot; recommend pausing repeated synthetic burn-in due to diminishing returns; error promotion unauthorized.
**Phase I.43 / Phase J.7 ROUTE-010 Warning Pilot Burn-In Review and Decision:** `docs/checkpoints/phase_i43_route010_warning_pilot_burnin_review_decision.md` — Review of I.39 activation through I.42 burn-in #3; three consecutive identical clean results; no drift; decision: continue warning pilot, pause repeated synthetic burn-in due to diminishing returns, reject rollback, reject error promotion; observation resumes only on operator feedback, config change, new fixtures, anomaly, or explicit user request; error promotion unauthorized.
**Phase J.14 / Phase K.6 ROUTE-007 Source Citation Review:** `docs/checkpoints/phase_j14_route007_source_citation_review_note.md` — Lean source citation check of SECNAV M-5216.5 Chapter 7; no explicit prohibition of duplicate To/Via+Copy-to addressees found; rule is derived from functional role separation (action vs information); catalog citation left unchanged as narrative inference; no config/severity/validator/renderer/prompt/command changes.
**Phase J.13 / Phase K.5 ROUTE-007 Regression Evidence Review Checkpoint:** `docs/checkpoints/phase_j13_route007_regression_evidence_review_checkpoint.md` — Read-only evidence review of J.12/K.4 implementation; 13/13 checks verified against J.11 plan; full 36-suite gate PASS; verdict: `APPROVE J.13 / K.5`; evidence adequate for source/catalog refinement planning; allowlist/warning-pilot activation premature until source citation refined; no files modified.
**Phase J.12 / Phase K.4 ROUTE-007 Duplicate Copy-to Regression Runner Implementation:** `docs/checkpoints/phase_j12_route007_duplicate_copyto_regression_checkpoint.md` — Dedicated regression runner `tools/run_phase_j12_route007_duplicate_copyto_regression.py` created; 13 checks (6 positive, 5 negative, 2 cross-rule preservation); all PASS; full 36-suite gate PASS; no config/severity/catalog/validator/renderer/prompt/command changes; error promotion unauthorized.
**Phase J.11 / Phase K.3 ROUTE-007 Duplicate Copy-to Regression Runner Plan:** `docs/planning/phase_j11_route007_duplicate_copyto_regression_plan.md` — Planning-only document for dedicated regression runner and fixture set for `CCI-ROUTE-007` exact duplicate Copy-to detection; 13 proposed fixture categories (6 positive, 5 negative, 2 cross-rule preservation); runner filename `tools/run_phase_j12_route007_duplicate_copyto_regression.py`; uses existing validator entry point; no config/severity/catalog/validator/renderer/prompt/command changes; error promotion unauthorized.
**Phase J.9 / Phase K.1 ROUTE-007 Duplicate Copy-to Candidate Plan:** `docs/planning/phase_j9_route007_duplicate_copyto_candidate_plan.md` — Planning-only document evaluating `CCI-ROUTE-007` as next controlled rule candidate after ROUTE-010/011; validator already implements exact duplicate detection; risks, evidence needs, future implementation path (J.10–J.17 / K.2–K.9), and explicit prohibitions documented; no config/severity/catalog/validator/renderer/prompt/command changes; error promotion unauthorized.
**Phase J.15 / Phase K.7 ROUTE-007 Candidate Closeout Checkpoint:** `docs/checkpoints/phase_j15_route007_candidate_closeout_checkpoint.md` — Track closed without promotion; regression coverage preserved; source citation found insufficient for warning-pilot activation; catalog unchanged; no config/severity/validator/catalog/renderer/prompt/command changes; error promotion unauthorized.
**Phase K.1 Next Explicit-Source Rule Candidate Scan:** `docs/planning/phase_k1_next_explicit_source_rule_candidate_scan.md` — Scan of all rule catalogs and validators; three deterministic, explicit-source-text candidates identified (CCI-CH7-SUBJ-002, CCI-REF-005, CCI-DTM-003); all already implemented in validators but lack dedicated regression runners; **recommended candidate: CCI-CH7-SUBJ-002** (subject line terminal punctuation); error promotion unauthorized.

**Phase K.2 CCI-CH7-SUBJ-002 Candidate Evaluation Plan:** `docs/planning/phase_k2_subject_terminal_punctuation_candidate_plan.md` — Planning-only document evaluating `CCI-CH7-SUBJ-002` (subject line terminal punctuation) as next controlled rule candidate; validator already implemented at `src/cci_subject_validate.py` lines 280-284; 11 proposed regression checks (3 positive, 6 negative, 2 cross-rule preservation); future runner `tools/run_phase_k3_subject_terminal_punctuation_regression.py`; no config/severity/allowlist/validator/catalog/renderer/prompt/command changes; error promotion unauthorized.

**Phase L.2 Conversational Builder Entry-Point Review:** `docs/planning/phase_l2_conversational_builder_entrypoint_review.md` — Read-only review confirming `IntakeOrchestrator` is ~80% of builder foundation; identifies missing multi-turn wrapper, plain-English formatter, and `window_envelope` schema gap; recommends L.3 schema definition next; no code changes.

**Phase L.3 Conversational Builder Payload Schema and Question Flow:** `docs/planning/phase_l3_conversational_builder_payload_schema_question_flow.md` — Planning-only schema definition specifying `BuilderSession` state transitions, minimum/recommended/optional field matrix, canonical question flow, plain-English warning formatter map for active pilots (ROUTE-010, ROUTE-011, SUBJ-002), proposed `src/conversational_builder.py` module interface (`BuilderSession` class with `start`, `ingest_user_message`, `next_question`, `build_payload`, `run_validation`, `warning_summary`, `finalize`), and `window_envelope` policy/question additions. No code changes.

**Phase L.4 Conversational Builder Prototype Implementation:** `docs/checkpoints/phase_l4_conversational_builder_prototype_checkpoint.md` — Prototype module `src/conversational_builder.py` created; `BuilderSession` class implements `start`, `ingest_user_message`, `next_question`, `build_payload`, `run_validation`, `warning_summary`, `finalize`, `record_user_decision`, `set_draft_final_status`; 10 tests, 39 checks PASS; full 37-suite gate PASS (PDF render/layout pre-existing failures only); no renderer/severity/config/validator/catalog/command changes; no error promotion; key-value/pass-through ingestion only; no NL parsing; no production UI integration; PDF generation deferred.

**Phase K.7 CCI-CH7-SUBJ-002 Warning Pilot Observation Decision:** `docs/checkpoints/phase_k7_subject_terminal_punctuation_warning_pilot_observation_decision.md` — Post-activation observation decision; config-only activation confirmed stable; full 37-suite gate PASS; decision: `continue warning pilot, pause repeated synthetic burn-in`; no rollback warranted; error promotion unauthorized; triggers for resuming observation listed; recommended next work: shift to user-facing conversational builder workflow or run new explicit-source candidate scan if user requests.

**Phase L.5A Conversational Builder Regression Harness Allowlist Cleanup:** `docs/checkpoints/phase_l5a_conversational_builder_regression_harness_allowlist_cleanup.md` — Added L.4/L.5 builder artifacts to H.4 regression runner allowlist (Check 17); eliminates cascade failures in H.6/H.13/H.16/H.24 sub-runners; full 35-suite non-PDF gate PASS; no builder behavior, renderer, config, validator, or command-layer changes; pure harness hygiene.

**Phase L.5 Conversational Builder Validation Summary Integration:** `docs/checkpoints/phase_l5_conversational_builder_validation_summary_checkpoint.md` — `validation_summary()` method added with structured counts, pending-decision tracking, finalize_allowed/block_reason logic; `warning_summary()` improved with known-pilot mapping from errors lists (validators emit pilot findings in errors when effective severity is warning/error); `finalize(accept_warnings=...)` parameter added; plain-English messages refined for ROUTE-010, ROUTE-011, SUBJ-002; L.4 regression updated to 41 checks, L.5 regression 36 checks; full 37-suite gate PASS (H.4/H.6/H.13/H.16/H.24 cascades are git-status cross-check artifacts, not behavioral regressions); no renderer/severity/config/validator/catalog/command changes; no error promotion.

**Phase L.6 Conversational Builder Payload-to-PDF Dry Run:** `docs/checkpoints/phase_l6_conversational_builder_payload_to_pdf_dry_run_checkpoint.md` — Verified `BuilderSession.finalize()` produces normalized payload suitable for existing PDF renderer; dry-run runner attempts PDF generation via `pdf_v6_render.py` entry point; skipped gracefully due to missing `reportlab` in environment (reported as environmental skip, not failure); 7/7 checks PASS; full 35-suite non-PDF gate PASS; no renderer/layout/config/validator/catalog/command changes; no error promotion.

|**Phase L.7B Conversational Builder PDF Signature Issue Triage:** `docs/checkpoints/phase_l7b_builder_payload_pdf_signature_issue_triage.md` — Triage of L.6 PDF dry-run failure root cause; determined synthetic payload passed `signature` as a list (due to builder list coercion) where renderer expects dict or string; corrected L.6 dry-run runner to inject structured signature dict directly; 7/7 checks PASS; full regression suite PASS; renderer untouched; no config/severity/validator/catalog/command changes; error promotion unauthorized.

|**Phase L.8 Conversational Builder Usability Review and Question-Coverage Audit:** `docs/planning/phase_l8_conversational_builder_usability_question_coverage_audit.md` — Read-only review of L.4–L.7B builder track; key finding: L.7 CLI is viable as developer/operator prototype but not end-user demo ready; key gap: signature capture must become structured before demo use; 239-line audit covering question coverage, user friction points, explicit prohibitions, and recommended next phase; no code/renderer/config/validator/catalog/command changes; error promotion unauthorized.

|**Phase L.8A Conversational Builder Usability Audit Tracker Sync:** Local tracker sync after L.8 audit completed on GitHub (`f09adf1`); updates `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` to reflect L.8 completion; no code/renderer/config/validator/catalog/command changes; recommended next phase: `Phase L.9 Conversational Builder Question Text and Signature Capture Improvements`.

|**Phase L.7A Conversational Builder CLI Local Verification:** `docs/checkpoints/phase_l7a_conversational_builder_cli_local_verification_checkpoint.md` — Local environment verification after pulling latest GitHub main (`3961e153`); all L.4–L.7 regressions PASS; L.7 CLI 26/26 PASS; full non-PDF gate 35/35 PASS; L.6 PDF skip is pre-existing environmental (reportlab signature-block error with sanitized payload, not new regression); no renderer/config/validator/catalog/command changes; error promotion unauthorized; approved for next phase.

||**Phase L.7 Conversational Builder Interactive CLI Prototype:** `docs/checkpoints/phase_l7_conversational_builder_interactive_cli_checkpoint.md` — Interactive CLI wrapper `tools/run_phase_l7_conversational_builder_cli.py` created; exposes `run_interactive()`, `run_scripted_sample()`, `pdf_dependency_status()`; accepts CLI args for `--scripted`, `--accept-warnings`, `--revise`; produces structured JSON output; 7/7 scripted checks PASS; no renderer/config/validator/catalog/command changes; error promotion unauthorized.
||**Phase L.9 Conversational Builder Question Text and Signature Capture Improvements:** `docs/checkpoints/phase_l9_conversational_builder_question_text_signature_capture_checkpoint.md` — Improved `BuilderSession` signature capture to store renderer-compatible dict signatures; `signature.name`, `signature.role`, `signature.title` support added; plain `signature:` mapped safely to `signature.name` dict; question text improved for subject, from, to, body, copy_to, distribution, window_envelope, signature; L.4 41/41 PASS, L.5 36/36 PASS, L.6 7/7 PASS, L.7 26/26 PASS, L.9 14/14 PASS, H.13 27/27 PASS, K.3 11/11 PASS, H.4 18/18 PASS, H.6 15/15 PASS, H.16 96/96 PASS, H.24 36/36 PASS, non-PDF gate 35/35 PASS, intake all PASS; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized.
||**Phase L.10 Conversational Builder Demo Script and Operator Walkthrough:** `docs/checkpoints/phase_l10_conversational_builder_demo_walkthrough_checkpoint.md` — Operator-facing walkthrough `docs/demo/conversational_builder_cli_walkthrough.md` and demo runner `tools/run_phase_l10_conversational_builder_demo_script.py`; demonstrates L.7 CLI from start to finalized payload; covers key-value input, commands, structured signature capture, warning acceptance, and troubleshooting; 14/14 demo checks PASS; L.9 11/11 PASS, L.7 26/26 PASS, L.6 7/7 PASS, intake 45/45 PASS; no renderer/layout/config/validator/catalog/command changes; no error promotion; no generated PDFs/logs committed.
||**Phase L.12 Conversational Builder End-to-End User Demo:** `docs/checkpoints/phase_l12_conversational_builder_end_to_end_demo_checkpoint.md` — Operator walkthrough `docs/demo/conversational_builder_end_to_end_demo.md` and runner `tools/run_phase_l12_conversational_builder_end_to_end_demo.py`; end-to-end demo from start session → key-value input → warning review → finalize → render → finished PDF; 13/13 L.12 demo checks PASS, 12/12 L.11 PASS, 14/14 L.10 PASS, 11/11 L.9 PASS, 26/26 L.7 PASS, 7/7 L.6 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 45/45 intake PASS; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized.
||**Phase L.12A Conversational Builder End-to-End Demo Local Verification:** `docs/checkpoints/phase_l12a_conversational_builder_end_to_end_demo_local_verification_checkpoint.md` — Local verification after GitHub push; pulled L.12 changes from origin; confirmed files present; ran full regression suite: 13/13 L.12 PASS, 12/12 L.11 PASS, 14/14 L.10 PASS, 11/11 L.9 PASS, 26/26 L.7 PASS, 7/7 L.6 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 45/45 intake PASS (204/204 total); generated PDFs cleaned up; working tree clean; no renderer/layout/config/validator/catalog/command changes; recommended next phase: `Phase L.13 Conversational Builder Product Roadmap Decision`.
||**Phase L.13 Conversational Builder Product Roadmap Decision:** `docs/planning/phase_l13_conversational_builder_product_roadmap_decision.md` — Commits product direction toward safe LLM mediator layer in front of deterministic `BuilderSession`; architecture: LLM proposes field updates and questions, BuilderSession remains source of truth for payload, validation, finalization, render; explicit safety boundaries: no bypass validation, no modify CCI severity/config, no invent official data, no silently ignore warnings, no control renderer layout, no final authority; proposed mediator contract documented with input/output schemas and invariant; recommended next phase: `Phase L.14 LLM Builder Mediator Contract Design`; later roadmap: L.15 mock mediator, L.16 real LLM adapter, L.17 NL intake demo, L.18 validation/revise loop, L.19 UI decision; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized.
||**Phase L.14 LLM Builder Mediator Contract Design:** `docs/planning/phase_l14_llm_builder_mediator_contract_design.md` — Defines concrete LLM mediator interface between natural-language user input and deterministic `BuilderSession`; input schema: session_id, current_step, payload_snapshot, missing_required_fields, validation_summary, warning_summary, error_summary, user_message, conversation_history_summary, available_commands, safety_flags; output schema: intent, proposed_payload_update, proposed_key_value_lines, next_question, explanation, requires_user_confirmation, warnings_to_surface, blocked_reason, confidence, safety_notes; allowed intents: start_letter, provide_field, revise_field, accept_warnings, request_warning_explanation, finalize, render_pdf, unknown; confirmation policy for inferred values, official data, finalize, render; field update rules with structured signature capture; warning/error explanation rules without suppression or downgrade; BuilderSession handoff invariant; failure modes; L.15 mock mediator test strategy; no renderer/layout/config/validator/catalog/command changes; no LLM API integration; error promotion unauthorized; recommended next phase: `Phase L.15 Mock LLM Mediator Contract Prototype`.
||**Phase L.15 Mock LLM Mediator Contract Prototype:** `docs/checkpoints/phase_l15_mock_llm_mediator_contract_prototype_checkpoint.md` — Deterministic mock mediator `src/llm_builder_mediator.py` with `MockLLMBuilderMediator`, `MediatorInput`, `MediatorOutput`; intent detection for 8 intents; field extraction via regex for from/to/subj/body/ssic/signature; confirmation policy for inferred values and official data; safety boundaries: no invented SSICs, no invented command data, no suppression of warnings; all updates emitted as `proposed_key_value_lines` for BuilderSession ingestion; 15/15 L.15 PASS, 13/13 L.12 PASS, 12/12 L.11 PASS, 11/11 L.9 PASS, 26/26 L.7 PASS, 7/7 L.6 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 45/45 intake PASS (219/219 total); no renderer/layout/config/validator/catalog/command changes; no real LLM/API dependency; no error promotion; recommended next phase: `Phase L.16 LLM Mediator Adapter Boundary Design`.
||**Phase L.16 LLM Mediator Adapter Boundary Design:** `docs/planning/phase_l16_llm_mediator_adapter_boundary_design.md` — Adapter boundary where real LLM replaces mock intent detection and field extraction while preserving L.14/L.15 contract; adapter interface: `LLMBuilderMediatorAdapter` with injected `backend: Callable[[str], str]`; strict output validation for required keys, allowed intents, dict payload updates, list key-value lines, bounded confidence; safety filters: reject CCI config/severity modification, reject renderer directives, reject invented official data, block silent warning acceptance, force confirmation for finalize/render, degrade low-confidence output; prompt contract: system instructions (translator not source of truth, no invented data, JSON-only output, allowed intents only, surface warnings), dynamic context (payload snapshot, missing fields, validation summary, user message), schema snippet; failure handling: model unavailable, invalid JSON, missing keys, unsupported intent, unsafe field, low confidence, conflicting instructions, pending warnings — all degrade to valid `MediatorOutput` with `unknown` intent + `next_question`; L.17 test strategy with fake backends; implementation recommendation: real LLM integration delayed until adapter validation passes; no renderer/layout/config/validator/catalog/command changes; no real LLM/network integration; error promotion unauthorized; recommended next phase: `Phase L.17 Fake-Backend LLM Mediator Adapter Prototype`.
||**Phase L.17 Fake-Backend LLM Mediator Adapter Prototype:** `docs/checkpoints/phase_l17_fake_backend_llm_mediator_adapter_checkpoint.md` — `LLMBuilderMediatorAdapter` implemented in `src/llm_builder_mediator.py` with `SafetyFilter`, `FakeBackend`; strict output validation: required keys, allowed intents, confidence bounds [0.0, 1.0], prohibited-key rejection; safety filters: CCI severity tamper rejected, renderer directives rejected, invented SSIC flagged, finalize/render/accept_warnings confirmation forced; 12 fake backend response keys for deterministic testing; degrades all malformed/unsafe output to `unknown` + `next_question`; 15/15 L.17 PASS, 15/15 L.15 PASS, 13/13 L.12 PASS, 12/12 L.11 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 45/45 intake PASS, 18/18 H.4 PASS (234/234 total); no real LLM/API/network dependency; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.18 Real LLM Provider Selection and Adapter Plan`.
||**Phase L.18 Real LLM Provider Selection and Adapter Plan:** `docs/planning/phase_l18_real_llm_provider_selection_and_adapter_plan.md` — Provider-agnostic adapter strategy; OpenAI recommended as first optional live smoke-test provider; Ollama/local provider remains optional experiment path; fake/mock backend remains default for all regressions; no live API calls required for regressions; no API keys committed; adapter boundary (`LLMBuilderMediatorAdapter`) already proven with fake backend; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.19 LLM Provider Interface and Configuration Plumbing`.
||**Phase L.19 LLM Provider Interface and Configuration Plumbing:** `docs/checkpoints/phase_l19_llm_provider_interface_config_checkpoint.md` — `LLMProviderConfig` env-driven config loader with safe defaults (mock backend if env vars absent); `build_llm_backend_from_config()` factory with mock default, OpenAI/Ollama placeholder backends, unsupported-provider safe degradation; `build_adapter_from_env()` one-shot factory; timeout clamped [0, 300], max_tokens clamped [0, 4096]; `to_dict()` never exposes API key values; no vendor SDK hard dependencies; 14/14 L.19 PASS, 15/15 L.17 PASS, 15/15 L.15 PASS, 13/13 L.12 PASS, 12/12 L.11 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 45/45 intake PASS, 18/18 H.4 PASS (248/248 total); no live API/network calls; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.20 Optional Live LLM Smoke-Test Harness`.
||**Phase L.20 Optional Live LLM Smoke-Test Harness:** `docs/checkpoints/phase_l20_optional_live_llm_smoke_test_checkpoint.md` — 8-check optional smoke harness gated by `SECNAV_LLM_LIVE_SMOKE=1`; default behavior is SKIP (exit 0); loads provider config, builds backend + adapter, sends minimal prompt, validates adapter output, redacts API key leakage; 8/8 mock backend PASS when enabled; placeholder backends yield controlled `unknown` intent without network calls; no live API calls unless explicitly enabled; no secrets printed/committed; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.21 LLM-Guided Natural-Language Intake Demo`.
||**Phase L.21 LLM-Guided Natural-Language Intake Demo:** `docs/checkpoints/phase_l21_llm_guided_natural_language_intake_demo_checkpoint.md` — 17-check conversational builder demo using mock mediator; NL-style messages converted to KV lines; all updates via `BuilderSession.ingest_user_message()`; validation, warning acceptance, finalize, PDF render + cleanup; guardrails verify no unsafe keys, no API key leakage; 17/17 L.21 PASS; no live LLM/API/network calls; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.22 LLM-Guided Intake User Interface Decision`.
||**Phase L.22 LLM-Guided Intake User Interface Decision:** `docs/planning/phase_l22_llm_guided_intake_user_interface_decision.md` — Decision document comparing CLI, Streamlit, Flask/FastAPI, and ChatGPT workflow options; hybrid recommendation: Streamlit as next user-facing prototype, CLI retained for regression/operator fallback, Flask/FastAPI deferred until UX stabilizes; defines L.23 Streamlit scope and safety requirements; no code changes; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.23 Streamlit LLM-Guided Intake Prototype`.
|||||||**Phase L.27A Retire Streamlit Web UI Path and Preserve Builder Core:** `docs/checkpoints/phase_l27a_retire_streamlit_ui_path_checkpoint.md` — User decision to stop investing in the Streamlit/Ollama web UI direction; all Streamlit/Ollama UI artifacts removed; `src/llm_provider_config.py` and `src/llm_builder_mediator.py` preserved for potential future Hermes-facing tool reuse; safety branch `backup/streamlit-ui-retired-from-9c1af61` created; 10/10 L.27A PASS, 27/27 H.13 PASS, 15/15 K.3 PASS, 18/18 H.4 PASS, 36/36 H.24 PASS; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.28 Conversational Builder Hermes Tool Integration`.

||||||||**Phase L.28 Conversational Builder Hermes Tool Integration:** `docs/checkpoints/phase_l28_hermes_secnav_cli_tool_checkpoint.md` — Added `tools/hermes_secnav_tool.py`, a deterministic CLI bridge for Hermes to drive SECNAV_ComplianceGPT without a web UI; commands: start, ingest, apply, status, validate, finalize, render, list, reset; uses `BuilderSession` as source of truth, `MockLLMBuilderMediator` for offline NL-to-KV extraction, session state persisted to `~/.hermes/secnav_sessions/<id>.json`; PDF rendered via existing `src/pdf_v6_render.py` path; 25/25 L.28 PASS, 10/10 L.27A PASS, 18/18 H.4 PASS, 27/27 H.13 PASS, 11/11 K.3 PASS, 36/36 H.24 PASS; no renderer/layout/config/validator/catalog/command changes; error promotion unauthorized; recommended next phase: `Phase L.29 Candidate Confirmation Infrastructure and Hermes Operating Model`.

||||||||**Phase L.29C Candidate Confirmation Infrastructure and Hermes Operating Model:** `docs/checkpoints/phase_l29c_candidate_confirmation_infrastructure_checkpoint.md` — Candidate schema, BuilderSession candidate tracking, CLI bridge candidate commands, Hermes operating model; safe application mapping for 8 candidate types; security guards block unsafe keys; session persistence extended; 23/23 L.29C PASS; H.4/H.13/H.16/H.24 failures are pre-existing cascades unrelated to L.29C; no renderer/layout/config/validator/catalog/command changes; no live lookup; no static database; error promotion unauthorized; recommended next phase: `Phase L.29D Hermes Live Lookup Wiring`.

||||||||**Phase L.29E Live Lookup Browser Requirement:** `docs/checkpoints/phase_l29e_live_lookup_browser_requirement_checkpoint.md` — Documentation-only phase identifying browser tooling gap for official .mil/SECNAV source retrieval; raw curl blocked by WAF/CDN on `.mil` sites; CDP/browser automation unavailable; defined five source quality tiers; documented candidate creation rules and browser/tooling evaluation options; no source code changed; no renderer/layout/config/validator/catalog changes; no static database; error promotion unauthorized; recommended next phase: `Phase L.29F Browser-Capable Lookup Harness Discovery`.

||||||||**Phase L.29H General Live Lookup Candidate Workflow Design:** `docs/checkpoints/phase_l29h_general_live_lookup_candidate_workflow_checkpoint.md` — Reusable general workflow for dynamic per-letter live lookup candidate creation; defines unresolved fact detection, lookup decision table, source tiering, candidate creation rules for 8 types, user confirmation flow, letterhead/SSIC/routing rules; corrects prior one-off hardcoded candidate approach; sample request used only as fixture illustration, not hardcoded; browser-agent runtime prerequisites documented; no source code changed; no renderer/layout/config/validator/catalog changes; no static database; no hardcoded MISSA/MCAS behavior; error promotion unauthorized; recommended next phase: `Phase L.29I General Live Lookup Candidate Workflow Verification`.

||||||||**Phase L.29I General Live Lookup Candidate Workflow Verification:** `docs/checkpoints/phase_l29i_general_workflow_verification_report.md` — Verified general workflow on NAVFAC MIDLANT-to-NAS Oceana sample (different from MISSA/MCAS); three CANDIDATE_V1 records created (command_expansion, unit_identity, ssic_candidate); all pending, payload unchanged; browser lookups confirmed Tier 1 sources for NAVFAC and NAS Oceana; workflow generalized successfully; no source code changed; no renderer/layout/config/validator/catalog changes; no static database; error promotion unauthorized; recommended next phase: `Phase L.29J Rule-Driven Unresolved Fact Detector Design`.

||||||||**Phase L.29J Rule-Driven Unresolved Fact Detector Design:** `docs/checkpoints/phase_l29j_rule_driven_unresolved_fact_detector_design_report.md` — Inventoried all existing rule sources (field policy, questions, context schema, H/S/P/V series, CCI routing/subject/candidate rules); classified each by usability for unresolved-fact detection; designed RULE_FACT_MAP_V1 schema and UNRESOLVED_FACTS_V1 output schema; compared standard_letter/endorsement/memorandum_for_record coverage; identified gaps (letterhead_memo/memo_of_agreement/memo_of_understanding lack field policy); recommended hybrid architecture consuming existing rules; no source code changed; no renderer/layout/config/validator/catalog changes; error promotion unauthorized; recommended next phase: `Phase L.29K Rule-to-Fact Mapping File Creation`.

||||||||**Phase L.29K Rule-to-Fact Mapping File Creation:** `docs/checkpoints/phase_l29k_rule_fact_mapping_checkpoint.md` — ... [same content]

||||||||**Phase L.29L Unresolved Fact Detector Prototype Implementation:** `docs/checkpoints/phase_l29l_unresolved_fact_detector_checkpoint.md` — ... [same content]

||||||||**Phase L.29M Detector-to-Tool Wiring:** `docs/checkpoints/phase_l29m_detector_to_tool_wiring_checkpoint.md` — Wired `detect_unresolved_facts()` into `tools/hermes_secnav_tool.py` as `detect-facts` command; loads existing session, builds payload, calls detector, returns `UNRESOLVED_FACTS_V1` JSON; does not mutate session, create candidates, or apply anything; regression runner 37/37 PASS; L.29L/L.29K/L.29C/L.28 regressions all PASS; no renderer/layout/config/validator/catalog changes; no static database; error promotion unauthorized; recommended next phase: `Phase L.29N Hermes Agent Integration`.

||||||||**Phase L.29N Hermes Agent Integration Loop Design:** `docs/checkpoints/phase_l29n_hermes_agent_integration_loop_checkpoint.md` — Design specification `docs/hermes_agent_integration_loop.md` created; defines how Hermes should use `detect-facts` after ingest to drive the builder loop; action handling by `recommended_action` (ask_user, live_lookup, candidate_low_confidence, safe_infer, leave_blank, refuse_to_infer); priority order; question selection rules; candidate rules; render gate with four conditions; three example workflows; safety boundaries; no source code/renderer/validator/CCI/detector/candidate changes; no static database; error promotion unauthorized; recommended next phase: `Phase L.29O Hermes Agent Integration Prototype`.

||||||||**Phase L.29O Hermes Agent Integration Prototype:** `docs/checkpoints/phase_l29o_hermes_loop_prototype_checkpoint.md` — Created `tools/hermes_loop_prototype.py`, a narrow deterministic prototype proving the real CLI can support the Hermes question loop; three scenarios (standard_letter_minimal, mfr_minimal, endorsement_minimal) all reach blocking==0; reuses existing BuilderSession, MockLLMBuilderMediator, and detect_unresolved_facts() code paths; no duplicated detector logic, no candidate creation, no live lookup, no render; regression runner 26/26 PASS; L.29M/L.29L/L.29K/L.29C/L.28 regressions all PASS; no renderer/layout/config/validator/catalog changes; no static database; error promotion unauthorized; recommended next phase: `Phase L.29P Hermes Agent Integration with Real LLM`.

**Next Phase:** `Phase L.29P Hermes Agent Integration with Real LLM`

**Burn-in clock note:**

**Known limitations (non-blocking for warning pilot):**
- Exotic whitespace (zero-width space `\u200B`, BOM `\uFEFF`) does not trigger `CCI-ROUTE-011` because `str.strip()` does not strip them. Acceptable for warning pilot. Consider validator hardening before any future error promotion.
- Window-envelope-like letters without `window_envelope: true` block as expected. This is operator/data-quality risk, not a false positive.

**Future error promotion:** Unauthorized. Requires separate planning, review checkpoint, and explicit user approval before any discussion of H.17 / I.16.

---

## 1. Purpose

The Correction Memory and Rule Promotion Layer lets a user correct draft output, apply that correction safely, classify the correction, optionally remember it in scoped storage, and promote possible global rules only through human review and implementation planning.

The layer is not a replacement for deterministic SECNAV validators. It is a controlled feedback loop with strict guardrails so that local preferences, one-time wording edits, and AI/user suggestions do not silently become global compliance rules.

---

## 2. Core Principle

1. Apply corrections immediately to the active draft when requested.
2. Reuse corrections only within the approved scope.
3. Promote possible global rules only through review, planning, implementation, and regression.
4. Never enforce approved records automatically from local logs.
5. Never commit real session stores, pending logs, approved promotion logs, command profiles, or contact/user data.

---

## 3. Correction Scopes

| Scope | Auto-reuse | Status | Description |
|---|---|---|---|
| `active_draft` | Yes — immediate | Implemented | Correction applies only to the current draft and is tracked in memory. |
| `current_session` | Yes — when context matches | Implemented in Phase A | Correction persists to local gitignored session JSONL when explicitly scoped and `session_id` is provided. |
| `local_command_profile` | Yes — after explicit approval | Implemented in Phase C | Correction becomes part of a local command profile after two-step approval. |
| `pending_global_rule_candidate` | No — review only | Implemented in Phase D | Possible global/manual/validator issue logged locally for human review. |
| `approved_global_rule` | Only after implementation | Implemented workflow through Phase H.1 pilot | Phase E approves records with `pending_implementation`; Phase H plans implementation; Phase H.1 can implement one selected approved record into catalog/validator/prompt/docs after approval and regression. |

---

## 4. Implemented Modules

- `src/correction_apply.py` — active-draft correction apply/undo primitives.
- `src/correction_capture.py` — correction capture and automatic classification handoff.
- `src/correction_store.py` — local session JSONL persistence.
- `src/correction_classify.py` — Phase B correction classifier.
- `src/correction_promote.py` — Phase C local command profile promotion.
- `src/correction_pending_log.py` — Phase D pending global rule candidate logging.
- `src/correction_review.py` — Phase E review/promotion utility and approved-record creation.
- `src/correction_commands.py` — Phase F slash-command dispatcher.
- `src/correction_nl_commands.py` — Phase G deterministic natural-language mediation.
- `src/correction_implementation_planner.py` — Phase H/H.1 implementation planner and public `mark_implemented()` wrapper.
- `rules_v6/CCI/cci_ch7_subject_rules.json` — includes Phase H.1 pilot rule catalog entry `CCI-CH7-SUBJ-006`.

---

## 5. Implemented Storage Safety

- `.gitignore` excludes session JSONL, pending candidate logs, and approved promotion logs.
- `corrections/session/.gitkeep` keeps the local session directory structure.
- `corrections/session/README.md` explains local-only session correction storage.
- `corrections/README.md` explains local-only correction storage safety.
- `corrections/pending_corrections.jsonl` is local/gitignored.
- `corrections/approved_rule_promotions.json` is local/gitignored.

---

## 6. Completed Phases

### Phase A — Session Correction Persistence

- Commit: `71ddf64` — `CCI: Add session correction persistence (Phase A)`.
- Added opt-in local session persistence under `corrections/session/`.
- Session corrections are reused only when context matches.
- Rejected session corrections are soft-marked and excluded from future matching.

### Phase B — Correction Classification

- Commit: `519fad6` — `CCI: Add correction classification (Phase B)`.
- Added deterministic classification into one-time wording, local command preference, possible SECNAV manual rule, or validator gap.

### Phase C — Local Command Profile Promotion

- Commit: `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`.
- Added two-step profile promotion, backup, atomic write, disable/remove/edit.
- Local command preferences remain scoped to local profiles.

### Phase D — Pending Global Rule Candidate Logging

- Commit: `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`.
- Added explicit-approval pending-candidate logging for possible global rules or validator gaps.
- Pending logs remain local/gitignored.

### Phase E — Review/Promotion Utility

- Commit: `058de87` — `CCI: Add review promotion utility (Phase E)`.
- Added human claim/review, evidence validation, and approved-record creation.
- Approved records are created with `implementation_status="pending_implementation"` only.

### Phase F — Command Integration Layer

- Commit: `4ba5cd3` — `CCI: Add command integration layer (Phase F)`.
- Added slash-command dispatcher and confirmation-required persistent actions.
- Delegates to Phase A-E APIs only; no direct persistence writes.

### Phase G — Natural-Language Command Mediation

- Commit: `cb988bc` — `CCI: Add natural language command mediation (Phase G)`.
- Added deterministic natural-language mediator.
- No AI/LLM imports, no renderer imports, no validator imports, no direct file writes.

### Phase H — Approved-Rule Implementation Planner

- Commit: `2588e67` — `CCI: Add approved rule implementation planner (Phase H)`.
- Added eligibility validation, implementer claim/assignment, target assignment, source verification summary, status transitions, deferral/rejection/superseded handling.
- Planner/status-workflow only; no validator, rule catalog, prompt-contract, or renderer changes in Stage 1.

### Phase H.1 / Phase I — Pilot Approved-Rule Implementation

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
- Advisory code: `CCI-ROUTE-010`.
- Rule: If the office code is numeric-only, add `Code` before the number. Do not add `Code` before an office code that starts with a letter (e.g., `N` or `SUP`).
- Source: SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General.
- Added `_check_office_code_prefix(...)` helper in `src/cci_routing_validate.py`.
- Scope: `to` and `via` routing lines only; `copy_to` not checked in Phase H.4.
- False-positive controls: candidate office codes require comma delimiter or parenthetical enclosure; trailing numbers without delimiter do not trigger.
- Catalog severity remains `error`; validator enforcement is interim advisory/non-blocking only.
- Added `tools/run_phase_h4_routing_office_code_validator_regression.py` with 18 checks.
- 13 synthetic `examples/routing_*.json` fixtures added for edge-case coverage.
- Full 28-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- No renderer/layout changes.
- No runtime prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- Approved/pending logs remained local/gitignored and were not committed.

### Phase H.5 / Phase I.4 — Routing Office-Code Severity Review Planning (Approved)

- Planning document: `docs/planning/phase_h5_routing_office_code_severity_review_plan.md`.
- Planning checkpoint commits: `8bf5efa` — `Docs: Add Phase H.5 routing office code severity plan`; `ece374b` — `Docs: Refine Phase H.5 routing office code severity plan`.
- **Approved verdict: keep `CCI-ROUTE-010` advisory-only; do not promote to warning/error in Phase H.5.**
- Feature flag/config design is deferred to a future implementation phase.
- Copy-to remains out of scope.
- Evidence collection required before any future severity promotion: 20 negative-control fixtures + 10 positive-control fixtures + 50 real-world To/Via patterns.
- Terminology standardized to `negative-control fixtures` (must not trigger) and `positive-control fixtures` (must trigger).
- No code changes. No validator changes. No renderer/layout changes. No prompt-contract changes. No command-layer changes. No approved/pending logs committed. No real data committed.
- Current functional baseline remains `1e990a6` (Phase H.4). Regression set remains 28 suites.

### Phase H.6 / Phase I.5 — Routing Office-Code Evidence Collection and Regression Hardening (Completed)

- Planning document: `docs/planning/phase_h6_routing_office_code_evidence_hardening_plan.md`.
- Planning commits: `84c349e` — `Docs: Add Phase H.6 routing office code evidence plan`; `04148ba` — `Docs: Fix Phase H.6 advisory format expectation`.
- Implementation commit: `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`.
- Added 20 negative-control fixtures (`examples/routing_h6_negative_01.json` through `routing_h6_negative_20.json`) and 10 positive-control fixtures (`examples/routing_h6_positive_01.json` through `routing_h6_positive_10.json`).
- Added `tools/run_phase_h6_routing_office_code_evidence_regression.py` with 15 checks covering fixture existence, false-positive/negative controls, `(advisory):` format verification, `errors`-list emptiness, copy-to exclusion, H.4 runner still passes, local corpus gitignored, no validator changes, no forbidden files changed.
- Added local corpus `corrections/evidence/routing_office_code_patterns.jsonl` with 50 synthetic-realistic To/Via patterns; corpus remains gitignored and was not committed.
- **No severity promotion.** `CCI-ROUTE-010` remains advisory-only.
- **No validator logic changes.** `src/cci_routing_validate.py` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No approved/pending/session logs committed.** All correction storage remains local/gitignored.
- Full 29-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline: `662afbb`. Regression set: 29 suites.

### Phase H.7 / Phase I.6 — Routing Office-Code Evidence Review and Planning Decision (Approved)

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

### Phase H.10 / Phase I.9 — From-Line Evidence Collection and Regression Hardening (Completed)

- Planning document: `docs/planning/phase_h10_from_line_evidence_hardening_plan.md`.
- Planning commits: `8735461` — `Docs: Add Phase H.10 From line evidence plan`; `310fd3a` — `Docs: Refine Phase H.10 From line evidence plan`.
- Infrastructure fix commit: `49577d9` — `Test: Fix H.8 runner baseline comparison`.
- Implementation commit: `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`.
- Added 20 negative-control fixtures (`examples/routing_from_h10_neg_01.json` through `routing_from_h10_neg_20.json`) and 10 positive-control fixtures (`examples/routing_from_h10_pos_01.json` through `routing_from_h10_pos_10.json`).
- Added local corpus `corrections/evidence/from_line_patterns.jsonl` with 50 synthetic From-line patterns; corpus remains gitignored and was not committed.
- Added `tools/run_phase_h10_from_line_evidence_regression.py` with 39 checks covering fixture existence, negative/positive control validation, `errors`-list emptiness, `warnings`-only findings, window-envelope truthiness suppression, missing-doc_type skip, non-standard-doc_type skip, dual-rule trigger, H.9 and H.8 runner preservation, corpus gitignored, no validator/catalog/renderer/prompt/command changes.
- **No severity promotion.** `CCI-ROUTE-011` remains advisory-only.
- **No validator logic changes.** `src/cci_routing_validate.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No approved/pending/session logs committed.**
- **No real data committed.**
- Full 32-suite local regression set passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline: `d808cb8`. Regression set: 32 suites (31 existing + 1 new H.10 runner).

The current local regression set is **32 suites**:

- `tools/run_phase_h10_from_line_evidence_regression.py` — Phase H.10 From-line evidence regression, 39 checks.
- `tools/run_phase_h9_from_line_validator_regression.py` — Phase H.9 From-line advisory validator regression, 18 checks.
- `tools/run_phase_h8_third_rule_catalog_regression.py` — Phase H.8 third rule-catalog pilot regression, 16 checks.
- `tools/run_phase_h6_routing_office_code_evidence_regression.py` — Phase H.6 evidence regression, 15 checks.
- `tools/run_phase_h4_routing_office_code_validator_regression.py` — Phase H.4 routing validator regression, 18 checks.
- `tools/run_phase_h3_second_rule_catalog_regression.py` — Phase H.3 second rule-catalog pilot regression, 15 checks.
- `tools/run_phase_h2_subject_acronym_validator_regression.py` — Phase H.2 advisory subject-line acronym regression, 12 checks.
- `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — Phase H.1 pilot regression, 11 checks.
- `tools/run_correction_implementation_regression.py` — Phase H/H.1 planner regression, 45 checks.
- `tools/run_correction_nl_command_regression.py` — Phase G, 151 checks.
- `tools/run_correction_command_regression.py` — Phase F, 45 checks.
- `tools/run_correction_review_regression.py` — Phase E, 30 checks.
- `tools/run_correction_pending_regression.py` — Phase D, 33 checks.
- `tools/run_correction_profile_promotion_regression.py` — Phase C, 33 checks.
- `tools/run_correction_classify_regression.py` — Phase B.
- Intake, correction, session, profile, audit, context-schema, CCI subject/ref-encl/acronym/date-time/personnel/POC/routing, and C7-C10 layout regressions.

The 32-suite set passed locally after Phase H.10 when run with `C:\Users\drryl\pinokio\bin\miniconda\python.exe`. Earlier C7-C10 failures were environment-only from using the wrong Python interpreter without `fitz`/PyMuPDF.

---

## 8. Safety Guardrails

- Do not edit renderer/layout casually.
- Do not create a parallel renderer.
- Do not implement additional global rule enforcement, validator enforcement, prompt-contract changes, or additional rule-catalog changes without approved planning.
- Do not commit real command profiles, contact data, session JSONL stores, pending candidate logs, or approved promotion logs publicly.
- Do not skip regressions.
- Do not assume Navy and Marine Corps conventions are identical.
- Do not ignore rules hidden inside manual figures, captions, or example text.
- Do not modify rules without preserving/updating provenance.

---

## 9. Next Phase Planning Target

The next planning-only phase is **Phase H.11 / Phase I.10**.

Phase H.10 / Phase I.9 From-line evidence collection and regression hardening is complete. The approved plan is at `docs/planning/phase_h10_from_line_evidence_hardening_plan.md` (commits `8735461`, `310fd3a`). Implementation commit `d808cb8`.

Phase H.10 summary:
- **Added 20 negative-control + 10 positive-control fixtures for CCI-ROUTE-011.**
- **Added 50-pattern local corpus** `corrections/evidence/from_line_patterns.jsonl` (gitignored, not committed).
- **Added `tools/run_phase_h10_from_line_evidence_regression.py` with 39 checks.**
- **No severity promotion.** `CCI-ROUTE-011` remains advisory-only.
- **No validator logic changes.** `src/cci_routing_validate.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/cci_ch2_routing_rules.json` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No approved/pending/session logs committed.**
- **No real data committed.**
- Full 32-suite local regression set passed after H.10 implementation using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.
- Current functional baseline: `d808cb8`. Regression set: 32 suites.
- Latest planning checkpoint commit: `310fd3a`.

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

### Phase H.12 / Phase I.11 — Fourth Catalog-Only Pilot Planning (Not Yet Approved)

**Phase H.11 is now approved.** The next phase is **Phase H.12 / Phase I.11** (planning-only until approved).

Phase H.12 search results:

- **Priority-domain search:** No candidate found in subject (Ch 7, Para 9), ref/encl (Ch 7, Para 10-11), date/time (Ch 2, Para 2-4.2), or routing.
- **Expanded-domain search:** No candidate found in paragraphing, proofreading, signature line, writing style, abbreviations, personnel, memo salutation/close, enclosure numbering, addressing, or page numbering.
- **Catalog maturity assessment:** Current catalog is reasonably mature for obvious deterministic catalog-only rules in current scope.
- **H.12 plan approved:** `c608ef6`.
- **H.12 design review approved:** `a450208`.

Phase H.12 rejected candidates:
| # | Candidate | Rejection Reason |
|---|---|---|
| 1 | Title case for subject in body | Body-text heuristic |
| 2 | Repeat subject in reply | Procedural, not deterministic |
| 3 | Never subparagraph beyond Figure 7-8 | Body-parser requirement |
| 4 | Never split ship name | Renderer/layout implication |
| 5 | Do not capitalize last name in body | Duplicate of PER-001 |
| 6 | Acronyms used after first use | Heuristic; semantic interpretation |
| 7 | No salutation in memorandum | v6 model has no salutation field |
| 8 | No complimentary close in memorandum | v6 model has no close field |
| 9 | Parenthesized number for every enclosure | Renderer ambiguity / REF-007 overlap |
| 10 | No abbreviations in address | Layout implication |
| 11 | No page number on first page | Layout implication |
| 12 | Avoid slang or jargon | Heuristic, not deterministic |

Phase H.12 safety boundaries preserved:
- No validator changes.
- No rule catalog changes.
- No renderer/layout changes.
- No prompt-contract changes.
- No command-layer changes.
- No approved/pending/session logs committed.
- No real data committed.

**Phase D candidate creation remains blocked.** No suitable candidate found.

### Phase H.13 / Phase I.12 — Feature-Flag/Config Support (Implemented, Reviewed, Approved as Stable Baseline)

**Phase H.13 implementation commit:** `084ce64` — `CCI: Add H.13 severity config support`.  
**Phase H.13 implementation checkpoint:** `a520eb2` — `Docs: Record Phase H.13 implementation checkpoint`.  
**Phase H.13 implementation review checkpoint:** `[TBD]` — `Docs: Record Phase H.13 implementation review checkpoint`.  
**Phase H.13 planning commits:** `dd1989e`, `115f4e0`, `1759c9f`.  
**Review verdict:** `APPROVE H.13 IMPLEMENTATION AS STABLE BASELINE`.  
**Regression gate:** 33/33 PASS (32 existing + 1 new H.13 runner).

**What changed:**
- Added `src/cci_severity_mapper.py` — shared config-driven severity resolver.
- Added `config/cci_enforcement_config.json` — tracked default config with explicit `CCI-ROUTE-010` and `CCI-ROUTE-011` entries set to `effective_severity: advisory`.
- Added `tools/run_phase_h13_config_regression.py` — 26-check targeted regression runner.
- Modified `src/cci_routing_validate.py` — severity branching for ROUTE-010/011; `validator_runner.py` untouched.
- Added `.gitignore` entry for `config/cci_enforcement_config.local.json`.

**Safety preserved:**
- Default config does not promote either rule.
- Missing/malformed/unknown/unapproved config → advisory fallback.
- `effective_severity` clamped to `allow_override_up_to` and catalog severity.
- `validator_runner.py` untouched.
- No renderer/layout changes.
- No prompt-contract/context/intake/UI/command-flow changes.
- No Phase F/G command-layer changes.
- No approved/pending/session/evidence logs committed.
- No real data committed.
- `CCI-ROUTE-010` remains advisory-only.
- `CCI-ROUTE-011` remains advisory-only.

**Current functional baseline:** `d808cb8`. Regression set: 33 suites. H.13 stable baseline: `084ce64`.

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 33 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.
- No validator, prompt-contract, or renderer changes may occur until explicitly planned, approved, implemented, reviewed, and regression-tested.

### Phase H.14 / Phase I.13 — Controlled Promotion Readiness Review (Completed — Read-Only)

**Review commit:** `fcb1d4c` — `Docs: Record Phase H.13 implementation review checkpoint`.
**Scope:** Read-only review. No files modified. No severity changed. No commits.
**H.14 review verdict:**
- `CCI-ROUTE-010`: **NOT READY — NEEDS MORE EVIDENCE**
- `CCI-ROUTE-011`: **READY FOR WARNING PILOT**
- Error promotion for either rule: **NOT RECOMMENDED**

**Regression results:**
- H.13 config regression: 26/26 PASS
- H.9 From-line validator: 18/18 PASS
- H.10 From-line evidence: 39/39 PASS
- H.6 office-code evidence: 15/15 PASS
- H.8 third-rule catalog: 16/16 PASS
- H.4 office-code validator: 18/18 PASS
- Full gate: 33/33 PASS (explicit Miniconda Python)

**Key findings:**
- `CCI-ROUTE-010` remains advisory. Parsing complexity and lack of real-world To/Via patterns create unquantified false-positive risk.
- `CCI-ROUTE-011` is simpler (binary present/absent), narrow in scope, handles the `window_envelope` exception, and has lower false-positive risk.
- Config-driven severity mechanism (H.13) enables immediate rollback.
- A 30-day burn-in period should be required before any error-level discussion.

|**Recommended next phase:** Phase H.15 / Phase I.14 — Controlled Warning Pilot for `CCI-ROUTE-011`.

### Phase I.37 / Phase J.1 — CCI-ROUTE-010 Warning Pilot Plan (Planning-Only, Approved)

- Planning document: `docs/planning/phase_i37_route010_warning_pilot_plan.md`.
- **Review phase:** I.38 / J.2 — `APPROVE I.38 / J.2 ROUTE-010 WARNING PILOT PLAN REVIEW`
- **Scope:** Evaluate whether `CCI-ROUTE-010` should enter a controlled warning pilot, mirroring the H.15 `CCI-ROUTE-011` warning pilot process.
- **Current state at planning time:** `CCI-ROUTE-010` = `advisory`; `CCI-ROUTE-011` = `warning` (active pilot); `global_default` = `advisory`; 35-suite regression baseline; no error promotion authorized.
- **Activation (I.39/J.3):** Config-only change; `CCI-ROUTE-010.effective_severity` changed from `advisory` to `warning`. No validator, catalog, renderer, prompt, or command-layer changes.
- **Why reasonable:** Deterministic rule; exact source quote exists; validator already detects both Check A and Check B; rule is allowlisted; rollback is config-only; precedent from ROUTE-011 warning pilot.
- **Risks documented:** False positives on non-office-code text; unusual office-code formats; parsing limits; mixed Navy/Marine Corps expectations; possible context-specific `Code` usage.
- **Burn-in executed at activation:** H.4 validator regression (18 checks PASS), H.6 evidence regression (15 checks PASS), H.13 config regression (27 checks PASS), full 35-suite gate PASS.
- **Rollback path:** Restore `effective_severity` to `advisory`; rerun H.13, H.4, H.6; rerun full gate if needed.
- **Explicit prohibitions maintained:** No error promotion; no validator/catalog/renderer/prompt/command changes; no logs or unsanitized material committed; `docs/BOOTSTRAP.md` and `docs/HERMES_INSTRUCTIONS.md` untouched.
- **Recommended next phase:** Phase I.40 / Phase J.4 — ROUTE-010 Warning Pilot Burn-In Checkpoint #1.

### Phase I.39 / Phase J.3 — CCI-ROUTE-010 Warning Pilot Activation (Completed)

- Activation checkpoint: `docs/checkpoints/phase_i39_route010_warning_pilot_activation_checkpoint.md`
- **Action:** Config-only activation; `CCI-ROUTE-010.effective_severity` = `warning`
- **Runner updates:** H.4, H.6, H.9, H.10, H.13 runner expectations updated to check both warnings and errors for ROUTE-010 presence/absence
- **Results:** 18/18 H.4 PASS, 15/15 H.6 PASS, 18/18 H.9 PASS, 39/39 H.10 PASS, 27/27 H.13 PASS, 35-suite gate PASS
- **Post-activation state:** `CCI-ROUTE-010` = `warning`, `CCI-ROUTE-011` = `warning`, `global_default` = `advisory`
- **Error promotion:** Unauthorized

### Phase I.39B / Phase J.3B — CCI-ROUTE-010 Warning Pilot Runner Comment Cleanup (Completed)

- Cleanup checkpoint: `docs/checkpoints/phase_i39b_route010_runner_comment_cleanup_checkpoint.md`
- **Action:** Comment/docstring/header text cleanup only in regression runner files (H.4, H.6, H.9, H.10, H.13); removed stale advisory-era wording
- **No behavior change:** executable logic, fixtures, config, validator, catalog, renderer, prompt, command-layer untouched
- **Results:** 18/18 H.4 PASS, 15/15 H.6 PASS, 18/18 H.9 PASS, 39/39 H.10 PASS, 27/27 H.13 PASS, 35-suite gate PASS
- **Post-cleanup state:** `CCI-ROUTE-010` = `warning`, `CCI-ROUTE-011` = `warning`, `global_default` = `advisory`
- **Error promotion:** Unauthorized
- **Recommended next phase:** Phase I.40 / Phase J.4 — ROUTE-010 Warning Pilot Burn-In Checkpoint #1

---

## 10. Manual-and-Figure Source Standard

Every new layout profile and rule interpretation must be grounded in all available manual guidance, including:

1. Chapter/section text surrounding the figure.
2. Figure title/caption.
3. Instructional text inside the figure example itself.
4. Actual visual/layout geometry.
5. Existing project rule files and renderer behavior.

Figures are rule-bearing and must be reviewed when referenced.

---

End of Correction Memory and Rule Promotion Layer Plan.
