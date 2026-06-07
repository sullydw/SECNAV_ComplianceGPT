# Phase H.8 / Phase I.7 Third Catalog-Pilot Implementation Checkpoint

**Checkpoint Date:** 2026-06-08
**Implementation Commit:** `769437d` — `CCI: Add From line catalog rule (Phase H.8)`
**Previous Functional Baseline:** `662afbb` — `CCI: Add routing office code evidence regression (Phase H.6)`
**Current Functional Baseline:** `769437d` — Phase H.8 third catalog-pilot implementation complete
**Regression Set:** 30 suites (29 existing + 1 new H.8 runner)
**Full Gate Result:** 30/30 PASS
**Correct Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`

---

## Summary

Phase H.8 third rule-catalog-only pilot implementation is **complete**.

The approved record `agr_20260607_49947aca` (promoted from candidate `cand_20260607_5dcc97cf`) has been implemented as catalog rule `CCI-ROUTE-011` in `rules_v6/CCI/cci_ch2_routing_rules.json` and marked `implemented` with commit `769437d`.

All safety boundaries were preserved. No validator, renderer/layout, prompt-contract, or command-layer changes occurred.

---

## Approved Record

| Field | Value |
|---|---|
| rule_id | `agr_20260607_49947aca` |
| promoted_from_candidate | `cand_20260607_5dcc97cf` |
| rule_category | `manual_rule` |
| field_path | `routing.from` |
| doc_type_filter | `standard_letter` |
| component_filter | `navy` |
| evidence_quality | `high` |
| implementation_status | `implemented` |
| implementation_commit | `769437d` |
| implementer | `phase_h8_implementer` |

---

## Catalog Rule Added

| Field | Value |
|---|---|
| rule_id | `CCI-ROUTE-011` |
| source | `SECNAV M-5216.5` |
| source_type | `manual_text` |
| source_location | `Chapter 7, Section 6, "From:" Line, subparagraph a. General` |
| applies_to | `["standard_letter"]` |
| component_scope | `["navy"]` |
| rule_text_summary | `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.` |
| enforcement | `deterministic` |
| validator | `cci_routing` |
| severity | `error` |
| manual_chapter | `7` |
| manual_section | `6` |
| page_or_figure | `50` |
| source_quote | `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.` |
| effective_date | `2026-06-07` |
| added_by_implementation_id | `agr_20260607_49947aca` |
| implementation_target | `rule_catalog` |
| implementation_status | `active` |

---

## SECNAV Provenance

- **Source file:** `references/SECNAV_M-5216.5_CH-1.pdf`
- **PDF page:** 50
- **Rendered source location:** Chapter 7, Section 6, `"From:" Line`, subparagraph a. General
- **Paragraph-numbering caveat:** `7-2.5a` may be inferred/manual-convention numbering but is not visibly printed on the PDF page.
- **Exact quote:** `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.`
- **Window-envelope exception:** Verified in the same sentence.

---

## Files Changed in Implementation Commit

| File | Change |
|---|---|
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Added CCI-ROUTE-011 rule entry (+20 lines) |
| `tools/run_phase_h8_third_rule_catalog_regression.py` | New regression runner (+183 lines) |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | Updated allowed-changes list for H.8 artifacts |
| `tools/run_phase_h6_routing_office_code_evidence_regression.py` | Removed `cci_ch2_routing_rules.json` from forbidden list |

---

## Regression Results

### H.8 Targeted Runner

**PASS** — 16/16 checks

- `tools/run_phase_h8_third_rule_catalog_regression.py`
- Verified: catalog loads, object schema with `"rules"` array, CCI-ROUTE-011 exists exactly once, CCI-ROUTE-010 still present, SECNAV source/provenance fields present, quote includes `"From:"` and `window envelope`, `applies_to` is `["standard_letter"]`, implementation ID and target correct, no validator/renderer/prompt/command-layer changes, no approved/pending logs tracked.

### Full 30-Suite Gate

**PASS** — 30/30 suites

All regression runners including C7, C8, C9, C10, all CCI validators, correction pipeline, intake, context schema, profile, and all Phase H runners (H.2, H.3, H.4, H.6, H.8) pass cleanly.

---

## Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No validator changes | Preserved — `src/cci_routing_validate.py` and all other validators untouched |
| No renderer/layout changes | Preserved — `src/pdf_v6_render.py` and layout profiles untouched |
| No prompt-contract changes | Preserved — `src/context_resolver.py` untouched |
| No Phase F/G command-layer changes | Preserved — `src/correction_commands.py`, `src/correction_nl_commands.py` untouched |
| No approved/pending/session logs committed | Preserved — all correction logs remain local/gitignored |
| No real command/user data committed | Preserved — only catalog entry and regression runner committed |
| CCI-ROUTE-010 remains advisory-only | Preserved — no severity promotion occurred |
| Feature flag/config not implemented | Preserved — remains conceptual only |

---

## Catalog State After H.8

The routing catalog `rules_v6/CCI/cci_ch2_routing_rules.json` now contains **11 rules**:

- CCI-ROUTE-001 through CCI-ROUTE-009 (heuristic warnings)
- CCI-ROUTE-010 (deterministic, error severity, advisory-only validator enforcement)
- CCI-ROUTE-011 (deterministic, error severity, catalog-only — no validator enforcement yet)

Object schema with top-level `"rules"` array preserved.

---

## Next Recommended Phase: Phase H.9 / Phase I.8

Phase H.8 is complete. The next phase is **planning-only until approved** and must decide among:

1. **Fourth low-risk catalog pilot:**
   - Search for a new deterministic rule in subject, ref/encl, date/time, personnel, or acronym domains.
   - Requires planning document, provenance verification, Phase D/E workflow, and regression runner.
   - No validator/renderer/prompt/command-layer changes.

2. **Advisory validator enforcement for CCI-ROUTE-011:**
   - Add non-blocking validator behavior in `src/cci_routing_validate.py` for the From-line rule.
   - Requires planning document, synthetic fixtures, targeted regression runner update.
   - Catalog severity remains `error`; validator enforcement would be interim advisory only.

3. **Feature flag / config support for severity promotion:**
   - Design config-driven severity override mechanism for advisory rules.
   - Requires planning document, schema design, and regression coverage.
   - No implementation until explicitly approved.

4. **Keep CCI-ROUTE-010 advisory indefinitely:**
   - Do not promote. Maintain existing 30-suite regression.
   - No additional evidence collection or config support.

5. **Improve rule-catalog governance / provenance tooling:**
   - Add catalog schema validation, change audit trails, or catalog change review workflow.
   - Requires planning document.
   - No validator/renderer/prompt/command-layer changes.

**Constraints for any next phase:**
- Planning documents must be created and approved before any code changes.
- All 30 regression suites must pass before any commit.
- Use `C:\Users\drryl\pinokio\bin\miniconda\python.exe` for full regression runs.
- No renderer/layout changes unless explicitly scoped and regression-protected.
- No automatic enforcement from approved/pending logs.
- No AI-only implementation decisions.
- No real command/user data committed.

Do not implement Phase H.9 / Phase I.8 without explicit user approval.

---

## Open Questions

1. Should CCI-ROUTE-011 receive advisory validator enforcement before any fourth catalog pilot?
2. Should the project prioritize feature-flag/config support over additional catalog pilots?
3. Should CCI-ROUTE-010 severity promotion be revisited after config support is implemented?
4. Should `multiple_address_letter` be added to CCI-ROUTE-011 `applies_to` after separate verification?
5. Is a catalog schema validator (e.g., JSON Schema for `rules_v6/CCI/*.json`) worth implementing?

---

End of Phase H.8 / Phase I.7 Third Catalog-Pilot Implementation Checkpoint.
