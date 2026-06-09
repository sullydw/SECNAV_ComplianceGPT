# Phase H.16 / Phase I.15 — ROUTE-011 Warning Pilot Burn-In Review Plan

**Date:** 2026-06-08  
**Previous Phase:** H.15 / I.14 — Controlled Warning Pilot for `CCI-ROUTE-011` (active)  
**H.15 Implementation Commit:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**H.15 Follow-up Commit:** `c12e904` — `Docs: Update H.15 checkpoint commit hash`  
**Warning Pilot Checkpoint:** `docs/checkpoints/phase_h15_route011_warning_pilot_checkpoint.md`

---

## 1. H.15 Status Summary

The Phase H.15 controlled warning pilot for `CCI-ROUTE-011` is **active**.

- `CCI-ROUTE-011.effective_severity` = `warning` in `config/cci_enforcement_config.json`.
- `CCI-ROUTE-010.effective_severity` = `advisory` (unchanged).
- No validator logic changes.
- No rule catalog changes.
- No renderer/layout changes.
- No prompt-contract changes.
- No command-layer changes.
- Full 33-suite regression gate: **33/33 PASS**.

Rollback is immediate: restore `CCI-ROUTE-011.effective_severity` to `"advisory"` in the config file, commit, and push. No code changes required.

---

## 2. H.16 Purpose — Burn-In Observation Planning

Phase H.16 is **planning-only**. Its purpose is to define the burn-in observation criteria and checkpoint requirements before any future discussion of error-level promotion.

**H.16 must NOT:**
- Promote any rule severity.
- Modify `config/cci_enforcement_config.json`.
- Modify validators.
- Modify rule catalogs.
- Modify renderer/layout behavior.
- Modify prompt contracts.
- Modify context/intake/UI/command-flow.
- Modify Phase F/G command layer.
- Commit approved/pending/session/evidence logs.
- Commit real command/user data.

H.16 produces a planning document only. No implementation is authorized by this plan.

---

## 3. Burn-In Objective

Observe `CCI-ROUTE-011` warning behavior under realistic or synthetic-simulated load to confirm:

1. The warning fires correctly for standard letters missing a `from` line.
2. The warning does not fire for non-standard-letter document types.
3. The `window_envelope: true` suppression works as documented.
4. No unintended side effects occur in other validators or the audit pipeline.
5. Operator understanding of `window_envelope` usage is sufficient.
6. False-positive rate remains acceptably low.

---

## 4. Minimum Observation Period

**Preferred:** 30 calendar days of real-world standard-letter processing.  
**Acceptable alternative:** A single synthetic batch review of at least 100 distinct standard-letter payloads covering all evidence categories in Section 7, plus regression confirmation.

If real-world data is unavailable, the synthetic batch review is sufficient for planning purposes but does **not** replace real-world observation before any error-level discussion.

---

## 5. Evidence to Collect

### 5.1 Standard letters missing `from`

- Expected: `CCI-ROUTE-011` appears in `errors` list (blocking).
- Count and catalog.
- Verify message text is clear: indicates missing `From:` line.

### 5.2 Standard letters with valid `from`

- Expected: No `CCI-ROUTE-011` finding.
- Count and confirm no false positives.

### 5.3 Standard letters with whitespace/null/empty `from`

- Expected: `CCI-ROUTE-011` fires (whitespace-only, null, empty string, `""`, `"   "` should all be treated as missing).
- Confirm current validator behavior handles these cases.

### 5.4 Non-standard-letter documents that must not trigger

Document types that must **never** trigger `CCI-ROUTE-011`:

| Document Type | Expected |
|---|---|
| Memorandum (plain-paper, MFR, etc.) | No finding |
| Endorsement | No finding |
| Joint letter | No finding |
| Multiple-address letter | No finding |
| Missing/unknown `doc_type` | Skip (no finding) |

### 5.5 Window-envelope letters with `window_envelope: true`

- Expected: `CCI-ROUTE-011` suppressed.
- Confirm suppression works for all standard-letter payloads.
- Verify no other warnings are lost due to suppression logic.

### 5.6 Window-envelope-like letters without the field

- These represent operator/data-quality risk.
- If `window_envelope` is absent or `false`, the warning fires even for letters that may be intended for window envelopes.
- Assess frequency and decide if documentation or operator guidance is needed.

### 5.7 Realistic Navy/Marine Corps payloads

If available:
- De-identified standard-letter JSON payloads from actual Navy/Marine Corps correspondence.
- Mix of with-From and without-From cases.
- Mix of window-envelope and non-window-envelope cases.
- Observe trigger rate and operator response.

If unavailable:
- Use synthetic fixtures that approximate realistic patterns (rank, command, office codes, ship names).

---

## 6. False-Positive Review Criteria

A false positive is defined as `CCI-ROUTE-011` appearing in `errors` when the document should **not** have triggered.

**Acceptable false-positive rate:** Zero for all non-standard-letter document types.  
**Tolerable for standard letters:** If a standard letter intentionally omits `from` for a valid reason not covered by `window_envelope`, document the case and assess whether a new exception field is needed.

**Review steps:**
1. For every unexpected `CCI-ROUTE-011` finding, record: payload `doc_type`, `from` value (or absence), `window_envelope` value, and expected vs actual behavior.
2. Categorize: true positive, false positive, or edge case requiring clarification.
3. If false positives exceed 5% of standard-letter samples, recommend immediate rollback to advisory.

---

## 7. Rollback Criteria

Rollback to advisory must be triggered immediately if any of the following occur:

| Criterion | Action |
|---|---|
| False positives on non-standard-letter types | Rollback + investigate |
| False positives > 5% on standard-letter samples | Rollback + reassess |
| `window_envelope: true` suppression fails | Rollback + fix |
| Any other validator or audit pipeline breakage | Rollback + investigate |
| Operator confusion about `window_envelope` usage documented | Consider rollback + improve documentation |
| Regression gate fails (any suite) | Rollback immediately |

Rollback procedure:
1. Edit `config/cci_enforcement_config.json`.
2. Set `CCI-ROUTE-011.effective_severity` to `"advisory"`.
3. Update `reason` and `snapshot_id`.
4. Run full 33-suite regression gate.
5. Commit and push.

---

## 8. Operator Clarity Requirements

Before any error-level discussion, operators must understand:

1. What `CCI-ROUTE-011` checks: presence of `from` field on standard letters.
2. What suppresses it: `window_envelope: true`.
3. What document types are excluded: memorandum, endorsement, joint letter, multiple-address letter.
4. How to interpret warning vs error: warning = blocking (current H.15 behavior), advisory = non-blocking.
5. How to temporarily override (if local config override is documented and supported).

If operator understanding is insufficient, error promotion is blocked regardless of technical readiness.

---

## 9. `window_envelope` Usage Verification

Verify the following:

- `window_envelope: true` suppresses `CCI-ROUTE-011` on standard letters.
- `window_envelope: false` or absent allows `CCI-ROUTE-011` to fire.
- `window_envelope` field is respected only for standard letters; other doc types ignore it (no effect needed).
- No other validator warnings are accidentally suppressed.

Test fixtures:
- `examples/routing_from_h10_neg_05.json` — `window_envelope: true`, no finding.
- `examples/routing_from_h10_neg_06.json` — `window_envelope: false`, standard letter, finding fires.
- `examples/routing_from_h10_neg_07.json` — absent `window_envelope`, standard letter, finding fires.

---

## 10. Regression Gate Requirements

The 33-suite regression gate must remain passing throughout burn-in:

| Suite | Purpose |
|---|---|
| H.13 config regression | Config parsing, severity branching, default/warning/error transitions |
| H.10 From-line evidence | 20 negative + 10 positive fixture validation |
| H.9 From-line validator | Validator scope, doc_type filtering, window_envelope suppression |
| H.8 third-rule catalog | Catalog schema, rule provenance, catalog entry presence |
| H.6 office-code evidence | ROUTE-010 evidence preservation |
| H.4 office-code validator | ROUTE-010 advisory enforcement preservation |
| All other 27 suites | Unrelated system integrity |

Any regression failure blocks error promotion discussion until resolved.

---

## 11. What Must Be Reviewed Before Any Error Discussion

Before Phase H.17 / Phase I.16 (error promotion readiness review) can be planned, the following must be reviewed and documented:

1. **Burn-in observation log:** dates, sample count, trigger rate, false-positive count.
2. **Operator feedback:** any confusion, requests for clarification, or override usage.
3. **`window_envelope` field adoption rate:** how often operators supply it correctly.
4. **Real-world payload coverage:** if real data exists, summary statistics; if not, synthetic coverage summary.
5. **Regression stability:** 33/33 gate passing at review time.
6. **Rollback test:** confirm rollback to advisory still works and is documented.

---

## 12. What Would Block Error Promotion

| Blocker | Resolution |
|---|---|
| Any false positive on non-standard-letter types | Fix validator scope + re-test |
| False-positive rate > 2% on standard letters | Add exception handling or improve detection |
| `window_envelope` suppression failures | Fix suppression logic + re-test |
| Operator confusion documented | Improve docs/guidance + re-evaluate |
| Missing real-world payload coverage | Collect real data or extend synthetic coverage |
| Any regression suite failure | Fix + re-run full gate |
| `CCI-ROUTE-010` still not ready | Keep ROUTE-010 advisory; do not bundle promotions |

---

## 13. What Would Support Continued Warning Status

- Zero false positives on non-standard-letter types.
- Low false-positive rate (< 2%) on standard letters.
- `window_envelope` suppression working reliably.
- Operator clarity confirmed.
- 33/33 regression gate stable.
- No operator complaints or rollback requests.

---

## 14. What Would Trigger Rollback to Advisory

- Any regression failure.
- Documented operator confusion or override abuse.
- False-positive rate exceeding thresholds.
- `window_envelope` suppression failure.
- New evidence showing the rule is too broad or ambiguous.
- Explicit operator or stakeholder request.

---

## 15. Files That May Be Modified in Future Implementation

If burn-in review leads to approved action, these files may be modified:

- `config/cci_enforcement_config.json` — severity change (warning → advisory rollback, or warning → error promotion).
- `docs/checkpoints/phase_h16_route011_warning_burnin_checkpoint.md` — checkpoint document (if created).
- `docs/PROJECT_STATUS.md` — status update.
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — plan update.

---

## 16. Files That Must NOT Be Modified

- `src/cci_routing_validate.py` — no validator changes during burn-in planning.
- `rules_v6/CCI/cci_ch2_routing_rules.json` — no catalog changes.
- `src/pdf_v6_render.py` — no renderer changes.
- `src/context_resolver.py` — no prompt-contract changes.
- `src/validator_runner.py` — untouched.
- `src/intake_orchestrator.py` — no intake changes.
- `src/correction_commands.py`, `src/correction_nl_commands.py` — no command-layer changes.
- `src/cci_severity_mapper.py` — no mapper changes.

---

## 17. Recommended Decision

**Recommended:** Approve this burn-in review plan as the source-of-truth observation criteria for `CCI-ROUTE-011` warning pilot.

**Recommended next phase after burn-in:**
- If burn-in passes: Phase H.17 / Phase I.16 — Error Promotion Readiness Review (planning-only until approved).
- If burn-in fails: Immediate rollback to advisory (config-only), then reassess.

**Open questions needing approval:**
1. Is 30 days the correct observation period, or should a shorter synthetic batch review be accepted?
2. Should a new H.16 regression runner be added to the 33-suite gate, or is the existing H.13/H.9/H.10 coverage sufficient?
3. Should `CCI-ROUTE-010` remain permanently advisory, or should a separate evidence-collection phase be planned?

---

End of Phase H.16 Warning Pilot Burn-In Review Plan.
