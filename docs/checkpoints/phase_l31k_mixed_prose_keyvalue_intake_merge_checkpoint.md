# Phase L.31K — Mixed Prose + Key:Value Intake Merge Checkpoint

**Date:** 2026-07-26
**Baseline Commit:** `92f1e1d`
**Git History:** Fast-forward from `b63bb27` to `92f1e1d`

## Implementation Files
- `tools/hermes_chat_builder.py` — refactored mixed prose + key:value intake merge logic
- `tools/run_phase_l31k_mixed_prose_keyvalue_intake_merge_smoke.py` — new smoke test

## Problem Fixed
Before L.31K, a first-turn request containing both natural prose and explicit key:value pairs:
- dropped body when mixed with prose
- dropped letterhead fields if embedded in prose rather than sent as separate key:value turns
- required multiple follow-up turns to reach `draft_preview`

## Fixes Applied
- Prose-extracted fields merge with explicit key:value fields in a single turn
- Body is captured whether provided inline or as explicit `body:`
- Letterhead fields (`letterhead_top_line`, `letterhead_activity`, `letterhead_address`) captured inline
- One-shot natural-language requests now reach `draft_preview` immediately

## Actual Preview Confirmed
```
LETTERHEAD
UNITED STATES MARINE CORPS
MARINE CORPS AIR STATION NEW RIVER
JACKSONVILLE NC 28545-0000

SSIC: 5216
Originator Code: S-1
Date: 1 July 2026

From: Commanding Officer, Marine Corps Air Station New River
To:   Commanding General, II Marine Expeditionary Force

Subj: REVIEW OF CORRESPONDENCE PROCEDURES

Body: This letter addresses implementing local correspondence review procedures.

Signature: A. B. SAMPLE
```

## Validation Results
- First turn reaches `draft_preview` with no additional field turns needed
- `validation_ready=True` immediately
- SSIC 5216 captured
- Originator code S-1 captured
- Letterhead fields captured and shown in preview
- Body captured
- `approved_ready` remains gated by explicit approval
- Render blocked before approval
- Render succeeds after approval

## Smoke Results
| Test | Result |
|---|---|
| py_compile | PASS |
| L.31K mixed prose key:value intake merge | PASS 19/19 |
| L.31J letterhead authority line validation | PASS 7/7 |
| L.31I standard letterhead required | PASS 7/7 |
| L.31H first-turn extraction quality | PASS 7/7 |

## PDF Output
- Path: `C:\Users\drryl\SECNAV_ComplianceGPT\tmp\chat_builder_20260726_231947.pdf`
- Size: 2085 bytes
- Content order confirmed: letterhead, date, from, to, subj, body, signature

## Constraints Followed
- No interactive command used.
- No live lookup used.
- No renderer/layout/validator/catalog/config/rule changes.

## Verdict
Mixed prose + key:value intake merge is now sufficient for normal Hermes tool use.
