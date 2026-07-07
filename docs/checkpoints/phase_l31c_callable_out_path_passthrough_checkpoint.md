# Phase L.31C — Callable Out-Path Pass-Through Checkpoint

**Baseline commit:** `9679991`
**Date:** 2026-07-07
**Status:** Merged to `main`

## Issue Fixed

`send_secnav_chat_turn(chat_id, text, out=None)` declared an `out` parameter but did not actually pass it through or persist it. This meant callers could not set or override the output PDF path via the callable API after starting a chat.

## Files Changed in Implementation

- `tools/hermes_chat_builder.py` — `_send_chat_turn` now accepts `out` and stores it in `state["out_path"]`; `send_secnav_chat_turn` forwards `out` to the internal backend.
- `tools/run_phase_l31c_out_path_passthrough_smoke.py` — new smoke test covering the fix.
- `docs/PROJECT_STATUS.md` — L.31C entry added.

## Implementation Summary

- `_send_chat_turn(chat_id, text, out=None)` stores `out` into `state["out_path"]` when provided, then persists state.
- `send_secnav_chat_turn(chat_id, text, out=None)` forwards `out` to `_send_chat_turn`.
- `_run_render_gate` uses `state.get("out_path")` if present; falls back to the default tmp path (`tmp\chat_{session_id}.pdf`) when `out` is omitted.
- Existing behavior is fully preserved when `out` is not supplied.

## Behavior Preserved

- Callable functions remain silent (no stdout).
- CLI commands (`start`, `chat`, `status`, `reset`, `interactive`) continue to work.
- Render is still blocked before `approval` and `validation_ready` gates are satisfied.
- Approval clears on revision when `payload_changed=True`.
- Unsupported revise does not falsely claim changes (`payload_changed` stays `False`/`None`).

## Smoke Results

| Test | Result |
|---|---|
| `run_phase_l31c_out_path_passthrough_smoke.py` | PASS (6/6) |
| `run_phase_l31a_tool_interface_smoke.py` | PASS (13/13) |
| `run_phase_l30x_chat_response_consistency_smoke.py` | PASS |
| `run_phase_l30u_interactive_chat_loop_smoke.py` | PASS |

## Deployment

Pushed to `origin/main` at commit `9679991`.

## Notes

- This is a minimal callable-interface patch with no changes to renderer, layout, validator, CCI config, rule files, approval hash, candidate confirmation, or render gates.
- Future phases (L.31D+) may choose to refactor `_run_manager` from subprocess calls to direct in-process backends, but the current subprocess boundary remains acceptable.
