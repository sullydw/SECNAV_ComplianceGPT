# Phase L.29P Next-Action CLI Checkpoint

**Commit:** `TBD`  
**Phase:** L.29P — Add Next-Action CLI Command  
**Baseline:** `19464db` — `Tools: Add Hermes loop prototype`

---

## Summary

Added a read-only `next-action` CLI command to `tools/hermes_secnav_tool.py` that tells Hermes the next recommended action for a BuilderSession. Sits deterministically above `detect-facts` as a convenience layer. Does not mutate sessions, create candidates, perform live lookup, or render.

## New CLI command

```bash
python tools/hermes_secnav_tool.py next-action --session <id> [--text "..."] [--doc-type "..."]
```

## Output shape

Returns `NEXT_ACTION_V1` JSON:
- `next_action.action`: ask_user | live_lookup | candidate_low_confidence | safe_infer | leave_blank | refuse_to_infer | blocked_by_validation | render_ready
- `next_action.priority`: blocking | recommended | optional | ready
- `next_action.field`, `.question`, `.rule_id`, `.source_file`, `.recommended_action`, `.candidate_type`
- `next_action.reason`
- `render_gate`: blocking_resolved, recommended_remaining, validator_errors, finalize_allowed, can_render, reason
- `unresolved_summary`: blocking, recommended, optional

## Selection rules (deterministic)

1. If blocking > 0: pick first blocking fact by stable fact_id order, action = recommended_action.
2. If blocking == 0 but validator errors > 0: blocked_by_validation.
3. If blocking == 0 but finalize not allowed: blocked_by_validation.
4. If blocking == 0 and recommended > 0: pick first recommended fact, action = recommended_action.
5. If optional > 0: pick first optional fact.
6. Otherwise: render_ready.

## Files Changed

| File | Action |
|------|--------|
| `tools/hermes_secnav_tool.py` | Modified — added `select_next_action()` helper + `cmd_next_action()` handler + `next-action` argparse subparser + handler registration |
| `tools/run_phase_l29p_next_action_cli_regression.py` | Created |
| `docs/checkpoints/phase_l29p_next_action_cli_checkpoint.md` | Created (this file) |
| `docs/PROJECT_STATUS.md` | Modified |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Modified |

## Regression Results

| Suite | Checks | Result |
|-------|--------|--------|
| **L.29P** (new) | 27/27 | **PASS** |
| L.29O | 26/26 | PASS |
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
- No candidate creation in this phase.
- No render performed.
- `docs/BOOTSTRAP.md` untouched.
- `docs/HERMES_INSTRUCTIONS.md` untouched.

## Recommended Next Phase

**Phase L.29Q — Hermes Agent Session Manager**

Teach Hermes to:
1. Maintain a persistent session across conversational turns.
2. Call `start` to initialize a session, store the session_id.
3. After each user message, call `ingest` then `next-action`.
4. When `next-action` returns `ask_user`, surface the question to the user.
5. When `next-action` returns `render_ready`, ask the user to confirm before finalize/render.
6. When `next-action` returns `blocked_by_validation`, explain the blocker.
7. Handle the full start → ingest → next-action → ask user → apply → next-action loop natively.

This makes Hermes a true conversational builder driver rather than a passive proxy.
