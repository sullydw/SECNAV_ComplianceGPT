# Phase L.26E Ollama Provider and Model Picker Checkpoint

**Date:** 2026-06-16  
**Baseline Commit:** `85e6d66`  
**Phase:** L.26E  
**Status:** Implementation complete

---

## Goal

Add a provider/model selection experience in the Streamlit sidebar so the user can choose between mock mode, local Ollama models (with live discovery), and a future cloud/hosted option — without manually editing environment variables.

---

## Files Changed

| File | Change |
|------|--------|
| `app_streamlit_llm_guided_intake.py` | **Modified** — Added `Provider & Model` picker in sidebar with three options: Mock / Offline, Ollama Local, Ollama Cloud / Hosted. For Ollama Local, queries `localhost:11434/api/tags` via `list_ollama_models()` and shows a dropdown of installed models. Shows `ollama pull llama3.2` instructions if no models found. Cloud placeholder shows "not yet configured" with env var instructions. `_run_mediation()` now respects UI session state (`selected_provider`, `selected_model`) over env defaults. |
| `src/llm_provider_config.py` | **Modified** — Added `list_ollama_models()` function using stdlib `urllib` to query `localhost:11434/api/tags`. Returns sorted list of model names, empty list on any error (fail-closed). |
| `tools/run_phase_l23_streamlit_intake_import_smoke.py` | **Modified** — Updated required labels: replaced "Provider Status" with "Provider & Model" to match new UI. |
| `tools/run_phase_l26e_ollama_model_picker_regression.py` | **New** — 18-check regression verifying all provider options present, model dropdown exists, `list_ollama_models` function, localhost URL, fail-closed behavior, no API key display, mock default, UI selection respected, cloud fail-closed, launchers exist, no renderer/CCI changes. |
| `docs/checkpoints/phase_l26e_ollama_provider_model_picker_checkpoint.md` | **New** — This document. |
| `docs/PROJECT_STATUS.md` | L.26E entry added. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.26E entry added; next phase updated. |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — L.26E artifacts added. |

---

## Provider/Model Picker Behavior

### Mock / Offline (default)
- No network required
- Deterministic offline parser
- Selected by default on first load

### Ollama Local
- Queries `localhost:11434/api/tags` for installed models
- Dropdown shows all available models (e.g., `llama3.2`, `mistral`, etc.)
- If Ollama not running: shows warning + `ollama pull llama3.2` instructions
- If Ollama running but no models: shows same instructions
- Selected model passed to `_run_mediation()` via `LLMProviderConfig(provider="ollama", model=selected_model)`

### Ollama Cloud / Hosted
- Visible as a placeholder option
- Shows "not yet configured" message
- Displays env var setup instructions
- Fail-closed: no live cloud calls unless explicitly configured

---

## Manual Test Instructions

1. Start Ollama: `ollama serve`
2. Pull at least one model: `ollama pull llama3.2`
3. Launch app: double-click `launch_secnav_streamlit.bat` (or `.ps1`)
4. In the sidebar:
   - Select `Ollama Local`
   - Pick `llama3.2` from the dropdown
5. Confirm provider status shows `ollama` and model shows `llama3.2`
6. Type a complex message like:
   "I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN"
7. Check the debug panel — mediator output should show Ollama-generated JSON
8. Verify adapter still validates output before ingestion

---

## Runner/Test Results

| Runner | Result |
|--------|--------|
| L.26E model picker | 18/18 PASS |
| L.26D Ollama launcher | 19/19 PASS |
| L.26C Ollama provider | 11/11 PASS |
| L.26B debug panel | 10/10 PASS |
| L.26A hotfix | 7/7 PASS |
| L.26 launcher | 12/12 PASS |
| L.24 usability | 16/16 PASS |
| L.23 import smoke | 10/10 PASS |
| H.13 config | 27/27 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| Intake regression | 45/45 PASS |
| H.4 validator | 18/18 PASS |

**367/367 PASS + 1 optional smoke SKIP**

---

## Recommended Next Phase

`Phase L.27 Streamlit Launcher Manual Verification`

---
