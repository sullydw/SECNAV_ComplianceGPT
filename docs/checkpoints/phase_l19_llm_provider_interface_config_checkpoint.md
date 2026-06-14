# Phase L.19 LLM Provider Interface and Configuration Plumbing Checkpoint

**Date:** 2026-06-13  
**Commit:** `b33a1eb` (baseline)  
**Phase:** L.19  
**Purpose:** Add provider-interface and configuration plumbing so future real LLM providers can be selected safely, while keeping mock backend as the default and keeping regressions offline.

---

## Files Changed

| File | Change |
|------|--------|
| `src/llm_provider_config.py` | **New** — `LLMProviderConfig` (env-driven config loader), `build_llm_backend_from_config()` (factory), `build_adapter_from_env()` (one-shot factory); safe defaults; no vendor SDK hard dependencies; no API keys committed |
| `tools/run_phase_l19_llm_provider_config_regression.py` | **New** — 14-check runner covering default mock, missing env vars, provider normalization, unsupported provider, OpenAI without key, Ollama without server, valid timeout/tokens, invalid timeout/tokens, no secrets in to_dict, fake backend through adapter, no real imports, no renderer references, no CCI references |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — Added L.19 artifacts to Check 17 |
| `docs/PROJECT_STATUS.md` | L.19 entry added |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.19 entry added; next phase updated to L.20 |

---

## Provider Config Behavior

`LLMProviderConfig.from_env(prefix="SECNAV_LLM")` reads:

| Env Var | Default | Behavior |
|---|---|---|
| `SECNAV_LLM_PROVIDER` | `mock` | Provider name; normalized to lowercase |
| `SECNAV_LLM_MODEL` | `None` | Optional model name |
| `SECNAV_LLM_TIMEOUT_SECONDS` | `30.0` | Clamped `[0, 300]`; invalid → `30.0` |
| `SECNAV_LLM_MAX_TOKENS` | `512` | Clamped `[0, 4096]`; invalid → `512` |
| `SECNAV_LLM_API_KEY_ENV_VAR` | `None` | Name of env var holding API key (not the key itself) |
| `SECNAV_OPENAI_API_KEY` | N/A | Referenced by `api_key_env_var`; never read directly by config loader |
| `SECNAV_OLLAMA_MODEL` | `None` | Stored in `extra` dict |

`to_dict()` never includes actual API key values.

---

## Provider Factory Behavior

`build_llm_backend_from_config(config)`:

| Provider | Key Present? | Backend |
|---|---|---|
| `mock` | N/A | `FakeBackend("valid")` from `llm_builder_mediator` |
| `openai` | No | `_unavailable_backend` |
| `openai` | Yes | `_openai_placeholder_backend` (no network) |
| `ollama` | N/A | `_ollama_placeholder_backend` (no network) |
| unsupported | N/A | `_unavailable_backend` |

All placeholder backends return valid `MediatorOutput` JSON with `intent="unknown"`, `confidence=0.0`, and an explanation pointing to configuration gap.

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.19 provider config | **14/14 PASS** |
| L.17 adapter | **15/15 PASS** |
| L.15 mock mediator | **15/15 PASS** |
| L.12 end-to-end demo | **13/13 PASS** |
| L.11 PDF export | **12/12 PASS** |
| H.13 config | **27/27 PASS** |
| K.3 SUBJ-002 | **11/11 PASS** |
| Intake regression | **45/45 PASS** |
| H.4 validator | **18/18 PASS** |

**Total: 248/248 PASS**

---

## Prohibitions Verified

- No real LLM/API imports (`openai`, `anthropic`, `requests`, `httpx`, `urllib`, `aiohttp` absent from `llm_provider_config.py` import statements)
- No network calls
- No API keys committed or printed
- No renderer/layout changes
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- Generated PDFs cleaned up

---

## Decision

Phase L.19 is **COMPLETE**. The provider configuration plumbing:
- Loads config from environment variables safely
- Defaults to mock backend when no env vars are set
- Normalizes provider names
- Rejects unsupported providers gracefully
- Fails closed for OpenAI without API key and Ollama without server
- Clamps timeout/max_tokens to safe ranges
- Never exposes API key values in serialization
- Works end-to-end with `LLMBuilderMediatorAdapter` using fake backend
- Has no hard vendor SDK dependencies

The system is now ready for optional live LLM smoke-testing (L.20) without changing regression behavior.

---

## Recommended Next Phase

`Phase L.20  Optional Live LLM Smoke-Test Harness`

Goal: Add an optional, feature-flagged smoke-test harness that can call a real LLM (OpenAI or Ollama) behind the adapter for a single end-to-end letter creation. All standard regressions continue using the fake backend.
