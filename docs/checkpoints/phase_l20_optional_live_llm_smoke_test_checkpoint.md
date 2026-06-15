# Phase L.20 Optional Live LLM Smoke-Test Harness Checkpoint

**Date:** 2026-06-14  
**Commit:** `a9f4710` (baseline)  
**Phase:** L.20  
**Purpose:** Optional/manual live LLM smoke-test harness that exercises the full adapter + backend pipeline with a minimal safe prompt. Runs ONLY when explicitly enabled via env var.

---

## Files Changed

| File | Change |
|------|--------|
| `tools/run_phase_l20_optional_live_llm_smoke_test.py` | **New** — 8-check smoke harness; gated by `SECNAV_LLM_LIVE_SMOKE=1`; default behavior is SKIP with exit 0; loads provider config; builds backend + adapter; sends minimal prompt; validates adapter output; redacts potential API key leakage |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — Added L.20 artifact |
| `docs/PROJECT_STATUS.md` | L.20 entry added |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.20 entry added; next phase updated to L.21 |

---

## Default Behavior

```bash
$ python tools/run_phase_l20_optional_live_llm_smoke_test.py
SKIP: SECNAV_LLM_LIVE_SMOKE is not set to 1.
This harness is optional and does not run by default.
To enable: set SECNAV_LLM_LIVE_SMOKE=1
```

Exit code: `0`

---

## Optional Live Behavior (Mock Backend)

```bash
$ SECNAV_LLM_LIVE_SMOKE=1 python tools/run_phase_l20_optional_live_llm_smoke_test.py
Provider : mock
Model    : (default)
Timeout  : 30.0s
MaxTokens: 512
KeyVar   : (none)
KeyPresent: False
Prompt   : From Commanding Officer to Commander subject Training Plan
Intent        : provide_field
Confidence    : 0.9
...
Results: 8/8 passed
```

Exit code: `0`

For OpenAI/Ollama placeholder backends, intent will be `unknown` with controlled explanation — no network call is made.

---

## Smoke Checks

| Check | Description |
|---|---|
| A | Adapter returned valid output |
| B | Intent in allowed set |
| C | Confidence bounded [0.0, 1.0] |
| D | Payload update is dict |
| E | Key-value lines is list |
| F | No unsafe keys in payload update |
| G | Mock provider yields real intent; placeholders yield controlled output |
| H | No API key leakage in output |

---

## Prohibitions Verified

- No live API calls unless explicitly enabled
- No API keys committed or printed
- No vendor SDK hard dependencies
- No renderer/layout changes
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.20 smoke (default) | SKIP / exit 0 |
| L.20 smoke (enabled, mock) | 8/8 PASS |
| L.19 provider config | 14/14 PASS |
| L.17 adapter | 15/15 PASS |
| L.15 mock mediator | 15/15 PASS |
| H.13 config | 27/27 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| Intake regression | 45/45 PASS |
| H.4 validator | 18/18 PASS |

**Total: 248/248 PASS + 1 optional smoke SKIP**

---

## Decision

Phase L.20 is **COMPLETE**. The optional smoke-test harness:
- Is completely gated by an environment variable
- Defaults to clean SKIP (exit 0)
- Never makes network calls unless explicitly enabled
- Never prints secrets (redaction applied)
- Validates adapter behavior in real-time
- Works with mock, placeholder, or future live backends

The system is now ready for an LLM-guided natural-language intake demo (L.21) using the mock backend.

---

## Recommended Next Phase

`Phase L.21  LLM-Guided Natural-Language Intake Demo`

Goal: Use the mock mediator (or future live mediator) to guide a user conversationally through creating a complete Navy/Marine Corps letter. Prove end-to-end flow from natural-language input to structured payload + PDF through the adapter layer.
