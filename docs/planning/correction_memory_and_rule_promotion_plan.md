# Correction Memory and Rule Promotion Layer Plan

**Current Verified Baseline:** `46edcbd` — CCI: Add routing office code catalog rule (Phase H.3)  
**Phase H.3 Implementation:** `46edcbd` — CCI: Add routing office code catalog rule (Phase H.3)  
**Phase H.2 Implementation:** `609821e` — CCI: Add subject acronym advisory validator (Phase H.2)  
**Phase H.1 Pilot Implementation:** `ef365d3` — CCI: Implement pilot approved rule (Phase H.1)  
**Phase H.1 Mark-Implemented Wrapper:** `6298dab` — CCI: Add public mark implemented wrapper  
**Phase H Implementation:** `2588e67` — CCI: Add approved rule implementation planner (Phase H)  
**Phase G Implementation:** `cb988bc` — CCI: Add natural language command mediation (Phase G)  
**Phase F Implementation:** `4ba5cd3` — CCI: Add command integration layer (Phase F)  
**Phase E Implementation:** `058de87` — CCI: Add review promotion utility (Phase E)  
**Phase D Implementation:** `2e31892` — CCI: Add pending global rule candidate logging (Phase D)  
**Phase C Implementation:** `8b8a95c` — CCI: Add local command profile promotion (Phase C)  
**Phase B Implementation:** `519fad6` — CCI: Add correction classification (Phase B)  
**Phase A Implementation:** `71ddf64` — CCI: Add session correction persistence (Phase A)  
**Latest Checkpoint:** `46edcbd` / Phase H.3 second rule-catalog-only pilot handoff  
**Next Phase:** Phase H.4 / Phase I.3 validator enforcement planning or third catalog-pilot planning — planning-only until approved

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

---

## 7. Current Regression Coverage

Use the explicit Pinokio/Miniconda Python for full local regression runs:

`C:\Users\drryl\pinokio\bin\miniconda\python.exe`

The current local regression set is **27 suites**:

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

The 27-suite set passed locally after Phase H.3 when run with `C:\Users\drryl\pinokio\bin\miniconda\python.exe`. Earlier C7-C10 failures were environment-only from using the wrong Python interpreter without `fitz`/PyMuPDF.

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

The next planning-only phase is **Phase H.4 / Phase I.3 validator enforcement planning or third catalog-pilot planning**.

Phase H.3 / Phase I.2 second rule-catalog-only pilot is complete:
- Catalog entry `CCI-ROUTE-010` added to `rules_v6/CCI/cci_ch2_routing_rules.json`.
- Rule: numeric-only office codes require `Code`; office codes starting with letters must not use `Code`.
- 27-suite regression set verified PASS.
- No validator changes. No renderer/layout changes. No prompt-contract changes. No command-layer changes.

Phase H.2 / Phase I.1 subject-line acronym validator advisory enforcement is also complete:
- Advisory code `CCI-CH7-SUBJ-007` implemented in `src/cci_subject_validate.py`.
- Curated prohibited list: `POC`, `UIC`, `OIC`.
- 26-suite regression set verified PASS.
- `src/cci_acronym_validate.py` untouched.
- No renderer/layout changes. No prompt-contract changes. No command-layer changes.

The next phase must decide **one** of the following directions:

1. **Plan validator enforcement for `CCI-ROUTE-010`** so the office-code rule is checked by the routing validator.
2. **Further refine `CCI-CH7-SUBJ-007`** (expand prohibited list or promote severity).
3. **Add a third low-risk approved-rule pilot** (rule-catalog-only first, then validator if approved), requiring separate planning document.
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
