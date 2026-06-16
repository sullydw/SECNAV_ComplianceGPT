# Phase L.26C Ollama Provider Manual Path Checkpoint

**Date:** 2026-06-16  
**Baseline Commit:** `3a41187`  
**Phase:** L.26C  
**Status:** Implementation complete

---

## Goal

Add a real Ollama provider path for manual Streamlit use so that complex natural-language input (which the mock mediator's regex cannot handle) can be parsed by a local LLM, while keeping the mock provider as the default offline regression path.

---

## Files Changed

| File | Change |
|------|--------|
| `src/llm_provider_config.py` | **Modified** — Added `_ollama_backend(config)` factory using stdlib `urllib` (no hard dependency on requests/httpx). Calls `http://localhost:11434/api/tags` for health check, then `POST /api/chat` with `format: "json"` and `temperature: 0.2`. Fails closed on any error (URLError, JSONDecodeError, empty content, missing server). Model defaults to `llama3.2` or reads from `SECNAV_OLLAMA_MODEL`. Updated factory to inject real backend when `provider == "ollama"`. |
| `app_streamlit_llm_guided_intake.py` | **Modified** — Updated `_provider_available()` to return `False` for Ollama (availability is runtime-only; UI shows "manual" status). No other changes. |
| `tools/run_phase_l26c_ollama_provider_manual_path_regression.py` | **New** — 11-check regression: mock default, Ollama selection, fail-closed when server down, idempotent no-crash, FakeBackend in default mode, adapter validates output, Streamlit safety boundaries, backend callable, model env var, L.24 still passes. |
| `docs/checkpoints/phase_l26c_ollama_provider_manual_path_checkpoint.md` | **New** — This document. |
| `docs/PROJECT_STATUS.md` | L.26C entry added. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.26C entry added; next phase updated. |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — L.26C artifacts added. |

---

## Ollama Provider Behavior

| Condition | Behavior |
|-----------|----------|
| No env vars set | Mock provider (FakeBackend) — deterministic, no network |
| `SECNAV_LLM_PROVIDER=ollama` set, Ollama running | Real Ollama call to `localhost:11434/api/chat` with JSON-format prompt |
| `SECNAV_LLM_PROVIDER=ollama` set, Ollama NOT running | Fail-closed: returns `{"intent": "unknown", ...}` with explanation |
| `SECNAV_OLLAMA_MODEL=custom-model` set | Uses specified model instead of default `llama3.2` |
| Any error (network, JSON, empty) | Fail-closed: safe fallback JSON, no crash |

---

## Default Mock Behavior

Unchanged. When no `SECNAV_LLM_*` env vars are set:
- `LLMProviderConfig.from_env()` returns `provider="mock"`
- `build_llm_backend_from_config()` returns `FakeBackend("valid")`
- No network calls
- Deterministic responses for regressions

---

## Failure Behavior When Ollama Unavailable

```json
{
  "intent": "unknown",
  "proposed_payload_update": {},
  "proposed_key_value_lines": [],
  "confidence": 0.0,
  "explanation": "Ollama server not reachable at localhost:11434 (URLError). Ensure Ollama is installed and running.",
  "requires_user_confirmation": false,
  "safety_notes": ["Ollama unavailable — fail-closed."]
}
```

The adapter receives this, validates it, and returns it as the mediator output. The Streamlit app shows "Detected intent: `unknown`" and no fields are ingested. No crash.

---

## Prompt Sent to Ollama

The adapter's existing `_build_prompt()` is reused unchanged. It includes:
- System instruction: "You are a translator, not the source of truth"
- Rules: no invented official data, JSON-only output, allowed intents only
- Current builder state: payload, missing fields, validation summary, warnings, errors
- User message
- Expected JSON schema

Ollama is called with:
- `format: "json"` (forces JSON output)
- `temperature: 0.2` (deterministic-ish)
- `num_predict: 512` (max tokens)

---

## Manual Ollama Launch/Config Instructions

### 1. Install Ollama

Download from https://ollama.com and install.

### 2. Pull a model

```powershell
ollama pull llama3.2
```

Or any other model that supports JSON mode.

### 3. Start Ollama server

```powershell
ollama serve
```

Verify it's running:
```powershell
curl http://localhost:11434/api/tags
```

### 4. Launch Streamlit with Ollama enabled

```powershell
# In PowerShell
$env:SECNAV_LLM_PROVIDER = "ollama"
$env:SECNAV_OLLAMA_MODEL = "llama3.2"
.\launch_secnav_streamlit.ps1
```

Or in Command Prompt:
```cmd
set SECNAV_LLM_PROVIDER=ollama
set SECNAV_OLLAMA_MODEL=llama3.2
launch_secnav_streamlit.bat
```

### 5. Test complex natural language

In the chat box, type:
> "I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN"

Expected:
- Ollama parses the intent and proposes structured fields
- Adapter validates the output
- Debug panel shows the full mediator output
- BuilderSession ingests only validated KV lines

---

## Runner/Test Results

| Runner | Result |
|--------|--------|
| L.26C Ollama | 11/11 PASS |
| L.26B debug panel | 10/10 PASS |
| L.26A hotfix | 7/7 PASS |
| L.26 launcher | 12/12 PASS |
| L.24 usability | 16/16 PASS |
| L.23 import smoke | 10/10 PASS |
| H.13 config | 27/27 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| Intake regression | 45/45 PASS |
| H.4 validator | 18/18 PASS |

**329/329 PASS + 1 optional smoke SKIP**

---

## Recommended Next Phase

`Phase L.27 Streamlit Launcher Manual Verification`

---
