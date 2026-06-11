# Phase K.2 — CCI-CH7-SUBJ-002 Subject Terminal Punctuation Candidate Plan

**Date:** 2026-06-10  
**Commit:** `78f59d1`  
**Suite count:** 36/36 PASS  
**Rule:** `CCI-CH7-SUBJ-002` — Subject line has no terminal punctuation  
**Status:** Planning-only — no implementation in this phase

---

## 1. Current state

| Item | Status |
|------|--------|
| Rule exists in catalog | YES — `rules_v6/CCI/cci_ch7_subject_rules.json` |
| Source text | YES — Chapter 7, paragraph 7-2.9 and Figure 7-1 |
| Validator implemented | YES — `src/cci_subject_validate.py` lines 280-284 |
| Dedicated regression runner | **NO** |
| In config allowlist | **NO** |
| Warning pilot active | **NO** |
| Error promotion | **UNAUTHORIZED** |

## 2. Why this is a good candidate

1. **Explicit source text** — Catalog `source_location` points to a specific chapter/paragraph and figure: "Chapter 7, paragraph 7-2.9 and Figure 7-1"
2. **Deterministic** — Terminal punctuation check is purely mechanical: `content.endswith((".", "?", "!"))`. No ambiguity.
3. **Narrow field scope** — Only inspects the `subject` field. No body text, no routing, no references.
4. **Low false-positive risk** — A period, question mark, or exclamation mark at the end of a military correspondence subject line is virtually never intentional.
5. **Common user-facing drafting issue** — Authors frequently add terminal punctuation out of civilian habit.
6. **Validator already implements** — No new validator logic needed; only regression coverage is missing.
7. **Bounded scope** — Applies only to `standard_letter`, `multiple_address_letter`, `endorsement`, `joint_letter` (subject-required types).

## 3. Proposed regression coverage

The future dedicated runner (`tools/run_phase_k3_subject_terminal_punctuation_regression.py`) should cover:

### Positive cases (must trigger SUBJ-002)

| # | Fixture description | Expected behavior |
|---|---------------------|-------------------|
| 1 | Subject ending with period | `errors` contains CCI-CH7-SUBJ-002 |
| 2 | Subject ending with question mark | `errors` contains CCI-CH7-SUBJ-002 |
| 3 | Subject ending with exclamation point | `errors` contains CCI-CH7-SUBJ-002 |

### Negative cases (must NOT trigger SUBJ-002)

| # | Fixture description | Expected behavior |
|---|---------------------|-------------------|
| 4 | Subject with no terminal punctuation | No SUBJ-002 error |
| 5 | Subject containing internal punctuation (e.g., "ABC/123") | No SUBJ-002 error |
| 6 | Subject with comma or semicolon at end | No SUBJ-002 error (only `.`, `?`, `!` are terminal) |
| 7 | Uppercase subject without terminal punctuation | No SUBJ-002 error |
| 8 | Lowercase/mixed-case subject without terminal punctuation | No SUBJ-002 error |
| 9 | Blank/missing subject | Handled by existing SUBJ-001; SUBJ-002 should not appear |

### Cross-rule preservation cases

| # | Fixture description | Expected behavior |
|---|---------------------|-------------------|
| 10 | Subject with terminal punctuation AND missing subject content | SUBJ-001 still triggers; SUBJ-002 triggers |
| 11 | Subject with terminal period AND likely acronym | SUBJ-004 warning still fires alongside SUBJ-002 error |

## 4. Future implementation path (not in this phase)

| Phase | Action |
|-------|--------|
| K.3 | Create dedicated runner `tools/run_phase_k3_subject_terminal_punctuation_regression.py` with inline sanitized payloads |
| K.4 | Runner implementation checkpoint |
| K.5 | Evidence review — verify all checks PASS, no false positives, no false negatives |
| K.6 | Source citation verification (already exact) |
| K.7 | Decision: keep advisory, plan warning-pilot, or close track |

## 5. Decision posture

- **This phase is planning-only.** No runner created, no fixtures committed.
- After runner passes and full 36-suite gate passes, the decision posture is:
  - **Option A:** Keep CCI-CH7-SUBJ-002 as advisory (default; no config change)
  - **Option B:** Plan warning-pilot activation in a later phase (requires explicit user approval)
  - **Option C:** Close track (if evidence shows insufficient value)
- **No warning pilot in this phase.**
- **Error promotion remains unauthorized** in all cases.

## 6. Explicit prohibitions

| Action | Authorized |
|--------|------------|
| Create runner in this phase | **NO** |
| Create fixtures in this phase | **NO** |
| Modify config | **NO** |
| Modify severity | **NO** |
| Add to allowlist | **NO** |
| Promote to error | **NO** |
| Modify validator | **NO** |
| Modify catalog | **NO** |
| Modify renderer/layout | **NO** |
| Modify prompt/context/intake/UI/command-flow | **NO** |
| Modify Phase F/G command layer | **NO** |
| Commit logs or unsanitized material | **NO** |
| Read or modify `docs/BOOTSTRAP.md` | **NO** |
| Modify `docs/HERMES_INSTRUCTIONS.md` | **NO** |

## 7. Files touched in this phase

| File | Action |
|------|--------|
| `docs/planning/phase_k2_subject_terminal_punctuation_candidate_plan.md` | **Created** |
| `docs/PROJECT_STATUS.md` | Updated |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Updated |

## 8. No files modified in this phase

- `config/cci_enforcement_config.json` — unchanged
- `rules_v6/CCI/cci_ch7_subject_rules.json` — unchanged
- `src/cci_subject_validate.py` — unchanged
- All existing regression runners — unchanged
- All fixtures — unchanged

## 9. Verdict

**APPROVE Phase K.2 candidate evaluation plan.**

CCI-CH7-SUBJ-002 is a well-sourced, deterministic, low-risk rule with existing validator implementation. The next step is creating a dedicated regression runner (Phase K.3) using inline sanitized payloads. No config, severity, allowlist, validator, catalog, renderer, layout, prompt, context, intake, UI, or command-layer changes are authorized in this phase. Error promotion remains unauthorized.

---

**Approved by:** Phase K.2 planning review  
**Recommended next phase:** Phase K.3 — CCI-CH7-SUBJ-002 Dedicated Regression Runner
