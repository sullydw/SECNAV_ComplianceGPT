# Phase H.3 / Phase I.2 — Second Low-Risk Rule-Catalog-Only Pilot Plan

**Current Verified Functional Baseline:** `609821e` — CCI: Add subject acronym advisory validator (Phase H.2)  
**Phase H.2 Implementation Commit:** `609821e` — CCI: Add subject acronym advisory validator (Phase H.2)  
**Phase H.1 Pilot Implementation Commit:** `ef365d3` — CCI: Implement pilot approved rule (Phase H.1)  
**Phase H.1 Mark-Implemented Wrapper Commit:** `6298dab` — CCI: Add public mark implemented wrapper  
**Branch:** `main`  
**Status:** Planning-only until reviewed and approved. No code may be written under this plan without separate user approval.  
**Scope:** Select, plan, and prepare one second low-risk approved-rule pilot that is strictly rule-catalog-only (no validator enforcement, no renderer/layout changes, no prompt-contract changes, no command-layer changes).

---

## 1. Purpose

Phase H.3 / Phase I.2 is the **second approved-rule pilot** following the successful H.1 rule-catalog-only pilot (`CCI-CH7-SUBJ-006`) and the H.2 validator-enforcement follow-up (`CCI-CH7-SUBJ-007`).

This phase intentionally returns to **rule-catalog-only** scope to:

- Continue proving the approved-record workflow end-to-end before adding more validator complexity.
- Build confidence in the candidate-selection, Phase E review, Phase H claim/plan, catalog-entry, and `mark_implemented()` workflow with a fresh rule.
- Avoid validator-enforcement risks (false positives, feature flags, regression breakage) until more rule-catalog pilots have succeeded.
- Keep blast radius minimal: one new JSON entry in `rules_v6/CCI/` plus a targeted regression runner.

**This plan is planning-only until reviewed and approved.** No code may be written under this plan without separate user approval.

---

## 2. Why Rule-Catalog-Only for the Second Pilot

### 2.1 Evidence from H.1 and H.2

| Pilot | Scope | Risk Level | Regression Suites | Outcome |
|---|---|---|---|---|
| H.1 | Rule-catalog only | Very low | 25 | PASS — clean workflow proof |
| H.2 | Validator advisory enforcement | Low-medium | 26 | PASS — but required `isupper()` guard analysis, false-positive assessment, and fixture expansion |

H.2 showed that even advisory-level validator changes require:
- Curated token lists with provenance.
- False-positive risk assessment per token.
- Dedicated fixture files (7 new fixtures for 3 tokens).
- Targeted regression runner (12 checks).
- Updates to the pilot catalog runner to allow expected mutations.

A second rule-catalog-only pilot keeps the learning curve flat and validates that the **non-validator** portion of the workflow (candidate selection → Phase E → Phase H → catalog entry → `mark_implemented()`) is repeatable.

### 2.2 Benefits of Rule-Catalog-Only

- **Zero validator blast radius** — no `src/cci_*_validate.py` files touched.
- **Zero renderer/layout risk** — no `src/pdf_v6_render.py` or layout profile changes.
- **Zero prompt-contract risk** — no `src/context_resolver.py` changes.
- **Zero command-layer risk** — no `src/correction_commands.py` or `src/correction_nl_commands.py` changes.
- **Fast regression verification** — targeted runner focuses on catalog schema and entry presence.
- **Easy rollback** — delete one JSON object and one runner file.

### 2.3 When Validator Enforcement Follows

A separate Phase H.4 / Phase I.3 planning document may later propose validator enforcement for the H.3 rule *or* for the existing `CCI-CH7-SUBJ-006` catalog entry. That decision must be made **after** the H.3 catalog pilot is complete and approved, not during H.3.

---

## 3. How to Identify a Second Candidate from SECNAV M-5216.5

### 3.1 Source of Candidates

Candidate rules must come from one of these proven sources:

1. **Pending global rule candidate log** (`corrections/pending_corrections.jsonl`) — Phase D logged items that have not yet been reviewed.
2. **Existing CCI validator rules** that lack a catalog entry — some validators enforce rules not yet mirrored in `rules_v6/CCI/`.
3. **Direct manual review** of SECNAV M-5216.5 chapters 2, 7, 8, 9, 10 for explicit text rules not yet cataloged.
4. **Correction memory patterns** — recurring correction themes in session stores that suggest a deterministic manual rule.

### 3.2 Preferred Discovery Order

1. First, check the local pending candidate log for any already-sanitized candidate with clear manual provenance.
2. Second, review existing rule catalog files for gaps — compare `cci_ch2_*_rules.json` and `cci_ch7_*_rules.json` against the validators to find rules enforced but not cataloged, or cataloged but not yet promoted from `pending_implementation`.
3. Third, perform a focused manual-text review of SECNAV M-5216.5 Chapter 2 (date/time, personnel, POC, routing, acronym) and Chapter 7 (subject, reference/enclosure) for short, explicit imperative sentences.

---

## 4. Candidate Selection Criteria

A candidate must satisfy **all** of the following before it can be selected for the H.3 pilot:

| Criterion | Requirement |
|---|---|
| Explicit manual text | The rule must be stated as an imperative sentence or clear directive in SECNAV M-5216.5 narrative text (not inferred from figure geometry). |
| Deterministic rule statement | The rule must be expressible as a deterministic yes/no test with no subjective judgment required. |
| No renderer/layout implication | The rule must not require margin, font, spacing, indentation, or page-break changes. |
| No command-specific/local-only rule | The rule must be a SECNAV manual rule, not a local command preference or one-time wording edit. |
| Low blast radius | The rule must apply to a single field or small set of fields (e.g., subject line, date field, POC block) — not to entire body paragraph structure or multi-document workflows. |
| Provenance easy to document | Chapter, paragraph, subparagraph, and exact quote must be locatable in the manual within 10 minutes of search. |

---

## 5. Candidate Types to Prefer

These rule types have demonstrated low blast radius in the existing CCI layer:

### 5.1 Subject-Line Rule (example: H.1/H.2)
- Already proven viable.
- Single field (`subj`).
- Explicit manual text in Chapter 7, paragraph 9.

### 5.2 Reference/Enclosure Rule
- Single field (`refs`, `encls`).
- Chapter 7, paragraph 7-3.3 has explicit sequencing and citation rules.
- Existing validator (`cci_ref_encl_validate.py`) already enforces several deterministic rules; some may lack catalog entries.

### 5.3 Date/Time Wording Rule
- Single field (`date` or body text time mentions).
- Chapter 2, paragraph 2-4.2 has explicit military-time and date-format rules.
- Existing validator (`cci_date_time_validate.py`) enforces deterministic checks; some may not be mirrored in `cci_ch2_date_time_rules.json`.

### 5.4 Personnel Identification Rule
- Single field or small body-text pattern.
- Chapter 2 has rank/rate/grade capitalization rules.
- Existing validator (`cci_personnel_validate.py`) enforces `PER-001` (all-caps last names) deterministically.

### 5.5 Routing/Copy-To Rule
- Single field (`routing`, `copy_to`).
- Chapter 2 or Chapter 7 has sequencing and completeness rules for Via and Copy-to lines.
- Existing validator (`cci_routing_validate.py`) has deterministic and heuristic checks.

---

## 6. Candidate Types to Avoid

| Type | Reason |
|---|---|
| Body paragraph structure | Requires complex paragraph-level parsing, subparagraph sequencing, indentation logic — high blast radius. |
| Layout/margin/font/spacing | Requires renderer changes; explicitly out of scope for rule-catalog pilots. |
| Multi-document workflow rules | Requires coordination across endorsement chains, continuation pages, and enclosure tracking — too complex for a single pilot. |
| Ambiguous examples | If the manual says "generally" or "usually" without an imperative directive, it is a heuristic, not a deterministic rule. |
| Rules hidden in figures that require visual layout interpretation | Figure geometry is valid for layout work, but rule-catalog entries need narrative text quotes. If the rule exists *only* in a figure caption with no surrounding directive text, it is harder to document and more prone to layout coupling. |

---

## 7. How to Create or Identify the Pending Candidate Through the Normal Workflow

### 7.1 From Phase D Pending Log

If a suitable candidate exists in `corrections/pending_corrections.jsonl`:

1. Read the candidate entry.
2. Verify it has `proposed_scope` of `global_rule` or `validator_gap`.
3. Verify it has `sanitized=True` and no PII.
4. Verify the `correction_reason` or `proposed_rule_text` cites a manual location.
5. Open the candidate in Phase E review using the existing review workflow.

### 7.2 From Manual Direct Review

If no suitable pending candidate exists:

1. Select a manual chapter/paragraph known to contain explicit directives (Chapter 2 paragraphs 2-4.2, 2-4.3; Chapter 7 paragraphs 7-2.9, 7-3.3; Chapter 8 paragraph 8-2; Chapter 9 paragraph 9-2; Chapter 10 paragraph 10-2).
2. Extract one short imperative sentence.
3. Create a **synthetic** candidate record locally (do not commit it) using the Phase D pending-candidate format.
4. Review it locally for determinism and low blast radius.
5. Open it in Phase E review only if it passes local screening.

### 7.3 From Existing Validator Gap

If an existing validator enforces a rule not yet in the catalog:

1. Identify the validator check and its error/warning code.
2. Trace the code to the manual source (usually documented in the validator docstring or a nearby comment).
3. Create a synthetic approved record that maps the existing validator rule to a catalog entry.
4. Proceed to Phase E review.

**In all cases, do not commit pending candidates, approved records, or synthetic test data to the repository.**

---

## 8. How Phase E Review Should Approve the Candidate

### 8.1 Reviewer Responsibilities

The Phase E reviewer must:

1. **Claim** the candidate via the existing `claim_record_for_review()` workflow.
2. **Verify provenance** — confirm the manual chapter, paragraph, subparagraph, and exact quote.
3. **Assess determinism** — confirm the rule is a yes/no test, not a subjective style preference.
4. **Assess blast radius** — confirm the rule touches only one field or a small, well-defined set of fields.
5. **Check for duplicates** — confirm no existing catalog entry already covers this rule.
6. **Record the decision** — append review metadata with `review_status="approved_for_implementation"` and `implementation_status="pending_implementation"`.
7. **Create the approved record** — write the approved record to the local approved log only (gitignored).

### 8.2 Approval Gates

| Gate | Pass Criteria |
|---|---|
| Provenance gate | Manual chapter/paragraph/quote is verifiable and unambiguous. |
| Determinism gate | Rule can be written as a deterministic test with no subjective threshold. |
| Blast-radius gate | Rule affects ≤2 fields and does not require renderer/layout changes. |
| Duplicate gate | No existing catalog entry with the same or substantially overlapping rule text. |
| Safety gate | Rule is not a local command preference, one-time edit, or AI suggestion without manual grounding. |

Only if all five gates pass may the reviewer approve the candidate.

---

## 9. How Phase H Planner Should Claim and Plan It

### 9.1 Claim

1. The implementer calls `claim_record_for_implementation()` on the approved record ID.
2. The planner validates that the record status is `pending_implementation`.
3. The planner validates that the record has not already been claimed by another implementer.

### 9.2 Plan

1. The implementer calls `plan_implementation()` with:
   - `implementation_target`: `rule_catalog` (must be explicitly set to `rule_catalog`, not `validator`, `prompt_contract`, or `renderer`).
   - `target_file`: the specific `rules_v6/CCI/*.json` file.
   - `source_verification_summary`: provenance confirmation.
2. The planner creates an `implementation_planned` record with a unique `implementation_id`.
3. The approved record status transitions to `implementation_planned`.

### 9.3 H.3-Specific Planning Constraint

For the H.3 pilot, the `implementation_target` **must** be `rule_catalog`. Any plan proposing `validator`, `prompt_contract`, or `renderer` as the target must be rejected and redirected to a separate future planning phase (e.g., H.4 / I.3).

---

## 10. Required Rule-Catalog Entry Schema and Provenance

### 10.1 Schema

The new catalog entry must follow the same schema as `CCI-CH7-SUBJ-006`:

```json
{
  "rule_id": "CCI-XXX-NNN",
  "source": "SECNAV M-5216.5",
  "source_type": "narrative_text",
  "source_location": "Chapter N, paragraph X-Y, [Subparagraph Z]",
  "applies_to": [
    "standard_letter",
    "multiple_address_letter",
    "endorsement",
    "joint_letter",
    "memorandum_for_record",
    "from_to_memo",
    "plain_paper_memo",
    "letterhead_memo"
  ],
  "component_scope": [
    "navy",
    "marine_corps",
    "joint",
    "don_secretariat"
  ],
  "rule_text_summary": "Exact or closely paraphrased imperative rule text.",
  "enforcement": "deterministic",
  "validator": "cci_xxx_validate.py",
  "severity": "error",
  "manual_chapter": "N",
  "manual_section": "X",
  "page_or_figure": null,
  "source_quote": "Exact quoted sentence from the manual.",
  "effective_date": "YYYY-MM-DD",
  "added_by_implementation_id": "imp_YYYYMMDD_HHHHHHHH",
  "implementation_target": "rule_catalog",
  "implementation_status": "active"
}
```

### 10.2 Required Provenance Fields

| Field | Required | Notes |
|---|---|---|
| `rule_id` | Yes | Must not collide with existing IDs in the same JSON file. |
| `source` | Yes | Always `SECNAV M-5216.5` for manual-derived rules. |
| `source_type` | Yes | Prefer `narrative_text` or `narrative_and_figure_text`. Avoid `implementation_note` for new rules unless the rule is explicitly a cross-reference. |
| `source_location` | Yes | Chapter, paragraph, and subparagraph if applicable. |
| `applies_to` | Yes | Must include at least `standard_letter`, `multiple_address_letter`, `endorsement`, `joint_letter`. Add memo types if the manual text covers them. |
| `component_scope` | Yes | Must include `navy`, `marine_corps`, `joint`, `don_secretariat`. |
| `rule_text_summary` | Yes | Must be a deterministic directive, not a vague description. |
| `enforcement` | Yes | For H.3 pilots, must be `deterministic`. Heuristic rules require additional false-positive assessment and are deferred to later phases. |
| `validator` | Yes | Must name the existing validator module that would eventually enforce this rule, even if the H.3 pilot does not modify that validator. |
| `severity` | Yes | For H.3 pilots, prefer `error` if the manual uses imperative language (`shall`, `must`, `do not`). Use `warning` only if the manual uses advisory language (`should`, `avoid`). |
| `manual_chapter` | Yes | Numeric chapter string. |
| `manual_section` | Yes | Paragraph or section string. |
| `page_or_figure` | No | Set to `null` if no specific figure is referenced. Include figure number only if the figure text itself contains the directive. |
| `source_quote` | Yes | Exact quoted sentence. Must be verifiable by opening the manual to the cited location. |
| `effective_date` | Yes | Date of implementation or manual effective date. |
| `added_by_implementation_id` | Yes | The `implementation_id` from the Phase H planner. |
| `implementation_target` | Yes | For H.3, always `rule_catalog`. |
| `implementation_status` | Yes | Always `active` on creation. |

---

## 11. Required Targeted Regression Runner

### 11.1 Runner Requirements

A new targeted regression runner must be created:

- **File:** `tools/run_phase_h3_second_rule_catalog_regression.py`
- **Checks:** Minimum 10 checks, recommended 11–15.
- **Scope:** Catalog schema validation, entry presence, provenance fields, no unexpected file mutations.

### 11.2 Recommended Check List

| Check | Description |
|---|---|
| 01 | Catalog JSON is valid and parseable. |
| 02 | New rule ID is present and unique within the file. |
| 03 | `source` field equals `SECNAV M-5216.5`. |
| 04 | `source_location` is non-empty and contains a chapter reference. |
| 05 | `rule_text_summary` is non-empty and contains an imperative verb. |
| 06 | `enforcement` equals `deterministic`. |
| 07 | `implementation_target` equals `rule_catalog`. |
| 08 | `implementation_status` equals `active`. |
| 09 | `added_by_implementation_id` is non-empty and matches the expected synthetic record ID. |
| 10 | `source_quote` is non-empty and is a direct quote from the manual (verified by string length and keyword presence). |
| 11 | No validator files were modified in the commit. |
| 12 | No renderer/layout files were modified in the commit. |
| 13 | No prompt-contract files were modified in the commit. |
| 14 | No command-layer files were modified in the commit. |
| 15 | Existing regression runners (26 suites) still pass. |

### 11.3 Runner Safety

- The runner must use synthetic fixtures only.
- The runner must not read or write real user data.
- The runner must not depend on local pending/approved logs.
- The runner must be runnable with the explicit Pinokio/Miniconda Python path.

---

## 12. Full 27-Suite Regression Expectation

If the H.3 pilot adds one new targeted runner, the regression set becomes **27 suites**:

| Suite | Runner File | Checks (approx) |
|---|---|---|
| 1 | `run_phase_h3_second_rule_catalog_regression.py` | 11–15 (new) |
| 2 | `run_phase_h2_subject_acronym_validator_regression.py` | 12 |
| 3 | `run_pilot_subject_acronym_rule_catalog_regression.py` | 11 |
| 4 | `run_correction_implementation_regression.py` | 45 |
| 5 | `run_correction_nl_command_regression.py` | 151 |
| 6 | `run_correction_command_regression.py` | 45 |
| 7 | `run_correction_review_regression.py` | 30 |
| 8 | `run_correction_pending_regression.py` | 33 |
| 9 | `run_correction_profile_promotion_regression.py` | 33 |
| 10 | `run_correction_classify_regression.py` | varies |
| 11 | `run_intake_regression.py` | varies |
| 12 | `run_correction_regression.py` | varies |
| 13 | `run_correction_session_regression.py` | varies |
| 14 | `run_profile_regression.py` | varies |
| 15 | `run_cci_audit_regression.py` | varies |
| 16 | `run_context_schema_regression.py` | varies |
| 17 | `run_cci_subject_regression.py` | varies |
| 18 | `run_cci_ref_encl_regression.py` | varies |
| 19 | `run_cci_acronym_regression.py` | varies |
| 20 | `run_cci_date_time_regression.py` | varies |
| 21 | `run_cci_personnel_regression.py` | varies |
| 22 | `run_cci_poc_regression.py` | varies |
| 23 | `run_cci_routing_regression.py` | varies |
| 24 | `run_c7_phase1_regression.py` | varies |
| 25 | `run_c8_regression.py` | varies |
| 26 | `run_c9_regression.py` | varies |
| 27 | `run_c10_regression.py` | varies |

**All 27 suites must pass before any H.3 implementation commit.**

---

## 13. Files That May Be Modified in Future Implementation

If this plan is approved and implementation proceeds, the following files **may** be modified:

| File | Change Type | Reason |
|---|---|---|
| `rules_v6/CCI/*.json` | Append one new rule object | Catalog entry for the selected rule. |
| `tools/run_phase_h3_second_rule_catalog_regression.py` | Create new file | Targeted regression runner for the H.3 pilot. |
| `docs/PROJECT_STATUS.md` | Update | Reflect new baseline, regression count, and milestone. |
| `docs/planning/phase_h3_second_rule_catalog_pilot_plan.md` | Update | Mark sections as implemented, add commit references, resolve open questions. |
| `docs/checkpoints/phase_h3_second_rule_catalog_pilot_checkpoint.md` | Create new file | Post-implementation checkpoint. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Update | Update baseline and next-phase target. |

---

## 14. Files That Must Not Be Modified

| File | Reason |
|---|---|
| `src/cci_subject_validate.py` | H.3 is rule-catalog-only; no validator changes. |
| `src/cci_acronym_validate.py` | Body validator must remain untouched. |
| `src/cci_ref_encl_validate.py` | No validator changes in H.3. |
| `src/cci_date_time_validate.py` | No validator changes in H.3. |
| `src/cci_personnel_validate.py` | No validator changes in H.3. |
| `src/cci_poc_validate.py` | No validator changes in H.3. |
| `src/cci_routing_validate.py` | No validator changes in H.3. |
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract changes. |
| `src/correction_commands.py` | No command-layer changes. |
| `src/correction_nl_commands.py` | No command-layer changes. |
| `src/correction_implementation_planner.py` | No planner logic changes; only `mark_implemented()` usage. |
| `corrections/pending_corrections.jsonl` | Must remain gitignored; do not commit. |
| `corrections/approved_rule_promotions.json` | Must remain gitignored; do not commit. |
| `profiles/*.json` (real profiles) | Must remain outside repository or gitignored. |
| `docs/BOOTSTRAP.md` | Do not modify. |
| `docs/HERMES_INSTRUCTIONS.md` | Do not modify. |

---

## 15. Safety Constraints

These constraints apply to Phase H.3 implementation and are non-negotiable:

| Constraint | Enforcement |
|---|---|
| No validator changes | `src/cci_*_validate.py` must not appear in the commit diff. |
| No renderer/layout changes | `src/pdf_v6_render.py` and layout profiles must not appear in the commit diff. |
| No runtime prompt-contract changes | `src/context_resolver.py` must not appear in the commit diff. |
| No Phase F/G command-layer changes | `src/correction_commands.py`, `src/correction_nl_commands.py` must not appear in the commit diff. |
| No automatic enforcement from approved logs | The rule catalog entry is documentation only; no runtime code reads the catalog and enforces it automatically. |
| No AI-only implementation | All decisions must be traceable to manual text and deterministic criteria. |
| No approved/pending logs committed | `.gitignore` must continue to exclude `corrections/pending_corrections.jsonl` and `corrections/approved_rule_promotions.json`. |
| No real command/user data committed | All fixtures must be synthetic; no real names, commands, or contact data. |
| No background automation | No cron jobs, auto-apply scripts, or silent rule activation. |

---

## 16. Rollback Plan

If the H.3 pilot must be rolled back:

1. **Revert the catalog entry** — remove the single JSON object from the target `rules_v6/CCI/*.json` file.
2. **Delete the runner** — remove `tools/run_phase_h3_second_rule_catalog_regression.py`.
3. **Revert documentation** — revert `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` to the pre-H.3 state.
4. **Delete the checkpoint** — remove `docs/checkpoints/phase_h3_second_rule_catalog_pilot_checkpoint.md` if created.
5. **Restore baseline** — ensure `609821e` (or the then-current baseline) is restored as the functional baseline in all docs.
6. **Verify regression** — run the 26 pre-H.3 suites and confirm all pass.

Rollback should require **no more than 4 file deletions/reverts and one regression run**.

---

## 17. Open Questions Needing Approval

| # | Question | Default if unanswered |
|---|---|---|
| 1 | **Which rule domain should be searched first?** (subject, ref/encl, date/time, personnel, routing, other) | Default: ref/encl or date/time — both have explicit Chapter 2/7 text and existing validators that can be named without modification. |
| 2 | **Should the candidate come from the existing pending log, or from a fresh manual review?** | Default: pending log first, fresh manual review only if no suitable pending candidate exists. |
| 3 | **What severity should the new catalog entry use?** (`error` vs `warning`) | Default: `error` if the manual uses imperative language; `warning` only if the manual uses advisory language. |
| 4 | **Should the new rule ID follow the existing chapter-based convention** (`CCI-CH7-XXX` for Chapter 7 rules, `CCI-CH2-XXX` for Chapter 2 rules)? | Default: yes — maintain consistency with existing ID scheme. |
| 5 | **Should the targeted runner include a check that verifies the new catalog entry does NOT trigger any existing validator** (to prove the rule is catalog-only)? | Default: yes — add a check that runs the relevant existing validator against a synthetic fixture and confirms no new errors/warnings appear. |
| 6 | **Is a 27-suite regression gate acceptable, or should the H.3 runner be integrated into an existing runner to keep the count at 26?** | Default: 27 suites is acceptable — a separate runner makes the pilot independently verifiable and deletable. |
| 7 | **Should the H.3 pilot be blocked if any open Phase H.2 follow-up work remains** (e.g., expanding `PROHIBITED_SUBJECT_ACRONYMS`, promoting `SUBJ-007` to warning)? | Default: no — H.3 is independent of H.2 follow-ups. H.2 expansion and H.3 pilot may proceed in parallel planning, but only one may be implemented at a time. |
| 8 | **Should the approved record for H.3 use a real pending candidate ID, or a synthetic test record?** | Default: synthetic test record only for planning and regression; real pending candidate must be used for actual implementation. |

---

## 18. Recommended Second-Pilot Candidate Search Strategy

### 18.1 Immediate Next Step (No Implementation)

1. **Inspect the pending candidate log** for any candidate with:
   - `proposed_scope`: `global_rule` or `validator_gap`
   - `sanitized`: `true`
   - A clear manual chapter/paragraph reference
   - A short imperative rule statement

2. **If none found**, inspect existing rule catalog files for gaps:
   - Compare `cci_ch2_date_time_rules.json` against `cci_date_time_validate.py` to find enforced rules without catalog entries.
   - Compare `cci_ch2_personnel_rules.json` against `cci_personnel_validate.py`.
   - Compare `cci_ch7_ref_encl_rules.json` against `cci_ref_encl_validate.py`.

3. **If a gap is found**, verify the manual source text and document the provenance.

4. **If no gap is found**, perform a focused manual-text review of Chapter 2, paragraph 2-4.2 (date/time) or Chapter 7, paragraph 7-3.3 (ref/encl) for an explicit directive not yet cataloged.

### 18.2 Preferred First Candidate (Speculative)

A **reference/enclosure sequencing rule** from Chapter 7, paragraph 7-3.3 is a strong candidate because:

- The text is explicit: "References must be listed in the order of their first appearance or substantive citation in the body."
- The rule is deterministic — citation order can be compared to listing order.
- The existing validator (`cci_ref_encl_validate.py`) already enforces `CCI-REF-003` and `CCI-REF-004`.
- A catalog entry for a related but **not yet cataloged** sequencing sub-rule (e.g., "Endorsement continuation references must continue the prior sequence without restarting") could be rule-catalog-only and low blast radius.

**However, this is a speculative recommendation only.** The actual candidate must be selected through the workflow in Section 7 and approved through the gates in Section 8.

---

## 19. Recommended Implementation Target

| Attribute | Value |
|---|---|
| Implementation target | `rule_catalog` |
| Target file | `rules_v6/CCI/*.json` (exact file determined by candidate domain) |
| Validator named but not modified | Yes — the `validator` field must name the relevant existing `cci_*_validate.py` module |
| Enforcement level | Documentation only — no runtime code reads the catalog |
| Severity | `error` or `warning` based on manual language |

---

## 20. Recommended Regression Coverage

| Level | Runner | Checks |
|---|---|---|
| Targeted | `tools/run_phase_h3_second_rule_catalog_regression.py` | 11–15 |
| Full gate | All 26 existing suites + H.3 targeted runner | 27 suites total |
| Python interpreter | `C:\Users\drryl\pinokio\bin\miniconda\python.exe` | Required for C7–C10 layout suites |
| Fixture requirement | Synthetic only | No real data |

---

## 21. Open Questions Needing Approval (Summary)

1. Which rule domain to search first?
2. Pending log vs. fresh manual review vs. validator gap?
3. Severity level for the new catalog entry?
4. Rule ID naming convention consistency?
5. Should the runner verify no new validator behavior?
6. Is 27-suite regression gate acceptable?
7. Should H.3 be blocked by H.2 follow-ups?
8. Synthetic vs. real approved record for implementation?

---

**End of Phase H.3 / Phase I.2 — Second Low-Risk Rule-Catalog-Only Pilot Plan.**

*Planning document only. No implementation authorized without separate user approval.*
