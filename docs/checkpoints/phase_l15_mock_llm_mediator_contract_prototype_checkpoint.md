# Phase L.15 Mock LLM Mediator Contract Prototype Checkpoint

**Date:** 2026-06-13  
**Commit:** `5d8620a` (baseline)  
**Phase:** L.15  
**Purpose:** Build a deterministic mock mediator that follows the L.14 contract and proves safe handoff into `BuilderSession` without using a real LLM.

---

## Files Changed

| File | Change |
|------|--------|
| `src/llm_builder_mediator.py` | **New** — `MockLLMBuilderMediator`, `MediatorInput`, `MediatorOutput` constructors; deterministic NL-to-structured field extraction; signature, from/to/subj/body extraction; confirmation policy; safety flags; 8 allowed intents |
| `tools/run_phase_l15_mock_llm_mediator_regression.py` | **New** — 15-check runner covering intent detection, field extraction, signature capture, no SSIC invention, question generation, warning acceptance, finalize/render, unknown messages, BuilderSession handoff, end-to-end finalize |
| `docs/PROJECT_STATUS.md` | L.15 entry added |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.15 entry added; next phase updated to L.16 |

---

## Mediator Behavior Summary

`MockLLMBuilderMediator.mediate(input_data)` implements a deterministic, rule-based NL interpreter:

- **Intent detection:** Keyword heuristics for `start_letter`, `provide_field`, `revise_field`, `accept_warnings`, `request_warning_explanation`, `finalize`, `render_pdf`, `unknown`.
- **Field extraction:** Regex patterns for `from`, `to`, `subj`, `body`, `ssic`, `doc_type`, `distribution`, `copy_to`, `via`, `window_envelope`, and structured `signature.name`/`signature.role`/`signature.title`.
- **Confirmation policy:** Direct user-provided simple fields require no confirmation; inferred values and official data require confirmation; finalize/render/warning acceptance require confirmation.
- **Safety boundaries:** No invented SSICs; no invented command data; ambiguous official data triggers `next_question`; warnings are surfaced but not suppressed or downgraded.
- **BuilderSession handoff:** All proposed updates are emitted as `proposed_key_value_lines` and must be passed through `builder.ingest_user_message()`. Mediator never mutates BuilderSession directly.

---

## Contract Fields Implemented

### MediatorInput (11 fields)
`session_id`, `current_step`, `payload_snapshot`, `missing_required_fields`, `missing_recommended_fields`, `validation_summary`, `warning_summary`, `error_summary`, `user_message`, `conversation_history_summary`, `available_commands`, `safety_flags`

### MediatorOutput (10 fields)
`intent`, `proposed_payload_update`, `proposed_key_value_lines`, `next_question`, `explanation`, `requires_user_confirmation`, `warnings_to_surface`, `blocked_reason`, `confidence`, `safety_notes`

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.15 mock mediator | **15/15 PASS** |
| L.12 end-to-end demo | **13/13 PASS** |
| L.11 PDF export | **12/12 PASS** |
| L.9 signature capture | **11/11 PASS** |
| L.7 CLI regression | **26/26 PASS** |
| L.6 PDF dry-run | **7/7 PASS** |
| H.13 config | **27/27 PASS** |
| K.3 SUBJ-002 | **11/11 PASS** |
| Intake regression | **45/45 PASS** |

**Total: 219/219 PASS**

---

## Prohibitions Verified

- No renderer/layout changes (`src/pdf_v6_render.py` untouched)
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- No real LLM/API dependency (`requests`, `httpx`, `urllib`, `openai`, etc. not imported)
- No error promotion
- Generated PDFs cleaned up

---

## Decision

Phase L.15 is **COMPLETE**. The mock mediator successfully:
- Detects 8 intents from natural-language-ish input
- Extracts structured fields without inventing official data
- Generates clarifying questions for missing required fields
- Surfaces warnings without suppression
- Proposes updates as key-value lines for BuilderSession ingestion
- Reaches finalized payload in end-to-end flow

The contract is proven workable with deterministic logic. A real LLM adapter (L.16) can be layered on top without changing the BuilderSession or contract.

---

## Recommended Next Phase

`Phase L.16  LLM Mediator Adapter Boundary Design`

Goal: Design the boundary where a real LLM (OpenAI, local, etc.) would replace the mock mediator's intent detection and field extraction, while keeping the same input/output contract and BuilderSession handoff invariant.
