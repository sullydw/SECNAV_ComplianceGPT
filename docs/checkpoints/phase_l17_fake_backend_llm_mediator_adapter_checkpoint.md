# Phase L.17 Fake-Backend LLM Mediator Adapter Checkpoint

**Date:** 2026-06-13  
**Commit:** `b955542` (baseline)  
**Phase:** L.17  
**Purpose:** Implement the L.16 adapter boundary with a fake backend only. Prove adapter validation and safety filters before any real LLM/API integration.

---

## Files Changed

| File | Change |
|------|--------|
| `src/llm_builder_mediator.py` | **Extended** — Added `SafetyFilter`, `FakeBackend`, `LLMBuilderMediatorAdapter`; strict output validation; confidence bounds; intent validation; prohibited-key rejection; invented-official-data flagging; confirmation enforcement for finalize/render/accept_warnings; safe degradation to `unknown` + `next_question` |
| `tools/run_phase_l17_fake_backend_llm_mediator_adapter_regression.py` | **New** — 15-check runner covering valid pass-through, malformed JSON, missing keys, unsupported intent, low/high confidence, CCI tamper, renderer directive, invented SSIC, finalize confirmation, render confirmation, accept_warnings confirmation, BuilderSession handoff, direct-mutation guard, no API dependency |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — Added L.15/L.17 artifacts to Check 17 allowlist (no behavior change) |
| `docs/PROJECT_STATUS.md` | L.17 entry added |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.17 entry added; next phase updated to L.18 |

---

## Adapter Behavior Summary

`LLMBuilderMediatorAdapter.mediate(input_data)`:

1. **Builds prompt** from `MediatorInput` (system instructions + dynamic context + schema)
2. **Calls backend(prompt)** → raw text (injected `Callable[[str], str]`)
3. **Parses JSON** → degrades to `unknown` on parse failure
4. **Validates required keys** (`intent`, `proposed_payload_update`, `proposed_key_value_lines`, `confidence`)
5. **Enforces confidence bounds** (`[0.0, 1.0]`, degrades to `unknown` if below `min_confidence`)
6. **Enforces intent whitelist** (8 allowed intents)
7. **Rejects prohibited keys** (`cci_severity`, `renderer_directive`, `layout_override`, etc.)
8. **Flags invented official data** (SSIC not in prior payload → safety note)
9. **Forces confirmation** for `finalize`, `render_pdf`, `accept_warnings`
10. **Returns valid `MediatorOutput`** even on total failure

**`FakeBackend`** supports 12 response keys for deterministic testing:
`valid`, `malformed`, `missing_keys`, `unsupported_intent`, `low_confidence`, `high_confidence`, `cci_tamper`, `renderer_directive`, `invented_ssic`, `finalize_no_confirm`, `render_no_confirm`, `accept_warnings_silent`, `unknown`

---

## Safety Filters

| Filter | Behavior |
|---|---|
| CCI config/severity | Rejected + safety note |
| Renderer/layout directive | Rejected + safety note |
| Invented official data | Kept but flagged for confirmation |
| Silent warning acceptance | Confirmation forced |
| Unauthorized finalize/render | Confirmation forced |
| Low confidence (`< 0.3`) | Degraded to `unknown` + question |
| Unsupported intent | Replaced with `unknown` + safety note |

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.17 adapter | **15/15 PASS** |
| L.15 mock mediator | **15/15 PASS** |
| L.12 end-to-end demo | **13/13 PASS** |
| L.11 PDF export | **12/12 PASS** |
| H.13 config | **27/27 PASS** |
| K.3 SUBJ-002 | **11/11 PASS** |
| Intake regression | **45/45 PASS** |
| H.4 validator | **18/18 PASS** |

**Total: 234/234 PASS**

---

## Prohibitions Verified

- No real LLM/API imports (`openai`, `anthropic`, `requests`, `httpx`, `urllib`, `aiohttp` absent from `llm_builder_mediator.py`)
- No renderer/layout changes
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- Generated PDFs cleaned up

---

## Decision

Phase L.17 is **COMPLETE**. The `LLMBuilderMediatorAdapter`:
- Validates all LLM-like output before returning it
- Degrades safely on any failure (malformed JSON, missing keys, bad intent, low confidence)
- Rejects prohibited fields and flags invented data
- Forces confirmation for finalize/render/warning acceptance
- Never mutates BuilderSession directly
- Works with a deterministic `FakeBackend` for full regression coverage

The adapter is ready to accept a real LLM backend (OpenAI, local, etc.) as an injected callable without code changes.

---

## Recommended Next Phase

`Phase L.18  Real LLM Provider Selection and Adapter Plan`

Goal: Evaluate and select a real LLM provider (OpenAI, Anthropic, local llama.cpp, etc.) for integration behind the adapter. Define the concrete backend callable, prompt refinement strategy, and cost/latency guardrails. No active LLM calls in L.18 — only selection and planning.
