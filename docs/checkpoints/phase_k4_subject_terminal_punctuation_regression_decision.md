# Phase K.4 CCI-CH7-SUBJ-002 Regression Coverage Decision

**Date:** 2026-06-11
**Rule:** `CCI-CH7-SUBJ-002` — Subject line terminal punctuation
**Phase type:** Decision checkpoint
**Commit constraint:** No config, severity, allowlist, validator, catalog, renderer, prompt, or command-layer changes.

---

## 1. Current State

| Attribute | Value |
|-----------|-------|
| Rule ID | `CCI-CH7-SUBJ-002` |
| Catalog location | `rules_v6/CCI/cci_ch7_subject_rules.json` |
| Source citation | Chapter 7, paragraph 7-2.9; Figure 7-1 |
| Validator | `src/cci_subject_validate.py` lines 280-284 |
| Validator pre-existed K.3 | Yes |
| Dedicated runner | `tools/run_phase_k3_subject_terminal_punctuation_regression.py` |
| Runner checks | 11 (3 positive, 6 negative, 2 cross-rule preservation) |
| Runner result | **11/11 PASS** |
| Full gate result | **37 suites PASS** |
| Config allowlist | Not present |
| Effective severity | `global_default = advisory` |
| ROUTE-010 severity | `warning` (unchanged) |
| ROUTE-011 severity | `warning` (unchanged) |
| Error promotion | Unauthorized |

## 2. Decision Rationale

### Why this rule is a good candidate for future warning-pilot planning

1. **Explicit source support.** The rule is directly grounded in SECNAV M-5216.5 Chapter 7, paragraph 7-2.9 and Figure 7-1, which specify that the subject line should not end with terminal punctuation. This is stronger source authority than inferred heuristics.
2. **Deterministic check.** The validator logic is binary: does the subject line end with `.`, `?`, or `!`? This leaves little room for subjective interpretation.
3. **Low false-positive risk.** The 6 negative cases in K.3 confirm that internal punctuation, commas, semicolons, and absence of punctuation do not trigger the rule.
4. **Narrow scope.** The check is limited to terminal punctuation only; it does not attempt to police subject-line content, length, or formatting beyond the explicit catalog requirement.
5. **No validator changes required.** The existing `cci_subject_validate.py` already implements the check. K.3 only added a dedicated runner to exercise it.
6. **Regression coverage exists.** The 11-check runner provides a repeatable baseline for any future severity change.

### Risks and limits (still applicable)

1. **Only three terminal punctuation forms are checked.** Other symbols (e.g., ellipsis, em-dash) are not explicitly tested.
2. **Cross-rule interaction.** SUBJ-002 can fire alongside SUBJ-001 (blank subject) and SUBJ-007 (all caps). The K.3 cross-rule checks confirm coexistence is safe.
3. **No real-world burn-in.** Like ROUTE-007, SUBJ-002 has not been observed under a warning pilot. Burn-in evidence would be required before any allowlist activation.
4. **Subject semantics vary.** Some correspondence types (e.g., questions, exclamations) may intentionally use `?` or `!`. The catalog does not grant exceptions; this is acceptable for advisory but may need review if elevated to warning.

## 3. Evidence Summary

| Evidence | Status |
|----------|--------|
| Explicit source citation | Yes — 7-2.9 and Figure 7-1 |
| Validator implementation | Pre-existing; unchanged in K.3 |
| Dedicated regression runner | Created in K.3; 11/11 PASS |
| Positive trigger cases | 3/3 PASS |
| Negative non-trigger cases | 6/6 PASS |
| Cross-rule preservation | 2/2 PASS |
| Full suite gate | 37/37 PASS |
| Config changes | None |
| Severity changes | None |
| Allowlist changes | None |

## 4. Decision

**Verdict: APPROVE regression coverage. Recommend proceeding to a future warning-pilot plan for `CCI-CH7-SUBJ-002`.**

- The rule has explicit source support and deterministic behavior.
- Regression coverage is adequate and passing.
- No code, config, or catalog changes are needed to reach this decision.
- **Warning pilot is NOT activated in this phase.**
- **Allowlist entry is NOT added in this phase.**
- **Severity remains advisory via `global_default`.**
- Error promotion remains unauthorized and requires separate future phase and explicit user approval.

## 5. Explicit Prohibitions (This Phase)

- No config changes.
- No severity changes.
- No allowlist changes.
- No error promotion.
- No validator logic changes.
- No catalog changes.
- No renderer/layout changes.
- No prompt/context/intake/UI/command-flow changes.
- No Phase F/G command-layer changes.
- No fixture or runner modifications.
- No logs or unsanitized material committed.
- Do not read or modify `docs/BOOTSTRAP.md`.
- Do not modify `docs/HERMES_INSTRUCTIONS.md`.

## 6. Recommended Next Phase

**Phase K.5 — CCI-CH7-SUBJ-002 Warning Pilot Plan**

Purpose: Planning-only document evaluating whether `CCI-CH7-SUBJ-002` should enter a controlled warning pilot, including risks, rollback path, burn-in requirements, and explicit prohibitions.

---

**Decision authority:** Hermes Agent recommendation; user approval required before any K.5 planning.
