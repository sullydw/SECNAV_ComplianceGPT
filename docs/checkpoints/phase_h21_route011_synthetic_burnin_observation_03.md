# Phase H.21 / Phase I.20 — Synthetic Burn-In Observation Checkpoint #3

**Observation Checkpoint:** 03  
**Date:** 2026-06-09  
**Data Type:** synthetic/sanitized only  
**No real command/user data used**  

**Latest Commit:** `87fb03f` — `Docs: Record H.20 synthetic burn-in observation`  
**H.15 Activation Commit:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**H.17 Day 0 Checkpoint Commit:** `0b4c669`  
**H.18 Template Commit:** `a42d149`  
**H.19 Checkpoint #1 Commit:** `3d6f85b`  
**H.20 Checkpoint #2 Commit:** `87fb03f`  
**Current Functional Baseline:** `87fb03f`  
**Regression Set:** 34 suites  
**Last Verified Gate:** 34/34 PASS  
**Status:** Documentation-only checkpoint. No code changes. No config changes. No real data committed.

---

## 1. Config State Verification

Before recording this observation checkpoint, the following config checks were performed:

| Check | Expected Value | Result |
|---|---|---|
| `CCI-ROUTE-011.effective_severity` | `warning` | PASS |
| `CCI-ROUTE-010.effective_severity` | `advisory` | PASS |
| `global_default` | `advisory` | PASS |
| No error-level promotion exists | yes | PASS |
| Config file tracked in git, no uncommitted changes | yes | PASS |

**Config file path:** `config/cci_enforcement_config.json`  
**Config unchanged since H.15 activation.**

---

## 2. Regression Results

All required regression runners were executed with the explicit Miniconda Python interpreter:

| Priority | Runner | Expected Result | Actual Result |
|---|---|---|---|
| Required | `tools/run_phase_h16_route011_burnin_regression.py` | PASS | PASS (96/96) |
| Required | `tools/run_phase_h13_config_regression.py` | PASS | PASS (27/27) |
| Required | `tools/run_phase_h9_from_line_validator_regression.py` | PASS | PASS (18/18) |
| Required | `tools/run_phase_h10_from_line_evidence_regression.py` | PASS | PASS (39/39) |
| Required | Full 34-suite gate | ALL PASS | 34/34 PASS |

**Full gate summary:**
- `run_pilot_subject_acronym_rule_catalog_regression.py` — PASS
- `run_phase_h2_subject_acronym_validator_regression.py` — PASS
- `run_phase_h3_second_rule_catalog_regression.py` — PASS
- `run_phase_h4_routing_office_code_validator_regression.py` — PASS
- `run_phase_h6_routing_office_code_evidence_regression.py` — PASS
- `run_phase_h8_third_rule_catalog_regression.py` — PASS
- `run_correction_implementation_regression.py` — PASS
- `run_correction_nl_command_regression.py` — PASS
- `run_correction_command_regression.py` — PASS
- `run_correction_review_regression.py` — PASS
- `run_correction_pending_regression.py` — PASS
- `run_correction_profile_promotion_regression.py` — PASS
- `run_correction_classify_regression.py` — PASS
- `run_intake_regression.py` — PASS
- `run_correction_regression.py` — PASS
- `run_correction_session_regression.py` — PASS
- `run_profile_regression.py` — PASS
- `run_cci_audit_regression.py` — PASS
- `run_context_schema_regression.py` — PASS
- `run_cci_subject_regression.py` — PASS
- `run_cci_ref_encl_regression.py` — PASS
- `run_cci_acronym_regression.py` — PASS
- `run_cci_date_time_regression.py` — PASS
- `run_cci_personnel_regression.py` — PASS
- `run_cci_poc_regression.py` — PASS
- `run_cci_routing_regression.py` — PASS
- `run_c7_phase1_regression.py` — PASS
- `run_c8_regression.py` — PASS
- `run_c9_regression.py` — PASS
- `run_c10_regression.py` — PASS
- `run_phase_h13_config_regression.py` — PASS
- `run_phase_h16_route011_burnin_regression.py` — PASS
- `run_phase_h9_from_line_validator_regression.py` — PASS
- `run_phase_h10_from_line_evidence_regression.py` — PASS

**Gate status: GREEN. All 34 suites PASS.**

---

## 3. H.16 Synthetic Batch Results

This checkpoint uses synthetic fixtures from `examples/burnin_h16_route011/` and the H.16 burn-in regression runner. No real operational data was reviewed.

### 3.1 Synthetic Payload Summary

| Metric | Value | Notes |
|---|---|---|
| Total payloads reviewed | 90 (synthetic fixtures) | H.16 burn-in fixture set |
| Expected `CCI-ROUTE-011` triggers | 45 | Missing-from / empty-from / whitespace-from / window-envelope-like-without-tag cases |
| Unexpected triggers (false positives) | 0 | None observed in synthetic batch |
| False negatives | 0 | All expected trigger cases produced warnings |
| Window-envelope tagging observations | 15 | `window_envelope: true` correctly suppressed; `window_envelope: false/absent` correctly warned |

### 3.2 Category Breakdown (Synthetic Fixtures)

| Category | Description | Count | Result |
|---|---|---|---|
| A — Standard letter with valid `from` | `from` is non-empty real string | 20 | No finding — correct |
| B — Standard letter missing `from` | `from` absent/null/empty | 15 | Warning triggered — correct |
| C — Null `from` | `"from": null` | 5 | Warning triggered — correct |
| D — Empty string `from` | `"from": ""` | 5 | Warning triggered — correct |
| E — Whitespace-only `from` | `"from": "   "` or `\t` / `\n` | 5 | Warning triggered — correct |
| F — Non-standard document | memo, endorsement, joint, MFR, etc. | 10 | No finding — correct |
| G — Missing `doc_type` | `doc_type` absent/unknown | 5 | No finding — correct |
| H — Window envelope with tag | `window_envelope: true`, no `from` | 10 | No finding (suppressed) — correct |
| I — Window envelope with tag + `from` | `window_envelope: true`, `from` present | 5 | No finding — correct |
| J — Window-envelope-like without tag | Looks like window envelope but tag absent | 5 | Warning triggered — correct (operator risk documented) |
| K — Realistic synthetic/sanitized | Representative payload | 15 | Varies by case; all matched expectations |

**Total: 90 synthetic payloads. All behaved as expected.**

---

## 4. Comparison to H.19 Checkpoint #1 and H.20 Checkpoint #2

| Dimension | H.19 (#1) | H.20 (#2) | H.21 (#3) | Delta | Assessment |
|---|---|---|---|---|---|
| Total payloads reviewed | 90 | 90 | 90 | 0 | Same fixture set |
| Expected triggers | 45 | 45 | 45 | 0 | Consistent |
| False positives | 0 | 0 | 0 | 0 | Stable |
| False negatives | 0 | 0 | 0 | 0 | Stable |
| Window-envelope observations | 15 | 15 | 15 | 0 | Stable |
| Regression gate | 34/34 PASS | 34/34 PASS | 34/34 PASS | 0 | Stable |
| Config state | warning / advisory | warning / advisory | warning / advisory | 0 | Unchanged |
| Code changes since H.19 | none | none | none | 0 | No drift |

### 4.1 Trend Across All Three Checkpoints

- All synthetic batch metrics are identical across checkpoints #1, #2, and #3.
- No regression drift detected.
- No new behavior introduced.
- No increase in known limitations.

**Assessment: No behavior change, no regression change, no new risk identified across any of the three sequential checkpoints.**

---

## 5. Known Limitations

| Limitation | Impact | Status |
|---|---|---|
| Exotic whitespace (ZWS, BOM, invisible chars) not explicitly caught | Low | Documented. Basic whitespace (` `, `\t`, `\n`) is caught. No false negatives observed with standard fixtures. |
| Window-envelope-like letters without `window_envelope: true` block as expected | Moderate (operator education) | Documented in `docs/guidance/window_envelope_payload_guidance.md`. Operator must tag window-envelope letters manually. |
| No real-world payload variety in any synthetic checkpoint | Low | Expected. This is a synthetic checkpoint series. Real-world observation remains future work. |
| Repeated synthetic checkpoints with static fixture set | Low (diminishing returns) | Three consecutive checkpoints all review the same 90 synthetic payloads. Further synthetic-only checkpoints add no new evidence. |

---

## 6. Decision

### 6.1 Checkpoint Decision

| Option | Selected | Rationale |
|---|---|---|
| Continue warning pilot | **YES** | Zero false positives, zero false negatives, regressions green, synthetic batch behaved as expected. No change from H.19 or H.20. |
| Rollback to advisory | NO | No rollback triggers encountered. |
| Extend observation | NO | Not required at this checkpoint. Next checkpoint should use sanitized realistic examples or pause synthetic-only observation. |
| Pause synthetic-only observation until sanitized realistic examples are available | **RECOMMENDED** | Three consecutive synthetic checkpoints on the same static fixture set provide diminishing returns. Future checkpoints should include realistic sanitized payloads or operator feedback to produce meaningful new evidence. |
| Block future error promotion | NO | No anomalies encountered that would block future promotion review. |

### 6.2 Error Promotion Status

**Future error promotion remains UNAUTHORIZED.**

This checkpoint does not approve, plan, or implement error promotion for `CCI-ROUTE-011`. If future clean observation checkpoints accumulate and explicit user approval is obtained, a separate Phase H.22+ / I.21+ planning document must be created before any promotion work.

---

## 7. Recommendation

- **Continue the `CCI-ROUTE-011` warning pilot.**
- Maintain current config (`warning` for `CCI-ROUTE-011`, `advisory` for `CCI-ROUTE-010`).
- **Consider pausing synthetic-only observation checkpoints.** Three consecutive clean synthetic checkpoints on the same fixture set establish stability. Further synthetic-only checkpoints add minimal new evidence.
- If future checkpoint work is needed, prioritize acquiring sanitized realistic examples over repeating the same synthetic batch.
- No code, config, or catalog changes needed at this time.
- No validator, renderer, or command-layer changes needed.

---

## 8. Rollback Readiness

If a future observation reveals a false positive, false negative, or operator emergency:

1. Edit `config/cci_enforcement_config.json`:
   - Change `"CCI-ROUTE-011".effective_severity` from `"warning"` to `"advisory"`.
2. Run `tools/run_phase_h13_config_regression.py` and `tools/run_phase_h16_route011_burnin_regression.py`.
3. If regressions pass, rollback is complete.
4. Document rollback in a new checkpoint file.

Rollback is **config-only**. No validator, catalog, or renderer changes are required.

---

## 9. Related Documents

| Document | Role |
|---|---|
| `docs/planning/phase_h18_route011_burnin_observation_template.md` | Template used for this checkpoint |
| `docs/checkpoints/phase_h19_route011_synthetic_burnin_observation_01.md` | Checkpoint #1 baseline |
| `docs/checkpoints/phase_h20_route011_synthetic_burnin_observation_02.md` | Checkpoint #2 baseline |
| `docs/checkpoints/phase_h17_route011_day0_burnin_checkpoint.md` | Day 0 baseline |
| `docs/checkpoints/phase_h16_route011_burnin_regression_checkpoint.md` | H.16 burn-in baseline |
| `docs/guidance/window_envelope_payload_guidance.md` | Operator guidance |
| `docs/planning/phase_h15_route011_warning_pilot_plan.md` | H.15 warning pilot plan |
| `docs/planning/phase_h16_route011_warning_burnin_plan.md` | H.16 burn-in plan |
| `config/cci_enforcement_config.json` | Severity config (unchanged) |
| `tools/run_phase_h16_route011_burnin_regression.py` | Burn-in runner |
| `tools/run_phase_h13_config_regression.py` | Config runner |
| `tools/run_phase_h9_from_line_validator_regression.py` | Validator runner |
| `tools/run_phase_h10_from_line_evidence_regression.py` | Evidence runner |

---

## 10. What Was NOT Modified in This Checkpoint

This checkpoint is documentation-only. No code changes occurred:

- `config/cci_enforcement_config.json` — not modified.
- `src/cci_routing_validate.py` — not modified.
- `src/cci_severity_mapper.py` — not modified.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — not modified.
- `src/pdf_v6_render.py` — not modified.
- `src/context_resolver.py` — not modified.
- `src/intake_orchestrator.py` — not modified.
- `src/validator_runner.py` — not modified.
- `src/correction_commands.py` — not modified.
- `src/correction_nl_commands.py` — not modified.
- No fixtures added, removed, or modified.
- No runners added, removed, or modified.
- No approved/pending/session/evidence logs committed.
- No real command/user data committed.

---

End of Phase H.21 / Phase I.20 Synthetic Burn-In Observation Checkpoint #3.
