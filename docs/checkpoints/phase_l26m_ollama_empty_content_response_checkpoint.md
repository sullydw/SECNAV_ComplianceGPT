# Phase L.26M — Ollama Empty Content Response Handling

## Scope

Diagnosed and repaired why Ollama (`qwen3.5:9b` and potentially other models) returns empty `message.content` when `format: "json"` is used. Added robust response extraction, alternate-field fallback, and a retry without `format: "json"` — all while still enforcing valid JSON before returning content.

## Problem

Manual retest of L.26L showed the mediator returning:

```
intent: "unknown"
explanation: "Ollama inference failed after trying all available endpoints ..."
```

Both `/api/chat` and `/api/generate` reported `empty_content`. The debug panel showed `timeout: 30.0s` despite prior work intending a 120s cold-start-safe timeout.

## Root Causes

1. **Response field mismatch**: Some Ollama models (especially `qwen3.5`) place the JSON response in a different field when `format: "json"` is active, or the `message.content` is empty because the model isn't populating it under the structured-output constraint.

2. **Hardcoded extractors**: The old code used a single lambda per endpoint (`parsed.get("message", {}).get("content", "")` for chat, `parsed.get("response", "")` for generate) with no alternate-field search.

3. **No retry without format**: If `format: "json"` caused the model to misbehave, there was no fallback attempt omitting the `format` key.

4. **Timeout regression**: The active `LLMProviderConfig` constructor (second definition in the file) did not enforce the 120s minimum timeout for Ollama, so `ui_provider_config(...)` fell back to `30.0s`.

## Fixes

### `src/llm_provider_config.py`

1. **Added `_extract_ollama_content(parsed, endpoint_type)` helper**  
   Tries multiple safe fields in order:

   - For `/api/chat`: `message.content` → `message.thinking` (only if valid JSON) → `response` → `content`
   - For `/api/generate`: `response` → `message.content` → `content` → `thinking` (only if valid JSON)

2. **Added `_diagnose_empty_content(parsed)` helper**  
   Captures `top_keys`, `message_keys`, `done`, `done_reason`, and a compact response preview for diagnostics.

3. **Added `_safe_response_preview(parsed)` helper**  
   Returns a truncated compact JSON preview for safe logging.

4. **Refactored `call_ollama_inference()` loop**  
   - Introduced `_attempt(endpoint, payload, endpoint_type, attempt_label)` inner function returning `str | None`.
   - Attempt order: `chat(format_json)` → `generate(format_json)` → `chat(no_format_json)` → `generate(no_format_json)`.
   - Each attempt still validates JSON before accepting the content.
   - All four attempts are exhausted before fail-closed.

5. **Fixed Ollama timeout floor in `LLMProviderConfig.__init__`**  
   Added: `if self.provider == "ollama" and self.timeout_seconds < 120.0: self.timeout_seconds = 120.0`.

### `tools/run_phase_l26m_ollama_empty_content_response_regression.py`

New regression runner covering:

- Existence of `_extract_ollama_content`, `_diagnose_empty_content`, `_safe_response_preview`
- Alternate-field search and JSON guard on thinking
- Presence of `format_json` and `no_format_json` attempts
- Mock default preserved
- Ollama localhost-only preserved
- No silent mock fallback
- BuilderSession ingestion boundary preserved
- Min Ollama timeout enforced
- No renderer/CCI/bootstrap/hermes mutations

## Files Changed

- `src/llm_provider_config.py` — response extraction, diagnosis, retry logic, timeout fix
- `tools/run_phase_l26m_ollama_empty_content_response_regression.py` — new regression runner
- `tools/run_phase_l26k_ollama_inference_endpoint_diagnostics_regression.py` — updated Check D to match refactored `_attempt` loop

## Verification

- `tools/run_phase_l26m_ollama_empty_content_response_regression.py`: **17/17 PASS**
- `tools/run_phase_l26k_ollama_inference_endpoint_diagnostics_regression.py`: **19/19 PASS** (after Check D update)
- `tools/run_phase_l26l_guided_intake_inference_regression.py`: **17/17 PASS**
- `tools/run_phase_l26j_streamlit_ollama_availability_unification_regression.py`: **19/19 PASS**
- `tools/run_phase_l26i_ollama_localhost_detection_regression.py`: **24/24 PASS**
- `tools/run_phase_l26h_streamlit_dependency_autoinstall_regression.py`: **22/22 PASS**
- `tools/run_phase_l26g_ollama_timeout_fallback_and_coldstart_regression.py`: **8/8 PASS**
- `tools/run_phase_l26f_ollama_inference_debug_and_provider_state_fix_regression.py`: **24/24 PASS**
- `tools/run_phase_l26e_ollama_model_picker_regression.py`: **18/18 PASS**
- `tools/run_phase_l26_streamlit_launcher_regression.py`: **12/12 PASS**
- `tools/run_phase_l24_streamlit_usability_regression.py`: **16/16 PASS**
- `tools/run_phase_l23_streamlit_intake_import_smoke.py`: **10/10 PASS**
- `tools/run_phase_h13_config_regression.py`: **27/27 PASS**
- `tools/run_phase_k3_subject_terminal_punctuation_regression.py`: **11/11 PASS**
- `tools/run_phase_h4_routing_office_code_validator_regression.py`: **18/18 PASS**
- `tools/run_phase_h24_route011_sanitized_fixture_regression.py`: **36/36 PASS**

## Date

June 2026
