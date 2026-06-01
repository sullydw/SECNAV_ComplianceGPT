# Phase C Local Command Profile Promotion Checkpoint

**Created:** 2026-06-01  
**Verified Baseline Commit:** `a7f9aeb` — `CCI: Fix Phase B regression isolation`  
**Implementation Commit:** `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`  
**Previous Baseline:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Status:** Phase C implementation complete, regression-protected, and pushed to origin/main.

---

## What Was Implemented

Phase C adds user-approved local command profile promotion to the correction memory layer. When a user confirms promotion, `local_command_preference` corrections from the current session are written to a named profile as `override_rules` entries, preserving provenance, supporting disable/remove/edit, and respecting the merge priority stack.

### New Files

- `src/correction_promote.py` — Promotion logic with two-step approval workflow.
  - `is_eligible_for_promotion()` — strict eligibility gating.
  - `propose_promotion()` — Step 1 proposal with diff.
  - `confirm_and_write_promotion()` — Step 2 backup, validate, atomic write.
  - `list_promoted_corrections()`, `disable_promoted_correction()`, `remove_promoted_correction()`, `edit_promoted_correction()` — management APIs.
- `profiles/README.md` — Documents external real profile paths, fake vs real data, promotion behavior, and safety checklist.
- `tools/run_correction_profile_promotion_regression.py` — 33-check regression runner with temp-only fixtures.

### Modified Files

- `src/local_profile.py` — Extended `apply_profile_defaults()` to consume `override_rules` at Priority 3 in the merge stack.
  - Respects `doc_type_filter` and `component_filter`.
  - Skips `disabled: true` entries.
  - Validates `source`, `disabled`, `doc_type_filter`, `component_filter` in `validate_profile()`.
- `.gitignore` — Added `profiles/user/` as defense-in-depth against accidental real profile commits.

### Profile Safety Decisions

- Real profiles live externally:
  - **Windows:** `%USERPROFILE%\.secnav\profiles\`
  - **Linux/macOS:** `~/.config/secnav/profiles/`
- Repository `profiles/` directory contains only `example_local_profile.json` (fake data).
- `profiles/user/` is gitignored.
- Promotion to example profile is blocked by name pattern.
- No `--auto-approve` flag exists.
- No real profile data was committed during implementation.

### Merge Priority Stack (unchanged priorities, extended source)

| Priority | Source |
|---|---|
| 1 | Explicit payload values |
| 2 | `user_answers` from intake |
| 3 | Promoted profile corrections (`override_rules`) |
| 4 | Original profile `defaults` |
| 5 | Session corrections (`current_session`) |
| 6 | `active_draft` corrections |

### Schema Additions (backward compatible)

- `override_rules` entries now support:
  - `source: "user_promoted_correction"`
  - `disabled: true/false`
  - `doc_type_filter: [...]`
  - `component_filter: [...]`
- Optional top-level `correction_history` array and `promotion_metadata` object.

### Regression Coverage

The `tools/run_correction_profile_promotion_regression.py` runner exercises:

1. Eligibility: `local_command_preference` + `current_session` → eligible.
2. Proposal generated correctly.
3. Two-step approval required.
4. Blocked: `one_time_wording` classification.
5. Blocked: `possible_secnav_manual_rule` classification.
6. Blocked: `bug_validator_gap` classification.
7. Blocked: `user_rejected=True`.
8. Blocked: `validator_conflict=True`.
9. Blocked: example profile.
10. Blocked: ineligible field path.
11. Blocked: empty corrected value.
12. Blocked: placeholder value.
13. Backup created before write.
14. Field written into `override_rules` with `source` metadata.
15. `correction_history` entry created.
16. `promotion_metadata` updated.
17. `validate_profile()` passes before and after write.
18. `apply_profile_defaults()` respects promoted value at priority 3.
19. Payload still wins over promoted correction.
20. `user_answers` still wins over promoted correction.
21. Session correction lower priority than promoted profile correction.
22. `doc_type_filter` mismatch → override skipped.
23. `component_filter` mismatch → override skipped.
24. `disabled: true` → override skipped.
25. Remove promoted correction → field no longer applied.
26. Disable promoted correction → merge skips it.
27. Edit promoted correction → replacement works via full workflow.
28. External profile path resolution works.
29. No cross-profile accidental overwrite.
30. Schema backward compatibility (old profiles pass validation).
31. Field type mismatch → blocked.
32. Atomic write succeeds (temp + replace).
33. Old backup pruning (retention policy).

All 33 checks pass (0 failures).

---

## Regression Safety

### All 19 Regression Suites Pass

As of `8b8a95c`, all regression suites continue to pass:

- `run_intake_regression.py` — PASS
- `run_correction_regression.py` — PASS
- `run_correction_session_regression.py` — PASS
- `run_profile_regression.py` — PASS
- `run_cci_audit_regression.py` — PASS
- `run_context_schema_regression.py` — PASS
- `run_cci_subject_regression.py` — PASS
- `run_cci_ref_encl_regression.py` — PASS
- `run_cci_acronym_regression.py` — PASS
- `run_cci_date_time_regression.py` — PASS
- `run_cci_personnel_regression.py` — PASS
- `run_cci_poc_regression.py` — PASS
- `run_cci_routing_regression.py` — PASS
- `run_c7_phase1_regression.py` — PASS
- `run_c8_regression.py` — PASS
- `run_c9_regression.py` — PASS
- `run_c10_regression.py` — PASS
- `run_correction_classify_regression.py` — PASS
- `run_correction_profile_promotion_regression.py` — PASS (33 checks)

---

## What Was NOT Implemented

Phase C deliberately excluded the following items. They remain for future phases only after separate planning and approval.

1. **Pending global rule candidate log** — No `corrections/pending_corrections.jsonl` written (Phase D).
2. **Global rule promotion** — No corrections become SECNAV manual rules or validator updates (Phase E+).
3. **UI implementation** — No natural-language interface for promotion beyond orchestrator hooks.
4. **Renderer/layout changes** — No modifications to `src/pdf_v6_render.py` or layout profiles.
5. **Auto-cleanup of session stores** — 30-day retention remains advisory only.
6. **Cross-session promotion** — Only current session corrections are eligible.
7. **Auto-approve** — No automatic promotion flag or flow.

---

## Safety Notes

- Promotion requires explicit two-step user confirmation; no silent writes.
- Only `local_command_preference` + `current_session` corrections are eligible.
- Example profiles are blocked by name pattern check.
- Atomic writes (temp file + rename) prevent partial corruption.
- Backups are created before every write; last 10 retained.
- No real profile data was committed during implementation.
- `profiles/user/` is gitignored as defense-in-depth.
- The new regression runner uses temp-only synthetic fixtures (tempfile + NamedTemporaryFile + shutil.rmtree cleanup).
- No renderer/layout behavior changed.

---

## Key Files

- `docs/PROJECT_STATUS.md` — main status tracker.
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — long-term layer plan.
- `docs/planning/phase_c_local_command_profile_promotion_plan.md` — Phase C design plan.
- `docs/checkpoints/phase_b_correction_classification_checkpoint.md` — Phase B baseline checkpoint.
- `docs/checkpoints/phase_a_session_persistence_checkpoint.md` — Phase A baseline checkpoint.
- `src/correction_promote.py` — promotion logic implementation.
- `src/local_profile.py` — profile loading, validation, and merge priority stack.
- `profiles/README.md` — external profile safety documentation.
- `tools/run_correction_profile_promotion_regression.py` — Phase C regression runner.

---

## Next Recommended Phase

**Phase D: Pending Global Rule Candidate Log Planning (Planning Only)**

Considerations:

- How `possible_secnav_manual_rule` and `bug_validator_gap` corrections become logged candidates.
- Append-only `corrections/pending_corrections.jsonl` format.
- Review workflow: who reviews, how to promote or reject.
- Safety: never auto-apply; gitignore; no real command data.
- Regression coverage before implementation.

Phase D is **planning only** until reviewed and approved. Do not implement without explicit user direction. Keep global rule promotion out of Phase D planning unless explicitly scoped and approved.
