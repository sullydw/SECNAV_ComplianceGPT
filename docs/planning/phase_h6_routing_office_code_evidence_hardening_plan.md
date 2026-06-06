# Phase H.6 / Phase I.5 — Routing Office-Code Evidence Collection and Regression Hardening Plan

**Date:** 2026-06-06  
**Latest Docs Checkpoint:** `427e762` — `Docs: Record Phase H.5 severity review checkpoint`  
**Current Functional Baseline:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Previous Planning Baseline:** `ece374b` — Phase H.5 severity review plan approved  
**Current Regression Set:** 28 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until approved  
**Implementation Gate:** 28 suites if extending H.4 runner only; 29 suites if adding a new H.6 targeted runner

---

## 1. Purpose

Phase H.6 collects evidence and hardens regression coverage for `CCI-ROUTE-010` **without** changing its severity.

Phase H.5 decided to keep `CCI-ROUTE-010` advisory-only and deferred severity promotion until evidence is collected. Phase H.6 is that evidence-collection and regression-hardening phase.

**This plan does not authorize severity promotion. It does not authorize config implementation. It plans only fixtures, runner hardening, and safe storage.**

---

## 2. Current Behavior Summary

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

---

## 3. Why Phase H.6 Should Collect Evidence Before Severity Promotion

Phase H.5 kept `CCI-ROUTE-010` advisory-only for these reasons:

1. **False-positive risk is unmeasured.** Current detection relies on comma and parenthesis delimiters. Real-world Navy/Marine Corps routing lines may include command titles with trailing numbers, unit designations, hull numbers, or status notes that are not office codes.
2. **No real-world To/Via corpus exists.** All current coverage is synthetic. Evidence collection is required before any severity promotion.
3. **H.4 runner does not verify `errors`-list emptiness.** Hardening the runner is required to prove advisory-only behavior is preserved.
4. **Negative-control and positive-control fixture sets are not yet created.** They must exist as reproducible test assets before any severity change.

Phase H.6 closes these gaps without changing severity.

---

## 4. Evidence Collection Plan

### 4.1 Negative-Control Fixtures (must NOT trigger)

At least **20** synthetic negative-control fixtures.

These patterns must NOT produce warnings. If the validator flags any, it is a false positive.

| # | Pattern | Category |
|---|---|---|
| 1 | `Commanding Officer, USS NIMITZ (CVN-68)` | Hull number, not office code |
| 2 | `Commanding Officer, Task Force 71` | Command name with number |
| 3 | `Commanding Officer, Marine Aircraft Group 13` | Unit name with number |
| 4 | `Commanding Officer, 1st Marine Division` | Ordinal unit |
| 5 | `Commanding Officer (2025)` | Year in parenthesis |
| 6 | `Commanding Officer (Draft)` | Status note |
| 7 | `Commanding Officer; 123` | Semicolon delimiter — not supported |
| 8 | `Commanding Officer / 123` | Slash delimiter — not supported |
| 9 | `12345 Commander` | Leading number, not office code |
| 10 | `Commanding Officer, BUILDING 123` | Alphanumeric with letter start |
| 11 | `Commanding Officer (Bldg 123)` | Abbreviated building code |
| 12 | `Commanding Officer, PIER 7` | Facility number |
| 13 | `Commanding Officer, ROOM 101` | Room number |
| 14 | `Commanding Officer, DOCK 4` | Dock number |
| 15 | `Commanding Officer, HANGAR B` | Letter-only identifier |
| 16 | `Commanding Officer, BLDG 1234` | Abbreviated building number |
| 17 | `Commanding Officer, SUITE A` | Suite letter |
| 18 | `Commanding Officer, BOX 555` | Post box number |
| 19 | `Commanding Officer, Code 123` | Valid numeric with `Code` |
| 20 | `Commanding Officer, N1` | Valid letter without `Code` |

### 4.2 Positive-Control Fixtures (must trigger)

At least **10** synthetic positive-control fixtures.

These patterns MUST produce warnings. If the validator misses any, it is a false negative.

| # | Pattern | Expected Finding |
|---|---|---|
| 1 | `Commanding Officer, 12345` | Missing `Code` before numeric office code |
| 2 | `Commanding Officer (12345)` | Missing `Code` before numeric office code |
| 3 | `Commanding Officer, Code N1` | Improper `Code` before letter-starting code |
| 4 | `Commanding Officer (Code SUP)` | Improper `Code` before letter-starting code |
| 5 | `Via (1): Commanding Officer, 123` | Missing `Code` in Via line |
| 6 | `Via (1): Commanding Officer, Code N1` | Improper `Code` in Via line |
| 7 | `Commanding Officer, 00932` | Missing `Code` before numeric office code (zero-padded) |
| 8 | `Commanding Officer (00001)` | Missing `Code` before numeric office code (leading zeros) |
| 9 | `Commanding Officer, Code 99999` | Valid — no finding (tests that valid forms still pass) |
| 10 | `Commanding Officer, SUP` | Valid — no finding (tests that valid forms still pass) |

**Note:** Fixtures 9-10 are dual-purpose. They verify the validator does not over-flag valid patterns while the first 8 verify it catches violations.

### 4.3 Real-World or Synthetic-Realistic To/Via Patterns

At least **50** diverse addressee strings for later review.

- These are **not** all expected to trigger.
- They should represent realistic Navy/Marine Corps routing lines.
- They may be synthetic but must be plausible.
- Examples include fleet commanders, unit COs, staff offices, joint commands, and regional commands.
- Store in a separate non-committed review file or local spreadsheet, not in `examples/`.
- Do not commit real command/user data.

---

## 5. Fixture Storage Safety

### Where Fixtures Are Stored

- Negative-control and positive-control fixtures go under `examples/` as JSON files.
- File naming convention: `routing_h6_negative_##.json` and `routing_h6_positive_##.json`.
- Each file is a minimal routing context with `to` or `via` fields.
- No real command/user data.
- No local approved/pending logs.
- No secrets, no PII, no contact data.

### Where Real-World Patterns Are Stored

- Real-world or synthetic-realistic patterns go in a **local-only, gitignored** file.
- Suggested path: `corrections/h6_routing_corpus_review.jsonl` (must be gitignored).
- If a gitignored path does not exist, create the file but do not commit it.
- Contents: addressee string, expected finding (yes/no), source description (e.g., "synthetic — based on NAVADMIN style"), and any notes.

---

## 6. H.4 Runner Hardening

The existing H.4 runner must be updated to verify advisory-only behavior more explicitly.

### Checks to Add

1. **`errors`-list empty check:**
   - When a test case triggers `CCI-ROUTE-010`, verify the returned `errors` list is empty.
   - This proves the rule remains non-blocking.

2. **Advisory findings still in `warnings` only:**
   - Verify all `CCI-ROUTE-010` findings are in `warnings`, not `errors`.

3. **Copy-to still does not trigger:**
   - Add or strengthen the check that `copy_to` with a numeric-only office code produces no advisory.

4. **Warning message format preserved:**
   - Verify the warning string contains `[ADVISORY]`, `CCI-ROUTE-010`, and the SECNAV citation.

### Runner Strategy Tradeoff

| Approach | Pros | Cons | Regression Count |
|---|---|---|---|
| **Extend H.4 runner** | Single runner to maintain; fewer files; simpler gate | H.4 runner becomes larger; mixes original detection checks with hardening checks | **28 suites** |
| **Add new H.6 runner** | Clean separation of concerns; H.4 stays focused on detection; H.6 focused on hardening | Extra file; extra maintenance; gate becomes 29 suites | **29 suites** |

**Recommended approach: Add a new H.6 runner.**

Rationale:
- H.4 runner is already 18 checks and focuses on detection behavior.
- H.6 runner will focus on `errors`-empty verification, copy-to exclusion, and fixture-driven edge-case coverage.
- Clean separation makes future severity promotion easier — H.6 runner becomes the baseline that severity-promotion changes must not break.
- 29 suites is acceptable; the extra ~1s runner overhead is negligible compared to the value of separation.

---

## 7. New H.6 Targeted Runner Design

If approved, create:

`tools/run_phase_h6_routing_office_code_evidence_regression.py`

### Proposed Checks

| # | Check | Rationale |
|---|---|---|
| 1 | `errors` list is empty for every negative-control fixture | Proves advisory-only behavior |
| 2 | `errors` list is empty for every positive-control fixture | Proves advisory-only behavior |
| 3 | `warnings` list contains `CCI-ROUTE-010` for every positive-control fixture | Proves detection still works |
| 4 | `warnings` list does NOT contain `CCI-ROUTE-010` for any negative-control fixture | Proves false-positive control |
| 5 | Copy-to numeric-only office code does NOT trigger | Scope boundary preserved |
| 6 | Copy-to letter-starting office code with `Code` does NOT trigger | Scope boundary preserved |
| 7 | Warning message format includes `[ADVISORY]` | Format contract preserved |
| 8 | Warning message format includes `CCI-ROUTE-010` | Rule ID contract preserved |
| 9 | Warning message format includes `SECNAV M-5216.5` | Citation contract preserved |
| 10 | All 20 negative-control fixtures pass without warnings | Batch negative-control verification |
| 11 | All 10 positive-control fixtures pass with warnings | Batch positive-control verification |
| 12 | `validate_cci_routing` signature remains `tuple[list[str], list[str]]` | API contract preserved |
| 13 | No other `src/cci_*_validate.py` files are modified | Scope boundary preserved |
| 14 | `src/pdf_v6_render.py` is not modified | Renderer boundary preserved |
| 15 | `src/context_resolver.py` is not modified | Prompt-contract boundary preserved |

Total: **15 checks** (or more if batch checks are split).

---

## 8. Full Regression Gate Expectation

### If H.6 runner is added

Full regression set becomes **29 suites**:

1. `tools/run_phase_h6_routing_office_code_evidence_regression.py` — NEW (15 checks)
2. `tools/run_phase_h4_routing_office_code_validator_regression.py` — 18 checks
3. `tools/run_phase_h3_second_rule_catalog_regression.py` — 15 checks
4. `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12 checks
5. `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — 11 checks
6. `tools/run_correction_implementation_regression.py` — 45 checks
7. `tools/run_correction_nl_command_regression.py` — 151 checks
8. `tools/run_correction_command_regression.py` — 45 checks
9. `tools/run_correction_review_regression.py` — 30 checks
10. `tools/run_correction_pending_regression.py` — 33 checks
11. `tools/run_correction_profile_promotion_regression.py` — 33 checks
12. `tools/run_correction_classify_regression.py` — Phase B
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

### If H.4 runner is extended only

Full regression set remains **28 suites**.

---

## 9. Files That May Be Modified in a Future Implementation

| File | Change |
|---|---|
| `src/cci_routing_validate.py` | No changes in Phase H.6. (If future severity promotion occurs, this file would route findings based on config; not in H.6.) |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | Add `errors`-empty checks, copy-to scope checks, and advisory-format checks. |
| `tools/run_phase_h6_routing_office_code_evidence_regression.py` (NEW) | 15-check targeted runner for evidence and hardening. |
| `examples/routing_h6_negative_##.json` (NEW, 20 files) | Negative-control fixtures. |
| `examples/routing_h6_positive_##.json` (NEW, 10 files) | Positive-control fixtures. |
| `tools/run_phase_h3_second_rule_catalog_regression.py` | Update allowed-files filter to permit H.6 runner and fixtures. |
| `tools/run_pilot_subject_acronym_rule_catalog_regression.py` | Update allowed-files filter to permit H.6 runner and fixtures. |

---

## 10. Files That Must NOT Be Modified

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

## 11. What Phase H.6 Must NOT Do

- **No severity promotion.** `CCI-ROUTE-010` must remain advisory-only. No routing of findings to `errors`.
- **No renderer/layout changes.** Severity promotion is a validator semantic change, not a PDF geometry change.
- **No broad routing validator rewrite.** Only add fixtures and runner checks; preserve all existing detection logic.
- **No automatic enforcement from approved logs.** The validator must not read `corrections/approved_rule_promotions.json` to determine severity.
- **No AI-only implementation decisions.** Any future severity promotion requires explicit user approval after evidence review.
- **No prompt-contract runtime changes.** `src/context_resolver.py`, `src/intake_orchestrator.py`, and `src/validator_runner.py` contracts remain unchanged.
- **No Phase F/G command-layer changes.** No new slash commands or NL command mappings for fixture management.
- **No approved/pending logs committed.** `corrections/approved_rule_promotions.json` and `corrections/pending_corrections.jsonl` remain gitignored.
- **No real command/user data committed.** No contact info, no local profiles, no session stores.
- **No background automation.** The validator runs only when explicitly invoked.
- **No feature flag/config implementation.** Design may be referenced from H.5 plan, but no config file is created in H.6.

---

## 12. Rollback Plan

If Phase H.6 causes unexpected failures:

1. Revert the commit that added fixtures or runner changes.
2. The catalog entry `CCI-ROUTE-010` remains unchanged in `rules_v6/CCI/cci_ch2_routing_rules.json`.
3. The Phase H.4 advisory helper `_check_office_code_prefix(...)` remains in `src/cci_routing_validate.py` and continues to emit advisory warnings.
4. Remove the new H.6 runner if it was added.
5. Re-run the 28-suite gate without H.6.
6. All earlier phases (H.5, H.4, H.3, H.2, H.1, H, G, F, E, D, C, B, A) remain intact.

Rollback risk: **very low** — Phase H.6 adds only synthetic fixtures and runner checks. No validator logic changes.

---

## 13. Recommended Decision

| Decision | Recommendation |
|---|---|
| **Evidence collection** | **Yes** — create 20 negative-control and 10 positive-control fixtures now. |
| **Runner hardening** | **Yes** — add explicit `errors`-empty, copy-to exclusion, and advisory-format checks. |
| **Runner strategy** | **Add new H.6 runner** — clean separation from H.4 detection checks. |
| **Real-world corpus** | **Yes** — collect at least 50 synthetic-realistic To/Via patterns in a local-only gitignored file for future review. |
| **Severity promotion** | **No** — deferred to a future phase after evidence review and user approval. |
| **Feature flag/config** | **No implementation** — design remains in H.5 plan only. |
| **Regression coverage** | **29-suite gate** if H.6 runner added; **28-suite gate** if extending H.4 only. |
| **Rollback risk** | **Very low** — no validator logic changes. |

### Recommended Defaults Summary

| Decision | Recommended Default |
|---|---|
| **Evidence action** | Collect 20 negative + 10 positive synthetic fixtures |
| **Runner strategy** | Add new H.6 targeted runner (15 checks) |
| **Runner hardening** | Add `errors`-empty, copy-to scope, and advisory-format checks |
| **Real-world corpus** | 50 synthetic-realistic patterns in local gitignored file |
| **Severity action** | Do NOT promote — advisory-only remains |
| **Feature flag** | No implementation — design stays in H.5 plan |
| **Copy-to scope** | Remain out of scope for `CCI-ROUTE-010` |
| **Regression coverage** | 29-suite gate if H.6 runner added |
| **Rollback risk** | Very low — fixtures and runner checks only |

---

## 14. Open Questions Needing Approval

1. **Should Phase H.6 collect synthetic fixtures now, or defer to a later session?**
   - Default: collect now — 20 negative + 10 positive fixtures.

2. **Should Phase H.6 add a new targeted runner, or extend the H.4 runner?**
   - Default: add new H.6 runner — 15 checks, clean separation.

3. **Should the 50 synthetic-realistic To/Via patterns be created in Phase H.6, or deferred?**
   - Default: create now — store in local gitignored file.

4. **Should the H.4 runner also be extended with `errors`-empty checks, or should all hardening checks live only in the H.6 runner?**
   - Default: extend H.4 runner with `errors`-empty and copy-to checks; H.6 runner handles batch fixture verification. This gives dual coverage without duplicating everything.

5. **Should any negative-control fixture represent a copy-to entry, or should copy-to remain completely unrepresented in fixtures?**
   - Default: include at least 2 copy-to negative-control fixtures to document the scope boundary explicitly.

6. **Should Phase H.6 be approved for any code changes, or remain strictly planning-only?**
   - Default: planning-only; no code changes until a separate implementation session is approved.

7. **If the user later decides to keep `CCI-ROUTE-010` advisory indefinitely, should the fixtures still be collected?**
   - Default: yes — fixtures are valuable regardless of severity; they prove the validator behaves correctly and protect against future regressions.

8. **Should the H.6 runner verify that `CCI-ROUTE-010` warnings contain the exact expected string, or only that they contain the rule ID?**
   - Default: verify exact expected string for positive controls; verify absence of rule ID for negative controls.

---

## 15. Approval Gate

Phase H.6 implementation may proceed only after:

- [ ] This planning document is read and acknowledged by the user.
- [ ] All 8 open questions are answered or accepted with defaults.
- [ ] User explicitly states approval to implement Phase H.6 (if any implementation is desired).
- [ ] A separate implementation session is started with the approved plan as source of truth.

**Default for Phase H.6:** planning-only; no code changes; no severity promotion; evidence collection and runner hardening planned only.

---

End of Phase H.6 / Phase I.5 Routing Office-Code Evidence Collection and Regression Hardening Plan.
