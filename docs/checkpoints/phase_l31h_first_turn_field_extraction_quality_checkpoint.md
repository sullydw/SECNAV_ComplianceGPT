# Phase L.31H — First-Turn Field Extraction Quality Checkpoint

**Date:** 2026-07-12
**Baseline Commit:** `0c0109c`
**Git History:** Fast-forward from `046621a` to `0c0109c`

## Implementation Files
- `tools/hermes_chat_builder.py` — refactored field extraction logic
- `tools/run_phase_l31h_first_turn_field_extraction_quality_smoke.py` — new smoke test

## Problem Fixed
Before L.31H, a realistic first-turn natural-language request:
- left the `To` line contaminated with trailing topic text (e.g., "about reviewing correspondence procedures")
- dropped or mangled the explicit `subject`
- produced a body fragment instead of a complete sentence
- required follow-up key:value turns to reach `draft_preview`

## Fixes Applied
- `To` line is now parsed cleanly without trailing topic phrases
- Explicit `subject` is preserved from the user's text
- Body is converted into a usable sentence
- All required fields extract in a single first turn

## Actual Preview Confirmed
```
From: Commanding Officer, Marine Corps Air Station New River
To: Commanding General, II Marine Expeditionary Force
Date: 1 July 2026
Subject: REVIEW OF CORRESPONDENCE PROCEDURES
Body: This letter addresses implementing local correspondence review procedures.
Signature: A. B. SAMPLE
```

## Validation Results
- First turn reaches `draft_preview` with no follow-up fields needed
- `validation_ready=True` immediately
- `approved_ready` remains gated by explicit approval
- All regressions pass

## Smoke Results
| Test | Result |
|---|---|
| py_compile | PASS |
| L.31H first-turn extraction quality | PASS 7/7 |
| L.31F first-turn intake hardening | PASS 10/10 |
| L.31F-1 apply persistence debug | PASS 8/8 |
| L.31A tool interface | PASS 13/13 |
| L.31C out-path passthrough | PASS 6/6 |

## Constraints Followed
- No interactive command used.
- No live lookup used.
- No renderer/layout/validator/catalog/config/rule changes.

## Verdict
First-turn field extraction quality is now sufficient for normal Hermes tool use.
