# Phase H.8 / Phase I.7 — Third Low-Risk Rule-Catalog-Only Pilot Plan

**Date:** 2026-06-08  
**Latest Docs Checkpoint:** `1e16493` — `Docs: Record Phase H.7 evidence review checkpoint`  
**Current Functional Baseline:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`  
**Current Regression Set:** 29 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until reviewed and approved. No code may be written under this plan without separate user approval.  
**Scope:** Decide whether to select the proposed `CCI-ROUTE-011` From-line required rule as the third low-risk rule-catalog-only pilot, or reject it in favor of a different candidate or a different direction entirely.

---

## 1. Why Phase H.8 Should Prefer a Third Catalog Pilot Over Severity Promotion or Feature-Flag Work

### 1.1 Evidence from Prior Phases

| Phase | Scope | Risk Level | Regression Suites | Outcome |
|---|---|---|---|---|
| H.1 | Rule-catalog only (subject acronym) | Very low | 25 | PASS — clean workflow proof |
| H.2 | Validator advisory enforcement (subject acronym) | Low-medium | 26 | PASS — required curated token list, false-positive analysis, fixture expansion |
| H.3 | Rule-catalog only (office code) | Very low | 27 | PASS — clean second catalog pilot |
| H.4 | Validator advisory enforcement (office code) | Low-medium | 28 | PASS — required delimiter-scope analysis, copy-to exclusion |
| H.5 | Planning-only severity review | Zero | 28 | APPROVED — keep advisory-only |
| H.6 | Evidence collection (fixtures + corpus) | Low | 29 | PASS — 20 negative + 10 positive controls added |
| H.7 | Evidence review + decision | Zero | 29 | APPROVED — keep advisory; productive alternative identified |

### 1.2 Why Not Severity Promotion

- `CCI-ROUTE-010` severity promotion requires:
  1. Real-world Navy/Marine Corps usage evidence (not yet available)
  2. Feature flag/config mechanism design and implementation (conceptual only)
  3. Explicit user approval
  4. New regression checks for warning/error behavior
  5. Full 29-suite gate before commit
- The H.7 plan explicitly deferred severity promotion indefinitely.
- Additional synthetic evidence without real-world feedback has diminishing returns.

### 1.3 Why Not Feature-Flag/Config Design

- Feature-flag design is valuable but premature if no severity promotion is imminent.
- H.7 identified feature-flag work as a possible direction but ranked it below a third catalog pilot for immediate value.
- Config support affects the entire validator architecture; a third catalog pilot is narrower and safer.

### 1.4 Why a Third Catalog Pilot Is Preferred

- Two catalog pilots (`CCI-CH7-SUBJ-006`, `CCI-ROUTE-010`) have proven the workflow is repeatable.
- A third pilot expands CCI coverage **horizontally** into a new rule domain rather than deepening risk on one existing rule.
- Catalog-only work has zero validator blast radius, zero renderer risk, zero prompt-contract risk.
- It validates the end-to-end workflow again (candidate selection → Phase E review → Phase H claim/plan → catalog entry → `mark_implemented()` → regression) with a fresh rule family.
- It keeps the learning curve flat and builds organizational confidence in the approved-rule pipeline.

---

## 2. Candidate Under Review: CCI-ROUTE-011

### 2.1 Proposed Rule

| Attribute | Value |
|---|---|
| **Proposed rule ID** | `CCI-ROUTE-011` |
| **Rule text** | Every standard letter must have a "From:" line, except a letter that will be used with a window envelope. |
| **Window-envelope exception** | Letters used with window envelopes omit the From line because the sender's address shows through the window. |
| **Domain** | `routing.from` |
| **Deterministic test** | Presence/absence of `routing.from` field in standard-letter payload, with an override for `window_envelope=true`. |
| **SECNAV source** | SECNAV M-5216.5, Chapter 7, paragraph 7-2.5a |
| **Manual quote** | "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope." |

### 2.2 Candidate Status

**This candidate is NOT approved.** It is proposed for evaluation only. The sections below analyze whether it should be accepted, rejected, or replaced with a different candidate.

---

## 3. SECNAV Source and Provenance Requirements

### 3.1 Required Provenance Fields for CCI-ROUTE-011 (If Approved)

| Field | Required Value |
|---|---|
| `source` | `SECNAV M-5216.5` |
| `source_type` | `narrative_text` |
| `source_location` | `Chapter 7, paragraph 7-2.5a` |
| `manual_chapter` | `7` |
| `manual_section` | `7-2.5a` |
| `page_or_figure` | `null` (narrative text rule) |
| `source_quote` | `"Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope."` |

### 3.2 Provenance Verification Checklist (Before Approval)

- [ ] Open SECNAV M-5216.5 Chapter 7, paragraph 7-2.5a and confirm the exact quoted sentence exists.
- [ ] Confirm no conflicting text in nearby paragraphs (7-2.5b, 7-2.5c, 7-2.6) that would contradict the rule or the exception.
- [ ] Confirm the figure examples in Chapter 7 show a From line on standard letters.
- [ ] Verify whether "standard letter" in this context explicitly excludes memorandums, endorsements, or joint letters — the rule may need `applies_to` scoping.

### 3.3 Provenance Risk Assessment

- **Low risk** — Chapter 7 paragraph 7-2.5a is a well-known standard-letter formatting paragraph.
- **Medium risk** — the window-envelope exception is explicit, which means the rule is not unconditional. This is manageable but must be documented.
- **Open question:** Does the same From-line requirement exist in Chapter 2 (preparation rules) with different wording? Cross-checking both chapters is required.

---

## 4. Whether the Window-Envelope Exception Makes the Candidate Too Complex for Catalog-Only

### 4.1 Exception Complexity Analysis

The window-envelope exception is **not** a complexity barrier for a catalog-only entry. A rule-catalog entry can and should document exceptions explicitly. The catalog does not execute code; it records the rule text and its exceptions.

### 4.2 Catalog Representation of the Exception

The `rule_text_summary` field would contain the full rule including the exception:

```
"Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope."
```

No additional schema field is needed for the exception. The exception is part of the rule text.

### 4.3 Future Validator Complexity (If Ever Implemented)

If a future phase (e.g., H.9 / I.8) proposes validator enforcement for this rule, the exception would require:
- A `window_envelope` flag in the payload or context.
- A conditional check: if `window_envelope == true`, skip the From-line requirement.
- This is straightforward and does not make the catalog entry itself complex.

### 4.4 Verdict

**The window-envelope exception does NOT make this candidate too complex for catalog-only.** It is a simple, explicit exception that can be documented verbatim in the catalog entry.

---

## 5. Whether the Rule Is Deterministic Enough for Catalog Entry

### 5.1 Determinism Assessment

| Aspect | Assessment |
|---|---|
| **Trigger condition** | `routing.from` is absent or empty in a standard letter. |
| **Exception condition** | Payload indicates `window_envelope=true`. |
| **Subjective judgment required?** | No. Presence/absence of a field is a boolean test. |
| **Manual interpretation required?** | Minimal — only the window-envelope exception requires a flag. |
| **Risk of false positives?** | Low for catalog entry (documentation only). For future validator, low if window-envelope flag is reliable. |

### 5.2 Comparison to Existing Catalog Pilots

| Pilot | Determinism | Exception Handling |
|---|---|---|
| H.1 `CCI-CH7-SUBJ-006` | High — acronym presence in subject is boolean | None |
| H.3 `CCI-ROUTE-010` | High — numeric vs letter-starting code is regex-testable | None |
| Proposed `CCI-ROUTE-011` | High — From-line presence is boolean | One explicit exception (window envelope) |

### 5.3 Verdict

**The rule is deterministic enough for catalog entry.** The exception is explicit and does not introduce subjective judgment.

---

## 6. Whether There Is Any Renderer/Layout Implication

### 6.1 Layout Impact Assessment

| Aspect | Impact |
|---|---|
| **From-line presence** | The renderer already supports `routing.from`; it renders the From line when present. |
| **From-line absence** | The renderer already supports omitting the From line (used for memorandums, MFRs, etc.). |
| **Window envelope** | The renderer does not need to know about window envelopes for layout purposes; the absence of a From line is sufficient. |
| **Margin/spacing changes** | None. The From line occupies the same vertical space whether present or absent. |
| **Font changes** | None. |
| **New render target** | None. |

### 6.2 Verdict

**No renderer/layout implication.** The rule is about field presence, not spatial positioning, font metrics, or page geometry. The renderer already handles both present and absent `routing.from` fields for other document types.

---

## 7. Whether the Rule Overlaps Existing Routing Rules

### 7.1 Overlap Analysis with Existing `cci_ch2_routing_rules.json` Entries

| Existing Rule | Topic | Overlap with CCI-ROUTE-011? |
|---|---|---|
| `CCI-ROUTE-001` | Via numbering | None |
| `CCI-ROUTE-002` | Via consecutive numbering | None |
| `CCI-ROUTE-003` | Single Via should not be numbered | None |
| `CCI-ROUTE-004` | Via specific addressees vs generic phrases | None |
| `CCI-ROUTE-005` | Copy-to need-to-know limits | None |
| `CCI-ROUTE-006` | Copy-to specificity | None |
| `CCI-ROUTE-007` | To/Via vs Copy-to duplication | None |
| `CCI-ROUTE-008` | Four or fewer action addressees format | None |
| `CCI-ROUTE-009` | To-plus-Distribution group title | None |
| `CCI-ROUTE-010` | Office code prefix (Code before numbers) | None |

### 7.2 Verdict

**No overlap with existing routing rules.** `CCI-ROUTE-011` would be the first catalog entry addressing the `routing.from` field specifically. All existing entries address `to`, `via`, `copy_to`, or distribution formatting.

---

## 8. Whether `cci_routing_validate.py` Can Be Named as Existing Validator Domain Without Modifying It

### 8.1 Existing Validator Structure

The `src/cci_routing_validate.py` validator currently checks:
- Via numbering and consecutiveness
- To/Via duplication with Copy-to
- Office code prefix (`CCI-ROUTE-010`, Phase H.4)
- Various heuristic routing warnings

### 8.2 Naming Without Modification

For a **catalog-only** pilot, the `validator` field in the catalog entry names the module that **would eventually enforce** the rule, even if the current pilot does not modify that module. This is the same pattern used by H.1 and H.3:

- `CCI-CH7-SUBJ-006` names `validator: "cci_subject"` but H.1 did not modify `cci_subject_validate.py`.
- `CCI-ROUTE-010` names `validator: "cci_routing"` but H.3 did not modify `cci_routing_validate.py`.

### 8.3 Verdict

**Yes.** `cci_routing_validate.py` can be named as the validator domain in the catalog entry without modifying the file. This follows the established H.1/H.3 catalog-only pilot pattern.

---

## 9. Whether Target Catalog File Should Be `rules_v6/CCI/cci_ch2_routing_rules.json`

### 9.1 File Selection Criteria

| Criterion | Assessment |
|---|---|
| Rule domain | `routing.from` — routing field family |
| Manual chapter | Chapter 7 (standard letters), but Chapter 2 also covers routing conventions |
| Existing routing catalog | `rules_v6/CCI/cci_ch2_routing_rules.json` contains all routing rules (001–010) |
| Existing subject catalog | `rules_v6/CCI/cci_ch7_subject_rules.json` contains subject rules |

### 9.2 Decision

**Yes, `rules_v6/CCI/cci_ch2_routing_rules.json` is the correct target file.**

Rationale:
- All existing routing rules (001–010) live in this file, regardless of whether their manual source is Chapter 2 or Chapter 7.
- `CCI-ROUTE-010` (Chapter 7 source) is already in `cci_ch2_routing_rules.json`, establishing precedent.
- The file's `_catalog_id` is `CCI-CH2-ROUTING` and its title is "Routing, Via, Copy-to, and Distribution Intelligence" — the From line is a routing element.
- Adding `CCI-ROUTE-011` to this file keeps routing rules co-located and discoverable.

---

## 10. Required Rule-Catalog Schema and Proposed Fields

### 10.1 Schema Compliance

The new entry must follow the same schema as `CCI-ROUTE-010`:

```json
{
  "rule_id": "CCI-ROUTE-011",
  "source": "SECNAV M-5216.5",
  "source_type": "narrative_text",
  "source_location": "Chapter 7, paragraph 7-2.5a",
  "applies_to": [
    "standard_letter",
    "multiple_address_letter",
    "endorsement",
    "joint_letter"
  ],
  "component_scope": [
    "navy",
    "marine_corps",
    "joint",
    "don_secretariat"
  ],
  "rule_text_summary": "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope.",
  "enforcement": "deterministic",
  "validator": "cci_routing",
  "severity": "error",
  "manual_chapter": "7",
  "manual_section": "7-2.5a",
  "page_or_figure": null,
  "source_quote": "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope.",
  "effective_date": "YYYY-MM-DD",
  "added_by_implementation_id": "imp_YYYYMMDD_HHHHHHHH",
  "implementation_target": "rule_catalog",
  "implementation_status": "active"
}
```

### 10.2 Required Provenance Fields

| Field | Required | Notes |
|---|---|---|
| `rule_id` | Yes | Must not collide with `CCI-ROUTE-001` through `CCI-ROUTE-010`. |
| `source` | Yes | `SECNAV M-5216.5` |
| `source_type` | Yes | `narrative_text` |
| `source_location` | Yes | `Chapter 7, paragraph 7-2.5a` |
| `applies_to` | Yes | Must include `standard_letter` and `multiple_address_letter`. Memorandum types may be excluded if the manual text is specific to standard letters. Endorsements and joint letters should be included if they use standard-letter format. |
| `component_scope` | Yes | `navy`, `marine_corps`, `joint`, `don_secretariat` |
| `rule_text_summary` | Yes | Must include the full rule including the window-envelope exception. |
| `enforcement` | Yes | `deterministic` for catalog-only pilot. |
| `validator` | Yes | `cci_routing` — names the existing validator module without modifying it. |
| `severity` | Yes | `error` — the manual uses imperative language ("must have"). |
| `manual_chapter` | Yes | `7` |
| `manual_section` | Yes | `7-2.5a` |
| `page_or_figure` | No | `null` — no specific figure referenced. |
| `source_quote` | Yes | Exact quoted sentence including the exception clause. |
| `effective_date` | Yes | Date of implementation commit. |
| `added_by_implementation_id` | Yes | The `implementation_id` from the Phase H planner. |
| `implementation_target` | Yes | `rule_catalog` for this pilot. |
| `implementation_status` | Yes | `active` on creation. |

### 10.3 Open Schema Question

Should `applies_to` include `memorandum_for_record`, `from_to_memo`, `plain_paper_memo`, and `letterhead_memo`? The manual text says "standard letter," which technically excludes memorandums (they have a different format, often with no From line or a different originator block). This must be verified by opening the manual to 7-2.5a and checking whether the surrounding paragraphs scope this rule to standard letters only.

**Default:** include only `standard_letter`, `multiple_address_letter`, `endorsement`, and `joint_letter` unless manual review confirms memorandums are also covered.

---

## 11. Required Targeted Regression Runner and Minimum Checks

### 11.1 Runner File

- **File:** `tools/run_phase_h8_third_rule_catalog_regression.py`
- **Checks:** Minimum 10, recommended 11–15.
- **Scope:** Catalog schema validation, entry presence, provenance fields, no unexpected file mutations.

### 11.2 Recommended Check List

| Check | Description |
|---|---|
| 01 | Catalog JSON is valid and parseable. |
| 02 | `CCI-ROUTE-011` is present and unique within the file (no collision with 001–010). |
| 03 | `source` field equals `SECNAV M-5216.5`. |
| 04 | `source_location` is non-empty and contains `Chapter 7, paragraph 7-2.5a`. |
| 05 | `rule_text_summary` is non-empty and contains the word `From`. |
| 06 | `rule_text_summary` contains the window-envelope exception text (`window envelope` or `except`). |
| 07 | `enforcement` equals `deterministic`. |
| 08 | `implementation_target` equals `rule_catalog`. |
| 09 | `implementation_status` equals `active`. |
| 10 | `severity` equals `error`. |
| 11 | `added_by_implementation_id` is non-empty and matches expected synthetic record ID. |
| 12 | `source_quote` is non-empty and is a direct quote from the manual. |
| 13 | No validator files were modified in the commit. |
| 14 | No renderer/layout files were modified in the commit. |
| 15 | Existing regression runners (29 suites) still pass. |

### 11.3 Runner Safety

- The runner must use synthetic fixtures only.
- The runner must not read or write real user data.
- The runner must not depend on local pending/approved logs.
- The runner must be runnable with the explicit Pinokio/Miniconda Python path.

---

## 12. Future Regression Gate

### 12.1 Current Gate (No Changes)

- **Gate:** 29 suites
- **Status:** All PASS

### 12.2 If H.8 Implements a Third Catalog Pilot

- **Gate becomes:** 30 suites
- **New runner:** `tools/run_phase_h8_third_rule_catalog_regression.py`
- **All existing 29 suites must still pass.**

### 12.3 If H.8 Remains Planning-Only

- **Gate remains:** 29 suites
- **No code changes.**
- **No new runner.**
- **All 29 suites must still pass before any future commit.**

---

## 13. Phase D → Phase E → Phase H Workflow Required Before Implementation

### 13.1 Phase D — Pending Global Rule Candidate Logging (If Not Already Logged)

If `CCI-ROUTE-011` is approved as the candidate, the workflow requires:

1. A synthetic pending candidate record is created locally (if one does not already exist in `corrections/pending_corrections.jsonl`) with:
   - `proposed_scope`: `global_rule`
   - `sanitized`: `true`
   - `correction_reason` or `proposed_rule_text` citing `Chapter 7, paragraph 7-2.5a`
2. The pending candidate remains local/gitignored and is NOT committed.

### 13.2 Phase E — Review/Promotion Utility

1. A human reviewer claims the candidate via `claim_record_for_review()`.
2. The reviewer verifies provenance (Chapter 7, paragraph 7-2.5a, exact quote).
3. The reviewer confirms determinism (boolean presence test, explicit exception).
4. The reviewer confirms blast radius (single field, no renderer/layout implication).
5. The reviewer confirms no duplicate existing catalog entry.
6. The reviewer approves the candidate with `review_status="approved_for_implementation"` and `implementation_status="pending_implementation"`.
7. The approved record is written to the local approved log only (gitignored, NOT committed).

### 13.3 Phase H — Implementation Planner

1. The implementer claims the approved record via `claim_record_for_implementation()`.
2. The implementer calls `plan_implementation()` with:
   - `implementation_target`: `rule_catalog`
   - `target_file`: `rules_v6/CCI/cci_ch2_routing_rules.json`
   - `source_verification_summary`: provenance confirmation
3. The planner creates an `implementation_planned` record.
4. After catalog entry is written and all 30 suites pass, the implementer calls `mark_implemented()` with the implementation commit hash.
5. The approved record status transitions to `implemented` locally (gitignored, NOT committed).

### 13.4 Phase H.8 Planning Constraint

For the H.8 pilot, the `implementation_target` **must** be `rule_catalog`. Any plan proposing `validator`, `prompt_contract`, or `renderer` as the target must be rejected and redirected to a separate future planning phase (e.g., H.9 / I.8).

---

## 14. Files That May Be Modified in Future Implementation

If this plan is approved and implementation proceeds:

| File | Change Type | Reason |
|---|---|---|
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Append one new rule object | Catalog entry for `CCI-ROUTE-011`. |
| `tools/run_phase_h8_third_rule_catalog_regression.py` | Create new file | Targeted regression runner for the H.8 pilot. |
| `docs/PROJECT_STATUS.md` | Update | Reflect new baseline, regression count (30), milestone. |
| `docs/planning/phase_h8_third_catalog_pilot_plan.md` | Update | Mark sections as implemented, add commit references, resolve open questions. |
| `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` | Create new file | Post-implementation checkpoint. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Update | Update baseline and next-phase target. |

---

## 15. Files That Must Not Be Modified

| File | Reason |
|---|---|
| `src/cci_routing_validate.py` | H.8 is rule-catalog-only; no validator changes. |
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract runtime changes. |
| `src/intake_orchestrator.py` | No intake orchestration changes unless separately approved. |
| `src/validator_runner.py` | No validator runner contract changes unless separately approved. |
| `src/correction_commands.py` | No Phase F command-layer changes. |
| `src/correction_nl_commands.py` | No Phase G command-layer changes. |
| `src/correction_implementation_planner.py` | No planner logic changes; only `mark_implemented()` usage. |
| `src/cci_subject_validate.py` | No subject validator changes. |
| `src/cci_acronym_validate.py` | No acronym validator changes. |
| `src/cci_ref_encl_validate.py` | No ref/encl validator changes. |
| `src/cci_date_time_validate.py` | No date/time validator changes. |
| `src/cci_personnel_validate.py` | No personnel validator changes. |
| `src/cci_poc_validate.py` | No POC validator changes. |
| `corrections/approved_rule_promotions.json` | Remains local/gitignored; do not commit. |
| `corrections/pending_corrections.jsonl` | Remains local/gitignored; do not commit. |
| `corrections/session/*.jsonl` | Remains local/gitignored; do not commit. |
| `corrections/evidence/*` | Remains local/gitignored; do not commit. |
| Any real command/user profile | Do not commit contact data or local profiles. |
| `docs/BOOTSTRAP.md` | Do not modify. |
| `docs/HERMES_INSTRUCTIONS.md` | Do not modify. |

---

## 16. What Phase H.8 Must NOT Do

Phase H.8 is a **planning-only phase** unless explicitly approved for implementation. It must NOT:

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **No validator changes** | `src/cci_routing_validate.py` must remain untouched. Catalog-only pilot does not add runtime enforcement. |
| 2 | **No renderer/layout changes** | `src/pdf_v6_render.py` must remain untouched. No x/y, margin, font, or spacing changes. |
| 3 | **No prompt-contract changes** | `src/context_resolver.py` must remain untouched. No runtime prompt template changes. |
| 4 | **No Phase F/G command-layer changes** | No new slash commands or NL command mappings for From-line management or window-envelope toggling. |
| 5 | **No automatic enforcement from approved logs** | The catalog entry is documentation only; no runtime code reads the catalog and enforces it automatically. |
| 6 | **No severity promotion of `CCI-ROUTE-010`** | H.7 already approved keeping `CCI-ROUTE-010` advisory-only. H.8 must not revisit or override that decision. |
| 7 | **No feature flag/config implementation** | Feature-flag support remains conceptual only. No config files, environment variables, or severity override mechanisms may be added. |
| 8 | **No approved/pending/session logs committed** | All correction storage remains local/gitignored. |
| 9 | **No real command/user data committed** | All fixtures must be synthetic. No real names, commands, or contact data. |
| 10 | **No background automation** | No cron jobs, watchers, or CI triggers for rule activation. |
| 11 | **No AI-only implementation decisions** | Candidate selection, approval, and implementation target require human approval. |
| 12 | **No multi-record batch implementation** | The pilot is one record only. |

---

## 17. Rollback Plan

If the H.8 pilot must be rolled back after implementation:

1. **Revert the catalog entry** — remove the single JSON object for `CCI-ROUTE-011` from `rules_v6/CCI/cci_ch2_routing_rules.json`.
2. **Delete the runner** — remove `tools/run_phase_h8_third_rule_catalog_regression.py`.
3. **Revert documentation** — revert `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` to the pre-H.8 state.
4. **Delete the checkpoint** — remove `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` if created.
5. **Restore baseline** — ensure `662afbb` (or the then-current baseline) is restored as the functional baseline in all docs.
6. **Verify regression** — run the 29 pre-H.8 suites and confirm all pass.

Rollback should require **no more than 4 file deletions/reverts and one regression run**.

---

## 18. Open Questions Needing Approval

| # | Question | Default if Unanswered |
|---|---|---|
| 1 | **Should `CCI-ROUTE-011` (From-line required) be accepted as the third catalog pilot, or rejected in favor of a different candidate?** | Default: **ACCEPT** — the candidate is low-risk, deterministic, well-sourced, and does not overlap existing rules. |
| 2 | **If accepted, should the `applies_to` list include memorandum types, or is it standard-letter only?** | Default: standard-letter only unless manual review at 7-2.5a explicitly includes memorandums. |
| 3 | **Should the targeted runner verify that `CCI-ROUTE-011` does NOT trigger any existing validator (to prove catalog-only isolation)?** | Default: yes — add a check that runs `cci_routing_validate` against a synthetic fixture and confirms no new errors/warnings appear. |
| 4 | **Should the window-envelope exception be documented in a separate catalog field (e.g., `exceptions`), or is inclusion in `rule_text_summary` sufficient?** | Default: `rule_text_summary` inclusion is sufficient. No new schema field. |
| 5 | **Should H.8 remain planning-only, or is implementation authorized if the user approves this plan?** | Default: planning-only until user explicitly authorizes implementation. |
| 6 | **If `CCI-ROUTE-011` is rejected, which alternative candidate domain should be searched?** | Default: date/time format (Chapter 2, paragraph 2-4.2) or reference/enclosure sequencing (Chapter 7, paragraph 7-3.3) — both have explicit manual text and existing validators. |
| 7 | **Should the H.8 runner be frozen at 15 checks, or is a different count acceptable?** | Default: 11–15 checks is acceptable; exact count determined at implementation time. |
| 8 | **Should the 30-suite regression gate be the new permanent standard, or should H.8 be designed so the runner can later be merged into an existing runner?** | Default: 30 suites is acceptable — a separate runner makes the pilot independently verifiable and deletable. |
| 9 | **Should the catalog entry include a `note` or `caveat` field about the window-envelope exception, or is the quote sufficient?** | Default: the `source_quote` and `rule_text_summary` are sufficient; no new field needed. |
| 10 | **Who approves the final candidate — the user only, or a documented reviewer workflow through Phase E?** | Default: user-only approval for planning; Phase E reviewer workflow required for actual implementation. |

---

## Recommended Decision Summary

| Decision | Recommended Default |
|---|---|
| **Accept `CCI-ROUTE-011` as third pilot?** | **Yes** — accept pending manual-text verification at Chapter 7, paragraph 7-2.5a |
| **Keep `CCI-ROUTE-010` advisory?** | Yes — unchanged; H.8 does not revisit H.7 decision |
| **Severity promotion?** | No — deferred indefinitely |
| **Feature flag/config design?** | Deferred until severity promotion is requested |
| **Copy-to scope?** | Remain out of scope |
| **Implementation target** | `rule_catalog` only |
| **Target file** | `rules_v6/CCI/cci_ch2_routing_rules.json` |
| **Regression coverage if implemented** | 30-suite gate (29 existing + 1 new H.8 runner) |
| **Rollback risk** | Very low — one JSON object + one runner + docs |

---

## Recommended Implementation Target (If Approved)

| Attribute | Value |
|---|---|
| Implementation target | `rule_catalog` |
| Target file | `rules_v6/CCI/cci_ch2_routing_rules.json` |
| Validator named but not modified | Yes — `validator: "cci_routing"` |
| Enforcement level | Documentation only — no runtime code reads the catalog |
| Severity | `error` (manual uses imperative "must have") |
| Expected new rule ID | `CCI-ROUTE-011` |
| Expected new runner | `tools/run_phase_h8_third_rule_catalog_regression.py` |
| Expected regression gate | 30 suites |

---

## Recommended Regression Gate

- **If planning-only:** 29 suites (current gate, no changes).
- **If third pilot implemented:** 30 suites (29 existing + 1 new H.8 runner).
- **All suites must pass before any commit.**

---

## Open Questions Needing Approval

1. Should `CCI-ROUTE-011` be accepted as the third catalog pilot, or should a different candidate be selected?
2. Should the `applies_to` list for `CCI-ROUTE-011` include memorandum types or be standard-letter only?
3. Should H.8 remain planning-only, or is implementation authorized upon approval of this plan?
4. If `CCI-ROUTE-011` is rejected, which alternative domain (date/time, ref/encl, personnel, POC, acronym) should be searched?
5. Should the 30-suite regression gate become the new permanent standard?

---

End of Phase H.8 / Phase I.7 — Third Low-Risk Rule-Catalog-Only Pilot Plan.
