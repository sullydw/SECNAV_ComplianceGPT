# Phase H.2 / Phase I.1 Subject-Line Acronym Validator Enforcement Plan

**Status:** Planning-only; not approved for implementation.  
**Scope:** Decide whether and how to add validator enforcement for the already-cataloged subject-line acronym rule `CCI-CH7-SUBJ-006`. No code changes under this plan without separate user approval.  
**Rule:** `CCI-CH7-SUBJ-006` — "In correspondence, do not use acronyms in the subject line."  
**Source:** SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General  
**Catalog file:** `rules_v6/CCI/cci_ch7_subject_rules.json`  
**Baseline:** `6298dab` — `CCI: Add public mark implemented wrapper`  
**Branch:** `main`

---

## 1. Is Validator Enforcement Appropriate for This Rule?

**Yes, but only as an elevated warning (advisory) in the first implementation phase.**

The SECNAV M-5216.5 rule is explicit: "In correspondence, do not use acronyms in the subject line." This is a deterministic textual constraint that can be checked at validation time. However, the rule interacts with another SECNAV requirement (subjects must be in all caps), which makes acronym detection in subjects inherently ambiguous. For this reason, the enforcement should not be promoted to a hard error without extensive false-positive testing.

**Recommended approach:** Elevate the existing `CCI-CH7-SUBJ-004` warning from a simple heuristic to a more precise advisory, and consider a subject-specific acronym list. Do not promote to `error` until false-positive rate is measured on synthetic and, later, representative fixtures.

---

## 2. Avoiding False Positives in Acronym Detection

### Current False-Positive Risk

The existing `_check_acronyms()` in `cci_subject_validate.py` suppresses acronym detection entirely when `text.isupper()` because, in all-caps text, every word looks like an acronym. This suppression prevents massive false positives on subjects like `STANDARD LETTER PHASE 1 AUDIT AND VALIDATION`.

**Critical consequence:** Because compliant SECNAV subjects are required to be all-caps, the existing `isupper()` guard means `SUBJ-004` currently fires only on mixed-case (already invalid) subjects. A prohibited-acronym list placed inside the existing `_check_acronyms()` would also never be consulted for all-caps subjects unless the guard is relaxed.

### Chosen Approach: Relax the `isupper()` Guard for Curated Prohibited-List Scanning Only

The `isupper()` guard will be relaxed in Phase H.2 so that **all-caps subjects are scanned against a curated prohibited-acronym list**, but the relaxed scan will **not** use the generic `\b[A-Z]{2,}\b` regex that would flag every word.

### Recommended Mitigations (Design-Only, Not Implemented Here)

1. **Relax `isupper()` guard for prohibited list only** — When `text.isupper()` is true, skip the generic regex scan but still scan token-by-token against the `PROHIBITED_SUBJECT_ACRONYMS` list. Normal all-caps words (e.g., `UPDATE`, `POLICY`, `MEETING`) that are not on the prohibited list are not flagged.
2. **Use a subject-specific prohibited-acronym list** — Instead of a generic regex, the only signal for all-caps subjects is exact membership in `PROHIBITED_SUBJECT_ACRONYMS`.
3. **Retain generic regex only for mixed-case subjects** — When `text.isupper()` is false, the existing generic `_ACRONYM_RE` scan still runs as today (producing `SUBJ-004`).
4. **Length filter** — Exclude 2-letter tokens from the prohibited list (too ambiguous). Minimum prohibited token length: 3 characters.
5. **Approved-term tolerance** — Maintain the existing `APPROVED_ACRONYMS` set. Approved acronyms are never treated as prohibited, even if they appear on both lists by mistake.

### Initial Prohibited-Subject-Acronym List (Pre-Implementation Deliverable)

The following initial list is proposed for Phase H.2. Each entry must carry provenance before any implementation commit. Subsequent additions require separate review.

| Prohibited acronym | Rationale / Source |
|---|---|
| `POC` | Phase H.1 pilot correction: `REQUEST FOR POC UPDATE` -> `REQUEST FOR POINT OF CONTACT UPDATE`. SECNAV M-5216.5 Ch7 para 9 prohibits acronyms in subjects; `POC` is a common abbreviation for Point of Contact. |
| `UIC` | Common Navy administrative acronym for Unit Identification Code. Explictly prohibited in subject lines per Ch7 para 9 guidance. |
| `OIC` | Common abbreviation for Officer in Charge. Subject-line usage is non-compliant per Ch7 para 9. |

**Note:** This list is intentionally small. Additional terms (e.g., `SOP`, `TAD`, `IAW`, `FYSA`, `WRT`) may be added in future phases only after provenance review and false-positive assessment. No command-specific or local-only abbreviations may be added without SECNAV manual citation.

**Conclusion:** False-positive avoidance is the primary reason enforcement remains advisory in Phase H.2 / Phase I.1. The curated-list approach limits false positives to exact known-bad tokens.

---

## 3. Reuse Existing Acronym Validator or Add Subject-Specific Logic?

**Recommendation: Do NOT reuse `cci_acronym_validate.py` directly. Add subject-specific logic to `cci_subject_validate.py` instead.**

### Why Reuse Is Unsafe

- `cci_acronym_validate.py` is scoped to **body text only** (`body`/`body_paragraphs`). Its docstring explicitly says: "Does NOT inspect subject, reference titles, enclosure titles, From/To/Via lines, addresses, or signatures."
- The body validator uses first-use-definition logic (`"Full Name (ACR)"`) that is meaningless in subject lines, where there is no prior text for definition.
- The body validator's `APPROVED_ACRONYMS` list is duplicated in `cci_subject_validate.py` already, but the two contexts have different tolerance levels.

### Why Subject-Specific Logic Is Better

- The subject validator already has `_check_acronyms()`. Enhancing this function is the correct, narrow scope.
- Subjects are short (typically 5–15 words), so false positives are more destructive than in body text.
- Subjects are all-caps, requiring a different heuristic than body text.

**Implementation boundary if later approved:** Modify only `src/cci_subject_validate.py`. Do not modify `src/cci_acronym_validate.py`.

---

## 4. Distinguishing Acronyms from Normal All-Caps Subject Text

### Problem Statement

SECNAV subjects are required to be all-caps. In all-caps text, `UPDATE`, `POLICY`, `MEETING`, and `ACRONYM` all match `\b[A-Z]{2,}\b`. There is no case differentiation.

**Current behavior:** Because the subject validator requires all-caps (SUBJ-001), the existing `_check_acronyms()` returns `[]` immediately when `text.isupper()`. This means `CCI-CH7-SUBJ-004` currently fires only on mixed-case (already invalid) subjects.

### Chosen Design for Phase H.2

Approach **A** from Section 2:

- When the subject is all-caps (`text.isupper()` is true), skip the generic regex entirely.
- Instead, tokenize the subject and scan each token against the curated `PROHIBITED_SUBJECT_ACRONYMS` list only.
- Normal all-caps words like `UPDATE`, `POLICY`, `MEETING` that are not on the prohibited list pass without advisory.
- Mixed-case subjects continue to receive the existing `SUBJ-004` generic acronym warning as today.

| Approach | Rationale | Phase H.2 Decision |
|---|---|---|
| Relax `isupper()` guard for curated prohibited-list scan | Normal all-caps words pass; only exact prohibited tokens flagged | **Adopted (A)** |
| Keep generic `\b[A-Z]{2,}\b` for all-caps subjects | Would flag every word; false-positive rate unacceptable | **Rejected** |
| Limit enhancement to mixed-case subjects only | Would not help any compliant (all-caps) subjects; misses the point | **Rejected (B)** |
| Exclude `_COMMON_UPPER_WORDS` | Still present for mixed-case fallback; not needed for exact prohibited-list scan | **Retain for mixed-case** |
| Exclude `_LABEL_WORDS` | Still present for mixed-case fallback; not needed for exact prohibited-list scan | **Retain for mixed-case** |
| Minimum token length >= 3 | Reduces ambiguity; 2-letter tokens are too noisy | **Enforced** |

**Key insight:** The signal for all-caps subjects is not "does this token look like an acronym?" but "is this token on the prohibited list?" The only way to avoid massive false positives on all-caps subjects is to abandon generic regex scanning for them and use exact membership only.

---

## 5. Approved/Common Terms Treatment

### Current Approved Acronyms (Both Validators Share This List)

`SECNAV`, `DON`, `USN`, `USMC`, `DoD`, `NATO`, `SSIC`, `MCO`, `OPNAV`, `NAVMC`, `CNO`, `CMC`, `FOIA`, `PII`, `CUI`, `FOUO`

### New Constant: `PROHIBITED_SUBJECT_ACRONYMS`

Phase H.2 introduces a new frozenset constant in `cci_subject_validate.py`:

```python
PROHIBITED_SUBJECT_ACRONYMS = frozenset([
    "POC",  # Phase H.1 pilot correction; SECNAV M-5216.5 Ch7 para 9
    "UIC",  # Unit Identification Code; prohibited in subject lines per Ch7 para 9
    "OIC",  # Officer in Charge; prohibited in subject lines per Ch7 para 9
])
```

Minimum token length: 3 characters. No 2-letter tokens.

### Recommendations

1. **Approved acronyms are never treated as prohibited** — The `APPROVED_ACRONYMS` set takes precedence. Any token appearing in both `APPROVED_ACRONYMS` and `PROHIBITED_SUBJECT_ACRONYMS` is treated as approved (not prohibited). This prevents accidental conflicts.
2. **In subjects, approved acronyms may still generate a `SUBJ-004` warning** — The existing `SUBJ-004` heuristic on mixed-case subjects continues unchanged. Approved acronyms on the prohibited list in an all-caps subject are permitted.
3. **Document the prohibited list provenance** — Each entry in `PROHIBITED_SUBJECT_ACRONYMS` must cite the manual section or correction record that justifies its inclusion.
4. **Future additions require review** — Any term not in the initial list requires a new planning/update cycle. The list must not be expanded ad-hoc during implementation.

---

## 6. Feature Flagging

### Decision: YES — A lightweight opt-in feature flag is required if this rule is ever promoted to `error`.

### Rationale

- The `isupper()` suppression exists for a reason. Removing it changes behavior for every subject, not just acronym-containing ones.
- Even a prohibited-acronym-list approach could produce unexpected results on real user data that are not captured by synthetic fixtures.
- The Phase H.1 checkpoint explicitly states: "If there is any false-positive risk, wrap the new validator check in an `if pilot_rule_enabled:` guard or equivalent opt-in mechanism."

### Recommended Flag Design (Future Implementation Only)

- Introduce a config flag in the validator or in `rules_v6/CCI/cci_context_schema.json`:
  - `subject_acronym_enforcement: "advisory" | "error" | "disabled"`
  - Default: `"advisory"` for Phase H.2 / Phase I.1.
- If set to `"error"`, the validator produces `error` (not `warning`) for detected acronyms.
- If set to `"disabled"`, the check is skipped entirely.
- The flag must NOT be read from approved promotion logs or local command profiles. It should be a code-level or schema-level config, not a user-level setting.

**Phase H.2 / Phase I.1 scope:** The planning document should require a feature flag for any `error`-level implementation, but the first implementation may remain advisory without a flag if it does not change exit status.

---

## 7. Warning vs. Advisory vs. Error

### Recommended Gradual Rollout

| Phase | Level | Behavior | Message code |
|---|---|---|---|
| **Current (`6298dab`)** | Warning | `CCI-CH7-SUBJ-004: likely acronyms detected in subject: ...` — does not affect PASS/FAIL; fires only on mixed-case (already invalid) subjects due to `isupper()` guard | `SUBJ-004` |
| **Phase H.2 / Phase I.1** | **Advisory** (new advisory code) | `CCI-CH7-SUBJ-007: prohibited subject-line acronym detected: <token> — SECNAV M-5216.5 Ch7 para 9` — fires on all-caps subjects containing prohibited tokens; does not affect PASS/FAIL; subject validator still exits 0 | `SUBJ-007` |
| **Future Phase (separate approval)** | Error | Affects PASS/FAIL; requires feature flag; requires broader fixture testing | `SUBJ-007` or new code |

### Message Code Decision

Phase H.2 **introduces a new advisory code `CCI-CH7-SUBJ-007`** for prohibited subject-line acronyms.

- `CCI-CH7-SUBJ-004` behavior remains **unchanged** in Phase H.2. It continues to run the generic `_ACRONYM_RE` heuristic on mixed-case subjects only.
- `CCI-CH7-SUBJ-007` is the new advisory produced by the curated `PROHIBITED_SUBJECT_ACRONYMS` scan on all-caps subjects.
- This separation means downstream consumers parsing `SUBJ-004` are unaffected.
- The new code `SUBJ-007` is reserved for the advisory level. If later promoted to error, the same code may be upgraded from advisory to error without renumbering.

**Why advisory first:** Because the all-caps ambiguity cannot be fully eliminated even with a curated prohibited list. The advisory level preserves non-blocking behavior while improving detection precision. The user or downstream system can still act on the advisory.

---

## 8. Interaction with Existing Subject-Line Validator

### Current Subject Validator Checks

1. `CCI-CH7-SUBJ-001` — Presence / all-caps / missing subject
2. `CCI-CH7-SUBJ-002` — Terminal punctuation
3. `CCI-CH7-SUBJ-003` — Duplicated / embedded `Subj:` label
4. `CCI-CH7-SUBJ-004` — Likely acronyms (warning)
5. `CCI-CH7-SUBJ-005` — Vague / short subject (warning)

### Interaction Design

- The acronym check should continue to run **after** label stripping and capitalization checks, in the same position in `validate_cci_subject()`.
- If `CCI-CH7-SUBJ-001` (missing subject) fires, the acronym check is skipped (current behavior is correct).
- The acronym check should use the **stripped** subject content (after `_SINGLE_LABEL_RE` removal), just as it does today.
- If the subject is all-caps and passes length checks, the acronym check runs with its enhanced heuristics.
- The acronym check MUST NOT re-introduce `Subj:` label detection or capitalization logic.

---

## 9. Interaction with Existing Acronym Validator

### Current Acronym Validator (`cci_acronym_validate.py`)

- Scope: body text only.
- Errors: `CCI-ACR-001` (undefined acronym in body).
- Warnings: `CCI-ACR-002` (approved acronym used without definition), `CCI-ACR-003` (defined but unused).

### Interaction Design

- **No coupling:** The subject-line acronym rule and the body acronym rule are independent. A subject with `POC` does not absolve the body from defining `POC`.
- **No shared state:** The two validators should not share mutable state or configuration files in Phase H.2 / Phase I.1. A future phase may consider a unified acronym list, but that requires separate planning.
- **Error-code uniqueness:** Any new error or warning code for subject-line acronym enforcement must not collide with `CCI-ACR-001/002/003` or `CCI-CH7-SUBJ-001/002/003/004/005`. The next available subject-line code is `CCI-CH7-SUBJ-006` (already used by the rule catalog entry) or `CCI-CH7-SUBJ-007` for a new validator message.
- **APPROVED_ACRONYMS duplication:** Both modules currently maintain an identical `APPROVED_ACRONYMS` frozenset. A future refactor could extract this to a shared constants module, but Phase H.2 / Phase I.1 must not perform broad refactors. If a change is needed, update both lists identically.

---

## 10. Required SECNAV Provenance in Validator Messages and Docstrings

### Docstring Requirement

Any modified function in `cci_subject_validate.py` must include a docstring citing:
- `SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General`
- Rule ID: `CCI-CH7-SUBJ-006`
- Approved record ID: `agr_20260604_b69c92d9` (the Phase H.1 pilot record)
- Implementation target: `validator_update` (if this plan is later approved)

### Message Requirement

Any new warning or error message should include the rule ID:

```
CCI-CH7-SUBJ-007: subject-line acronym detected: <token> — SECNAV M-5216.5 Ch7 para 9
```

Or, if reusing the existing code:

```
CCI-CH7-SUBJ-004: likely acronyms detected in subject: <token_list> (CCI-CH7-SUBJ-006)
```

### Catalog Requirement

The rule catalog entry `CCI-CH7-SUBJ-006` already exists in `rules_v6/CCI/cci_ch7_subject_rules.json`. When validator enforcement is added, update the catalog entry with:
- `validator_status`: `"implemented"` (or `"pending"` during the advisory phase)
- `validator_implementation_commit`: `<commit_hash>`
- `enforcement_level`: `"advisory"` or `"error"`

---

## 11. Required Targeted Regression Runner and Minimum Checks

### Runner Location

`tools/run_pilot_subject_acronym_validator_regression.py`

### Minimum Checks (10+)

| Check | Category | Description |
|---|---|---|
| 1 | Positive | Subject with known prohibited acronym (e.g., `POC`) triggers advisory. |
| 2 | Positive | Subject with known prohibited acronym (e.g., `UIC`) triggers advisory. |
| 3 | Positive | Subject with mixed-case known acronym (`Poc` in non-all-caps subject) triggers advisory. |
| 4 | Negative | Subject with only common all-caps words (`STANDARD LETTER...`) passes without advisory. |
| 5 | Negative | Subject with approved acronym (`SECNAV`) passes or triggers only approved-level warning. |
| 6 | Negative | Subject with no acronyms passes cleanly. |
| 7 | Edge | Empty subject (after label strip) — should fail on presence, not reach acronym check. |
| 8 | Edge | Single-word subject (`UPDATE`) — should pass or trigger short-subject warning, not acronym error. |
| 9 | Regression insulation | Existing `audit_cci_subject_valid.json` still passes. |
| 10 | Regression insulation | Existing `audit_cci_subject_invalid.json` still fails on non-acronym reasons. |
| 11 | Regression insulation | Existing `audit_cci_subject_warning.json` still passes with expected warnings. |
| 12 | Interaction | Body acronym validator behavior unchanged when subject has acronyms. |

### Fixture Requirements

- All fixtures must be synthetic.
- No real command/user data, contact information, real names, or real session data.
- All fixtures must be committed to `examples/` if needed.

---

## 12. Full 25-Suite Regression Requirement Before Commit

Before any Phase H.2 / Phase I.1 implementation commit, the full regression gate must pass:

1. `run_correction_implementation_regression.py` — 45 checks.
2. `run_correction_nl_command_regression.py`
3. `run_correction_command_regression.py`
4. `run_correction_review_regression.py`
5. `run_correction_pending_regression.py`
6. `run_correction_profile_promotion_regression.py`
7. `run_correction_classify_regression.py`
8. `run_intake_regression.py`
9. `run_correction_regression.py`
10. `run_correction_session_regression.py`
11. `run_profile_regression.py`
12. `run_cci_audit_regression.py`
13. `run_context_schema_regression.py`
14. `run_cci_subject_regression.py`
15. `run_cci_ref_encl_regression.py`
16. `run_cci_acronym_regression.py`
17. `run_cci_date_time_regression.py`
18. `run_cci_personnel_regression.py`
19. `run_cci_poc_regression.py`
20. `run_cci_routing_regression.py`
21. `run_c7_phase1_regression.py`
22. `run_c8_regression.py`
23. `run_c9_regression.py`
24. `run_c10_regression.py`
25. `run_pilot_subject_acronym_validator_regression.py` (new)

**Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for C7–C10 suites.**

All 25 must PASS. Any failure blocks the commit.

---

## 13. Rollback Plan

### Pre-Implementation Rollback Strategy

Document the exact commands before writing code:

```
git revert <implementation_commit_hash>
```

Or, manual restore:

```
git checkout HEAD -- src/cci_subject_validate.py
```

After rollback, verify:
- `run_cci_subject_regression.py` still passes (3/3).
- `run_cci_acronym_regression.py` still passes (3/3).
- Full 24-suite gate still passes.
- The rule catalog entry `CCI-CH7-SUBJ-006` in `rules_v6/CCI/cci_ch7_subject_rules.json` remains untouched (it was added in Phase H.1).

### Rollback Triggers

- Any subject regression fails after the change.
- Any acronym regression fails due to unintended coupling.
- Any C7-C10 layout regression fails (even though the change should not affect layout).
- New targeted runner produces false positives on obviously synthetic valid fixtures.
- **False negative on targeted runner:** The new runner fails to catch a known prohibited acronym (e.g., `POC` in `REQUEST FOR POC UPDATE` in an all-caps subject) after implementation.
- Any existing `SUBJ-004` behavior changes unexpectedly (e.g., new output on previously passing fixtures).

---

## 14. Files That May Be Modified in a Future Implementation

If Phase H.2 / Phase I.1 is approved for implementation, the following files may be modified:

1. **`src/cci_subject_validate.py`**
   - Enhanced `_check_acronyms()` function.
   - Updated `APPROVED_ACRONYMS` or addition of `SUBJECT_APPROVED_ACRONYMS`.
   - Updated docstrings with SECNAV provenance.
   - Potential new error code `CCI-CH7-SUBJ-007`.

2. **`tools/run_pilot_subject_acronym_validator_regression.py`** (new file)
   - Minimum 12 checks per above.

3. **`examples/audit_cci_subject_acronym_*.json`** (new fixtures)
   - Synthetic fixtures for positive, negative, and edge cases.

4. **`rules_v6/CCI/cci_ch7_subject_rules.json`** (metadata update only)
   - Update `CCI-CH7-SUBJ-006` with `validator_status` and `enforcement_level` fields.
   - No rule text change.

5. **`docs/planning/phase_h2_subject_acronym_validator_enforcement_plan.md`**
   - This file itself may receive minor updates if the plan is revised.

---

## 15. Files That Must Not Be Modified

The following files must remain untouched in any Phase H.2 / Phase I.1 implementation:

1. `src/pdf_v6_render.py` — no renderer changes.
2. `src/body_v6_validate.py` — no body validation changes.
3. `docs/layout_profiles/` — no layout profile changes.
4. `src/correction_commands.py` — no Phase F command-layer changes.
5. `src/correction_nl_commands.py` — no Phase G NL command changes.
6. `src/correction_implementation_planner.py` — no planner changes unless fixing a planner bug.
7. `src/correction_review.py` — no review logic changes.
8. `src/correction_pending_log.py` — no pending log changes.
9. `src/correction_promote.py` — no promotion logic changes.
10. `corrections/approved_rule_promotions.json` — must remain local-only, uncommitted.
11. `corrections/pending_corrections.jsonl` — must remain local-only, uncommitted.
12. Any real user session JSONL files.

---

## 16. What Phase H.2 / Phase I.1 Must NOT Do

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **No renderer/layout changes** | Subject-line acronym detection is a content validation concern, not a spatial one. |
| 2 | **No broad validator rewrites** | Only `_check_acronyms()` and related constants in `cci_subject_validate.py` may change. |
| 3 | **No automatic enforcement from approved logs** | Approved records do not become active validator rules without explicit human implementation, merge, and status transition. |
| 4 | **No AI-only implementation** | AI may assist drafting but cannot claim, verify, approve, or sign off on validator logic. |
| 5 | **No prompt-contract runtime changes** | This is a deterministic validator update, not a prompt or drafting guide update. |
| 6 | **No Phase F/G command-layer changes** | New commands or NL intents require their own planning phase. |
| 7 | **No approved/pending logs committed** | Correction logs remain local-only and gitignored. |
| 8 | **No real command/user data committed** | All test fixtures must be synthetic. |
| 9 | **No background automation** | No cron jobs, watchers, or CI triggers may update validators automatically. |
| 10 | **No multi-record batch implementation** | Phase H.2 / Phase I.1 is one rule (`CCI-CH7-SUBJ-006`) only. |
| 11 | **No combined implementation and docs-handoff commit** | Implementation and checkpoint documentation must be separate commits. |
| 12 | **No deletion of existing `CCI-CH7-SUBJ-004`** | Existing behavior must be preserved or gracefully elevated, not removed. |
| 13 | **No change to body acronym validator** | `cci_acronym_validate.py` scope is body text; subject-line concerns belong in `cci_subject_validate.py`. |

---

## 17. Recommended Decisions (Summary)

| Question | Recommendation |
|---|---|
| **Implementation target** | `validator_update` (narrow enhancement to `cci_subject_validate.py`) |
| **Enforcement level** | **Advisory** (non-blocking) for Phase H.2 / Phase I.1 via new code `CCI-CH7-SUBJ-007`. Error deferred to future phase with separate approval. |
| **Feature flag** | **Not required for advisory level**, but a lightweight `subject_acronym_enforcement` config flag must be designed and documented so it can be activated if the level is later promoted to `error`. |
| **Message code** | **New code `CCI-CH7-SUBJ-007`** for prohibited subject-line acronyms. `CCI-CH7-SUBJ-004` behavior remains unchanged. |
| **isupper() guard** | **Relaxed for prohibited-list scan only.** All-caps subjects are scanned against `PROHIBITED_SUBJECT_ACRONYMS` by exact token match. Generic `_ACRONYM_RE` remains suppressed for all-caps subjects. |
| **Regression coverage** | New targeted runner with **minimum 12 checks** (3 positive, 3 negative, 2 edge, 4 regression insulation). Full **25-suite gate** must pass before commit. |
| **Open questions needing approval** | See Section 18 below. |

---

## 18. Open Questions Needing Approval

1. **Should Phase H.2 / Phase I.1 implement the advisory enhancement, or remain planning-only?**
   This plan is ready for review but must be explicitly approved before any code is written.

2. **What acronyms should be on the prohibited-subject list?**
   The current `APPROVED_ACRONYMS` list identifies tolerated terms. A prohibited list (e.g., `POC`, `OIC`, `CO`, `XO`, `SOP`, `TAD`, `IAW`, `FYSA`, `WRT`) must be curated from SECNAV M-5216.5 examples, common Navy usage, and known false-positive risk.

3. **Should the `isupper()` suppression be relaxed partially?**
   **Resolved in Sections 2 and 4:** The refined plan explicitly adopts Approach A. The `isupper()` guard is relaxed for the curated `PROHIBITED_SUBJECT_ACRONYMS` scan only, while the generic `_ACRONYM_RE` remains suppressed for all-caps subjects. This provides detection on compliant (all-caps) subjects without reintroducing generic false positives.

4. **Should `APPROVED_ACRONYMS` be deduplicated into a shared constants module?**
   Today it is duplicated in `cci_subject_validate.py` and `cci_acronym_validate.py`. A shared `src/cci_constants.py` would reduce drift but is a refactor outside Phase H.2 scope.

5. **Should the rule catalog entry `CCI-CH7-SUBJ-006` be updated with `validator_status` before or after the validator implementation?**
   Recommended: update catalog metadata in the same commit as the validator change, but only after the targeted regression passes.

6. **Should the existing `CCI-CH7-SUBJ-004` warning be renumbered to `CCI-CH7-SUBJ-007` if the behavior changes significantly?**
   Renumbering breaks downstream consumers who parse `SUBJ-004`. Recommended: keep `SUBJ-004` for the advisory and reserve `SUBJ-007` for a future error level.

7. **Should the targeted regression runner test the interaction with the body acronym validator explicitly?**
   Recommended yes, but this requires an integration-style fixture that exercises both validators on the same payload. This is optional for Phase H.2.

8. **If false positives are detected after merge, what is the correct reversion path?**
   Options: (a) `git revert`, (b) set feature flag to `"disabled"`, (c) move record to `rejected_for_implementation`. The plan recommends option (a) as primary, (b) as fallback if a flag exists.

---

## 19. References

- `docs/PROJECT_STATUS.md` — Current handoff and baseline.
- `docs/checkpoints/phase_h1_pilot_approved_rule_implementation_checkpoint.md` — Phase H.1 completion status and next-phase recommendation.
- `docs/planning/phase_h1_pilot_approved_rule_implementation_plan.md` — Phase H.1 planning methodology.
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — Correction memory and rule promotion layer.
- `src/cci_subject_validate.py` — Subject-line validator (current behavior).
- `src/cci_acronym_validate.py` — Body acronym validator (for interaction context).
- `rules_v6/CCI/cci_ch7_subject_rules.json` — Rule catalog entry `CCI-CH7-SUBJ-006`.
- `SECNAV M-5216.5, Change 1, Chapter 7, paragraph 9, Subject Line, subparagraph a. General` — Source text: "In correspondence, do not use acronyms in the subject line."

---

End of Phase H.2 / Phase I.1 Subject-Line Acronym Validator Enforcement Plan.
