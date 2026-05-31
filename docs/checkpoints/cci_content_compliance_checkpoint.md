# CCI Content Compliance Checkpoint

## Baseline Commit

- **Commit hash:** `a876fd17da216029ba80820ea0da223acb01f4d4`
- **Tag:** none at HEAD
- **Date:** 2026-05-31
- **Branch:** `main`
- **Status:** clean, up to date with `origin/main`

## Purpose of the CCI Layer

The Correspondence Content Intelligence (CCI) layer is a deterministic and heuristic content-validation system that sits above the layout/render pipeline. It checks that the *textual content* of a correspondence draft complies with SECNAV M-5216.5 rules, independent of whether the PDF layout is correct. CCI validators examine subject lines, references/enclosures, acronyms, dates, military time usage, and personnel identification inside the JSON payload before rendering.

All CCI work is **additive** — no existing C7-C10 layout profiles, validators, renderers, examples, or README files have been modified.

## Implemented CCI Validators

### 1. CCI Subject-Line Validator
- **Source:** Chapter 7, paragraph 7-2.9 and Figure 7-1
- **Validator file:** `src/cci_subject_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch7_subject_rules.json`
- **Regression runner:** `tools/run_cci_subject_regression.py`
- **Example files:**
  - `examples/audit_cci_subject_valid.json`
  - `examples/audit_cci_subject_invalid.json`
  - `examples/audit_cci_subject_warning.json`

**What it checks:**
- Subject content is all caps for letter types that require it (standard, multiple-address, endorsement, joint).
- Subject line has no terminal punctuation (period, question mark, exclamation mark).
- Subject field does not embed a literal `Subj:` label.
- Warns if subject contains acronyms (unless on a narrow approved list).
- Warns if subject is vague or too short (fewer than three meaningful words).

**What it does not check yet:**
- Substantive accuracy of the subject against the body.
- Subject-line compliance for memo types (MFR, from-to, plain-paper, letterhead) — rules are defined but not yet enforced beyond terminal punctuation and embedded-label checks.

---

### 2. CCI Reference/Enclosure Validator
- **Source:** Chapter 7, paragraph 7-3.3 and Figure 7-1
- **Validator file:** `src/cci_ref_encl_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch7_ref_encl_rules.json`
- **Regression runner:** `tools/run_cci_ref_encl_regression.py`
- **Example files:**
  - `examples/audit_cci_ref_encl_valid.json`
  - `examples/audit_cci_ref_encl_invalid_no_citation.json`
  - `examples/audit_cci_ref_encl_invalid_duplicate.json`
  - `examples/audit_cci_ref_encl_invalid_wrong_order.json`
  - `examples/audit_cci_ref_encl_warning_sep_cover.json`

**What it checks:**
- Every listed reference is cited or substantively mentioned in the body.
- Every listed enclosure is substantively mentioned in the body.
- References appear in the order of their first body citation.
- Enclosures appear in the order of their first body mention.
- The same item does not appear as both a reference and an enclosure.
- Non-endorsement reference markers follow lowercase alphabetical sequence `(a), (b), (c)` without skips or duplicates.
- Non-endorsement enclosure markers follow numeric sequence `(1), (2), (3)` without skips or duplicates.
- Warns for "separate cover" or "provided separately" notations.
- Warns for vague reference/enclosure entries with fewer than three meaningful tokens.
- Warns for bare marker citations in the body without substantive explanatory text nearby.

**What it does not check yet:**
- Endorsement-specific continuation of prior reference/enclosure marker sequences — this remains the responsibility of `src/c9_validate.py` (see rule `CCI-REF-NOTE-001`).

---

### 3. CCI Acronym First-Use Validator
- **Source:** Chapter 2, paragraph 2-4.1
- **Validator file:** `src/cci_acronym_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_acronym_rules.json`
- **Regression runner:** `tools/run_cci_acronym_regression.py`
- **Example files:**
  - `examples/audit_cci_acronym_valid.json`
  - `examples/audit_cci_acronym_invalid_undefined.json`
  - `examples/audit_cci_acronym_warning_approved.json`

**What it checks:**
- Every acronym used in the body is spelled out in full the first time, followed by the acronym in parentheses.
- Flags acronyms used before their first parenthetical definition as non-compliant.
- Warns when approved acronyms (SECNAV, DON, USN, USMC, DoD, NATO, SSIC, MCO, OPNAV, NAVMC, CNO, CMC, FOIA, PII, CUI, FOUO) are used without explicit definition — still allowed, but flagged for clarity.
- Warns when an acronym is defined in the body but never used afterward.

**What it does not check yet:**
- Acronyms inside subject lines (handled by the subject-line validator).
- Acronyms inside signatures, copy-to, or distribution lines.
- Context-aware detection of whether an acronym is truly "first use" across multi-document endorsement chains.

---

### 4. CCI Date and Military-Time Validator
- **Source:** Chapter 2, paragraph 2-4.2
- **Validator file:** `src/cci_date_time_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_date_time_rules.json`
- **Regression runner:** `tools/run_cci_date_time_regression.py`
- **Example files:**
  - `examples/audit_cci_date_time_valid.json`
  - `examples/audit_cci_date_time_invalid_date_format.json`
  - `examples/audit_cci_date_time_invalid_military_time.json`
  - `examples/audit_cci_date_time_warning_civilian_date.json`

**What it checks:**
- Military time is written as four digits `0000` through `2359` with no colon.
- Military time values are within valid range (rejects `2400`, `2561`, etc.).
- Standard text date uses `day Month year` with no leading zero on single-digit day (e.g., `5 May 2026`).
- Top-level `date` field matches the standard military text date format.
- Warns for civilian date format (`Month day, year`) detected in body text.
- Warns for abbreviated two-digit year in body text.
- Warns if the top-level date does not clearly match the expected format.

**What it does not check yet:**
- Date consistency across endorsement chains (e.g., endorsement date must be on or after basic letter date).
- Calendar validity (e.g., `31 Feb 2026`) — format and range are checked, but not whether the day exists in the month.
- Time-zone annotations or Zulu-time conversion.

---

### 5. CCI Personnel Identification Validator
- **Source:** Chapter 2, paragraph 2-4.3 and general military correspondence conventions
- **Validator file:** `src/cci_personnel_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_personnel_rules.json`
- **Regression runner:** `tools/run_cci_personnel_regression.py`
- **Example files:**
  - `examples/audit_cci_personnel_valid.json`
  - `examples/audit_cci_personnel_invalid_lastname_allcaps.json`
  - `examples/audit_cci_personnel_warning_sailor_marine.json`

**What it checks:**
- All-caps last name after a known rank/rate/grade prefix is flagged as a hard error (e.g., "Capt JOHN DOE" or "SgtMaj SMITH").
- Lowercase `Sailor`, `Marine`, or `Service Member` usage is warned — these terms must be capitalized when referring to personnel.
- Possible Navy/Marine Corps convention mixing is warned when Navy rank/rate patterns appear alongside Marine grade patterns in the same document.
- SSN pattern (three-dash-two-four format) detected in body text is flagged as a privacy warning.
- EDIPI / DoD ID pattern near a 10-digit number is flagged as a privacy warning.
- Missing or unknown military component context (Navy vs Marine Corps) is warned when the validator cannot determine which rank/grade system applies.

**What it does not check yet:**
- Full Navy rank/rate database correctness — the validator uses a representative subset, not the complete BUPERS catalog.
- Full Marine Corps grade/MOS completeness — only common grades are recognized.
- Personnel identification inside `From`, `To`, `Via`, or signature blocks — these are header fields, not body text.
- Subject-line or signature last-name casing — handled by other validators.
- Required presence of EDIPI / DoD ID — the validator only warns when one is found, not when one is missing.
- Full privacy/PII policy enforcement — SSN and EDIPI patterns are detected, but other PII (addresses, phone numbers, family names) is not yet scanned.

---

### 6. CCI Point-of-Contact (POC) Validator
- **Source:** Chapter 2, point-of-contact expectations
- **Validator file:** `src/cci_poc_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_poc_rules.json`
- **Regression runner:** `tools/run_cci_poc_regression.py`
- **Example files:**
  - `examples/audit_cci_poc_valid.json`
  - `examples/audit_cci_poc_invalid_missing_poc.json`
  - `examples/audit_cci_poc_warning_incomplete_poc.json`

**What it checks:**
- Body text scanned for action/response/request/inquiry/follow-up expectation keywords (e.g., reply, respond, inquiry, action required, follow up, coordinate, submit, review, endorse, contact).
- Warns when action keywords are detected but no top-level POC field (`point_of_contact`, `poc`, `contact`, `pointOfContact`) and no contact markers appear in body text.
- Warns when a POC field is present but appears incomplete (missing telephone number or e-mail address).
- Warns when body text suggests follow-up but contains no telephone or e-mail markers.

**What it does not check yet:**
- Does not inspect rendered PDF layout or signature blocks for POC.
- Does not inspect From/To/Via lines for POC data.
- Does not enforce strict phone/e-mail format validation.
- Does not require POC on every letter type (only when expectation keywords appear).

### 7. CCI Routing / Via / Copy-to Intelligence Validator
- **Source:** Chapter 2 routing/copy-to conventions and Chapter 7/8 Via/multiple-address context
- **Validator file:** `src/cci_routing_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_routing_rules.json`
- **Regression runner:** `tools/run_cci_routing_regression.py`
- **Example files:**
  - `examples/audit_cci_routing_valid.json`
  - `examples/audit_cci_routing_warning_via_unnumbered.json`
  - `examples/audit_cci_routing_warning_copyto_excess.json`
  - `examples/audit_cci_routing_warning_need_to_know.json`

**What it checks:**
- Warns when multiple Via addressees exist but are not numbered with `(1)`, `(2)`, etc.
- Warns when Via numbering does not start at `(1)` or is not consecutive.
- Warns when a single Via addressee is numbered even though a single Via line normally should not be.
- Warns when Via text contains vague routing phrases (e.g., "through appropriate channels") instead of specific addressees.
- Warns when Copy-to list exceeds 6 entries; flags for need-to-know review.
- Warns when Copy-to entries are vague or overly broad (e.g., "All Hands", "Distribution", "Interested Parties").
- Warns when the same addressee appears as both an action addressee (To or Via) and a Copy-to recipient.
- Warns when `distribution_only` mode is used with 4 or fewer entries (unusual; consider To-line format).
- Warns when `to_plus_distribution` mode appears to lack a group title in To or individual members in Distribution.

**What it does not check yet:**
- Does not validate C8 structural correctness (mode, list emptiness) — `src/c8_validate.py` owns that.
- Does not validate C9 endorsement-specific copy_to completeness (originator, prior endorsers) — `src/c9_validate.py` owns that.
- Does not perform real chain-of-command validation or verify actual routing order.
- Does not inspect rendered PDF layout or physical addressing block positions.
- v1 is warnings-only; no hard errors are returned.

---

## Regression Commands

```bash
# CCI regressions
python tools/run_cci_subject_regression.py
python tools/run_cci_ref_encl_regression.py
python tools/run_cci_acronym_regression.py
python tools/run_cci_date_time_regression.py
python tools/run_cci_personnel_regression.py
python tools/run_cci_poc_regression.py
python tools/run_cci_routing_regression.py

# C7-C10 layout/render regressions
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
python tools/run_c9_regression.py
python tools/run_c10_regression.py
```

## Regression Results (at checkpoint)

| Regression | Result |
|---|---|
| CCI Subject | PASS |
| CCI Ref/Encl | PASS |
| CCI Acronym | PASS |
| CCI Date/Time | PASS |
| CCI Personnel | PASS |
| CCI POC | PASS |
| CCI Routing | PASS |
| C7 Phase 1 | PASS |
| C8 | PASS |
| C9 | PASS |
| C10 | PASS |

All eleven regressions passed on the checkpoint commit.

## CI / GitHub Actions Coverage

The full regression suite (seven CCI + context schema + consolidated audit + C7-C10) is now protected by GitHub Actions.

- **Workflow file:** `.github/workflows/regression.yml`
- **Job name:** `compliance-regression`
- **Timeout:** `15 minutes`
- **Trigger:** `push`, `pull_request`
- **CI baseline commit:** `a876fd17da216029ba80820ea0da223acb01f4d4`
- **GitHub Actions run:** Run #18 completed successfully
- **Status:** GitHub Actions verified PASS (API-confirmed `completed` / `success`)

**CI step order:**
1. CCI subject regression
2. CCI ref/encl regression
3. CCI acronym regression
4. CCI date/time regression
5. CCI personnel regression
6. CCI POC regression
7. CCI routing regression
8. Context schema regression
9. CCI consolidated audit regression
10. C7 Phase 1 regression
11. C8 regression
12. C9 regression
13. C10 regression

Future CCI validators should be added to the workflow before the C7-C10 steps, keeping the fast pure-Python checks first and the slower PDF-based checks last.

## Baseline Integrity Note

The C7-C10 layout and render baseline remains fully intact. Every CCI validator was added as a new file; no existing renderer, validator, layout profile, example, or regression tool was edited. The CCI layer is strictly additive.

## Foundation Layer: CCI Context Schema

A canonical context schema and resolver have been added to support future CCI validators and AI drafting workflows.

- **Schema file:** `rules_v6/CCI/cci_context_schema.json`
- **Resolver source:** `src/context_resolver.py`
- **Public API:** `resolve_context(payload, user_answers=None)` -> `(context, warnings)`
- **Regression runner:** `tools/run_context_schema_regression.py`
- **Example fixtures:**
  - `examples/audit_context_full.json` — fully explicit context
  - `examples/audit_context_minimal.json` — minimal payload, multiple unknowns
  - `examples/audit_context_inferred.json` — mixed Navy/Marine body, automatic inference

**What it provides:**
- Normalized `document.doc_type`, `component.service`, `audience.primary_audience`
- Routing counts and `distribution_mode` normalization
- Privacy/security keyword detection (SSN/EDIPI/FOUO/CUI/classified)
- Response context from body keywords (reply_expected, action_required, deadline_required, POC_required)
- Correction memory metadata placeholder (active_profile, session_corrections_applied, pending_conflicts)
- Non-blocking warnings for all inferred fields

**What it does not do (by design in Phase 1):**
- No intake questioning UI
- No validator_runner.py orchestrator
- No SSIC resolution
- No correction memory behavior
- No AI drafting integration
- Does not modify existing CCI validators, C7-C10 validators, renderer, layout profiles, or examples

**Integration instruction:**
Future CCI validators can call `from context_resolver import resolve_context` and use the returned context object to scope rules by doc_type and component/service. Phase 2 will add validator_runner.py and intake orchestration.

## Regression Results (at checkpoint)

| Regression | Result |
|---|---|
| CCI Subject | PASS |
| CCI Ref/Encl | PASS |
| CCI Acronym | PASS |
| CCI Date/Time | PASS |
| CCI Personnel | PASS |
| CCI POC | PASS |
| CCI Routing | PASS |
| Context Schema | PASS |
| C7 Phase 1 | PASS |
| C8 | PASS |
| C9 | PASS |
| C10 | PASS |

All twelve regressions (seven CCI + Context Schema + C7-C10) passed on the checkpoint commit.

## CCI Consolidated Validator Runner (Verified)

A centralized validator runner has been added to execute all seven CCI validators in a single pass, include resolved context, and produce a consolidated audit report.

- **Runner source:** `src/validator_runner.py`
- **Public API:** `run_cci_audit(payload, user_answers=None)` -> `dict`
- **Schema version:** `CCI_AUDIT_V1`
- **CLI command:** `python src/validator_runner.py <payload.json>`
- **CLI JSON mode:** `python src/validator_runner.py --json <payload.json>`
- **Regression runner:** `tools/run_cci_audit_regression.py`
- **Example fixtures:**
  - `examples/audit_cci_combined_valid.json` — clean payload, expected overall PASS
  - `examples/audit_cci_combined_warning.json` — warnings only, expected overall PASS (exit 0)
  - `examples/audit_cci_combined_invalid.json` — hard errors from ≥3 validators, expected overall FAIL (exit 1)

**What it does:**
- Calls `resolve_context(payload)` first and stores the resolved context object.
- Runs all seven CCI validators in a deterministic order (subject → ref_encl → acronyms → date_time → personnel → poc → routing).
- Collects errors and warnings verbatim from each validator, preserving original rule IDs.
- Returns a structured `CCI_AUDIT_V1` dict with `context`, `context_warnings`, `validators`, and `summary`.
- CLI prints a human-readable report by default; `--json` emits raw audit JSON.
- Exit 0 when `overall_pass` is true (no hard errors); exit 1 when `total_errors > 0`.
- Warnings alone never cause a nonzero exit in v1.

**What it does not do:**
- Does not render PDFs.
- Does not run C7-C10 layout validators.
- Does not deduplicate or rewrite validator messages in v1.
- Does not include strict mode in v1.
- Does not modify existing validators.

**Integration instruction:**
Future AI drafting and intake workflows should call `run_cci_audit(payload)` as the single entry point for all CCI content validation. The returned `CCI_AUDIT_V1` object provides rule IDs, context, and pass/fail status without requiring per-validator imports.

> **Note:** This commit (`a876fd1`) represents the stable baseline before intake orchestration. All 13 regressions (7 CCI + context schema + consolidated audit + C7-C10) have been verified locally and via GitHub Actions Run #18.

## Regression Results (post-runner)

| Regression | Result |
|---|---|
| CCI Subject | PASS |
| CCI Ref/Encl | PASS |
| CCI Acronym | PASS |
| CCI Date/Time | PASS |
| CCI Personnel | PASS |
| CCI POC | PASS |
| CCI Routing | PASS |
| Context Schema | PASS |
| CCI Consolidated Audit | PASS |
| C7 Phase 1 | PASS |
| C8 | PASS |
| C9 | PASS |
| C10 | PASS |

All thirteen regressions passed after adding the consolidated validator runner.

## Known Limitations

- `rule_reuse.py` and `correction_reuse.py` are not yet integrated into the CCI layer.
- Future context fields (activity_source, via_required, chain_of_command) rely on planned intake orchestration and are not inferred beyond keyword heuristics.
- Privacy/security detection is keyword-based only and may produce false positives for redacted or placeholder text.

## Recommended Next CCI Areas

These remain proposed for future CCI work, in no particular order:

1. Privacy / security / PII warning layer — enhance keyword detection with false-positive suppression and integration into context resolver.

---

>*Checkpoint updated after commit a876fd1 — consolidated validator runner CI baseline verified.*

---

## Phase 1: Intake Orchestrator Foundation

An intake orchestration layer has been added to transform user intent into a structured draft payload, ask only for missing information, normalize answers, resolve context, run the consolidated CCI audit, and prepare a validated payload for future rendering without touching the renderer, validators, examples, layout profiles, README, or GitHub Actions in v1.

- **Source:** `src/intake_orchestrator.py`
- **Public API:**
  - `IntakeOrchestrator(payload, user_answers)` — constructor
  - `get_status()` -> `dict` — resolved context, missing fields, blocking status, audit summary
  - `next_questions(limit)` -> `list[dict]` — prioritized missing-field questions
  - `apply_answers(answers)` -> `None` — merge new answers into internal state
  - `build_payload()` -> `dict` — merge payload + user_answers without overriding explicit values
  - `run_audit()` -> `dict` — convenience wrapper for `run_cci_audit`
- **Schema version:** `CCI_INTAKE_V1`
- **CLI command:** `python src/intake_orchestrator.py <payload.json> [answers.json]`
- **Field policy file:** `rules_v6/CCI/cci_intake_field_policy.json`
- **Question definitions:** `rules_v6/CCI/cci_intake_questions.json`
- **Regression runner:** `tools/run_intake_regression.py`
- **Example fixtures:**
  - `examples/audit_intake_standard_letter.json` — partial standard letter missing subj
  - `examples/audit_intake_mfr.json` — partial MFR missing title/signer_name
  - `examples/audit_intake_endorsement.json` — partial endorsement missing basic_letter_id/endorsement_ordinal
  - `examples/audit_intake_joint.json` — partial joint letter missing joint_heading/commands
  - `examples/audit_intake_user_answers.json` — example dot-notation and nested user answers

**What it does:**
- Loads deterministic field policy and question definitions from JSON files.
- Supports flat dot-notation answer keys (`component.service`) and normalizes them to nested dictionaries.
- Payload explicit values take priority over user_answers when both exist.
- Calls `resolve_context` and `run_cci_audit` from existing modules.
- Prioritizes questions as required -> recommended -> optional.
- Filters questions by doc_type and component.service.
- Skips questions for fields already present in payload or user_answers.
- Surfaces `correction_memory` from resolved context as a reserved future field.

**Current v1 limitations:**
- No natural-language parsing.
- No renderer calls. PDF generation is a future downstream step.
- No correction apply/capture/reuse behavior.
- No SSIC suggestion.
- In-memory only; no persistent sessions, SQLite, or filesystem state.
- Purely additive; does not modify existing validators, renderers, layout profiles, examples, README, or GitHub Actions.

**Integration instruction:**
Future intake UIs or AI drafting layers should instantiate `IntakeOrchestrator` with a partial payload, call `get_status()` to understand gaps, present `next_questions()` to the user, and call `apply_answers()` iteratively until `blocking` is false. Only then should the downstream system call the renderer.

## Regression Results (post-intake)

| Regression | Result |
|---|---|
| CCI Subject | PASS |
| CCI Ref/Encl | PASS |
| CCI Acronym | PASS |
| CCI Date/Time | PASS |
| CCI Personnel | PASS |
| CCI POC | PASS |
| CCI Routing | PASS |
| Context Schema | PASS |
| CCI Consolidated Audit | PASS |
| Intake Orchestrator | PASS |
| C7 Phase 1 | PASS |
| C8 | PASS |
| C9 | PASS |
| C10 | PASS |

All fourteen regressions (seven CCI + context schema + consolidated audit + intake orchestration + C7-C10) passed locally after adding the intake orchestration foundation.

## Known Limitations

- `rule_reuse.py` and `correction_reuse.py` are not yet integrated into the CCI layer.
- Future context fields (activity_source, via_required, chain_of_command) rely on planned intake orchestration and are not inferred beyond keyword heuristics.
- Privacy/security detection is keyword-based only and may produce false positives for redacted or placeholder text.
- Intake orchestrator v1 is deterministic JSON-driven only; no natural-language understanding or AI-assisted question generation.

## Recommended Next CCI Areas

These remain proposed for future CCI work, in no particular order:

1. Privacy / security / PII warning layer — enhance keyword detection with false-positive suppression and integration into context resolver.

2. Intake orchestrator Phase 2 — natural-language intent parsing, paragraph-by-paragraph drafting, persistent sessions/correction memory.

---

>*Checkpoint updated after intake orchestration foundation — Phase 1 complete.*
