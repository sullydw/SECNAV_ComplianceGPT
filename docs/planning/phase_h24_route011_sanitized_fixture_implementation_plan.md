# Phase H.24 / Phase I.23 — Sanitized Fixture Implementation Plan

**Status:** Planning only  
**Rule:** `CCI-ROUTE-011`  
**Current state:** `CCI-ROUTE-011 = warning`; `CCI-ROUTE-010 = advisory`; `global_default = advisory`  
**Regression baseline:** 34 suites  
**Error promotion:** Not authorized

## 1. Purpose

Phase H.24 plans a possible future implementation phase for sanitized realistic `CCI-ROUTE-011` fixtures and a dedicated regression runner.

This phase is documentation-only. It does not create fixtures, create a runner, change configuration, change severity, promote a rule, roll back a rule, or modify runtime behavior.

## 2. Relationship to H.22 and H.23

H.22 established that repeated static synthetic burn-in checkpoints have diminishing returns and that the next useful evidence step is sanitized realistic Navy/Marine Corps-style payloads.

H.23 approved the read-only planning review and confirmed that H.19, H.20, and H.21 recorded identical clean synthetic results.

H.24 turns that planning direction into a future implementation plan, but does not perform the implementation.

## 3. Current Rule and Config State

- `CCI-ROUTE-011 = warning`
- `CCI-ROUTE-010 = advisory`
- `global_default = advisory`
- no error promotion authorized
- regression baseline remains 34 suites

Rollback remains config-only by restoring `CCI-ROUTE-011.effective_severity` to `advisory` if future evidence requires it.

## 4. Proposed Future Fixture Directory

If approved later, sanitized realistic payloads should be added under:

- `examples/burnin_h24_route011_sanitized/`

Possible future support files:

- `README.md` for fixture categories and sanitization rules.
- JSON payload files named by category and sequence.
- Optional generator only if all generated content is synthetic.

This H.24 step does not create that directory.

## 5. Proposed Future Runner

If approved later, a dedicated runner may be added at:

- `tools/run_phase_h24_route011_sanitized_fixture_regression.py`

The runner should validate expected `CCI-ROUTE-011` outcomes without changing validator behavior.

This H.24 step does not create that runner.

## 6. Proposed Fixture Target

Future implementation should target 25 to 50 sanitized realistic payloads.

Recommended fixture mix:

- 8 to 12 valid standard letters with `from`.
- 5 to 8 standard letters missing `from`.
- 5 to 8 null, empty, or whitespace-only `from` cases.
- 4 to 6 correctly tagged `window_envelope: true` cases.
- 4 to 6 window-envelope-like cases missing the flag.
- 4 to 6 non-standard document exclusions.
- 4 to 6 Navy-style routing examples.
- 4 to 6 Marine Corps-style routing examples.
- 4 to 6 distribution, copy-to, and via combinations.

Categories may overlap when the expected behavior is clearly documented.

## 7. Proposed Fixture Categories

| Category | Purpose | Expected Behavior |
|---|---|---|
| Valid standard letter with `from` | Normal pass behavior | No `CCI-ROUTE-011` finding |
| Missing `from` | Required-field detection | `CCI-ROUTE-011` warning/blocking finding |
| Null/empty/whitespace `from` | Data-quality detection | `CCI-ROUTE-011` warning/blocking finding |
| `window_envelope: true` | Suppression path | No `CCI-ROUTE-011` finding |
| Window-envelope-like without flag | Operator tagging risk | `CCI-ROUTE-011` warning/blocking finding |
| Non-standard document | Scope guard | No `CCI-ROUTE-011` finding |
| Navy/Marine Corps-style routing | Realism coverage | Expected pass/fail by payload |
| Distribution/copy-to/via combinations | Side-effect guard | From-line behavior only |

## 8. Proposed Per-Fixture Metadata

Each future fixture should have either embedded metadata or a manifest entry with:

- fixture id;
- category;
- document type;
- synthetic/sanitized marker;
- expected pass/fail result;
- expected `CCI-ROUTE-011` result;
- expected warning/blocking behavior;
- whether window-envelope behavior is being tested;
- brief rationale for the expected behavior.

## 9. Proposed Runner Checks

The future runner should verify:

1. Fixture directory exists.
2. Fixture count is within the approved target range.
3. All fixtures parse as JSON.
4. All fixtures are marked synthetic or sanitized.
5. Each fixture has an expected outcome.
6. Actual validator output matches expected outcome.
7. No false positives occur.
8. No false negatives occur.
9. Non-standard documents remain excluded.
10. `window_envelope: true` suppresses `CCI-ROUTE-011`.
11. Window-envelope-like payloads without the flag warn as expected.
12. Routing/via/copy-to/distribution combinations do not create unrelated findings.
13. H.13 config regression still passes.
14. H.16 burn-in regression still passes.
15. H.9 From-line validator regression still passes.
16. H.10 From-line evidence regression still passes.

The runner should not modify files or create logs.

## 10. Regression Gate Impact

If future implementation is approved, the new runner may become the 35th regression suite.

This planning-only step does not change regression inventory, suite count, GitHub Actions workflow configuration, or local gate scripts.

## 11. Required Review Before Implementation

Before fixture or runner implementation:

- Human approval is required to create fixtures.
- Human approval is required to create a runner.
- Human approval is required to change regression inventory.
- Sanitization rules must be reviewed before fixture creation.
- Expected outcomes must be defined before execution.
- Error-promotion work must not be combined with fixture implementation.

## 12. Explicit Prohibitions

This phase does not authorize config changes, severity changes, error promotion, rollback, fixture creation, runner creation, validator changes, rule catalog changes, renderer/layout changes, prompt/context/intake/UI/command-flow changes, Phase F/G command-layer changes, committing logs or unsanitized material, reading or modifying `docs/BOOTSTRAP.md`, or modifying `docs/HERMES_INSTRUCTIONS.md`.

## 13. Handoff Note

If direct updates to `docs/PROJECT_STATUS.md` or `docs/planning/correction_memory_and_rule_promotion_plan.md` are not safe because full-file editing is unavailable, create a separate H.24 handoff addendum instead of overwriting those long files.

## 14. Recommended Next Phase

Recommended next phase:

**Phase H.25 / Phase I.24 — H.24 Planning Review**

The next phase should review this H.24 plan and decide whether it is safe to proceed to actual fixture and runner creation in a later phase.
