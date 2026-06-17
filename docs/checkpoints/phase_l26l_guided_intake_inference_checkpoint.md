# Phase L.26L — Guided Intake Inference and Follow-Up Question Repair

## Scope

Repaired the `MockLLMBuilderMediator` (offline default) so that natural-language intake messages are no longer blocked by existing validator errors. The mediator now behaves as a guided-intake assistant rather than a finalization gatekeeper.

## Problem

For the test message:

> I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN

The mediator returned:

- `intent: "unknown"`
- Empty `proposed_key_value_lines`
- `blocked_reason: "Errors must be fixed before finalizing..."`
- `next_question: null`

Root cause: The prompt prefix told the mediator that "the builder currently has blocking validation findings" and instructed it to "refuse extractions until errors are fixed." This gatekeeping behavior is correct for `finalize`/`render` actions but wrong for `provide_field`/`revise_field` intake.

## Fix

### `src/llm_builder_mediator.py`

1. **Rewrote `mediator_prompt_prefix`**  
   - Removed language that suppressed extraction when validator errors exist.
   - New instructions:
     - "Current validator errors describe missing fields; they are NOT a reason to refuse extraction."
     - "For intake/provide_field/revise_field, propose any fields you can safely infer."
     - "blocked_reason is for finalize/render/accept_warning only."
     - "Ask exactly one next_question when more information is needed."
     - "You may infer plain-language subject and body draft from the user's stated purpose."
     - "Do not invent official facts (SSIC, references, enclosures, routing chain, names, dates, command authority)."

2. **Added `_infer_subject()` helper**  
   Derives a plain-language subject line from natural-language requests using keyword heuristics (date-change, TBD, request to change, etc.).

3. **Added `_infer_body()` helper**  
   Produces a concise purpose-draft paragraph from the user's stated intent, preserving their own words.

4. **Added "from X to Y" post-processing**  
   Detects routing clauses embedded in the same sentence and splits them into separate `from:` and `to:` KV proposals.

5. **Added contextual follow-up question**  
   When a date-change request lacks an original/current date, asks: "What is the current/original scheduled date that should be changed to TBD?"

6. **Updated `call_with_fallback_with_diagnostics()`**  
   - Adds `unblock_gate: intent in {"provide_field","revise_field","unknown"}` — after LLM call, if the detected intent is intake-oriented and a `blocked_reason` was produced, strip the block so the user sees a useful next question instead of a refusal.
   - Preserves `blocked_reason` for `finalize`/`render`/`accept_warning`.

7. **Regression runner added**  
   `tools/run_phase_l26l_guided_intake_inference_regression.py`

## Files Changed

- `src/llm_builder_mediator.py` — prompt prefix, `_infer_subject()`, `_infer_body()`, crossover parser, unblock gate
- `tools/run_phase_l26l_guided_intake_inference_regression.py` — new regression runner

## Verification

- `tools/run_phase_l26l_guided_intake_inference_regression.py`: **17/17 PASS**
- Downstream reruns all PASS:
  - L.26K 19/19, L.26J 19/19, L.26I 24/24, L.26H 22/22, L.26G 8/8, L.26F 24/24, L.26E 18/18
  - L.26 12/12, L.24 16/16, L.23 10/10, L.21 17/17, L.25 14/14
  - H.13 27/27, K.3 15/15, H.4 18/18, H.24 36/36

## Date

June 2026
