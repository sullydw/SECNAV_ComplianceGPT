# Phase H.3 / Phase I.2 — Second Rule-Catalog-Only Pilot Checkpoint

**Date:** 2026-06-04  
**Implementation Commit:** `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`  
**Baseline Commit:** `609821e` — `CCI: Add subject acronym advisory validator (Phase H.2)`  
**Regression Suites at Completion:** 27 (26 existing + 1 new Phase H.3 targeted runner)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Status:** COMPLETE

---

## What Was Implemented

Phase H.3 adds a **second rule-catalog-only** approved-rule pilot, this time in the routing domain rather than the subject domain.

### Rule Source

- **Catalog entry:** `CCI-ROUTE-010`
- **Rule text:** `If the office code is composed of only numbers, add the word "Code" before the numbers. Do not add the word "Code" before an office code that starts with a letter (e.g., "N" or "SUP").`
- **Source:** SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General
- **Source file:** `references/SECNAV_M-5216.5_CH-1.txt`, line 1763
- **Approved record:** `agr_20260604_7b5d44a2`
- **Source candidate:** `cand_20260604_a0f49e2e`
- **Implementation target:** `rule_catalog`
- **Field path/domain:** `routing.office_code`
- **Severity:** `error`
- **Validator:** `cci_routing_validate.py` (named only; no validator code changed)

### Catalog Entry

Appended one provenance-tracked rule object to `rules_v6/CCI/cci_ch2_routing_rules.json`:

- `rule_id`: `CCI-ROUTE-010`
- `title`: Office Code Prefix Rule
- `source`: `SECNAV M-5216.5`
- `source_location`: `Chapter 7, paragraph 7-2.7a, To Line, General`
- `source_quote`: exact quote from line 1763
- `field_path`: `routing.office_code`
- `applies_to`: To and Via lines / routing addresses
- `severity`: `error`
- `enforcement`: deterministic / catalog-only
- `added_by_implementation_id`: `agr_20260604_7b5d44a2`
- All existing provenance fields from earlier routing rules preserved

Catalog now has 10 routing rules (was 9). Object schema with `"rules"` array preserved.

---

## Files Changed

### Modified

- `rules_v6/CCI/cci_ch2_routing_rules.json` — appended `CCI-ROUTE-010` rule object inside existing `"rules"` array.

### Added

- `tools/run_phase_h3_second_rule_catalog_regression.py` — 15-check targeted regression runner.

---

## What Was NOT Changed

- `src/cci_routing_validate.py` — untouched (no validator enforcement added).
- `src/pdf_v6_render.py` — no renderer changes.
- `src/context_resolver.py` — no prompt-contract changes.
- `src/correction_commands.py`, `src/correction_nl_commands.py` — no command-layer changes.
- `rules_v6/CCI/cci_ch7_subject_rules.json` — no subject catalog changes.
- Approved/pending logs — not committed; remain local/gitignored.
- No automatic enforcement from approved logs.
- No AI-only implementation.
- No background automation.

---

## Regression Results

### Phase H.3 Targeted Runner

```
tools/run_phase_h3_second_rule_catalog_regression.py
15/15 checks passed — PASS
```

Checks covered:
1. Routing catalog JSON loads successfully.
2. Routing catalog has object schema with `"rules"` array.
3. Rule `CCI-ROUTE-010` exists exactly once.
4. Rule has source `SECNAV M-5216.5`.
5. Rule has precise source location: Chapter 7, paragraph 7-2.7a.
6. Rule source quote contains both required clauses.
7. Rule has field/domain for `routing.office_code`.
8. Rule has implementation ID `agr_20260604_7b5d44a2`.
9. Rule target is `rule_catalog`.
10. No validator files changed for H.3.
11. No renderer/layout files changed for H.3.
12. No prompt-contract files changed for H.3.
13. No Phase F/G command-layer files changed for H.3.
14. Approved/pending logs are not tracked/staged.
15. Existing H.2 targeted runner still passes (H.2 artifacts remain present).

### Full Suite Gate (27 suites)

All 27 regression suites passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`:

- Phase H.3 targeted runner
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

## Approved Record Status

- Approved record `agr_20260604_7b5d44a2` was claimed by implementer `phase_h3_implementer`.
- `plan_implementation()` recorded source verification summary and implementation plan summary.
- `mark_implemented()` succeeded after commit `46edcbd`.
- Status changed: `implementation_planned` -> `implemented`.
- Implementation commit `46edcbd` recorded in approved record metadata.
- Approved/pending logs remain local-only and gitignored; not committed.

---

## Safety Notes for Next Phase

- **Phase H.4 / Phase I.3 is planning-only until approved.**
- Any validator enforcement for `CCI-ROUTE-010` requires a separate planning document, feature-flag assessment, and targeted regression coverage.
- Any expansion of `PROHIBITED_SUBJECT_ACRONYMS` requires provenance, evidence, false-positive assessment, and fixture coverage per token.
- Any promotion of `SUBJ-007` from advisory to warning/error requires feature-flag mechanism and broader fixture testing.
- Any third approved-rule pilot requires a separate planning document before implementation.
- All 27 regression suites must continue to pass.
- No renderer/layout changes without explicit scope and regression protection.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.
