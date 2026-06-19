# Phase L.29L Checkpoint: Unresolved Fact Detector Prototype

**Phase:** L.29L — Unresolved Fact Detector Prototype Implementation  
**Date:** 2026-06-19  
**Commit:** (to be filled after commit)  
**Status:** Complete

## Artifacts Created

1. **`src/unresolved_fact_detector.py`** — Deterministic unresolved-fact detector module
2. **`tools/run_phase_l29l_unresolved_fact_detector_regression.py`** — 38-check regression runner

## What Was Done

- Implemented a fully deterministic `UnresolvedFactDetector` that reads `rules_v6/CCI/cci_unresolved_fact_map.json` and emits `UNRESOLVED_FACTS_V1` JSON.
- Core API: `detect_unresolved_facts(payload, user_text=None, doc_type=None, mapping_path=None)`
- Respects doc_type field policies from `cci_intake_field_policy.json`:
  - `standard_letter` → blocking on from, to, date, subj, body, signature
  - `endorsement` → blocking on basic_letter_id, endorsement_ordinal
  - `memorandum_for_record` → blocking on body, date only (not from/to/signature)
  - `multiple_address_letter` → blocking on distribution_mode
- Subject formatting detection (lowercase, terminal punctuation, acronyms, vagueness) emits `recommended` priority facts, never `blocking` for present-but-malformed text.
- User-text assisted detection for SSIC ignorance, vague dates, copy-to hints, possible acronyms — all conservative, no invented expansions.
- No network calls, no LLM calls, no candidate creation, no payload mutation, no file writes.

## Regression Results

| Regression | Checks | Result |
|-----------|--------|--------|
| **L.29L** (new) | 38/38 | **PASS** |
| L.29K | 23/23 | PASS |
| L.29C | 23/23 | PASS |
| L.28 | 25/25 | PASS |

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `src/unresolved_fact_detector.py` | **Created** | 264 lines / 10,342 bytes |
| `tools/run_phase_l29l_unresolved_fact_detector_regression.py` | **Created** | ~200 lines / 9,220 bytes |
| `docs/checkpoints/phase_l29l_unresolved_fact_detector_checkpoint.md` | **Created** | 45 lines |
| `docs/PROJECT_STATUS.md` | **Modified** | +2 lines |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | **Modified** | +4/-1 lines |

## No Source Changes

- `renderer/layout` — no changes
- `validator/CCI config` — no changes
- `docs/BOOTSTRAP.md` — untouched
- `docs/HERMES_INSTRUCTIONS.md` — untouched
