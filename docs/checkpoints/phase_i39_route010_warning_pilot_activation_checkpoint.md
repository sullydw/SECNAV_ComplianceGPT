# Phase I.39 / Phase J.3 — CCI-ROUTE-010 Warning Pilot Activation Checkpoint

**Date:** 2026-06-10
**Phase:** I.39 / J.3
**Action:** Activation of controlled warning pilot for `CCI-ROUTE-010`
**Activation type:** Config-only (no validator, catalog, renderer, or command-layer changes)

---

## 1. Pre-activation approval

| Item | Value |
|------|-------|
| Planning document | `docs/planning/phase_i37_route010_warning_pilot_plan.md` |
| Review phase | I.38 / J.2 |
| Review verdict | `APPROVE I.38 / J.2 ROUTE-010 WARNING PILOT PLAN REVIEW` |
| Prior warning pilot precedent | H.15 / H.34 `CCI-ROUTE-011` warning pilot |

---

## 2. Config change executed

**File:** `config/cci_enforcement_config.json`

**Diff:**

```diff
     "CCI-ROUTE-010": {
-      "effective_severity": "advisory",
+      "effective_severity": "warning",
       "allow_override_up_to": "error",
-      "reason": "Office code prefix rule; evidence collected in Phase H.6; advisory by default",
+      "reason": "Office code prefix rule; evidence collected in Phase H.6; warning pilot active in Phase I.39 / Phase J.3",
+      "snapshot_id": "cfg_20260610_warning"
     },
```

**What changed:**
- `CCI-ROUTE-010.effective_severity`: `advisory` → `warning`
- `reason` field updated to reflect warning pilot activation
- `snapshot_id` added for traceability

**What did NOT change:**
- `CCI-ROUTE-011.effective_severity`: remains `warning`
- `global_default`: remains `advisory`
- `allow_override_up_to`: remains `error` for both rules
- Validator logic (`src/cci_routing_validate.py`): unchanged
- Rule catalog (`rules_v6/CCI/cci_ch2_routing_rules.json`): unchanged
- Renderer/layout: unchanged
- Prompt contracts: unchanged
- Context/intake/UI/command-flow: unchanged
- Phase F/G command layer: unchanged
- Fixtures or runners: only runner expectations updated to match new severity output destination

---

## 3. Runner expectation updates

Because `CCI-ROUTE-010` now emits at `warning` severity, findings appear in the `errors` list (blocking) rather than the `warnings` list. The following runners were updated to check both lists for ROUTE-010 presence/absence, without changing test fixtures or validator logic:

- `tools/run_phase_h4_routing_office_code_validator_regression.py`
- `tools/run_phase_h6_routing_office_code_evidence_regression.py`
- `tools/run_phase_h9_from_line_validator_regression.py`
- `tools/run_phase_h10_from_line_evidence_regression.py`
- `tools/run_phase_h13_config_regression.py`

No fixtures were modified. No validator logic was modified. The `allowed` file list in H.4 check 17 was updated to include new Phase I.37/I.39 artifacts.

---

## 4. Regression results

### 4.1 Targeted regressions

| Runner | Checks | Result |
|--------|--------|--------|
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | 18/18 | PASS |
| `tools/run_phase_h6_routing_office_code_evidence_regression.py` | 15/15 | PASS |
| `tools/run_phase_h9_from_line_validator_regression.py` | 18/18 | PASS |
| `tools/run_phase_h10_from_line_evidence_regression.py` | 39/39 | PASS |
| `tools/run_phase_h13_config_regression.py` | 27/27 | PASS |

### 4.2 Full 35-suite gate

All 35 regression suites were executed via the cascading runner invocations embedded in H.4 and H.13. All suites passed.

| Suite count | 35 |
| Failures | 0 |
| Gate status | PASS |

---

## 5. Post-activation state

| Rule | effective_severity |
|------|-------------------|
| `CCI-ROUTE-010` | `warning` |
| `CCI-ROUTE-011` | `warning` |
| `global_default` | `advisory` |
| Error promotion | Unauthorized |

---

## 6. Rollback path

If the warning pilot must be reversed:

1. Restore `CCI-ROUTE-010.effective_severity` to `advisory` in `config/cci_enforcement_config.json`
2. Rerun `tools/run_phase_h13_config_regression.py`
3. Rerun `tools/run_phase_h4_routing_office_code_validator_regression.py`
4. Rerun `tools/run_phase_h6_routing_office_code_evidence_regression.py`
5. Rerun full 35-suite gate
6. Document rollback in a new checkpoint

---

## 7. Recommended next phase

**Phase I.40 / Phase J.4 — ROUTE-010 Warning Pilot Burn-In Checkpoint #1**

Purpose: Observe pilot behavior for a cooldown period, collect any user feedback, and verify no regressions emerge before considering further promotion.

---

## 8. Explicit prohibitions maintained

- No error promotion authorized
- No validator changes
- No catalog changes
- No renderer/layout changes
- No prompt/context/intake/UI/command-flow changes
- No Phase F/G command-layer changes
- No logs or unsanitized material committed
- `docs/BOOTSTRAP.md` untouched
- `docs/HERMES_INSTRUCTIONS.md` untouched

---

## 9. Signatures

| Role | Status |
|------|--------|
| Planning (I.37) | Complete |
| Review (I.38/J.2) | Approved |
| Activation (I.39/J.3) | Complete |
| Burn-in (I.40/J.4) | Pending |
