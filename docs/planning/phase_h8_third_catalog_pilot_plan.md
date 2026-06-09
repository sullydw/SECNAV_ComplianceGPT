# Phase H.8 / Phase I.7 — Third Low-Risk Rule-Catalog-Only Pilot Plan

**Date:** 2026-06-07  
**Latest Docs Checkpoint:** `1e16493` — `Docs: Record Phase H.7 evidence review checkpoint`  
**Current Functional Baseline:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`  
**Previous Functional Baseline:** `1e990a6` — `CCI: Add routing office code advisory validator (Phase H.4)`  
**Current Regression Set:** 29 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until reviewed and approved  
**Candidate Status:** proposed, not yet approved

---

## 1. Why H.8 Should Prefer a Third Catalog Pilot Over Severity Promotion or Feature-Flag Work

### 1.1 Evidence from H.1 Through H.7

| Pilot | Scope | Risk Level | Regression Suites | Outcome |
|---|---|---|---|---|
| H.1 | Rule-catalog only | Very low | 25 | PASS — clean workflow proof |
| H.2 | Validator advisory enforcement | Low-medium | 26 | PASS — required token guard analysis and fixture expansion |
| H.3 | Rule-catalog only | Very low | 27 | PASS — second catalog pilot proved repeatability |
| H.4 | Validator advisory enforcement | Low-medium | 28 | PASS — routing office-code prefix advisory |
| H.5 | Planning-only (severity review) | Zero | 28 | PASS — no code changes |
| H.6 | Evidence collection | Low | 29 | PASS — synthetic fixtures + corpus added |
| H.7 | Planning-only (evidence review) | Zero | 29 | PASS — no code changes |

H.7 reviewed the H.6 evidence for `CCI-ROUTE-010` and concluded:
- The evidence is sufficient to maintain the advisory-only posture.
- The evidence is **insufficient** to justify severity promotion to warning or error.
- Real-world usage feedback is the missing link.
- Continuing to deepen `CCI-ROUTE-010` (more evidence, feature flags, config design) yields diminishing returns without real-world data.

### 1.2 Benefits of a Third Catalog Pilot Over Alternatives

| Alternative | Risk | Value | Recommendation |
|---|---|---|---|
| Severity promotion (warning/error) | Medium-high — could block common routing formats | Low without real-world evidence | **Reject** |
| Feature-flag / config design | Low — but speculative if promotion never happens | Medium — reusable infrastructure | **Defer** |
| More evidence for `CCI-ROUTE-010` | Low — but diminishing returns | Low without real users | **Defer** |
| Third catalog pilot | Very low | High — expands CCI coverage horizontally | **Select** |

A third catalog pilot:
- Follows the proven H.1/H.3 pattern (rule-catalog-only first).
- Adds a new compliance domain (From line) without touching existing rules.
- Keeps blast radius minimal: one JSON object + one runner.
- Provides tangible new coverage rather than speculative deepening.

---

## 2. Candidate Under Review: CCI-ROUTE-011

### 2.1 Rule Statement

> Every standard letter must have a `"From:"` line, except a letter that will be used with a window envelope.

### 2.2 Window-Envelope Exception

A letter that will be used with a window envelope may omit the `From:` line because the sender's address appears in the envelope window, not on the letter itself.

This exception is **explicit in the manual text** and is not an inferred loophole.

### 2.3 Domain

`routing.from` — the rule governs the presence of the `from` field in standard letter payloads.

### 2.4 Proposed Rule ID

`CCI-ROUTE-011`

This follows the existing routing rule numbering (`CCI-ROUTE-001` through `CCI-ROUTE-010` already exist in `rules_v6/CCI/cci_ch2_routing_rules.json`).

---

## 3. SECNAV Source and Provenance Requirements

### 3.1 Source Citation

- **Manual:** SECNAV M-5216.5
- **Chapter:** 7
- **Section:** 6 — `"From:" Line`
- **Subparagraph:** a. General
- **PDF page:** 50
- **Exact quote:** "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope."

### 3.2 Provenance Verification Steps

1. Open SECNAV M-5216.5 PDF.
2. Navigate to Chapter 7, Section 6, subparagraph a.
3. Confirm the exact quote matches the candidate text.
4. Document the PDF page number for future verification.
5. Verify that no other catalog entry already covers this rule text.

### 3.3 Source Type

`narrative_text` — the rule is stated as an explicit imperative sentence in the manual body text, not inferred from a figure or example.

---

## 4. Whether the Window-Envelope Exception Makes the Candidate Too Complex for Catalog-Only

**Conclusion: NO — the exception does not make the candidate too complex for catalog-only entry.**

Rationale:
- A rule-catalog entry is **documentation only**. It records the rule text, provenance, and metadata. It does not implement enforcement logic.
- The exception is part of the rule text itself. The catalog entry should include the full quoted sentence with the exception clause.
- Complexity only arises if/when a validator is later added (Phase H.9 or beyond). At that point, the validator must handle the `window_envelope` suppression logic.
- For H.8 (catalog-only), the exception is simply text to be documented, not logic to be executed.

---

## 5. Whether the Rule Is Deterministic Enough for Catalog Entry

**Conclusion: YES — the rule is fully deterministic.**

Rationale:
- The test is binary: does the payload have a non-empty `from` field?
- The exception is also binary: is `window_envelope: true` present?
- No subjective judgment, no heuristic threshold, no semantic interpretation required.
- A validator can implement this as a straightforward presence check with an explicit override flag.

---

## 6. Whether There Is Any Renderer/Layout Implication

**Conclusion: NO — the rule has no renderer or layout implication.**

Rationale:
- The rule concerns the **presence** of a data field (`from`), not its visual placement, font, margin, or spacing.
- The renderer (`src/pdf_v6_render.py`) already knows how to place a `From:` line when `from` is present.
- The rule does not change how the `From:` line is rendered; it only documents that the line must be present.
- The window-envelope exception is a data-quality rule, not a layout rule.

---

## 7. Whether the Rule Overlaps Existing Routing Rules

**Conclusion: NO — CCI-ROUTE-011 does not overlap existing routing rules.**

Existing routing rules in `rules_v6/CCI/cci_ch2_routing_rules.json`:

| Rule ID | Topic | Field |
|---|---|---|
| CCI-ROUTE-001 | Addressee completeness | `to` |
| CCI-ROUTE-002 | Via line usage | `via` |
| CCI-ROUTE-003 | Copy-to placement | `copy_to` |
| CCI-ROUTE-004 | Routing line ordering | `to` / `via` |
| CCI-ROUTE-005 | Multiple-address format | `to` |
| CCI-ROUTE-006 | Joint-letter routing | `to` / `via` |
| CCI-ROUTE-007 | Endorsement routing | `via` |
| CCI-ROUTE-008 | Distribution list format | `distribution` |
| CCI-ROUTE-009 | Return address | `return_address` |
| CCI-ROUTE-010 | Office code prefix | `to` / `via` |
| **CCI-ROUTE-011** | **From line presence** | **`from`** |

- ROUTE-010 checks office-code formatting in To/Via lines.
- ROUTE-011 checks From line presence.
- Different fields, different checks, no overlap.

---

## 8. Whether `cci_routing_validate.py` Can Be Named as Existing Validator Domain Without Modifying It

**Conclusion: YES — the existing routing validator can be named without modification.**

Rationale:
- The catalog entry's `validator` field names the module that **would eventually** enforce the rule.
- Naming `cci_routing_validate.py` does not require changing the file.
- H.8 is catalog-only; no validator code is added.
- When a future Phase H.9 proposes validator enforcement for this rule, the same module will be modified then.
- The naming convention is consistent with all existing catalog entries.

---

## 9. Whether Target Catalog File Should Be `rules_v6/CCI/cci_ch2_routing_rules.json`

**Conclusion: YES — this is the correct target file.**

Rationale:
- The rule governs routing content (`from` is a routing field).
- All existing routing rules live in `rules_v6/CCI/cci_ch2_routing_rules.json`.
- The file uses a wrapper schema with `_schema_version`, `_catalog_id`, `chapter`, `title`, and a `"rules"` array.
- New rules must be appended inside the `"rules"` array, not flattened to the top level.
- The file already contains 10 routing rules; adding `CCI-ROUTE-011` makes 11.

---

## 10. Required Rule-Catalog Schema and Proposed Fields

### 10.1 Schema Wrapper

`cci_ch2_routing_rules.json` uses this wrapper:

```json
{
  "_schema_version": "1.0",
  "_catalog_id": "cci_ch2_routing",
  "chapter": "2",
  "title": "Routing Rules",
  "rules": [
    ...
  ]
}
```

New rules are appended to the `"rules"` array.

### 10.2 Proposed Entry

```json
{
  "rule_id": "CCI-ROUTE-011",
  "source": "SECNAV M-5216.5",
  "source_type": "narrative_text",
  "source_location": "Chapter 7, Section 6, \"From:\" Line, subparagraph a. General",
  "applies_to": [
    "standard_letter"
  ],
  "component_scope": [
    "navy",
    "marine_corps",
    "joint",
    "don_secretariat"
  ],
  "rule_text_summary": "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope.",
  "enforcement": "deterministic",
  "validator": "cci_routing_validate.py",
  "severity": "error",
  "manual_chapter": "7",
  "manual_section": "6",
  "page_or_figure": "50",
  "source_quote": "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope.",
  "effective_date": "2026-06-07",
  "added_by_implementation_id": "imp_20260607_HHHHHHHH",
  "implementation_target": "rule_catalog",
  "implementation_status": "active"
}
```

### 10.3 Required Fields

| Field | Required | Notes |
|---|---|---|
| `rule_id` | Yes | Must not collide with existing IDs. |
| `source` | Yes | Always `SECNAV M-5216.5`. |
| `source_type` | Yes | `narrative_text` for manual body text. |
| `source_location` | Yes | Chapter, section, subparagraph. |
| `applies_to` | Yes | `standard_letter` only for this rule. |
| `component_scope` | Yes | All four components. |
| `rule_text_summary` | Yes | Deterministic directive. |
| `enforcement` | Yes | `deterministic` for H.8. |
| `validator` | Yes | Names `cci_routing_validate.py` without modifying it. |
| `severity` | Yes | `error` — the manual uses imperative language (`must`). |
| `manual_chapter` | Yes | `7`. |
| `manual_section` | Yes | `6`. |
| `page_or_figure` | No | `50` for traceability. |
| `source_quote` | Yes | Exact quoted sentence. |
| `effective_date` | Yes | Implementation date. |
| `added_by_implementation_id` | Yes | From Phase H planner. |
| `implementation_target` | Yes | `rule_catalog` for H.8. |
| `implementation_status` | Yes | `active` on creation. |

---

## 11. Required Targeted Regression Runner and Minimum Checks

### 11.1 Runner File

`tools/run_phase_h8_third_rule_catalog_regression.py`

### 11.2 Minimum Checks

| Check | Description |
|---|---|
| 01 | Catalog JSON is valid and parseable. |
| 02 | `CCI-ROUTE-011` is present and unique within the file. |
| 03 | `source` equals `SECNAV M-5216.5`. |
| 04 | `source_location` contains Chapter 7 and Section 6. |
| 05 | `rule_text_summary` contains the exact rule text. |
| 06 | `enforcement` equals `deterministic`. |
| 07 | `implementation_target` equals `rule_catalog`. |
| 08 | `implementation_status` equals `active`. |
| 09 | `source_quote` is non-empty and matches the manual quote. |
| 10 | `applies_to` includes `standard_letter`. |
| 11 | `severity` equals `error` (catalog severity, not validator severity). |
| 12 | No validator files were modified in the commit. |
| 13 | No renderer/layout files were modified. |
| 14 | No prompt-contract files were modified. |
| 15 | No command-layer files were modified. |
| 16 | Existing 29 regression suites still pass. |

Recommended check count: 16.

---

## 12. Future Regression Gate

### Current Gate

- **29 suites** (all PASS after Phase H.7).

### If H.8 Adds a New Runner

- **30 suites** (29 existing + 1 new H.8 runner).
- All existing 29 suites must still pass.

### If H.8 Remains Planning-Only

- **29 suites** — no new runner.
- No code changes.

---

## 13. Phase D -> Phase E -> Phase H Workflow Required Before Implementation

### 13.1 Phase D — Pending Candidate Logging (Optional)

If the candidate originates from a correction or manual review:

1. Create a synthetic pending candidate record locally.
2. Verify it cites the manual source.
3. Do **not** commit the pending log.

### 13.2 Phase E — Review and Approval

1. Claim the candidate for review.
2. Verify provenance (Chapter 7, Section 6, subparagraph a, PDF page 50).
3. Confirm determinism (binary presence check).
4. Confirm blast radius (single field, no renderer impact).
5. Check for duplicates (no existing From-line rule in catalog).
6. Record approval with `review_status="approved_for_implementation"`.
7. Create approved record locally (gitignored).

### 13.3 Phase H — Claim and Plan

1. Claim the approved record for implementation.
2. Set `implementation_target` to `rule_catalog`.
3. Set `target_file` to `rules_v6/CCI/cci_ch2_routing_rules.json`.
4. Record source verification summary.
5. Create `implementation_planned` record.

### 13.4 Phase H.8 — Implementation

1. Append the new rule object to the `"rules"` array.
2. Create the targeted regression runner.
3. Run the 30-suite gate.
4. Commit.
5. Mark the approved record `implementation_status="implemented"` locally.

---

## 14. Files That May Be Modified in Future Implementation

| File | Change Type | Reason |
|---|---|---|
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Append one new rule object | Catalog entry for `CCI-ROUTE-011`. |
| `tools/run_phase_h8_third_rule_catalog_regression.py` | Create new file | Targeted regression runner. |
| `docs/PROJECT_STATUS.md` | Update | New baseline, regression count, milestone. |
| `docs/planning/phase_h8_third_catalog_pilot_plan.md` | Update | Mark sections implemented, add commit refs. |
| `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` | Create new file | Post-implementation checkpoint. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Update | Update baseline and next-phase target. |

---

## 15. Files That Must Not Be Modified

| File | Reason |
|---|---|
| `src/cci_routing_validate.py` | H.8 is catalog-only; no validator changes. |
| `src/cci_subject_validate.py` | No subject validator changes. |
| `src/cci_acronym_validate.py` | No acronym validator changes. |
| `src/cci_ref_encl_validate.py` | No ref/encl validator changes. |
| `src/cci_date_time_validate.py` | No date/time validator changes. |
| `src/cci_personnel_validate.py` | No personnel validator changes. |
| `src/cci_poc_validate.py` | No POC validator changes. |
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract changes. |
| `src/intake_orchestrator.py` | No intake changes. |
| `src/validator_runner.py` | No runner contract changes. |
| `src/correction_commands.py` | No Phase F command-layer changes. |
| `src/correction_nl_commands.py` | No Phase G command-layer changes. |
| `src/correction_implementation_planner.py` | No planner logic changes; only `mark_implemented()` usage. |
| `corrections/pending_corrections.jsonl` | Remains gitignored; do not commit. |
| `corrections/approved_rule_promotions.json` | Remains gitignored; do not commit. |
| `corrections/session/*.jsonl` | Remains gitignored; do not commit. |
| `corrections/evidence/*` | Remains gitignored; do not commit. |
| Any real command/user profile | Do not commit contact data or local profiles. |
| `docs/BOOTSTRAP.md` | Do not modify. |
| `docs/HERMES_INSTRUCTIONS.md` | Do not modify. |

---

## 16. What Phase H.8 Must NOT Do

Phase H.8 is a **rule-catalog-only pilot**. It must NOT:

- **No validator changes.** `src/cci_routing_validate.py` must remain untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` and layout profiles must not be modified.
- **No prompt-contract changes.** `src/context_resolver.py` must remain untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` must not be modified.
- **No automatic enforcement from approved logs.** The catalog entry is documentation only; no runtime code reads the catalog to enforce it automatically.
- **No severity promotion of CCI-ROUTE-010.** The existing office-code rule remains advisory-only.
- **No feature flag/config implementation.** Config support remains conceptual; no new config files or severity override mechanisms.
- **No approved/pending/session/evidence logs committed.** All correction storage remains local/gitignored.
- **No real command/user data committed.** All fixtures must be synthetic.
- **No background automation.** No cron jobs, auto-apply scripts, or silent rule activation.

---

## 17. Rollback Plan

If the H.8 pilot must be rolled back:

1. **Revert the catalog entry** — remove the `CCI-ROUTE-011` JSON object from `rules_v6/CCI/cci_ch2_routing_rules.json`.
2. **Delete the runner** — remove `tools/run_phase_h8_third_rule_catalog_regression.py`.
3. **Revert documentation** — revert `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` to the pre-H.8 state.
4. **Delete the checkpoint** — remove `docs/checkpoints/phase_h8_third_catalog_pilot_checkpoint.md` if created.
5. **Restore baseline** — ensure `662afbb` (or the then-current baseline) is restored as the functional baseline in all docs.
6. **Verify regression** — run the 29 pre-H.8 suites and confirm all pass.

Rollback should require **no more than 4 file deletions/reverts and one regression run**.

---

## 18. Open Questions Needing Approval

| # | Question | Default if unanswered |
|---|---|---|
| 1 | **Should CCI-ROUTE-011 be approved as the third catalog pilot?** | Default: yes — it is deterministic, low blast radius, and well-provenanced. |
| 2 | **Is the SECNAV source citation (Chapter 7, Section 6, subparagraph a, PDF page 50) correct and verifiable?** | Default: yes — must be verified by opening the manual before implementation. |
| 3 | **Should the rule ID be CCI-ROUTE-011, or does a different numbering scheme apply?** | Default: yes — follows existing routing rule sequence. |
| 4 | **Should the catalog severity be error (matching manual imperative language) even though a future validator may start as advisory?** | Default: yes — catalog severity reflects the manual; validator severity can be overridden later. |
| 5 | **Should the applies_to list include any document types beyond standard_letter?** | Default: no — the manual text explicitly says "standard letter." Memorandums, endorsements, and joint letters are excluded. |
| 6 | **Should a window_envelope exception be documented in the catalog entry metadata, or only in the rule text summary?** | Default: rule text summary only — the exception is part of the quoted sentence. Future validator planning (H.9) will handle the suppression logic. |
| 7 | **Should the H.8 runner verify that the new catalog entry does NOT trigger any existing validator?** | Default: yes — include a check that runs `cci_routing_validate.py` against a synthetic fixture and confirms no new errors/warnings appear. |
| 8 | **Is a 30-suite regression gate acceptable?** | Default: yes — one new runner for an independently verifiable pilot. |
| 9 | **Should Phase H.8 remain strictly planning-only until this document is approved, or is any implementation authorized now?** | Default: strictly planning-only — no code changes until explicit approval. |
| 10 | **If CCI-ROUTE-011 is rejected, should the project search for a different third pilot, or pause implementation?** | Default: search for a different third pilot — the H.7 recommendation is to expand horizontally, not to pause. |

---

## Recommended Decision

| Decision | Recommendation |
|---|---|
| **Use CCI-ROUTE-011 candidate?** | **YES** — Approve as the third low-risk catalog pilot. |
| **Reject CCI-ROUTE-011?** | No — the candidate meets all selection criteria. |
| **Search for a different third pilot?** | Only if the user rejects this candidate after review. |

---

## Recommended Implementation Target

| Attribute | Value |
|---|---|
| Implementation target | `rule_catalog` |
| Target file | `rules_v6/CCI/cci_ch2_routing_rules.json` |
| Validator named but not modified | `cci_routing_validate.py` |
| Enforcement level | Documentation only |
| Severity | `error` (catalog) — future validator may start as `advisory` in a separate phase |
| Rule ID | `CCI-ROUTE-011` |

---

## Recommended Regression Gate

| Scenario | Gate |
|---|---|
| Planning-only (no implementation) | 29 suites (current gate, no changes) |
| If H.8 implemented with new runner | 30 suites (29 existing + 1 new H.8 runner) |

All suites must pass before any commit.

---

## Open Questions Needing Approval (Summary)

1. Is the proposed `CCI-ROUTE-011` candidate approved for implementation?
2. Has the SECNAV source citation been verified in the actual manual PDF?
3. Is the `error` catalog severity acceptable given that validator enforcement (if any) would come later at advisory level?
4. Should `applies_to` remain `standard_letter` only?
5. Is implementation authorized, or should this plan remain planning-only pending further review?

---

End of Phase H.8 / Phase I.7 Third Low-Risk Rule-Catalog-Only Pilot Plan.
