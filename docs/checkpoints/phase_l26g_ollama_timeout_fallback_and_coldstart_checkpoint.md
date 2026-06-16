# Phase L.26G Ollama Timeout Fallback and Cold-Start Headroom Checkpoint

**Date:** 2026-06-16  
**Baseline Commit:** `1a88d77`  
**Phase:** L.26G  
**Status:** Implementation complete

---

## Goal

Fix the timeout fallback loop bug and give Ollama enough headroom for cold model loads, so the local Ollama path actually works instead of silently returning `intent: unknown` after 30 seconds.

## Root Cause Confirmed

User observed:
- app launched correctly
- Ollama Local selected, model picked
- submitted prompt
- result: `Detected intent: unknown — Ollama request failed at http://localhost:11434/api/chat: TimeoutError: timed out`

Code inspection showed:
- `call_ollama_inference()` iterates `/api/chat` then `/api/generate`
- `TimeoutError` on `/api/chat` was caught by the generic `except Exception` handler at lines 167-176
- that handler **returned immediately** with a fail-closed JSON
- fallback to `/api/generate` **never executed**

Second factor:
- Ollama cold-start often takes 60-90 seconds the first time a model is loaded into GPU/CPU memory
- default timeout was 30.0 seconds
- this meant even a correct fallback would still likely time out

## Changes Made

### 1. Timeout fallback loop fix
File: `src/llm_provider_config.py`

Added explicit `except TimeoutError` before the generic `except Exception`:
- catches `TimeoutError` on `/api/chat`
- stores it in `last_error`
- **continues** to `/api/generate` instead of returning
- if `/api/generate` also times out, the accumulated last error is surfaced at the end

### 2. Cold-start headroom
File: `src/llm_provider_config.py`

Changed Ollama timeout logic in `LLMProviderConfig.__init__`:
- old: `<= 0` → 30.0
- new: `<= 0` → 120.0, and `< 60` → 120.0
- this gives cold model loads sufficient time without requiring user intervention

### 3. UI cold-start notice
File: `app_streamlit_llm_guided_intake.py`

Added `st.caption` under the Ollama model selector:
> "Note: First inference may take 60–90 seconds while the model loads into memory. Wait for the response — this is normal for local Ollama."

## Safety Boundaries Preserved

- Mock/default provider unchanged
- BuilderSession remains source of truth
- Fail-closed behavior unchanged (both endpoints must fail before unknown)
- No renderer/layout changes
- No CCI severity/config changes
- No external network by default
- No secrets displayed

## Regression Coverage

New runner:
- `tools/run_phase_l26g_ollama_timeout_fallback_and_coldstart_regression.py`

Checks:
- TimeoutError caught with `continue` in loop
- Ollama default timeout raised to 120s
- Minimum timeout capped at 120s
- App shows cold-start caption
- No renderer/CCI changes

Result: 8/8 PASS

## Recommended Next Phase

`Phase L.27 Streamlit Launcher Manual Verification`

Actually run `launch_secnav_streamlit_ollama.bat`, start Ollama, select a model, submit a complex prompt, and verify the response comes back after the cold-load wait instead of timing out at 30s.

## Notes

- Combined prior regression suites all still pass (rerun during this phase)
- GitHub Actions cannot be verified from this environment (`gh` CLI unavailable)
- No generated PDFs/logs committed
- No force-push; pushed `origin main` only
