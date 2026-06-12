# Phase L.5 Conversational Builder Validation Summary Integration Checkpoint

## Date
2026-06-11

## Baseline
Latest verified baseline: `71b8952`
Current HEAD after L.4: `71b8952`

## Files Changed
- `src/conversational_builder.py` — updated with validation summary and improved finalize behavior
- `tools/run_phase_l4_conversational_builder_regression.py` — updated for L.5 builder_version assertion
- `tools/run_phase_l5_conversational_builder_validation_summary_regression.py` — new regression runner
- `docs/PROJECT_STATUS.md` — updated (this commit)
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — updated (this commit)
- `docs/checkpoints/phase_l5_conversational_builder_validation_summary_checkpoint.md` — this file

## Validation Summary Behavior

### `validation_summary()` method
Returns a structured dict with:
- `total_findings`, `errors`, `warnings`, `advisories` — counts
- `known_pilot_findings` — count of active-pilot-related findings
- `pending_decisions` — count of warning-level findings without accept/ignore decision
- `finalize_allowed` — boolean; True only if no errors and no pending warning decisions
- `block_reason` — list of human-readable blocking reasons (empty if allowed)
- `findings` — full list from `warning_summary()`

### Blocking policy
- **Errors block finalization** unconditionally
- **Warnings block finalization** if pending (no accept/ignore decision recorded)
- **Advisories do NOT block finalization** (they are informational only)
- `accept_warnings=True` parameter on `finalize()` overrides pending-warning blocking without mutating stored decisions (sets `accepted_via_flag` transiently)

### Warning formatter improvements
- `CCI-ROUTE-010`: "A routing office code appears as numbers only (for example, '123'). SECNAV M-5216.5 recommends writing it as 'Code 123'."
- `CCI-ROUTE-011`: "This standard letter has no 'From:' line. Add one, or mark it as a window-envelope letter if it will use a window envelope."
- `CCI-CH7-SUBJ-002`: "The subject line ends with punctuation (such as a period or question mark). SECNAV M-5216.5 Chapter 7 recommends no terminal punctuation in the subject line."
- Unknown findings: advisory fallback with "Please verify the content follows SECNAV conventions before finalizing."

### Error-list handling
Known pilot rules that appear in validator `errors` lists (due to effective severity mapping) are still presented with their mapped warning severity and plain-English message, not raw validator output. Unknown errors remain as severity `error` with "Fix before finalizing" action.

## Finalize Behavior
- `finalize()` returns structured dict including:
  - `validation_summary` (full structured summary)
  - `warning_summary` (findings list only)
  - `finalize_allowed` (boolean)
  - `block_reason` (list of reasons)
  - `payload`, `audit`, `draft_final_status`, `builder_version`
- Signature presence still gates `draft_final_status` to "draft" if missing

## Test Coverage

### L.4 regression runner (updated)
- 10 tests, **41 passed, 0 failed**
- Added assertions for `validation_summary`, `finalize_allowed` in finalize output
- `builder_version` updated to L.5

### L.5 regression runner (new)
10 tests, **36 passed, 0 failed**:
1. no_findings_summary — clean payload: 0 errors, 0 warnings, finalize allowed
2. known_route010_warning_summary — ROUTE-010 appears, severity warning, plain-English message
3. known_route011_warning_summary — ROUTE-011 appears, severity warning, plain-English message
4. known_subj002_warning_summary — SUBJ-002 appears, severity warning, mentions punctuation
5. unknown_advisory_fallback — unknown code mapped to advisory with plain-English message
6. pending_decision_state — unaccepted warning blocks finalize, pending count > 0
7. accepted_warning_state — recorded accept decision allows finalize, pending = 0
8. finalize_allowed_with_accepted_warnings — decisions present, finalize allowed without flag
9. finalize_allowed_with_accept_warnings_flag — `accept_warnings=True` overrides pending
10. finalize_blocked_with_synthetic_error — injected synthetic error blocks finalize

## Full Gate Result
37-suite regression executed.

### Notable results
| Runner | Result |
|--------|--------|
| run_phase_l4_conversational_builder_regression.py | **PASS** (41/41) |
| run_phase_l5_conversational_builder_validation_summary_regression.py | **PASS** (36/36) |
| run_intake_regression.py | **PASS** |
| run_phase_k3_subject_terminal_punctuation_regression.py | **PASS** (11/11) |
| run_phase_h16_route011_burnin_regression.py | **FAIL** (95/96 — check 94: H.13 sub-runner cascade) |
| run_phase_h24_route011_sanitized_fixture_regression.py | **FAIL** (34/36 — H.13/H.16 sub-runner cascades) |
| run_phase_h13_config_regression.py | **FAIL** (26/27 — check 21: H.6 sub-runner cascade) |
| run_phase_h4_routing_office_code_validator_regression.py | **FAIL** (17/18 — check 17: unexpected changed files from L.4/L.5 work) |
| run_phase_h6_routing_office_code_evidence_regression.py | **FAIL** (14/15 — check 11: H.4 sub-runner cascade) |

### Cascade failure analysis
The H.4, H.6, H.13, H.16, and H.24 failures are **cross-check cascades caused by uncommitted L.4/L.5 files in the working tree**, not behavioral regressions:
- H.4 check 17 inspects `git status` and flags `src/conversational_builder.py` and `tools/run_phase_l4_conversational_builder_regression.py` as unexpected changed files (not in its hardcoded allowlist).
- H.6 check 11 runs H.4 as a sub-runner and fails because H.4 fails.
- H.13 check 21 runs H.6 as a sub-runner and fails because H.6 fails.
- H.16 check 94 runs H.13 as a sub-runner and fails because H.13 fails.
- H.24 sub-runner step runs H.13 and H.16, propagating the same cascades.

**These cascades will resolve after commit because `git status` becomes clean.** No validator, config, or behavioral changes caused the failures.

All other non-PDF suites pass. C7/C10 PDF render/layout remain pre-existing environment failures (reportlab/fitz missing).

## No Renderer/Layout Changes
Confirmed. `pdf_v6_render.py` untouched. `audit_pdf_layout.py` untouched.

## No CCI Config/Severity Changes
Confirmed. `cci_severity_config.json` untouched. `cci_config_defaults.json` untouched.

## No Validator/Catalog Changes
Confirmed. No validator source files modified. No routing/subject/ref_encl/acronym/date_time/personnel/poc catalogs modified.

## No Phase F/G Command-Layer Changes
Confirmed. `correction_nl_commands.py` untouched. `correction_classify.py` untouched.

## No Error Promotion
Confirmed. All active rules remain at their current severity levels. `global_default = advisory` unchanged.

## Known Limitations
- `window_envelope` still accepted via pass-through only; not in formal JSON policy/questions
- Warning summary uses static `_WARNING_MAP`; new rules require map updates
- Key-value/pass-through ingestion only; no NL parsing
- No production UI integration
- PDF generation deferred to L.6 or later

## Recommended Next Phase
**Phase L.6  Conversational Builder Payload-to-PDF Dry Run**
- Wire `finalize()` output into existing `pdf_v6_render.py` via safe isolated entry point
- Ensure payload normalization produces renderable JSON
- Add dry-run validation that payload schema matches renderer expectations
- Do not modify renderer layout logic; only validate payload compatibility

## Notes
- Advisory-level findings (e.g., CCI-CH7-SUBJ-005) are intentionally non-blocking. The builder distinguishes severity tiers: error = block, warning = block if pending, advisory = never block.
- The `accept_warnings` parameter on `finalize()` is a transient override for batch/automated use cases. It does not persist user decisions into `_user_decisions`.
