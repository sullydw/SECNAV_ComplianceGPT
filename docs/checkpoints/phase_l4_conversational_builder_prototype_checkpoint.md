# Phase L.4 Conversational Builder Prototype Checkpoint

## Date
2026-06-11

## Baseline
Latest verified baseline: `2f2ba95`
Current HEAD after L.3: `2771f0a`

## Files Changed
- `src/conversational_builder.py` — new prototype module (Phase L.4)
- `tools/run_phase_l4_conversational_builder_regression.py` — new regression runner
- `docs/PROJECT_STATUS.md` — updated (this commit)
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — updated (this commit)
- `docs/checkpoints/phase_l4_conversational_builder_prototype_checkpoint.md` — this file

## Prototype Scope
Isolated conversational builder module with zero changes to renderer, validators, config, catalogs, or command layers.

### BuilderSession Methods Implemented
- `start(initial_payload=None)` — initializes session, returns first question/status
- `ingest_user_message(text)` — parses key:value pairs or applies text as answer to current question; updates orchestrator; returns status + next question
- `next_question()` — returns next missing-field question (required first, then recommended, then optional)
- `build_payload()` — returns current merged payload from orchestrator
- `run_validation()` — runs CCI_AUDIT_V1 via existing validator entry point
- `warning_summary()` — maps audit findings to plain-English messages for CCI-ROUTE-010, CCI-ROUTE-011, CCI-CH7-SUBJ-002, plus generic advisory fallback
- `finalize(accept_warnings=False)` — normalizes payload, sets draft/final status, returns structured JSON with payload, audit, and warning summary
- `record_user_decision(rule_code, decision)` — stores explicit user acceptance/revision/ignore choices per warning
- `set_draft_final_status(status)` — sets "draft" or "final"

### Key Behaviors
- Key-value/pass-through ingestion only; no NL parsing
- Deterministic step resolution: intake -> routing -> body -> refs_encls -> signature -> validation -> finalize
- `window_envelope` captured as optional boolean in payload (not added to JSON policy/questions to avoid regression failures)
- Signature coercion supports list input (e.g., `["J. DOE", "By direction"]`)
- Body coercion splits multi-line strings into paragraph list

## Test Coverage
10 tests in `tools/run_phase_l4_conversational_builder_regression.py`:
1. builder_start — session_id set, step valid
2. missing_required_tracked — from/subj/to/date missing for standard_letter
3. key_value_ingestion — from/to/subj/window_envelope captured
4. next_question_behavior — returns required when missing, recommended after required filled
5. window_envelope_field — yes -> True, false -> False
6. warning_summary_known_ids — CCI-CH7-SUBJ-002 mapped, CCI-ROUTE/010/011 framework ready
7. generic_fallback — advisory severity present for unknown findings
8. no_renderer_mutation — pdf_v6_render.py file intact (no import to avoid reportlab dependency)
9. finalize_returns_structured_payload — payload, audit, warning_summary, builder_version L.4
10. run_validation_returns_audit_v1 — schema_version CCI_AUDIT_V1, validators + summary present

Result: **39 passed, 0 failed**

## Full Gate Result
37-suite regression executed.

### Results Summary
| Runner | Result |
|--------|--------|
| run_intake_regression.py | PASS |
| run_phase_h13_config_regression.py | PASS |
| run_phase_h4_routing_office_code_validator_regression.py | PASS |
| run_phase_h6_routing_office_code_evidence_regression.py | PASS |
| run_phase_k3_subject_terminal_punctuation_regression.py | PASS |
| run_phase_h24_route011_sanitized_fixture_regression.py | PASS |
| run_phase_h16_route011_burnin_regression.py | PASS |
| run_phase_h2_subject_acronym_validator_regression.py | PASS |
| run_phase_h3_second_rule_catalog_regression.py | PASS |
| run_phase_h8_third_rule_catalog_regression.py | PASS |
| run_phase_h9_from_line_validator_regression.py | PASS |
| run_phase_h10_from_line_evidence_regression.py | PASS |
| run_phase_j12_route007_duplicate_copyto_regression.py | PASS |
| run_cci_subject_regression.py | PASS |
| run_cci_routing_regression.py | PASS |
| run_cci_ref_encl_regression.py | PASS |
| run_cci_acronym_regression.py | PASS |
| run_cci_date_time_regression.py | PASS |
| run_cci_personnel_regression.py | PASS |
| run_cci_poc_regression.py | PASS |
| run_cci_audit_regression.py | PASS |
| run_context_schema_regression.py | PASS |
| run_correction_regression.py | PASS |
| run_correction_classify_regression.py | PASS |
| run_correction_command_regression.py | PASS |
| run_correction_implementation_regression.py | PASS |
| run_correction_nl_command_regression.py | PASS |
| run_correction_pending_regression.py | PASS |
| run_correction_profile_promotion_regression.py | PASS |
| run_correction_review_regression.py | PASS |
| run_correction_session_regression.py | PASS |
| run_profile_regression.py | PASS |
| run_c8_regression.py | PASS |
| run_c9_regression.py | PASS |
| run_c10_regression.py | PASS (validator); PDF render FAIL (pre-existing reportlab/fitz missing) |
| run_c7_phase1_regression.py | PASS (validator); PDF render/layout FAIL (pre-existing reportlab/fitz missing) |
| run_pilot_subject_acronym_rule_catalog_regression.py | PASS |
| **run_phase_l4_conversational_builder_regression.py** | **PASS** |

**Note on PDF failures:** C7 and C10 PDF render/layout checks fail because `reportlab` and `fitz` (PyMuPDF) are not installed in the current environment. These are **pre-existing failures** unrelated to L.4 — no renderer code was modified.

## No Renderer/Layout Changes
Confirmed. `pdf_v6_render.py` untouched. `audit_pdf_layout.py` untouched.

## No CCI Config/Severity Changes
Confirmed. `cci_severity_config.json` untouched. `cci_config_defaults.json` untouched.

## No Validator/Catalog Changes
Confirmed. No validator source files modified. No routing/subject/ref_encl/acronym/date_time/personnel/poc catalogs modified.

## No Phase F/G Command-Layer Changes
Confirmed. `correction_nl_commands.py` untouched. `correction_classify.py` untouched. No new NL intents added.

## No Error Promotion
Confirmed. All active rules remain at their current severity levels. `global_default = advisory` unchanged.

## Known Limitations
- **Key-value/pass-through only** — no natural language parsing in this phase
- **No production UI integration** — prototype is a Python class, not a web/CLI chatbot yet
- **PDF generation not part of L.4** — `finalize()` returns structured JSON only; rendering deferred to L.6 or later
- **No window_envelope in JSON policy/questions** — field is accepted by builder but not formally declared in `cci_intake_field_policy.json` or `cci_intake_questions.json` to avoid regression side effects; can be added later with regression updates
- **Warning summary uses static map** — `_WARNING_MAP` hardcodes messages for the three active pilots; new rules require map updates

## Recommended Next Phase
**Phase L.5  Conversational Builder Validation Summary Integration**
- Wire warning_summary into a user-facing approval flow
- Add accept/revise/ignore decision persistence per warning
- Integrate with session-based correction memory if applicable
- Keep blocking behavior aligned with current severity levels (advisory/warning = non-blocking, error = blocking)

## Notes
- `window_envelope` was added to `cci_intake_field_policy.json` and `cci_intake_questions.json` initially, then **reverted** after H.4 regression check 17 failed (only expected validator files changed). The builder module still accepts and coerces `window_envelope` via pass-through ingestion; formal JSON schema alignment is deferred to a later phase with regression updates.
- Builder session history is in-memory only; no persistence layer added.
