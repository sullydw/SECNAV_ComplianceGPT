# Phase J.13 / Phase K.5 — ROUTE-007 Regression Evidence Review Checkpoint

**Status:** Read-only evidence review complete.

**Date:** 2026-06-10
**Author:** Hermes Agent (CCI Compliance Automation)
**Review Scope:** `tools/run_phase_j12_route007_duplicate_copyto_regression.py`, `docs/checkpoints/phase_j12_route007_duplicate_copyto_regression_checkpoint.md`, `docs/planning/phase_j11_route007_duplicate_copyto_regression_plan.md`, `docs/planning/phase_j9_route007_duplicate_copyto_candidate_plan.md`, `rules_v6/CCI/cci_ch2_routing_rules.json`, `src/cci_routing_validate.py`, `config/cci_enforcement_config.json`, `docs/PROJECT_STATUS.md`, `docs/planning/correction_memory_and_rule_promotion_plan.md`

---

## 1. Review Criteria Assessment

### 1.1 Does the J.12 runner implement the J.11 plan?

**VERDICT: YES** — with minor implementation deviation.

- J.11 plan specified 13 fixture categories (6 positive, 5 negative, 2 cross-rule preservation).
- J.12 runner implements all 13 categories inline as Python dicts instead of external JSON fixture files.
- The J.11 plan suggested external fixtures in `examples/`; the J.12 runner uses inline payloads. This deviation is acceptable: it improves determinism, reduces file count, and avoids external file I/O dependencies.
- All planned positive and negative scenarios are covered.

### 1.2 Does it use sanitized/synthetic inline payloads only?

**VERDICT: YES**

- All payloads use synthetic organization names ("Chief of Naval Operations", "Commander, Fleet Cyber Command", "Commanding Officer, Example Unit").
- No real command data, personnel names, addresses, or contact information.
- All subject lines prefixed with "TEST FIXTURE ROUTE-007".

### 1.3 Does it use the existing validator entry point without changing validator logic?

**VERDICT: YES**

- Runner imports `validate_cci_routing` from `cci_routing_validate` and calls it directly.
- `src/cci_routing_validate.py` lines 216-235 (`_check_copy_to()`) are unchanged from pre-J.12 state.
- No validator modifications were made in the J.12 commit.

### 1.4 Does it cover the planned positive cases?

**VERDICT: YES**

| J.11 Plan Category | J.12 Check | Status |
|---|---|---|
| Copy-to duplicates To | Check 1 | Covered |
| Copy-to duplicates Via | Check 2 | Covered |
| Multiple Copy-to entries, one duplicate | Check 3 | Covered |
| Normalized duplicate (case/spacing) | Check 5 | Covered |
| To and Via present; Copy-to duplicates Via | Check 4 | Covered |
| Multiple Via entries; Copy-to duplicates one | Check 4 | Covered |

### 1.5 Does it cover the planned negative cases?

**VERDICT: MOSTLY YES** — one minor gap noted.

| J.11 Plan Category | J.12 Check | Status |
|---|---|---|
| No duplicate | Check 7 | Covered |
| Near-duplicate | Check 8 | Covered |
| Abbreviation | Check 9 | Covered |
| Empty Copy-to | Check 10 | Covered |
| Copy-to self-duplicate only | Check 11 | Covered |
| Punctuation difference | — | **Not explicitly tested** |

The punctuation-difference edge case (e.g., trailing period or comma) is not explicitly tested. The validator's `_normalize_for_match()` does not strip punctuation, so "Org Name" and "Org Name." would not match. This behavior is acceptable for the current heuristic scope, but explicit test coverage would strengthen the runner.

### 1.6 Does it cover cross-rule preservation for ROUTE-010 and ROUTE-011?

**VERDICT: YES**

- Check 6 (combined payload) verifies ROUTE-007, ROUTE-010, and ROUTE-011 all trigger simultaneously.
- Check 12 verifies ROUTE-010 behavior is unchanged.
- Check 13 verifies ROUTE-011 behavior is unchanged.
- No cross-rule suppression detected.

### 1.7 Does it fail on false positives and false negatives?

**VERDICT: YES**

- Positive cases: strict assertion on `expect_route007=True` with exact count verification.
- Negative cases: strict assertion on `expect_route007=False`.
- Additional guard: `CCI-ROUTE-007` must never appear in `errors` list.
- Returns `SystemExit(1)` on any failure.

### 1.8 Does it verify CCI-ROUTE-007 warning text enough to identify Copy-to duplication and To/Via role?

**VERDICT: PARTIAL** — gap noted, non-blocking.

- The runner verifies rule ID (`CCI-ROUTE-007`) presence and count.
- The runner defines helper functions `_has_to_duplicate()` and `_has_via_duplicate()` but **does not call them** in the test assertions.
- The validator source code (lines 225-227, 232-234) confirms the warning text includes "duplicates To line" or "duplicates Via line" as appropriate.
- **Recommendation:** Future runner refinement should assert warning text structure explicitly.

### 1.9 Does it avoid config/severity/allowlist changes?

**VERDICT: YES**

- `config/cci_enforcement_config.json` unchanged.
- `_allowlist` still contains only `CCI-ROUTE-010` and `CCI-ROUTE-011`.
- `CCI-ROUTE-007` remains not allowlisted.
- `global_default` remains `advisory`.

### 1.10 Does the checkpoint accurately document runner result, full gate, suite count, and no unauthorized changes?

**VERDICT: YES**

- Runner result: PASS (13/13) — correctly documented.
- Full gate: PASS (36/36) — correctly documented.
- Suite count: 36 (increased from 35) — correctly documented.
- No unauthorized changes — confirmed in sections 5 and 6.

### 1.11 Is the evidence strong enough to proceed to a decision phase about source/catalog refinement or future allowlist planning?

**VERDICT: ADEQUATE for source/catalog refinement planning; PREMATURE for allowlist/warning-pilot activation.**

**Strengths:**
- 13/13 checks PASS with zero false positives and zero false negatives on synthetic fixtures.
- Full 36-suite regression gate PASS.
- Deterministic exact-match behavior confirmed.
- Cross-rule preservation verified.

**Limitations:**
- Only synthetic fixtures tested — no real-world correspondence evidence.
- Source location in catalog is narrative ("Chapter 7 To / Via / Copy-to separation"), not a specific paragraph/figure citation.
- Near-duplicate and abbreviation tests are limited to single examples.
- Warning text structure is not explicitly asserted in the runner.

**Conclusion:** Evidence is sufficient to plan source citation refinement and catalog source_location update. Evidence is NOT sufficient to proceed directly to allowlist addition or warning-pilot activation without first refining the source citation.

### 1.12 Are any fixes required before proceeding?

**VERDICT: NO REQUIRED FIXES.**

**Optional refinements (non-blocking):**
1. Add explicit assertion for warning text structure ("duplicates To line" vs "duplicates Via line") in the runner.
2. Add a punctuation-difference negative test case.
3. Remove or utilize the currently unused `_has_to_duplicate()` and `_has_via_duplicate()` helper functions.

---

## 2. Verdict

**`APPROVE J.13 / K.5 ROUTE-007 REGRESSION EVIDENCE REVIEW`**

**Conditions:**
- Evidence is adequate for proceeding to source/catalog refinement planning.
- Allowlist planning and warning-pilot activation remain premature until source citation is refined.
- Optional runner refinements may be addressed in a future maintenance phase if desired.

---

## 3. Recommended Next Phase

**Phase J.14 / Phase K.6 — ROUTE-007 Source/Catalog Refinement Planning**

**Purpose:** Refine the `source_location` field in `rules_v6/CCI/cci_ch2_routing_rules.json` for `CCI-ROUTE-007` from narrative text to a specific paragraph, figure, or example citation in SECNAV M-5216.5 Chapter 7.

**Scope:**
- Identify exact manual location supporting the "same addressee should not appear as both action and copy" rule.
- Update catalog entry `source_location` and optionally add `source_quote`.
- No severity changes.
- No config changes.
- No allowlist changes.
- Planning-only; separate approval required for any catalog write.

---

## 4. Notes

- No files were modified during this read-only review.
- `docs/BOOTSTRAP.md` and `docs/HERMES_INSTRUCTIONS.md` were not accessed.
- No project skill references modified.
- Working tree remains clean.

---

*End of Phase J.13 / Phase K.5 — ROUTE-007 Regression Evidence Review*
