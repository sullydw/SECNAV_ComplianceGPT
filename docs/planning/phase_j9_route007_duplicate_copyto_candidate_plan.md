# Phase J.9 / Phase K.1 — CCI-ROUTE-007 Duplicate Copy-to Candidate Plan

## Metadata
- **Phase:** J.9 / K.1
- **Date:** 2026-06-10
- **Type:** Planning-only — no config changes, no severity changes, no code changes
- **Rule candidate:** `CCI-ROUTE-007`
- **Purpose:** Evaluate whether `CCI-ROUTE-007` should become the next controlled rule candidate after `CCI-ROUTE-010` and `CCI-ROUTE-011`

---

## 1. Current State

| Item | Value |
|------|-------|
| `CCI-ROUTE-007` catalog status | Exists in `rules_v6/CCI/cci_ch2_routing_rules.json` |
| Catalog `enforcement` | `heuristic_warning` |
| Catalog `severity` | `warning` |
| Catalog `validator` | `cci_routing` |
| Config allowlist | **NOT present** in `config/cci_enforcement_config.json` |
| Config `global_default` | `advisory` |
| `CCI-ROUTE-010.effective_severity` | `warning` (active warning pilot) |
| `CCI-ROUTE-011.effective_severity` | `warning` (active warning pilot) |
| Error promotion authorized | **No** |
| Regression baseline | 35 suites |

### Validator behavior today

`src/cci_routing_validate.py` already implements exact duplicate detection in `_check_copy_to()` (lines 216–235):

- Normalizes Copy-to, To, and Via entries via `_normalize_for_match()` (lowercase + whitespace collapse)
- Iterates each Copy-to entry
- Compares normalized text against each normalized To entry
- Compares normalized text against each normalized Via entry
- Emits `CCI-ROUTE-007` warning if any exact match found
- Only the first match per Copy-to entry is reported (break after first hit)

This is a deterministic exact-text match, not fuzzy or semantic.

---

## 2. Why This Is a Good Next Candidate

1. **Exact duplicate matching is deterministic.** The validator uses strict normalized string equality. There is no ambiguity in whether two strings match.
2. **Limited scope.** The rule only inspects Copy-to versus To/Via. It does not involve body text, subject lines, references, enclosures, or signatures.
3. **Smaller ambiguity than vague routing rules.** Unlike ROUTE-004 (vague Via phrases) or ROUTE-005/006 (excessive/vague Copy-to), duplicate detection has a binary outcome: match or no match.
4. **Existing validator logic already present.** No new validator function needed. The check already runs on every payload. A regression runner can validate the existing behavior.
5. **Likely user-facing value.** Preventing an addressee from appearing as both an action recipient (To/Via) and a copy recipient is a concrete data-quality improvement with low false-positive risk for exact matches.
6. **Precedent exists.** ROUTE-010 and ROUTE-011 followed the same path: catalog rule → config allowlist → warning pilot. ROUTE-007 can reuse that proven workflow.

---

## 3. Risks and Limits

| Risk | Description | Mitigation |
|------|-------------|------------|
| Near-duplicate false negatives | Abbreviations, alternate command names, or formatting differences (e.g., "COMNAVAIRFOR" vs "Commander, Naval Air Forces") will not match | Accept for initial phase; exact match is the documented scope |
| Intentional dual-role listings | Some correspondence may legitimately list the same organization in different roles (e.g., action and info) | Document that exact match triggers a review warning, not a hard block; user decides |
| Copy-to semantics vary by type | MFRs, endorsements, and joint letters may have different Copy-to conventions | Apply `applies_to` filter from catalog; do not expand scope without evidence |
| Source citation needs refinement | Current catalog `source_location` is "Chapter 7 To / Via / Copy-to separation" — needs a more specific paragraph or figure reference | Required before any severity promotion; acceptable for planning |
| No config allowlist entry | Cannot be promoted to warning or error without config changes | Config planning is a future phase, not this one |
| Single-match break behavior | Only the first duplicate per Copy-to entry is reported; multiple duplicates may be under-reported | Document in regression expectations; acceptable for initial phase |

**Overall risk assessment:** Low to moderate. The exact-match behavior is safe for a warning-pilot candidate, but the rule should remain advisory/heuristic until evidence is stronger and source citation is refined.

---

## 4. Evidence Needs

Before any config change or warning-pilot activation, the following evidence should be collected:

### 4.1 Source citation refinement
- Identify the specific SECNAV M-5216.5 paragraph, figure, or section that prohibits duplicate action/copy addressees
- Add `source_quote` to catalog entry (currently missing)
- Add `manual_chapter`, `manual_section`, `page_or_figure` if available

### 4.2 Regression fixtures

| Fixture category | Description | Expected behavior |
|------------------|-------------|-------------------|
| Positive — Copy-to duplicates To | One Copy-to entry exactly matches a To entry | `CCI-ROUTE-007` warning emitted |
| Positive — Copy-to duplicates Via | One Copy-to entry exactly matches a Via entry | `CCI-ROUTE-007` warning emitted |
| Positive — multiple duplicates | Multiple Copy-to entries each duplicate different To/Via entries | Multiple `CCI-ROUTE-007` warnings (one per Copy-to entry) |
| Negative — no overlap | Copy-to, To, and Via are all distinct | No `CCI-ROUTE-007` warning |
| Negative — same org, different wording | "COMNAVAIRFOR" in To, "Commander, Naval Air Forces" in Copy-to | No match (exact-match only); no warning |
| Negative — case difference | To: "Commanding Officer", Copy-to: "commanding officer" | Match after normalization; warning emitted (document as expected) |
| Negative — whitespace difference | To: "CO,  NMCB-1", Copy-to: "CO, NMCB-1" | Match after whitespace collapse; warning emitted |
| Edge — empty Copy-to | Copy-to is empty or missing | No warning (guard already exists) |
| Edge — empty To/Via | To and Via missing, Copy-to present | No warning (no action addressees to duplicate) |
| Edge — single Via numbered | Via has one numbered entry, Copy-to duplicates it | Warning emitted (Via normalization works) |

### 4.3 Expected output verification
- Warning text must contain `CCI-ROUTE-007`
- Warning text must identify the duplicate Copy-to index and entry
- Warning text must identify the matching To or Via entry
- No errors emitted (rule is advisory/heuristic at this stage)

---

## 5. Proposed Future Implementation Path

This plan does not authorize any implementation. It defines the ordered future phases if approved:

| Phase | Action | Approval required |
|-------|--------|-------------------|
| **J.10 / K.2** | Read-only plan review | User or designated reviewer |
| **J.11 / K.3** | Create or expand regression runner for ROUTE-007 exact duplicate detection | User approval after plan review |
| **J.12 / K.4** | Evidence checkpoint — run regression fixtures, collect results | Automatic after runner creation |
| **J.13 / K.5** | Evidence review — evaluate false positives, false negatives, decide if rule is stable | User or designated reviewer |
| **J.14 / K.6** | If evidence is clean: config allowlist planning document | User approval |
| **J.15 / K.7** | If plan approved: add `CCI-ROUTE-007` to `config/cci_enforcement_config.json` with `effective_severity: warning` | User approval |
| **J.16 / K.8** | Warning pilot activation checkpoint | Follow ROUTE-010/011 precedent |
| **J.17+ / K.9+** | Burn-in checkpoints, review, decision | Same cadence as ROUTE-010/011 |

**Critical gate:** No warning-pilot activation unless separately approved. No config change unless separately approved. No severity change unless separately approved.

---

## 6. Explicit Prohibitions

The following are **not authorized** in this planning phase:

- No config changes
- No severity changes
- No allowlist changes
- No error promotion
- No rollback of any existing rule
- No validator logic changes
- No catalog changes (except source citation refinement, which requires separate approval)
- No renderer/layout changes
- No prompt/context/intake/UI/command-flow changes
- No Phase F/G command-layer changes
- No fixture or runner creation (requires J.10/K.2 approval)
- No logs or unsanitized material committed
- Do not read or modify `docs/BOOTSTRAP.md`
- Do not modify `docs/HERMES_INSTRUCTIONS.md`

---

## 7. Comparison to Prior Candidates

| Aspect | ROUTE-011 (From-line) | ROUTE-010 (Office-code) | ROUTE-007 (Duplicate Copy-to) |
|--------|----------------------|------------------------|------------------------------|
| Catalog enforcement | `deterministic` | `deterministic` | `heuristic_warning` |
| Catalog severity | `error` | `error` | `warning` |
| Validator logic | Added in H.9 | Added in H.4 | Already exists |
| Config allowlist | Yes | Yes | **No** |
| Source quote | Exact | Exact | **Missing** |
| Scope | Standard letter only | Universal | Universal |
| Ambiguity | Low (binary: has From or not) | Low (binary: Code prefix correct or not) | Low (binary: exact match or not) |
| Warning pilot status | Active, paused | Active, paused | **Not started** |

ROUTE-007 is less mature than ROUTE-010/011 because it lacks an exact source quote and is not yet in the config allowlist. These gaps must be closed before any warning-pilot discussion.

---

## 8. Recommended Next Phase

**Phase J.10 / Phase K.2 — CCI-ROUTE-007 Candidate Plan Review**

Purpose: Review this plan, approve or reject it, and decide whether to proceed to regression runner creation (J.11/K.3) or defer ROUTE-007 in favor of another candidate.

---

## 9. Constraints Preserved

- No config change in this planning phase
- No severity change in this planning phase
- No error promotion
- No rollback
- No validator changes
- No catalog changes without separate approval
- No renderer/layout changes
- No prompt/context/intake/UI/command-flow changes
- No Phase F/G command-layer changes
- No logs or unsanitized material committed
- `docs/BOOTSTRAP.md` and `docs/HERMES_INSTRUCTIONS.md` untouched
