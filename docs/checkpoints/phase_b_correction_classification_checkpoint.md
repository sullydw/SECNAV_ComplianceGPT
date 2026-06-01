# Phase B Correction Classification Checkpoint

**Created:** 2026-06-01  
**Verified Baseline Commit:** `a7f9aeb` — `CCI: Fix Phase B regression isolation`  
**Implementation Commit:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Previous Baseline:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`  
**Status:** Phase B implementation complete, regression-protected, isolated, and pushed to origin/main.

---

## What Was Implemented

Phase B adds deterministic correction classification to the correction memory layer. When a user captures a correction and does not explicitly specify a correction type, the system now classifies it automatically.

### New Files

- `src/correction_classify.py` — Correction classifier with deterministic heuristics.
- `tools/run_correction_classify_regression.py` — 32-check regression runner for classification.

### Modified Files

- `src/correction_capture.py` — `capture_correction()` now calls `classify_correction()` when `correction_type` is not provided.
- `src/intake_orchestrator.py` — `persist_correction()` gates session persistence based on classification:
  - `one_time_wording` + `current_session` → persisted (explicit opt-in)
  - `local_command_preference` + `current_session` → persisted
  - `possible_secnav_manual_rule` + `current_session` → persisted
  - `bug_validator_gap` + `current_session` → persisted
  - `one_time_wording` without `current_session` → NOT persisted (default behavior)

### Classification Types

| Type | Classification Rules |
|---|---|
| `one_time_wording` | Reason contains "one time", "just this once", "only for this", "wording", "phrasing", or field path is `body.*` without further context |
| `local_command_preference` | Field path is `from`, `to`, `signature`, `point_of_contact`, `ssic`, `originator_code`, `unit_identity`, `letterhead_lines` |
| `possible_secnav_manual_rule` | Reason contains "manual", "SECNAV", "M-5216", "regulation", "chapter", "figure", or field path is `subj`, `ref`, `encl`, `via` |
| `bug_validator_gap` | Reason contains "validator", "should have caught", "false negative", "false positive", "bug", or `validator_conflict=True` |

### Regression Coverage

The `tools/run_correction_classify_regression.py` runner exercises:

1. Classification for each of the four types with `active_draft` scope.
2. Classification for `local_command_preference` with `current_session` scope → persisted.
3. Classification for `possible_secnav_manual_rule` with `current_session` scope → persisted.
4. Classification for `bug_validator_gap` with `current_session` scope → persisted.
5. `one_time_wording` with `current_session` scope → persisted (explicit opt-in).
6. `one_time_wording` without `current_session` → NOT persisted.
7. `local_command_preference` without `current_session` → NOT persisted.
8. `possible_secnav_manual_rule` without `current_session` → NOT persisted.
9. `bug_validator_gap` without `current_session` → NOT persisted.
10. `user_override` classification (explicit user-provided type preserved).
11. `field_path` override classification.
12. `validator_conflict=True` without reason keywords -> `bug_validator_gap`.
13. Mixed keywords resolution (user reason prioritized over field path).
14. Explicit `correction_type` bypasses classifier.
15. Nested indexed body paths: `body[0].text`, `body[0].content`.
16. Unknown field path with generic reason -> `one_time_wording`.
17. Loaded verification from temp session store (regression isolation fix).

All 32 checks pass (0 failures).

---

## Regression Safety

### Phase B Regression Isolation Fix

The original `tools/run_correction_classify_regression.py` accidentally wrote to the real `corrections/session/` directory during testing, creating `corrections/session/test_session_phase_b.jsonl`.

Fix at `a7f9aeb`:

- All persistence tests now use a temporary directory only.
- The temp directory and its files are cleaned up after the runner completes.
- The accidental real artifact was removed.
- `load_session_corrections()` signature is correctly handled (tuple return).

### All 18 Regression Suites Pass

As of `a7f9aeb`, all existing regression suites continue to pass:

- `run_intake_regression.py` — PASS
- `run_correction_regression.py` — PASS
- `run_correction_session_regression.py` — PASS
- `run_profile_regression.py` — PASS
- `run_cci_audit_regression.py` — PASS
- `run_context_schema_regression.py` — PASS
- `run_cci_subject_regression.py` — PASS
- `run_cci_ref_encl_regression.py` — PASS
- `run_cci_acronym_regression.py` — PASS
- `run_cci_date_time_regression.py` — PASS
- `run_cci_personnel_regression.py` — PASS
- `run_cci_poc_regression.py` — PASS
- `run_cci_routing_regression.py` — PASS
- `run_c7_phase1_regression.py` — PASS
- `run_c8_regression.py` — PASS
- `run_c9_regression.py` — PASS
- `run_c10_regression.py` — PASS
- `run_correction_classify_regression.py` — PASS

---

## What Was NOT Implemented

Phase B deliberately excluded the following items. They remain for future phases only after separate planning and approval.

1. **Profile promotion** — No corrections are promoted to local command profiles.
2. **Global rule promotion** — No corrections become SECNAV manual rules or validator updates.
3. **Pending global rule candidate log** — No `corrections/pending_corrections.jsonl` is written.
4. **UI override implementation** — No natural-language interface for overriding classification.
5. **Renderer/layout changes** — No modifications to `src/pdf_v6_render.py` or layout profiles.
6. **Auto-cleanup of session stores** — 30-day retention remains advisory only.

---

## Safety Notes

- Classification is deterministic and heuristic-based. It does not use an LLM.
- Classification gates persistence only; it does not auto-promote.
- User override is preserved: if `correction_type` is explicitly provided, the classifier is bypassed.
- Session JSONL files remain gitignored and local-only.
- No real command/user data was committed during Phase B implementation.
- The accidental artifact `corrections/session/test_session_phase_b.jsonl` was removed before push.

---

## Key Files

- `docs/PROJECT_STATUS.md` — main status tracker.
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — long-term layer plan.
- `docs/planning/phase_b_correction_classification_plan.md` — Phase B design plan.
- `docs/checkpoints/phase_a_session_persistence_checkpoint.md` — Phase A baseline checkpoint.
- `src/correction_classify.py` — classifier implementation.
- `src/correction_capture.py` — capture with auto-classification integration.
- `src/intake_orchestrator.py` — persistence gating.
- `tools/run_correction_classify_regression.py` — Phase B regression runner.

---

## Next Recommended Phase

**Phase C: Local Command Profile Promotion Planning**

Considerations:

- How `local_command_preference` corrections get promoted to named profiles.
- User approval workflow (explicit opt-in before writing to profile).
- Profile structure (overrides vs defaults).
- Safety rules: prevent committing real profile data to public repo.
- Regression coverage before implementation.

Phase C is **planning only** until reviewed and approved. Do not implement without explicit user direction.
