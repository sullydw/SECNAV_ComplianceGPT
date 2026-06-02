# Phase F UI/Command Integration Plan

**Status:** Planning-only — awaiting approval before implementation  
**Baseline:** `058de87` — Phase E review/promotion utility complete  
**Scope:** Slash-command UI layer atop existing correction-memory APIs  
**Safety rule:** No renderer, validator, rule catalog, or automatic enforcement changes

---

## 1. Supported User-Facing Correction Commands

Phase F exposes a thin slash-command interface that maps structured instructions to the existing correction-memory API. Supported commands:

| Command | Purpose |
|---|---|
| `/correct <field> <value>` | Apply a correction to the active draft. |
| `/undo` | Revert the last active-draft correction. |
| `/remember [scope]` | After a correction, persist it to a chosen scope (session, profile, candidate). |
| `/session corrections` | List session-stored corrections for the current session_id. |
| `/accept <id>` / `/reject <id>` | Accept or reject a pre-applied session correction. |
| `/promote profile` | Start Phase C two-step promotion for the most recent active-draft or current-session correction. |
| `/log candidate` | Start Phase D explicit approval to write a pending global rule candidate for the most recent active-draft or current-session correction. |
| `/review pending` | List pending global rule candidates (Phase D → E bridge). |
| `/claim <candidate_id>` | Claim a candidate for review (Phase E). |
| `/decide <candidate_id> <approve\|reject\|defer\|supersede>` | Record a review decision (Phase E). |
| `/approved rules` | List approved global rule records (Phase E). |
| `/status` | Show active draft corrections, conflicts, and session state. |

The command layer does **not** add new storage formats or mutation paths. It is a dispatcher to `intake_orchestrator`, `correction_promote`, `correction_pending_log`, and `correction_review`.

**Natural-language parsing is deferred.** Phase F is strictly slash-command-only. Natural-language mediation may be proposed in a future Phase G plan.

---

## 2. How Users Apply a Correction to the Active Draft

Flow:

1. User issues a correction command.
2. **Parser** extracts `field_path` (e.g., `subj`, `from`, `body[1]`, `via[0]`) and `corrected_value`.
3. **Command layer** calls `intake_orchestrator.capture_correction()` with:
   - `scope="active_draft"`
   - `original_value` read from the current payload
   - `corrected_value` from user input
   - `field_path`, `doc_type`, `component` from current context
4. `intake_orchestrator` calls `correction_apply.apply_correction()` to mutate the in-memory payload.
5. `intake_orchestrator` calls `rerun_audit_after_correction()` to run the CCI audit on the modified payload.
6. Results returned to user: corrected draft + any new validator findings or conflicts.

The renderer is **not** invoked by the command layer. The caller (existing orchestration above the command layer) decides when to render.

---

## 3. How Users Choose Whether to Remember a Correction

After a correction is applied, the command layer presents a **scope selection prompt** based on the correction's classification (from Phase B). The user chooses one of:

| Scope | When Offered | Safety Gate |
|---|---|---|
| `active_draft` | Always; default. | No persistence. Undo available. |
| `current_session` | Offered if `session_id` is active. | Blocked if classification is `one_time_wording` unless user explicitly overrides. Calls `intake_orchestrator.persist_correction()`. |
| `local_command_profile` | Offered only if classification is `local_command_preference`. | Redirects to Phase C two-step approval workflow. Never silent. |
| `pending_global_rule_candidate` | Offered only if classification is `possible_secnav_manual_rule` or `bug_validator_gap`. | Redirects to Phase D explicit approval + sanitization workflow. Never auto-written. |

The command layer **reads** classification from `correction_classify.py` and uses it to filter available options. It does not reclassify or bypass classification gating.

---

## 4. How Users Review and Accept/Reject Session Corrections

When a draft begins, `intake_orchestrator._preapply_session_corrections()` may auto-apply stored session corrections. The command layer exposes:

- `/session corrections` — lists pre-applied corrections with IDs, field paths, and values.
- `/accept <id>` — confirms the pre-applied correction; no further action needed.
- `/reject <id>` — calls `intake_orchestrator.reject_session_correction(id)`, which soft-marks the record with `user_rejected=True`. Rejected records are excluded from future matching.

The UI must show pre-applied corrections clearly so the user knows the draft has been modified before they start editing.

---

## 5. How Users Promote Local Command Preferences (Phase C Safeguards)

`/promote profile` operates only on the **most recently applied correction** in the active draft or current session context. It does **not** accept arbitrary correction IDs.

Promotion flow:

1. Command layer identifies the most recent active-draft or current-session correction.
2. **Step 1 — Eligibility check:** verify classification is `local_command_preference` and field is eligible for profile override.
3. **Step 2 — Explicit confirmation:** present the exact rule that will be written to the external profile, the profile path, and a backup reminder.
4. On confirmation, `correction_promote` performs:
   - Backup of existing profile
   - Atomic write
   - Validation of new profile JSON
5. Command layer reports success/failure and the backup file path.
6. No profile change occurs without both steps confirmed by the user.

The command layer never writes directly to profile files. It delegates entirely to `correction_promote`.

---

## 6. How Users Log Possible Global Rule Candidates (Phase D Safeguards)

`/log candidate` operates only on the **most recently applied correction** in the active draft or current session context. It does **not** accept arbitrary correction IDs.

Logging flow:

1. Command layer identifies the most recent active-draft or current-session correction.
2. **Explicit approval required:** show a preview of the sanitized candidate record that would be appended to `corrections/pending_corrections.jsonl`.
3. User must type "confirm" or click an explicit approve action.
4. On approval, `correction_pending_log` performs:
   - Full PII sanitization (names, emails, phones, EDIPI, SSN, DoD ID, UIC, hull/tail, building/room)
   - Duplicate fingerprint check against existing candidates
   - Append-only JSONL write
5. Command layer returns the candidate ID and status.

Without user confirmation, nothing is written. The command layer cannot bypass this.

---

## 7. How Users Review/Promotion Records (Phase E Safeguards)

The review utility remains programmatic, but the command layer exposes human-readable bridges:

- `/review pending` → `correction_review.list_candidates_for_review()` with filters.
- `/claim <id>` → `correction_review.claim_candidate()`; single-reviewer local-only.
- `/decide <id> approve` → prompts for `rationale` and `evidence`:
  - `secnav_citation` required for `manual_rule` candidates
  - `validator_evidence` required for `bug_validator_gap` candidates
  - Empty rationale blocked
- On valid input, `correction_review.record_review_decision()` appends review metadata and creates an approved-rule record with `implementation_status="pending_implementation"`.
- `/approved rules` → `correction_review.load_approved_promotions()` (anonymized by default).

The command layer does **not** implement review logic; it only formats inputs/outputs for the Phase E API. All evidence validation, append-only metadata, and PII sanitization remain inside `correction_review.py`.

---

## 8. How the UI/Command Layer Calls Existing APIs Without Bypassing Safety Gates

Design principle: **The command layer is a dispatcher, not a gatekeeper.** All safety logic lives in the existing modules.

- **Correction application:** `intake_orchestrator.capture_correction()` → `correction_apply.apply_correction()`
- **Session persistence:** `intake_orchestrator.persist_correction()` (checks session_id, scope, classification)
- **Profile promotion:** `correction_promote.*` (eligibility, backup, atomic write)
- **Pending logging:** `correction_pending_log.*` (sanitization, duplicate check, append-only)
- **Review utility:** `correction_review.*` (evidence validation, status transitions)

The command layer is not allowed to:
- Open and write `corrections/session/*.jsonl` directly
- Open and write `profiles/*.json` directly
- Modify `src/cci_*.py` or rule catalogs
- Call the renderer with corrected payloads directly

It passes structured arguments and relays responses.

---

## 9. How to Prevent Accidental Automatic Promotion or Global Rule Enforcement

- **Default scope is `active_draft`.** Every correction starts as ephemeral unless the user explicitly chooses otherwise.
- **Multi-step confirmation for all persistence.**
  - Session: one confirmation + classification gate.
  - Profile: two-step Phase C workflow.
  - Candidate: explicit approval + preview.
  - Review decision: evidence fields + rationale required.
- **No background automation.** No cron, no auto-promote, no AI-initiated rule creation.
- **No single-command promotion.** `/promote` and `/decide approve` require interactive prompts.
- **Classification blocks inappropriate scopes.** A `one_time_wording` correction cannot be saved to session unless the user overrides, and cannot be promoted to profile or global candidate at all.
- **`/promote profile` and `/log candidate` are constrained to the most recent correction.** They cannot target arbitrary unattached IDs, preventing accidental promotion or logging of stale or unrelated corrections.

---

## 10. Required Command Syntax or Command Schema

Phase F supports **structured slash commands only.** Natural-language parsing is deferred to a future Phase G.

```text
/correct <field_path> <corrected_value>
/undo
/remember <active_draft|session|profile|candidate>
/session corrections
/accept <session_correction_id>
/reject <session_correction_id>
/promote profile
/log candidate
/review pending
/claim <candidate_id>
/decide <candidate_id> approve --rationale "..." --evidence "..."
/decide <candidate_id> reject --rationale "..."
/decide <candidate_id> defer --rationale "..."
/decide <candidate_id> supersede --rationale "..."
/approved rules
/status
```

All persistent or destructive commands require an explicit confirmation step.

---

## 11. Error Handling and Confirmation Prompts

| Scenario | Behavior |
|---|---|
| Invalid field path | Reject before apply; suggest valid fields from context schema. |
| Correction increases validator errors | Apply correction but surface advisory conflict; do not block unless user requests strict mode. |
| Missing `session_id` | Disable `/remember session`; inform user. |
| Profile promotion fails | Report backup location if available; do not leave partial profile writes. |
| Pending log duplicate detected | Warn user and show existing candidate ID instead of re-logging. |
| Review evidence missing | Block `/decide approve` and list required fields. |
| User rejects confirmation | Cancel operation; no state changed. |
| `/promote profile` or `/log candidate` with no recent correction | Error: "No recent correction to promote/log. Apply a correction first." |

All destructive or persistent actions require an explicit "confirm" step. Passive application (active draft only) does not require confirmation but supports `/undo`.

---

## 12. How to Surface Conflicts and Validator Warnings

After any `/correct` or session pre-application:

1. Run `validator_runner.run_audit()` on the modified payload.
2. Compare error count before vs after.
3. If errors increased, emit a `correction_conflict` advisory:
   - List new validator findings.
   - Show the field path and corrected value.
   - Offer `/undo` or `/accept conflict`.
4. If errors decreased or stayed same, emit standard validator summary (warnings only).

Conflicts are **advisory only**; they do not block the draft. The user may proceed, undo, or escalate the conflict to a `bug_validator_gap` candidate log.

---

## 13. How to Keep Renderer/Layout Behavior Untouched

- The command layer operates on the **JSON payload** produced by intake/context resolution.
- It never imports or calls `pdf_v6_render.py`.
- It does not modify layout profiles, figure measurements, or rendering constants.
- Corrections are applied to payload fields (strings, arrays, objects), not to PDF coordinates or styles.
- The existing orchestration layer (above Phase F) continues to own the render decision.

If a correction changes content that later affects layout (e.g., adding a Via line), the renderer handles it the same way it would handle that content coming from intake normally.

---

## 14. Required Regression Coverage

Before any Phase F implementation is merged, the following regression coverage must be defined:

| Suite | Checks |
|---|---|
| Command parsing regression | Valid/invalid slash commands; rejected natural-language inputs. |
| Scope selection regression | Correct options presented per classification; blocked options rejected. |
| Confirmation flow regression | Cancellation leaves no state; confirmation triggers correct downstream API. |
| API delegation regression | Mocked backend APIs receive correct arguments; no direct file writes from command layer. |
| Safety bypass negative tests | Attempts to skip classification gates, evidence requirements, or approval steps must fail. |
| Conflict surfacing regression | Conflict advisory emitted when audit errors increase; undo restores prior state. |
| Session review regression | Accept/reject session corrections updates store correctly. |
| No-side-effect regression | Command layer tests prove no renderer, validator, or catalog files are modified. |
| Promotion/candidate constraint regression | `/promote profile` and `/log candidate` reject calls with no recent correction; accept only most-recent correction. |

Minimum new runner: `tools/run_correction_command_regression.py` with ≥20 checks.

All 21 existing regression suites must continue to pass unchanged.

---

## 15. Files That Would Be Added or Changed in Future Implementation

**New files (to be created only after plan approval):**

- `src/correction_commands.py` — Command parser, dispatcher, confirmation prompt builder, and user-facing message formatter.
- `tools/run_correction_command_regression.py` — Phase F regression runner.
- `docs/checkpoints/phase_f_ui_command_integration_checkpoint.md` — Post-implementation checkpoint (future).

**Likely updated files (minimal, wrapper-only changes):**

- `src/intake_orchestrator.py` — Potentially expose `propose_pending_log()` and `get_review_status()` as public helpers if not already exposed; no logic changes.
- `docs/PROJECT_STATUS.md` — Updated after implementation to list Phase F complete.

**Not touched:**

- `src/pdf_v6_render.py`
- `src/cci_*.py` validators
- `rules_v6/` rule catalogs
- `src/correction_apply.py`, `src/correction_capture.py`, `src/correction_classify.py`, `src/correction_promote.py`, `src/correction_pending_log.py`, `src/correction_review.py`, `src/correction_store.py` — unless a required API is missing; in that case, a separate mini-plan is needed.

---

## 16. What Phase F Must NOT Do

Phase F is strictly UI/command integration. It must not:

- **Change renderer or layout behavior** — no PDF coordinate, font, or figure modifications.
- **Change validators or rule catalogs** — no new CCI rules, no validator edits, no catalog updates.
- **Implement automatic global rule enforcement** — approved records remain `pending_implementation`.
- **Allow AI-only promotion decisions** — all profile promotions, candidate logs, and review decisions require explicit human confirmation.
- **Commit real command or user data** — no profiles, session JSONL, pending logs, or approved records enter the git tree.
- **Enable silent profile/global promotion** — every persistent action requires interactive confirmation.
- **Add background automation** — no cron, no daemon, no auto-review, no auto-cleanup.
- **Bypass Phase C, D, or E safety gates** — the command layer delegates; it does not reimplement or weaken gates.
- **Implement natural-language parsing** — deferred to a future Phase G plan.

---

## Recommended Phase F Implementation Sequence

If this plan is approved, implement in this order:

1. **Finalize the command schema** — slash-command signatures only.
2. **Create `src/correction_commands.py` skeleton** — dispatcher with no-op passthroughs; prove import chain does not break existing tests.
3. **Implement `/correct` and `/undo`** — map to `intake_orchestrator` active-draft flow only.
4. **Run all 21 existing regressions** — confirm zero breakage.
5. **Implement `/remember` scope selection** — active draft → session → profile → candidate, gated by classification.
6. **Implement `/session corrections`, `/accept`, `/reject`** — read-only and soft-reject only.
7. **Implement `/promote profile` bridge** — constrained to most recent correction; calls Phase C API with two-step confirmation UI.
8. **Implement `/log candidate` bridge** — constrained to most recent correction; calls Phase D API with explicit approval UI.
9. **Implement `/review pending`, `/claim`, `/decide` bridge** — call Phase E API with evidence prompts.
10. **Write `tools/run_correction_command_regression.py`** — ≥20 checks, all passing.
11. **Run full 22-suite regression** (21 existing + 1 new).
12. **Update `docs/PROJECT_STATUS.md`** and create `docs/checkpoints/phase_f_ui_command_integration_checkpoint.md`.
13. **Commit:** `CCI: Add UI/command integration (Phase F)`

---

## Open Questions Needing Approval

1. **Interface target:** Should Phase F remain CLI-only (Hermes terminal), or is a lightweight web/dashboard UI in scope? A web UI is significantly larger.
2. **Session correction preview:** Should pre-applied session corrections be shown inline in the draft (e.g., highlighted suggestions) or only via `/session corrections` list?
3. **Strict mode option:** Should there be a user setting that blocks draft generation when a correction conflict is detected, or keep conflicts advisory-only forever?
4. **Multi-user review:** Is local single-reviewer claim sufficient, or should Phase F plan for multi-user claim/locking? Multi-user requires a different persistence model.
5. **Natural-language parsing:** Deferred to Phase G. Should Phase G also include AI-suggested corrections, or only NL-to-slash translation?

---

*End of Phase F planning document.*

*Approve, revise, or reject. No implementation code will be written until you confirm.*
