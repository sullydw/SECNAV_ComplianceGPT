# Phase J.12 / Phase K.4 — ROUTE-007 Duplicate Copy-to Regression Runner Checkpoint

**Status:** Implementation complete. Runner created and executed. Full regression gate verified.

**Date:** 2026-06-10
**Author:** Hermes Agent (CCI Compliance Automation)
**Commit:** (to be inserted after commit)

---

## 1. Runner Created

**Filename:** `tools/run_phase_j12_route007_duplicate_copyto_regression.py`

**Purpose:** Dedicated deterministic regression runner for CCI-ROUTE-007 exact duplicate Copy-to detection.

**Approach:**
- Uses existing validator entry point (`src/cci_routing_validate.cci_routing_validate`)
- Inline sanitized synthetic payloads — no external fixture files
- No validator logic changes
- No catalog changes
- No config changes

---

## 2. Checks Implemented

Total: **13 checks**

### Positive Cases (6)
1. Copy-to duplicates To exactly
2. Copy-to duplicates Via exactly
3. Multiple Copy-to entries with one duplicate
4. Multiple Via entries; Copy-to duplicates one Via
5. Duplicate after case/spacing normalization
6. Combined payload preserving ROUTE-010/011 while triggering ROUTE-007

### Negative Cases (5)
7. No duplicate Copy-to
8. Near-duplicate should not trigger
9. Abbreviation should not trigger unless exact match
10. Empty Copy-to list should not trigger
11. Copy-to self-duplicate only; should not trigger ROUTE-007

### Cross-Rule Preservation (2)
12. ROUTE-010 warning behavior unchanged
13. ROUTE-011 warning behavior unchanged

---

## 3. Runner Result

```
CCI-ROUTE-007 REGRESSION RESULT: PASS (13/13 checks)
```

All positive cases emitted `CCI-ROUTE-007`.
All negative cases did not emit `CCI-ROUTE-007`.
Warning text identified Copy-to duplicate and whether it duplicated To or Via.
ROUTE-010 and ROUTE-011 behavior unchanged.

---

## 4. Full Regression Gate Results

| Runner | Result | Checks |
|--------|--------|--------|
| run_phase_j12_route007_duplicate_copyto_regression.py | PASS | 13/13 |
| run_cci_routing_regression.py | PASS | 4/4 fixtures |
| run_phase_h4_routing_office_code_validator_regression.py | PASS | 18/18 |
| run_phase_h6_routing_office_code_evidence_regression.py | PASS | 15/15 |
| run_phase_h9_from_line_validator_regression.py | PASS | 18/18 |
| run_phase_h10_from_line_evidence_regression.py | PASS | 39/39 |
| run_phase_h13_config_regression.py | PASS | 27/27 |
| run_phase_h16_route011_burnin_regression.py | PASS | 96/96 |
| run_phase_h24_route011_sanitized_fixture_regression.py | PASS | 32/32 fixtures + 4/4 sub-runners |
| run_correction_regression.py | PASS | 32/32 |
| run_correction_classify_regression.py | PASS | 41/41 |
| run_correction_pending_regression.py | PASS | 33/33 |
| run_correction_review_regression.py | PASS | 30/30 |
| run_correction_implementation_regression.py | PASS | 45/45 |
| run_correction_session_regression.py | PASS | 30/30 |
| run_correction_profile_promotion_regression.py | PASS | 33/33 |
| run_correction_command_regression.py | PASS | 45/45 |
| run_correction_nl_command_regression.py | PASS | 151/151 |
| run_intake_regression.py | PASS | 44/44 |
| run_profile_regression.py | PASS | 9/9 |
| run_context_schema_regression.py | PASS | 3/3 fixtures |
| run_cci_audit_regression.py | PASS | 3/3 fixtures |
| run_cci_subject_regression.py | PASS | 3/3 fixtures |
| run_cci_ref_encl_regression.py | PASS | 5/5 fixtures |
| run_cci_acronym_regression.py | PASS | 3/3 fixtures |
| run_cci_date_time_regression.py | PASS | 4/4 fixtures |
| run_cci_personnel_regression.py | PASS | 3/3 fixtures |
| run_cci_poc_regression.py | PASS | 3/3 fixtures |
| run_c7_phase1_regression.py | PASS | layout + render |
| run_c8_regression.py | PASS | layout + render |
| run_c9_regression.py | PASS | layout + render |
| run_c10_regression.py | PASS | layout + render |
| run_phase_h2_subject_acronym_validator_regression.py | PASS | 12/12 |
| run_phase_h3_second_rule_catalog_regression.py | PASS | 15/15 |
| run_phase_h8_third_rule_catalog_regression.py | PASS | 16/16 |
| run_pilot_subject_acronym_rule_catalog_regression.py | PASS | (included in suite) |

**Full Gate Result:** PASS — 36/36 runners passed

---

## 5. Configuration Verification

- `CCI-ROUTE-007` = not in allowlist (heuristic/advisory candidate)
- `CCI-ROUTE-010` = warning (unchanged)
- `CCI-ROUTE-011` = warning (unchanged)
- `global_default` = advisory (unchanged)
- Error promotion remains unauthorized

---

## 6. Change Summary

**No config changes** — confirmed.
**No severity changes** — confirmed.
**No allowlist changes** — confirmed.
**No validator changes** — confirmed.
**No catalog changes** — confirmed.
**No renderer changes** — confirmed.
**No prompt/context/intake/UI/command-layer changes** — confirmed.
**No logs or unsanitized material committed** — confirmed.

**Files changed:**
- `tools/run_phase_j12_route007_duplicate_copyto_regression.py` — created (new runner)
- `docs/checkpoints/phase_j12_route007_duplicate_copyto_regression_checkpoint.md` — created (this checkpoint)

---

## 7. Safety Constraints Verified

- [x] Sanitized/synthetic payloads only
- [x] Deterministic execution
- [x] No real data
- [x] No logs committed
- [x] No false positives
- [x] No false negatives
- [x] Clear PASS summary printed
- [x] Nonzero exit on failure
- [x] Existing warning pilots unchanged

---

## 8. Recommended Next Phase

**Phase J.13 / Phase K.5 — ROUTE-007 Regression Evidence Review**

Purpose: Review the 13-check regression evidence to determine whether ROUTE-007 is ready for warning-pilot consideration, or whether additional fixture categories or real-world evidence are needed before promotion.

---

## 9. Notes

- Suite count increased from 35 to 36 with addition of new runner.
- The new runner is independent and does not affect existing runner behavior.
- ROUTE-007 remains advisory/heuristic; no severity promotion authorized in this phase.
- Evidence review must be read-only; no config or allowlist changes without explicit approval.

---

*End of Phase J.12 / Phase K.4 Checkpoint*
