# Phase L.26K — Ollama Inference Endpoint Diagnostics and Repair

## Scope

Added rich per-endpoint failure diagnostics to `call_ollama_inference()` so the debug panel explains exactly why each localhost endpoint failed instead of collapsing everything into a generic "Ollama inference endpoint unavailable" message.

## Rationale

L.26J eliminated the false-negative availability mismatch between sidebar and mediation path, but manual verification showed the actual inference still fails:

- `/api/tags` is reachable (models discovered)
- `/api/chat` returns HTTP 404 or other error
- `/api/generate` may also fail
- Debug panel showed only: `"Ollama inference endpoint unavailable. Tried ... and ..."`

Users could not tell whether the model was missing, the endpoint was wrong, the payload was malformed, or Ollama was truly down.

## Fix

### `src/llm_provider_config.py`

- `call_ollama_inference()` now initializes a `diagnostics: list[dict[str, Any]]` accumulator.
- For each endpoint (`/api/chat`, then `/api/generate`), it captures:
  - `endpoint`, `model`, `provider`, `timeout`
  - `status` (e.g., `http_error`, `timeout`, `endpoint_not_found`, `json_decode_error`, `empty_content`, `unexpected_exception`)
  - `exception_type` and `exception_message`
  - `http_code` (when applicable)
  - `response_snippet` (first 500 bytes of the HTTP error body)
- On exhaustion of both endpoints, it builds a multi-line `explanation` containing:
  - Summary sentence: "Ollama inference failed after trying all available endpoints (...)"
  - Selected provider, model, host, timeout
  - One line per endpoint showing status, exception type, HTTP code, message, and response snippet
- `safety_notes` now carry the same structured data in compact form.
- Fail-closed: still returns `intent: "unknown"`, empty KV lines, confidence `0.0`.
- No early return on intermediate failure — both endpoints are always attempted.

### `app_streamlit_llm_guided_intake.py`

- Debug panel (`🐛 Debug — Behind the Scenes`) detects when the last mediator output contains `"Ollama inference failed"` in its explanation.
- If detected, it renders a dedicated **Ollama Inference Diagnostics** subsection:
  - Displays selected provider and model from session state
  - Shows a read-only `st.text_area` with the full multi-line diagnostics
  - Lists each safety note as a `st.code` block
- If not detected, shows the previous compact caption.

## Files Changed

- `src/llm_provider_config.py` — rich diagnostics in `call_ollama_inference()`
- `app_streamlit_llm_guided_intake.py` — debug panel surfaces diagnostics when present

## Verification

- `tools/run_phase_l26k_ollama_inference_endpoint_diagnostics_regression.py`: 19/19 PASS.

## Date

June 2026
