# Phase I.39B / Phase J.3B — CCI-ROUTE-010 Warning Pilot Runner Comment Cleanup Checkpoint

**Date:** 2026-06-10
**Phase:** I.39B / J.3B
**Action:** Comment/docstring cleanup only in regression runner files
**Purpose:** Remove stale advisory-era wording now that ROUTE-010 is in warning pilot

---

## 1. Scope

Comment and docstring changes only. No executable logic modified. No fixture payloads modified. No validator behavior modified.

Files touched:

- `tools/run_phase_h4_routing_office_code_validator_regression.py`
- `tools/run_phase_h6_routing_office_code_evidence_regression.py`
- `tools/run_phase_h9_from_line_validator_regression.py`
- `tools/run_phase_h10_from_line_evidence_regression.py`
- `tools/run_phase_h13_config_regression.py`

---

## 2. Stale wording removed

| File | Old wording | New wording |
|------|-------------|-------------|
| H.4 | "Advisory Validator Regression Runner" | "Warning Validator Regression Runner" |
| H.4 | "ROUTE-010 positive" (without destination) | "ROUTE-010 positive in errors" |
| H.4 | "office-code prefix advisory" | "office-code prefix checks" |
| H.6 | "without changing severity" | "under the active warning pilot" |
| H.6 | "Warnings contain CCI-ROUTE-010" | "Findings contain CCI-ROUTE-010" |
| H.6 | "errors list remains empty for all fixtures" | "Negative fixtures have empty errors list" |
| H.6 | "Advisory findings go into warnings only" | "Positive fixtures produce ROUTE-010 findings (in errors under warning config)" |
| H.9 | "Advisory Validator Enforcement Regression Runner" | "Warning Validator Enforcement Regression Runner" |
| H.9 | "triggers advisory ROUTE-011" | "triggers warning ROUTE-011" |
| H.9 | "suppresses advisory" | "suppresses warning" |
| H.10 | "CCI-ROUTE-010 behavior preserved" | "CCI-ROUTE-010 behavior preserved (findings in errors under warning config)" |
| H.13 | "ROUTE-010 effective_severity=advisory" | "ROUTE-010 effective_severity=warning" |
| H.13 | "Advisory config still produces warnings" | "Default warning config produces errors (blocking) for ROUTE-010" |
| H.13 | "still emit warnings, not errors" | "produce ROUTE-010 errors under default warning config" |

---

## 3. What did NOT change

- Config (`config/cci_enforcement_config.json`)
- Severity levels
- Validator logic
- Rule catalog
- Renderer/layout
- Prompt contracts
- Context/intake/UI/command-flow
- Phase F/G command layer
- Fixtures or runners (logic unchanged)
- `docs/BOOTSTRAP.md`
- `docs/HERMES_INSTRUCTIONS.md`

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

All suites passed via cascading runner invocations in H.4 and H.13.

| Suite count | 35 |
| Failures | 0 |
| Gate status | PASS |

---

## 5. Post-cleanup state

| Rule | effective_severity |
|------|-------------------|
| `CCI-ROUTE-010` | `warning` |
| `CCI-ROUTE-011` | `warning` |
| `global_default` | `advisory` |
| Error promotion | Unauthorized |

---

## 6. Decision

I.39 activation remains acceptable as-is. Comment cleanup does not affect behavior, severity, or config.

---

## 7. Recommended next phase

**Phase I.40 / Phase J.4 — ROUTE-010 Warning Pilot Burn-In Checkpoint #1**

Purpose: Observe pilot behavior for a cooldown period, collect any user feedback, and verify no regressions emerge before considering further promotion.

---

## 8. Signatures

| Role | Status |
|------|--------|
| Activation (I.39) | Complete |
| Comment cleanup (I.39B) | Complete |
| Burn-in (I.40) | Pending |
