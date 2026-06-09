# Phase H.16 / Phase I.15 — ROUTE-011 Warning Pilot Burn-In Regression Checkpoint

**Commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**Date:** 2026-06-08

---

## Summary

Phase H.16 burn-in regression implemented and verified. 90 synthetic fixtures and a 96-check runner were added under the active `CCI-ROUTE-011` warning pilot configuration. No validator, catalog, renderer, prompt, or command-layer changes were made. Full 34-suite regression gate passes.

---

## Burn-In Fixture Inventory

| Category | Count | Expected ROUTE-011 | Verdict |
|---|---|---|---|
| Valid standard letters with `from` | 20 | No finding | PASS |
| Missing `from` standard letters | 15 | `errors` has ROUTE-011 | PASS |
| Null/empty/whitespace `from` | 13 | `errors` has ROUTE-011 | PASS |
| Exotic whitespace (ZWS, BOM) | 2 | No finding (known limitation) | PASS |
| Non-standard documents (memo, MFR, endorsement, joint, multiple-address) | 15 | No finding | PASS |
| Window-envelope suppressions | 10 | No finding | PASS |
| Window-envelope-like without tag | 10 | `errors` has ROUTE-011 | PASS |
| Realistic Navy/Marine Corps mixed | 5 | Mixed | PASS |
| **Total** | **90** | — | **All PASS** |

## Regression Results

| Runner | Checks | Result |
|---|---|---|
| `run_phase_h16_route011_burnin_regression.py` | 96 | **PASS** |
| `run_phase_h13_config_regression.py` | 27 | **PASS** |
| `run_phase_h9_from_line_validator_regression.py` | 18 | **PASS** |
| `run_phase_h10_from_line_evidence_regression.py` | 39 | **PASS** |
| Full 34-suite gate | 34 suites | **PASS** |

## Config State at Checkpoint

- `CCI-ROUTE-011.effective_severity` = `warning`
- `CCI-ROUTE-010.effective_severity` = `advisory`
- `global_default` = `advisory`
- `_allowlist` = `["CCI-ROUTE-010", "CCI-ROUTE-011"]`
- No error-level promotion exists for any rule.
- Rollback: immediate by restoring `CCI-ROUTE-011.effective_severity` to `"advisory"`.

## Files Added

- `examples/burnin_h16_route011/burnin_h16_neg_01..20_valid_from.json`
- `examples/burnin_h16_route011/burnin_h16_pos_01..15_missing_from.json`
- `examples/burnin_h16_route011/burnin_h16_pos_01..15_bad_from.json`
- `examples/burnin_h16_route011/burnin_h16_nonstd_01..15.json`
- `examples/burnin_h16_route011/burnin_h16_we_01..10.json`
- `examples/burnin_h16_route011/burnin_h16_welike_01..10_no_tag.json`
- `examples/burnin_h16_route011/burnin_h16_realistic_01..05.json`
- `examples/burnin_h16_route011/gen_fixtures.py`
- `tools/run_phase_h16_route011_burnin_regression.py`

## Files Modified

- `docs/PROJECT_STATUS.md`
- `docs/planning/correction_memory_and_rule_promotion_plan.md`

## Files Not Modified

- `config/cci_enforcement_config.json` (severity unchanged)
- `src/cci_routing_validate.py`
- `src/cci_severity_mapper.py`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `src/pdf_v6_render.py`
- `src/context_resolver.py`
- `src/intake_orchestrator.py`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`

## Known Limitations

- Exotic whitespace characters (zero-width space `\u200B`, BOM `\uFEFF`) are not stripped by `str.strip()` and therefore do not trigger `CCI-ROUTE-011`. This is a known operator/data-quality edge case, not a false negative in normal use.

## Open Questions

1. Should the 30-day burn-in observation period start from this commit or from the H.15 warning pilot activation commit (`18fc9bf`)?
2. Should exotic-whitespace detection be hardened in a future validator patch, or is documentation sufficient?
3. Should a dedicated real-world payload collection phase be scheduled before any error-level promotion discussion?

## Recommended Next Phase

Continue H.16 burn-in observation. After the observation period, possible future phase:
- **H.17 / I.16 — Error Promotion Readiness Review** (requires separate user approval; planning-only until authorized).

---

End of checkpoint.
