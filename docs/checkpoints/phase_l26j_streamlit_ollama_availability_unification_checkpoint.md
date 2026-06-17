# Phase L.26J — Unify Streamlit Ollama Availability Check

## Scope

Eliminated the duplicate Ollama `/api/tags` probe between sidebar and mediation path.
Sidebar now caches `ollama_service_status()` in `st.session_state.ollama_status`, and `provider_debug_status()` accepts an optional `cached_ollama_status` argument so the sidebar uses that same cached dict instead of making a second probe.

## Rationale

Previously:
- Sidebar called `ollama_service_status()` once for the model list.
- Sidebar then called `list_ollama_models()` which internally called `ollama_service_status()` again.
- Later in the render, `provider_debug_status()` called `ollama_service_status()` a third time.
- During submission, `_run_mediation()` built a backend that independently called `_discover_working_ollama_host()` (yet another probe).

Because Ollama’s /api/tags could respond differently on each call (cold-start timing, GC pauses), the sidebar could report reachable with models while the mediation path or provider status label reported unreachable. The UI therefore showed contradictory messages.

## Fix

- `provider_debug_status()` now accepts `cached_ollama_status: dict | None = None`.
- App sidebar stores the first `ollama_service_status()` result in `st.session_state.ollama_status`.
- Sidebar model list now uses `ollama_status.get("models", [])` instead of calling `list_ollama_models()` separately.
- `provider_debug_status(effective_config, cached_ollama_status=...)` reuses the cached status.
- `_discover_working_ollama_host()` remains used only inside `call_ollama_inference()` for the actual inference call — this is correct, since inference needs its own connectivity check independent of the UI selection phase.

## Files Changed

- `app_streamlit_llm_guided_intake.py` — cache `ollama_status` in session state, reuse for model list and provider status.
- `src/llm_provider_config.py` — `provider_debug_status()` accepts `cached_ollama_status`, propagates `reachable`/`active_endpoint`/`tried_endpoints`.

## Verification

- `tools/run_phase_l26j_streamlit_ollama_availability_unification_regression.py`: 19/19 PASS.
- Downstream suite: L.26I, L.26H, L.26G, L.26E, L.24, L.23, H.13, K.3 all PASS.

## Date

June 2026
