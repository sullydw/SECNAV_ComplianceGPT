# Phase H.13 / Phase I.12 — Feature-Flag/Config Support Implementation Checkpoint

**Commit:** `[TBD]` — `CCI: Add H.13 severity config support`  
**Planning Document:** `1759c9f` — `Docs: Fix markdown table formatting in Phase H.13 config plan`  
**Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Regression Gate:** 33 suites (32 existing + 1 new H.13 runner) — **33/33 PASS**  
**Date:** 2026-06-08

---

## What Was Implemented

### New Files Added

| File | Purpose |
|---|---|
| `src/cci_severity_mapper.py` | Shared severity mapper module. Reads `config/cci_enforcement_config.json`, resolves per-rule effective severity. Safe fallback to advisory on all error paths. |
| `config/cci_enforcement_config.json` | Tracked default config with explicit entries for `CCI-ROUTE-010` and `CCI-ROUTE-011`. Both set to `effective_severity: advisory`, `allow_override_up_to: error`. |
| `tools/run_phase_h13_config_regression.py` | 26-check targeted regression runner validating mapper, config, fallback behavior, ceiling clamp, and cross-phase runner preservation. |

### Modified Files

| File | Change |
|---|---|
| `src/cci_routing_validate.py` | Imported `cci_severity_mapper.effective_severity`. Modified `validate_cci_routing()` to route ROUTE-010/011 findings into `errors` (when configured as warning/error) or `warnings` (when advisory), preserving all existing behavior in default state. |
| `.gitignore` | Added `config/cci_enforcement_config.local.json` to prevent accidental local override commits. |

### Files NOT Modified

- `src/validator_runner.py` — unchanged; overall_pass logic remains `total_errors == 0`
- `src/context_resolver.py` — unchanged
- `src/pdf_v6_render.py` — unchanged
- `src/intake_orchestrator.py` — unchanged
- `src/correction_commands.py` — unchanged
- `src/correction_nl_commands.py` — unchanged
- `src/letter_model_v6.py` — unchanged
- `rules_v6/CCI/cci_ch2_routing_rules.json` — unchanged (catalog severity remains `error` for both rules)
- All existing regression runners — unchanged

---

## Behavior Summary

### Default State (No Severity Promotion)

With the tracked default config in place:

- `CCI-ROUTE-010` remains **advisory** — findings appended to `warnings`, no effect on `overall_pass`.
- `CCI-ROUTE-011` remains **advisory** — same behavior.
- All 32 existing regression suites pass unchanged.
- The new H.13 regression runner (26 checks) passes.

### Config-Driven Severity Mapping

The mapper supports three effective severity levels:

| Level | Behavior | Effect on `overall_pass` |
|---|---|---|
| `advisory` | Finding appended to `warnings` list with `(advisory)` prefix | None |
| `warning` | Finding appended to `errors` list | Causes `overall_pass = False` |
| `error` | Finding appended to `errors` list | Causes `overall_pass = False` |

### Safety Guarantees

1. **Missing config** → advisory fallback.
2. **Malformed JSON** → advisory fallback.
3. **Unknown schema version** → advisory fallback.
4. **Unknown rule ID** → advisory fallback.
5. **Unsupported severity string** → advisory fallback.
6. **Rule not in allowlist** → advisory fallback (override ignored).
7. **`effective_severity` > `allow_override_up_to`** → clamped to ceiling.
8. **Config `effective_severity` > catalog severity** → clamped to catalog ceiling.

### No Breaking Changes

- No existing fixtures changed behavior.
- No existing regression runners required modification.
- No renderer, layout, prompt-contract, command-layer, or intake changes.
- No approved/pending/session/evidence logs committed.
- No real command/user data committed.
- No background automation introduced.

---

## Regression Gate Results

| Runner | Status |
|---|---|
| run_c10_regression.py | PASS |
| run_c7_phase1_regression.py | PASS |
| run_c8_regression.py | PASS |
| run_c9_regression.py | PASS |
| run_cci_acronym_regression.py | PASS |
| run_cci_audit_regression.py | PASS |
| run_cci_date_time_regression.py | PASS |
| run_cci_personnel_regression.py | PASS |
| run_cci_poc_regression.py | PASS |
| run_cci_ref_encl_regression.py | PASS |
| run_cci_routing_regression.py | PASS |
| run_cci_subject_regression.py | PASS |
| run_context_schema_regression.py | PASS |
| run_correction_classify_regression.py | PASS |
| run_correction_command_regression.py | PASS |
| run_correction_implementation_regression.py | PASS |
| run_correction_nl_command_regression.py | PASS |
| run_correction_pending_regression.py | PASS |
| run_correction_profile_promotion_regression.py | PASS |
| run_correction_regression.py | PASS |
| run_correction_review_regression.py | PASS |
| run_correction_session_regression.py | PASS |
| run_intake_regression.py | PASS |
| run_phase_h10_from_line_evidence_regression.py | PASS |
| **run_phase_h13_config_regression.py** | **PASS** |
| run_phase_h2_subject_acronym_validator_regression.py | PASS |
| run_phase_h3_second_rule_catalog_regression.py | PASS |
| run_phase_h4_routing_office_code_validator_regression.py | PASS |
| run_phase_h6_routing_office_code_evidence_regression.py | PASS |
| run_phase_h8_third_rule_catalog_regression.py | PASS |
| run_phase_h9_from_line_validator_regression.py | PASS |
| run_pilot_subject_acronym_rule_catalog_regression.py | PASS |
| run_profile_regression.py | PASS |

**Total: 33/33 PASS**

---

## Open Questions / Next Steps

1. **Severity promotion for ROUTE-010/011** remains deferred. A future approved phase may change `effective_severity` from `advisory` to `warning` or `error` in the config file.
2. **Local override support** (`config/cci_enforcement_config.local.json`) is not yet implemented. The infrastructure supports it (gitignore entry present), but the mapper currently reads only the tracked default.
3. **Auto-reload vs. read-on-demand** is currently read-on-demand (no caching). If performance becomes a concern, a cached reload mechanism could be added.
4. **Additional validators** (subject, ref/encl, date/time, personnel, POC, acronym) may import the mapper in future phases if advisory rules are added there.
5. **External config directory** (e.g., `~/.seccg/`) is not yet supported.

---

## Rollback Plan

| Scenario | Action |
|---|---|
| Config causes unexpected behavior | Revert `config/cci_enforcement_config.json` to default (advisory entries only). |
| Severity mapper causes crash | Revert `src/cci_routing_validate.py` to pre-H.13 version (remove import and severity branching). |
| Any unknown side effect | Git revert the H.13 implementation commit. All new files are tracked; `config/` can be deleted if needed. |

---

*End of checkpoint.*
