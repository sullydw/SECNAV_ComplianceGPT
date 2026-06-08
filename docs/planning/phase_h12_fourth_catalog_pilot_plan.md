# Phase H.12 / Phase I.11 — Fourth Low-Risk Catalog-Only Pilot Plan

**Planning Commit (Expected):** `[TBD]` — `Docs: Add Phase H.12 fourth catalog pilot plan`  
**Current Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Previous Baseline:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Full Regression Gate:** 32/32 PASS  
**Correct Python:** `C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe`

---

## 1. Why Phase H.12 Should Prefer a Fourth Catalog-Only Pilot

Phase H.11 evidence review confirmed that:

- `CCI-ROUTE-010` remains **advisory-only.**
- `CCI-ROUTE-011` remains **advisory-only.**
- Severity promotion remains **deferred.**
- Feature flag/config support remains **conceptual only** and must be designed before any promotion.

The most productive next path is therefore **not** severity promotion, feature-flag work, or renderer changes. The most productive next path is a **fourth low-risk catalog-only pilot** — adding a new deterministic rule to the rule catalog without touching validators, renderers, prompt contracts, or command layers.

**Rationale for catalog-only preference:**

| Alternative | Risk Level | Why Deferred |
|---|---|---|
| Severity promotion for CCI-ROUTE-010 | High | Insufficient real-world evidence; no feature flag/config support |
| Severity promotion for CCI-ROUTE-011 | High | Insufficient real-world evidence; no feature flag/config support |
| Feature flag/config design | Medium | Requires planning document, schema design, regression coverage; concept-only now |
| Fourth catalog-only pilot | **Low** | Proven pattern from H.1, H.3, H.8; narrow scope; no runtime changes |

The three prior catalog-only pilots (H.1 `CCI-CH7-SUBJ-006`, H.3 `CCI-ROUTE-010`, H.8 `CCI-ROUTE-011`) each followed the same Phase D → Phase E → Phase H workflow and added only a single rule-catalog entry plus a targeted regression runner. No validator, renderer, or command-layer changes occurred until **separate** follow-up phases (H.2, H.4, H.9) explicitly added advisory enforcement.

H.12 should repeat this proven pattern.

---

## 2. Candidate Domains to Search

The following CCI domains have existing rule catalogs in `rules_v6/CCI/`:

### 2.1 Subject Rules (`cci_ch7_subject_rules.json`)

- Current rules: `CCI-CH7-SUBJ-001` through `CCI-CH7-SUBJ-006`.
- `CCI-CH7-SUBJ-006` is the H.1 pilot subject-acronym rule.
- `CCI-CH7-SUBJ-007` (advisory) was added in H.2 as a validator-only behavior, not a catalog addition.
- **Catalog space exists.** `CCI-CH7-SUBJ-007` (or higher) is available as a catalog ID.
- **Pros:** narrowly scoped; deterministic; subject field is simple string.
- **Cons:** `CCI-CH7-SUBJ-006` already covers subject-acronym prohibition; must find a clearly different rule.

### 2.2 Reference/Enclosure Rules (`cci_ch7_ref_encl_rules.json`)

- Current rules: `CCI-REF-001` through `CCI-REF-010`, plus `CCI-REF-NOTE-001`.
- **Catalog space exists.** `CCI-REF-011` (or higher) is available.
- **Pros:** deterministic; source text in Chapter 7 paragraph 7-3.3 and Figure 7-1 is explicit.
- **Cons:** `ref` and `encl` fields are optional arrays; rule behavior depends on optional fields being present; edge-case complexity may be higher than subject or routing.

### 2.3 Date/Time Rules (`cci_ch2_date_time_rules.json`)

- Current rules: `CCI-DTM-001` through `CCI-DTM-007`.
- **Catalog space exists.** `CCI-DTM-008` (or higher) is available.
- **Pros:** deterministic; date/time rules are typically format-only.
- **Cons:** `DTM-001`–`DTM-007` already cover many date/time constraints; finding a new unduplicated rule may require deeper source reading.

### 2.4 Personnel Identification Rules (`cci_ch2_personnel_rules.json`)

- Current rules: `CCI-PER-001` through `CCI-PER-006`.
- **Catalog space exists.** `CCI-PER-007` (or higher) is available.
- **Pros:** deterministic; personnel names and titles are straightforward.
- **Cons:** Marine Corps vs. Navy rank conventions differ; false-positive risk may be higher than subject/routing.

### 2.5 Point-of-Contact Rules (`cci_ch2_poc_rules.json`)

- Current rules: `CCI-POC-001` through `CCI-POC-003`.
- **Catalog space exists.** `CCI-POC-004` (or higher) is available.
- **Pros:** narrowly scoped.
- **Cons:** few remaining subparagraphs in source text; limited candidate inventory.

### 2.6 Acronym/Abbreviation Rules (`cci_ch2_acronym_rules.json`)

- Current rules: `CCI-ACR-001` through `CCI-ACR-003`.
- **Catalog space exists.** `CCI-ACR-004` (or higher) is available.
- **Pros:** deterministic; text-only rule.
- **Cons:** `CCI-ACR-003` may overlap with H.1 `CCI-CH7-SUBJ-006`; must verify non-duplication carefully.

### 2.7 Routing Rules (`cci_ch2_routing_rules.json`)

- Current rules: `CCI-ROUTE-001` through `CCI-ROUTE-011`.
- **Catalog space exists.** `CCI-ROUTE-012` (or higher) is available.
- **Pros:** proven domain; H.3 and H.8 were both routing rules; source text in Chapter 7 is dense.
- **Cons:** must confirm non-overlap with `CCI-ROUTE-010` and `CCI-ROUTE-011`; routing domain rules tend to have more exceptions (window envelope, etc.).
- **Recommendation:** search routing only if a clearly separate subparagraph is found; otherwise favor subject, ref/encl, or date/time.

### 2.8 Summary by Domain

| Domain | Existing Rules | Next Available ID | Expansion Likelihood | Priority |
|---|---|---|---|---|
| Subject | 6 | CCI-CH7-SUBJ-007 | Medium | **High** |
| Ref/Encl | 10 + 1 | CCI-REF-011 | Medium | **High** |
| Date/Time | 7 | CCI-DTM-008 | Medium | Medium |
| Personnel | 6 | CCI-PER-007 | Medium | Medium |
| Acronym | 3 | CCI-ACR-004 | Low-Medium | Medium |
| POC | 3 | CCI-POC-004 | Low | Low |
| Routing | 11 | CCI-ROUTE-012 | Medium | **Conditional** — only if non-overlapping |

---

## 3. Candidate Selection Criteria

A candidate for the H.12 fourth catalog-only pilot **must** satisfy all of the following:

### 3.1 Hard Requirements

| Criterion | Standard | Why |
|---|---|---|
| Deterministic | Binary yes/no compliance | Eliminates judgment calls; enables regression fixtures |
| Short source quote | One sentence or short paragraph | Reduces ambiguity; simplifies provenance verification |
| Clear `applies_to` scope | Explicit document types | Prevents false positives on unaffected types |
| Low false-positive risk | Narrow scope; few exceptions | Catalog-only rules should be unambiguous |
| Catalog-only target | `rule_catalog` only | No validator, renderer, prompt, or command changes |
| No validator change | `src/*_validate.py` untouched | H.12 must not add new validator logic |
| No renderer/layout implication | `src/pdf_v6_render.py` untouched | Catalog-only rules do not affect layout |
| No prompt-contract implication | `src/context_resolver.py` untouched | Field requirements stay stable |
| No command-layer implication | `src/correction_commands.py`, `src/correction_nl_commands.py` untouched | No new commands |
| No feature flag/config needed | No `config.yaml` changes | Adheres to concept-only policy |

### 3.2 Soft Requirements

| Criterion | Standard | Why |
|---|---|---|
| Source availability | Chapter 7 or Chapter 2 paragraph | Proven from prior pilots |
| Non-overlap with existing rules | Unique rule ID and unique behavior | Each pilot adds distinct value |
| Document-type exclusivity | Applies to one or few document types | Narrower scope = lower risk |
| No exception complexity | Prefer no exceptions to simple exceptions | `window_envelope` is acceptable; complex branching is not |
| Proven validator domain | Existing `*_validate.py` can handle it | Enables future advisory enforcement in separate phase |

---

## 4. Source/Provenance Requirements

Every candidate **must** have:

### 4.1 Required Provenance Fields

| Field | Requirement |
|---|---|
| Exact SECNAV quote | Full sentence or paragraph, copied from manual |
| Source file/path | `SECNAV M-5216.5` |
| Chapter/section | e.g. `Chapter 7, paragraph 7-3.3` |
| Page or figure | PDF page number or figure number |
| Surrounding context | 1–2 sentences before and after for conflict check |
| Manual scope | `navy`, `marine_corps`, `joint`, `don_secretariat`, or subset |

### 4.2 Near-By Context Conflict Check

Before approving any candidate, verify:

1. Does the source paragraph contain a figure or example that **modifies** the rule?
2. Does the same section have a "however," "except," or "unless" clause?
3. Does a nearby paragraph contain an **explicitly excluded** document type?
4. Does the figure caption add an exception not in the paragraph text?

If any of the above apply, the candidate may be too complex for catalog-only; document the exception in the planning file.

### 4.3 Source Comparison Table (Example)

| Candidate | Exact Quote | Chapter | Page | Context Conflict | Scope |
|---|---|---|---|---|---|
| CCI-CH7-SUBJ-006 | "In correspondence, do not use acronyms in the subject line." | Ch 7, para 9a | PDF 56 | None identified | all |
| CCI-ROUTE-010 | "If the office code is composed of only numbers, add the word 'Code' before the numbers..." | Ch 7, para 7-2.7a | PDF 51 | None identified | `to`, `via` |
| CCI-ROUTE-011 | "Every standard letter must have a 'From:' line, except a letter that will be used with a window envelope." | Ch 7, Section 6, para a | PDF 50 | `window_envelope` exception documented | `DT_STD_LTR`, `standard_letter` |

H.12 candidates must pass the same table before approval.

---

## 5. Duplicate/Overlap Checks

### 5.1 Existing Catalog IDs

Verify the proposed `rule_id` does not exist in any of:

- `rules_v6/CCI/cci_ch7_subject_rules.json`
- `rules_v6/CCI/cci_ch7_ref_encl_rules.json`
- `rules_v6/CCI/cci_ch2_date_time_rules.json`
- `rules_v6/CCI/cci_ch2_personnel_rules.json`
- `rules_v6/CCI/cci_ch2_poc_rules.json`
- `rules_v6/CCI/cci_acronym_rules.json`
- `rules_v6/CCI/cci_ch2_routing_rules.json`

### 5.2 Existing Validator Behavior

Verify the proposed rule does not duplicate any existing validator check:

| Validator File | Existing Checks |
|---|---|
| `src/cci_subject_validate.py` | Subject-line acronym, prohibited acronyms, all-caps scan |
| `src/cci_ref_encl_validate.py` | Reference substantiation, enclosure validation |
| `src/cci_date_time_validate.py` | Date format, military time format |
| `src/cci_personnel_validate.py` | Personnel name/title validation |
| `src/cci_poc_validate.py` | POC presence/format |
| `src/cci_acronym_validate.py` | Global acronym first-use |
| `src/cci_routing_validate.py` | Office-code prefix, From-line required |

### 5.3 Existing Catalog Pilot Patterns

| Pilot | Rule ID | Domain | Target | Validator Later? |
|---|---|---|---|---|
| H.1 | CCI-CH7-SUBJ-006 | Subject | `rule_catalog` | Yes (H.2) |
| H.3 | CCI-ROUTE-010 | Routing | `rule_catalog` | Yes (H.4) |
| H.8 | CCI-ROUTE-011 | Routing | `rule_catalog` | Yes (H.9) |
| H.12 | **TBD** | **TBD** | **TBD** | No (future phase only) |

H.12 must not duplicate any of the three prior pilots in behavior or text.

---

## 6. Recommended Search Order

### 6.1 Priority 1: Subject Domain

1. Open SECNAV M-5216.5, Chapter 7, paragraph 9 (Subject Line).
2. Read subparagraphs a, b, c for a clearly deterministic rule not covered by `CCI-CH7-SUBJ-001` through `006`.
3. Check figure 7-1 caption for any additional subject-line constraints.
4. Check if the rule applies to all correspondence types or can be narrowed.
5. Confirm no overlap with `CCI-CH7-SUBJ-006` (acronym prohibition).

### 6.2 Priority 2: Reference/Enclosure Domain

1. Open Chapter 7, paragraph 7-3.3 (References, Enclosures, and Copy-To Blocks).
2. Read subparagraphs for a clearly deterministic rule not covered by `CCI-REF-001` through `CCI-REF-NOTE-001`.
3. Check if the rule is about listing format, ordering, or count limitations.
4. Confirm the rule does not require body-text scanning (too complex for catalog-only).

### 6.3 Priority 3: Date/Time Domain

1. Open Chapter 7, relevant date/time paragraph.
2. Look for format rules that are purely syntactic (e.g., "use only Arabic numerals for dates").
3. Verify `CCI-DTM-001`–`007` do not already cover it.

### 6.4 Priority 4: Routing Domain (Only if Non-Overlapping)

1. Search Chapter 7, Section 7-2 (Routing) for subparagraphs not yet represented in `CCI-ROUTE-001` through `011`.
2. Explicitly confirm non-overlap with `CCI-ROUTE-010` and `CCI-ROUTE-011`.
3. Prefer rules with narrow scope and few exceptions.

### 6.5 Priority 5: Personnel, POC, Acronym Domains

1. Search remaining paragraphs in Chapter 2 or Chapter 7.
2. Accept only if a clearly separate, deterministic rule is found.

---

## 7. Recommended Default Candidate Type

**Default recommendation for H.12: a subject or ref/encl catalog-only rule.**

**Subject rule preference rationale:**

- Subject is a single string field — simplest data type in the correspondence JSON.
- No array-based complexity (unlike `ref`, `encl`, `via`, `to`, `copy_to`, `distribution`).
- No document-type branching complexity (unlike routing rules that must exclude memoranda, endorsements, etc.).
- Prior H.1 pilot (`CCI-CH7-SUBJ-006`) was the cleanest and fastest of all three pilots.

**Ref/encl rule as second preference:**

- Reference/enclosure rules have strong source text in Chapter 7, paragraph 7-3.3.
- Figure 7-1 provides clear visual examples.
- Arrays add some complexity, but listing-order or format rules are still deterministic.

---

## 8. Required Phase D → Phase E → Phase H Workflow

Before any H.12 implementation, the following workflow **must** be followed:

| Phase | Action | Output |
|---|---|---|
| Phase D | Log candidate as pending global rule | `corrections/pending_corrections.jsonl` (local/gitignored) |
| Phase E | Review candidate; claim, validate, approve or reject | Approved rule record (local/gitignored) |
| Phase H Stage 1 | Run `mark_implemented()` with eligibility validation | Implementation planned status |
| Phase H.12 | Add catalog entry + regression runner + fixtures | Git commit, 33-suite gate |

**H.12 planning-only scope:** The H.12 planning document itself does **not** execute Phase D–E. It documents what Phase D–E should look like for H.12 and identifies candidate domains to search. The actual candidate selection and approval occur in a later phase after H.12 plan approval.

---

## 9. Recommended Future Rule ID Strategy

### 9.1 Preferred ID Pattern

Follow the existing numbering convention:

| Domain | Prefix | Next Available |
|---|---|---|
| Subject | `CCI-CH7-SUBJ-` | `007` |
| Ref/Encl | `CCI-REF-` | `011` |
| Date/Time | `CCI-DTM-` | `008` |
| Personnel | `CCI-PER-` | `007` |
| POC | `CCI-POC-` | `004` |
| Acronym | `CCI-ACR-` | `004` |
| Routing | `CCI-ROUTE-` | `012` |

### 9.2 Severity Setting

- Catalog `severity` should remain `"error"` (consistent with existing entries).
- If a future phase adds advisory validator enforcement, the validator helper will be interim advisory/non-blocking only — catalog severity stays `"error"`.
- Do **not** create a new catalog with `"severity": "advisory"`. Severity is handled at the validator layer, not the catalog layer.

---

## 10. Required Targeted Regression Runner (If Implementation Proceeds)

If H.12 is approved and proceeds to implementation, a new targeted regression runner **must** be created:

### 10.1 Minimum Checks

| Check | Required |
|---|---|
| Target catalog file exists | Yes |
| Target file is valid JSON | Yes |
| New rule entry exists with correct `rule_id` | Yes |
| `rule_text` matches expected text | Yes |
| `source`, `source_location` match expected values | Yes |
| `applies_to` and `component_scope` are populated | Yes |
| `severity` is `"error"` | Yes |
| `target` is `"rule_catalog"` | Yes |
| Catalog schema (`rules` array or top-level array) preserved | Yes |
| No other rules in same catalog were accidentally modified | Yes |
| `src/pdf_v6_render.py` was not modified | Yes |
| No validator files were modified | Yes |
| No command-layer files were modified | Yes |
| No approved/pending/session logs were committed | Yes |
| No real data was committed | Yes |
| H.10 runner still passes | Yes |
| H.9 runner still passes | Yes |
| H.8 runner still passes | Yes |

### 10.2 Proposed Runner Name

```
tools/run_phase_h12_fourth_rule_catalog_regression.py
```

Follows naming convention from H.1 (`run_pilot_*`), H.3 (`run_phase_h3_*`), H.8 (`run_phase_h8_*`).

---

## 11. Future Regression Gate

### 11.1 Current State

- **Current gate:** 32 suites.
- **Last full gate:** 32/32 PASS at commit `d808cb8`.

### 11.2 Expected H.12 Gate

If H.12 proceeds to implementation:

- **New target:** 33 suites (32 existing + 1 new H.12 targeted runner).
- Use same Python: `C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe`.

### 11.3 Proposed 33-Suite Catalog

```bat
... (existing 32 runners) ...
C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe tools\\run_phase_h12_fourth_rule_catalog_regression.py
```

---

## 12. Files That May Be Modified in Future H.12 Implementation

| File | Action |
|---|---|
| `docs/planning/phase_h12_fourth_catalog_pilot_plan.md` | Exists (this file) |
| `rules_v6/CCI/<target_catalog_file>.json` | Append new rule entry |
| `tools/run_phase_h12_fourth_rule_catalog_regression.py` | New runner (if implementation proceeds) |
| `examples/<domain>_h12_*.json` | New synthetic fixtures (if implementation proceeds) |
| `docs/checkpoints/phase_h12_fourth_catalog_pilot_checkpoint.md` | New checkpoint (if implementation proceeds) |

---

## 13. Files That Must Not Be Modified

| File | Reason |
|---|---|
| `src/pdf_v6_render.py` | No renderer/layout changes |
| `src/cci_subject_validate.py` | No validator changes |
| `src/cci_ref_encl_validate.py` | No validator changes |
| `src/cci_date_time_validate.py` | No validator changes |
| `src/cci_personnel_validate.py` | No validator changes |
| `src/cci_poc_validate.py` | No validator changes |
| `src/cci_acronym_validate.py` | No validator changes |
| `src/cci_routing_validate.py` | No validator changes |
| `src/context_resolver.py` | No prompt-contract changes |
| `src/intake_orchestrator.py` | No intake/UI changes |
| `src/correction_commands.py` | No Phase F changes |
| `src/correction_nl_commands.py` | No Phase G changes |
| `src/correction_implementation_planner.py` | No planner changes unless Phase H.1 style wrapper needed |
| `config.yaml` (if exists) | No feature flag/config changes |
| `docs/BOOTSTRAP.md` | Do not modify |
| `docs/HERMES_INSTRUCTIONS.md` | Do not modify |

---

## 14. What Phase H.12 Must NOT Do

H.12 is **planning-only** unless separately approved and the implementation phase is explicitly authorized.

H.12 must **not**:

1. Modify any validator file (`src/*_validate.py`).
2. Modify the renderer (`src/pdf_v6_render.py`).
3. Modify the prompt contract (`src/context_resolver.py`).
4. Modify the intake orchestrator (`src/intake_orchestrator.py`).
5. Modify Phase F command layer (`src/correction_commands.py`).
6. Modify Phase G command mediator (`src/correction_nl_commands.py`).
7. Implement automatic enforcement from approved/pending/session logs.
8. Promote `CCI-ROUTE-010` severity from advisory to warning/error.
9. Promote `CCI-ROUTE-011` severity from advisory to warning/error.
10. Implement feature flag/config support.
11. Commit approved/pending/session/evidence logs.
12. Commit real command/user data.
13. Add background automation, periodic jobs, or cron.
14. Approve a candidate without verified source quote, chapter/paragraph citation, and overlap check.

---

## 15. Rollback Plan

If H.12 planning is rejected:

1. **This file remains** as rejected planning documentation.
2. **No code changes were made** — nothing to revert.
3. **Functional baseline remains `d808cb8`.** Regression set remains 32 suites.
4. **Alternative paths** documented in H.11 checkpoint remain valid:
   - Keep all advisory rules advisory indefinitely.
   - Improve rule-catalog governance/provenance tooling.
   - Design feature flag/config support.

---

## 16. Open Questions Needing Approval

1. **Candidate domain:** Which domain should be searched first — subject, ref/encl, date/time, or other?
2. **Candidate selection method:** Should the search be manual chapter reading, or is there a preferred existing subparagraph already known?
3. **Target catalog file:** Which `rules_v6/CCI/*.json` file should be the target?
4. **Rule ID assignment:** What id prefix and number should be reserved?
5. **Fixture count:** How many synthetic fixtures should be created (H.1 used 5, H.3 used edge cases, H.8 used 16, H.10 used 30)?
6. **H.12 plan approval:** Is this plan approved as the source of truth for Phase H.12?
7. **Implementation authorization:** Is Phase H.12 implementation explicitly authorized, or should it remain planning-only?

---

## 17. Recommended Decision

| Question | Recommendation |
|---|---|
| **Use H.12 as next phase?** | **YES** — fourth catalog-only pilot is the lowest-risk productive path. |
| **Candidate-search order** | **Priority 1: Subject domain** (new `CCI-CH7-SUBJ-007`). **Priority 2: Ref/encl domain** (new `CCI-REF-011`). **Priority 3: Date/time** (new `CCI-DTM-008`). **Avoid routing** unless a clearly non-overlapping subparagraph is identified. |
| **Implementation target** | **Catalog-only rule entry** in `rules_v6/CCI/<target>.json`. No validator, renderer, prompt, or command changes. Phase D → E → H workflow required before any commit. |
| **Regression gate** | **33 suites** (32 existing + 1 new `run_phase_h12_fourth_rule_catalog_regression.py` runner). |
| **Open questions needing approval** | Candidate domain priority, specific subparagraph to target, rule ID assignment, fixture count, and whether implementation is authorized. |

---

End of Phase H.12 / Phase I.11 planning document.
