# Phase H.14 / Phase I.13 — Controlled Promotion Readiness Review Checkpoint

**Review Date:** 2026-06-08  
**Review Commit:** `fcb1d4c` — `Docs: Record Phase H.13 implementation review checkpoint`  
**H.13 Implementation Baseline:** `a520eb2`  
**H.13 Stable Baseline:** `084ce64`  
**Functional Baseline:** `d808cb8`  
**Current Regression Gate:** 33 suites — **33/33 PASS**  
**Scope:** Read-only review. No files modified. No severity changed. No commits.

---

## 1. Review Verdict Summary

| Rule | Recommendation |
|---|---|
| `CCI-ROUTE-010` | **NOT READY — NEEDS MORE EVIDENCE** |
| `CCI-ROUTE-011` | **READY FOR WARNING PILOT** (with conditions) |
| Error promotion for either rule | **NOT RECOMMENDED** |

---

## 2. What Was Reviewed

### Sources Inspected

1. `docs/checkpoints/phase_h13_implementation_review_checkpoint.md`
2. `docs/checkpoints/phase_h13_feature_flag_config_checkpoint.md`
3. `docs/checkpoints/phase_h12_fourth_catalog_pilot_search_checkpoint.md`
4. `docs/checkpoints/phase_h11_from_line_evidence_review_checkpoint.md`
5. `docs/checkpoints/phase_h10_from_line_evidence_checkpoint.md`
6. `docs/checkpoints/phase_h9_from_line_validator_checkpoint.md`
7. `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md`
8. `docs/planning/correction_memory_and_rule_promotion_plan.md`
9. `config/cci_enforcement_config.json`
10. `src/cci_routing_validate.py`
11. `src/cci_severity_mapper.py`
12. `tools/run_phase_h13_config_regression.py`

### Review Scope

- **No files modified.**
- **No severity changed.**
- **No commits made during review.**
- **No validator logic altered.**
- **No config altered.**

---

## 3. Regression Results Verified

| Runner | Result |
|---|---|
| `run_phase_h13_config_regression.py` | **PASS — 26/26 checks** |
| `run_phase_h9_from_line_validator_regression.py` | PASS — 18/18 checks |
| `run_phase_h10_from_line_evidence_regression.py` | PASS — 39/39 checks |
| `run_phase_h6_routing_office_code_evidence_regression.py` | PASS — 15/15 checks |
| `run_phase_h8_third_rule_catalog_regression.py` | PASS — 16/16 checks |
| `run_phase_h4_routing_office_code_validator_regression.py` | PASS — 18/18 checks |
| C7–C10 layout regressions (explicit Miniconda Python) | PASS |
| **Full 33-suite gate** | **33/33 PASS** |

**Note:** A looped `execute_code` run using generic `sys.executable` reported 29/33 with C7–C10 non-zero exits. When re-run directly via terminal with explicit `C:\Users\drryl\pinokio\bin\miniconda\python.exe`, all four passed. The loop failure is an environment/subprocess artifact, not a code defect.

---

## 4. CCI-ROUTE-010 — Office Code Prefix Rule

| Criterion | Assessment |
|---|---|
| Current default severity | **advisory** |
| Catalog severity ceiling | **error** |
| Source provenance | **Strong** — SECNAV M-5216.5, Ch 7, para 7-2.7a, To Line, General. Exact quote. |
| Validator maturity | **Mature** — parenthetical and comma-delimited forms, Code prefix logic, length guard. |
| Evidence coverage | **Synthetic-only** — 20 negative + 10 positive fixtures (H.6). No real-world patterns. |
| Regression coverage | **Good** — H.4 (18), H.6 (15), H.13 (temp error/warning config). |
| False-positive risk | **Moderate** — real-world addressee formats may produce unexpected token boundaries. |
| Warning-level pilot safety | **Marginal** — parsing complexity creates non-trivial FP risk. |
| Error-level readiness | **Premature** |
| Additional evidence required | **Yes** — real-world Navy To/Via lines with known correct/incorrect formatting. |
| 30-day burn-in required | **Yes** (minimum) |
| Config-controlled promotion | **Yes** |
| Immediate rollback by config reset | **Yes** |
| Docs/tests/config clarification needed | **Yes** — copy_to scope must be documented as in-scope or permanently out-of-scope. |

**Conclusion:** Keep advisory indefinitely until real-world evidence is collected. Do not promote to warning without dedicated false-positive review.

---

## 5. CCI-ROUTE-011 — From Line Required Rule

| Criterion | Assessment |
|---|---|
| Current default severity | **advisory** |
| Catalog severity ceiling | **error** |
| Source provenance | **Strong** — SECNAV M-5216.5, Ch 7, Section 6, `"From:"` Line, subparagraph a. General (PDF page 50). |
| Validator maturity | **Mature** — doc_type filtering, `window_envelope` suppression, null/empty/whitespace detection. |
| Evidence coverage | **Synthetic-only** — 20 negative + 10 positive fixtures (H.10), plus H.9 edge fixtures. |
| Regression coverage | **Good** — H.9 (18), H.10 (39), H.13 (temp error config). |
| False-positive risk | **Low** — binary present/absent check. Only FP path is window-envelope letter without `window_envelope: true` (data-quality, not logic error). |
| Warning-level pilot safety | **High** — simpler than ROUTE-010, narrow scope, handled exception. |
| Error-level readiness | **Premature** — should complete warning burn-in first. |
| Additional evidence required | **Recommended but not blocking** — real-world Navy standard letters would strengthen confidence. |
| 30-day burn-in required | **Yes** |
| Config-controlled promotion | **Yes** |
| Immediate rollback by config reset | **Yes** |
| Docs/tests/config clarification needed | **Yes** — `window_envelope` field usage should be documented in payload schema or intake docs. |

**Conclusion:** Approved for a controlled, time-bounded warning-level promotion pilot via config change only, with mandatory burn-in and immediate rollback readiness.

---

## 6. Blockers

| # | Blocker | Affected Rule(s) |
|---|---|---|
| 1 | No real-world evidence — all fixtures synthetic. Parsing complexity creates unquantified FP risk for ROUTE-010. | ROUTE-010 |
| 2 | No real-world evidence for ROUTE-011. Risk is lower; acceptable for warning pilot but blocking for error. | ROUTE-011 |
| 3 | No 30-day burn-in completed at any severity above advisory. | Both |

---

## 7. Non-Blocking Recommendations

1. **Select CCI-ROUTE-011 as the first warning pilot** if the project proceeds with promotion. Lower complexity, lower false-positive risk.
2. **Add real-world Navy/Marine Corps fixtures** for both rules before any error-level promotion or before considering ROUTE-010 for warning.
3. **Document `window_envelope` usage** in payload schema / intake documentation.
4. **Explicitly document copy_to scope** for ROUTE-010 (permanently out-of-scope vs future in-scope).
5. **Implement any warning pilot as config-only** — change `effective_severity` in `config/cci_enforcement_config.json`, observe, then decide.

---

## 8. Recommended Next Phase

**Phase H.15 / Phase I.14 — Controlled Warning Pilot for CCI-ROUTE-011**

If approved, the next phase should:

1. Create a planning document for a time-bounded warning pilot.
2. Change `CCI-ROUTE-011` `effective_severity` to `"warning"` in a staging or local config.
3. Run the full 33-suite regression gate after config change.
4. Verify that `overall_pass` correctly transitions to `False` when ROUTE-011 is triggered.
5. Conduct 30-day observation / synthetic batch testing.
6. Require an explicit review checkpoint before any error-level promotion.
7. Keep `CCI-ROUTE-010` advisory indefinitely until real-world evidence is collected.

**Alternative:** If ROUTE-011 warning pilot is not approved, keep both rules advisory and shift effort to real-world evidence collection.

---

## 9. Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No validator changes | **PRESERVED** |
| No catalog changes | **PRESERVED** |
| No renderer/layout changes | **PRESERVED** |
| No prompt-contract changes | **PRESERVED** |
| No Phase F/G command-layer changes | **PRESERVED** |
| No severity promotion occurred | **PRESERVED** |
| No config altered | **PRESERVED** |
| No approved/pending/session logs committed | **PRESERVED** |
| No real data committed | **PRESERVED** |

---

## 10. Open Questions / Next Steps

1. Approve Phase H.15 warning pilot plan?
2. If approved, approve changing `CCI-ROUTE-011` `effective_severity` from `advisory` to `warning`?
3. If approved, define the staging environment or local config override for the pilot.
4. Collect real-world Navy standard-letter payloads for future hardening.
5. Collect real-world Navy To/Via line patterns for ROUTE-010 future reconsideration.

---

*End of checkpoint.*
