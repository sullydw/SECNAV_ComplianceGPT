# Phase F UI/Command Integration Checkpoint

**Status:** Implemented  
**Implementation commit:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`  
**Previous baseline:** `058de87` — Phase E review/promotion utility  
**Date:** 2026-06-02  
**Branch:** `main`  
**Regression:** All 22 suites PASS at `4ba5cd3`

---

## What Was Implemented

Phase F adds a slash-command dispatcher layer that exposes correction-memory functionality to users without requiring raw JSON path editing. It is strictly a command/UI integration layer; all persistence, promotion, and review logic continues to live in Phase A-E modules.

### New files

- `src/correction_commands.py` — `CorrectionCommandDispatcher` class.
  - Slash-command parser (`_parse_command`).
  - Command dispatcher (`dispatch()` + internal `_run_*` handlers).
  - Confirmation prompt builder (`build_confirmation_prompt()`).
  - User-facing message formatter (`format_message()`).
- `tools/run_correction_command_regression.py` — 30 checks, 45 sub-assertions. All PASS.

### Supported commands

| Command | Description | Delegates to |
|---|---|---|
| `/correct <field> <value>` | Apply a correction to the active draft. | `intake_orchestrator.apply_correction()` |
| `/undo` | Revert the most recent correction. | `intake_orchestrator.undo_correction()` |
| `/remember session` | Persist current-session corrections to JSONL. | `intake_orchestrator` + `correction_store` |
| `/session corrections` | List corrections in the current session. | `correction_store` |
| `/accept <id>` | Accept a session correction for future reuse. | `correction_store` |
| `/reject <id>` | Reject a session correction (soft-mark). | `correction_store` |
| `/promote profile` | Promote the most recent correction to a local profile. | `correction_promote` |
| `/log candidate` | Log the most recent correction as a pending global candidate. | `correction_pending_log` |
| `/review pending` | List pending global rule candidates for review. | `correction_review` |
| `/claim <candidate_id>` | Claim a candidate for review. | `correction_review` |
| `/decide <candidate_id> approve\|reject\|defer\|supersede` | Record a review decision. | `correction_review` |
| `/approved rules` | List approved global rule promotions. | `correction_review` |
| `/status` | Show orchestrator status (corrections, conflicts, profile, session). | `intake_orchestrator.get_status()` |

### Safety constraints enforced by the command layer

- **Slash-command only.** No natural-language parsing is implemented in Phase F; that is deferred to Phase G planning.
- **No direct persistence writes.** The command layer delegates to existing Phase A-E APIs (`intake_orchestrator`, `correction_promote`, `correction_pending_log`, `correction_review`, `correction_store`). It never writes directly to session JSONL, pending logs, approved promotion records, profile files, rule catalogs, validators, or renderer files.
- **Confirmation required for persistent actions.** `/promote profile`, `/log candidate`, `/remember session`, `/accept`, and `/decide approve` all require an explicit `confirmed=True` flag or return a preview message first.
- **Constrained promotion/candidate scope.** `/promote profile` and `/log candidate` may operate only on:
  - the most recently applied active-draft correction, or
  - a correction in the current session context.
  Arbitrary unattached correction IDs are rejected.
- **Review API name alignment.** `/decide approve` calls `correction_review.review_candidate()`, matching the actual Phase E API surface.
- **Approved records remain pending.** Any approved global rule promotion created via `/decide approve` carries `implementation_status="pending_implementation"`. No validator, catalog, or renderer changes occur.

### What is NOT in Phase F

- Natural-language parsing (deferred to Phase G planning).
- Web UI or CLI menu system (the dispatcher is a library interface; UI wiring is future work).
- Automatic global rule enforcement.
- AI-only promotion decisions.
- Silent profile or global promotion.
- Background automation, cron, or daemon processes.
- Changes to renderer, validators, or rule catalogs.

---

## Regression Results

The new command regression runner covers:

- Command parsing and validation.
- `/correct` apply and require-args guard.
- `/undo` revert and empty-failure guard.
- `/remember session` persistence and one-time wording block.
- `/session corrections` listing.
- `/reject` session correction.
- `/promote profile` eligibility, confirmation, and wrong-type block.
- `/log candidate` eligibility, confirmation, and wrong-type block.
- `/status` output shape.
- Unknown command and non-slash rejection.
- `/decide` argument validation and invalid-decision guard.
- Confirmation helper behavior.
- Dispatcher state isolation (last-correction tracking).
- Multiple corrections ordering.
- No direct file writes in dispatcher.
- Empty command rejection.
- Dict return-type consistency.

Results: **45 passed / 45 total** (30 checks, 45 sub-assertions).

Full suite at `4ba5cd3`:

- All 22 regression suites PASS.
- No new failures in C7-C10, CCI, intake, profile, correction, session, classification, promotion, pending, or review suites.

---

## Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| Renderer/layout unchanged | Preserved |
| Validators unchanged | Preserved |
| Rule catalogs unchanged | Preserved |
| No automatic global rule enforcement | Preserved |
| No AI-only promotion decisions | Preserved |
| No silent profile/global promotion | Preserved |
| No background automation | Preserved |
| No real command/user data committed | Preserved |
| No session JSONL committed | Preserved |
| No pending logs committed | Preserved |
| No approved promotion logs committed | Preserved |
| No profile files committed | Preserved |

---

## Next Recommended Phase

**Phase G — Natural-Language Command Mediation Planning**

Phase G is planning-only until approved. It should define:

- How natural-language user input is parsed into the slash-command structures already defined in Phase F.
- Whether a lightweight intent classifier or keyword matcher is sufficient.
- How ambiguous input is handled (confirmation prompts, fallback to slash commands, or refusal).
- Safety: no automatic promotion, no validator/catalog changes, no renderer changes.
- Regression requirements before implementation.

Do not implement Phase G without explicit approval.

---

## Files Referenced

- `src/correction_commands.py`
- `tools/run_correction_command_regression.py`
- `docs/planning/phase_f_ui_command_integration_plan.md`
- `docs/PROJECT_STATUS.md`
- `docs/planning/correction_memory_and_rule_promotion_plan.md`

---

## Checkpoint Authorship

This checkpoint was generated as part of the Phase F documentation handoff. It records the implementation state immediately after commit `4ba5cd3`.
