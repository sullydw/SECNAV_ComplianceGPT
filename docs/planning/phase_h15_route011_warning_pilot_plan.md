# Phase H.15 / Phase I.14 — Controlled Warning Pilot for CCI-ROUTE-011

**Status:** Planning-only. Not approved. No implementation authorized.  
**Date:** 2026-06-08  
**Previous Phase:** H.14 / I.13 — Controlled Promotion Readiness Review  
**H.14 Review Verdict:** `CCI-ROUTE-011` READY FOR WARNING PILOT; `CCI-ROUTE-010` NOT READY; error promotion NOT RECOMMENDED for either.  
**Current Baselines:**
- Functional baseline: `d808cb8` — Phase H.10 From-line evidence collection and regression hardening.
- H.13 stable baseline: `084ce64` — severity config support.
- Latest checkpoint: `fcb1d4c` — Phase H.13 implementation review checkpoint.
- Regression gate: 33 suites — 33/33 PASS.

---

## 1. Purpose

Design a controlled, time-bounded warning-level promotion pilot for `CCI-ROUTE-011` (standard letters must have a From line) using the existing config-driven severity mechanism implemented in Phase H.13. This document is planning-only; no config changes, code changes, or severity promotions are authorized by this plan.

---

## 2. Pilot Target

| Attribute | Value |
|---|---|
| Rule ID | `CCI-ROUTE-011` |
| Pilot severity | `warning` (blocking) |
| Config entry | `config/cci_enforcement_config.json` → `overrides.CCI-ROUTE-011.effective_severity` |
| Current value | `advisory` |
| Proposed pilot value | `warning` |
| Ceiling | `allow_override_up_to: error` |
| Catalog severity | `error` (upper bound; warning is safely below) |

---

## 3. What This Phase Is NOT Authorized To Do

The following are explicitly **out of scope** and must not occur until separately approved in a future phase:

| Forbidden Action | Rationale |
|---|---|
| Change `config/cci_enforcement_config.json` in this planning step | Planning only; implementation requires explicit separate approval and regression gate. |
| Promote `CCI-ROUTE-011` to `error` | Warning pilot must complete burn-in first. |
| Promote `CCI-ROUTE-010` to `warning` or `error` | H.14 review found ROUTE-010 NOT READY. |
| Modify `src/cci_routing_validate.py` | Config-only severity change; no validator logic changes needed. |
| Modify `rules_v6/CCI/cci_ch2_routing_rules.json` | Catalog severity remains `error`; no catalog change needed. |
| Modify renderer/layout (`src/pdf_v6_render.py`) | No layout implication for this rule. |
| Modify prompt-contract (`src/context_resolver.py`) | No prompt change needed. |
| Modify intake/UI (`src/intake_orchestrator.py`) | No intake change needed. |
| Modify Phase F/G command layer (`src/correction_commands.py`, `src/correction_nl_commands.py`) | No command-layer change needed. |
| Commit approved/pending/session/evidence logs or real data | Remains gitignored as before. |
| Enable automatic enforcement from approved logs | Out of scope. |
| Background automation / scheduled automation | Out of scope. |

---

## 4. Why CCI-ROUTE-011 Was Selected

| Factor | ROUTE-011 | ROUTE-010 |
|---|---|---|
| Structural simplicity | **Binary** (From present / absent) | **Parsing** (tokenize addressee, detect Code prefix) |
| Exception handling | One clear exception (`window_envelope`) | No exception; edge cases in delimiter detection |
| False-positive risk | **Low** | **Moderate** (real-world addressee formats untested) |
| Scope | Narrow (`standard_letter` only) | Broader (`to` and `via` lines) |
| Evidence | 30 synthetic fixtures + 50 corpus patterns | 30 synthetic fixtures + 50 corpus patterns |
| Config rollback | Immediate | Immediate |
| H.14 verdict | **READY** | **NOT READY** |

---

## 5. Pilot Design

### 5.1 Activation

When separately approved, the pilot is activated by changing one field in `config/cci_enforcement_config.json`:

```json
{
  "overrides": {
    "CCI-ROUTE-011": {
      "effective_severity": "warning",
      ...
    }
  }
}
```

No other config fields change.

### 5.2 Expected Behavior Change

With `effective_severity: warning`:
- `CCI-ROUTE-011` findings move from `warnings` list to `errors` list.
- `validator_runner.py` `overall_pass` transitions from `True` to `False` when ROUTE-011 is triggered.
- `CCI-ROUTE-010` remains advisory; no behavior change.
- All other validators unaffected.

### 5.3 Burn-In / Observation Period

| Parameter | Value |
|---|---|
| Minimum burn-in | 30 days |
| Observation metric | Count of ROUTE-011 findings per batch; ratio of true positives to false positives |
| Acceptance criteria | Zero unexpected false positives in synthetic batch; no regression suite failures |
| Escalation trigger | Any ROUTE-011 false positive or regression failure → immediate rollback |

### 5.4 Rollback

| Scenario | Action |
|---|---|
| Unexpected false positive observed | Revert `CCI-ROUTE-011.effective_severity` to `advisory` in config file. |
| Regression failure | Revert config; investigate; do not patch validator under pressure. |
| Pilot completes successfully after burn-in | Optionally proceed to error-promotion planning (separate phase; not authorized here). |
| Pilot rejected before burn-in ends | Revert config; document reason in checkpoint. |

Rollback is **immediate** — no code change, no restart required (config is read on every `effective_severity()` call).

---

## 6. Regression Requirements

Before ANY config change is committed, the following must pass:

| Requirement | Runner / Check |
|---|---|
| Full 33-suite gate | All `tools/run_*_regression.py` scripts pass. |
| H.13 config runner verifies warning behavior | `tools/run_phase_h13_config_regression.py` must include checks for temp warning config. |
| H.9 runner still passes | `tools/run_phase_h9_from_line_validator_regression.py` — 18/18. |
| H.10 runner still passes | `tools/run_phase_h10_from_line_evidence_regression.py` — 39/39. |
| H.6 runner still passes | `tools/run_phase_h6_routing_office_code_evidence_regression.py` — 15/15. |

If the H.13 runner does not already include a dedicated warning-config check for ROUTE-011, that check must be added in the implementation phase.

---

## 7. Preconditions for Pilot Approval

Before this plan becomes an approved implementation target, the following must be true:

1. **This planning document is reviewed and approved** as source of truth.
2. **Operator readiness:** Users/operators understand the `window_envelope` payload field and how to set it to suppress false positives for window-envelope letters.
3. **Staging or safe environment identified:** If a production equivalent exists, pilot should run in a non-production context first.
4. **Synthetic batch prepared:** A batch of standard-letter payloads (positive and negative controls) is ready to exercise the warning severity.
5. **No open blockers:** ROUTE-010 remains advisory and is not part of this pilot.

---

## 8. Files That May Be Modified in Future Implementation

| File | Change |
|---|---|
| `config/cci_enforcement_config.json` | Change `CCI-ROUTE-011` `effective_severity` from `advisory` to `warning` |
| `tools/run_phase_h13_config_regression.py` | Add dedicated warning-config check for ROUTE-011 (if not already present) |
| `docs/checkpoints/phase_h15_warning_pilot_checkpoint.md` | Created after implementation to record results |

### Files That Must NOT Be Modified

- `src/cci_routing_validate.py`
- `src/cci_severity_mapper.py`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `src/pdf_v6_render.py`
- `src/context_resolver.py`
- `src/intake_orchestrator.py`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`
- `src/validator_runner.py`
- All existing fixtures and regression runners (except permitted H.13 runner additions)

---

## 9. Open Questions

1. Should the pilot use the tracked default config or a local override (`config/cci_enforcement_config.local.json`) in a staging environment?
2. Should the burn-in period be extended beyond 30 days?
3. Should an explicit operator sign-off checklist be added before activating the pilot?
4. Should a new regression runner be created specifically for the warning-pilot observation period (e.g., counting ROUTE-011 error findings over a fixture batch)?
5. What is the criteria for declaring the pilot successful and moving to error-level promotion planning?

---

## 10. Recommended Decision

| Decision | Action |
|---|---|
| **Approve this plan** | Mark as approved planning source of truth. Wait for explicit go-ahead before changing config. |
| **Reject this plan** | Keep both rules advisory indefinitely. Shift effort to real-world evidence collection or other work. |
| **Defer** | Keep advisory. Revisit after real-world Navy standard-letter payloads are collected. |

**Recommended:** Approve this plan as a planning document. Do not activate the pilot until all preconditions are met and an explicit go-ahead is given.

---

*End of Phase H.15 / Phase I.14 planning document.*
