# Phase L.29M Checkpoint: Detector-to-Tool Wiring

**Phase:** L.29M — Detector-to-Tool Wiring  
**Date:** 2026-06-19  
**Commit:** (to be filled after commit)  
**Status:** Complete

## Artifacts Modified

1. **`tools/hermes_secnav_tool.py`** — Added `detect-facts` command and handler
2. **`tools/run_phase_l29m_detect_facts_cli_regression.py`** — 37-check regression runner

## What Was Done

- Imported `detect_unresolved_facts` from `src/unresolved_fact_detector.py` into the CLI bridge.
- Added `cmd_detect_facts(args)` handler that:
  - Loads an existing session via `_load_session()`
  - Builds the current payload via `builder.build_payload()`
  - Optionally accepts `--text` and `--doc-type` overrides
  - Calls `detect_unresolved_facts(payload, user_text, doc_type)`
  - Returns JSON with `success`, `session_id`, `payload`, `unresolved_facts`, `validation_summary`, `warning_summary`
  - Does **not** mutate the session, create candidates, or apply anything
- Registered `detect-facts` subparser in argparse with `--session`, `--text`, `--doc-type`.
- Wired `detect-facts` into the handler dispatch dictionary.
- Verified backward compatibility: `start`, `status`, `validate`, `candidate-add`, `candidate-confirm`, `candidate-reject`, `apply-resolved` all still work.
- All prior regressions (L.29L, L.29K, L.29C, L.28) continue to pass.

## Regression Results

| Regression | Checks | Result |
|-----------|--------|--------|
| **L.29M** (new) | 37/37 | **PASS** |
| L.29L | 38/38 | PASS |
| L.29K | 23/23 | PASS |
| L.29C | 23/23 | PASS |
| L.28 | 25/25 | PASS |

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `tools/hermes_secnav_tool.py` | **Modified** | +34 lines (import + cmd + subparser + handler registration) |
| `tools/run_phase_l29m_detect_facts_cli_regression.py` | **Created** | ~280 lines / 10,558 bytes |
| `docs/checkpoints/phase_l29m_detector_to_tool_wiring_checkpoint.md` | **Created** | 52 lines |
| `docs/PROJECT_STATUS.md` | **Modified** | +2 lines |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | **Modified** | +4/-1 lines |

## No Source Changes

- `renderer/layout` — no changes
- `validator/CCI config` — no changes
- `src/unresolved_fact_detector.py` — no changes (only imported)
- `docs/BOOTSTRAP.md` — untouched
- `docs/HERMES_INSTRUCTIONS.md` — untouched
