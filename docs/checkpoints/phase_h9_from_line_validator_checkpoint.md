# Phase H.9 / Phase I.8 — From-Line Advisory Validator Enforcement Checkpoint

**Commit:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Date:** 2026-06-08  
**Previous Functional Baseline:** `769437d` — Phase H.8 third catalog-pilot implementation  
**Current Functional Baseline:** `6f320af` — Phase H.9 From-line advisory validator enforcement  
**Previous Regression Set:** 30 suites  
**Current Regression Set:** 31 suites (30 existing + 1 new H.9 runner)  
**Full Gate Result:** 31/31 PASS  
**Target Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`

---

## What Phase H.9 Implemented

Phase H.9 added advisory/non-blocking validator enforcement for the existing catalog rule `CCI-ROUTE-011`.

| Attribute | Value |
|---|---|
| Rule ID | `CCI-ROUTE-011` |
| Advisory code | `CCI-ROUTE-011` |
| Rule text | `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.` |
| Source | SECNAV M-5216.5, Chapter 7, Section 6, `"From:" Line`, subparagraph a. General (PDF page 50) |
| Approved record | `agr_20260607_49947aca` |
| Source candidate | `cand_20260607_5dcc97cf` |
| Domain | `routing.from` |
| Catalog severity | `error` (unchanged) |
| Validator enforcement | `advisory` / non-blocking only |
| Implementation target | `src/cci_routing_validate.py` |

---

## Files Changed

### Implementation Files

| File | Change | Notes |
|---|---|---|
| `src/cci_routing_validate.py` | Modified | Added `_check_from_line_required()` helper (~48 lines); wired into `validate_cci_routing()` after office-code prefix checks |
| `tools/run_phase_h9_from_line_validator_regression.py` | Created | 18-check targeted regression runner |
| `examples/routing_from_missing.json` | Created | Synthetic fixture: `DT_STD_LTR`, no `from` field |
| `examples/routing_from_empty.json` | Created | Synthetic fixture: `DT_STD_LTR`, `from: ""` |
| `examples/routing_from_present.json` | Created | Synthetic fixture: `DT_STD_LTR`, `from` present (pass) |
| `examples/routing_from_window_envelope.json` | Created | Synthetic fixture: `DT_STD_LTR`, `window_envelope: true`, no `from` |
| `examples/routing_from_memo_skipped.json` | Created | Synthetic fixture: `DT_MEMO_FROM_TO_PLAIN`, no `from` (must skip) |
| `examples/routing_from_endorsement_skipped.json` | Created | Synthetic fixture: `endorsement`, no `from` (must skip) |
| `examples/routing_from_both_rules.json` | Created | Synthetic fixture: triggers both `CCI-ROUTE-010` and `CCI-ROUTE-011` |
| `examples/routing_from_no_doctype.json` | Created | Synthetic fixture: no `doc_type`, no `from` (must skip) |

### Supporting Runner Updates (to avoid false positives from later phases)

| File | Change | Notes |
|---|---|---|
| `tools/run_phase_h8_third_rule_catalog_regression.py` | Modified | Check 11 baseline comparison changed from `HEAD` to `769437d` |
| `tools/run_phase_h6_routing_office_code_evidence_regression.py` | Modified | Check 14 baseline comparison changed from `HEAD` to `662afbb` |

---

## Behavior Summary

### Advisory Check Logic

```
if doc_type not in (DT_STD_LTR, "standard_letter"):
    skip
if doc_type is missing:
    skip
if window_envelope is true:
    skip
if from is missing, empty, or whitespace-only:
    append advisory to warnings
```

### Advisory Message Format

```
CCI-ROUTE-011 (advisory): Standard letter "From:" line is missing. SECNAV M-5216.5, Ch7, "From:" Line, a. General (page 50). Include "From:" unless the letter will be used with a window envelope.
```

### Key Safety Properties

| Property | Status |
|---|---|
| `errors` list remains empty | **Confirmed** |
| Findings append to `warnings` only | **Confirmed** |
| No third advisory channel created | **Confirmed** |
| `window_envelope: true` suppresses advisory | **Confirmed** |
| Missing `doc_type` skips (no inference) | **Confirmed** |
| Memorandum excluded | **Confirmed** |
| Endorsement excluded | **Confirmed** |
| Joint letter excluded | **Confirmed** |
| Multiple-address letter excluded | **Confirmed** |
| `CCI-ROUTE-010` behavior preserved | **Confirmed** |
| Existing Via / Copy-to / Distribution warnings preserved | **Confirmed** |

---

## Regression Results

### H.9 Targeted Runner

```
PHASE H.9 FROM-LINE ADVISORY VALIDATOR REGRESSION RUNNER
RESULT: 18/18 checks passed
PHASE H.9 REGRESSION RESULT: PASS
```

### H.8 Targeted Runner

```
PHASE H.8 THIRD RULE-CATALOG-ONLY PILOT REGRESSION RUNNER
RESULT: 16/16 checks passed
PHASE H.8 REGRESSION RESULT: PASS
```

### Full 31-Suite Gate

```
TOTAL: 31/31 runners passed
FULL GATE: PASS
```

---

## Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No renderer/layout changes | **Preserved** |
| No prompt-contract changes | **Preserved** |
| No rule catalog changes | **Preserved** — `rules_v6/CCI/cci_ch2_routing_rules.json` untouched |
| No Phase F/G command-layer changes | **Preserved** |
| No approved/pending/session/evidence logs committed | **Preserved** |
| No real command/user data committed | **Preserved** |
| No severity promotion of `CCI-ROUTE-010` | **Preserved** |
| No severity promotion of `CCI-ROUTE-011` | **Preserved** — catalog severity remains `error` |
| No feature flag/config implementation | **Preserved** |
| No background automation | **Preserved** |
| No AI-only implementation decisions | **Preserved** |

---

## Open Items / Notes for Future Work

1. **Catalog severity vs validator severity mismatch:** `CCI-ROUTE-011` catalog severity is `error`, but validator behavior is advisory/non-blocking. This is intentional — the catalog records the manual rule severity; the validator enforces it as advisory until sufficient evidence and config support exist for promotion.

2. **Window-envelope false-positive risk:** If a real window-envelope letter is submitted without `window_envelope: true` in the payload, the validator will emit a non-blocking advisory. This is acceptable because H.9 is advisory-only. Full `window_envelope` payload support is deferred.

3. **Future evidence collection:** Additional negative/positive fixtures for joint letters, multiple-address letters, and real-world Navy/Marine Corps patterns may be added in Phase H.10.

4. **Feature flag/config support:** Remains conceptual only. Must be planned separately before any severity promotion.

5. **Copy-to scope:** Copy-to (`copy_to`) remains out of scope for From-line validation. The rule only checks the `from` field.

6. **Memorandum handling:** Memorandums (From-To and MFR) are explicitly excluded. If a future rule requires From-line checking for memorandums, that must be a separate catalog/validator entry.

---

## Suggested Startup Prompt for Next Session

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, `docs/checkpoints/phase_h9_from_line_validator_checkpoint.md`, and `docs/planning/phase_h9_from_line_validator_enforcement_plan.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs. Run all regressions before committing implementation changes.

---

End of Phase H.9 / Phase I.8 From-Line Advisory Validator Enforcement Checkpoint.
