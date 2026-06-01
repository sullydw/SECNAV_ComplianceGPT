# Phase D Pending Global Rule Candidate Logging Checkpoint

**Implementation commit:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`  
**Date:** 2026-06-01  
**Verifier status:** Working tree clean, all 20 regression suites passed locally

---

## Scope

Phase D implements a safe, append-only pending candidate log for global rule corrections. It logs corrections classified as `possible_secnav_manual_rule` or `bug_validator_gap` without auto-applying them or promoting them to global rules.

### What was implemented

1. **`src/correction_pending_log.py`** (527 lines)
   - `is_eligible_for_pending_log(correction)` — deterministic eligibility gates
   - `propose_pending_log(correction)` — builds a candidate record proposal
   - `confirm_and_write_pending_log(log_file, proposal)` — writes only on explicit `user_confirmed=True`
   - `_sanitize_value(value)` — covers EDIPI, SSN, DoD ID, UIC, hull/tail numbers, building/room numbers, emails, phone numbers, addresses, command names, person names
   - `_compute_fingerprint(record)` — deterministic duplicate detection
   - `list_pending_candidates(log_file, status=None, correction_type=None)` — read/filter helper
   - `update_candidate_status(log_file, candidate_id, new_status, review_note=None)` — status transitions
   - Statuses: `pending`, `under_review`, `deferred`, `rejected`, `promoted`, `superseded`
   - `body.*` paths are blocked from eligibility
   - Duplicate candidates are skipped or warned (not merged)

2. **`tools/run_correction_pending_regression.py`** (500 lines, 33 checks)
   - Uses only `tempfile.NamedTemporaryFile()` for pending log fixtures
   - Never writes to real `corrections/pending_corrections.jsonl`
   - Covers eligibility, sanitization, JSONL format, required fields, status transitions, duplicate handling, misclassifications, and missing-file resilience

3. **`corrections/README.md`** (new)
   - Documents `session/` and `pending_corrections.jsonl` as local-only
   - States both are gitignored
   - References `corrections/session/README.md` for session detail
   - Minimal, non-repetitive content

4. **`src/intake_orchestrator.py`** (+28 lines)
   - Added `propose_pending_log(self, correction)` method
   - Opt-in hook; does not write to disk automatically
   - Caller must explicitly confirm before any write

### Eligibility rules (implemented)

- Allowed correction types:
  - `possible_secnav_manual_rule`
  - `bug_validator_gap`
- Required gates:
  - `scope == "current_session"`
  - Current active session only
  - Explicit user approval required before logging
  - Not `user_rejected=True`
  - Not `validator_conflict=True`
  - Not placeholder or empty corrected value
  - Not duplicate `pending`/`under_review` candidate
  - Not `body.*` field path
- Blocked correction types:
  - `one_time_wording`
  - `local_command_preference`
  - `active_draft` only
  - `unknown`

### Candidate record schema (implemented)

All required fields are present:

- `candidate_id`
- `recorded_at`
- `status` (defaults to `pending`)
- `correction_type`
- `field_path`
- `original_value_sanitized`
- `sanitized_value`
- `doc_type`
- `component`
- `user_reason`
- `classification_confidence`
- `classification_method`
- `source_correction_id`
- `session_id`
- `review_metadata` (null until review)
- `duplicate_of` (null unless known duplicate)

### Sanitization coverage (implemented)

| Token | Pattern |
|---|---|
| `[EDIPI]` | 10-digit number |
| `[SSN]` | `ddd-dd-dddd` |
| `[DOD_ID]` | `N` followed by 7-9 digits |
| `[UIC]` | 4-6 uppercase alphanumeric; not 10 digits |
| `[HULL_NUMBER]` | USS/PCU/SSN + number |
| `[TAIL_NUMBER]` | Tail number or squadron prefix |
| `[BUILDING]` | Bldg/Building variants |
| `[ROOM]` | Rm/Room variants |
| `[EMAIL]` | Email pattern |
| `[PHONE]` | Phone number pattern (with/without parentheses) |
| `[ADDRESS]` | Street/city/state/zip pattern |
| `[COMMAND_NAME]` | USMC/Navy command keywords |
| `[SIGNATORY]` / `[POC_NAME]` / `[ADDRESSEE]` / `[REDACTED_VALUE]` | Person-name tokens |

### What was NOT implemented (by design)

- Global rule promotion
- Review/promotion utility
- Validator or rule catalog changes
- Renderer/layout changes
- UI implementation
- Automatic logging without explicit approval
- Cross-session logging
- Duplicate auto-merge
- Profile promotion changes
- Real command or user data committed

### Regression results

All 20 suites passed (0 failures):

| Runner | Phase | Result |
|---|---|---|
| run_intake_regression.py | Intake | PASS |
| run_correction_regression.py | Active-draft | PASS |
| run_correction_session_regression.py | A | PASS |
| run_correction_classify_regression.py | B | PASS |
| run_correction_profile_promotion_regression.py | C | PASS |
| run_correction_pending_regression.py | D | PASS (33/33) |
| run_profile_regression.py | Profile | PASS |
| run_cci_audit_regression.py | Audit | PASS |
| run_context_schema_regression.py | Context | PASS |
| run_cci_subject_regression.py | CCI | PASS |
| run_cci_ref_encl_regression.py | CCI | PASS |
| run_cci_acronym_regression.py | CCI | PASS |
| run_cci_date_time_regression.py | CCI | PASS |
| run_cci_personnel_regression.py | CCI | PASS |
| run_cci_poc_regression.py | CCI | PASS |
| run_cci_routing_regression.py | CCI | PASS |
| run_c7_phase1_regression.py | Layout | PASS |
| run_c8_regression.py | Layout | PASS |
| run_c9_regression.py | Layout | PASS |
| run_c10_regression.py | Layout | PASS |

### Safety checklist

- [x] `corrections/pending_corrections.jsonl` is in `.gitignore`
- [x] Runner never touches real `corrections/pending_corrections.jsonl`
- [x] Sanitization strips PII before any candidate record is written
- [x] `body.*` paths are blocked from candidate eligibility
- [x] `user_confirmed=True` is required for every write
- [x] `propose_pending_log()` does not write; only returns a proposal dict
- [x] No renderer or validator changes were made
- [x] No real command/user data was committed

### Known decision records

- **Sanitization is heuristic, not perfect.** The `_sanitize_value()` function attempts to replace identifiable tokens but may miss edge cases. If `confidence` is `low`, the caller should surface a warning.
- **No `[PERSON_NAME]` fallback is used.** If the person-name regexes miss a value, it remains in the sanitized string. This is considered safer than aggressive redaction that could remove structural information.

### Next recommended phase

**Phase E — Review/Promotion Utility (planning only).**

Phase E should define a human or AI-assisted review workflow for pending global rule candidates, criteria for promoting a candidate to `approved_global_rule`, and UI/command integration considerations if needed.

Do not implement Phase E until its plan is reviewed and approved. Phase E is strictly review/promotion utility planning, not automatic global rule activation.

---

## How to resume from this checkpoint

1. Read `docs/PROJECT_STATUS.md` for current context.
2. Read `docs/planning/correction_memory_and_rule_promotion_plan.md` for the master roadmap.
3. Read `docs/checkpoints/phase_c_local_command_profile_promotion_checkpoint.md` for Phase C context if needed.
4. Read `docs/checkpoints/phase_b_correction_classification_checkpoint.md` for Phase B context if needed.
5. Read `docs/checkpoints/phase_a_session_persistence_checkpoint.md` for Phase A context if needed.
6. If continuing implementation, run all 20 regression suites before committing.
7. Do not modify renderer/layout unless explicitly asked.

---

*This checkpoint marks the completion of Phase D pending global rule candidate logging. The system is ready for Phase E planning when approved.*
