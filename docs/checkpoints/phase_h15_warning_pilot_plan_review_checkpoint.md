# Phase H.15 / Phase I.14 — Warning Pilot Plan Review Checkpoint

**Date:** 2026-06-08  
**Review commit:** `[TBD]` — `Docs: Record Phase H.15 plan review checkpoint`  
**Plan document:** `docs/planning/phase_h15_route011_warning_pilot_plan.md`  
**Previous phase:** H.14 / I.13 — Controlled Promotion Readiness Review (`fcb1d4c`)  
**Scope:** Read-only review. No files modified during review. No severity changed. No commits made during review.  
**Verdict:** `APPROVE H.15 WARNING PILOT PLAN FOR CONFIG-ONLY IMPLEMENTATION`

---

## 1. Review Summary

The Phase H.15 / Phase I.14 controlled warning pilot plan for `CCI-ROUTE-011` was reviewed against the 17-point checklist and approved as a planning source of truth.

**This approval does not itself authorize implementation.** A separate explicit go-ahead is required before any config change.

---

## 2. Checklist Confirmation

| # | Item | Status |
|---|---|---|
| 1 | Pilot target is ONLY `CCI-ROUTE-011` | PASS |
| 2 | `CCI-ROUTE-010` remains advisory | PASS |
| 3 | Pilot is config-only | PASS |
| 4 | Changes only `CCI-ROUTE-011` `effective_severity` from `advisory` to `warning` | PASS |
| 5 | No error-level promotion authorized | PASS |
| 6 | Full 33-suite gate required after any config change | PASS |
| 7 | H.13 runner verifies warning behavior (Check 14: temp warning for ROUTE-010; Check 13: temp error for ROUTE-011) | PASS — dedicated ROUTE-011 warning-config check to be added during implementation |
| 8 | H.9 runner still passes | PASS — 18/18 |
| 9 | H.10 runner still passes | PASS — 39/39 |
| 10 | `window_envelope` usage documented as operator consideration | PASS |
| 11 | No validator code change needed | PASS |
| 12 | No catalog change needed | PASS |
| 13 | No renderer/layout change needed | PASS |
| 14 | No prompt-contract/intake/UI change needed | PASS |
| 15 | No Phase F/G command-layer change | PASS |
| 16 | No approved/pending/session logs or real data committed | PASS |
| 17 | No error promotion until separate burn-in/review checkpoint | PASS |

---

## 3. Default Config Verified

| Rule | `effective_severity` | `allow_override_up_to` |
|---|---|---|
| `CCI-ROUTE-010` | `advisory` | `error` |
| `CCI-ROUTE-011` | `advisory` | `error` |

Both rules remain at `advisory`. Neither promoted. No config file modified during review.

---

## 4. Regression Results at Review Time

| Runner | Checks | Result |
|---|---|---|
| H.13 config regression | 26 | PASS |
| H.9 From-line validator | 18 | PASS |
| H.10 From-line evidence | 39 | PASS |
| H.6 office-code evidence | 15 | PASS |
| H.8 third-rule catalog | 16 | PASS |
| H.4 office-code validator | 18 | PASS |
| C7-C10 layout | — | PASS |
| **Full gate** | **33 suites** | **33/33 PASS** |

All runs used `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

---

## 5. Blockers

None.

---

## 6. Non-Blocking Recommendations

1. **Add dedicated `CCI-ROUTE-011` warning-config check to H.13 runner** during implementation phase.
2. **Document `window_envelope` field usage** in payload schema or intake docs.
3. **Define staging/burn-in approach** before pilot activation.
4. **Prepare synthetic batch** for observation period.

---

## 7. What Phase H.15 Must NOT Do

- No validator changes — `src/cci_routing_validate.py` untouched.
- No renderer/layout changes — `src/pdf_v6_render.py` untouched.
- No prompt-contract changes — `src/context_resolver.py` untouched.
- No Phase F/G command-layer changes — `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- No automatic enforcement from approved logs.
- No severity promotion of `CCI-ROUTE-010`.
- No feature flag/config implementation beyond the one-field change in `config/cci_enforcement_config.json`.
- No approved/pending/session/evidence logs committed.
- No real command/user data committed.
- No background automation.

---

## 8. Rollback Plan

Immediate: revert `config/cci_enforcement_config.json` → `overrides.CCI-ROUTE-011.effective_severity` back to `advisory`. No code change required. No restart required (config is read on every `effective_severity()` call).

---

## 9. Open Questions Requiring Approval

1. Should the pilot use the tracked default config or a local override (`config/cci_enforcement_config.local.json`) in a staging environment?
2. Should the burn-in period be extended beyond 30 days?
3. Should an explicit operator sign-off checklist be added before activating the pilot?
4. Should a new regression runner be created specifically for the warning-pilot observation period?
5. What is the criteria for declaring the pilot successful and moving to error-level promotion planning?

---

## 10. Recommended Next Steps

1. Wait for explicit go-ahead before changing `config/cci_enforcement_config.json`.
2. When approved, change `CCI-ROUTE-011.effective_severity` from `advisory` to `warning`.
3. Run full 33-suite regression gate.
4. Begin 30-day burn-in observation.
5. Monitor ROUTE-011 error findings vs false positives.
6. Any unexpected result → immediate rollback to `advisory`.

---

End of Phase H.15 / Phase I.14 warning pilot plan review checkpoint.
