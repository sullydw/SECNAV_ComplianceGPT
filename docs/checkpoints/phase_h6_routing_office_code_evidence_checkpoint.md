# Phase H.6 — Routing Office-Code Evidence Checkpoint

**Phase:** H.6 / Phase I.5  
**Date:** 2026-06-07  
**Implementation Commit:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`  
**Previous Baseline:** `1e990a6` — Phase H.4 routing office-code advisory validator  
**Current Verified Baseline:** `662afbb`  
**Regression Gate:** `29/29` suites PASS

---

## What Was Implemented

Phase H.6 adds evidence fixtures, a targeted regression runner, and a local gitignored corpus for CCI-ROUTE-010 without modifying validator severity or logic.

### Evidence Collection Only

Phase H.6 does **not** promote CCI-ROUTE-010 from advisory to error/warning. It does **not** change `src/cci_routing_validate.py`. It does **not** change the rule catalog, renderer, prompt contracts, or command layer.

Phase H.6 **does** add:
- 20 negative-control fixtures (must NOT trigger CCI-ROUTE-010).
- 10 positive-control fixtures (MUST trigger CCI-ROUTE-010).
- 50 synthetic-realistic To/Via patterns in a local-only corpus.
- A new 15-check targeted regression runner.
- A `.gitignore` rule for `corrections/evidence/`.

### Fixture Coverage

**Negative controls (must NOT trigger):**
- Hull number references (e.g., `USS Nimitz (CVN-68)`)
- Task force designators (e.g., `Task Force 70`)
- MAG/MEU numeric identifiers (e.g., `Marine Air Group 12`)
- Ordinal unit references (e.g., `1st Marine Division`)
- Fiscal year references (e.g., `FY 2026`)
- Status notes in parentheses (e.g., `(Acting)`)
- Semicolon-delimited addressees without numeric codes
- Slash-delimited addressees without numeric codes
- Facility numbers with letters (e.g., `Building N-23`)
- Room numbers with letters (e.g., `Room A-101`)
- Valid `Code` prefix forms that should not trigger
- And 9 additional edge cases

**Positive controls (MUST trigger):**
- Missing-Code numeric comma forms in `to` lines
- Missing-Code numeric parenthetical forms in `to` lines
- Missing-Code numeric comma forms in `via` lines
- Improper-Code letter-starting comma forms
- Improper-Code letter-starting parenthetical forms
- Multi-part comma forms with partial numeric codes
- Multi-part parenthetical forms with partial numeric codes
- Consecutive numeric codes in `to` lines
- Consecutive numeric codes in `via` lines

### Warning Format Verification

The H.6 runner verifies every positive-control fixture warning contains:
- `CCI-ROUTE-010`
- `(advisory):` format (not `[ADVISORY]`)

### Local Corpus

- **Path:** `corrections/evidence/routing_office_code_patterns.jsonl`
- **Content:** 50 synthetic-realistic To/Via patterns for future analysis
- **Status:** gitignored via `.gitignore` (`corrections/evidence/`)
- **Committed:** No — local-only

---

## Files Changed

### Modified
- `.gitignore` — added `corrections/evidence/` ignore rule.
- `tools/run_phase_h4_routing_office_code_validator_regression.py` — added `.gitignore` to allowed changed-files whitelist (Check 17), preventing false failures caused by H.6 `.gitignore` change.

### Added
- `tools/run_phase_h6_routing_office_code_evidence_regression.py` — 15-check targeted runner.
- `examples/routing_h6_negative_01.json` through `examples/routing_h6_negative_20.json`
- `examples/routing_h6_positive_01.json` through `examples/routing_h6_positive_10.json`

### NOT Changed
- `src/cci_routing_validate.py` — untouched.
- `src/pdf_v6_render.py` — untouched.
- `src/context_resolver.py` — untouched.
- `src/correction_commands.py` — untouched.
- `src/correction_nl_commands.py` — untouched.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — untouched.
- `corrections/evidence/routing_office_code_patterns.jsonl` — NOT committed (gitignored).
- Approved/pending/session logs — untouched/uncommitted.
- Runtime prompt contracts — untouched.

---

## Regression Results

### Targeted H.6 Runner
`tools/run_phase_h6_routing_office_code_evidence_regression.py`
- Result: `PASS`
- Checks: `15/15` passed

### Targeted H.4 Runner
`tools/run_phase_h4_routing_office_code_validator_regression.py`
- Result: `PASS`
- Checks: `18/18` passed

### Full 29-Suite Regression Gate
All suites passed using `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

Phase H.6 runner + all 28 pre-existing suites passed.

---

## Safety Boundaries Preserved

- No renderer/layout modifications.
- No runtime prompt-contract modifications.
- No Phase F/G command-layer modifications.
- No rule catalog modifications.
- No validator logic modifications.
- No approved/pending log modifications or commits.
- No real command/user data committed.
- No background automation introduced.
- No automatic enforcement from approved logs.
- CCI-ROUTE-010 remains advisory-only.
- `errors` list remains empty for this rule.
- `copy_to` remains excluded from detection.

---

## Known Limitations / Cautions

1. **Severity not promoted.** Catalog severity is `error`; validator enforcement is advisory only. Phase H.6 did not change this.
2. **Synthetic fixtures only.** No real-world correspondence patterns have been tested beyond the 50 local corpus entries.
3. **Delimiter scope unchanged.** Relies on comma or parenthesis after addressee title. Semicolon/slash delimiters are tested as negative controls.
4. **Local corpus is local-only.** The `corrections/evidence/` directory is gitignored. Future workstations must regenerate or copy the corpus locally.

---

## Recommended Next Phase

**Phase H.7 / Phase I.6 — Evidence Review, Severity-Promotion Planning, or Third Catalog-Pilot Planning** (planning-only until approved).

Phase H.6 evidence collection is complete. The next phase must decide **one** direction:

1. **Review H.6 fixture results and local corpus patterns for CCI-ROUTE-010.**
   - Analyze 30 synthetic fixtures and 50 corpus patterns for coverage gaps.
   - Decide whether additional edge cases need fixtures before severity promotion.

2. **Continue collecting evidence.**
   - Add more negative/positive fixtures or expand corpus.
   - Does not change validator severity.

3. **Design feature flag/config support for future severity promotion.**
   - Create planning document for config-driven severity override.
   - Design only; no implementation unless explicitly approved.

4. **Keep CCI-ROUTE-010 advisory indefinitely.**
   - Do not promote. Maintain existing 29-suite regression.

5. **Plan warning/error promotion after evidence review.**
   - Use H.6 evidence to decide whether to promote from advisory to warning/error.
   - Requires planning document and new regression checks.

6. **Start a third low-risk catalog pilot.**
   - Separate approved record in `rules_v6/CCI/`.
   - Planning document required before implementation.

**Constraint:** Planning document must be created and approved before any code changes. All 29 regression suites must pass before any commit.

---

End of Phase H.6 Routing Office-Code Evidence Checkpoint.
