# Phase J.11 / Phase K.3 — CCI-ROUTE-007 Duplicate Copy-to Regression Runner Plan

**Status:** Planning-only. No code changes. No runner created. No fixtures committed.

**Date:** 2026-06-10
**Author:** SECNAV ComplianceGPT rule promotion layer
**Rule candidate:** `CCI-ROUTE-007`
**Phase type:** Read-only regression/evidence planning

---

## 1. Current Reviewed State

### 1.1 J.10 / K.2 Review Verdict

`docs/planning/phase_j9_route007_duplicate_copyto_candidate_plan.md` was reviewed in Phase J.10 / Phase K.2 with the following verdict:

- **Verdict:** `APPROVE J.10 / K.2 ROUTE-007 CANDIDATE PLAN REVIEW`
- **Required fixes:** None
- **Evidence/regression planning:** APPROVED to proceed to regression runner/evidence planning when explicitly requested and approved

### 1.2 Rule Candidate Status

`CCI-ROUTE-007` remains an **advisory/heuristic candidate only**:

- Not in the config allowlist
- No severity override configured
- No effective_severity override
- Validator produces `warning`-class findings only
- No promotion to error is authorized

### 1.3 Config State (unchanged)

From `config/cci_enforcement_config.json`:

- `_allowlist` contains `CCI-ROUTE-010` and `CCI-ROUTE-011` only
- `CCI-ROUTE-007` is **not** in the allowlist
- `global_default` = `advisory`
- `CCI-ROUTE-010.effective_severity` = `warning` (warning pilot active)
- `CCI-ROUTE-011.effective_severity` = `warning` (warning pilot active)
- Error promotion remains **unauthorized**

### 1.4 Existing Runner State

- `tools/run_cci_routing_regression.py` — 4 tests (valid, via_unnumbered, copyto_excess, need_to_know)
- No dedicated `CCI-ROUTE-007` duplicate detection runner exists
- No dedicated `CCI-ROUTE-007` fixtures exist in `examples/`
- `examples/audit_cci_combined_warning.json` contains a **live** `CCI-ROUTE-007` trigger (see Section 2.4)

---

## 2. Current Validator Behavior

### 2.1 Exact Normalized Duplicate Detection

`src/cci_routing_validate.py` lines 216-235 implement `CCI-ROUTE-007`:

```python
# Rule 007: duplication with To or Via
to_entries = _normalize_list(_get_field(payload, _TO_FIELD_NAMES))
via_entries = _normalize_list(_get_field(payload, _VIA_FIELD_NAMES))

for i, entry in enumerate(copy_entries, start=1):
    entry_norm = _normalize_for_match(entry)
    for to_entry in to_entries:
        if _normalize_for_match(to_entry) == entry_norm:
            warnings.append(
                f"CCI-ROUTE-007: Copy-to entry {i} {entry!r} duplicates To line "
                f"addressee {to_entry!r}; verify role is not duplicated"
            )
            break
    for via_entry in via_entries:
        if _normalize_for_match(via_entry) == entry_norm:
            warnings.append(
                f"CCI-ROUTE-007: Copy-to entry {i} {entry!r} duplicates Via line "
                f"addressee {via_entry!r}; verify role is not duplicated"
            )
            break
```

### 2.2 Normalization Details

- `_normalize_for_match()` lowercases and collapses whitespace (`" ".join(str(text).lower().split())`)
- Exact equality of normalized strings is required
- Near-duplicates and abbreviations do **not** trigger
- Case differences and extra whitespace **do** trigger after normalization

### 2.3 First-Match-Only Behavior

- Each Copy-to entry is checked against `to` entries first
- If a match is found in `to`, the warning is emitted and `via` is **not** checked for that entry
- If no `to` match, `via` entries are checked
- A Copy-to entry can trigger at most **one** ROUTE-007 warning

### 2.4 Live Trigger in Combined Fixture

`examples/audit_cci_combined_warning.json` contains:

- `via`: `["Commander, Naval Surface Force Atlantic", ...]` (line 8)
- `copy_to`: `[..., "Commander, Naval Surface Force Atlantic"]` (line 15)

When validated, this produces:

```
CCI-ROUTE-007: Copy-to entry 3 'Commander, Naval Surface Force Atlantic' duplicates Via line addressee 'Commander, Naval Surface Force Atlantic'; verify role is not duplicated
```

This confirms the validator logic is live and functioning.

---

## 3. Proposed Runner

### 3.1 Filename

```
tools/run_phase_j12_route007_duplicate_copyto_regression.py
```

### 3.2 Purpose

Dedicated deterministic regression runner for `CCI-ROUTE-007` exact duplicate matching.

### 3.3 Design Principles

1. **Use existing validator entry point** — Call `src/cci_routing_validate.py` via subprocess, same pattern as `tools/run_cci_routing_regression.py`
2. **Do not change catalog** — Fixtures must use existing `doc_type`, `component`, and payload fields
3. **Do not change config** — No `cci_enforcement_config.json` modifications
4. **Do not change severity** — All ROUTE-007 findings remain advisory/warning only
5. **Do not change validator** — Existing `_check_copy_to()` logic is sufficient
6. **Sanitized/synthetic fixtures only** — No real correspondence data
7. **Deterministic assertions** — Expected results are exact string matches, not heuristic interpretation

### 3.4 Runner Structure (proposed)

```
def run_validator(root, fixture, expect_route007=False, expected_count=0)
    """Run cci_routing_validate.py on a fixture.

    expect_route007: bool — whether CCI-ROUTE-007 should appear in output
    expected_count: int — expected number of CCI-ROUTE-007 warnings
    """
```

The runner should:
- Load fixture from `examples/audit_cci_routing_route007_*.json`
- Run `python src/cci_routing_validate.py examples/<fixture>`
- Parse stdout for `CCI-ROUTE-007:` occurrences
- Assert `expect_route007` matches actual presence
- Assert `expected_count` matches actual count
- Report PASS/FAIL per fixture
- Aggregate PASS/FAIL at end
- Exit 0 if all pass, exit 1 if any fail

---

## 4. Proposed Test Cases

### 4.1 Positive Cases (must trigger CCI-ROUTE-007)

| # | Fixture name | Description | Expected |
|---|---|---|---|
| 1 | `audit_cci_routing_route007_copyto_duplicates_to.json` | Copy-to entry exactly matches To entry | 1 warning, contains `CCI-ROUTE-007` and `duplicates To line` |
| 2 | `audit_cci_routing_route007_copyto_duplicates_via.json` | Copy-to entry exactly matches Via entry | 1 warning, contains `CCI-ROUTE-007` and `duplicates Via line` |
| 3 | `audit_cci_routing_route007_multiple_copyto_one_duplicate.json` | 3 Copy-to entries, 1 duplicates Via | 1 warning for duplicate entry only; other 2 silent |
| 4 | `audit_cci_routing_route007_normalized_duplicate.json` | Copy-to differs by case/extra spaces from To; normalized match | 1 warning after normalization |
| 5 | `audit_cci_routing_route007_to_and_via_both_present_copyto_duplicates_via.json` | To and Via both present; Copy-to duplicates only Via | 1 warning, contains `duplicates Via line` |
| 6 | `audit_cci_routing_route007_multiple_via_one_duplicate.json` | 3 Via entries; Copy-to duplicates one | 1 warning, identifies correct Via entry |

### 4.2 Negative Cases (must NOT trigger CCI-ROUTE-007)

| # | Fixture name | Description | Expected |
|---|---|---|---|
| 7 | `audit_cci_routing_route007_no_duplicate.json` | No overlap between Copy-to and To/Via | 0 ROUTE-007 warnings |
| 8 | `audit_cci_routing_route007_near_duplicate.json` | Same organization, different wording (`CO, USS NIMITZ` vs `Commanding Officer, USS NIMITZ`) | 0 ROUTE-007 warnings |
| 9 | `audit_cci_routing_route007_abbreviation.json` | Abbreviation does not normalize to exact match | 0 ROUTE-007 warnings |
| 10 | `audit_cci_routing_route007_empty_copyto.json` | Empty Copy-to list | 0 ROUTE-007 warnings |
| 11 | `audit_cci_routing_route007_copyto_self_duplicate_only.json` | Two Copy-to entries are identical to each other but not in To/Via | 0 ROUTE-007 warnings (duplicate Copy-to alone is not a ROUTE-007 violation) |
| 12 | `audit_cci_routing_route007_punctuation_diff.json` | Same text with different punctuation (trailing period, comma) | 0 or 1 depending on normalization; this tests edge case |

### 4.3 Cross-Rule Preservation Cases

| # | Fixture name | Description | Expected |
|---|---|---|---|
| 13 | `audit_cci_routing_route007_combined_with_010_011.json` | Fixture triggers ROUTE-007 + existing ROUTE-010 + ROUTE-011 conditions | ROUTE-007 warning emitted; ROUTE-010/011 behavior unchanged; no findings promoted to error |

---

## 5. Expected Assertions

### 5.1 Positive Control Assertions

For every positive fixture:

1. `assert "CCI-ROUTE-007" in stdout`
2. `assert "duplicates To line" in stdout` OR `assert "duplicates Via line" in stdout`
3. `assert expected_count == actual_route007_count`
4. `assert "FAIL" not in stdout` (warnings-only; validator exits 0)

### 5.2 Negative Control Assertions

For every negative fixture:

1. `assert "CCI-ROUTE-007" not in stdout`
2. `assert actual_route007_count == 0`
3. Other rule warnings (ROUTE-010, ROUTE-011, etc.) may be present and should not be suppressed

### 5.3 Cross-Rule Preservation Assertions

For combined fixtures:

1. `assert "CCI-ROUTE-010" in stdout` (if applicable)
2. `assert "CCI-ROUTE-011" in stdout` (if applicable)
3. `assert "CCI-ROUTE-007" in stdout`
4. `assert "FAIL" not in stdout`
5. No findings promoted to error

---

## 6. Evidence Checkpoint After Runner Creation

### 6.1 Future Checkpoint Document

```
docs/checkpoints/phase_j12_route007_duplicate_copyto_regression_checkpoint.md
```

### 6.2 Checkpoint Contents

The future checkpoint must document:

1. Runner result (PASS/FAIL)
2. Fixture count (positive + negative + cross-rule)
3. Positive coverage (which duplicate scenarios are tested)
4. Negative coverage (which non-duplicate scenarios are tested)
5. No config changes made
6. No severity changes made
7. No allowlist changes made
8. No validator changes made
9. No catalog changes made
10. No renderer/layout changes made
11. Decision: continue, refine fixtures, or defer

---

## 7. Future Review Path

This path is **proposed only** and requires explicit approval before any step is executed.

| Phase | Action | Approval Required |
|---|---|---|
| J.12 / K.4 | Implement runner and fixtures; run evidence checkpoint | Yes |
| J.13 / K.5 | Read-only evidence review: evaluate false-positive/false-negative rates | Yes |
| J.14 / K.6 | Decision: defer, continue advisory, or plan source/catalog refinement | Yes |
| *(future)* | Only after evidence review, consider config allowlist planning | Separate approval |
| *(future)* | Warning-pilot activation only if separately approved | Separate approval |
| *(future)* | Error promotion only if separately approved after burn-in | Separate approval |

**No step in this path may be executed without user approval.**

---

## 8. Explicit Prohibitions

The following actions are **prohibited** in Phase J.11 / Phase K.3 and remain prohibited unless separately approved in a future phase:

1. No config changes.
2. No severity changes.
3. No allowlist changes (`CCI-ROUTE-007` remains not allowlisted).
4. No error promotion.
5. No rollback of existing warning pilots.
6. No validator changes.
7. No catalog changes.
8. No renderer or layout changes.
9. No prompt, context, intake, UI, or command-flow changes.
10. No Phase F or Phase G command-layer changes.
11. No runner creation in this phase.
12. No fixtures committed in this phase.
13. No logs or unsanitized material committed.
14. Do not read or modify `docs/BOOTSTRAP.md`.
15. Do not modify `docs/HERMES_INSTRUCTIONS.md`.

---

## 9. Decision

**Decision:** Plan a dedicated regression runner and fixture set for `CCI-ROUTE-007` exact duplicate Copy-to detection.

**Rationale:**
- J.10/K.2 candidate plan review approved the evaluation path
- Validator already implements exact duplicate detection
- Scope is narrow and deterministic
- Existing combined fixture confirms live trigger behavior
- Dedicated runner will provide bounded, repeatable evidence for future severity discussions
- No config/severity/catalog/validator changes required to begin

**Status:** Planning-only. No implementation authorized.

---

## 10. Recommended Next Phase

**Phase J.12 / Phase K.4 — ROUTE-007 Duplicate Copy-to Regression Runner Implementation**

- Create `tools/run_phase_j12_route007_duplicate_copyto_regression.py`
- Create sanitized synthetic fixtures in `examples/`
- Run validator against all fixtures
- Document results in `docs/checkpoints/phase_j12_route007_duplicate_copyto_regression_checkpoint.md`
- Requires explicit user approval before execution
- No config changes
- No severity changes
- Error promotion remains unauthorized

---

End of Phase J.11 / Phase K.3 — CCI-ROUTE-007 Duplicate Copy-to Regression Runner Plan.
