# Phase L.30U — Single Interactive Chat Loop Checkpoint

## Summary

Single `interactive` command added to `tools/hermes_chat_builder.py`, enabling a conversational stdin-based session where the user types naturally and the existing deterministic chat handler routes each turn.

## Baseline

- Commit: `0cccb8d`
- Parent: `fb307ef`

## Files Added / Modified

- `tools/hermes_chat_builder.py` — added `interactive` command and `_run_interactive` loop
- `tools/run_phase_l30u_interactive_chat_loop_smoke.py` — 12-step smoke test (created)

## New Command

```
python tools/hermes_chat_builder.py interactive [--chat-id <CHAT_ID>] [--out <PDF_PATH>] [--json-lines]
```

## Behavior

- Auto-creates a new chat session unless `--chat-id` is provided.
- Prints `chat_id` and session info at startup.
- Accepts repeated stdin lines; each line is a chat turn.
- Routes every turn through the existing deterministic `_process_turn` / `_classify_intent` logic.
- Prints `assistant_response` (plain-English) after each turn.
- Preserves existing JSON behavior for non-interactive commands (`start`, `chat`, `status`, `reset`).
- `--out` overrides the default PDF output path.
- `--json-lines` emits one full JSON object per turn (useful for UI integration).
- Exit commands: `exit`, `quit`, `/exit`, `/quit`.

## Safety Gates Preserved

- No auto-render.
- Render blocked unless `validation_ready` and `approved_ready`.
- Approval clears on revision (existing manager behavior).
- All gates delegated to `hermes_session_manager.py`; no logic duplication.

## Smoke Test Results

- Tool: `tools/run_phase_l30u_interactive_chat_loop_smoke.py`
- Result: **PASS** — all 12 steps passed
  - interactive auto-create
  - interactive initial letter request
  - interactive provide missing details
  - interactive preview intent
  - interactive revise
  - fill remaining fields via manager
  - interactive approve
  - interactive render → PDF generated
  - json-lines mode emits parseable JSON objects
  - non-interactive start still works
  - non-interactive chat still works
  - non-interactive status and reset still work

## Output PDF

- `tmp\chat_builder_20260703_223027.pdf`
- Size: 1,809 bytes

## Constraints Honored

- No renderer/layout changes.
- No validator rule changes.
- No CCI config changes.
- No rule file changes.
- No docs changes (other than this checkpoint and PROJECT_STATUS.md).
- No changes to `hermes_secnav_tool.py`.
- No changes to `hermes_session_manager.py`.
- No regressions run.
- No live lookup.
- No approval hash behavior changes.
- No candidate confirmation behavior changes.
- No render/finalize gate changes.

## Status

- Committed: `0cccb8d`
- Pushed to origin/main: yes
