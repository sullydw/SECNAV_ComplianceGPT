# Phase C Local Command Profile Promotion Plan

**Status:** Planning-only — not approved for implementation  
**Created:** 2026-06-01  
**Current baseline:** `ac20c1a` — `Docs: Record Phase B correction classification checkpoint`  
**Phase B implementation:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Phase A implementation:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`

---

## 1. Eligible Corrections for Profile Promotion

Only corrections meeting **all** of the following criteria are eligible:

| Criterion | Requirement |
|---|---|
| **Classification** | `correction_type == "local_command_preference"` |
| **Scope** | Originally captured with `scope="current_session"` |
| **Field path** | One of: `from`, `to`, `signature`, `point_of_contact`, `ssic`, `originator_code`, `unit_identity`, `letterhead_lines` |
| **User approval** | Explicit user confirmation received via the two-step approval workflow |
| **No validator conflict** | The correction did not trigger `validator_conflict=True` |
| **Not previously rejected** | The session correction is not soft-marked `user_rejected=True` |
| **Value stability** | The corrected value is non-empty and not a placeholder like "TBD" or "TODO" |
| **Session recency** | Correction belongs to the current active session only (see Section 6) |

Rationale: `local_command_preference` represents recurring command-specific defaults. Requiring `current_session` scope proves the user wants reuse beyond a single draft.

---

## 2. Ineligible Corrections (Must Be Rejected or Redirected)

| Classification | Why Ineligible | Redirect Action |
|---|---|---|
| `one_time_wording` | By definition transient | Keep in session scope only |
| `possible_secnav_manual_rule` | May affect all users | Future Phase D pending candidate log only |
| `bug_validator_gap` | Indicates code/prompt issue | Future Phase D pending candidate log only |
| `active_draft` only scope | No persistence proven | Require `current_session` scope first |
| `user_rejected=True` | User declined reuse | Exclude permanently |
| `validator_conflict=True` | Contradicts deterministic validator | Block and surface conflict |
| Body/text fields (`body.*`, `subj`) | Content varies per document | Keep in session scope only |
| Older-session corrections | Out of current active session scope | Defer to future planning |

---

## 3. Approval Workflow (Mandatory Two-Step Confirmation)

Step 1 — Promotion Proposal:

```
PROPOSED PROFILE UPDATE
Profile: <profile_id>
Field: <field_path>
Current profile value: <existing_value_or_null>
Corrected value: <corrected_value>
Document types: <doc_type(s)>
Component: <component>

Approve adding this to profile? (yes/no/review)
```

Step 2 — Write Confirmation:

```
PROFILE UPDATE CONFIRMED
Field: <field_path>
New value: <corrected_value>
Old value: <previous_value_or_null>

This will affect future drafts for: <doc_types> / <component>
```

Safety rule: No profile write occurs unless both steps complete. There is no silent promotion and no `--auto-approve` flag in Phase C.

---

## 4. Real Profile Storage (Approved Decision)

Real user and command profiles **must not** be stored inside the repository.

- **Repository `profiles/` directory:** Only `example_local_profile.json` (fake example data) may exist.
- **Real profiles:** Use an external directory outside version control.
  - **Windows:** `%USERPROFILE%\.secnav\profiles\`
  - **Linux/macOS:** `~/.config/secnav/profiles/`
- `src/local_profile.py` `load_profile()` already accepts direct file paths, so external resolution is compatible with existing APIs.
- If the user attempts promotion but no real profile exists, abort with: "Create a real profile first. See profiles/README.md."

---

## 5. Profile Write and Backup Behavior (Approved Decision)

When a correction is approved for promotion to profile `<profile_id>`:

1. Load the existing profile from its external resolved path.
2. Create a timestamped backup: `<profile>.json.backup.<timestamp>` in the same directory.
3. Append the promoted correction as an entry in the profile's `override_rules` array with `source: "user_promoted_correction"`.
4. Add a history entry to `correction_history`.
5. Update `promotion_metadata.last_promoted_at` and increment `promotion_metadata.promotion_count`.
6. Validate the mutated profile with `validate_profile()` before writing.
7. Write atomically (temp file + `os.replace()`).

**Backup retention:** Keep the last 10 backups per profile. Older backups may be removed during subsequent promotion writes.

**Profile size:** Warn if the resulting profile JSON exceeds 100 KB. Do not hard-block solely on size unless `validate_profile()` fails.

**Promotion target:** Write into `override_rules`, not directly into plain `defaults`. This preserves provenance and allows disable/remove without affecting static defaults.

---

## 6. Preventing Accidental Profile Overwrite

| Safeguard | Implementation |
|---|---|
| Backup before write | Mandatory timestamped backup, last 10 retained |
| Validation gate | `validate_profile()` on mutated dict; abort if errors |
| Field type consistency | Reject if new value type differs from existing default type |
| Atomic write | Temp file + `os.replace()` |
| No cross-profile overwrite | Promotion must specify target `profile_id` |
| Read-only example guard | If resolved path includes "example", block with error |
| Explicit confirmation | Two-step approval; no auto-approve in Phase C |

---

## 7. Conflict Priority Stack

Resolution order when preparing a draft (unchanged by Phase C):

| Priority | Source |
|---|---|
| 1 | Explicit payload values |
| 2 | `user_answers` from intake |
| 3 | Promoted profile corrections (`override_rules` or `defaults`) |
| 4 | Original profile `defaults` |
| 5 | Session corrections (`current_session`) |
| 6 | `active_draft` corrections |

Rules:
- Profile wins over session (user explicitly approved promotion).
- `user_answers` wins over profile (real-time explicit choice).
- Payload wins over all.

Phase C must not change the existing merge priority in `apply_profile_defaults()`. Promoted corrections fold into the profile schema so existing logic handles them naturally.

---

## 8. Disable, Edit, or Remove Promoted Corrections

| Mechanism | How |
|---|---|
| Disable | Add `disabled: true` to the `override_rules` entry; `apply_profile_defaults()` skips it |
| Edit | Re-promote a new correction for the same field; approval workflow shows diff and asks to replace |
| Remove | `remove_profile_correction(profile_id, field_path)` deletes the matching `override_rules` entry with confirmation |

 Minimum API surface for future implementation:
- `list_promoted_corrections(profile_id)` — show all promoted entries
- `remove_promoted_correction(profile_id, field_path)` — delete with confirmation
- `disable_promoted_correction(profile_id, field_path)` — soft-disable

---

## 9. Schema Additions (Backward Compatible)

`LOCAL_PROFILE_V1` requires these optional additions:

### `correction_history` array
```json
"correction_history": [
  {
    "field_path": "from",
    "previous_value": "...",
    "corrected_value": "...",
    "promoted_at": "2026-06-01T12:00:00Z",
    "doc_type": "standard_letter",
    "component": "marine_corps",
    "session_correction_id": "<id>"
  }
]
```

### `promotion_metadata` object
```json
"promotion_metadata": {
  "last_promoted_at": "2026-06-01T12:00:00Z",
  "promotion_count": 1
}
```

### `override_rules` entry additions
```json
{
  "field_path": "from",
  "value": "...",
  "doc_type_filter": ["standard_letter"],
  "component_filter": ["marine_corps"],
  "source": "user_promoted_correction",
  "disabled": false
}
```

Validation update required:
- Allow `source` and `disabled` in `override_rules` entries.
- Allow optional `correction_history` and `promotion_metadata` at top level.

---

## 10. Required Regression Coverage (23+ Checks Before Implementation)

New runner: `tools/run_correction_profile_promotion_regression.py`

| # | Check |
|---|---|
| 1 | `local_command_preference` + `current_session` → proposal generated |
| 2 | Two-step approval required |
| 3 | Profile backup created before write |
| 4 | Field written into `override_rules` with `source` metadata |
| 5 | `history` entry created |
| 6 | `validate_profile()` passes |
| 7 | `apply_profile_defaults()` respects promoted value at priority 3 |
| 8 | Payload still wins over promoted correction |
| 9 | `user_answers` still wins over promoted correction |
| 10 | Session correction lower priority than promoted profile correction |
| 11 | `one_time_wording` → promotion blocked |
| 12 | `possible_secnav_manual_rule` → promotion blocked |
| 13 | `bug_validator_gap` → promotion blocked |
| 14 | `validator_conflict=True` → promotion blocked |
| 15 | `user_rejected=True` → promotion blocked |
| 16 | Promotion to example profile → blocked |
| 17 | Field type mismatch → promotion blocked |
| 18 | Disable promoted correction → skipped by merge |
| 19 | Remove promoted correction → field no longer applied |
| 20 | Edit promoted correction → replacement workflow works |
| 21 | External profile path resolution works |
| 22 | No cross-profile accidental overwrite |
| 23 | Schema backward compatibility (old profiles pass validation) |

---

## 11. Files to Add or Change in Future Implementation

### New files
- `src/correction_promote.py` — promotion logic
- `tools/run_correction_profile_promotion_regression.py` — 23+ check runner
- `docs/checkpoints/phase_c_local_command_profile_promotion_checkpoint.md` — post-impl checkpoint

### Modified files
- `src/local_profile.py` — validate new schema fields, handle `disabled` in rules
- `src/intake_orchestrator.py` — hook promotion proposal after session pre-application
- `profiles/README.md` — document external profile path and safety rules

### Unchanged
- Renderer, layout profiles, `src/correction_classify.py`, `src/correction_capture.py`, `profiles/example_local_profile.json`

---

## 12. What Phase C Must NOT Do

- No global rule promotion (Phase E+)
- No pending global rule candidate log (Phase D)
- No renderer/layout changes
- No UI implementation unless separately approved
- No real profile data committed to public repository
- No silent or automatic promotion
- No `--auto-approve` flag
- No promotion of older-session corrections
- No promotion of `one_time_wording`, `possible_secnav_manual_rule`, or `bug_validator_gap`
- No AI-powered classification changes

---

## 13. Recommended Implementation Sequence (If Approved)

1. Create `profiles/README.md` with external profile path instructions.
2. Add schema additions to `LOCAL_PROFILE_V1` (backward compatible).
3. Update `validate_profile()` in `src/local_profile.py`.
4. Create `src/correction_promote.py`.
5. Hook promotion proposal into `src/intake_orchestrator.py`.
6. Write regression runner (23+ checks).
7. Run full regression suite (all 18 existing + new runner).
8. Commit: `CCI: Add local command profile promotion (Phase C)`.
9. Create checkpoint and update status docs.

---

## 14. Decisions Resolved

| # | Decision | Resolution |
|---|---|---|
| 1 | Real profile storage | External directory (`%USERPROFILE%\.secnav\profiles\` on Windows, `~/.config/secnav/profiles/` on Unix) |
| 2 | Promotion target | `override_rules` array with `source` metadata |
| 3 | Backup retention | Last 10 backups per profile |
| 4 | Profile size | Warn at 100 KB; do not hard-block unless validation fails |
| 5 | Auto-approval | Not implemented in Phase C; two-step confirmation required |
| 6 | Cross-session promotion | Current active session only; older sessions deferred |
