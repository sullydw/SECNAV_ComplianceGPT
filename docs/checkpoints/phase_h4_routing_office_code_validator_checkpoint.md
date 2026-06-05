# Phase H.4 — Routing Office-Code Advisory Validator Checkpoint

**Phase:** H.4 / Phase I.3  
**Date:** 2026-06-05  
**Implementation Commit:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Previous Baseline:** `46edcbd` — Phase H.3 second rule-catalog-only pilot  
**Current Verified Baseline:** `1e990a6`  
**Regression Gate:** `28/28` suites PASS  

---

## What Was Implemented

Phase H.4 adds narrow advisory/non-blocking validator behavior for the existing catalog rule `CCI-ROUTE-010`.

### Advisory Rule

- **Catalog ID:** `CCI-ROUTE-010`
- **Rule text:** If the office code is composed of only numbers, add the word "Code" before the numbers. Do not add the word "Code" before an office code that starts with a letter (e.g., "N" or "SUP").
- **SECNAV source:** M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General  
  Source quote:  
  > `If the office code is composed of only numbers, add the word "Code" before the numbers. Do not add the word "Code" before an office code that starts with a letter (e.g., "N" or "SUP").`

### Validator Changes

- **Target file:** `src/cci_routing_validate.py`
- **New helper:** `_check_office_code_prefix(...)`
- **Integration:** Called inside `validate_cci_routing(...)` without changing its public signature.
- **Return type preserved:** `tuple[list[str], list[str]]` (errors, warnings)
- **Enforcement level:** Advisory-only; findings appended to existing `warnings` list.
- **Errors list:** Remains empty for this advisory implementation.
- **No third advisory channel added.**

### Scope

- Checked on: `to` and `via` routing entries.
- Not checked on: `copy_to` in Phase H.4.
- Not checked: body, subject, references, enclosures, distribution, free text.

### Detection Patterns

| Scenario | Expected Result |
|---|---|
| `Commanding Officer, 123` | Trigger — missing `Code` before numeric code |
| `Commanding Officer (123)` | Trigger — missing `Code` before numeric code |
| `Commanding Officer, Code N1` | Trigger — improper `Code` before letter-starting code |
| `Commanding Officer (Code SUP)` | Trigger — improper `Code` before letter-starting code |
| `Commanding Officer, Code 123` | OK — valid numeric code with `Code` |
| `Commanding Officer (Code 123)` | OK — valid parenthetic numeric code with `Code` |
| `Commanding Officer, N1` | OK — valid letter-starting code without `Code` |
| `Commanding Officer (SUP)` | OK — valid parenthetic letter-starting code without `Code` |
| `Commander U.S. Pacific Fleet 123` | OK — no comma/parenthesis delimiter |
| Normal title without delimiter | OK — no trigger |

### Warning Format

Every advisory warning includes:
- Advisory severity label (`[ADVISORY]`)
- Rule code `CCI-ROUTE-010`
- SECNAV citation
- Suggested correction

Example:
```
Adv: [ADVISORY] CCI-ROUTE-010 Office line "Commanding Officer, 123" has numeric-only office code '123' but is missing the word "Code" before it. Correction: "Commanding Officer, Code 123". Source: SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General. (non-blocking advisory)
```

---

## Files Changed

### Modified
- `src/cci_routing_validate.py` — added `_check_office_code_prefix` helper.
- `tools/run_phase_h3_second_rule_catalog_regression.py` — updated allowed-files filter for H.4.
- `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — updated allowed-files filter for H.4.
- `docs/planning/phase_h4_routing_office_code_validator_enforcement_plan.md` — updated recommended-defaults summary from stale `16-check` to `18-check`.

### Added
- `tools/run_phase_h4_routing_office_code_validator_regression.py` — 18-check targeted runner.
- `examples/routing_numeric_no_code_comma.json`
- `examples/routing_numeric_no_code_paren.json`
- `examples/routing_numeric_with_code_comma.json`
- `examples/routing_numeric_with_code_paren.json`
- `examples/routing_letter_with_code_comma.json`
- `examples/routing_letter_with_code_paren.json`
- `examples/routing_letter_no_code_comma.json`
- `examples/routing_letter_no_code_comma_sup.json`
- `examples/routing_via_numeric_comma.json`
- `examples/routing_no_delimiter.json`
- `examples/routing_existing_behavior.json`
- `examples/routing_copy_to_numeric_comma.json`
- `examples/routing_numeric_long_comma.json`

---

## Files NOT Changed

- No other `src/cci_*_validate.py` files.
- `src/pdf_v6_render.py` — untouched.
- Layout profiles — untouched.
- `src/context_resolver.py` — untouched.
- `src/correction_commands.py` — untouched.
- `src/correction_nl_commands.py` — untouched.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — untouched (catalog already had `CCI-ROUTE-010`).
- Approved/pending logs — untouched.
- Runtime prompt contracts — untouched.

---

## Regression Results

### Targeted H.4 Runner
`tools/run_phase_h4_routing_office_code_validator_regression.py`
- Result: `PASS`
- Checks: `18/18` passed

### Full 28-Suite Regression Gate
All suites passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

Phase H.4 runner + all 27 pre-existing suites passed.

---

## Safety Boundaries Preserved

- No renderer/layout modifications.
- No runtime prompt-contract modifications.
- No Phase F/G command-layer modifications.
- No rule catalog modifications (catalog already contained `CCI-ROUTE-010` from Phase H.3).
- No approved/pending log modifications or commits.
- No real command/user data committed.
- No background automation introduced.
- No automatic enforcement from approved logs.
- Existing routing validator behavior preserved except for the new advisory helper.

---

## Known Limitations / Cautions

1. **Copy-to not checked.** The SECNAV citation is To Line, General; scope is `to` and `via` only. A separate candidate with its own citation would be needed for `copy_to`.
2. **Catalog vs validator severity mismatch.** The catalog entry `CCI-ROUTE-010` has severity `error`. The validator emits it as advisory only. This is intentional interim behavior. Severity promotion requires future Phase H.5 planning.
3. **Delimiter-dependent detection.** Relies on comma or parenthesis after the addressee title. Unusual formats such as slash or semicolon delimiters are not supported.
4. **Synthetic fixtures only.** All edge-case coverage is synthetic; real-world To/Via patterns from actual correspondence have not been tested.

---

## Recommended Next Phase

**Phase H.5 / Phase I.4 — Validator Severity Review or Third Catalog-Pilot Planning** (planning-only until approved).

Choose one direction:

1. Collect more real/synthetic evidence before increasing `CCI-ROUTE-010` severity.
2. Keep `CCI-ROUTE-010` advisory only.
3. Plan validator severity promotion with feature flag/config.
4. Further refine office-code detection (additional delimiters, edge cases).
5. Add a third low-risk catalog pilot (rule-catalog-only first).
6. Improve rule-catalog governance/provenance tooling.

**Constraint:** Planning document must be created and approved before any code changes. All 28 regression suites must pass before any commit.

---

End of Phase H.4 Routing Office-Code Advisory Validator Checkpoint.