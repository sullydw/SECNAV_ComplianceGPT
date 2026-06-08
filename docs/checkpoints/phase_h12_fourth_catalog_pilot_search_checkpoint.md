# Phase H.12 / Phase I.11 — Fourth Low-Risk Catalog-Only Pilot Search Checkpoint

**Phase H.12 Plan Commit:** `c608ef6` — `Docs: Add Phase H.12 fourth catalog pilot plan`  
**Phase H.12 Search Checkpoint Commit:** `[TBD]` — `Docs: Record Phase H.12 no-candidate search checkpoint`  
**Current Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Current Regression Set:** 32 suites (32/32 PASS)  
**Phase Status:** H.12 plan approved for candidate search; both priority and expanded searches complete; no safe candidate found.

---

## Approved Verdict

**APPROVE PHASE H.12 PLAN FOR CANDIDATE SEARCH**

The H.12 planning document (`docs/planning/phase_h12_fourth_catalog_pilot_plan.md`) was reviewed and approved as a planning-only source of truth on commit `c608ef6`.

---

## Search Execution Summary

### Priority-Domain Search (First Pass)

| Domain | Search Order | Result | Reason |
|---|---|---|---|
| Subject (Ch 7, Para 9) | 1st | No candidate | Paragraph 9 fully mapped by SUBJ-001 through SUBJ-006 |
| Reference/Enclosure (Ch 7, Para 10-11) | 2nd | No candidate | Paragraphs 10-11 fully mapped by REF-001 through REF-010 |
| Date/Time (Ch 2, Para 2-4.2) | 3rd | No candidate | Paragraph 2-4.2 fully mapped by DTM-001 through DTM-007 |
| Routing (conditional) | 4th (deferred) | No candidate | ROUTE-001 through ROUTE-011 already dense; no clear non-overlap |

### Expanded-Domain Search (Second Pass)

| Area | Manual Source | Result | Reason |
|---|---|---|---|
| Paragraphing / Subparagraphing | Ch 7, Para 18 / Figure 7-8 | No candidate | Body-text nesting rule; requires parser expansion |
| Proofreading / Writing Mechanics | Ch 7, Para 19 | No candidate | No deterministic structural rules found |
| Signature Line | Ch 7, Para 12 / Figure 7-7 | No candidate | Renderer/layout implication (line spacing, centering) |
| Writing Style / Capitalization | Ch 2, Para 2-4.1 | No candidate | "After first use, acronyms shall be used throughout" is heuristic |
| Abbreviations & Acronyms | Ch 2, Para 17 | No candidate | ACR-001 through ACR-003 already cover deterministic rules |
| Personnel / Rank / Name | Ch 7, Para 11 | No candidate | PER-001 already covers last-name all-caps in body |
| Point of Contact | Ch 7 | No candidate | POC-001 through POC-003 already cover |
| Memo Salutation/Close | Ch 7, Memo section | No candidate | v6 model has no salutation/complimentary_close fields |
| Enclosure Marking & Numbering | Ch 7, Para 11b | No candidate | REF-007 covers numeric sequence; renderer implication for formatting |
| Letterhead / Addressing | Ch 7 | No candidate | Layout/renderer implication |
| Page Numbering | Ch 7, Para 17 | No candidate | Layout/renderer implication |
| Ship Name Non-Splitting | Ch 7, Para 18b | No candidate | Line-wrap renderer implication |
| Never Hyphenate at Page End | Ch 7, Para 18b | No candidate | Renderer implication |

### Candidate Selection Criteria Results

All candidate phrases from the expanded search failed at least one of the 10 hard selection criteria:

| Criterion | Pass/Fail | Notes |
|---|---|---|
| Deterministic | **FAIL** | "Acronyms shall be used throughout" is ambiguous; body-text rules need parsing |
| Short exact quote | **FAIL** | Remaining quotes are multi-sentence or contain exceptions |
| Clear `applies_to` | **FAIL** | Body-text rules lack narrow structural scope |
| Low false-positive risk | **FAIL** | Heuristic candidates (acronym re-use, salutation detection) rejected |
| Catalog-only target | **FAIL** | Body scanning or renderer awareness needed |
| No validator change | **FAIL** | Any body-text rule needs validator scanning |
| No renderer/layout implication | **FAIL** | Signature, page numbering, hyphenation, addressing all layout |
| No prompt-contract implication | **PASS** | Not applicable for rejected candidates |
| No command-layer implication | **PASS** | Not applicable for rejected candidates |
| No feature flag/config needed | **PASS** | Not applicable for rejected candidates |

---

## Proposed Candidates Evaluated and Rejected

| # | Proposed Candidate | Source Quote | Rejection Reason |
|---|---|---|---|
| 1 | Title case for subject in body | "capitalize it using the 'Title Case' format" | Body-text heuristic, not catalog-only |
| 2 | Repeat subject in reply letters | "repeat the subject of the incoming correspondence in the subject line" | Procedural, not deterministic on payload |
| 3 | Never subparagraph beyond Figure 7-8 | "Never subparagraph beyond the levels shown in figure 7-8" | Body-parser requirement |
| 4 | Never split ship name | "Never split the name of a ship" | Renderer/layout implication |
| 5 | Do not capitalize last name in body | "Do not capitalize every letter of a member's last name, except in the subject and signature lines" | **DUPLICATE** — PER-001 already covers |
| 6 | Acronyms used after first use | "After first use, acronyms shall be used throughout the rest of the correspondence" | Heuristic; semantic interpretation required |
| 7 | No salutation in memorandum | "Do not use a salutation in a memorandum" | v6 model has no salutation field |
| 8 | No complimentary close in memorandum | "Do not use a complimentary close in memorandums" | v6 model has no complimentary_close field |
| 9 | Parenthesized number for every enclosure | "Use a number in parentheses before the description of every enclosure, even if you have only one" | Renderer ambiguity / REF-007 overlap |
| 10 | No abbreviations in address | "Do not use abbreviations or punctuation in the address" | Layout implication |
| 11 | No page number on first page | "Do not number a single-page letter or the first page of a multiple-page letter" | Layout implication |
| 12 | Avoid slang or jargon | "Do not use slang or jargon" | Heuristic, not deterministic |

---

## Duplicate/Overlap Status

| Domain | Existing Coverage | Unmapped Text | New Overlap? |
|---|---|---|---|
| Subject | SUBJ-001 through SUBJ-006 | None | No |
| Ref/Encl | REF-001 through REF-010 | None | No |
| Date/Time | DTM-001 through DTM-007 | None | No |
| Routing | ROUTE-001 through ROUTE-011 | Ship names, signature mins, page numbers | Layout-rejected |
| Personnel | PER-001 through PER-006 | None | No |
| Acronym | ACR-001 through ACR-003 | "Shall be used throughout" | Heuristic-rejected |
| POC | POC-001 through POC-003 | None | No |

---

## Safety Boundaries Preserved

- **No validator changes.** `src/cci_*_validate.py` untouched.
- **No rule catalog changes.** `rules_v6/CCI/*.json` untouched.
- **No renderer/layout changes.** `src/pdf_v6_render.py` untouched.
- **No prompt-contract changes.** `src/context_resolver.py` untouched.
- **No Phase F/G command-layer changes.** `src/correction_commands.py`, `src/correction_nl_commands.py` untouched.
- **No approved/pending/session logs committed.** All correction storage remains local/gitignored.
- **No real data committed.**
- `CCI-ROUTE-010` remains advisory-only.
- `CCI-ROUTE-011` remains advisory-only.

---

## Current Catalog Maturity Assessment

The three prior catalog pilots captured the most obvious deterministic structural rules:

- **Phase H.1:** `CCI-CH7-SUBJ-006` — No acronyms in subject line (paragraph 9)
- **Phase H.3:** `CCI-ROUTE-010` — Office code prefix rule (paragraph 7-2.7a)
- **Phase H.8:** `CCI-ROUTE-011` — From line required for standard letters (paragraph 7-2.5a)

The remaining SECNAV M-5216.5 manual text either:
1. Is already cataloged in existing rule files
2. Requires body text parsing or semantic interpretation
3. Implies renderer/layout/page geometry changes
4. Is a procedural guideline rather than a deterministic structural rule

**Assessment:** The current catalog is reasonably mature for obvious deterministic catalog-only rules within the current scope.

---

## Future Expansion Paths Identified

| Path | Description | Blockers |
|---|---|---|
| **Feature Flag / Config Planning** | Design config-driven severity override system | No blocker; can be planned immediately |
| **Body-Scanning Validator Expansion** | Extend validators to scan body text for rules like acronym re-use, salutation detection | Requires v6 model extension or validator expansion; out of H.12 scope |
| **Model Extension Planning** | Add salutation/complimentary_close fields to v6 letter model | Requires schema change, renderer update, regression update |
| **Supplementary Manual Search** | Search SECNAVINSTs or other directives outside M-5216.5 | Requires separate manual acquisition |

---

## Recommended Next Phase

**Phase H.13 / Phase I.12 — Feature-Flag/Config Planning**

Given that H.12 found no safe fourth catalog-only pilot, the most productive next path is feature-flag/config planning. This is needed before any future severity promotion of:

- `CCI-ROUTE-010` (office code prefix)
- `CCI-ROUTE-011` (From line required)
- Any future rule that transitions from advisory to warning/error

Feature-flag/config planning should cover:
1. Configuration schema for per-rule severity overrides
2. Default severity preservation (no breaking changes)
3. Integration with existing validator runner
4. No renderer/layout changes
5. No prompt-contract changes
6. No command-layer changes
7. No automatic enforcement from approved logs

---

## Open Questions Before Phase H.13

1. Should H.13 plan a global config file or per-profile severity overrides?
2. Should feature flags be runtime-switchable or startup-config only?
3. Which rules should be eligible for severity override (all `heuristic_warning` rules? all rules?)
4. Should the config system be a new module or integrated into `src/local_profile.py`?
5. What is the minimum viable feature-flag implementation for the next promotion pilot?

---

## Files That Were NOT Modified in H.12

- `rules_v6/CCI/cci_ch7_subject_rules.json` — untouched
- `rules_v6/CCI/cci_ch7_ref_encl_rules.json` — untouched
- `rules_v6/CCI/cci_ch2_date_time_rules.json` — untouched
- `rules_v6/CCI/cci_ch2_routing_rules.json` — untouched
- `rules_v6/CCI/cci_ch2_personnel_rules.json` — untouched
- `rules_v6/CCI/cci_ch2_acronym_rules.json` — untouched
- `rules_v6/CCI/cci_ch2_poc_rules.json` — untouched
- `src/pdf_v6_render.py` — untouched
- `src/cci_subject_validate.py` — untouched
- `src/cci_routing_validate.py` — untouched
- `src/cci_ref_encl_validate.py` — untouched
- `src/cci_date_time_validate.py` — untouched
- `src/cci_personnel_validate.py` — untouched
- `src/cci_acronym_validate.py` — untouched
- `src/cci_poc_validate.py` — untouched
- `src/context_resolver.py` — untouched
- `src/intake_orchestrator.py` — untouched
- `src/correction_commands.py` — untouched
- `src/correction_nl_commands.py` — untouched
- `src/letter_model_v6.py` — untouched
- All regression runners — untouched
- All existing fixtures — untouched

---

End of Phase H.12 / Phase I.11 Fourth Catalog-Only Pilot Search Checkpoint.
