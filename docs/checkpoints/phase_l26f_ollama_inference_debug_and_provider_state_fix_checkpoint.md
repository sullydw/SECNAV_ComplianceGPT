# Phase L.26F Ollama Inference Debug and Provider-State Fix Checkpoint

Date: 2026-06-16
Baseline Commit: `d910a87`
Phase: L.26F
Status: Implementation complete

## Goal

Fix the real Ollama manual-use path so the Streamlit app can distinguish between:
- Ollama service reachable for model discovery
- Ollama inference endpoint compatible and working
- provider/model UI selection actually reaching the backend

without changing renderer/layout, CCI config/severity, BuilderSession ownership, or mock default behavior.

## Root Cause Confirmed

The user symptom was:
- launcher opens correctly
- prompt is accepted
- app appears not to break down or pass along the request

Investigation reproduced a real backend failure:
- `/api/tags` reachable
- `/api/chat` returned HTTP 404 in the local environment
- adapter then safely degraded to `intent=unknown`
- no proposed key-value lines were ingested

A second issue was present in UI state propagation:
- `selected_model` persistence depended on a fragile condition
- provider/model dropdown changes were not guaranteed to update the effective mediation config consistently turn-to-turn

## Changes Made

### 1. Ollama inference fallback path
File: `src/llm_provider_config.py`

Added centralized helpers:
- `OLLAMA_TAGS_URL`
- `OLLAMA_CHAT_URL`
- `OLLAMA_GENERATE_URL`
- `call_ollama_inference(prompt, config)`
- `_ollama_http_get_json(...)`
- `_ollama_http_post_json(...)`
- `ollama_service_status()`
- `endpoint_fallback_order()`

Behavior:
- health-check local Ollama via `/api/tags`
- try `/api/chat` first
- if `/api/chat` returns HTTP 404, fall back to `/api/generate`
- if both fail, return controlled fail-closed `unknown` JSON
- preserve localhost-only behavior
- preserve no external network default

### 2. Provider/model state propagation fix
Files:
- `src/llm_provider_config.py`
- `app_streamlit_llm_guided_intake.py`

Added helpers:
- `ui_provider_config(...)`
- `selected_model_changed(...)`
- `selected_model_from_state(...)`
- `selected_provider_from_state(...)`
- `resolve_ollama_default_model(...)`
- `provider_debug_status(...)`

Behavior:
- sidebar selection now updates provider/model state deterministically
- selected model is synchronized into session state every turn
- `_run_mediation()` now resolves config from UI helpers instead of ad hoc local logic

### 3. Better provider/debug visibility
File: `app_streamlit_llm_guided_intake.py`

Added/updated:
- explicit `Provider Status` line in the sidebar
- saved `provider_status_snapshot` in session state
- more explicit Ollama-not-running / no-models-found warnings
- assistant transcript note when provider status indicates Ollama unavailable or inference failed

## Safety Boundaries Preserved

- Mock/default provider remains default
- BuilderSession remains source of truth
- all payload changes still route through `builder.ingest_user_message()`
- no renderer/layout changes
- no CCI severity/config changes
- no rule promotion
- no external cloud calls by default
- no secrets displayed

## Regression Coverage

New runner:
- `tools/run_phase_l26f_ollama_inference_debug_and_provider_state_fix_regression.py`

Checks include:
- `/api/chat` endpoint referenced
- `/api/generate` fallback referenced
- provider/model state helpers exist
- provider debug/status helpers exist
- app displays provider status
- app stores provider status snapshot
- state helpers persist provider/model correctly
- fail-closed JSON still returned safely when inference unavailable
- error explanation mentions endpoint/path on failure
- no renderer/layout controls added
- no CCI severity/config controls added

## Test Results

- L.26F regression: 24/24 PASS
- L.26E regression: 18/18 PASS
- L.26D regression: 19/19 PASS
- L.26C regression: 11/11 PASS
- L.26B regression: 10/10 PASS
- L.26A regression: 7/7 PASS
- L.24 regression: 16/16 PASS
- H.13 regression: 27/27 PASS
- K.3 regression: 11/11 PASS
- H.4 validator regression: 18/18 PASS

Combined total reported in this phase run: 151/151 PASS across the explicitly rerun suites.

## Manual Verification Notes

Recommended manual check after pull:
1. Start Ollama
2. Launch `launch_secnav_streamlit_ollama.bat`
3. In sidebar, confirm:
   - provider = Ollama Local
   - provider status reflects actual reachability
   - selected model can be changed
4. Submit a complex prompt
5. Check debug panel for:
   - backend explanation
   - proposed key-value lines
   - whether fallback worked or failed closed

## Recommended Next Phase

Phase L.27 Streamlit Launcher Manual Verification

Actually verify launcher + browser + local Ollama behavior end-to-end on Windows with a real model installed, then document any remaining environment-specific gaps.

## Notes

GitHub Actions could not be verified from this environment because `gh` CLI / web verification path remains unavailable here.

Warnings/tracebacks during this phase:
- none in the code path after fix
- one benign terminal-side `/usr/bin/bash: python: command not found` occurred earlier during investigation when probing with bare `python`; project runners continued using the pinned Miniconda Python path successfully.

No generated PDFs/logs were committed.

Local and GitHub project/documentation update pattern preserved.