# Phase H.15 / Phase I.14 — ROUTE-011 Warning Pilot Checkpoint

**Date:** 2026-06-08  
**Commit:** `[TBD]` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**Previous commit:** `575c2aa` — `Docs: Record Phase H.15 plan review checkpoint`  
**Plan document:** `docs/planning/phase_h15_route011_warning_pilot_plan.md`  
**Plan review checkpoint:** `docs/checkpoints/phase_h15_warning_pilot_plan_review_checkpoint.md`

---

## What Changed

### 1. Config-only severity elevation

File: `config/cci_enforcement_config.json`

- `CCI-ROUTE-011.effective_severity` changed from `"advisory"` to `"warning"`.
- `CCI-ROUTE-010.effective_severity` remains `"advisory"`.
- `allow_override_up_to` unchanged for both rules (`"error"`).
- `reason` and `snapshot_id` updated to reflect warning-pilot activation.
- No catalog severity changed.
- No new config keys added.

### 2. H.13 runner updated for dedicated ROUTE-011 warning-config check

File: `tools/run_phase_h13_config_regression.py`

- Check 06 updated to expect `ROUTE-011` default severity = `warning`.
- Check 11b added: default warning config produces `ROUTE-011` in `errors` (blocking).
- Check 14b added: temp warning config produces `ROUTE-011` in `errors` (blocking).
- Check 17 updated: uses synthetic payload with `from` present so `ROUTE-011` does not fire.
- Check 18 updated: uses `routing_from_h10_pos_01_missing_from.json` for temp error config test.
- Check 20 updated: expects `ROUTE-011` in `errors` under default warning config for all H.10 positive fixtures.
- All existing checks preserved; no checks removed.
- Total checks increased from 25 to 27.

### 3. H.9 / H.10 runner helpers updated

Files: `tools/run_phase_h9_from_line_validator_regression.py`, `tools/run_phase_h10_from_line_evidence_regression.py`

- `has_route_011()` helper updated to accept optional `errors` list so it can detect `ROUTE-011` in either `warnings` or `errors`.
- `has_route_011_in_errors()` helper added.
- All check sites updated to pass both `errors` and `warnings` to `has_route_011()`.
- Check 35 in H.10 updated: removed `len(errors) == 0` expectation since warning config now places `ROUTE-011` in `errors`.
- No behavioral changes to validator logic.

### 4. H.4 runner allowed-files list updated

File: `tools/run_phase_h4_routing_office_code_validator_regression.py`

- Added H.9/H.10/H.13/H.15 artifacts, `config/cci_enforcement_config.json`, and updated routing example fixtures to the `allowed` changed-files set.

### 5. Routing example fixtures updated

Files:
- `examples/audit_cci_routing_valid.json`
- `examples/audit_cci_routing_warning_via_unnumbered.json`
- `examples/audit_cci_routing_warning_copyto_excess.json`
- `examples/audit_cci_routing_warning_need_to_know.json`
- `examples/audit_cci_combined_warning.json`

- Added `"from": "Commanding Officer, Example Unit"` to each fixture so `ROUTE-011` does not trigger, preserving their original pass expectations.

---

## What Did NOT Change

- `src/cci_routing_validate.py` — untouched. Severity branching already implemented in H.13.
- `src/cci_severity_mapper.py` — untouched.
- `src/validator_runner.py` — untouched.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — untouched.
- `src/pdf_v6_render.py` — untouched.
- `src/context_resolver.py` — untouched.
- `src/correction_commands.py` — untouched.
- `src/correction_nl_commands.py` — untouched.
- `src/intake_orchestrator.py` — untouched.
- No approved/pending/session/evidence logs committed.
- No real command/user data committed.
- No renderer/layout changes.
- No prompt-contract changes.
- No Phase F/G command-layer changes.
- No automatic enforcement from approved logs.
- No background automation.
- `CCI-ROUTE-010` remains advisory.
- No error-level promotion.

---

## Rollback

Immediate: restore `CCI-ROUTE-011.effective_severity` to `"advisory"` in `config/cci_enforcement_config.json`, commit, and push. No code changes required.

---

## Regression Results

| Runner | Result |
|---|---|
| H.13 config regression | 27/27 PASS |
| H.9 From-line validator | 18/18 PASS |
| H.10 From-line evidence | 39/39 PASS |
| H.6 office-code evidence | 15/15 PASS |
| H.8 third-rule catalog | 16/16 PASS |
| H.4 office-code validator | 18/18 PASS |
| CCI consolidated audit | PASS |
| CCI routing | PASS |
| CCI subject | PASS |
| CCI ref/encl | PASS |
| CCI acronym | PASS |
| CCI date/time | PASS |
| CCI personnel | PASS |
| CCI POC | PASS |
| C7 phase 1 layout | PASS |
| C8 layout | PASS |
| C9 layout | PASS |
| C10 layout | PASS |
| Context schema | PASS |
| Correction classify | PASS |
| Correction command | 45/45 PASS |
| Correction implementation | 45/45 PASS |
| Correction NL command | 151/151 PASS |
| Correction pending | 33/33 PASS |
| Correction profile promotion | 33/33 PASS |
| Correction regression | PASS |
| Correction review | 30/30 PASS |
| Correction session | PASS |
| Intake regression | PASS |
| Profile regression | PASS |
| H.2 subject acronym | 12/12 PASS |
| H.3 second rule catalog | 15/15 PASS |
| Pilot subject acronym rule catalog | 11/11 PASS |

**Full 33-suite gate: 33/33 PASS**

---

## Open Questions / Next Steps

1. **Burn-in observation:** A mandatory observation period is required before any discussion of error-level promotion. No error-level promotion may be discussed until after a separate burn-in checkpoint.
2. **Dedicated ROUTE-011 warning-config check:** H.13 runner now includes Check 11b and 14b. Consider adding a synthetic warning-config fixture if more granularity is needed.
3. **Real-world payload monitoring:** If real Navy standard-letter payloads are available, observe `ROUTE-011` trigger rate and `window_envelope` usage.
4. **Future Phase H.16 / Phase I.15:** Possible next phases include:
   - Error-level promotion readiness review (after burn-in).
   - Additional catalog-pilot search.
   - `CCI-ROUTE-010` reconsideration (requires more real-world evidence).

---

End of Phase H.15 Warning Pilot Checkpoint.
