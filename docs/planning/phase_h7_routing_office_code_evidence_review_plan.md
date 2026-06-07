# Phase H.7 / Phase I.6 — Routing Office-Code Evidence Review and Next-Action Decision Plan

**Date:** 2026-06-07  
**Latest Docs Checkpoint:** `8e3e715` — `Docs: Record Phase H.6 evidence checkpoint`  
**Current Functional Baseline:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`  
**Previous Functional Baseline:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Current Regression Set:** 29 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until approved  

---

## 1. Current CCI-ROUTE-010 Advisory Behavior

### Advisory Validator State

- **Validator file:** `src/cci_routing_validate.py`
- **Helper:** `_check_office_code_prefix(...)` — added in Phase H.4
- **Integration:** called inside `validate_cci_routing(...)` without signature change
- **Return type:** `tuple[list[str], list[str]]` as `(errors, warnings)` — preserved
- **Enforcement level:** advisory/non-blocking only
- **Errors list:** remains empty for this rule
- **Warnings list:** advisory findings appended as formatted strings containing `(advisory):`, `CCI-ROUTE-010`, and `SECNAV M-5216.5` citation

### Detection Scope

- Checked on: `routing.to` and `routing.via` addressee strings
- Not checked on: `routing.copy_to` (deferred)
- Not checked: body, subject, references, enclosures, distribution, free text

### Detection Patterns

| Scenario | Current Result |
|---|---|
| `Commanding Officer, 123` (numeric, no `Code`) | Advisory warning — missing `Code` |
| `Commanding Officer (123)` (numeric, no `Code`) | Advisory warning — missing `Code` |
| `Commanding Officer, Code N1` (letter, improper `Code`) | Advisory warning — improper `Code` |
| `Commanding Officer (Code SUP)` (letter, improper `Code`) | Advisory warning — improper `Code` |
| `Commanding Officer, Code 123` | OK — valid numeric with `Code` |
| `Commanding Officer (Code 123)` | OK — valid parenthetic with `Code` |
| `Commanding Officer, N1` | OK — valid letter without `Code` |
| `Commanding Officer (SUP)` | OK — valid parenthetic without `Code` |
| `Commander U.S. Pacific Fleet 123` (no delimiter) | OK — no trigger |
| Normal title without comma or parenthesis | OK — no trigger |

### Catalog Severity vs Validator Severity

- **Catalog severity:** `error` (set at Phase H.3)
- **Validator severity:** `advisory` (interim, non-blocking since Phase H.4)
- **Gap:** catalog declares the rule as `error`-level; validator intentionally emits it as advisory only
- **Rationale:** avoid breaking existing routing workflows while collecting evidence

---

## 2. Summary of H.6 Evidence Fixtures

### 20 Negative-Control Fixtures (must NOT trigger)

Phase H.6 added 20 synthetic negative-control fixtures under `examples/routing_h6_negative_01.json` through `routing_h6_negative_20.json`.

| # | Pattern Category | Example |
|---|---|---|
| 1 | Hull number references | `USS Nimitz (CVN-68)` |
| 2 | Task force designators | `Task Force 70` |
| 3 | MAG/MEU numeric identifiers | `Marine Air Group 12` |
| 4 | Ordinal unit references | `1st Marine Division` |
| 5 | Fiscal year references | `FY 2026` |
| 6 | Status notes in parentheses | `(Acting)` |
| 7 | Semicolon-delimited addressees without numeric codes | `Commanding Officer; 123` |
| 8 | Slash-delimited addressees without numeric codes | `Commanding Officer / 123` |
| 9 | Facility numbers with letters | `Building N-23` |
| 10 | Room numbers with letters | `Room A-101` |
| 11 | Valid `Code` prefix forms that should not trigger | `Commanding Officer, Code 123` |
| 12 | Valid letter-starting forms without `Code` | `Commanding Officer, N1` |
| 13 | Parenthetical status notes | `(Draft)` |
| 14 | Year-in-parenthesis forms | `(2025)` |
| 15 | Leading number forms (not office codes) | `12345 Commander` |
| 16 | Abbreviated building codes | `Bldg 123` |
| 17 | Letter-only identifiers | `HANGAR B` |
| 18 | Post box numbers | `BOX 555` |
| 19 | Suite letters | `SUITE A` |
| 20 | Dock/facility numbers | `PIER 7`, `DOCK 4` |

### 10 Positive-Control Fixtures (MUST trigger)

Phase H.6 added 10 synthetic positive-control fixtures under `examples/routing_h6_positive_01.json` through `routing_h6_positive_10.json`.

| # | Pattern Category | Expected Finding |
|---|---|---|
| 1 | Missing-Code numeric comma forms in `to` lines | Missing `Code` before numeric office code |
| 2 | Missing-Code numeric parenthetical forms in `to` lines | Missing `Code` before numeric office code |
| 3 | Missing-Code numeric comma forms in `via` lines | Missing `Code` before numeric office code |
| 4 | Improper-Code letter-starting comma forms | Improper `Code` before letter-starting code |
| 5 | Improper-Code letter-starting parenthetical forms | Improper `Code` before letter-starting code |
| 6 | Multi-part comma forms with partial numeric codes | Missing `Code` before numeric office code |
| 7 | Multi-part parenthetical forms with partial numeric codes | Missing `Code` before numeric office code |
| 8 | Consecutive numeric codes in `to` lines | Missing `Code` before numeric office code |
| 9 | Consecutive numeric codes in `via` lines | Missing `Code` before numeric office code |
| 10 | Zero-padded numeric codes | Missing `Code` before numeric office code |

### Local Gitignored 50-Pattern Corpus

- **Path:** `corrections/evidence/routing_office_code_patterns.jsonl`
- **Content:** 50 synthetic-realistic To/Via patterns for future analysis
- **Status:** gitignored via `.gitignore` (`corrections/evidence/`)
- **Committed:** No — local-only, not in repository
- **Purpose:** future review and potential expansion of fixture coverage

---

## 3. What Evidence Is Sufficient for Now

The following evidence thresholds are **met** as of Phase H.6:

1. **20 negative-control fixtures** — met. The H.6 runner verifies all 20 produce zero `CCI-ROUTE-010` warnings.
2. **10 positive-control fixtures** — met. The H.6 runner verifies all 10 produce `CCI-ROUTE-010` warnings with `(advisory):` format.
3. **50 synthetic-realistic To/Via patterns** — met. Stored in local gitignored corpus for future review.
4. **`errors`-list emptiness verification** — met. H.6 runner checks that `errors` list is empty for all fixtures.
5. **Copy-to exclusion verification** — met. H.6 runner verifies `copy_to` numeric-only and letter-starting codes do NOT trigger.
6. **Advisory format contract verification** — met. H.6 runner verifies `(advisory):`, `CCI-ROUTE-010`, and `SECNAV M-5216.5` appear in warning strings.
7. **Zero regression failures** — met. All 29 suites pass.
8. **No validator logic changes** — met. `src/cci_routing_validate.py` was untouched in H.6.
9. **No forbidden files changed** — met. H.6 runner verifies no renderer, prompt-contract, command-layer, or catalog files were modified.

---

## 4. What Evidence Is Still Missing

The following evidence is **not yet collected** or **not yet sufficient**:

1. **Real-world Navy/Marine Corps To/Via patterns.** The 50 local corpus patterns are synthetic-realistic, not from actual correspondence. Real-world patterns may reveal edge cases not covered by synthetic fixtures.
2. **Joint-letter multi-addressee stress testing.** Current fixtures test single-addressee and consecutive-addressee forms, but not complex joint-letter routing with mixed numeric and letter codes across multiple `to` entries.
3. **Copy-to explicit SECNAV citation.** No manual citation has been identified for `copy_to` office-code behavior. A separate candidate rule would need its own provenance.
4. **Extended real-world usage sessions.** No production or extended beta usage has occurred with `CCI-ROUTE-010` advisory active. False-positive reports from real users are the strongest evidence.
5. **Warning-level behavior testing.** The current evidence only proves advisory behavior. Warning-level behavior (e.g., stronger CI gate impact) has not been tested.
6. **Feature flag/config mechanism validation.** No config-driven severity override exists, so no evidence exists that severity promotion would work safely via config.
7. **Cross-rule severity consistency.** If `CCI-ROUTE-010` is promoted, should `CCI-CH7-SUBJ-007` (subject-line acronym advisory) also be reviewed? No cross-rule evidence exists.

---

## 5. Whether CCI-ROUTE-010 Should Remain Advisory

**Recommendation: YES — keep `CCI-ROUTE-010` advisory-only.**

Rationale:
- H.6 evidence is synthetic-only. No real-world usage feedback exists.
- The 50 local corpus patterns are plausible but not validated against actual correspondence.
- Routing is a high-frequency field; every letter has at least one addressee. A false positive at error/warning level would block or flag common command formats.
- The severity gap (catalog `error` vs validator `advisory`) is documented and intentional. Closing it requires real-world evidence, not just synthetic fixtures.
- Phase H.5 already approved the advisory-only verdict. Phase H.6 collected the evidence H.5 required. The evidence supports maintaining the H.5 verdict.

---

## 6. Whether Severity Promotion Should Still Be Deferred

**Recommendation: YES — defer severity promotion indefinitely until real-world evidence is available.**

Rationale:
- Synthetic fixtures prove the validator behaves correctly on controlled inputs. They do not prove it behaves correctly on uncontrolled real-world inputs.
- The H.5 plan established criteria for moving from advisory to warning (Section 9) and from warning to error (Section 10). Neither set of criteria is fully met:
  - Criterion 3 (50 real-world patterns with zero unexpected findings) — not met; only synthetic patterns exist.
  - Criterion 5 (no open issues or user reports of false positives) — not met; no real-world usage sessions have occurred.
  - Criterion 6 (feature flag/config mechanism designed) — partially met; design exists in H.5 plan but is not implemented.
- Deferring does not mean abandoning. It means maintaining the current safe posture until stronger evidence justifies a change.

---

## 7. Whether Feature Flag/Config Support Should Be Planned Before Any Severity Promotion

**Recommendation: YES — feature flag/config support must be designed and at least partially implemented before any severity promotion.**

Rationale:
- Advisory findings are non-blocking; they do not stop rendering or submission.
- Warning findings could affect downstream tooling or CI pipelines that treat warnings as review triggers.
- Error findings would reject the payload entirely.
- A feature flag allows gradual rollout without code changes — e.g., a config file or environment variable.
- Precedent: no existing feature-flag mechanism exists in the routing validator today.
- The H.5 plan proposed a minimal mechanism: `profiles/severity_overrides.json` or `config/validator_severity.yaml` with per-rule ID override.
- Planning for this mechanism should be the next planning phase if severity promotion is ever approved.

**Proposed minimal mechanism (design-only for now):**
- Config file: `profiles/severity_overrides.json` or `config/validator_severity.yaml`
- Override per rule ID: `"CCI-ROUTE-010": "advisory"` → `"warning"` → `"error"`
- Default: read catalog severity; override takes precedence.
- No change to catalog severity field; override is runtime only.
- Validator reads config at call time; missing config defaults to advisory for interim rules.

---

## 8. Whether Copy-To Should Remain Out of Scope

**Recommendation: YES — keep `copy_to` out of scope for `CCI-ROUTE-010`.**

Rationale:
- The SECNAV source citation is `Chapter 7, paragraph 7-2.7a, To Line, General`.
- The manual text explicitly discusses the To line, not the Copy-To line.
- Copy-To office-code conventions may differ (e.g., abbreviated formats, distribution lists).
- A separate candidate rule with its own provenance citation would be needed for `copy_to`.
- Expanding scope without separate provenance would violate the project's manual-and-figure source standard.
- H.6 verified that `copy_to` does not trigger (Check 5 and Check 6 in the H.6 runner). This boundary is regression-protected.

Future work: if a user identifies an explicit SECNAV citation for `copy_to` office-code formatting, that becomes a separate Phase H.x candidate.

---

## 9. Whether More Real-World or Synthetic-Realistic Evidence Should Be Collected

**Recommendation: OPTIONAL — collect more evidence only if real-world usage begins or if a user reports an edge case.**

Rationale:
- The current 30 fixtures + 50 corpus patterns provide reasonable synthetic coverage.
- Diminishing returns: additional synthetic fixtures without real-world feedback may not improve confidence.
- The highest-value evidence would come from:
  1. Actual Navy/Marine Corps correspondence samples (sanitized)
  2. User reports of false positives or false negatives during advisory usage
  3. Extended beta testing with advisory-only enforcement
- If no real-world usage is planned, the current evidence is sufficient to maintain the advisory-only posture.
- If a third catalog pilot is selected instead, evidence collection for `CCI-ROUTE-010` can pause indefinitely.

---

## 10. Whether a Third Low-Risk Catalog Pilot Should Be Selected Instead of Continuing Severity Work

**Recommendation: CONSIDER — a third catalog pilot may be higher-value than continuing severity work on `CCI-ROUTE-010`.**

Rationale:
- Two catalog pilots exist: `CCI-CH7-SUBJ-006` (subject-line acronym) and `CCI-ROUTE-010` (routing office code).
- Both pilots follow the same safe pattern: rule-catalog entry first, then optional advisory validator, then evidence collection, then severity review.
- A third pilot could apply this proven pattern to a new rule from a different chapter or section, expanding CCI coverage horizontally rather than deepening one rule vertically.
- Potential third-pilot candidates (from existing Phase H/H.1/H.2/H.3/H.4 work):
  - Date/time format rules (Chapter 7, paragraph 7-2.3)
  - Reference/enclosure format rules (Chapter 7, paragraph 7-2.5)
  - Personnel identification rules (Chapter 7, paragraph 7-2.6)
  - Point-of-contact expectation rules
  - Acronym first-use rules beyond subject line
- A third pilot would:
  - Follow the proven H.1/H.3 pattern (rule-catalog-only first)
  - Add a new targeted regression runner
  - Increase the regression gate from 29 to 30 suites
  - Not affect `CCI-ROUTE-010` or its advisory status
- This may be preferable to continuing to build evidence for a rule that may never be promoted.

---

## 11. Decision Options

### Option A: Keep Advisory Indefinitely

- **Action:** Do not promote `CCI-ROUTE-010`. Do not collect additional evidence. Do not add severity config.
- **Pros:** Zero risk. No code changes. Existing 29-suite regression maintained.
- **Cons:** Catalog/validator severity gap remains. Rule never achieves its catalog-declared `error` level.
- **When to choose:** If real-world usage is unlikely or if false-positive risk is deemed unacceptable.

### Option B: Collect More Evidence

- **Action:** Add more negative/positive fixtures or expand the local corpus. Does not change validator severity.
- **Pros:** Increases confidence in current behavior. Protects against future regressions.
- **Cons:** Diminishing returns without real-world data. Adds maintenance overhead.
- **When to choose:** If a user reports an edge case or if real-world usage is imminent.

### Option C: Design Feature Flag/Config Support

- **Action:** Create a planning document for config-driven severity override. Design only; no implementation unless explicitly approved.
- **Pros:** Enables future severity promotion without code changes. Useful for all advisory rules, not just `CCI-ROUTE-010`.
- **Cons:** Design work without implementation may be premature if severity promotion is never approved.
- **When to choose:** If the user wants to preserve the option of future severity promotion across multiple rules.

### Option D: Plan Warning-Level Rollout

- **Action:** Use H.6 evidence to plan promotion from advisory to warning. Requires planning document, config implementation, and new regression checks.
- **Pros:** Closes the catalog/validator severity gap partially. Warning level is less risky than error.
- **Cons:** Still requires real-world evidence per H.5 criteria. Synthetic fixtures alone are insufficient.
- **When to choose:** Only after real-world usage sessions with zero false-positive reports.

### Option E: Plan Third Catalog Pilot

- **Action:** Select a new low-risk rule from a different chapter/section. Follow H.1/H.3 pattern: catalog entry first, then optional validator, then evidence.
- **Pros:** Expands CCI coverage horizontally. Uses proven safe pattern. Does not deepen `CCI-ROUTE-010` risk.
- **Cons:** New runner adds to regression gate (30 suites). Requires new planning document.
- **When to choose:** If the user wants to broaden compliance coverage rather than refine one rule.

---

## 12. Recommended Default Decision

**Recommended: Option A (Keep Advisory Indefinitely) as the default, with Option E (Third Catalog Pilot) as the preferred alternative if the user wants to continue implementation work.**

Rationale:
- The evidence collected in H.6 is sufficient to maintain the advisory-only posture but insufficient to justify severity promotion.
- Real-world usage feedback is the missing link. Without it, additional synthetic evidence or config design is speculative.
- A third catalog pilot provides tangible value (new compliance coverage) with the same proven safety pattern.
- If the user explicitly wants to continue with `CCI-ROUTE-010`, Option C (Feature Flag Design) is the next safest step.

---

## 13. Regression Expectations

### Current Gate (No Changes)

- **Gate:** 29 suites
- **Status:** All PASS
- **No new runner needed** for Phase H.7 if it remains planning-only.

### If a New H.7 Runner Is Added

If Phase H.7 implements anything (e.g., a third catalog pilot with a new runner, or a feature-flag config runner):
- **Gate becomes:** 30 suites
- **New runner would be:** `tools/run_phase_h7_*.py` or similar
- **All existing 29 suites must still pass.**

### If Phase H.7 Remains Planning-Only

- **Gate remains:** 29 suites
- **No code changes.**
- **No new runner.**
- **All 29 suites must still pass before any future commit.**

---

## 14. Files That May Be Modified in Future Implementation

If Phase H.7 or a future phase implements any of the decision options:

| File | Potential Change |
|---|---|
| `docs/PROJECT_STATUS.md` | Update baseline, next-phase guidance, historical milestones |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Update next-phase directions, regression list |
| `docs/checkpoints/phase_h7_routing_office_code_evidence_review_checkpoint.md` | New checkpoint if H.7 is implemented |
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Only if a new routing rule is added (Option E third pilot) |
| `rules_v6/CCI/cci_ch7_subject_rules.json` | Only if a new subject rule is added (Option E third pilot) |
| `tools/run_phase_h7_*.py` | New runner if H.7 implements anything |
| `examples/*` | New fixtures if Option B or Option E is chosen |
| `src/cci_routing_validate.py` | Only if Option D (warning promotion) is approved and implemented |
| `profiles/severity_overrides.json` or `config/validator_severity.yaml` | Only if Option C is implemented |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | Update allowed-files whitelist if new docs/files are added |
| `tools/run_phase_h6_routing_office_code_evidence_regression.py` | Update allowed-files whitelist if new docs/files are added |

---

## 15. Files That Must Not Be Modified

| File | Why |
|---|---|
| `src/pdf_v6_render.py` | No renderer/layout changes unless explicitly scoped and regression-protected |
| `src/context_resolver.py` | No prompt-contract runtime changes |
| `src/intake_orchestrator.py` | No intake orchestration changes unless separately approved |
| `src/validator_runner.py` | No validator runner contract changes unless separately approved |
| `src/correction_commands.py` | No Phase F command-layer changes |
| `src/correction_nl_commands.py` | No Phase G command-layer changes |
| `src/correction_implementation_planner.py` | No planner changes unless separately approved |
| `src/cci_subject_validate.py` | No subject validator changes |
| `src/cci_acronym_validate.py` | No acronym validator changes |
| `src/cci_date_time_validate.py` | No date/time validator changes |
| `src/cci_personnel_validate.py` | No personnel validator changes |
| `src/cci_poc_validate.py` | No POC validator changes |
| `corrections/approved_rule_promotions.json` | Remains local/gitignored; do not commit |
| `corrections/pending_corrections.jsonl` | Remains local/gitignored; do not commit |
| `corrections/session/*.jsonl` | Remains local/gitignored; do not commit |
| `corrections/evidence/*` | Remains local/gitignored; do not commit |
| Any real command/user profile | Do not commit contact data or local profiles |

---

## 16. What Phase H.7 Must NOT Do

Phase H.7 is a **review and decision phase**. It must NOT:

- **No severity promotion.** `CCI-ROUTE-010` must remain advisory-only. No routing of findings to `errors`.
- **No validator logic changes** unless separately approved by the user. `src/cci_routing_validate.py` must remain untouched.
- **No renderer/layout changes.** Severity promotion is a validator semantic change, not a PDF geometry change.
- **No automatic enforcement from approved logs.** The validator must not read `corrections/approved_rule_promotions.json` to determine severity.
- **No AI-only implementation decisions.** Any future severity promotion, config implementation, or third-pilot selection requires explicit user approval.
- **No prompt-contract runtime changes.** `src/context_resolver.py`, `src/intake_orchestrator.py`, and `src/validator_runner.py` contracts remain unchanged.
- **No Phase F/G command-layer changes.** No new slash commands or NL command mappings for severity management or fixture management.
- **No approved/pending/session logs committed.** All correction storage remains local/gitignored.
- **No real command/user data committed.** No contact info, no local profiles, no session stores.
- **No background automation.** The validator runs only when explicitly invoked.

---

## 17. Rollback Plan

If Phase H.7 causes unexpected failures (e.g., if an implementation decision is made and executed):

1. Revert the commit that implemented the change.
2. The catalog entry `CCI-ROUTE-010` remains unchanged in `rules_v6/CCI/cci_ch2_routing_rules.json`.
3. The Phase H.4 advisory helper `_check_office_code_prefix(...)` remains in `src/cci_routing_validate.py` and continues to emit advisory warnings.
4. The Phase H.6 runner and fixtures remain intact and continue to pass.
5. Remove any new H.7 runner if it was added.
6. Re-run the 29-suite gate without H.7.
7. All earlier phases (H.6, H.5, H.4, H.3, H.2, H.1, H, G, F, E, D, C, B, A) remain intact.

Rollback risk: **very low** — Phase H.7 is planning-only by default. If implementation occurs, it follows the same safe pattern as previous phases.

---

## 18. Open Questions Needing Approval

1. **Should `CCI-ROUTE-010` remain advisory indefinitely, or is severity promotion still a future goal?**
   - Default: remain advisory indefinitely.

2. **Should more evidence be collected for `CCI-ROUTE-010` before any future severity review?**
   - Default: no — current evidence is sufficient for advisory maintenance.

3. **Should feature flag/config support be designed now, or deferred until severity promotion is explicitly requested?**
   - Default: deferred — design only when severity promotion is requested.

4. **Should a third low-risk catalog pilot be selected as the next implementation target instead of continuing `CCI-ROUTE-010` work?**
   - Default: yes — third pilot is higher-value than deepening `CCI-ROUTE-010`.

5. **If a third pilot is selected, which rule category should it target (subject, date/time, reference/enclosure, personnel, POC, acronym)?**
   - Default: undecided — requires user input or manual review.

6. **Should the H.6 runner be extended with additional checks, or should it remain frozen at 15 checks?**
   - Default: frozen — extend only if new fixtures or edge cases are added.

7. **Should the 50-pattern local corpus be periodically reviewed and expanded, or left as-is?**
   - Default: left as-is — expand only if real-world usage begins.

8. **Should the project maintain `advisory` as a permanent tier for some rules, or should all advisory rules eventually be promoted?**
   - Default: permanent tier allowed — some rules may stay advisory indefinitely if false-positive risk is unacceptable.

9. **Who approves the next implementation target — the user only, or a documented reviewer workflow?**
   - Default: user-only approval; no automated promotion or AI-only decisions.

10. **Should Phase H.7 remain strictly planning-only, or is any implementation authorized?**
    - Default: strictly planning-only; no code changes.

---

## Recommended Decision Summary

| Decision | Recommended Default |
|---|---|
| **Keep `CCI-ROUTE-010` advisory?** | Yes — indefinitely |
| **Severity promotion?** | No — deferred until real-world evidence exists |
| **Feature flag/config design?** | Deferred until severity promotion is requested |
| **Copy-to scope?** | Remain out of scope |
| **More evidence collection?** | No — current 30 fixtures + 50 corpus is sufficient for advisory |
| **Third catalog pilot?** | Yes — preferred next implementation target |
| **Regression coverage** | 29-suite gate (planning-only); 30-suite if third pilot implemented |
| **Rollback risk** | Very low — planning-only by default |

## Recommended Next Implementation Target

**If the user approves continued implementation work:**
- Select and plan a **third low-risk catalog pilot** (rule-catalog-only, following the H.1/H.3 pattern).
- Candidate areas: date/time format, reference/enclosure format, personnel identification, or acronym first-use (outside subject line).
- Planning document required before implementation.
- New targeted regression runner required (30-suite gate).

**If the user prefers to pause implementation:**
- Maintain current 29-suite regression.
- Keep `CCI-ROUTE-010` advisory indefinitely.
- No code changes. No new runners.
- Resume only when user explicitly requests a new phase.

## Recommended Regression Gate

- **If planning-only:** 29 suites (current gate, no changes).
- **If third pilot implemented:** 30 suites (29 existing + 1 new pilot runner).
- **All suites must pass before any commit.**

## Open Questions Needing Approval

1. Should `CCI-ROUTE-010` remain advisory indefinitely, or is severity promotion still a future goal?
2. Should a third catalog pilot be the next implementation target?
3. If a third pilot is selected, which rule category should it target?
4. Should Phase H.7 remain planning-only, or is any implementation authorized?
5. Should the 50-pattern local corpus be periodically reviewed, or left as-is?

---

End of Phase H.7 / Phase I.6 Routing Office-Code Evidence Review and Next-Action Decision Plan.
