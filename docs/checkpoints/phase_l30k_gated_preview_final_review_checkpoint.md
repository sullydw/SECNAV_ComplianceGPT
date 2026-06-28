# Phase L.30K — Gated Preview and Final Review Loop

## Baseline Commit
`fa10fea` — `Tools: Enforce preview approval before finalize`

## Summary
Phase L.30K completes the controlled preview and final-review loop for the SECNAV conversational builder. It adds a read-only preview command, explicit user approval of the current draft preview, controlled revision that automatically clears stale approval, and enforcement that finalize/render require current approval.

## Sub-Phases

### L.30K-1 — Gated Read-Only Preview Command
- Added `preview` command to `tools/hermes_secnav_tool.py` and `tools/hermes_session_manager.py`
- Preview is strictly read-only: does not save, mutate payload, answer fields, confirm/reject/apply candidates, finalize, render, run live lookup, or create candidates
- Implements preview gate: `mode="build_status"` when minimum fields are missing; `mode="draft_preview"` once minimum completeness is met
- Minimum fields for `draft_preview`: `from`, `to`, `subj`, `body`, `date`, `signature.name` (or `signature` as usable signer)
- `build_status` output includes: known_fields, missing_for_preview, missing_required, pending/confirmed candidate summaries, validation_summary, render_gate, next_action, and a readable BUILD STATUS block
- `draft_preview` output includes: preview_text with `DRAFT PREVIEW  NOT FINAL`, body review label `[AI-DRAFTED OR USER-PROVIDED BODY  REVIEW REQUIRED]`, known fields rendered in letter-like order, and recommended next action

### L.30K-2 — Preview Approval State and Preview Hash
- Added `compute_preview_hash()` to `BuilderSession` for deterministic payload hashing of draft-relevant fields
- Added `record_approval()` to record explicit user approval with timestamp and hash snapshot
- Added `approval_state()` to compare current hash against approved hash, returning `approved_for_finalize`, `approved_at`, `approved_preview_hash`, `current_preview_hash`, `approval_current`
- Approval is invalidated automatically when any draft-relevant field changes (hash mismatch)

### L.30K-3 — Revision Command Clears Approval
- Added `revise` command to `tools/hermes_secnav_tool.py` and `tools/hermes_session_manager.py`
- Accepts `--text "field: new value"` format; supports body, from, to, subj, date, ssic, originator_code, signature.name, signature.role, signature.title
- Loads session, computes hash before and after applying the proposed change
- If payload changed (`hash_before != hash_after`), calls `clear_approval(reason="Draft-relevant revision applied")` to reset `approved_for_finalize=false`, `approved_at=None`, `approved_preview_hash=None`
- Does not finalize, render, apply candidates, confirm/reject candidates, or run live lookups
- Outputs: proposed_kv, applied_answers, preview_hash_before, preview_hash_after, payload_changed, approval_cleared, approval state, validation_summary, warning_summary

### L.30K-4 — Enforce Preview Approval Before Finalize/Render
- Added `_check_approval_gate()` helper to `tools/hermes_secnav_tool.py`
- Gate passes only when `approved_for_finalize=true` and `approval_current=true`
- `finalize` and `render` blocked before approval with error: `Draft preview not approved. Run 'approve' first.`
- If approval hash is stale (revision occurred after approval), gate fails with same message
- Manager wrappers (`tools/hermes_session_manager.py`) pass through `approval` and `approval_gate` fields in finalize/render JSON output
- No bypass flag added

## Preview Modes
- `build_status` — shown when session is incomplete; lists missing fields and next recommended action
- `draft_preview` — shown once minimum completeness is met; renders a readable draft preview with `NOT FINAL` label and body review notice

## Approval Hash Safety
- Hash covers all draft-relevant payload fields
- Any successful body/field revision clears approval automatically
- Re-approval is required after any draft-relevant change
- Prevents stale approval from finalizing an out-of-date draft

## Mutation Safety
- Preview: read-only, no session mutations
- Revise: modifies payload and session state, but never finalizes, renders, or applies candidates
- Finalize/Render: gated on current approval; fail fast before producing output if not approved

## Smoke Tests
- `tools/run_phase_l30k1_gated_preview_smoke.py` — verifies build_status vs draft_preview modes, preview gate, read-only safety, no mutations
- `tools/run_phase_l30k3_revise_clears_approval_smoke.py` — verifies approval recorded, revise clears it, preview shows stale state
- `tools/run_phase_l30k4_approval_gate_smoke.py` — verifies finalize blocked before approval, render blocked before approval (no PDF), approve then finalize succeeds, revise clears approval and blocks again, re-approve then finalize succeeds
- All targeted smoke tests passed

## Files Changed
- `src/conversational_builder.py` — `compute_preview_hash`, `record_approval`, `approval_state`, `clear_approval`
- `tools/hermes_secnav_tool.py` — `preview`, `approve`, `revise`, `finalize` (gated), `render` (gated)
- `tools/hermes_session_manager.py` — `preview`, `approve`, `revise`, `finalize` (pass-through), `render` (pass-through)

## Next Phase
TBD

## Date
2026-06-28
