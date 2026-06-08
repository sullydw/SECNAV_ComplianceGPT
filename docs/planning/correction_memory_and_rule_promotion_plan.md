# Correction Memory and Rule Promotion Layer Plan

**Current Verified Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`
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
**Latest Checkpoint:** `[TBD]` / Phase H.12 no-candidate search complete (approved plan; no candidate found)  
**Next Phase:** Phase H.13 / Phase I.12 feature-flag/config planning — planning-only until approved

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

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 32 regression suites must pass before any commit.
- Use `C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.
- No validator, prompt-contract, or renderer changes may occur until Phase H.12 / Phase I.11 is explicitly planned, approved, implemented, reviewed, and regression-tested.

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
