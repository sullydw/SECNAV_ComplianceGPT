# Phase H.5 / Phase I.4 — Routing Office-Code Severity Review Plan

**Date:** 2026-06-05  
**Latest Docs Checkpoint:** `a0a0247` — `Docs: Record Phase H.4 routing validator checkpoint`  
**Current Functional Baseline:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Previous Functional Baseline:** `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`  
**Current Regression Set:** 28 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until approved  
**Regression Suites if Implemented:** 29 (28 existing + 1 new Phase H.5 targeted runner)

---

## 1. Current Behavior Summary

### Advisory Validator for `CCI-ROUTE-010`

- **Validator file:** `src/cci_routing_validate.py`
- **Helper:** `_check_office_code_prefix(...)` — added in Phase H.4
- **Integration:** called inside `validate_cci_routing(...)` without signature change
- **Return type:** `tuple[list[str], list[str]]` as `(errors, warnings)` — preserved
- **Enforcement level:** advisory/non-blocking only
- **Errors list:** remains empty for this rule
- **Warnings list:** advisory findings appended as formatted strings

### Detection Scope

- Checked on: `routing.to` and `routing.via` addressee strings
- Not checked on: `routing.copy_to` (deferred)
- Not checked: body, subject, references, enclosures, distribution, free text

### Detection Patterns

| Scenario | Current Result |
|---|---|
| `Commanding Officer, 123` (numeric, no `Code`) | Advisory warning — missing `Code` |
| `Commanding Officer (123)` (numeric, no `Code`) | Advisory warning — missing `Code` |
| `Commanding Officer, Code N1` (letter, improper `Code`) | Advisory warning — improper `Code` |
| `Commanding Officer (Code SUP)` (letter, improper `Code`) | Advisory warning — improper `Code` |
| `Commanding Officer, Code 123` | OK — valid numeric with `Code` |
| `Commanding Officer (Code 123)` | OK — valid parenthetic with `Code` |
| `Commanding Officer, N1` | OK — valid letter without `Code` |
| `Commanding Officer (SUP)` | OK — valid parenthetic without `Code` |
| `Commander U.S. Pacific Fleet 123` (no delimiter) | OK — no trigger |
| Normal title without comma or parenthesis | OK — no trigger |

### Catalog Severity vs Validator Severity

- **Catalog severity:** `error` (set at Phase H.3)
- **Validator severity:** `advisory` (interim, non-blocking)
- **Gap:** catalog declares the rule as `error`-level; validator intentionally emits it as advisory only
- **Rationale:** avoid breaking existing routing workflows while collecting evidence

---

## 2. Why Immediate Severity Promotion May Be Risky

### False-Positive Risk

1. **Command titles with trailing numbers:** `Battalion 3`, `Task Force 71`, `Squadron 101` — these are titles, not office codes, but a naive validator could flag them.
2. **Parenthetical clarifications:** `(2025)` for year references in addressee lines, `(Draft)` status notes — could be mistaken for office codes.
3. **Joint letter formats:** `Commanding Officer, Code 123 / Commanding Officer, N1` — multi-addressee lines may split incorrectly.
4. **Non-standard delimiters:** semicolons, slashes, dashes — not covered by current comma/parenthesis detection.
5. **All-numeric command designators that are not office codes:** fleet numbers, hull numbers, aircraft tail numbers appearing in routing.

### False-Negative Risk

1. **Missing `Code` without delimiter:** some office codes may appear inline without comma or parenthesis, e.g., `Commanding Officer Code 123` — current detection misses these.
2. **Multi-word office codes:** `Code 123 N1` or nested codes — not handled.
3. **Copy-to lines:** the same rule may apply to `copy_to` but is not currently checked.

### Blast Radius

- Routing is a **high-frequency** field; every letter has at least one addressee.
- Promoting to `error` would cause the renderer/intake pipeline to reject the payload.
- A single false positive would block letter generation for a common command format.
- No real-world To/Via patterns have been tested yet — all coverage is synthetic.

---

## 3. Evidence Required Before Promotion

Before `CCI-ROUTE-010` can be promoted from advisory to warning or error, the following evidence must be collected:

1. **Synthetic negative-control fixture set:** at least 20 negative-control fixtures showing patterns that must NOT trigger (see Section 4). These help detect false positives.
2. **Synthetic positive-control fixture set:** at least 10 positive-control fixtures showing patterns that MUST trigger (see Section 5). These help detect false negatives.
3. **Real-world or realistic To/Via corpus:** at least 50 diverse addressee strings from actual or representative Navy/Marine Corps correspondence, with expected vs actual validator output documented.
4. **Copy-to audit:** evidence that `copy_to` either does or does not need the same rule, with separate citation.
5. **Zero regression failures:** all 28 existing suites plus the new H.5 runner must pass.
6. **User approval:** explicit approval after reviewing evidence.

---

## 4. Negative-Control Fixtures to Collect

These patterns must NOT produce warnings at any severity level. They are **negative-control fixtures** — if the validator flags any of them, it is a false positive.

| # | Pattern | Why It Is NOT a Violation |
|---|---|---|
| 1 | `Commander, U.S. Pacific Fleet` | Title with geographic name, no office code |
| 2 | `Commanding Officer, USS NIMITZ (CVN-68)` | Hull number, not office code |
| 3 | `Commanding Officer, Task Force 71` | Task force number, not office code |
| 4 | `Commanding Officer, Marine Aircraft Group 13` | Unit designation, not office code |
| 5 | `Commanding Officer, 1st Marine Division` | Ordinal unit, not office code |
| 6 | `Commanding Officer (2025)` | Year in parenthesis, not office code |
| 7 | `Commanding Officer (Draft)` | Status note, not office code |
| 8 | `Commanding Officer; 123` | Semicolon delimiter — not supported, should not trigger |
| 9 | `Commanding Officer / 123` | Slash delimiter — not supported, should not trigger |
| 10 | `Code 123; N1` | Multi-code line with semicolon |
| 11 | `12345 Commander` | Leading number, not office code |
| 12 | `Commanding Officer, BUILDING 123` | Alphanumeric with letter start, no `Code` needed |
| 13 | `Commanding Officer (Bldg 123)` | Abbreviated building code |
| 14 | `Commanding Officer, PIER 7` | Facility number |
| 15 | `Commanding Officer, ROOM 101` | Room number |
| 16 | `Commanding Officer, DOCK 4` | Dock number |
| 17 | `Commanding Officer, HANGAR B` | Letter-only identifier |
| 18 | `Commanding Officer, BLDG 1234` | Abbreviated building number |
| 19 | `Commanding Officer, SUITE A` | Suite letter |
| 20 | `Commanding Officer, BOX 555` | Post box number |

---

## 5. Positive-Control Fixtures to Collect

These patterns MUST produce warnings at the appropriate severity level. They are **positive-control fixtures** — if the validator misses any of them, it is a false negative.

| # | Pattern | Expected Finding |
|---|---|---|
| 1 | `Commanding Officer, 12345` | Missing `Code` before numeric office code |
| 2 | `Commanding Officer (12345)` | Missing `Code` before numeric office code |
| 3 | `Commanding Officer, Code N1` | Improper `Code` before letter-starting office code |
| 4 | `Commanding Officer (Code SUP)` | Improper `Code` before letter-starting office code |
| 5 | `Via (1): Commanding Officer, 123` | Missing `Code` in Via line |
| 6 | `Via (1): Commanding Officer, Code N1` | Improper `Code` in Via line |
| 7 | `Commanding Officer, Code 00932` | Valid — no finding |
| 8 | `Commanding Officer, N1` | Valid — no finding |
| 9 | `Commanding Officer (SUP)` | Valid — no finding |
| 10 | `Commanding Officer, Code 12345` | Valid — no finding |

---

## 6. Whether Copy-To Should Remain Out of Scope

**Recommendation: Keep `copy_to` out of scope for `CCI-ROUTE-010`.**

Rationale:
- The SECNAV source citation is `Chapter 7, paragraph 7-2.7a, To Line, General`.
- The manual text explicitly discusses the To line, not the Copy-To line.
- Copy-To office-code conventions may differ (e.g., abbreviated formats, distribution lists).
- A separate candidate rule with its own provenance citation would be needed for `copy_to`.
- Expanding scope without separate provenance would violate the project's manual-and-figure source standard.

Future work: if a user identifies an explicit SECNAV citation for `copy_to` office-code formatting, that becomes a separate Phase H.x candidate.

---

## 7. Whether Feature Flag/Config Is Required Before Warning/Error Promotion

**Recommendation: Yes. A feature flag or config mechanism is required before promoting `CCI-ROUTE-010` to warning or error.**

Rationale:
- Advisory findings are non-blocking; they do not stop rendering or submission.
- Warning findings could affect downstream tooling or CI pipelines that treat warnings as review triggers.
- Error findings would reject the payload entirely.
- A feature flag allows gradual rollout without code changes — e.g., a config file or environment variable.
- Precedent: no existing feature-flag mechanism exists in the routing validator today.

Proposed minimal mechanism (not to be implemented in Phase H.5):
- Config file: `profiles/severity_overrides.json` or `config/validator_severity.yaml`
- Override per rule ID: `"CCI-ROUTE-010": "advisory"` → `"warning"` → `"error"`
- Default: read catalog severity; override takes precedence.
- No change to catalog severity field; override is runtime only.

---

## 8. Proposed Severity Ladder

```
advisory (current) → warning → error (catalog-declared)
```

| Level | Behavior | User Impact |
|---|---|---|
| `advisory` | Non-blocking warning string appended to `warnings` list | Visible in CCI audit report; does not block rendering |
| `warning` | Blocking or potentially blocking; may trigger review gates | May require explicit override in CI or intake; still in `warnings` list but with stronger semantics |
| `error` | Blocking; payload rejected or renderer refuses to proceed | Must be fixed before letter generation; appended to `errors` list |

**Note:** The existing `validate_cci_routing(...) -> (errors, warnings)` signature must be preserved. Moving a finding from `warnings` to `errors` changes which list it is appended to, not the function signature.

---

## 9. Criteria for Moving from Advisory to Warning

All of the following must be met:

1. [ ] At least 20 negative-control fixtures documented and passing (Section 4). These help detect false positives.
2. [ ] At least 10 positive-control fixtures documented and passing (Section 5). These help detect false negatives.
3. [ ] At least 50 real-world or realistic To/Via patterns tested with zero unexpected findings.
4. [ ] Zero regression failures across all 28 existing suites.
5. [ ] No open issues or user reports of false positives from advisory phase.
6. [ ] Feature flag/config mechanism designed and documented (not necessarily implemented).
7. [ ] User explicitly approves the promotion to warning.

---

## 10. Criteria for Moving from Warning to Error

All of the following must be met:

1. [ ] Warning-level enforcement has been active for at least 2 real-world usage sessions with no false-positive reports.
2. [ ] All synthetic fixture coverage expanded to at least 40 total fixtures (20 negative, 20 positive).
3. [ ] Copy-to scope explicitly decided (either yes with separate citation, or no with documented rationale).
4. [ ] Feature flag/config mechanism is implemented and tested.
5. [ ] Zero regression failures across all suites.
6. [ ] User explicitly approves the promotion to error.
7. [ ] Rollback plan documented and tested.

---

## 11. How to Preserve Existing Routing Validator Behavior

- The signature of `validate_cci_routing(...)` must remain `tuple[list[str], list[str]]`.
- Existing routing checks (ROUTE-001 through ROUTE-009) must not be modified.
- The `_check_office_code_prefix(...)` helper must remain a standalone function with clear docstring.
- If severity is promoted, the helper's return value should be routed to either `errors` or `warnings` based on the severity config, not hardcoded.
- Existing behavior for comma-delimited and parenthetical detection must be preserved.
- Existing false-positive controls (no delimiter = no trigger) must be preserved.

---

## 12. How to Preserve H.1/H.2/H.3/H.4 Regression Protections

- All 28 existing regression suites must continue to pass.
- The Phase H.4 targeted runner (`tools/run_phase_h4_routing_office_code_validator_regression.py`) must not be removed or broken.
- The Phase H.3 targeted runner (`tools/run_phase_h3_second_rule_catalog_regression.py`) must not be removed or broken.
- The Phase H.2 targeted runner (`tools/run_phase_h2_subject_acronym_validator_regression.py`) must not be removed or broken.
- The Phase H.1 targeted runner (`tools/run_pilot_subject_acronym_rule_catalog_regression.py`) must not be removed or broken.
- Catalog files must not be accidentally modified during severity promotion.
- No validator files other than `src/cci_routing_validate.py` should be affected.

---

## 13. Required Targeted Regression Updates if Severity Changes

If `CCI-ROUTE-010` is promoted from advisory to warning or error:

1. **Update the H.4 targeted runner:** checks that currently expect `warnings` list to contain advisory strings must be updated to expect `errors` or modified `warnings` strings.
2. **Add a new H.5 targeted runner:** `tools/run_phase_h5_routing_office_code_severity_regression.py` with checks specifically for:
   - Config-driven severity override loading
   - Advisory mode still works when config says advisory
   - Warning mode works when config says warning
   - Error mode works when config says error
   - Invalid config values fallback to advisory
   - Existing routing validator behavior unchanged under all severity settings
3. **Update full suite gate count:** from 28 to 29 suites.
4. **Verify cross-phase compatibility:** H.1, H.2, H.3 runners still pass.

---

## 14. Full 29-Suite Regression Expectation if New H.5 Runner Added

If Phase H.5 is implemented with a new targeted runner, the full regression set becomes **29 suites**:

1. `tools/run_phase_h5_routing_office_code_severity_regression.py` — NEW (config/severity checks).
2. `tools/run_phase_h4_routing_office_code_validator_regression.py` — 18 checks.
3. `tools/run_phase_h3_second_rule_catalog_regression.py` — 15 checks.
4. `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12 checks.
5. `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — 11 checks.
6. `tools/run_correction_implementation_regression.py` — 45 checks.
7. `tools/run_correction_nl_command_regression.py` — 151 checks.
8. `tools/run_correction_command_regression.py` — 45 checks.
9. `tools/run_correction_review_regression.py` — 30 checks.
10. `tools/run_correction_pending_regression.py` — 33 checks.
11. `tools/run_correction_profile_promotion_regression.py` — 33 checks.
12. `tools/run_correction_classify_regression.py` — Phase B.
13. `tools/run_intake_regression.py`
14. `tools/run_correction_regression.py`
15. `tools/run_correction_session_regression.py`
16. `tools/run_profile_regression.py`
17. `tools/run_cci_audit_regression.py`
18. `tools/run_context_schema_regression.py`
19. `tools/run_cci_subject_regression.py`
20. `tools/run_cci_ref_encl_regression.py`
21. `tools/run_cci_acronym_regression.py`
22. `tools/run_cci_date_time_regression.py`
23. `tools/run_cci_personnel_regression.py`
24. `tools/run_cci_poc_regression.py`
25. `tools/run_cci_routing_regression.py`
26. `tools/run_c7_phase1_regression.py`
27. `tools/run_c8_regression.py`
28. `tools/run_c9_regression.py`
29. `tools/run_c10_regression.py`

All 29 suites must pass before any commit.

---

## 15. Files That May Be Modified in a Future Implementation

| File | Change |
|---|---|
| `src/cci_routing_validate.py` | Add severity-config lookup; route `_check_office_code_prefix` findings to `errors` or `warnings` based on config. |
| `config/validator_severity.yaml` (NEW) or `profiles/severity_overrides.json` (NEW) | Runtime severity override config file. |
| `tools/run_phase_h5_routing_office_code_severity_regression.py` (NEW) | Targeted runner for severity config and promotion behavior. |

---

## 16. Files That Must NOT Be Modified

| File | Why |
|---|---|
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract runtime changes. |
| `src/correction_commands.py` | No Phase F command-layer changes. |
| `src/correction_nl_commands.py` | No Phase G command-layer changes. |
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Catalog severity remains `error`; do not modify. |
| `rules_v6/CCI/cci_ch7_subject_rules.json` | No subject catalog changes. |
| `src/cci_subject_validate.py` | No subject validator changes. |
| `src/cci_acronym_validate.py` | No acronym validator changes. |
| `corrections/approved_rule_promotions.json` | Remains local/gitignored; do not commit. |
| `corrections/pending_corrections.jsonl` | Remains local/gitignored; do not commit. |
| Any real command/user profile | Do not commit contact data or local profiles. |

---

## 17. What Phase H.5 Must NOT Do

- **No immediate severity promotion without evidence.** Advisory must remain until all criteria in Sections 9 and 10 are met.
- **No renderer/layout changes.** Severity promotion is a validator semantic change, not a PDF geometry change.
- **No broad routing validator rewrite.** Only modify severity routing logic; preserve all existing checks.
- **No automatic enforcement from approved logs.** The validator must not read `corrections/approved_rule_promotions.json` to determine severity.
- **No AI-only implementation decisions.** Severity promotion requires explicit user approval after evidence review.
- **No prompt-contract runtime changes.** `src/context_resolver.py`, `src/intake_orchestrator.py`, and `src/validator_runner.py` contracts remain unchanged.
- **No Phase F/G command-layer changes.** No new slash commands or NL command mappings for severity management.
- **No approved/pending logs committed.** `corrections/approved_rule_promotions.json` and `corrections/pending_corrections.jsonl` remain gitignored.
- **No real command/user data committed.** No contact info, no local profiles, no session stores.
- **No background automation.** The validator runs only when explicitly invoked.

---

## 18. Rollback Plan

If Phase H.5 causes unexpected failures:

1. Revert the commit that added severity promotion or config changes.
2. The catalog entry `CCI-ROUTE-010` remains unchanged in `rules_v6/CCI/cci_ch2_routing_rules.json`.
3. The Phase H.4 advisory helper `_check_office_code_prefix(...)` remains in `src/cci_routing_validate.py` and continues to emit advisory warnings.
4. Remove the targeted regression runner `tools/run_phase_h5_routing_office_code_severity_regression.py` if it exists.
5. Re-run the 28-suite gate without H.5.
6. All earlier phases (H.4, H.3, H.2, H.1, H, G, F, E, D, C, B, A) remain intact.

Rollback risk: **low** — severity promotion is a routing of existing findings between lists, not new detection logic. The advisory helper remains as the safe default.

---

## 19. Recommended Decision

| Decision | Recommendation |
|---|---|
| **Keep advisory, refine advisory, or plan promotion** | **Keep advisory** — continue collecting evidence. Do not promote to warning or error in Phase H.5. |
| **Feature flag** | **Design but do not implement** — document the config mechanism design, implement only when warning/error promotion is approved. |
| **Evidence-gathering plan** | Add 20 synthetic false-positive fixtures and 10 false-negative fixtures in Phase H.5. Test against real-world or realistic To/Via patterns before any severity change. |
| **Regression coverage** | Maintain 28-suite gate. If H.5 runner is added for config design testing, expect 29-suite gate. |

### Recommended Defaults Summary

| Decision | Recommended Default |
|---|---|
| **Severity action** | Keep advisory; refine advisory coverage; do NOT promote |
| **Feature flag** | Design documented; implementation deferred to future phase |
| **Copy-to scope** | Remain out of scope for `CCI-ROUTE-010` |
| **Evidence collection** | 20 negative + 10 positive synthetic fixtures added to `examples/` |
| **Real-world testing** | Required before any warning/error promotion; not in Phase H.5 |
| **Regression coverage** | 28-suite gate preserved; 29-suite if H.5 runner added for config design |
| **Rollback risk** | Low — advisory helper remains the safe default |

---

## 20. Open Questions Needing Approval

1. **Should Phase H.5 collect synthetic evidence, or should evidence collection be deferred to a separate session?**
   - Default: collect synthetic evidence now; real-world testing deferred.

2. **Should the feature flag design be created in Phase H.5, or deferred?**
   - Default: design documented in Phase H.5; implementation deferred.

3. **Should `copy_to` be explicitly excluded in planning documentation, or left as an open future candidate?**
   - Default: explicitly exclude; document rationale.

4. **Should the severity ladder be applied to other advisory rules (e.g., `CCI-CH7-SUBJ-007`) at the same time?**
   - Default: no — each rule requires its own evidence review and approval.

5. **Should the H.4 runner be updated to verify advisory-only behavior (i.e., verify `errors` list remains empty)?**
   - Default: yes — but **deferred to a future evidence-collection / regression-hardening phase** (e.g., Phase H.5 implementation or a subsequent H.6 phase), not during this planning-only document. This is a future regression-hardening task that must be completed before any warning/error promotion. Do not imply it is already implemented.

6. **Should Phase H.5 be approved to implement anything, or remain strictly planning-only?**
   - Default: strictly planning-only; no code changes.

7. **Should the project maintain `advisory` as a permanent tier, or is it strictly a staging tier before `warning`/`error`?**
   - Default: permanent tier allowed — some rules may stay advisory indefinitely if false-positive risk is unacceptable.

8. **Who approves severity promotion — the user only, or a documented reviewer workflow?**
   - Default: user-only approval; no automated promotion.

---

## 21. Approval Gate

Phase H.5 implementation may proceed only after:

- [ ] This planning document is read and acknowledged by the user.
- [ ] All 8 open questions are answered or accepted with defaults.
- [ ] User explicitly states approval to implement Phase H.5 (if any implementation is desired).
- [ ] A separate implementation session is started with the approved plan as source of truth.

**Default for Phase H.5:** planning-only; no code changes; no severity promotion; evidence collection and feature-flag design in documentation only.

---

End of Phase H.5 / Phase I.4 Routing Office-Code Severity Review Plan.
