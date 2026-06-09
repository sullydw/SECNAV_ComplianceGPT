# Phase H.18 / Phase I.17 — Burn-In Observation Template for CCI-ROUTE-011 Warning Pilot

**Date:** 2026-06-08  
**Template Commit:** See git log for `Docs: Add H.18 burn-in observation template`  
**H.15 Activation Commit:** `18fc9bf` — `CCI: Start H.15 ROUTE-011 warning pilot`  
**H.16 Burn-In Regression Commit:** `7e42f64` — `CCI: Add H.16 ROUTE-011 burn-in regression`  
**H.16 Review Approval Commit:** `95ac852` — `Docs: Record H.16 burn-in review approval`  
**H.17 Day 0 Checkpoint Commit:** `0b4c669` — `Docs: Record H.17 day zero burn-in checkpoint`  
**Current Functional Baseline:** `7e42f64`  
**Regression Set:** 34 suites  
**Status:** Documentation-only template. No code changes. No real data committed.

---

## 1. Observation Period

### 1.1 Timeline

| Milestone | Commit | Date | Purpose |
|---|---|---|---|
| Warning pilot activation | `18fc9bf` | 2026-06-08 | `CCI-ROUTE-011.effective_severity` changed to `warning` |
| Burn-in regression added | `7e42f64` | 2026-06-08 | 90 synthetic fixtures + 96-check runner |
| Burn-in review approved | `95ac852` | 2026-06-08 | H.16 regression approved as stable baseline |
| Day 0 checkpoint | `0b4c669` | 2026-06-08 | Day 0 documentation; 34/34 gate PASS |
| **This template** | H.18 commit | 2026-06-08 | Observation template for manual/staged review |
| Day ~15 checkpoint (optional) | TBD | ~2026-06-23 | Mid-burn-in review if noteworthy |
| Day 30 checkpoint (target) | TBD | ~2026-07-08 | End-of-observation decision point |

### 1.2 Observation Scope

- Monitor `CCI-ROUTE-011` behavior at `warning` severity on standard letters.
- Verify no unintended side effects on non-standard documents.
- Track operator experience with `window_envelope` tagging.
- Collect evidence for the eventual end-of-observation decision.

### 1.3 What Is NOT Allowed During Observation

- No error promotion for any rule.
- No config changes without explicit user approval.
- No validator, catalog, renderer, prompt, or command-layer modifications.
- No automatic enforcement from approved/pending logs.
- No background automation or cron jobs.

---

## 2. Config State Checklist

Before each observation session or checkpoint, verify the config matches the expected state:

| Check | Expected Value | Verification Method |
|---|---|---|
| `CCI-ROUTE-011.effective_severity` | `warning` | Read `config/cci_enforcement_config.json` |
| `CCI-ROUTE-010.effective_severity` | `advisory` | Read `config/cci_enforcement_config.json` |
| `global_default` | `advisory` | Read `config/cci_enforcement_config.json` |
| `_allowlist` contains `CCI-ROUTE-011` | yes | Read `config/cci_enforcement_config.json` |
| No error-level promotion exists | yes | Confirm no rule has `"error"` in `effective_severity` |
| Config file is tracked in git | yes | `git status` should show no uncommitted changes to config |

**If any check fails, stop observation and investigate before continuing.**

---

## 3. Regression Checklist

Before recording any observation findings, confirm the regression gate is green:

| Priority | Runner | Checks (approx) | Expected Result |
|---|---|---|---|
| Required | `tools/run_phase_h16_route011_burnin_regression.py` | 96 | PASS |
| Required | `tools/run_phase_h13_config_regression.py` | 27 | PASS |
| Required | `tools/run_phase_h9_from_line_validator_regression.py` | 18 | PASS |
| Required | `tools/run_phase_h10_from_line_evidence_regression.py` | 39 | PASS |
| Required | Full 34-suite gate | 34 suites | ALL PASS |

**Use the explicit Miniconda Python:**
```bat
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h16_route011_burnin_regression.py
```

If any required runner fails, resolve the regression before proceeding with observation.

---

## 4. Observation Categories

When reviewing payloads (synthetic, sanitized, or real with PII removed), classify each case into one of these categories:

| Category | Description | Expected `CCI-ROUTE-011` Behavior |
|---|---|---|
| A — Standard letter with valid `from` | `doc_type` = standard, `from` is non-empty real string | No finding |
| B — Standard letter missing `from` | `doc_type` = standard, `from` absent/null/empty/whitespace | Warning in `errors` |
| C — Null `from` | `"from": null` | Warning in `errors` |
| D — Empty string `from` | `"from": ""` | Warning in `errors` |
| E — Whitespace-only `from` | `"from": "   "` or `\t` / `\n` only | Warning in `errors` |
| F — Non-standard document | `doc_type` = memo, endorsement, joint, MAL, MFR, etc. | No finding (excluded) |
| G — Missing `doc_type` | `doc_type` absent or unknown | No finding (skip) |
| H — Window envelope with tag | `window_envelope: true`, no `from` | No finding (suppressed) |
| I — Window envelope with tag + `from` | `window_envelope: true`, `from` present | No finding |
| J — Window-envelope-like without tag | Looks like window envelope but `window_envelope` absent/missing | Warning in `errors` (operator risk) |
| K — Realistic synthetic/sanitized | Representative Navy/Marine Corps payload | Varies by case |

**Record each observation with:**
- Category letter
- Synthetic fixture reference or sanitized description
- Expected vs actual result
- Any anomaly notes

---

## 5. Metrics to Record Manually

Use this table (copy to local notes, not committed) for each observation batch:

| Metric | Tally | Notes |
|---|---|---|
| Total payloads reviewed | ___ | Count all cases examined |
| `CCI-ROUTE-011` warnings triggered | ___ | Any appearance in `errors` |
| Expected triggers (Categories B, C, D, E, J) | ___ | Should match warnings triggered |
| Unexpected triggers (Categories A, F, G, H, I) | ___ | **False positives — escalate immediately** |
| False negatives (Categories B-E/J with no warning) | ___ | **Bug — escalate immediately** |
| Window-envelope tagging issues | ___ | Category J cases; operator confusion |
| Rollback triggers encountered | ___ | Any anomaly requiring severity rollback |
| Operator questions/feedback | ___ | Free-text notes |
| Exotic whitespace cases | ___ | ZWS, BOM, other invisible chars |

### 5.1 What Constitutes a False Positive

A false positive occurs when `CCI-ROUTE-011` appears in `errors` for:
- A standard letter that **does** have a real, visible `from` line.
- A non-standard document type that should be excluded.
- A window-envelope letter with `window_envelope: true`.

**Any confirmed false positive is a rollback trigger.**

### 5.2 What Constitutes a False Negative

A false negative occurs when `CCI-ROUTE-011` **does not** appear in `errors` for:
- A standard letter with a genuinely missing, null, empty, or whitespace-only `from` field.
- When the payload is clearly a standard letter and the `from` field is absent.

**Any confirmed false negative is a bug and requires immediate investigation.**

---

## 6. Decision Thresholds

At the end of each observation batch or checkpoint, apply these thresholds:

| Decision | Threshold | Action |
|---|---|---|
| **Continue warning pilot** | Zero unexpected triggers; zero false positives; zero false negatives; operator feedback neutral or positive | Maintain `warning`. Schedule next checkpoint. |
| **Rollback to advisory** | Any confirmed false positive; any confirmed false negative; operator reports blocking legitimate workflow; config regression | Immediately restore `effective_severity` to `advisory`. Document rollback. |
| **Extend observation** | Edge cases discovered that need more samples; exotic whitespace concerns; insufficient payload variety reviewed | Maintain `warning`. Extend observation period. Add fixtures if needed. |
| **Block future error promotion** | Any false positive or false negative during warning pilot | Error promotion is **permanently blocked** for this rule until the root cause is fixed and a new burn-in period completes. |
| **Consider future error-promotion review** | 30+ days of clean warning pilot; zero false positives; zero false negatives; operator comfort with current behavior; explicit user request | Create **separate** H.19 / I.18 planning document. Do not promote without planning + approval. |

---

## 7. Data-Handling Rules

### 7.1 What May Be Committed

- This template document (sanitized, no real data).
- Updated status/progress references in `docs/PROJECT_STATUS.md` and planning docs.
- Synthetic fixture additions (if observation reveals gaps).
- New regression runners (if observation reveals test gaps).

### 7.2 What Must NOT Be Committed

- Real command or user contact data.
- Real payload content with PII, unit identifiers, or operational details.
- Approved/pending/session/evidence logs from local storage.
- Operator notes containing real correspondence content.
- Unsanitized error reports or screenshots.

### 7.3 Sanitization Rules for Examples

If an observation example is documented in any project file:

- Replace all real names with `COMMANDING OFFICER, USS EXAMPLE` or equivalent.
- Replace real unit codes with `N00`, `N1`, `SUP`, or generic placeholders.
- Replace real hull numbers with `CVN-68`, `DDG-1000`, etc. (generic but plausible).
- Replace real dates with `2026-06-08` or similar.
- Remove any email addresses, phone numbers, or mailing addresses.
- Mark the example as `synthetic` or `sanitized` in the documentation.

---

## 8. Rollback Instructions

### 8.1 Immediate Rollback (Emergency)

If a false positive, false negative, or operator emergency requires immediate deactivation:

1. Edit `config/cci_enforcement_config.json`.
2. Change:
   ```json
   "CCI-ROUTE-011": {
     "effective_severity": "warning",
     ...
   }
   ```
   to:
   ```json
   "CCI-ROUTE-011": {
     "effective_severity": "advisory",
     ...
   }
   ```
3. Save the file.
4. Run the required regressions:
   ```bat
   C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h13_config_regression.py
   C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_h16_route011_burnin_regression.py
   ```
5. If regressions pass, the rollback is complete.
6. Document the rollback in a new checkpoint document (e.g., `docs/checkpoints/phase_h18_route011_rollback_checkpoint.md`).

### 8.2 No Validator/Catalog/Renderer Changes Needed

Rollback is **config-only**. No code changes are required because the validator reads `effective_severity()` at runtime.

### 8.3 Post-Rollback Regression Gate

After any rollback, the full 34-suite gate must still pass to confirm no unintended side effects.

---

## 9. Future Review Checklist

At the end of the observation period (or at any checkpoint), answer these questions:

### 9.1 Evidence Supporting Continued Warning

- [ ] All expected triggers were caught correctly.
- [ ] No false positives observed.
- [ ] No false negatives observed.
- [ ] Window-envelope suppression behaved correctly.
- [ ] Non-standard document exclusion behaved correctly.
- [ ] Operator feedback was neutral or positive.
- [ ] Regressions remained green throughout observation.

### 9.2 Evidence Blocking Error Promotion

- [ ] Any false positive observed → **blocks error promotion**.
- [ ] Any false negative observed → **blocks error promotion**.
- [ ] Operator reports confusion or blocking → **blocks error promotion**.
- [ ] Exotic whitespace not caught → document as known limitation; does not block error promotion alone, but requires hardening before promotion.
- [ ] Insufficient real-world payload variety → **blocks error promotion** until more evidence collected.

### 9.3 Evidence That Might Justify Future Error-Review Planning

- [ ] 30+ days of clean warning pilot.
- [ ] Zero false positives across all observation batches.
- [ ] Zero false negatives across all observation batches.
- [ ] Operator comfort confirmed (if asked).
- [ ] No regression failures during observation period.
- [ ] No config regressions during observation period.

**Even if all boxes are checked, error promotion requires:**
1. A separate Phase H.19 / I.18 planning document.
2. Explicit user approval.
3. Implementation of the plan.
4. A new regression gate after implementation.
5. A review checkpoint after regression.

---

## 10. Related Documents

| Document | Role |
|---|---|
| `docs/planning/phase_h18_route011_burnin_observation_template.md` | This template |
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

## 11. What Was NOT Modified in This Template

This template is documentation-only. No code changes occurred:

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

End of Phase H.18 / Phase I.17 Burn-In Observation Template.
