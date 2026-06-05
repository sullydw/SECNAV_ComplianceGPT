# Phase H.4 / Phase I.3 — Routing Office-Code Prefix Validator Enforcement Plan

**Date:** 2026-06-04  
**Baseline Commit:** `46edcbd` — `CCI: Add routing office code catalog rule (Phase H.3)`  
**Target Rule:** `CCI-ROUTE-010`  
**Planning Status:** planning-only until approved  
**Regression Suites if Implemented:** 28 (27 existing + 1 new Phase H.4 targeted runner)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`

---

## 1. Purpose

This plan defines how to add **validator enforcement** for the already-cataloged routing office-code rule `CCI-ROUTE-010`. The rule is currently in the catalog only (`rule_catalog` target). Phase H.4 moves it into the routing validator so it is actually checked during CCI audit.

---

## 2. Rule Under Enforcement

| Field | Value |
|---|---|
| **Rule ID** | `CCI-ROUTE-010` |
| **Catalog File** | `rules_v6/CCI/cci_ch2_routing_rules.json` |
| **Rule Text** | If the office code is composed of only numbers, add the word `Code` before the numbers. Do not add the word `Code` before an office code that starts with a letter (e.g., `N` or `SUP`). |
| **Source** | SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General |
| **Source File** | `references/SECNAV_M-5216.5_CH-1.txt`, line 1763 |
| **Field Path** | `routing.office_code` |
| **Applies To** | To and Via lines / routing addresses |
| **Severity (catalog)** | `error` |
| **Approved Record** | `agr_20260604_7b5d44a2` |
| **Status** | `implemented` (catalog-only) |

---

## 3. Is Validator Enforcement Appropriate?

**Yes.**

- The rule has **explicit SECNAV source text** with an exact quote.
- The rule is **deterministic**: numeric-only vs. letter-starting is unambiguous.
- The rule has **no renderer/layout implication**: it is about text content in routing lines, not about spacing, margins, fonts, or page breaks.
- The rule has **low blast radius**: it affects only To/Via office-code strings, not body paragraphs, subject lines, or enclosures.
- The rule has **easy provenance**: one paragraph, one quote, one figure example.
- The existing routing validator (`cci_routing`) already validates routing structures; adding office-code prefix checking is a natural extension.

---

## 4. Recommended Enforcement Level

**Start at `advisory` (non-blocking), following the Phase H.2 precedent for `CCI-CH7-SUBJ-007`.**

Rationale:
- The rule is new in validator form; we have no real-world fixture coverage yet.
- Office codes can appear in many formats (parenthetical, inline, after titles, in Via numbering).
- A false positive on a valid command name or title would be disruptive if blocking.
- Advisory allows gathering feedback without breaking existing workflows.

**Promotion path:** After 2+ sessions of real-world testing with no false positives, plan Phase H.5 to promote `CCI-ROUTE-010` from advisory to `error` (blocking). This requires a separate planning document.

---

## 5. Detection Design

### 5.1 What to Detect

Two complementary checks:

**Check A — Missing `Code` on numeric-only office codes:**
- Input: an office-code string from a To or Via addressee.
- Condition: the string is composed entirely of digits (e.g., `12345`, `00932`).
- Violation: the string does NOT have the word `Code` immediately before it.
- Example violation: `Commanding Officer, 12345` should be `Commanding Officer, Code 12345`.

**Check B — Improper `Code` on letter-starting office codes:**
- Input: an office-code string from a To or Via addressee.
- Condition: the string starts with a letter (e.g., `N1`, `SUP`, `MFR`).
- Violation: the word `Code` appears immediately before the string.
- Example violation: `Commanding Officer, Code N1` should be `Commanding Officer, N1`.

### 5.2 Tokenization and Matching

- Extract the office-code portion from each addressee string.
- An office code is the **last token or parenthetical group** in an addressee line, typically appearing after a comma or inside parentheses.
- If the office code is inside parentheses, strip the parentheses before checking.
- If the office code appears after a comma, split on comma and take the last segment, then strip whitespace.
- **Numeric check:** `re.fullmatch(r"\d+", token)` — true if and only if the token is all digits.
- **Letter-starting check:** `token[0].isalpha()` — true if the first character is a letter.
- **Code-prefix check:** look for the exact word `Code` immediately before the token (case-insensitive, word-boundary sensitive).

### 5.3 Scoping — To and Via Lines Only

The rule applies only to routing addresses, not to body text, subject lines, or enclosures.

Validator scope:
- `routing.addressees` — each To-line addressee.
- `routing.via` — each Via-line addressee.
- Do NOT check `routing.copy_to` — office codes in copy-to lines follow the same rule, but the SECNAV citation specifically references "To Line, General" (paragraph 7-2.7a). Copy-to enforcement can be added later with separate provenance.
- Do NOT check body paragraphs, reference lines, or enclosures.

---

## 6. False-Positive Avoidance

### 6.1 Known Risk Areas

1. **Command names that look like office codes:** `Commander, U.S. Pacific Fleet` — no office code here, just a title.
2. **Parenthetical clarifications:** `Commanding Officer (Code 12345)` vs. `Commanding Officer (12345)` — parenthetical form is common; the validator must handle both.
3. **Via numbering:** `Via (1): Commanding Officer, Code 12345` — the `Code` should be checked after stripping the Via prefix.
4. **Joint letter addressees:** `Commanding Officer, Code 12345 / Commanding Officer, N1` — both forms may appear in the same letter.

### 6.2 Mitigations

- Only check tokens that are plausibly office codes:
  - Minimum length: 1 character.
  - Maximum length: 10 characters (reasonable for known office code formats).
  - Exclude tokens that contain spaces (they are likely titles, not codes).
- Require the office code to be the **final token** in the addressee string or inside the **final parenthetical group**.
- Do not flag tokens that appear mid-sentence unless they are in the office-code position.
- Use word-boundary regex for `Code` detection: `r"\bCode\s+"` to avoid matching inside words like `Decode`.

---

## 7. False-Negative Avoidance

- Check every addressee in `routing.addressees` and `routing.via`.
- Do not skip addressees that have already passed other routing checks (Via numbering, copy-to overlap, etc.).
- Handle both parenthetical and comma-separated office-code forms.
- Handle both uppercase and lowercase `Code` (normalize to lowercase for comparison).

---

## 8. SECNAV Provenance in Validator Code

Every validator message and docstring must include:

- **Rule ID:** `CCI-ROUTE-010`
- **Source:** `SECNAV M-5216.5`
- **Source Location:** `Chapter 7, paragraph 7-2.7a, To Line, General`
- **Exact Quote:** `"If the office code is composed of only numbers, add the word 'Code' before the numbers. Do not add the word 'Code' before an office code that starts with a letter (e.g., 'N' or 'SUP')."`

Docstring template:
```python
def _check_office_code_prefix(addressee: str) -> List[dict]:
    """
    CCI-ROUTE-010: Office Code Prefix Rule.
    Source: SECNAV M-5216.5, Chapter 7, paragraph 7-2.7a, To Line, General.
    Quote: "If the office code is composed of only numbers, add the word
    'Code' before the numbers. Do not add the word 'Code' before an office
    code that starts with a letter (e.g., 'N' or 'SUP')."

    Checks that numeric-only office codes have 'Code' prefixed, and that
    letter-starting office codes do NOT have 'Code' prefixed.

    Advisory (non-blocking) until Phase H.5 promotion.
    """
```

Message format:
```
CCI-ROUTE-010: numeric office code missing 'Code' prefix: <code> — SECNAV M-5216.5 Ch7 para 7-2.7a
CCI-ROUTE-010: letter-starting office code should not use 'Code' prefix: <code> — SECNAV M-5216.5 Ch7 para 7-2.7a
```

---

## 9. Implementation Target

**`src/cci_routing_validate.py`**

Rationale:
- The routing validator already processes `routing.addressees` and `routing.via`.
- Adding a small helper function is lower risk than creating a new validator file.
- The existing routing validator emits `warning`-level findings for heuristic checks (ROUTE-001 through ROUTE-009); adding an `advisory`-level check is consistent.
- No new validator registration needed; the existing `cci_routing` validator name is already referenced in the catalog entry.

### 9.1 Proposed Code Changes

Add one helper function and one loop call:

```python
def _check_office_code_prefix(addressee: str) -> List[dict]:
    """CCI-ROUTE-010 helper. See docstring template in Section 8."""
    findings = []
    # Extract candidate office code from addressee string
    # ... (implementation details to be determined at implementation time)
    return findings
```

Call sites in the main routing validate function:
- After existing checks on each `addressee` in `routing.addressees`.
- After existing checks on each `via_addressee` in `routing.via`.

Do NOT modify:
- The signature of the main `validate()` function.
- The return schema (list of dicts with `rule_id`, `severity`, `message`).
- Any existing routing check logic.

---

## 10. Feature Flag Decision

**Not required for advisory level.**

Rationale:
- Advisory findings are non-blocking; they do not prevent rendering or submission.
- They appear in the CCI audit report alongside other warnings and advisories.
- If a user wants to suppress them, the existing `--skip-advisory` or `--severity-min` mechanisms (if any) can be used.
- A feature flag becomes necessary only when promoting to `warning` or `error` (blocking) level in Phase H.5.

**Phase H.5 promotion will require a feature flag or config mechanism** if the promotion is to `error`.

---

## 11. Targeted Regression Runner

Create:

`tools/run_phase_h4_routing_office_code_validator_regression.py`

**Minimum 12 checks:**

1. Validator module loads successfully.
2. `_check_office_code_prefix` function exists.
3. Numeric-only office code `12345` missing `Code` triggers advisory.
4. Numeric-only office code `00932` missing `Code` triggers advisory.
5. Numeric-only office code with `Code 12345` does NOT trigger advisory.
6. Letter-starting office code `N1` with `Code N1` triggers advisory.
7. Letter-starting office code `SUP` with `Code SUP` triggers advisory.
8. Letter-starting office code `N1` without `Code` does NOT trigger advisory.
9. Normal command name without office code does NOT trigger advisory (negative control).
10. Parenthetical office code `(12345)` missing `Code` triggers advisory.
11. Parenthetical office code `(Code 12345)` does NOT trigger advisory.
12. No renderer/layout files changed for H.4.
13. No prompt-contract files changed for H.4.
14. No Phase F/G command-layer files changed for H.4.
15. Approved/pending logs are not tracked/staged.
16. Existing H.3 targeted runner still passes (H.3 artifacts remain present).

**Expected result:** 16/16 checks PASS.

---

## 12. Full Regression Expectation

If Phase H.4 is implemented with the new targeted runner, the full regression set becomes **28 suites**:

1. `tools/run_phase_h4_routing_office_code_validator_regression.py` — NEW, 16 checks.
2. `tools/run_phase_h3_second_rule_catalog_regression.py` — 15 checks.
3. `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12 checks.
4. `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — 11 checks.
5. `tools/run_correction_implementation_regression.py` — 45 checks.
6. `tools/run_correction_nl_command_regression.py` — 151 checks.
7. `tools/run_correction_command_regression.py` — 45 checks.
8. `tools/run_correction_review_regression.py` — 30 checks.
9. `tools/run_correction_pending_regression.py` — 33 checks.
10. `tools/run_correction_profile_promotion_regression.py` — 33 checks.
11. `tools/run_correction_classify_regression.py` — Phase B.
12. `tools/run_intake_regression.py`
13. `tools/run_correction_regression.py`
14. `tools/run_correction_session_regression.py`
15. `tools/run_profile_regression.py`
16. `tools/run_cci_audit_regression.py`
17. `tools/run_context_schema_regression.py`
18. `tools/run_cci_subject_regression.py`
19. `tools/run_cci_ref_encl_regression.py`
20. `tools/run_cci_acronym_regression.py`
21. `tools/run_cci_date_time_regression.py`
22. `tools/run_cci_personnel_regression.py`
23. `tools/run_cci_poc_regression.py`
24. `tools/run_cci_routing_regression.py`
25. `tools/run_c7_phase1_regression.py`
26. `tools/run_c8_regression.py`
27. `tools/run_c9_regression.py`
28. `tools/run_c10_regression.py`

All 28 suites must pass before any commit.

---

## 13. Rollback Plan

If Phase H.4 causes unexpected failures:

1. Revert the commit that added the validator changes.
2. The catalog entry `CCI-ROUTE-010` remains in `rules_v6/CCI/cci_ch2_routing_rules.json` — it is harmless as text-only.
3. Remove the targeted regression runner `tools/run_phase_h4_routing_office_code_validator_regression.py`.
4. Re-run the 27-suite gate without H.4.
5. All earlier phases (H.3, H.2, H.1, H, G, F, E, D, C, B, A) remain intact.

Rollback risk: **low** — one helper function in one validator file.

---

## 14. Files That May Be Modified in Future Implementation

| File | Change |
|---|---|
| `src/cci_routing_validate.py` | Add `_check_office_code_prefix()` helper; call it during addressee and via validation. |

---

## 15. Files That Must NOT Be Modified

| File | Why |
|---|---|
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract runtime changes. |
| `src/correction_commands.py` | No Phase F command-layer changes. |
| `src/correction_nl_commands.py` | No Phase G command-layer changes. |
| `rules_v6/CCI/cci_ch2_routing_rules.json` | No catalog text changes (rule already exists from Phase H.3). |
| `rules_v6/CCI/cci_ch7_subject_rules.json` | No subject catalog changes. |
| `src/cci_subject_validate.py` | No subject validator changes. |
| `src/cci_acronym_validate.py` | No acronym validator changes. |
| `corrections/approved_rule_promotions.json` | Remains local/gitignored; do not commit. |
| `corrections/pending_corrections.jsonl` | Remains local/gitignored; do not commit. |
| Any real command/user profile | Do not commit contact data or local profiles. |

---

## 16. What Phase H.4 Must NOT Do

- **No renderer/layout changes.** Office-code prefix checking is about text content, not about PDF geometry, margins, fonts, or spacing.
- **No broad routing validator rewrite.** Only add a small helper function; preserve all existing routing checks (Via numbering, copy-to overlap, format selection, etc.).
- **No automatic enforcement from approved logs.** The validator checks the JSON payload at audit time; it does not read `corrections/approved_rule_promotions.json`.
- **No AI-only implementation decisions.** Every detection rule must be deterministic, testable, and grounded in the SECNAV source text.
- **No prompt-contract runtime changes.** The context resolver, intake orchestrator, and validator runner contracts remain unchanged.
- **No Phase F/G command-layer changes.** No new slash commands or NL command mappings.
- **No approved/pending logs committed.** `corrections/approved_rule_promotions.json` and `corrections/pending_corrections.jsonl` remain gitignored.
- **No real command/user data committed.** No contact info, no local profiles, no session stores.
- **No background automation.** The validator runs only when explicitly invoked via `src/validator_runner.py` or the CLI.

---

## 17. Recommended Defaults Summary

| Decision | Recommended Default |
|---|---|
| **Implementation target** | `src/cci_routing_validate.py` |
| **Enforcement level** | `advisory` (non-blocking) |
| **Feature flag** | Not required for advisory |
| **Regression coverage** | 16-check targeted runner + 28-suite full gate |
| **Promotion path** | Phase H.5 to `error` after real-world testing |
| **Rollback risk** | Low — one helper function, one runner file |

---

## 18. Open Questions Needing Approval

1. **Should the initial enforcement level be `advisory` or `warning`?**
   - Advisory is safer; warning is more visible but risks false-positive disruption.
   - **Default:** advisory.

2. **Should the check also cover `routing.copy_to`?**
   - The SECNAV citation references "To Line, General" (paragraph 7-2.7a), which primarily covers To and Via.
   - Copy-to office codes likely follow the same convention but lack explicit provenance.
   - **Default:** check To and Via only; defer copy-to to a separate candidate with its own citation.

3. **Should parenthetical office codes be checked?**
   - Yes — `Commanding Officer (12345)` is a common format and should be covered.
   - **Default:** check both parenthetical and comma-separated forms.

4. **Should the check handle lowercase `code`?**
   - Yes — normalize to lowercase for comparison; the manual uses `"Code"` with capital C.
   - **Default:** case-insensitive `Code` detection.

5. **Should synthetic fixtures be added to `examples/`?**
   - Yes — at least 4 fixtures: numeric missing Code, numeric with Code, letter with improper Code, letter without Code.
   - **Default:** add 4 synthetic example fixtures.

6. **What is the maximum office-code length to check?**
   - **Default:** 10 characters.

7. **Should the H.4 runner verify that existing H.3 catalog runner still passes?**
   - Yes — cross-phase regression protection.
   - **Default:** include H.3 artifact-preservation check in H.4 runner.

8. **Should Phase H.4 be approved now, or deferred to a later session?**
   - This is a planning document; no implementation should occur until explicitly approved.
   - **Default:** defer to next session unless user explicitly approves now.

---

## 19. Approval Gate

Phase H.4 implementation may proceed only after:

- [ ] This planning document is read and acknowledged by the user.
- [ ] All 8 open questions are answered or accepted with defaults.
- [ ] User explicitly states approval to implement Phase H.4.
- [ ] A separate implementation session is started with the approved plan as source of truth.

Do not implement Phase H.4 without explicit user approval.

---

End of Phase H.4 / Phase I.3 Routing Office-Code Prefix Validator Enforcement Plan.
