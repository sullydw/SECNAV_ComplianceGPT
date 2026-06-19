# Phase L.29N Hermes Agent Integration Loop Checkpoint

**Commit:** `TBD`  
**Phase:** L.29N — Hermes Agent Integration Design  
**Baseline:** `2584eaf` — `Tools: Wire unresolved fact detector into CLI`

---

## Summary

Created `docs/hermes_agent_integration_loop.md`, a design specification defining how the Hermes conversational agent should use `detect-facts` to drive the builder loop after ingest. No source code changes.

## Design Deliverables

- Hermes builder loop: start → ingest → detect-facts → choose action → ask user → apply → rerun → candidate-add → candidate-confirm → render gate.
- Action handling by `recommended_action`: `ask_user`, `live_lookup`, `candidate_low_confidence`, `safe_infer`, `leave_blank`, `refuse_to_infer`.
- Priority order: blocking before recommended, required fields before formatting, user facts before lookup, no render until blocking == 0.
- Question selection rules: use `question` field, prefer unlock-progress, one/two at a time, keep simple.
- Candidate rules: session-scoped only, source evidence required, pending until confirmed, rejected remains in history.
- Render gate: blocking == 0 AND errors == 0 AND candidates resolved AND user approval.
- Three example workflows: standard letter, MFR, endorsement.
- Safety boundaries: no invented data, no auto-apply, no bypass, no CCI changes, no global candidates, no giant checklists.

## Files Changed

| File | Action |
|------|--------|
| `docs/hermes_agent_integration_loop.md` | Created |
| `docs/checkpoints/phase_l29n_hermes_agent_integration_loop_checkpoint.md` | Created (this file) |
| `docs/PROJECT_STATUS.md` | Modified |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Modified |

## No-Change Verification

- No source code modified.
- No renderer/layout changed.
- No validator/CCI config changed.
- No detector logic changed.
- No candidate schema changed.
- No static command/unit database added.
- No production live lookup code added.
- `docs/BOOTSTRAP.md` untouched.
- `docs/HERMES_INSTRUCTIONS.md` untouched.

## Recommended Next Phase

**Phase L.29O — Hermes Agent Integration Prototype**

Implement a minimal prototype where Hermes (via a mock or test harness):
1. Starts a BuilderSession.
2. Calls `detect-facts`.
3. Surfaces the highest-priority blocking question.
4. Accepts a simulated user answer.
5. Re-runs `detect-facts`.
6. Loops until blocking == 0.
7. Validates the render gate.

This tests the integration loop without live LLM inference or browser lookup.
