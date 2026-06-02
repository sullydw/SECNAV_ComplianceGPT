# Phase E Review/Promotion Utility Plan

**Status:** Planning-only — not approved for implementation  
**Created:** 2026-06-01  
**Current verified baseline:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`  
**Phase D implementation:** `2e31892` — `CCI: Add pending global rule candidate logging (Phase D)`  
**Phase C implementation:** `8b8a95c` — `CCI: Add local command profile promotion (Phase C)`  
**Phase B implementation:** `519fad6` — `CCI: Add correction classification (Phase B)`  
**Phase A implementation:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`

---

## 1. Purpose

Phase E defines a human or AI-assisted review workflow for pending global rule candidates created in Phase D. It provides structured decision-making, evidence gathering, and status transition management to promote or reject candidates safely. Phase E does **not** automatically modify validators, rule catalogs, or the renderer. Promotion means creating an `approved_global_rule` record only; actual validator/rule catalog changes require separate, explicit approval after Phase E.

---

## 2. Review Eligibility

Only candidates meeting **all** of the following are eligible for Phase E review:

| Criterion | Requirement |
|---|---|
| **Source** | Record exists in `corrections/pending_corrections.jsonl` |
| **Initial status** | `status` is `"pending"` or `"under_review"` |
| **Classification** | `correction_type` is `"possible_secnav_manual_rule"` or `"bug_validator_gap"` |
| **Not superseded** | No later candidate with `status="promoted"` covers the same `(field_path, doc_type, component)` fingerprint |
| **Not already promoted** | The same fingerprint is not already present in a future `corrections/approved_rule_promotions.json` |
| **Sanitization verified** | `sanitized_value` contains at least one structural token (e.g., `[COMMAND_NAME]`, field pattern) or the record is flagged for low-confidence review |
| **Field path** | Not `body.*` (already excluded by Phase D eligibility gates) |
| **Human reviewer available** | Review workflow requires a human reviewer ID or explicit AI-assisted review acknowledgment |

### 2.1 Records NOT Eligible for Review

| Condition | Why Blocked | Action |
|---|---|---|
| `status="rejected"` | Already reviewed and discarded | Keep for audit; do not re-enter review queue unless explicitly reopened by reviewer |
| `status="promoted"` | Already reviewed and promoted | Route to `approved_global_rule` maintenance, not review |
| `status="superseded"` | Obsolete due to later rule or candidate | Keep for audit; may be referenced by successor record |
| `correction_type="one_time_wording"` or `"local_command_preference"` | Never logged to Phase D by design | Route to session store or Phase C profile promotion if applicable |
| `status="deferred"` with no re-review trigger | Parked until future decision | Re-queue only when reviewer or expiration trigger fires |
| Missing `sanitized_value` or empty `field_path` | Corrupt or incomplete record | Log warning; require manual data recovery |
| Duplicate of an existing `pending`/`under_review` record | Fingerprint collision | Merge or deduplicate before review |

---

## 3. Review Statuses and Transitions

Phase E uses the same six statuses defined in Phase D, but adds transition rules and gating:

| Status | Meaning | Allowed Transitions | Who Can Set |
|---|---|---|---|
| `pending` | Newly logged, awaiting review | `under_review`, `rejected` | System or reviewer |
| `under_review` | A reviewer has claimed/opened this candidate | `deferred`, `rejected`, `promoted` | Reviewer only |
| `deferred` | Valid candidate but not actionable now; may be revisited | `under_review`, `rejected`, `superseded` | Reviewer only |
| `rejected` | Not a valid global rule or validator gap; discarded | `under_review` (reopen) | Reviewer only |
| `promoted` | Candidate approved as an `approved_global_rule` record | `superseded` | Reviewer only |
| `superseded` | Later candidate or rule update made this obsolete | None (terminal) | System or reviewer |

### 3.1 Transition Rules

- `pending` → `under_review`: reviewer claims the candidate. Record `reviewed_by` and `reviewed_at`.
- `pending` → `rejected`: quick-reject without full review if the candidate is obviously malformed, misclassified, or a duplicate.
- `under_review` → `deferred`: reviewer needs more evidence (e.g., pending SECNAV manual confirmation).
- `under_review` → `rejected`: reviewer determines the candidate is not a real global rule or validator gap.
- `under_review` → `promoted`: reviewer approves and creates an `approved_global_rule` record.
- `deferred` → `under_review`: re-triggered by reviewer action or expiration (e.g., 30 days deferred).
- `deferred` → `rejected`: deferred candidate never received resolution; reviewer discards.
- `deferred` → `superseded`: a later promoted rule covers the same case.
- `promoted` → `superseded`: a newer rule or validator update replaces the approved rule.
- `rejected` → `under_review`: reviewer reopens (e.g., new evidence discovered).

No automatic transitions from `under_review` to `promoted`. Every promotion requires explicit reviewer confirmation.

---

## 4. Human Review Workflow

### 4.1 Step 1 — Claim/Queue Listing

The system presents a filtered list of `pending` candidates to the reviewer:

```
PENDING GLOBAL RULE CANDIDATES (3)
---
1. cand_20260601_abc123 | subj | possible_secnav_manual_rule | Marine Corps
   "Subject line ends with period. SECNAV manual says no terminal punctuation."
2. cand_20260601_def456 | via | bug_validator_gap | Navy
   "Validator did not flag missing intermediate Via addressee for this document type."
3. cand_20260601_ghi789 | date | possible_secnav_manual_rule | Joint
   "Date format should be day Month year; validator accepted civilian format."
```

Filtering options:
- By `correction_type`
- By `doc_type`
- By `component`
- By `classification_confidence` (high first, or low first for triage)
- By date range (e.g., last 30 days)

### 4.2 Step 2 — Review Detail View

When a reviewer selects a candidate, the system shows a detail view with **all sanitized data only**:

```
CANDIDATE: cand_20260601_abc123
Status: pending
Type: possible_secnav_manual_rule
Field: subj
Classification confidence: high
Classification method: field_path_keyword

Original value (sanitized): POLICY UPDATE.
Corrected value (sanitized): POLICY UPDATE
Document type: standard_letter
Component: marine_corps
User reason: "SECNAV manual says subject should not end with a period"
Session ID: sess_20260601_001
Source correction: corr_abc123

---
REVIEWER DECISION
[ ] Promote to approved global rule candidate
[ ] Reject — not a global rule
[ ] Defer — need more evidence
[ ] Superseded by existing rule (specify rule ID)

SECNAV M-5216.5 Source Verification (required for promotion):
Chapter: ___  Paragraph: ___  Figure: ___  URL/page: ___
Direct quote from manual (optional): _________________________

Rationale (required): ________________________________________

Reviewer ID: ____________  Date: ____________
```

### 4.3 Step 3 — Evidence Verification Gate

Before any candidate can transition to `promoted`, the reviewer must provide **at least one** of the following:

1. **Direct SECNAV M-5216.5 citation**: chapter, paragraph, and/or figure number.
2. **Direct quote**: exact text from the manual supporting the rule.
3. **Figure reference**: specific figure in the manual showing the correct format.
4. **Cross-reference to existing rule**: citation of an existing `rules_v6/CCI/` rule that this candidate extends or clarifies.

If the reviewer selects `"bug_validator_gap"`, the evidence requirement is:
1. **Validator name**: which validator failed (e.g., `cci_subject`, `cci_routing`).
2. **Expected behavior**: what the validator should have caught.
3. **Actual behavior**: what the validator did instead (false positive, false negative, missing check).
4. **Reproduction steps**: minimal payload that triggers the gap.

If evidence is insufficient, the system rejects the promotion action and returns the candidate to `under_review` with a note: "Insufficient evidence for promotion. Required: SECNAV manual citation or validator reproduction steps."

### 4.4 Step 4 — Confirmation Dialog

Before finalizing any status change:

```
CONFIRM REVIEW DECISION
Candidate: cand_20260601_abc123
New status: promoted
Reviewer: reviewer_id
Evidence: Chapter 7, Paragraph 3 — "The subject line shall not end with a period."
Rationale: Confirmed against manual text and example in Figure 7-1.

This will create an approved_global_rule record ONLY.
It will NOT modify any validator, rule catalog, or renderer.
Actual tool changes require separate approval after Phase E.

Confirm? (yes/no)
```

---

## 5. Required Evidence Before Promotion

| Evidence Type | Required For | Format |
|---|---|---|
| SECNAV M-5216.5 chapter/paragraph | `possible_secnav_manual_rule` | Free text, validated as non-empty |
| SECNAV M-5216.5 figure reference | `possible_secnav_manual_rule` (strongly recommended) | Figure number, e.g., "Figure 7-1" |
| Direct manual quote | `possible_secnav_manual_rule` (optional but encouraged) | Free text, truncated to 2000 chars |
| Validator name | `bug_validator_gap` | Must match an existing `src/cci_*.py` module name or "unknown" |
| Expected vs actual validator behavior | `bug_validator_gap` | Free text, truncated to 2000 chars |
| Reproduction payload | `bug_validator_gap` (strongly recommended) | Minimal JSON payload or field_path + value pair |
| Reviewer ID | All promotions | Free text or system user ID |
| Review date | All promotions | ISO8601 timestamp (auto-populated) |
| Rationale | All promotions | Free text, truncated to 2000 chars, non-empty |

If any required field is missing or empty, the promotion action is blocked with a clear error message listing the missing evidence.

---

## 6. SECNAV M-5216.5 Source Verification

### 6.1 Source Verification Workflow

For every `possible_secnav_manual_rule` candidate, Phase E requires the reviewer to ground the proposed rule in the actual manual text:

1. **Citation field**: reviewer enters chapter, paragraph, and/or figure.
2. **Quote field**: reviewer optionally pastes the exact manual text.
3. **Validation**: the system performs a lightweight sanity check (non-blocking):
   - Citation format matches expected patterns (e.g., "Chapter 7", "para 3", "Figure 7-1").
   - If the project has a future digitized manual lookup utility, verify the citation exists.
   - If no lookup utility exists, the citation is stored as-is for human audit.
4. **Confidence flag**:
   - If citation + quote provided: `source_verification="strong"`
   - If citation only: `source_verification="moderate"`
   - If neither citation nor quote: `source_verification="weak"` — promotion blocked unless reviewer provides written rationale explaining why the manual cannot be cited (e.g., "new interpretation of existing text").

### 6.2 No AI-Only Source Verification

An AI assistant may suggest a citation or quote, but the final verification must be reviewed and confirmed by a human. The AI suggestion is stored in `review_metadata.ai_suggested_citation` but does not satisfy the evidence requirement until the reviewer explicitly approves it.

---

## 7. Distinguishing Candidate Types During Review

### 7.1 Real SECNAV Manual Rule

Indicators:
- User reason mentions specific chapter, paragraph, figure, or manual section.
- Correction aligns with known formatting conventions (e.g., subject punctuation, date format).
- Field path is structural (`subj`, `date`, `ref`, `encl`, `via`, `classification`).
- No validator conflict (the system failed to enforce an existing rule).

Action: If verified, promote to `approved_global_rule` with `rule_category="manual_rule"`.

### 7.2 Validator Bug / Gap

Indicators:
- User reason mentions validator failure, false positive, false negative, or missing check.
- `validator_conflict=True` on the originating correction.
- Correction fixes something the validator should have caught or incorrectly flagged.
- Field path may be any field covered by an existing validator.

Action: If verified, promote to `approved_global_rule` with `rule_category="validator_gap"`. The actual validator fix is a separate task requiring its own regression tests.

### 7.3 Misclassified Local Command Preference

Indicators:
- The "corrected" value contains command-specific identifiers (heavy `[COMMAND_NAME]` redaction in sanitized form).
- User reason mentions "our command", "our SOP", "local policy".
- Field path is `from`, `signature`, `originator_code`, `unit_identity`, `copy_to`.

Action: Reject from global promotion. Offer one-click redirect to Phase C local command profile promotion if the originating correction is still available in session store.

### 7.4 One-Time Wording Issue

Indicators:
- `body.*` field path (already excluded by Phase D, but may appear if Phase D gates are bypassed or a future exception is used).
- User reason mentions "this letter only", "specific example", "reword for this draft".

Action: Reject. No promotion path. Keep in session store if `current_session` scoped.

### 7.5 Insufficient Evidence

Indicators:
- No manual citation, no validator name, no reproduction steps.
- User reason is vague ("looks wrong", "should be different").
- Sanitization removed all structural information; record is mostly `[REDACTED_VALUE]` tokens.

Action: Defer or reject. If deferred, the reviewer may set a re-review date (e.g., "revisit in 30 days"). If rejected, record the reason as "insufficient evidence."

---

## 8. What Promotion Means in Phase E

Phase E promotion is **record-creation only**. It means creating a durable `approved_global_rule` record with full provenance. It explicitly does **not** mean:

- Modifying `src/cci_*.py` validator code.
- Adding to `rules_v6/CCI/` rule catalog.
- Changing AI prompt contracts.
- Enforcing the rule automatically on future drafts.
- Modifying renderer or layout behavior.

### 8.1 Approved Global Rule Record Schema

When a candidate is promoted, a new record is written to `corrections/approved_rule_promotions.json` (or equivalent):

| Field | Type | Required | Description |
|---|---|---|---|
| `rule_id` | string | Yes | Unique identifier, e.g., `agr_20260601_subj_punctuation_001` |
| `promoted_from_candidate_id` | string | Yes | Reference to originating `candidate_id` |
| `promoted_at` | ISO8601 | Yes | Timestamp of promotion |
| `promoted_by` | string | Yes | Reviewer ID |
| `rule_category` | enum | Yes | `"manual_rule"` or `"validator_gap"` |
| `field_path` | string | Yes | Canonical field path |
| `doc_type_filter` | list | No | Document types where rule applies |
| `component_filter` | list | No | Components where rule applies |
| `sanitized_value` | string | Yes | Abstracted corrected value (rule pattern) |
| `original_value_sanitized` | string | Yes | Abstracted original value (for comparison) |
| `segnav_citation` | object | Yes | `{chapter, paragraph, figure, quote}` |
| `rationale` | string | Yes | Reviewer rationale |
| `evidence_quality` | enum | Yes | `"strong"`, `"moderate"`, `"weak"` |
| `implementation_status` | enum | Yes | `"pending_implementation"` (Phase E sets this only) |
| `linked_validator_update` | string | No | Future validator ticket or PR reference |
| `linked_rule_file` | string | No | Future `rules_v6/CCI/` file path |
| `review_metadata` | object | Yes | Full Phase E review audit trail |

### 8.2 Implementation Status

Phase E sets `implementation_status="pending_implementation"` on every promoted rule. The transition to `"implemented"` requires:
1. A separate approval step.
2. Actual validator/rule catalog changes.
3. New regression tests covering the rule.
4. Full regression suite pass.

---

## 9. Recording Reviewer Decision and Rationale

All review decisions are permanently recorded in `review_metadata`:

```json
{
  "reviewed_at": "2026-06-15T10:00:00Z",
  "reviewed_by": "reviewer_id_or_name",
  "review_action": "promoted",
  "review_notes": "Subject punctuation rule confirmed against M-5216.5 Chapter 7, para 3.",
  "segnav_citation": {
    "chapter": "7",
    "paragraph": "3",
    "figure": "7-1",
    "quote": "The subject line shall not end with a period."
  },
  "evidence_quality": "strong",
  "rationale": "Verified against manual text and example figure. Applicable to all standard letters across components.",
  "previous_status": "under_review",
  "new_status": "promoted",
  "ai_assisted": false,
  "ai_suggested_citation": null
}
```

For rejected candidates:

```json
{
  "reviewed_at": "2026-06-15T11:00:00Z",
  "reviewed_by": "reviewer_id_or_name",
  "review_action": "rejected",
  "review_notes": "Correction is command-specific; originator code N7 is local to USS NEVERSAIL.",
  "rejection_reason": "local_command_preference_misclassified",
  "redirected_to_phase_c": true,
  "phase_c_profile_name": "uss_neversail_profile",
  "previous_status": "under_review",
  "new_status": "rejected"
}
```

All review metadata is append-only within the candidate record. Once written, it is never deleted or mutated. If a reviewer reopens a rejected candidate, a new review metadata entry is appended with the new decision.

---

## 10. Handling Duplicates and Superseded Candidates

### 10.1 Duplicate Detection During Review

When a reviewer claims a candidate, the system should display any existing candidates with the same fingerprint:

```
WARNING: Similar candidates exist
- cand_20260601_abc123 | subj | possible_secnav_manual_rule | status: promoted
- cand_20260601_xyz999 | subj | possible_secnav_manual_rule | status: rejected

Are you reviewing a new variant, or should this be linked to an existing candidate?
```

Actions:
- **New variant**: allow independent review; note relationship in `review_metadata.related_candidates`.
- **Duplicate of pending**: merge notes and proceed with one candidate; mark the other `superseded`.
- **Duplicate of promoted**: reject or supersede; direct reviewer to the approved rule record.

### 10.2 Superseded Rules

A candidate becomes `superseded` when:
- A later candidate covering the same `(field_path, doc_type, component)` is promoted.
- An existing `approved_global_rule` is implemented that makes the candidate obsolete.
- The SECNAV manual is updated, changing the rule.

The superseded record remains in the log for audit but is excluded from review queues.

### 10.3 Superseded Record Schema

```json
{
  "review_metadata": {
    "reviewed_at": "2026-07-01T09:00:00Z",
    "reviewed_by": "system_or_reviewer_id",
    "review_action": "superseded",
    "review_notes": "Superseded by approved rule agr_20260701_subj_punctuation_002.",
    "superseded_by_rule_id": "agr_20260701_subj_punctuation_002",
    "previous_status": "pending"
  }
}
```

---

## 11. Converting Rejected Global Candidates to Phase C Local Profile

### 11.1 Rejection with Redirect

When a reviewer rejects a candidate as "actually local command preference," Phase E should offer a structured redirect:

```
REJECTED: cand_20260601_def456
Reason: Local command preference, not global rule.

Redirect to Phase C local command profile?
[ ] Yes — create profile promotion proposal
[ ] No — discard completely

If yes, select target profile:
[ ] Existing profile: ____________
[ ] New profile: ____________
```

### 11.2 Redirect Mechanism

1. Phase E calls `correction_promote.propose_promotion()` with the originating session correction record.
2. The correction_type is overridden to `"local_command_preference"` for the promotion workflow.
3. Phase C's existing two-step approval workflow handles profile selection, backup, and atomic write.
4. The Phase E rejection record notes the redirect target in `review_metadata.redirected_to_phase_c`.

### 11.3 Redirect Safety

- Redirect is only possible if the originating correction still exists in the session JSONL store.
- If the session store has been cleaned or the correction is missing, the redirect fails gracefully with a message: "Original correction no longer available in session store. Manual profile entry required."
- No automatic profile write occurs. Phase C approval gates still apply.

---

## 12. Preventing Raw PII in Review Outputs

### 12.1 Display Sanitization

All review interfaces must display **only** sanitized values from `correction_pending_log.py`:

- `sanitized_value` and `original_value_sanitized` are the only values shown.
- Never show raw `corrected_value` or `original_value` from session store.
- Never show `session_id` beyond the internal reference (it may contain user-identifiable strings).
- Never show full file paths that include usernames or machine names.

### 12.2 Export Sanitization

If Phase E supports exporting candidate lists for external review (e.g., CSV, JSON), the export must:
- Use sanitized fields only.
- Strip `session_id`, `source_correction_id`, and any timestamp that could correlate to user activity.
- Replace reviewer IDs with anonymized handles if exported outside the local system.

### 12.3 Review Metadata Sanitization

Reviewer-entered free text (`rationale`, `review_notes`, `segnav_citation.quote`) must be scanned for PII leakage:
- Run `_sanitize_value()` on reviewer text before storage.
- If `[EMAIL]`, `[PHONE]`, or `[SSN]` tokens are detected in reviewer input, warn the reviewer and require confirmation before saving.

---

## 13. Required Regression Coverage

New runner: `tools/run_correction_review_promotion_regression.py`

| # | Check |
|---|---|
| 1 | List `pending` candidates returns only eligible records |
| 2 | List filters by `correction_type` |
| 3 | List filters by `component` |
| 4 | Claim candidate → status changes to `under_review` |
| 5 | Reject candidate → status changes to `rejected`, review metadata recorded |
| 6 | Promote candidate → status changes to `promoted`, `approved_global_rule` record created |
| 7 | Promotion blocked if `segnav_citation` missing for `possible_secnav_manual_rule` |
| 8 | Promotion blocked if `validator_name` missing for `bug_validator_gap` |
| 9 | Promotion blocked if `rationale` is empty |
| 10 | Deferred candidate → status `deferred`, can be re-opened |
| 11 | Superseded candidate → terminal status, excluded from active queue |
| 12 | Duplicate fingerprint detected during review → warning shown |
| 13 | Rejected candidate with redirect → Phase C proposal generated |
| 14 | Rejected candidate without redirect → no Phase C proposal |
| 15 | Review metadata append-only; previous entries preserved |
| 16 | `approved_global_rule` record contains all required fields |
| 17 | `approved_global_rule` record `implementation_status` defaults to `pending_implementation` |
| 18 | AI-suggested citation does not satisfy evidence requirement without human confirmation |
| 19 | Reviewer-entered PII in notes is sanitized before storage |
| 20 | Export of candidate list uses sanitized fields only |
| 21 | No real command data appears in review outputs (grep for patterns) |
| 22 | Existing Phase D regression still passes after Phase E module added |
| 23 | Existing Phase C regression still passes after Phase E module added |
| 24 | Existing Phase B regression still passes after Phase E module added |
| 25 | Existing Phase A regression still passes after Phase E module added |

---

## 14. Files to Add or Change in Future Implementation

### 14.1 New Files

- `src/correction_review.py` — review workflow engine
  - `list_candidates_for_review(log_file, filters)`
  - `claim_candidate(log_file, candidate_id, reviewer_id)`
  - `reject_candidate(log_file, candidate_id, review_metadata)`
  - `defer_candidate(log_file, candidate_id, review_metadata)`
  - `promote_candidate(log_file, candidate_id, review_metadata, approved_rule_record)`
  - `supersede_candidate(log_file, candidate_id, review_metadata)`
  - `reopen_candidate(log_file, candidate_id, review_metadata)`
  - `_validate_evidence(review_metadata, correction_type)`
  - `_create_approved_rule_record(candidate, review_metadata)`
- `tools/run_correction_review_promotion_regression.py` — 25+ check runner
- `docs/checkpoints/phase_e_review_promotion_utility_checkpoint.md` — post-impl checkpoint
- `corrections/approved_rule_promotions.json` (new storage file, gitignored)

### 14.2 Modified Files

- `src/correction_pending_log.py` — extend `update_candidate_status()` to support full review metadata validation; ensure `review_metadata` can store nested objects.
- `src/intake_orchestrator.py` — add optional `review_pending_candidates()` hook for CLI/gateway integration (opt-in, read-only by default).
- `corrections/README.md` — document `approved_rule_promotions.json` as gitignored and local-only.
- `.gitignore` — ensure `corrections/approved_rule_promotions.json` is covered.

### 14.3 Unchanged

- Renderer, layout profiles, `src/pdf_v6_render.py`
- `src/correction_classify.py`
- `src/correction_capture.py`
- `src/correction_promote.py` (Phase C logic unchanged)
- `src/correction_store.py` (Phase A logic unchanged)
- `src/local_profile.py`
- `profiles/example_local_profile.json`
- All existing validator modules (`src/cci_*.py`)
- `src/validator_runner.py`

---

## 15. What Phase E Must NOT Do

- **No automatic global rule enforcement** — `approved_global_rule` records are documentation only until separately implemented.
- **No renderer/layout changes** — Do not modify `src/pdf_v6_render.py` or layout profiles.
- **No validator/rule catalog changes unless separately approved** — Do not edit `src/cci_*.py`, `rules_v6/CCI/`, or prompt contracts as part of Phase E.
- **No AI-only promotion decision** — AI may suggest, but human reviewer must confirm every promotion.
- **No real command/user data committed** — Review outputs, approved records, and exports must all use sanitized values.
- **No UI implementation unless separately approved** — Phase E is a Python module with function-level API; any CLI/chat/web UI is a separate phase.
- **No automatic cleanup of pending log** — Do not prune `pending_corrections.jsonl` as part of review workflow.
- **No cross-session candidate review** — Reviewers see candidates from the local log only; no multi-user sharing.
- **No email/notification system** — Do not trigger emails, Slack messages, or other external notifications.
- **No Phase C auto-write on redirect** — Redirect to Phase C still requires Phase C two-step approval.
- **No `--auto-approve` flag** — Every promotion requires explicit reviewer confirmation.

---

## 16. Recommended Phase E Implementation Sequence (If Approved)

1. Update `.gitignore` to include `corrections/approved_rule_promotions.json`.
2. Update `corrections/README.md` to document approved rule promotions storage.
3. Define `_validate_evidence()` helper in `src/correction_review.py`.
4. Create `src/correction_review.py` with claim, reject, defer, promote, supersede, reopen functions.
5. Implement `approved_global_rule` record schema and `_create_approved_rule_record()`.
6. Hook into `src/correction_pending_log.py` `update_candidate_status()` for validation extension.
7. Add optional `review_pending_candidates()` to `src/intake_orchestrator.py` (read-only listing by default).
8. Write regression runner (25+ checks) with temp-only fixtures.
9. Run full regression suite (all 20 existing + new runner).
10. Commit: `CCI: Add review/promotion utility (Phase E)`.
11. Create checkpoint and update status docs.

---

## 17. Open Questions Needing Approval

1. **Reviewer identity system** — Is `reviewed_by` a free-text name, a local user ID, or an email? How is identity validated and stored?
2. **AI-assisted review scope** — Can an AI pre-fill citations, compare manual text, or flag likely misclassifications? If so, what confidence threshold requires human override?
3. **Approved rule record format** — Should `approved_rule_promotions.json` be a single JSON object or JSONL? Should it support append-only or in-place updates?
4. **Multi-reviewer collaboration** — Can multiple reviewers claim and comment on the same candidate before a final decision, or is it single-reviewer-only?
5. **Re-review expiration** — Should `deferred` candidates auto-return to `pending` after a set period (e.g., 30 days), or remain deferred indefinitely?
6. **Integration with future rule catalog** — When a rule is later implemented, should the system automatically link the `approved_global_rule` record to the actual `rules_v6/CCI/` file, or is that manual?
7. **Statistics and reporting** — Should Phase E expose metrics (e.g., pending count by type, average time to review, promotion rate) for dashboarding?
8. **Backwards compatibility** — If Phase D `review_metadata` schema changes, how are existing records migrated?

---

**Plan created:** 2026-06-01  
**Source functional baseline:** `2e31892` — CCI: Add pending global rule candidate logging (Phase D)  
**Next step:** Await review and approval before implementing Phase E.
