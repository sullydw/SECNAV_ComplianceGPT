# Phase K.5 CCI-CH7-SUBJ-002 Warning Pilot Plan

**Date:** 2026-06-11
**Rule:** `CCI-CH7-SUBJ-002` — Subject line terminal punctuation
**Phase type:** Planning-only
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
| Warning pilot active | No |

## 2. Proposed Future Activation

If approved in a future phase (K.6 or later), the activation is **config-only**:

1. Add `CCI-CH7-SUBJ-002` to the `allowlist` in `config/cci_enforcement_config.json`.
2. Set `CCI-CH7-SUBJ-002.effective_severity` to `warning`.

No validator, catalog, renderer, prompt, command-layer, fixture, or runner changes are required.

## 3. Why Warning Pilot Is Reasonable

1. **Explicit source text.** The rule is grounded in SECNAV M-5216.5 Chapter 7, paragraph 7-2.9 and Figure 7-1, which state that the subject line should not end with terminal punctuation. This is direct source authority, not an inferred heuristic.
2. **Deterministic check.** The validator logic is exact: does the subject line end with `.`, `?`, or `!`? No subjective interpretation.
3. **Narrow field scope.** The check touches only the subject line; it does not affect routing, addressees, enclosures, references, or body text.
4. **Low false-positive risk.** The 6 negative cases in K.3 confirm internal punctuation, commas, semicolons, and absence of punctuation do not trigger.
5. **Easy rollback.** A config-only change can be reverted by removing the allowlist entry or setting severity back to `advisory`.
6. **Existing precedent.** ROUTE-010 and ROUTE-011 warning pilots were activated with the same config-only pattern and have remained stable.

## 4. Risks

1. **Generated subject continuation/wrapping.** If the model generates a multi-line subject or continuation text that happens to end with punctuation on the first line, the validator may fire on the wrapped fragment. The validator operates on the subject field only; this risk exists today in advisory mode and is acceptable for warning.
2. **Abbreviations ending with periods.** Acronyms or abbreviations (e.g., "U.S.", "N.A.T.O.") at the end of a subject line would correctly trigger SUBJ-002. This is technically correct per the catalog but may surprise operators. The existing SUBJ-007 (all caps) may also fire, creating dual warnings. Acceptable for warning pilot.
3. **Existing examples/tests with terminal punctuation.** Any existing fixtures, examples, or documentation that intentionally show terminal punctuation in subjects would need expectation updates if they are wired to the validator. No such fixtures are known, but this risk should be verified before activation.
4. **Cross-rule interaction with SUBJ-001 and SUBJ-007.** A subject that is blank (SUBJ-001) or all caps (SUBJ-007) can coexist with SUBJ-002. The K.3 cross-rule checks confirm this is safe.

## 5. Required Activation Checks

Before any future config change, the following must pass:

| Check | Runner | Expected Result |
|-------|--------|----------------|
| SUBJ-002 positive triggers | K.3 runner | 11/11 PASS |
| Subject/acronym validator | H.2 runner | 12/12 PASS |
| Config regression | H.13 runner | 27/27 PASS |
| Full gate | All 37 suites | 37/37 PASS |

Any failure blocks activation.

## 6. Rollback Path

If the warning pilot causes unacceptable behavior:

1. Remove `CCI-CH7-SUBJ-002` from the allowlist, OR set `effective_severity` back to `advisory`.
2. Re-run K.3, H.2, H.13, and full 37-suite gate.
3. All must PASS before rollback is considered complete.
4. Document rollback decision in a checkpoint file.

## 7. Explicit Prohibitions (This Phase)

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

## 8. Recommended Next Phase

**Phase K.6 — CCI-CH7-SUBJ-002 Warning Pilot Activation**

Purpose: Execute the config-only activation if user approves this plan.

Requirements before K.6:
- User explicit approval of this K.5 plan.
- Full 37-suite gate PASS at time of activation.
- Activation checks listed in Section 5 must be re-verified immediately before the commit.

---

**Planning authority:** Hermes Agent recommendation; user approval required before any K.6 activation.
