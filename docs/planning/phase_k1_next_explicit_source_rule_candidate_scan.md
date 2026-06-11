# Phase K.1 — Next Explicit-Source Rule Candidate Scan

**Date:** 2026-06-10  
**Commit:** `be5a3a0`  
**Suite count:** 36/36 PASS  
**Purpose:** Identify the next best CCI rule candidate with explicit SECNAV M-5216.5 source text, deterministic enforcement, and low false-positive risk.

---

## Scan methodology

1. Reviewed all rule catalogs in `rules_v6/CCI/*.json`
2. Reviewed all validators in `src/cci_*_validate.py`
3. Reviewed all regression runners in `tools/run_phase_*.py`
4. Reviewed `config/cci_enforcement_config.json` for allowlist status
5. Filtered for rules meeting ALL criteria:
   - `enforcement` == `deterministic`
   - `severity` in catalog == `error` (not heuristic warning)
   - `source_location` is a specific chapter/paragraph (not "Requires refinement" or narrative inference)
   - Not already in the config allowlist
   - Not already a warning pilot (ROUTE-010, ROUTE-011)
   - Format-based, not subjective
   - Low false-positive risk

## Candidates excluded

| Rule | Reason excluded |
|------|-----------------|
| CCI-ROUTE-001 through CCI-ROUTE-009 | `source_location` = "Requires refinement" or heuristic warning |
| CCI-ROUTE-007 | Closed without promotion (J.15) |
| CCI-CH7-SUBJ-004, SUBJ-005 | `enforcement` = `heuristic_warning` |
| CCI-POC-001 through CCI-POC-003 | `source_location` = "paragraph requiring refinement"; all heuristic warnings |
| CCI-PER-002 through CCI-PER-006 | `source_location` = "paragraph requiring refinement"; mostly heuristic warnings |
| CCI-REF-008, REF-009, REF-010 | `enforcement` = `heuristic_warning` |
| CCI-DTM-005, DTM-006, DTM-007 | `enforcement` = `heuristic_warning` |
| CCI-ACR-002, ACR-003 | `enforcement` = `heuristic_warning` |

## Top 3 candidates

### Candidate 1: CCI-CH7-SUBJ-002 — Subject line terminal punctuation

| Attribute | Value |
|-----------|-------|
| **Rule ID** | `CCI-CH7-SUBJ-002` |
| **Family** | Subject-line formatting (Chapter 7) |
| **Source location** | Chapter 7, paragraph 7-2.9 and Figure 7-1 |
| **Exact source quote** | "Subject line has no terminal punctuation (period, question mark, exclamation mark)." |
| **Why deterministic** | Terminal punctuation at end of subject string is unambiguous; regex `endswith(('.', '?', '!'))` produces no ambiguity |
| **Current validator status** | **IMPLEMENTED** — `src/cci_subject_validate.py` lines 280-284 |
| **Current regression coverage** | **NONE DEDICATED** — covered indirectly by H.2 acronym runner but no terminal-punctuation-specific fixtures |
| **In severity allowlist** | NO |
| **Implementation effort** | LOW — validator already implements; needs dedicated regression runner only |
| **Risk** | LOW — terminal punctuation is almost never intentional in military correspondence subjects |
| **Recommendation** | **PICK** |

### Candidate 2: CCI-REF-005 — Same item in both references and enclosures

| Attribute | Value |
|-----------|-------|
| **Rule ID** | `CCI-REF-005` |
| **Family** | Reference/enclosure formatting (Chapter 7) |
| **Source location** | Chapter 7, paragraph 7-3.3 |
| **Exact source quote** | "The same item must not appear as both a reference and an enclosure in the same correspondence." |
| **Why deterministic** | Exact normalized text match between reference list entries and enclosure list entries; no ambiguity |
| **Current validator status** | **IMPLEMENTED** — `src/cci_ref_encl_validate.py` lines 365-384 (`_check_duplicate_ref_encl`) |
| **Current regression coverage** | **NONE DEDICATED** — no runner exists for ref/encl validator |
| **In severity allowlist** | NO |
| **Implementation effort** | LOW — validator already implements; needs dedicated regression runner only |
| **Risk** | LOW — same normalized text in both lists is functionally impossible under the manual |
| **Recommendation** | **PICK** |

### Candidate 3: CCI-DTM-003 — Leading zero on single-digit day

| Attribute | Value |
|-----------|-------|
| **Rule ID** | `CCI-DTM-003` |
| **Family** | Date/time formatting (Chapter 2) |
| **Source location** | Chapter 2, paragraph 2-4.2 |
| **Exact source quote** | "Standard text date for military correspondence uses the format day Month year with no leading zero for a single-digit day. Example: 5 May 2026 (not 05 May 2026)." |
| **Why deterministic** | Regex detects `0\d\s+Month` pattern; unambiguous mechanical check |
| **Current validator status** | **IMPLEMENTED** — `src/cci_date_time_validate.py` lines 158-166 |
| **Current regression coverage** | **NONE DEDICATED** — no runner exists for date/time validator |
| **In severity allowlist** | NO |
| **Implementation effort** | LOW — validator already implements; needs dedicated regression runner only |
| **Risk** | LOW — leading zero is never correct for military text dates |
| **Recommendation** | **PICK** |

## Recommended candidate

**CCI-CH7-SUBJ-002** — Subject line terminal punctuation

**Rationale:**
1. Cleanest explicit source text of the three candidates
2. Lowest false-positive risk — a period at the end of a subject line is virtually never correct
3. Validator already fully implements the check
4. No dedicated regression runner exists yet — creating one is straightforward
5. Subject-line rules are user-facing and high-value; terminal punctuation is a common drafting error
6. Scope is narrow and bounded: only standard_letter, multiple_address_letter, endorsement, joint_letter
7. Unlike REF-005 or DTM-003, this rule requires only a single payload field (`subject`) — simplest fixture design

## Future implementation path (if approved)

1. **Phase K.2** — Candidate evaluation plan for SUBJ-002
2. **Phase K.3** — Regression runner plan (positive: subject with `.`, `?`, `!`; negative: subject without terminal punctuation; cross-rule: presence checks still pass)
3. **Phase K.4** — Runner implementation
4. **Phase K.5** — Evidence review
5. **Phase K.6** — Source citation verification (already exact: Chapter 7, paragraph 7-2.9)
6. **Phase K.7** — Decision: allowlist planning or closeout

## Explicit prohibitions

- No config changes in this phase
- No severity changes in this phase
- No allowlist changes in this phase
- No error promotion in this phase
- No validator changes in this phase
- No catalog changes in this phase
- No renderer/layout changes in this phase
- No prompt/context/intake/UI/command-flow changes in this phase
- No Phase F/G command-layer changes in this phase
- No fixtures or runners created in this phase
- No logs or unsanitized material committed
- Do not read or modify `docs/BOOTSTRAP.md`
- Do not modify `docs/HERMES_INSTRUCTIONS.md`

---

**Approved by:** Phase K.1 scan review  
**Recommended next phase:** Phase K.2 — CCI-CH7-SUBJ-002 Candidate Evaluation Plan (if user approves)
