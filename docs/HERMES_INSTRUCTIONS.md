# Hermes Execution Instructions

## Required Reading Order

**Hermes Agent must first read and follow these documents in order**:

1. `docs/OPENCLAW_INSTRUCTIONS.md` - Shared SECNAV execution policy
2. `docs/HERMES_INSTRUCTIONS.md` - Hermes-specific overlay (this file)
3. `docs/PROJECT_STATUS.md` - Current project status
4. `HEARTBEAT.md` - HEARTBEAT signal requirements

## Policy Relationship

**docs/HERMES_INSTRUCTIONS.md is an overlay for Hermes behavior only**. docs/OPENCLAW_INSTRUCTIONS.md remains the authoritative shared SECNAV execution policy. Do not duplicate OpenClaw policy in this file; only add Hermes-specific workflow differences.

## Hermes-Specific Workflow Rules

- Use TUI or terminal-first workflow (leveraging Hermes' terminal/TUI capabilities)
- Use explicit shell commands to perform operations
- Confirm you're at the correct repository root before making any edits
- Run `git status` before and after every edit to verify changes
- Do NOT operate from workspace/root directories outside the repository
- Do NOT create loose files outside the repository boundaries

## Sync Rule

Before making code edits:

1. Run `git fetch origin`
2. Check if local branch is behind origin/main
3. If behind, run git pull/rebase before editing
4. If conflicts occur, **STOP and report** immediately

## Autonomy Limits

Do NOT perform these actions unless explicitly requested:

- Do NOT spawn subagents unless explicitly requested
- Do NOT create or modify skills unless explicitly requested
- Do NOT store new project memory unless explicitly requested
- Do NOT schedule automations (cron jobs) unless explicitly requested
- Do NOT use gateway/platform messaging unless explicitly requested

## Tool/Backend Rule

- Use only the tools required for the current task
- Do NOT change toolsets, terminal backends, MCP servers, or sandbox settings unless explicitly requested

## Test Rule

Run only the test/regression command specified by the task. If no command is specified, use the narrowest relevant regression runner:

- **C7 Phase 1**: `python tools/run_c7_phase1_regression.py`
- **C7 Phase 2**: `python tools/run_c7_regression.py`
- **C8**: `python tools/run_c8_regression.py`
- **C9**: `python tools/run_c9_regression.py`
- **C10**: `python tools/run_c10_regression.py`

## Visual-Review Warning

**PDF existence/non-empty checks do NOT prove visual compliance**. Layout changes require manual review against the applicable SECNAV figure. Do NOT assume document correctness based on file presence alone.

## Output Format

All responses must include the following fields when applicable:

```
file updated/created:
test result:
regression result:
commit hash:
push result:
warnings:
traceback:
git status:
git log --oneline -10:
```

---

*This is a Hermes-specific overlay. The shared SECNAV execution policy remains in `docs/OPENCLAW_INSTRUCTIONS.md`.*
