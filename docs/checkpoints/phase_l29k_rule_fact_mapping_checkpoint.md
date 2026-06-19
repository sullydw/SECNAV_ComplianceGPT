# Phase L.29K Checkpoint: Rule-to-Fact Mapping File

**Phase:** L.29K — Rule-to-Fact Mapping File Creation  
**Date:** 2026-06-19  
**Commit:** `72be568`  
**Status:** Complete

## Artifacts Created

1. **`rules_v6/CCI/cci_unresolved_fact_map.json`** — RULE_FACT_MAP_V1 mapping file
2. **`tools/run_phase_l29k_rule_fact_map_regression.py`** — 23-check regression script

## What Was Done

- Created a machine-readable mapping file connecting existing mined rules and field policies to unresolved-fact detection.
- Mappings were generated programmatically from `cci_intake_field_policy.json` — no manual invention of field lists.
- Added rule-specific mappings from `cci_ch7_subject_rules.json` (subject rules), `cci_ch2_routing_rules.json` (routing rules), and `V-series.json` (conditional distribution rules).
- All mappings include traceable `rule_id`, `source_file`, `evidence.policy_path`, and `evidence.rule_summary`.
- No static command/unit names appear in structural mapping data.
- No source/renderer/CCI config modified.

## Coverage

| Category | Count |
|----------|-------|
| Total mappings | 30 |
| Blocking | 14 |
| Recommended | 15 |
| Optional | 1 |
| Doc types covered | 9 (all 8 policy-defined + letterhead_memo) |

## Source files consumed

- `rules_v6/CCI/cci_intake_field_policy.json`
- `rules_v6/CCI/cci_intake_questions.json` (for question templates)
- `rules_v6/CCI/cci_ch7_subject_rules.json`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `rules_v6/V-series.json`

## Regression Results

- L.29K regression: 23/23 PASS
- L.29C regression: 23/23 PASS
- L.28 regression: 25/25 PASS
- K.3 regression: 11/11 PASS

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `rules_v6/CCI/cci_unresolved_fact_map.json` | Created | 760 lines |
| `tools/run_phase_l29k_rule_fact_map_regression.py` | Created | 196 lines |
| `docs/checkpoints/phase_l29k_rule_fact_mapping_checkpoint.md` | Created | 55 lines |
| `docs/PROJECT_STATUS.md` | Modified | +2 lines |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Modified | +4/-1 lines |

## No Source Changes

- `src/` — no changes
- `renderer/layout` — no changes
- `validator/CCI config` — no changes
- `docs/BOOTSTRAP.md` — untouched
- `docs/HERMES_INSTRUCTIONS.md` — untouched
