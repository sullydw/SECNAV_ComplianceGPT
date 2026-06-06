# Phase H.5 / Phase I.4 — Routing Office-Code Severity Review Checkpoint

**Phase:** H.5 / Phase I.4  
**Date:** 2026-06-06  
**Planning Document:** `docs/planning/phase_h5_routing_office_code_severity_review_plan.md`  
**Planning Commits:** `8bf5efa` — `Docs: Add Phase H.5 routing office code severity plan`; `ece374b` — `Docs: Refine Phase H.5 routing office code severity plan`  
**Current Functional Baseline:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Previous Functional Baseline:** `46edcbd` — Phase H.3 second rule-catalog-only pilot  
**Current Regression Set:** 28 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** approved; planning-only — no implementation authorized

---

## What Was Planned

Phase H.5 created a severity review plan for the existing advisory validator rule `CCI-ROUTE-010`.

### Rule Under Review

- **Catalog ID:** `CCI-ROUTE-010`
- **Rule text:** If the office code is composed of only numbers, add the word "Code" before the numbers. Do not add the word "Code" before an office code that starts with a letter (e.g., "N" or "SUP").
- **SECNAV source:** M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General

### Severity Gap Identified

- **Catalog severity:** `error` (set at Phase H.3)
- **Validator severity:** `advisory` (interim, non-blocking since Phase H.4)
- **Gap:** catalog declares the rule as `error`-level; validator intentionally emits it as advisory only
- **Rationale:** avoid breaking existing routing workflows while collecting evidence

### Approved Verdict

**Keep `CCI-ROUTE-010` advisory-only. Do not promote to warning or error in Phase H.5.**

---

## Evidence Required Before Any Future Promotion

Before `CCI-ROUTE-010` can be promoted from advisory to warning or error, the following evidence must be collected in a future phase:

1. **Synthetic negative-control fixture set:** at least 20 negative-control fixtures showing patterns that must NOT trigger. These help detect false positives.
2. **Synthetic positive-control fixture set:** at least 10 positive-control fixtures showing patterns that MUST trigger. These help detect false negatives.
3. **Real-world or realistic To/Via corpus:** at least 50 diverse addressee strings from actual or representative Navy/Marine Corps correspondence, with expected vs actual validator output documented.
4. **Copy-to audit:** evidence that `copy_to` either does or does not need the same rule, with separate citation.
5. **Zero regression failures:** all 28 existing suites plus any new runner must pass.
6. **User approval:** explicit approval after reviewing evidence.

---

## Terminology Standard Established

- **Negative-control fixtures:** patterns that must NOT produce warnings. If the validator flags any of them, it is a false positive.
- **Positive-control fixtures:** patterns that MUST produce warnings. If the validator misses any of them, it is a false negative.

This terminology is used consistently throughout the Phase H.5 plan and must be used in all future evidence-collection work.

---

## Files Changed (Planning Commits Only)

### Modified
- `docs/planning/phase_h5_routing_office_code_severity_review_plan.md` — created in `8bf5efa`, refined in `ece374b`.

### Not Modified (Intentionally)
- `src/cci_routing_validate.py` — no validator changes in Phase H.5.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — catalog severity remains `error`.
- `src/pdf_v6_render.py` — untouched.
- `src/context_resolver.py` — untouched.
- `src/correction_commands.py` — untouched.
- `src/correction_nl_commands.py` — untouched.
- Approved/pending logs — untouched and not committed.
- Runtime prompt contracts — untouched.

---

## Files NOT Changed

- No other `src/cci_*_validate.py` files.
- Layout profiles — untouched.
- `src/validator_runner.py` — untouched.
- `src/intake_orchestrator.py` — untouched.
- No examples added (evidence collection deferred).
- No new regression runner added (H.5 is planning-only).

---

## Regression Results

### Full 28-Suite Regression Gate
All suites passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

Phase H.4 runner + all 27 pre-existing suites passed.

No regression runner was added for Phase H.5 because Phase H.5 is strictly planning-only.

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
- Existing routing validator behavior preserved.

---

## Known Limitations / Cautions

1. **Copy-to not checked.** The SECNAV citation is To Line, General; scope is `to` and `via` only. A separate candidate with its own citation would be needed for `copy_to`.
2. **Catalog vs validator severity mismatch.** The catalog entry `CCI-ROUTE-010` has severity `error`. The validator emits it as advisory only. This is intentional interim behavior. Severity promotion requires future evidence collection and user approval.
3. **Delimiter-dependent detection.** Relies on comma or parenthesis after the addressee title. Unusual formats such as slash or semicolon delimiters are not supported.
4. **Synthetic fixtures only.** All edge-case coverage is synthetic; real-world To/Via patterns from actual correspondence have not been tested.
5. **H.4 runner does not yet verify `errors` list is empty.** This check is deferred to a future regression-hardening phase (e.g., H.6).

---

## Recommended Next Phase

**Phase H.6 / Phase I.5 — Evidence Collection and Regression Hardening, or Third Catalog-Pilot Planning** (planning-only until approved).

Choose one direction:

1. Collect the 20 negative-control and 10 positive-control fixtures for `CCI-ROUTE-010`.
2. Harden the H.4 runner with an explicit `errors`-empty check.
3. Design feature flag/config support for future severity promotion.
4. Keep `CCI-ROUTE-010` advisory indefinitely.
5. Add a third low-risk catalog pilot (rule-catalog-only first).

**Constraint:** Planning document must be created and approved before any code changes. All 28 regression suites must pass before any commit.

---

End of Phase H.5 / Phase I.4 Routing Office-Code Severity Review Checkpoint.
