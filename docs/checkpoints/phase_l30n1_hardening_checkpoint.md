# Phase L.30N-1 Hardening Preview Approval and Source Warnings — Checkpoint

**Status:** COMPLETE

**Baseline commit:** `0947f1d`

## Summary

Review-identified quality issues hardened. No renderer, validator, catalog, config, or rule changes.

## Changes

### 1. Candidate source provenance fallback
- `_get_candidate_attr(c, key)` helper added in `tools/hermes_secnav_tool.py`
- Reads `source_tier`, `source_url`, `source_title`, `source_limitation` from top-level candidate fields first
- Falls back to `candidate["resolved_value"]` dict when top-level fields are absent
- Supports L.30J-style `official_live` candidates where provenance lives inside `resolved_value`

### 2. Approve gate
- `approve --session` now calls `_preview_gate_met(payload)` before recording approval
- If gate not met:
  - `success: false`
  - `mode: "build_status"`
  - `missing_for_preview` included
  - `error: "Cannot approve: draft preview is not available yet. Provide required fields first."`
  - No approval state recorded or saved

### 3. Finalize validation gate
- `finalize --session` checks `builder.validation_summary()["finalize_allowed"]` before checking approval
- If validation blocks:
  - `success: false`
  - `validation_summary`, `approval`, `approval_gate` included
  - `error` explains validation/finalize_allowed blocked finalization
- Approval gate still enforced after validation check

### 4. Manager ready separation
- `tools/hermes_session_manager.py` `ready` command updated to surface:
  - `validation_ready`
  - `approved_ready`
  - `approval_required`
  - `approval_gate`
  - `approval`
- Message clearly distinguishes when validation can render but approval is missing

### 5. Preview read-only safety preserved
- Preview does not save session, mutate payload, answer fields, confirm/reject/apply candidates, finalize, or render
- Candidate counts unchanged after preview

## Smoke tests
- `tools/run_phase_l30n1_hardening_smoke.py` created
- Verifies L.30J-style candidate labels, source_url/title/limitation display, approve gate, finalize validation gate, ready separation, read-only safety
- Targeted checks passed (`py_compile` + smoke runner)

## Files changed
- `tools/hermes_secnav_tool.py`
- `tools/hermes_session_manager.py`
- `tools/run_phase_l30n1_hardening_smoke.py`

## Pushed
- Commit `0947f1d` on `origin/main`
