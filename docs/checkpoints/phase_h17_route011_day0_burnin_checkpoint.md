# Phase H.17 / Phase I.16 — Day 0 Burn-In Checkpoint

**Date:** 2026-06-08  
**Checkpoint Commit:** See git log for `Docs: Record H.17 day zero burn-in checkpoint`
**Burn-In Clock Start:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot` (2026-06-08)  
**H.16 Burn-In Regression Commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**H.16 Review Approval Commit:** `95ac852` — `Docs: Record H.16 burn-in review approval`  
**Window Envelope Guidance Commit:** `2d1bb68` — `Docs: Add window envelope payload guidance`  
**Current Functional Baseline:** `7e42f64`  
**Regression Set:** 34 suites  
**Full Gate Result:** 34/34 PASS  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Status:** Day 0 of burn-in observation period. No code changes. Documentation only.

---

## 1. Burn-In Period Definition

The burn-in observation period is **30 days** from the H.15 warning pilot activation commit (`18fc9bf`).

- **Start date:** 2026-06-08 (date of `18fc9bf`)
- **End date:** 2026-07-08 (30 days later)
- **Purpose:** Observe `CCI-ROUTE-011` at `warning` severity in real or realistic usage to detect false positives, operator confusion, or config issues before any discussion of error promotion.
- **Scope:** The warning pilot affects standard letters missing a `from` line. Window-envelope letters with `window_envelope: true` are suppressed.

---

## 2. Current Config State

```json
{
  "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
  "global_default": "advisory",
  "overrides": {
    "CCI-ROUTE-010": {
      "effective_severity": "advisory",
      "allow_override_up_to": "error"
    },
    "CCI-ROUTE-011": {
      "effective_severity": "warning",
      "allow_override_up_to": "error"
    }
  }
}
```

| Rule | Catalog Severity | Effective Severity | Status |
|---|---|---|---|
| `CCI-ROUTE-010` (Office code prefix) | `error` | `advisory` | Unchanged since H.4 |
| `CCI-ROUTE-011` (From line required) | `error` | `warning` | Active warning pilot |

**No error-level promotion is authorized for any rule.**

---

## 3. Regression Results at Day 0

All 34 suites were executed with the explicit Miniconda Python interpreter and passed.

| Suite | Runner | Checks | Result | Time |
|---|---|---|---|---|
| H.16 burn-in | `run_phase_h16_route011_burnin_regression.py` | 96/96 | PASS | ~4.9s |
| H.13 config | `run_phase_h13_config_regression.py` | 27/27 | PASS | ~4.6s |
| H.10 From-line evidence | `run_phase_h10_from_line_evidence_regression.py` | 39/39 | PASS | ~0.2s |
| H.9 From-line validator | `run_phase_h9_from_line_validator_regression.py` | 18/18 | PASS | ~0.1s |
| H.8 third catalog | `run_phase_h8_third_rule_catalog_regression.py` | 16/16 | PASS | ~0.1s |
| H.6 office-code evidence | `run_phase_h6_routing_office_code_evidence_regression.py` | 15/15 | PASS | ~4.0s |
| H.4 office-code validator | `run_phase_h4_routing_office_code_validator_regression.py` | 18/18 | PASS | ~0.4s |
| H.3 second catalog | `run_phase_h3_second_rule_catalog_regression.py` | 15/15 | PASS | ~0.1s |
| H.2 subject acronym | `run_phase_h2_subject_acronym_validator_regression.py` | 12/12 | PASS | ~0.3s |
| H.1 pilot catalog | `run_pilot_subject_acronym_rule_catalog_regression.py` | 11/11 | PASS | ~0.0s |
| Phase H planner | `run_correction_implementation_regression.py` | 45/45 | PASS | ~0.1s |
| Phase G NL | `run_correction_nl_command_regression.py` | 151/151 | PASS | ~0.1s |
| Phase F commands | `run_correction_command_regression.py` | 45/45 | PASS | ~0.1s |
| Phase E review | `run_correction_review_regression.py` | 30/30 | PASS | ~0.1s |
| Phase D pending | `run_correction_pending_regression.py` | 33/33 | PASS | ~0.1s |
| Phase C profile | `run_correction_profile_promotion_regression.py` | 33/33 | PASS | ~0.1s |
| Phase B classify | `run_correction_classify_regression.py` | — | PASS | ~0.1s |
| Intake | `run_intake_regression.py` | — | PASS | ~0.1s |
| Correction | `run_correction_regression.py` | — | PASS | ~0.0s |
| Session | `run_correction_session_regression.py` | — | PASS | ~0.1s |
| Profile | `run_profile_regression.py` | — | PASS | ~0.0s |
| CCI audit | `run_cci_audit_regression.py` | — | PASS | ~0.2s |
| Context schema | `run_context_schema_regression.py` | — | PASS | ~0.0s |
| CCI subject | `run_cci_subject_regression.py` | — | PASS | ~0.1s |
| CCI ref/encl | `run_cci_ref_encl_regression.py` | — | PASS | ~0.2s |
| CCI acronym | `run_cci_acronym_regression.py` | — | PASS | ~0.1s |
| CCI date/time | `run_cci_date_time_regression.py` | — | PASS | ~0.2s |
| CCI personnel | `run_cci_personnel_regression.py` | — | PASS | ~0.1s |
| CCI POC | `run_cci_poc_regression.py` | — | PASS | ~0.1s |
| CCI routing | `run_cci_routing_regression.py` | — | PASS | ~0.2s |
| C7 layout | `run_c7_phase1_regression.py` | 5216/144 | PASS | ~0.7s |
| C8 layout | `run_c8_regression.py` | 5216/144 | PASS | ~1.6s |
| C9 layout | `run_c9_regression.py` | 11/273 | PASS | ~3.0s |
| C10 layout | `run_c10_regression.py` | 5216/144 | PASS | ~6.4s |

**Total wall time:** ~28.4 seconds  
**Gate result:** 34/34 PASS

---

## 4. Operator Guidance

Operator-facing guidance exists and is current:

- **File:** `docs/guidance/window_envelope_payload_guidance.md`
- **Commit:** `2d1bb68`
- **Contents:** Quick-reference table, 5 JSON examples, excluded document types, current config state, rollback instructions, explicit statement that future error promotion is unauthorized.
- **Audience:** Operators creating payloads who need to know when to set `window_envelope: true`.

---

## 5. Known Accepted Limitations (Non-Blocking)

These limitations were reviewed and accepted during H.16 review. They are documented here as baseline observations for the burn-in period.

### 5.1 Exotic Whitespace

- **Issue:** Zero-width space (`\u200B`) and BOM (`\uFEFF`) do not trigger `CCI-ROUTE-011` because `str.strip()` does not remove them.
- **Impact:** A `from` field containing only ZWS or BOM is treated as non-empty and passes the presence check.
- **Risk level:** Very low — requires deliberate or corrupted input.
- **Disposition:** Acceptable for warning pilot. Consider validator hardening before any future error promotion.
- **Tracking:** If any real-world case appears during burn-in, escalate to H.18 hardening proposal.

### 5.2 Window-Envelope-Like Without Tag

- **Issue:** A standard letter missing `from` and lacking `window_envelope: true` produces `CCI-ROUTE-011` in `errors`.
- **Impact:** Operator/data-quality risk if the operator forgets the tag.
- **Risk level:** Low — intentional design; the validator cannot distinguish intent from omission.
- **Disposition:** Acceptable for warning pilot. The guidance document instructs operators to tag explicitly.
- **Tracking:** If operators report confusion, consider UI/intake hint (not validator change).

---

## 6. Burn-In Goals

During the 30-day observation period, the project seeks the following evidence:

| Goal | Metric | Threshold |
|---|---|---|
| Zero unexpected false positives | Operator reports or automated findings where a valid standard letter with a real `from` line triggers `CCI-ROUTE-011` | 0 |
| Zero config regressions | `effective_severity("CCI-ROUTE-011")` must remain `"warning"` across restarts/reloads | 0 |
| Window-envelope suppression verified | Letters with `window_envelope: true` and no `from` must not trigger | 100% |
| Non-standard exclusion verified | Memorandums, endorsements, joint letters must not trigger | 100% |
| Operator guidance utility | At least 1 operator confirms guidance was helpful (if asked) | ≥1 |
| Burn-in fixture stability | Re-running H.16 runner weekly must continue to pass | 100% |

---

## 7. Rollback Triggers

The warning pilot must be rolled back to `advisory` immediately if any of the following occur:

| Trigger | Action | Verification |
|---|---|---|
| Any confirmed false positive on a valid standard letter with real `from` | Restore `effective_severity` to `"advisory"` | Re-run H.9 + H.16 runners |
| Operator report that warning is blocking legitimate workflow | Restore `effective_severity` to `"advisory"` | Re-run full 34-suite gate |
| Config file corruption or unintended severity change | Restore from git; verify config | Re-run H.13 runner |
| Regression suite failure in H.16, H.13, H.9, or H.10 | Investigate; if related to warning severity, rollback | Full 34-suite gate |
| User explicit directive to deactivate warning pilot | Restore `effective_severity` to `"advisory"` | Re-run full 34-suite gate |

Rollback method: edit `config/cci_enforcement_config.json`, change `CCI-ROUTE-011.effective_severity` from `"warning"` to `"advisory"`. No validator, catalog, renderer, or command-layer changes required.

---

## 8. Future Error Promotion Remains Unauthorized

**Error promotion for `CCI-ROUTE-011` (or any other rule) is not authorized during this burn-in period or at its conclusion without a separate planning phase.**

- A future Phase H.18 / I.17 **Error Promotion Readiness Review** may be proposed after the burn-in period ends.
- That phase would require:
  1. New planning document approved by the user.
  2. Evidence that all burn-in goals were met.
  3. No open false-positive reports.
  4. Explicit user authorization to change `effective_severity` to `"error"`.
- Until then, `CCI-ROUTE-011` must remain at `warning` or lower.

---

## 9. What Was NOT Modified in This Checkpoint

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

## 10. Files Referenced by This Checkpoint

| File | Role |
|---|---|
| `docs/checkpoints/phase_h17_route011_day0_burnin_checkpoint.md` | This document |
| `docs/PROJECT_STATUS.md` | Updated to reference this checkpoint |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Updated to reference this checkpoint |
| `docs/guidance/window_envelope_payload_guidance.md` | Operator guidance (unchanged) |
| `docs/checkpoints/phase_h16_route011_burnin_regression_checkpoint.md` | H.16 burn-in baseline |
| `docs/planning/phase_h15_route011_warning_pilot_plan.md` | H.15 warning pilot plan |
| `config/cci_enforcement_config.json` | Current severity config (unchanged) |
| `tools/run_phase_h16_route011_burnin_regression.py` | H.16 burn-in runner (unchanged) |
| `tools/run_phase_h13_config_regression.py` | H.13 config runner (unchanged) |
| `tools/run_phase_h9_from_line_validator_regression.py` | H.9 validator runner (unchanged) |
| `tools/run_phase_h10_from_line_evidence_regression.py` | H.10 evidence runner (unchanged) |

---

## 11. Next Checkpoint

The next expected checkpoint is:

- **Mid-burn-in checkpoint (Day ~15):** Optional, only if intermediate observations are noteworthy.
- **End-of-burn-in checkpoint (Day 30, ~2026-07-08):** `docs/checkpoints/phase_h17_route011_day30_burnin_checkpoint.md` or similar.
- **Trigger:** Day 30 elapsed, or user request, or any rollback trigger activated.

---

End of Phase H.17 / Phase I.16 Day 0 Burn-In Checkpoint.
