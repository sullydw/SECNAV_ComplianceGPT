# Phase L.26I — Robust Ollama Localhost Detection Hotfix

## Problem

Ollama was running, but the Streamlit app/launcher reported:

```
Ollama does not appear to be running. Start Ollama, then try again.
```

The app and launchers only checked `http://localhost:11434/api/tags`. On Windows, `localhost` may resolve differently from `127.0.0.1`, causing a false-negative when Ollama is actually reachable.

## Fix

1. **Shared endpoint list** (`src/llm_provider_config.py`):
   - Added `OLLAMA_HOSTS = ["127.0.0.1", "localhost"]`
   - Default `OLLAMA_*_URL` constants now use `127.0.0.1`
   - `ollama_service_status()` probes both hosts in order, returning `active_endpoint` and `tried_endpoints`
   - Added `_discover_working_ollama_host()` helper
   - `call_ollama_inference()` discovers the working host first, then derives per-host `chat_url` and `generate_url`

2. **Streamlit UI** (`app_streamlit_llm_guided_intake.py`):
   - Shows `active_endpoint` caption when Ollama models are found
   - When no models found, shows expandable **Troubleshooting** panel with:
     - Tried endpoints (with `curl` commands)
     - `ollama serve`
     - `ollama list`
     - `ollama pull llama3.2`

3. **Ollama launchers**:
   - Both `.bat` and `.ps1` now probe `127.0.0.1:11434` **first**, then `localhost:11434`
   - Prints per-endpoint `[OK]` or `[FAIL]` status
   - On failure, prints troubleshooting commands
   - On success, prints `Endpoint: <host>:11434`
   - Does **not** silently fall back to mock provider

## Files Changed

- `src/llm_provider_config.py` — endpoint list, discovery, inference host selection
- `app_streamlit_llm_guided_intake.py` — active endpoint display, troubleshooting panel
- `launch_secnav_streamlit_ollama.bat` — dual endpoint check + troubleshooting output
- `launch_secnav_streamlit_ollama.ps1` — dual endpoint check + troubleshooting output

## Verification

- `tools/run_phase_l26i_ollama_localhost_detection_regression.py`: **24/24 PASS**

## Downstream Regression

All prior phase runners must continue to pass:
- L.26H, L.26G, L.26E, L.26D, L.26, L.24, L.23, H.13, K.3, H.4

## Next Phase

Phase L.27 — Streamlit Launcher Manual Verification (physical double-click test on Windows)

## Commit

```
Fix: Robustly detect local Ollama endpoint
```
