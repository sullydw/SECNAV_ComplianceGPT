# Phase E Review/Promotion Utility Checkpoint

**Status:** Completed
**Implementation commit:** `058de87` — `CCI: Add review promotion utility (Phase E)`
**Date:** 2026-06-02
**Verified by:** Local regression suite (all 21 suites PASS)
**Next recommended phase:** Phase F UI/command integration planning (planning-only until approved)
**Previous checkpoint:** `docs/checkpoints/phase_d_pending_global_rule_candidate_log_checkpoint.md`

---

## What Was Implemented

### 1. New source file: `src/correction_review.py`

Public API (all functions documented and regression-covered):

| Function | Purpose |
|----------|---------|
| `list_candidates_for_review(log_path, correction_type, component)` | Returns reviewable candidates filtered by `pending`/`under_review`, `possible_secnav_manual_rule`/`bug_validator_gap`, not superseded/rejected/promoted. |
| `claim_candidate(candidate_id, reviewer_id, log_path)` | Sets a candidate to `under_review` and records `reviewed_by`. Single-claimer, local-only. |
| `record_review_decision(candidate_id, decision, reviewer_id, rationale, evidence, log_path, promotions_path)` | Core review entry point. Validates evidence, appends review metadata, enforces status transitions, creates approved-rule records on `promote`. |
| `propose_phase_c_redirect(candidate_id, reviewer_id, log_path)` | Returns a Phase C redirect proposal; if session/original data missing, returns a synthetic fallback. |
| `load_approved_promotions(promotions_path)` | Loads the approved promotions JSON list. |
| `get_approved_promotion(record_id, promotions_path)` | Returns a single approved promotion record or `None`. |
| `export_approved_promotions(promotions_path, include_sensitive=False)` | Returns full or anonymized (session IDs stripped, reviewer IDs anonymized) list. |

Additional helpers (internal but auditable):

| Function | Purpose |
|----------|---------|
| `_sanitize_review_text(text)` | Strips names, emails, phones, EDIPI, SSN, DoD ID, UIC, hull/tail, building/room numbers. |
| `_validate_evidence(candidate, ctype)` | Enforces `secnav_citation` for `manual_rule` and `validator_evidence` for `validator_gap`. |
| `_create_approved_rule_record(candidate, reviewer_id, rationale, evidence)` | Builds the approved-rule record with `implementation_status="pending_implementation"`. |

### 2. New regression runner: `tools/run_correction_review_regression.py`

30 checks covering:

1. List pending returns eligible records.
2. List filters by correction type.
3. List filters by component.
4. Claim changes status to `under_review`.
5. Reject records metadata.
6. Promote creates approved record.
7. Promotion blocked missing `secnav_citation`.
8. Promotion blocked missing `validator_evidence`.
9. Promotion blocked empty rationale.
10. Defer then reopen works.
11. Superseded excluded from queue.
12. Duplicate fingerprint handling.
13. Rejected redirect recorded.
14. Rejected without redirect.
15. Review metadata append-only.
16. Approved record has required fields.
17. `implementation_status` is `pending_implementation`.
18. AI-suggested citation not enough.
19. Reviewer PII sanitized.
20. No real command data in outputs.
21. Phase D compatibility.
22. Phase C compatibility.
23. Phase B compatibility.
24. Phase A compatibility.
25. Validator gap promote creates record.
26. Invalid status transitions blocked.
27. Superseded explicit only.
28. Reviewer text truncation.
29. List excludes promoted and rejected.
30. Phase C redirect synthetic fallback.

All 30 checks PASS locally.

### 3. Updated `corrections/README.md`

Documented that `corrections/approved_rule_promotions.json` is gitignored and stores approved global rule records created by the review/promotion utility.

---

## Scope Boundaries

- ✅ Human reviewer required for all decisions.
- ✅ Promotion creates records only (`implementation_status="pending_implementation"`).
- ✅ No validator modifications.
- ✅ No rule catalog modifications.
- ✅ No renderer/layout modifications.
- ✅ No automatic global rule enforcement.
- ✅ PII sanitizer covers names, emails, phone numbers, EDIPI, SSN, DoD ID, UIC, hull/tail, building/room numbers.
- ✅ Review metadata is append-only (reopening appends new entries).
- ✅ `corrections/approved_rule_promotions.json` is gitignored and local-only.
- ✅ Rejected candidates can be redirected to Phase C (with existing Phase C approval gates).
- ✅ Superseded is explicit reviewer action only.
- ✅ Claim is local-only single reviewer (no multi-user locking; future multi-user would need separate planning).
- ✅ Reused existing `correction_pending_log.py` helpers; no changes needed to Phase D source.
- ✅ Spelling: authoritative `secnav_citation` used everywhere (no `segnav_citation` typo).

---

## Acceptance Criteria

| # | Criterion | Met? |
|---|-----------|------|
| 1 | Phase E implementation is in a single commit `058de87`. | ✅ |
| 2 | Includes new `src/correction_review.py` with public API. | ✅ |
| 3 | Includes new `tools/run_correction_review_regression.py` with ≥25 checks, all passing. | ✅ (30 checks) |
| 4 | Evidence validation enforces `secnav_citation` for `manual_rule` and `validator_evidence` for `validator_gap`. | ✅ |
| 5 | Promotion only creates `implementation_status="pending_implementation"` records. | ✅ |
| 6 | No validator/rule catalog modifications. | ✅ |
| 7 | No renderer/layout modifications. | ✅ |
| 8 | Review metadata is append-only. | ✅ |
| 9 | PII sanitizer prevents real command/user data leakage. | ✅ |
| 10 | `corrections/approved_rule_promotions.json` is gitignored. | ✅ |
| 11 | All 21 regression suites pass locally at `058de87`. | ✅ |

---

## What Was NOT Implemented (Intentionally Deferred)

- UI or web interface for the review utility (remains CLI-only / programmatic).
- Automatic candidate review or auto-promotion (still requires explicit human reviewer).
- Multi-user concurrent claim/locking (local single-reviewer only).
- Global rule enforcement (Phase E creates records only; enforcement needs future validator/catalog work).
- External system integration (e.g., Jira, Slack notifications).
- Automatic cleanup/aging of review metadata or approved records.
- Cross-session sharing of approved records (local-only for now).

---

## Safety Notes

- Real command profiles, session JSONL stores, pending candidate logs, and approved promotion logs are **not committed** to the repository.
- The example profile `profiles/example_local_profile.json` remains fake/template data only.
- All regression runners use synthetic/temp fixtures and do not write to real `corrections/` files.
- Reviewer-entered text is sanitized before storage.
- Anonymized export strips session IDs and anonymizes reviewer IDs.

---

## Next Phase Recommendation

### Phase F — UI/Command Integration Planning

The review utility is now implemented but is only accessible programmatically or via CLI. The next recommended phase is **planning only** until approved:

- Natural-language user commands for issuing corrections.
- CLI or web interface integration for the review utility.
- Whether offline/autonomous review features are needed (default: none).
- Regression requirements before any UI implementation.

Do not implement Phase F without an approved plan.

---

## Regression Baseline

Full regression suite verified PASS at `058de87`:

```bash
python tools/run_correction_review_regression.py         # PASS (30/30)
python tools/run_correction_pending_regression.py        # PASS (33/33)
python tools/run_correction_profile_promotion_regression.py  # PASS (33/33)
python tools/run_correction_classify_regression.py       # PASS
python tools/run_intake_regression.py                    # PASS
python tools/run_correction_regression.py                # PASS
python tools/run_correction_session_regression.py        # PASS
python tools/run_profile_regression.py                   # PASS
python tools/run_cci_audit_regression.py                 # PASS
python tools/run_context_schema_regression.py            # PASS
python tools/run_cci_subject_regression.py               # PASS
python tools/run_cci_ref_encl_regression.py             # PASS
python tools/run_cci_acronym_regression.py               # PASS
python tools/run_cci_date_time_regression.py            # PASS
python tools/run_cci_personnel_regression.py            # PASS
python tools/run_cci_poc_regression.py                   # PASS
python tools/run_cci_routing_regression.py               # PASS
python tools/run_c7_phase1_regression.py             # PASS
python tools/run_c8_regression.py                        # PASS
python tools/run_c9_regression.py                        # PASS
python tools/run_c10_regression.py                     # PASS
```

---

## Files Changed in Phase E Implementation

- `src/correction_review.py` — new (700 lines)
- `tools/run_correction_review_regression.py` — new (633 lines)
- `corrections/README.md` — updated (approved promotions description)

No changes to renderer, validators, rule catalogs, or Phase D source (`correction_pending_log.py`).

---

*This checkpoint was recorded after verifying local regressions on 2026-06-02.*
*For questions or next steps, read `docs/PROJECT_STATUS.md` and the latest phase checkpoint.*
