# Phase L.21 LLM-Guided Natural-Language Intake Demo Checkpoint

**Date:** 2026-06-14  
**Commit:** `5ac017d` (baseline)  
**Phase:** L.21  
**Purpose:** Deterministic LLM-guided natural-language intake demo using the mock mediator (no real LLM/API calls). Demonstrates conversational field population, warning acceptance, finalization, and PDF render/cleanup.

---

## Files Changed

| File | Change |
|------|--------|
| `tools/run_phase_l21_llm_guided_natural_language_intake_demo.py` | **New** — 17-check demo runner; conversational flow through mock mediator; NL-style messages converted to KV lines; BuilderSession.ingest_user_message() for all updates; validation, warning acceptance, finalize, render, cleanup |
| `docs/checkpoints/phase_l21_llm_guided_natural_language_intake_demo_checkpoint.md` | **New** — This checkpoint document |
| `docs/demo/llm_guided_natural_language_intake_demo.md` | **New** — Narrative walkthrough document |
| `docs/PROJECT_STATUS.md` | L.21 entry added |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.21 entry added; next phase updated to L.22 |

---

## Demo Flow

1. **Start** BuilderSession with `doc_type=standard_letter`, `component.service=NAVY`
2. **Conversational field intake** (7 NL-style messages through mock mediator):
   - `from Commanding Officer, Example Command`
   - `to Commander, Example Group`
   - `subject Training Plan`
   - `ssic 5216`
   - `body This letter provides the proposed training plan.`
   - `signed by J. Q. Sample`
   - `window envelope false`
3. **Mediator** converts each message to `proposed_key_value_lines`
4. **BuilderSession.ingest_user_message()** applies KV lines (never direct mutation)
5. **Validation** runs — finds advisory + subject-casing error (expected)
6. **Warning acceptance** via `accept_warnings` intent
7. **Finalize** via `finalize` intent → `finalize_allowed=True`
8. **Render PDF** → success → immediate cleanup
9. **Guardrails** verify no unsafe keys, no API key leakage

---

## Demo Results

| Check | Description | Result |
|-------|-------------|--------|
| 1 | Validation summary produced | PASS |
| 2 | Accept warnings intent detected | PASS |
| 3 | Finalize allowed after accepting warnings | PASS |
| 4 | Payload field doc_type | PASS |
| 5 | Payload field from | PASS |
| 6 | Payload field to | PASS |
| 7 | Payload field subj | PASS |
| 8 | Payload field ssic | PASS |
| 9 | Payload field body | PASS |
| 10 | Payload field signature | PASS |
| 11 | Payload field signature.name | PASS |
| 12 | Payload field window_envelope | PASS |
| 13 | Payload field component.service | PASS |
| 14 | PDF rendered successfully | PASS |
| 15 | Generated PDF cleaned up | PASS |
| 16 | No unsafe keys in final payload | PASS |
| 17 | No API key leakage in output | PASS |

**Total: 17/17 PASS**

---

## Guardrails Verified

- No unsafe keys (`cci_severity`, `renderer_directive`, etc.) in payload
- No API key values printed or committed
- No live LLM/API/network calls
- No renderer/layout changes
- No CCI config/severity changes
- All updates through `builder.ingest_user_message()`

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.21 demo | **17/17 PASS** |
| L.20 smoke | SKIP / exit 0 |
| L.19 provider config | 14/14 PASS |
| L.17 adapter | 15/15 PASS |
| L.15 mock mediator | 15/15 PASS |
| L.12 end-to-end | 13/13 PASS |
| H.13 config | 27/27 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| Intake regression | 45/45 PASS |
| H.4 validator | 18/18 PASS |

**Total: 265/265 PASS + 1 optional smoke SKIP**

---

## Decision

Phase L.21 is **COMPLETE**. The mock-mediator conversational builder demo proves:
- Natural-language messages can be translated to structured field updates deterministically
- All updates route through `BuilderSession.ingest_user_message()` (no direct mutation)
- Validation, warning acceptance, finalize, and render are all functional
- Adapter safety filters work transparently in the background
- The system is ready for a UI decision on how to expose this flow to users

---

## Recommended Next Phase

`Phase L.22  LLM-Guided Intake User Interface Decision`

Goal: Decide whether the conversational builder should be exposed through CLI, TUI, web dashboard, or API; document the chosen path and create a lightweight plan.
