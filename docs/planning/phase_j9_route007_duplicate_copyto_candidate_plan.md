# Phase J.9 / Phase K.1 — CCI-ROUTE-007 Duplicate Copy-to Candidate Plan

**Status:** Planning-only. No code changes. No config changes. No severity changes.

**Date:** 2026-06-10
**Author:** SECNAV ComplianceGPT rule promotion layer
**Rule candidate:** `CCI-ROUTE-007`
**Phase type:** Read-only planning and evaluation

---

## 1. Current State

### 1.1 Catalog Entry

`CCI-ROUTE-007` exists in `rules_v6/CCI/cci_ch2_routing_rules.json` with the following fields:

| Field | Value |
|---|---|
| `rule_id` | `CCI-ROUTE-007` |
| `source` | `SECNAV M-5216.5 Chapter 7 addressing conventions` |
| `source_type` | `manual_text` |
| `source_location` | `Chapter 7 To / Via / Copy-to separation` |
| `applies_to` | `standard_letter`, `multiple_address_letter`, `endorsement`, `joint_letter`, `memorandum_for_record`, `from_to_memo`, `plain_paper_memo`, `letterhead_memo` |
| `component_scope` | `universal` |
| `rule_text_summary` | `The same addressee should not appear as both an action addressee (To or Via) and a Copy-to recipient.` |
| `enforcement` | `heuristic_warning` |
| `validator` | `cci_routing` |
| `severity` | `warning` |

### 1.2 Validator Behavior

`src/cci_routing_validate.py` already implements exact duplicate detection for `CCI-ROUTE-007`:

- `_check_copy_to()` iterates over each `copy_to` entry.
- For each entry, it computes `_normalize_for_match(entry)`, which lowercases and collapses whitespace.
- It compares against every `to` entry and every `via` entry using the same normalization.
- On exact match, it appends a warning of the form:
  - `CCI-ROUTE-007: Copy-to entry N {entry!r} duplicates To line addressee {to_entry!r}; verify role is not duplicated`
  - `CCI-ROUTE-007: Copy-to entry N {entry!r} duplicates Via line addressee {via_entry!r}; verify role is not duplicated`

### 1.3 Config State

From `config/cci_enforcement_config.json`:

- `_allowlist` contains `CCI-ROUTE-010` and `CCI-ROUTE-011` only.
- `CCI-ROUTE-007` is **not** in the allowlist.
- `global_default` = `advisory`.
- `CCI-ROUTE-010.effective_severity` = `warning`.
- `CCI-ROUTE-011.effective_severity` = `warning`.
- Error promotion remains **unauthorized**.

### 1.4 Regression State

- Suite count: **35 suites**.
- Full 35-suite gate verified PASS.
- No existing regression runner specifically targets `CCI-ROUTE-007` duplicate detection.

---

## 2. Why This Is a Good Next Candidate

1. **Deterministic behavior is already implemented.** The validator uses exact normalized string comparison, which is deterministic enough for controlled testing. There is no parsing ambiguity about what constitutes a match.

2. **Limited scope.** The rule applies only to Copy-to versus To/Via. It does not require understanding command structure, chain of command, or document-type-specific formatting beyond the existing routing fields.

3. **Smaller ambiguity than vague routing rules.** Unlike `CCI-ROUTE-004` ("name specific addressees rather than generic routing phrases") or `CCI-ROUTE-006` ("Copy-to entries should be specific"), `CCI-ROUTE-007` is a binary exact-match check. The ambiguity surface is limited to normalization choices (whitespace, case).

4. **Existing validator logic.** No new validator code is needed to begin controlled testing. The existing `_check_copy_to()` logic in `src/cci_routing_validate.py` already produces `CCI-ROUTE-007` warnings.

5. **Likely user-facing value.** Preventing an addressee from being listed as both an action recipient and a copy recipient is a concrete compliance concern. It reduces redundant distribution and respects need-to-know boundaries.

---

## 3. Risks and Limits

1. **Exact text matching may miss near-duplicates.** Two entries that differ only by abbreviation expansion, punctuation, or trailing whitespace will not match under the current normalization. Example: `Commanding Officer, USS NIMITZ` vs `CO, USS NIMITZ`.

2. **Abbreviations or alternate command names may not match.** Navy/Marine Corps correspondence frequently uses abbreviated titles. The current validator does not perform semantic normalization.

3. **Some correspondence may intentionally list the same organization in different roles.** A letter may legitimately send action to one office while copying a related office with the same organizational name. The validator cannot distinguish intentional role duplication from accidental duplication without additional metadata.

4. **Copy-to semantics may vary by correspondence type.** Memorandums, joint letters, and endorsements may have different conventions for who receives copies. The rule is scoped to `universal` in the catalog, but real-world usage may vary.

5. **Source location in catalog may need refinement.** The current `source_location` is `Chapter 7 To / Via / Copy-to separation`, which is a narrative description, not a specific paragraph or figure citation. Any severity promotion should be preceded by source-location refinement.

6. **This should remain advisory/heuristic until evidence is stronger.** Exact duplicate detection is low-risk, but near-duplicate false negatives and intentional-duplication false positives are unmeasured. Severity promotion to warning or error requires evidence, regression fixtures, and burn-in observation.

---

## 4. Evidence Needs

### 4.1 Source Citation Refinement

- Identify the exact paragraph, figure, or example in SECNAV M-5216.5 Chapter 7 that states or implies that an addressee should not appear in both action and Copy-to lines.
- Update `source_location` from narrative to specific citation before any promotion.

### 4.2 Regression Fixture Categories

The following fixture categories are needed before any severity promotion discussion:

| # | Category | Expected Behavior |
|---|---|---|
| 1 | Copy-to duplicates To | Warning with `CCI-ROUTE-007` and rule id |
| 2 | Copy-to duplicates Via | Warning with `CCI-ROUTE-007` and rule id |
| 3 | No duplicate case | No `CCI-ROUTE-007` warning |
| 4 | Same organization with different wording | No `CCI-ROUTE-007` warning (exact match only) |
| 5 | Multiple Copy-to entries with one duplicate | Warning for duplicate entry only; other entries silent |
| 6 | To/Via list normalization stress test | Verify whitespace/case normalization works consistently |

### 4.3 Expected Output Verification

- Every fixture test should verify that the warning text contains `CCI-ROUTE-007`.
- Every fixture test should verify that the `rule_id` is present in the warning string.
- Positive-control fixtures must trigger the warning.
- Negative-control fixtures must not trigger the warning.

---

## 5. Proposed Future Implementation Path

This path is **proposed only** and requires explicit approval before any step is executed.

| Phase | Action | Approval Required |
|---|---|---|
| J.10 / K.2 | Read-only plan review of this document | Yes |
| J.11 / K.3 | Create or expand regression runner for ROUTE-007 exact duplicate detection | Yes |
| J.12 / K.4 | Evidence checkpoint: run fixtures, verify expected outputs | Yes |
| J.13 / K.5 | Evidence review: evaluate false-positive/false-negative rates | Yes |
| J.14 / K.6 | Decision: defer, continue advisory, or plan warning pilot | Yes |
| *(future)* | Only after evidence review, consider config allowlist planning | Separate approval |
| *(future)* | Warning-pilot activation only if separately approved | Separate approval |

**No step in this path may be executed without user approval.**

---

## 6. Explicit Prohibitions

The following actions are **prohibited** in Phase J.9 / Phase K.1 and remain prohibited unless separately approved in a future phase:

1. No config changes.
2. No severity changes.
3. No allowlist changes (`CCI-ROUTE-007` remains not allowlisted).
4. No error promotion.
5. No rollback of existing warning pilots.
6. No validator changes in this phase.
7. No catalog changes in this phase unless separately approved.
8. No renderer or layout changes.
9. No prompt, context, intake, UI, or command-flow changes.
10. No Phase F or Phase G command-layer changes.
11. No logs or unsanitized material committed.
12. Do not read or modify `docs/BOOTSTRAP.md`.
13. Do not modify `docs/HERMES_INSTRUCTIONS.md`.
14. Do not create fixtures or runners in this phase.

---

## 7. Decision

**Decision:** Plan `CCI-ROUTE-007` as the next controlled rule candidate for evaluation after `CCI-ROUTE-010` and `CCI-ROUTE-011`.

**Rationale:** Deterministic exact-match logic already exists in the validator; scope is narrow; ambiguity is lower than heuristic rules; evidence collection can be bounded; severity promotion remains deferred until evidence is collected.

**Status:** Planning-only. No implementation authorized.

---

## 8. Recommended Next Phase

**Phase J.10 / Phase K.2 — CCI-ROUTE-007 Candidate Plan Review**

- Read-only review of this planning document.
- Approve, defer, or reject the proposed future implementation path.
- No code changes.
- No config changes.
- Error promotion remains unauthorized.

---

End of Phase J.9 / Phase K.1 — CCI-ROUTE-007 Duplicate Copy-to Candidate Plan.
