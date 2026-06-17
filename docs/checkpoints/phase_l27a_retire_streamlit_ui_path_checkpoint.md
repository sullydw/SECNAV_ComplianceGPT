# Phase L.27A Checkpoint — Retire Streamlit Web UI Path and Preserve Builder Core

## Summary

User decision to stop investing in the Streamlit/Ollama web UI direction.
All Streamlit/Ollama UI artifacts were removed. Core builder modules were
preserved for future reuse (e.g., Hermes-facing tool or non-Streamlit CLI).

## Decision

The Streamlit/Ollama web UI path did not prove reliable enough for ongoing
investment. It is retired and no longer the active path. Future work should
explore a Hermes-facing tool or command-driven interaction model instead of
debugging or extending Streamlit.

## Safety Branch

`backup/streamlit-ui-retired-from-9c1af61`

Created from commit `9c1af61` before any retirement changes.

## Files Removed

- `app_streamlit_llm_guided_intake.py`
- `launch_secnav_streamlit.bat`
- `launch_secnav_streamlit.ps1`
- `launch_secnav_streamlit_ollama.bat`
- `launch_secnav_streamlit_ollama.ps1`
- `docs/demo/streamlit_guided_intake_manual_demo_script.md`
- Checkpoint docs for L.23, L.24, L.25, L.26, L.26A, L.26B, L.26C, L.26D,
  L.26E, L.26F, L.26G, L.26H, L.26I, L.26J, L.26K, L.26L, L.26M
- Regression runners for the same phases

## Files Preserved

- `src/llm_provider_config.py`
- `src/llm_builder_mediator.py`
- `src/conversational_builder.py`
- All renderer/layout modules
- All CCI config/severity/catalog modules
- All validator and command-layer modules

## Tracker Updates

- `docs/PROJECT_STATUS.md` — Replaced L.23–L.26M entries with a single L.27A
  entry; Streamlit UI path marked as retired.
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — Replaced
  L.23–L.26M block with L.27A entry; next phase updated to L.28.

## Core Changes

Only deletions of Streamlit/Ollama-specific UI files.
No source-code modifications to core builder, renderer, validator, config, or
command modules.

## Regression Results

- `tools/run_phase_l27a_retire_streamlit_ui_path_regression.py`: 10/10 PASS

Core regression runners may show harness-level failures (Check 17 in H.4,
Check 21 in H.13) because git-diff allowlists still expect the removed Streamlit
files to exist. These are harness cosmetics, not core regressions. They were
patched to allow the expected deletions for this phase.

## Confirmed Unchanged

- No renderer/layout file modified.
- No CCI config/severity file modified.
- No rule promotion.
- `docs/BOOTSTRAP.md` untouched.
- `docs/HERMES_INSTRUCTIONS.md` untouched.

## Future Direction

Recommended next phase:
**Phase L.28 Conversational Builder Hermes Tool Integration**

Goal: expose the conversational builder (`BuilderSession` + adapter) as a
Hermes tool/plugin so intake and draft interaction happens through the
Hermes CLI/agent rather than through Streamlit.

## Commit

- Commit message: `Project: Retire Streamlit web UI path`
- Push target: `origin/main`
