# Phase H.2 / Phase I.1 — Subject-Line Acronym Validator Advisory Enforcement Checkpoint

**Date:** 2026-06-04  
**Implementation Commit:** `609821e` — `CCI: Add subject acronym advisory validator (Phase H.2)`  
**Baseline Commit:** `6298dab` — `CCI: Add public mark implemented wrapper`  
**Regression Suites at Completion:** 26 (25 existing + 1 new Phase H.2 targeted runner)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Status:** COMPLETE

---

## What Was Implemented

Phase H.2 adds **advisory/non-blocking** validator enforcement for the already-cataloged rule `CCI-CH7-SUBJ-006`.

### Rule Source

- **Catalog entry:** `CCI-CH7-SUBJ-006`
- **Rule text:** `In correspondence, do not use acronyms in the subject line.`
- **Source:** SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General
- **Approved record:** `agr_20260604_b69c92d9` (Phase H.1)
- **Implementation target:** `src/cci_subject_validate.py`

### New Advisory Code

- **Code:** `CCI-CH7-SUBJ-007`
- **Level:** Advisory (non-blocking; validator exits 0)
- **Message format:** `CCI-CH7-SUBJ-007: prohibited subject-line acronym detected: <token> — SECNAV M-5216.5 Ch7 para 9`

### Curated Prohibited Subject-Acronym List

```python
PROHIBITED_SUBJECT_ACRONYMS = frozenset([
    "POC",  # Phase H.1 pilot correction; common Point of Contact abbreviation
    "UIC",  # Unit Identification Code; prohibited in subject lines per Ch7 para 9
    "OIC",  # Officer in Charge; prohibited in subject lines per Ch7 para 9
])
```

- **Minimum token length:** 3 characters (matches `_ACRONYM_RE`).
- **Scanning behavior:** Token-by-token exact membership check on all-caps subjects only.
- **Generic regex suppression:** The generic `\b[A-Z]{2,}\b` regex remains suppressed for all-caps subjects to prevent false positives on normal words like `UPDATE`, `POLICY`, `MEETING`.
- **Overlap with approved/common lists:** None. `APPROVED_ACRONYMS` and `_COMMON_UPPER_WORDS` remain unchanged.

---

## Files Changed

### Modified

- `src/cci_subject_validate.py` — added `PROHIBITED_SUBJECT_ACRONYMS`, `_check_prohibited_subject_acronyms()`, and `SUBJ-007` advisory emission.
- `docs/planning/phase_h2_subject_acronym_validator_enforcement_plan.md` — two minor wording cleanups (stale `SUBJECT_APPROVED_ACRONYMS` reference, Open Question 6 updated).
- `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — updated to allow `cci_subject_validate.py` modifications while still blocking unexpected validator changes.

### Added

- `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12-check targeted regression runner.
- `examples/audit_cci_subject_poc.json` — positive trigger fixture (POC).
- `examples/audit_cci_subject_uic.json` — positive trigger fixture (UIC).
- `examples/audit_cci_subject_oic.json` — positive trigger fixture (OIC).
- `examples/audit_cci_subject_no_acronym.json` — negative control (spelled out).
- `examples/audit_cci_subject_policy_update.json` — negative control (normal all-caps words).
- `examples/audit_cci_subject_secnav.json` — negative control (approved acronym).
- `examples/audit_cci_subject_mixed_poc.json` — mixed-case fixture for SUBJ-004 regression.

---

## What Was NOT Changed

- `src/cci_acronym_validate.py` — untouched (body-only scope).
- `src/pdf_v6_render.py` — no renderer changes.
- `src/context_resolver.py` — no prompt-contract changes.
- `src/correction_commands.py`, `src/correction_nl_commands.py` — no command-layer changes.
- `rules_v6/CCI/cci_ch7_subject_rules.json` — no catalog text changes (rule already existed from Phase H.1).
- Approved/pending logs — not committed; remain local/gitignored.
- No automatic enforcement from approved logs.
- No AI-only implementation.
- No background automation.

---

## Regression Results

### Phase H.2 Targeted Runner

```
tools/run_phase_h2_subject_acronym_validator_regression.py
12/12 checks passed — PASS
```

Checks covered:
1. POC triggers SUBJ-007 (all-caps subject).
2. UIC triggers SUBJ-007 (all-caps subject).
3. OIC triggers SUBJ-007 (all-caps subject).
4. Full spelled-out expansions do not trigger SUBJ-007.
5. Normal all-caps words do not trigger SUBJ-007.
6. Valid subject still passes.
7. Existing SUBJ-004 unchanged on mixed-case fixture.
8. Body acronym validator untouched.
9. No renderer/layout changes.
10. No logs tracked by git.
11. Pilot catalog runner still passes.
12. No approved/pending logs committed.

### Full Suite Gate (26 suites)

All 26 regression suites passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`:

- Phase H.2 targeted runner
- Pilot catalog runner
- Intake regression
- Profile regression
- CCI audit regression
- Context schema regression
- CCI subject regression
- CCI ref/encl regression
- CCI acronym regression
- CCI date/time regression
- CCI personnel regression
- CCI POC regression
- CCI routing regression
- C7 Phase 1 regression
- C8 regression
- C9 regression
- C10 regression
- Correction regression
- Correction session regression
- Correction classification regression
- Correction profile promotion regression
- Correction review regression
- Correction pending regression
- Correction implementation regression
- Correction NL command regression
- Phase F command integration regression

---

## Safety Notes for Next Phase

- **Phase H.3 / Phase I.2 is planning-only until approved.**
- Any expansion of `PROHIBITED_SUBJECT_ACRONYMS` requires provenance, evidence, false-positive assessment, and fixture coverage per token.
- Any promotion of `SUBJ-007` from advisory to warning/error requires feature-flag mechanism and broader fixture testing.
- Any second approved-rule pilot requires a separate planning document before implementation.
- All 26 regression suites must continue to pass.
- No renderer/layout changes without explicit scope and regression protection.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.