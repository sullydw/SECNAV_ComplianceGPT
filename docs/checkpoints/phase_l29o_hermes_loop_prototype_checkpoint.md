# Phase L.29O Hermes Loop Prototype Checkpoint

**Commit:** `TBD`  
**Phase:** L.29O — Hermes Agent Integration Prototype  
**Baseline:** `8c3f0ab` — `Docs: Define Hermes detector integration loop`

---

## Summary

Created `tools/hermes_loop_prototype.py`, a narrow deterministic prototype proving the real CLI can support the Hermes question loop: start → ingest → detect-facts → select next question → apply simulated answer → detect-facts again → render gate check. Three scenarios tested: standard_letter_minimal, mfr_minimal, endorsement_minimal.

## Prototype Behavior

- Reuses existing `BuilderSession`, `MockLLMBuilderMediator`, and `detect_unresolved_facts()` code paths.
- No duplicated detector logic, no direct session JSON editing, no candidate creation, no live lookup, no render.
- Question selection: sorts by priority (blocking > recommended > optional), stable fact_id order, excludes already-attempted fields.
- Simulated answers: scenario-local dictionaries keyed by field; clearly marked as test data only.
- Render gate: `can_render` true only when `blocking == 0` AND `validator_errors == 0` AND `finalize_allowed`.

## Scenario Results

| Scenario | Steps | Blocking → 0 | Recommended Remaining | Render Gate |
|----------|-------|-------------|----------------------|-------------|
| standard_letter_minimal | 5 | YES | 4 | can_render=true |
| mfr_minimal | 3 | YES | 4 | can_render=false (1 validator error) |
| endorsement_minimal | 8 | YES | 3 | can_render=true |

Key findings:
- MFR correctly does not treat from/to/signature as blocking.
- Endorsement correctly requires basic_letter_id and endorsement_ordinal.
- SSIC is never invented; recommended facts remain unresolved after blocking reaches zero.
- Every step includes question, rule_id, source_file, and recommended_action.

## Files Changed

| File | Action |
|------|--------|
| `tools/hermes_loop_prototype.py` | Created |
| `tools/run_phase_l29o_hermes_loop_prototype_regression.py` | Created |
| `docs/checkpoints/phase_l29o_hermes_loop_prototype_checkpoint.md` | Created (this file) |
| `docs/PROJECT_STATUS.md` | Modified |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Modified |

## Regression Results

| Suite | Checks | Result |
|-------|--------|--------|
| **L.29O** (new) | 26/26 | **PASS** |
| L.29M | 37/37 | PASS |
| L.29L | 38/38 | PASS |
| L.29K | 23/23 | PASS |
| L.29C | 23/23 | PASS |
| L.28 | 25/25 | PASS |

## No-Change Verification

- No renderer/layout changed.
- No validator/CCI config changed.
- No static command/unit database added.
- No live lookup code added.
- No candidate creation.
- No detector or rule-to-fact map changes.
- `docs/BOOTSTRAP.md` untouched.
- `docs/HERMES_INSTRUCTIONS.md` untouched.

## Recommended Next Phase

**Phase L.29P — Hermes Agent Integration with Real LLM**

Wire the prototype loop into a real Hermes conversational session where:
1. Hermes calls `detect-facts` after ingest.
2. Hermes surfaces the highest-priority blocking question to the user.
3. User provides a real answer (not simulated).
4. Hermes applies the answer and re-runs `detect-facts`.
5. Loop continues until blocking == 0.
6. Hermes presents render gate status and asks user to confirm before finalize/render.

This requires a real Hermes session (not a test harness) and the existing `hermes_secnav_tool.py` CLI bridge.
