# Phase L.30S Chat-Orchestrated Letter Builder Checkpoint

**Date:** 2026-07-03  
**Baseline commit:** `b717bf4`  
**Status:** Complete — chat-orchestrated letter builder proven

## Files Added

| File | Description |
|------|-------------|
| `tools/hermes_chat_builder.py` | Chat orchestration layer over `hermes_session_manager.py` |
| `tools/run_phase_l30s_chat_builder_smoke.py` | Smoke test script (10 steps) |

## Chat Commands

- `start` — Create a new chat session with a hidden builder session
- `chat --chat-id <ID> --text <TEXT>` — Process a natural-language turn
- `status --chat-id <ID>` — Show current phase, preview, and next step
- `reset --chat-id <ID>` — Reset the chat to a fresh builder session

## Deterministic Intent Routing

| User intent | Hidden action |
|-------------|---------------|
| new / need a letter / draft / create / say / answer | `say` + `ready` + `preview` |
| revise / edit / change / make body / shorten / remove / change signer / change subject | `revise` + `preview` + `ready` |
| approve / looks good / approved / good to go | `approve` + `ready` |
| render / finalize / export / make pdf | `ready` gate check → `render` (if approved) |
| preview / show me / review | `preview` + `ready` |
| status / ready | `ready` + `preview` |

## Hidden Workflow Behavior

- User does not need to know `new`, `say`, `preview`, `revise`, `approve`, `ready`, or `render` commands.
- Chat layer is a thin orchestrator over existing `hermes_session_manager.py` commands.
- Core builder, renderer, validator, candidate, and approval logic is **not duplicated**.
- Chat state is persisted as a lightweight JSON alongside the builder session.

## Safety Gates Preserved

- No `approve` unless the preview gate is met (build_status vs draft_preview).
- No `render` unless `validation_ready` and `approved_ready` are both true.
- Revisions clear approval through existing manager `revise` behavior (`approval_cleared: True` when payload changes).

## Smoke Test Results

All 10 steps PASS:

1. start — chat session created, hidden builder session attached
2. initial chat — natural letter request ingested, phase = build_status
3. answer missing details — signer and date provided, phase advances
4. preview — preview_text returned with draft layout
5. approve — draft approved, phase = approved_ready
6. revise — natural-language revision changes subject, approval cleared, phase = draft_preview
7. re-approve — draft re-approved, phase = approved_ready
8. render PDF — PDF generated after approval gates pass
9. reset — new hidden builder session attached, old chat_id retained
10. blocked render — render without approval blocked safely

## Output PDF

- **Path:** `tmp\chat_builder_20260703_080932.pdf`
- **Size:** 1,815 bytes

## Constraints Honored

- No renderer/layout changes.
- No validator rule changes.
- No CCI config changes.
- No rule file changes.
- No production behavior changed in existing tools.
- No live lookup.
- No LLM/freeform planner inside the chat builder.

## Recommended Next Phase

TBD
