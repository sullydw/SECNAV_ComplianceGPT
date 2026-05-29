# CCI Content Compliance Checkpoint

## Baseline Commit

- **Commit hash:** `693786fad6b9433ea7c13e88a87766b147ac35e0`
- **Tag:** none at HEAD
- **Date:** 2026-05-29
- **Branch:** `main`
- **Status:** clean, up to date with `origin/main`

## Purpose of the CCI Layer

The Correspondence Content Intelligence (CCI) layer is a deterministic and heuristic content-validation system that sits above the layout/render pipeline. It checks that the *textual content* of a correspondence draft complies with SECNAV M-5216.5 rules, independent of whether the PDF layout is correct. CCI validators examine subject lines, references/enclosures, acronyms, dates, and military time usage inside the JSON payload before rendering.

All CCI work is **additive** — no existing C7-C10 layout profiles, validators, renderers, examples, or README files have been modified.

## Implemented CCI Validators

### 1. CCI Subject-Line Validator
- **Source:** Chapter 7, paragraph 7-2.9 and Figure 7-1
- **Validator file:** `src/cci_subject_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch7_subject_rules.json`
- **Regression runner:** `tools/run_cci_subject_regression.py`
- **Example files:**
  - `examples/audit_cci_subject_valid.json`
  - `examples/audit_cci_subject_invalid.json`
  - `examples/audit_cci_subject_warning.json`

**What it checks:**
- Subject content is all caps for letter types that require it (standard, multiple-address, endorsement, joint).
- Subject line has no terminal punctuation (period, question mark, exclamation mark).
- Subject field does not embed a literal `Subj:` label.
- Warns if subject contains acronyms (unless on a narrow approved list).
- Warns if subject is vague or too short (fewer than three meaningful words).

**What it does not check yet:**
- Substantive accuracy of the subject against the body.
- Subject-line compliance for memo types (MFR, from-to, plain-paper, letterhead) — rules are defined but not yet enforced beyond terminal punctuation and embedded-label checks.

---

### 2. CCI Reference/Enclosure Validator
- **Source:** Chapter 7, paragraph 7-3.3 and Figure 7-1
- **Validator file:** `src/cci_ref_encl_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch7_ref_encl_rules.json`
- **Regression runner:** `tools/run_cci_ref_encl_regression.py`
- **Example files:**
  - `examples/audit_cci_ref_encl_valid.json`
  - `examples/audit_cci_ref_encl_invalid_no_citation.json`
  - `examples/audit_cci_ref_encl_invalid_duplicate.json`
  - `examples/audit_cci_ref_encl_invalid_wrong_order.json`
  - `examples/audit_cci_ref_encl_warning_sep_cover.json`

**What it checks:**
- Every listed reference is cited or substantively mentioned in the body.
- Every listed enclosure is substantively mentioned in the body.
- References appear in the order of their first body citation.
- Enclosures appear in the order of their first body mention.
- The same item does not appear as both a reference and an enclosure.
- Non-endorsement reference markers follow lowercase alphabetical sequence `(a), (b), (c)` without skips or duplicates.
- Non-endorsement enclosure markers follow numeric sequence `(1), (2), (3)` without skips or duplicates.
- Warns for "separate cover" or "provided separately" notations.
- Warns for vague reference/enclosure entries with fewer than three meaningful tokens.
- Warns for bare marker citations in the body without substantive explanatory text nearby.

**What it does not check yet:**
- Endorsement-specific continuation of prior reference/enclosure marker sequences — this remains the responsibility of `src/c9_validate.py` (see rule `CCI-REF-NOTE-001`).

---

### 3. CCI Acronym First-Use Validator
- **Source:** Chapter 2, paragraph 2-4.1
- **Validator file:** `src/cci_acronym_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_acronym_rules.json`
- **Regression runner:** `tools/run_cci_acronym_regression.py`
- **Example files:**
  - `examples/audit_cci_acronym_valid.json`
  - `examples/audit_cci_acronym_invalid_undefined.json`
  - `examples/audit_cci_acronym_warning_approved.json`

**What it checks:**
- Every acronym used in the body is spelled out in full the first time, followed by the acronym in parentheses.
- Flags acronyms used before their first parenthetical definition as non-compliant.
- Warns when approved acronyms (SECNAV, DON, USN, USMC, DoD, NATO, SSIC, MCO, OPNAV, NAVMC, CNO, CMC, FOIA, PII, CUI, FOUO) are used without explicit definition — still allowed, but flagged for clarity.
- Warns when an acronym is defined in the body but never used afterward.

**What it does not check yet:**
- Acronyms inside subject lines (handled by the subject-line validator).
- Acronyms inside signatures, copy-to, or distribution lines.
- Context-aware detection of whether an acronym is truly "first use" across multi-document endorsement chains.

---

### 4. CCI Date and Military-Time Validator
- **Source:** Chapter 2, paragraph 2-4.2
- **Validator file:** `src/cci_date_time_validate.py`
- **Rule file:** `rules_v6/CCI/cci_ch2_date_time_rules.json`
- **Regression runner:** `tools/run_cci_date_time_regression.py`
- **Example files:**
  - `examples/audit_cci_date_time_valid.json`
  - `examples/audit_cci_date_time_invalid_date_format.json`
  - `examples/audit_cci_date_time_invalid_military_time.json`
  - `examples/audit_cci_date_time_warning_civilian_date.json`

**What it checks:**
- Military time is written as four digits `0000` through `2359` with no colon.
- Military time values are within valid range (rejects `2400`, `2561`, etc.).
- Standard text date uses `day Month year` with no leading zero on single-digit day (e.g., `5 May 2026`).
- Top-level `date` field matches the standard military text date format.
- Warns for civilian date format (`Month day, year`) detected in body text.
- Warns for abbreviated two-digit year in body text.
- Warns if the top-level date does not clearly match the expected format.

**What it does not check yet:**
- Date consistency across endorsement chains (e.g., endorsement date must be on or after basic letter date).
- Calendar validity (e.g., `31 Feb 2026`) — format and range are checked, but not whether the day exists in the month.
- Time-zone annotations or Zulu-time conversion.

---

## Regression Commands

```bash
# CCI regressions
python tools/run_cci_subject_regression.py
python tools/run_cci_ref_encl_regression.py
python tools/run_cci_acronym_regression.py
python tools/run_cci_date_time_regression.py

# C7-C10 layout/render regressions
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
python tools/run_c9_regression.py
python tools/run_c10_regression.py
```

## Regression Results (at checkpoint)

| Regression | Result |
|---|---|
| CCI Subject | PASS |
| CCI Ref/Encl | PASS |
| CCI Acronym | PASS |
| CCI Date/Time | PASS |
| C7 Phase 1 | PASS |
| C8 | PASS |
| C9 | PASS |
| C10 | PASS |

All eight regressions passed on the checkpoint commit.

## Baseline Integrity Note

The C7-C10 layout and render baseline remains fully intact. Every CCI validator was added as a new file; no existing renderer, validator, layout profile, example, or regression tool was edited. The CCI layer is strictly additive.

## Recommended Next CCI Areas

These are proposed for future CCI work, in no particular order:

1. **Personnel identification** — validate that `From`, `To`, `Via`, and signature blocks use proper military rank/title conventions and that acting/by-direction notation is consistent.
2. **Point-of-contact expectations** — detect when correspondence requires a point-of-contact line (e.g., policy guidance, action requests) and warn if it is missing.
3. **Routing / Via / Copy-to intelligence** — validate that Via addressees are listed in correct order, that Copy-to includes required recipients per SECNAV distribution rules, and that endorsement copy-to includes prior endorsers and originator.
4. **Privacy / security / PII warning layer** — scan body text for potential PII patterns (SSN, DoD ID, home addresses, personal phone numbers) and flag for review before release.
5. **Context schema / intake orchestration** — define a unified intake schema so multiple CCI validators can run in a single pass and produce a consolidated audit report with cross-referenced rule IDs.
6. **GitHub Actions integration for CCI regressions** — add a CI workflow that runs all four CCI regression runners on every push/PR, similar to the existing C7-C10 regression workflow.

---

*Checkpoint generated 2026-05-29. See commit `693786fad6b9433ea7c13e88a87766b147ac35e0`.*
