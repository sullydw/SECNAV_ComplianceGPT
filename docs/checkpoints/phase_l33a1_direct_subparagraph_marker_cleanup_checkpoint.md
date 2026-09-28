# Phase L.33A-1 — Direct Subparagraph Marker Cleanup

**Status:** accepted cleanup checkpoint
**Baseline:** `15a6aee` — Tools+Builder: Normalize direct subparagraph markers and fix body-list serialization; add L.33A smoke

## Purpose

Correct the L.33A status wording so the accepted behavior matches the code that landed in `15a6aee`.

L.33A normalizes direct parenthetical **alpha** markers typed under a level-1 paragraph:

- `(a)` → `a.`
- `(b)` → `b.`
- `(c)` → `c.`

This supports a common user input mistake while preserving strict SECNAV body validation rules. The validator is not weakened; the correction happens at intake/coercion.

## Explicitly Deferred Behavior

L.33A does **not** normalize numeric parenthetical markers typed directly under a level-1 paragraph:

- `(1)` remains `(1)`
- `(2)` remains `(2)`
- `(3)` remains `(3)`

Direct numeric-parenthetical correction is deferred until a separate, explicitly scoped phase defines the intended hierarchy and validation consequences.

## Preserved Behavior

- Proper deeper hierarchy remains unchanged, including `1.` → `a.` → `(1)` → `(a)`.
- Body JSON arrays remain preserved during chat/builder intake.
- Candidate-intent fallback heuristics only fire when actual pending candidates exist.
- No renderer/layout, validator/rule, official lookup/provider, approval/render gate, or candidate suggestion behavior changed in this cleanup.

## Files Changed

- `tools/run_phase_l33a_direct_subparagraph_marker_normalization_smoke.py`
  - Updated wording to say direct alpha subparagraph marker normalization.
  - Added checks for `(c)` alpha normalization.
  - Added checks proving direct `(1)` and `(2)` are preserved/deferred.

## Validation to Run Locally

```bat
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l33a_direct_subparagraph_marker_normalization_smoke.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l32v_ready_to_approve_guidance_with_suggestions_smoke.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l32u_missing_detail_guidance_with_suggestions_smoke.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l30x_chat_response_consistency_smoke.py
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\run_phase_l30u_interactive_chat_loop_smoke.py
```
