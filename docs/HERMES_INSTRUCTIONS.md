# Hermes Execution Instructions

## Required Reading Order

**Hermes Agent must first read and follow these documents in order**:

1. `docs/OPENCLAW_INSTRUCTIONS.md` - Shared SECNAV execution policy
2. `docs/HERMES_INSTRUCTIONS.md` - Hermes-specific overlay (this file)
3. `docs/PROJECT_STATUS.md` - Current project status
4. `HEARTBEAT.md` - HEARTBEAT signal requirements

## Policy Relationship

**docs/HERMES_INSTRUCTIONS.md is an overlay for Hermes behavior only**. docs/OPENCLAW_INSTRUCTIONS.md remains the authoritative shared SECNAV execution policy. Do not duplicate OpenClaw policy in this file; only add Hermes-specific workflow differences.

## Hermes-Specific Repository Safety Rule

Hermes must use this working directory for SECNAV_ComplianceGPT work:

```text
C:\Users\drryl\SECNAV_ComplianceGPT
```

The full repository preflight is **not required before every task**. To conserve context and tool resources, use the full preflight only when:

- starting a new Hermes session
- the working directory is uncertain
- the remote/history looks suspicious
- a push is rejected
- Git reports unrelated history
- the user explicitly asks for verification

Full preflight command when needed:

```bat
cd C:\Users\drryl\SECNAV_ComplianceGPT
git remote -v
git branch --show-current
git log --oneline -5
git status
```

Hard safety rules still apply:

- Do not work from any Hermes/OpenClaw app directory
- Do not change Git remotes during normal task execution
- Use normal pushes only: `git push origin main`
- Stop and report if the remote points to Hermes, OpenClaw, NousResearch, or any repo other than `sullydw/SECNAV_ComplianceGPT`

## Hermes-Specific Workflow Rules

- Use TUI or terminal-first workflow (leveraging Hermes' terminal/TUI capabilities)
- Use explicit shell commands to perform operations
- Confirm you're at the correct repository root before making edits when the session or path is uncertain
- Run `git status` before commit and after commit to verify changes
- Do NOT operate from workspace/root directories outside the repository
- Do NOT create loose files outside the repository boundaries
- Do NOT work from any Hermes/OpenClaw app directory
- Do NOT change Git remotes during normal task execution

## Sync Rule

Before making code edits in a long-running or uncertain session:

1. Run `git fetch origin`
2. Check if local branch is behind origin/main
3. If behind, run git pull/rebase before editing
4. If conflicts occur, **STOP and report** immediately

For small follow-up tasks in a known-clean active session, do not repeat sync commands unless needed.

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