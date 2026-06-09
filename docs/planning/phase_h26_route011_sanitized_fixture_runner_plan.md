# Phase H.26 / Phase I.25 — Sanitized Fixture and Runner Implementation Plan

**Status:** Planning only  
**Rule:** `CCI-ROUTE-011`  
**Current state:** `CCI-ROUTE-011 = warning`; `CCI-ROUTE-010 = advisory`; `global_default = advisory`  
**Regression baseline:** 34 suites  
**Error promotion:** Not authorized

---

## 1. Relationship to H.22–H.25

| Phase | Role | Result |
|---|---|---|
| H.22 | Identified need for sanitized realistic evidence | `docs/planning/phase_h22_route011_sanitized_realistic_evidence_plan.md` created |
| H.23 | Read-only review of H.22 | `APPROVE H.23 READ-ONLY PLANNING REVIEW` — confirmed identical clean synthetic metrics |
| H.24 | Proposed fixture/runner implementation | `docs/planning/phase_h24_route011_sanitized_fixture_implementation_plan.md` created |
| H.25 | Read-only review of H.24 | `APPROVE H.25 READ-ONLY PLANNING REVIEW` — confirmed bounded and safe |
| H.26 | **Exact future implementation design** | This document defines precise fixture count, naming, manifest schema, runner behavior, and approval gates |

H.26 is the final planning step before any implementation. No fixtures, no runner, and no config changes are created in this phase.

---

## 2. Current Rule and Config State

- `CCI-ROUTE-011.effective_severity` = `warning`
- `CCI-ROUTE-010.effective_severity` = `advisory`
- `global_default` = `advisory`
- No error-level promotion exists
- No rule rollback is planned
- Regression gate remains 34 suites
- Rollback remains config-only

---

## 3. Future Fixture Directory

If approved later, sanitized realistic payloads will live under:

- `examples/burnin_h24_route011_sanitized/`

This path follows the existing `burnin_h16_route011/` naming convention but adds a `_sanitized` suffix to distinguish realistic Navy/Marine Corps-style fixtures from the original synthetic set.

---

## 4. Future Runner

If approved later, a dedicated runner will be added at:

- `tools/run_phase_h24_route011_sanitized_fixture_regression.py`

The runner filename preserves the H.24 planning phase label to maintain traceability.

---

## 5. Exact Future Fixture Count

**Recommended target: 32 fixtures.**

Rationale:

- Large enough to cover all 11 defined categories with at least 2–3 examples per category.
- Small enough to review manually, diff in PRs, and debug quickly if a fixture fails.
- 32 is a power of two, making it easy to reason about half/quarter splits during triage.
- Does not overwhelm the CI runner or local gate execution time.
- Aligns with the H.22 suggested range (25–50) while staying toward the conservative end.

---

## 6. Exact Fixture Naming Convention

All fixture filenames use category prefix + three-digit sequence:

| Category Prefix | Description | Planned Count |
|---|---|---|
| `valid_from_` | Standard letter with valid `from` line | 4 |
| `missing_from_` | Standard letter with `from` field absent | 3 |
| `null_from_` | Standard letter with `"from": null` | 2 |
| `empty_from_` | Standard letter with `"from": ""` | 2 |
| `whitespace_from_` | Standard letter with whitespace-only `from` | 2 |
| `window_envelope_tagged_` | `window_envelope: true` present | 3 |
| `window_envelope_missing_flag_` | Looks like window envelope but flag absent | 3 |
| `nonstandard_doc_` | Memo, endorsement, joint, MFR, etc. | 3 |
| `navy_routing_` | Navy-style routing combinations | 3 |
| `marine_routing_` | Marine Corps-style routing combinations | 3 |
| `distribution_combo_` | Distribution, copy-to, via combinations | 4 |

**Total: 32 fixtures.**

Examples:

- `valid_from_001.json`
- `valid_from_002.json`
- `missing_from_001.json`
- `window_envelope_tagged_003.json`
- `distribution_combo_004.json`

---

## 7. Manifest Design

A manifest file will be added at:

- `examples/burnin_h24_route011_sanitized/manifest.json`

The manifest is the single source of truth for expected outcomes. Test expectations live in the manifest, not inside the payload JSON, to keep payloads renderer/audit-compatible and free of test metadata.

### 7.1 Manifest Schema

Each manifest entry must contain:

| Field | Type | Required | Description |
|---|---|---|---|
| `fixture_filename` | string | yes | Name of the payload file |
| `fixture_id` | string | yes | Unique ID (e.g., `h24_san_001`) |
| `category` | string | yes | One of the 11 category prefixes |
| `doc_type` | string | yes | Document type used in payload |
| `marker` | string | yes | `"synthetic"` or `"sanitized"` |
| `expected_route011_present` | boolean | yes | `true` if warning expected, `false` if no finding expected |
| `expected_severity` | string | yes | `"warning"` or `"advisory"` or `"none"` |
| `expected_finding_count` | integer | yes | Expected number of `CCI-ROUTE-011` findings in result |
| `tests_window_envelope` | boolean | yes | `true` if this fixture tests window-envelope behavior |
| `rationale` | string | yes | One-line explanation of expected behavior |

### 7.2 Manifest Top-Level Fields

```json
{
  "_schema_version": "H24_SANITIZED_MANIFEST_V1",
  "_description": "Expected outcomes for H.24 sanitized CCI-ROUTE-011 fixtures",
  "_total_fixtures": 32,
  "_created": "2026-06-09",
  "fixtures": []
}
```

---

## 8. Fixture Payload Design

### 8.1 Payload Content Rules

- Payloads must be normal renderer/audit-compatible JSON.
- No real names; use `COMMANDING OFFICER, USS EXAMPLE` or `COMMANDING OFFICER, MARINE CORPS BASE EXAMPLE`.
- No real unit codes; use `N00`, `N1`, `SUP`, or generic placeholders.
- No real hull numbers; use `CVN-68`, `DDG-1000`, etc.
- No real dates tied to actual events; use `2026-06-09` or similar.
- No email addresses, phone numbers, or mailing addresses.
- No real signatures; use generic signature block text.
- No unique identifiers, case numbers, or file designators that could trace to real correspondence.
- All fixtures must be clearly labeled `synthetic` or `sanitized` in the manifest.

### 8.2 Where Expectations Live

- **Manifest** holds all expected outcomes.
- **Payload** holds only the data to be validated.
- No `_expected_` keys inside the payload JSON unless an existing runner pattern strictly requires it.

---

## 9. Runner Behavior

If approved later, the runner must:

1. Load `manifest.json`.
2. Verify manifest `_total_fixtures` matches actual file count.
3. For each manifest entry:
   a. Load the payload JSON.
   b. Verify payload is parseable.
   c. Verify payload contains a `synthetic` or `sanitized` marker in a known field or manifest reference.
   d. Run the payload through the existing CCI audit/validator path (e.g., `validator_runner` or equivalent).
   e. Compare actual `CCI-ROUTE-011` findings against `expected_route011_present`.
   f. Compare actual severity against `expected_severity`.
   g. Compare actual finding count against `expected_finding_count`.
   h. Record PASS or FAIL for the fixture.
4. Report results in a clear per-fixture table.
5. Final result: PASS only if all fixtures pass.

### 9. Hard Fail Conditions

The runner must fail (non-zero exit code) if any of the following occur:

- False positive: `CCI-ROUTE-011` appears when `expected_route011_present` is `false`.
- False negative: `CCI-ROUTE-011` is absent when `expected_route011_present` is `true`.
- Severity mismatch: actual severity does not match `expected_severity`.
- `window_envelope: true` present in payload but `CCI-ROUTE-011` is not suppressed.
- Window-envelope-like payload without `window_envelope: true` does not produce expected warning.
- Non-standard document type triggers `CCI-ROUTE-011`.
- Fixture count differs from manifest `_total_fixtures`.
- Any fixture lacks `synthetic` or `sanitized` marker.
- Any fixture JSON fails to parse.
- Manifest fails to parse.

### 9.3 What the Runner Must NOT Do

- Do not create log files.
- Do not modify existing fixtures, manifests, or payloads.
- Do not modify config, rule catalogs, validators, renderers, or prompt contracts.
- Do not modify the regression inventory or gate scripts.
- Do not commit anything automatically.

---

## 10. Regression Integration

### 10.1 Current Baseline

- Regression gate: 34 suites.
- This planning step does not change the regression inventory.

### 10.2 Future Integration

If fixture/runner implementation is approved later, the new runner may become the **35th regression suite**.

Before any future commit that adds the runner, the following must pass:

- H.24 new runner (future)
- H.13 config regression: 27/27 PASS
- H.16 burn-in regression: 96/96 PASS
- H.9 From-line validator regression: 18/18 PASS
- H.10 From-line evidence regression: 39/39 PASS
- Full 34-suite (or 35-suite) gate: ALL PASS

This planning-only step does not modify `.github/workflows/regression.yml` or any local gate script.

---

## 11. Approval Gates

Before any future implementation, the following approvals are required:

| Gate | Required | Description |
|---|---|---|
| Fixture creation approval | Yes | Explicit user approval to create the `examples/burnin_h24_route011_sanitized/` directory and populate it with 32 fixtures. |
| Runner creation approval | Yes | Explicit user approval to create `tools/run_phase_h24_route011_sanitized_fixture_regression.py`. |
| Regression inventory update approval | Yes | Explicit user approval to add the runner to the full regression gate list and any CI workflow. |
| Error-promotion prohibition | Permanent | No error-promotion work may be combined with fixture/runner implementation. |

---

## 12. Explicit Prohibitions

This phase does not authorize:

- config changes;
- severity changes;
- error promotion;
- rollback;
- fixture creation (H.26 is planning-only);
- runner creation (H.26 is planning-only);
- validator changes;
- rule catalog changes;
- renderer/layout changes;
- prompt/context/intake/UI/command-flow changes;
- Phase F/G command-layer changes;
- committing logs or unsanitized material;
- reading or modifying `docs/BOOTSTRAP.md`;
- modifying `docs/HERMES_INSTRUCTIONS.md`.

---

## 13. Recommended Decision

Keep `CCI-ROUTE-011` at warning, keep `CCI-ROUTE-010` advisory, keep error promotion unauthorized, and keep the 34-suite regression baseline unchanged.

H.26 defines the exact design for future sanitized fixture and runner implementation. Implementation itself requires separate explicit approval.

---

## 14. Recommended Next Phase

**Phase H.27 / Phase I.26 — H.26 Planning Review**

The next phase should review this H.26 plan and decide whether it is safe to proceed to actual fixture and runner creation in a later implementation phase.

Alternatively, if the user explicitly approves implementation:

**Phase H.28 / Phase I.27 — Sanitized Fixture and Runner Implementation**

Create the 32 fixtures, the manifest, and the runner, then run the full regression gate (now 35 suites) before committing.

---

End of Phase H.26 / Phase I.25 Sanitized Fixture and Runner Implementation Plan.
