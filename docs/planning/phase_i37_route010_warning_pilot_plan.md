# Phase I.37 / Phase J.1 — Controlled Warning Pilot Plan for CCI-ROUTE-010

**Rule under review:** `CCI-ROUTE-010`  
**Source:** SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General  
**Rule summary:** If the office code is composed only of numbers, add the word `Code` before the numbers. Do not add `Code` before office codes that start with a letter, such as `N` or `SUP`.  
**Document type:** Planning-only — no config change, no severity change, no code change  
**Date:** 2026-06-10  
**Implementation baseline:** `084ce64` (H.13 stable baseline) / `ee4f3a2` (H.28 stable baseline)  
**Regression baseline:** 35 suites

---

## 1. Current State

| Item | Value |
|---|---|
| `CCI-ROUTE-010.effective_severity` | `advisory` |
| `CCI-ROUTE-011.effective_severity` | `warning` (active warning pilot) |
| `global_default` | `advisory` |
| Regression baseline | 35 suites |
| Error promotion authorized | **No** |
| `CCI-ROUTE-010` catalog severity | `error` (validator currently overrides to advisory via config) |
| `CCI-ROUTE-010` enforcement type | `deterministic` |
| `CCI-ROUTE-010` validator | `cci_routing` |
| `CCI-ROUTE-010` allowlist status | Allowlisted in `config/cci_enforcement_config.json` |
| `CCI-ROUTE-010` allow_override_up_to | `error` |

The `CCI-ROUTE-011` warning pilot (Phase H.15) has been active since commit `18fc9bf`. It was paused for repeated fixture-only observation in Phase H.34/H.35 and remains active pending operator feedback. The `CCI-ROUTE-010` rule has remained at `advisory` throughout.

---

## 2. Existing Implementation and Evidence

### Rule Catalog
- `rules_v6/CCI/cci_ch2_routing_rules.json` contains `CCI-ROUTE-010` with full provenance:
  - `source_location`: `Chapter 7, paragraph 7-2.7a, To Line, General`
  - `source_quote`: exact manual text preserved
  - `effective_date`: `2026-06-04`
  - `added_by_implementation_id`: `agr_20260604_7b5d44a2`
  - `implementation_status`: `active`

### Validator Logic
- `src/cci_routing_validate.py` contains `_check_office_code_prefix()` (Phase H.4).
- **Check A:** numeric-only office code missing `Code` prefix → triggers.
- **Check B:** letter-starting office code improperly prefixed with `Code` → triggers.
- Scope: `to` and `via` lines; `copy_to` excluded.
- False-positive controls: comma delimiter or parenthetical enclosure required; length guard (1–10 chars); no trigger on trailing numbers without delimiter.

### Config Allowlist
- `config/cci_enforcement_config.json` allowlists `CCI-ROUTE-010` and `CCI-ROUTE-011`.
- `CCI-ROUTE-010` override: `effective_severity: advisory`, `allow_override_up_to: error`.
- `CCI-ROUTE-011` override: `effective_severity: warning`, `allow_override_up_to: error`.

### Regression Suites
- **H.4 validator regression:** `tools/run_phase_h4_routing_office_code_validator_regression.py` — 18 checks.
- **H.6 evidence regression:** `tools/run_phase_h6_routing_office_code_evidence_regression.py` — 15 checks (20 negative + 10 positive fixtures).
- **H.13 config regression:** `tools/run_phase_h13_config_regression.py` — 27 checks (includes temp warning/error config tests for both ROUTE-010 and ROUTE-011).
- Full 35-suite gate verified PASS at current baseline.

---

## 3. Proposed Pilot

If approved in a future Phase I.38 / Phase J.2 review, the activation would be a **single-line config change only**:

```json
"CCI-ROUTE-010": {
  "effective_severity": "warning",
  "allow_override_up_to": "error",
  "reason": "Office code prefix rule; warning pilot active in Phase I.39 / Phase J.3",
  "snapshot_id": "cfg_20260610_warning"
}
```

**What does NOT change:**
- Validator logic (`src/cci_routing_validate.py`)
- Rule catalog (`rules_v6/CCI/cci_ch2_routing_rules.json`)
- Renderer / layout (`src/pdf_v6_render.py`)
- Prompt / context / intake / UI / command-flow
- Phase F / Phase G command layer
- Any fixture or runner (no new regression suite created for activation)

The validator already branches on `effective_severity()` via `cci_severity_mapper`. Changing the config value from `advisory` to `warning` moves `CCI-ROUTE-010` findings from the `warnings` list to the `errors` list, causing `validator_runner` `overall_pass=False` when the rule triggers.

---

## 4. Why Warning Pilot Is Reasonable

1. **Deterministic rule:** The source quote is unambiguous and supports a binary classification (numeric-only vs letter-starting).
2. **Exact source quote exists:** The catalog entry contains the full quoted text from SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a.
3. **Validator already detects numeric-only code without `Code`:** Check A is implemented and covered by 10 positive-control fixtures (H.6).
4. **Validator already detects letter-starting code incorrectly prefixed with `Code`:** Check B is implemented and covered by positive-control fixtures.
5. **Rule is already allowlisted for severity override:** `config/cci_enforcement_config.json` explicitly lists `CCI-ROUTE-010` in `_allowlist` with `allow_override_up_to: error`.
6. **Rollback is config-only:** Reverting `effective_severity` to `advisory` immediately restores prior non-blocking behavior.
7. **Precedent exists:** `CCI-ROUTE-011` warning pilot (H.15) used the identical activation pattern and has remained stable through 35-suite regression gates.

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| False positives on text that looks like an office code but is not | Medium | Medium | Comma/parenthesis delimiter guard already limits scope; 20 negative H.6 fixtures cover common non-candidates. |
| Addressees with unusual office-code formats (e.g., hyphenated, alphanumeric mixed) | Low | Low | Length guard and tokenization already handle most cases; new patterns can be added to negative fixtures if discovered. |
| Parenthetical vs comma-delimited parsing limits | Low | Medium | Both forms are explicitly supported; unsupported delimiters do not trigger (safe default). |
| Mixed Navy / Marine Corps formatting expectations | Low | Medium | Rule applies to all component scopes per catalog; if service-specific exceptions emerge, config can be scoped or component filters tightened. |
| Possibility that `Code` wording belongs only in certain addressee contexts | Low | High | Source quote says "To Line, General," implying universal To-line applicability. If evidence contradicts this, severity can be rolled back immediately. |
| Validator currently does not inspect `copy_to` | N/A | N/A | Out of scope by design; copy-to office-code validation is not proposed in this phase. |

---

## 6. Required Burn-In Before Activation

Before any activation commit, the following must be rerun and verified PASS:

1. **H.4 office-code validator regression** (`tools/run_phase_h4_routing_office_code_validator_regression.py`) — 18/18 PASS.
2. **H.6 office-code evidence regression** (`tools/run_phase_h6_routing_office_code_evidence_regression.py`) — 15/15 PASS.
3. **H.13 config regression** (`tools/run_phase_h13_config_regression.py`) — 27/27 PASS (temp warning config tests prove the plumbing already works for ROUTE-010).
4. **Full 35-suite gate** — all existing suites must PASS with **default config unchanged** (advisory for ROUTE-010, warning for ROUTE-011).

Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for all runs.

---

## 7. Required Post-Activation Checkpoint

If activation is approved in a later phase, the following checkpoint artifacts must be created:

1. **Warning pilot checkpoint document** (`docs/checkpoints/phase_i39_route010_warning_pilot_checkpoint.md` or equivalent):
   - Config diff (one-line `effective_severity` change).
   - Regression results (H.4, H.6, H.13, full 35-suite gate).
   - Date of activation.
   - Burn-in clock start date.
   - Known limitations.
   - Decision: continue / pause / rollback.
2. **Rollback path documented** in the same checkpoint:
   - Restore `effective_severity` to `advisory`.
   - Rerun H.13 config regression.
   - Rerun H.4 / H.6 office-code regressions.
   - Rerun full gate if needed.

---

## 8. Rollback Procedure

If the warning pilot produces unacceptable false positives or operator feedback demands reversal:

1. Edit `config/cci_enforcement_config.json`:
   - Change `CCI-ROUTE-010.effective_severity` back to `advisory`.
   - Update `reason` and `snapshot_id` to reflect rollback.
2. Rerun `tools/run_phase_h13_config_regression.py` — verify 27/27 PASS.
3. Rerun `tools/run_phase_h4_routing_office_code_validator_regression.py` — verify 18/18 PASS.
4. Rerun `tools/run_phase_h6_routing_office_code_evidence_regression.py` — verify 15/15 PASS.
5. Rerun full 35-suite gate — verify all PASS.
6. Commit rollback with `Docs: Rollback ROUTE-010 to advisory` or `CCI: Rollback ROUTE-010 warning pilot`.
7. Create rollback checkpoint document.

No validator, catalog, renderer, prompt, or command-layer changes are required for rollback.

---

## 9. Explicit Prohibitions

This planning phase **does not authorize** any of the following:

- [ ] No config change in this planning phase.
- [ ] No severity change in this planning phase.
- [ ] No error promotion for `CCI-ROUTE-010` or any other rule.
- [ ] No rollback execution in this planning phase.
- [ ] No validator changes (`src/cci_routing_validate.py` remains untouched).
- [ ] No catalog changes (`rules_v6/CCI/cci_ch2_routing_rules.json` remains untouched).
- [ ] No renderer / layout changes (`src/pdf_v6_render.py` remains untouched).
- [ ] No prompt / context / intake / UI / command-flow changes.
- [ ] No Phase F / Phase G command-layer changes.
- [ ] No logs or unsanitized material committed.
- [ ] Do not read or modify `docs/BOOTSTRAP.md`.
- [ ] Do not modify `docs/HERMES_INSTRUCTIONS.md`.

All of the above remain in force until explicitly approved in a future review phase.

---

## 10. Recommended Next Phase

**Phase I.38 / Phase J.2 — CCI-ROUTE-010 Warning Pilot Plan Review**

Scope: read-only review of this planning document. Decision options:
- **Approve:** Proceed to Phase I.39 / Phase J.3 activation (config-only change + checkpoint).
- **Defer:** Hold at advisory pending additional evidence or operator feedback.
- **Reject:** Keep `advisory` indefinitely; update `reason` field in config if needed.

Constraints for any next phase:
- Planning documents must be created and approved before any code changes.
- All 35 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.

---

End of Phase I.37 / Phase J.1 Warning Pilot Plan.
