# Phase L.5A Conversational Builder Regression Harness Allowlist Cleanup Checkpoint

## Date
2026-06-11

## Baseline
Latest commit before L.5A: `c2d85f2` — `Docs: Update checkpoint and PROJECT_STATUS with L.5 commit hashes`

## Files Changed
- `tools/run_phase_h4_routing_office_code_validator_regression.py` — added L.4/L.5 builder artifacts to `allowed` set in Check 17 (git-status cross-check)

## Exact Allowlist/Status-Check Update
In `tools/run_phase_h4_routing_office_code_validator_regression.py`, Check 17 inspects `git diff HEAD --name-only` and compares against a hardcoded `allowed` set. Added the following entries to that set:

```python
# Phase L.4 / L.5 artifacts (conversational builder)
"src/conversational_builder.py",
"tools/run_phase_l4_conversational_builder_regression.py",
"tools/run_phase_l5_conversational_builder_validation_summary_regression.py",
"docs/planning/phase_l1_conversational_builder_workflow_plan.md",
"docs/planning/phase_l2_conversational_builder_entrypoint_review.md",
"docs/planning/phase_l3_conversational_builder_payload_schema_question_flow.md",
"docs/checkpoints/phase_l4_conversational_builder_prototype_checkpoint.md",
"docs/checkpoints/phase_l5_conversational_builder_validation_summary_checkpoint.md",
```

No other regression harness files were modified. H.6, H.13, H.16, and H.24 do not have their own git-status checks; they cascade through H.4 or each other as sub-runners. By fixing H.4's allowlist, the cascade failures are eliminated.

## Confirmation: No Builder Behavior Changed
- `src/conversational_builder.py` untouched.
- No changes to `IntakeOrchestrator`, validators, renderer, config, or command layer.
- This is purely regression-harness hygiene.

## Regression Results (Post-Cleanup)

### Individual targeted runners
| Runner | Result |
|--------|--------|
| run_phase_l4_conversational_builder_regression.py | **PASS** (41/41) |
| run_phase_l5_conversational_builder_validation_summary_regression.py | **PASS** (36/36) |
| run_phase_h4_routing_office_code_validator_regression.py | **PASS** (18/18) |
| run_phase_h6_routing_office_code_evidence_regression.py | **PASS** (15/15) |
| run_phase_h13_config_regression.py | **PASS** (27/27) |
| run_phase_h16_route011_burnin_regression.py | **PASS** (96/96) |
| run_phase_h24_route011_sanitized_fixture_regression.py | **PASS** (36/36) |
| run_intake_regression.py | **PASS** |
| run_phase_k3_subject_terminal_punctuation_regression.py | **PASS** (11/11) |

### Full non-PDF gate
- 35 non-PDF regression runners executed.
- **35 passed, 0 failed.**
- No cascade failures remain.

### PDF suites (environmental limitations)
- C7, C8, C9, C10 runners remain **FAIL** due to missing `reportlab`/`fitz` in this environment.
- These are **pre-existing** and unrelated to L.5A.

## No Renderer/Layout Changes
Confirmed. `pdf_v6_render.py` and `audit_pdf_layout.py` untouched.

## No CCI Config/Severity Changes
Confirmed. `cci_severity_config.json` and `cci_enforcement_config.json` untouched.

## No Validator/Catalog Changes
Confirmed. No validator source files or rule catalogs modified.

## No Phase F/G Command-Layer Changes
Confirmed. `correction_nl_commands.py`, `correction_classify.py` untouched.

## No Error Promotion
Confirmed. All active rules remain at current severity levels.

## Recommended Next Phase
**Phase L.6  Conversational Builder Payload-to-PDF Dry Run**
- Wire `finalize()` output into existing `pdf_v6_render.py` via safe isolated entry point.
- Ensure payload normalization produces renderable JSON.
- Add dry-run validation that payload schema matches renderer expectations.
- Do not modify renderer layout logic; only validate payload compatibility.

## Notes
- The H.4 allowlist pattern (hardcoded `allowed` set compared against `git diff HEAD --name-only`) is used by several historical runners. Future builder artifacts should be added to this allowlist proactively, or the pattern should be generalized. Deferring that refactor to a later maintenance phase.
