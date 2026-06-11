# Phase K.3 — CCI-CH7-SUBJ-002 Dedicated Regression Runner Checkpoint

**Date:** 2026-06-10  
**Commit:** `ec4ddd0`  
**Runner:** `tools/run_phase_k3_subject_terminal_punctuation_regression.py`  
**Suite count after adding runner:** 37 (H.24 36 + K.3 11 as separate runner; H.24 sub-runner count unaffected)

---

## Runner details

| Attribute | Value |
|-----------|-------|
| Filename | `tools/run_phase_k3_subject_terminal_punctuation_regression.py` |
| Entry point | `validate_cci_subject()` from `src/cci_subject_validate.py` |
| Payload type | Inline sanitized/synthetic dicts only |
| External fixtures | None |

## Checks implemented

| # | Category | Description | Result |
|---|----------|-------------|--------|
| 1 | Positive | Period at end triggers SUBJ-002 | PASS |
| 2 | Positive | Question mark at end triggers SUBJ-002 | PASS |
| 3 | Positive | Exclamation at end triggers SUBJ-002 | PASS |
| 4 | Negative | No terminal punctuation does not trigger | PASS |
| 5 | Negative | Internal punctuation does not trigger | PASS |
| 6 | Negative | Comma at end does not trigger | PASS |
| 7 | Negative | Semicolon at end does not trigger | PASS |
| 8 | Negative | Uppercase without terminal punctuation does not trigger | PASS |
| 9 | Negative | Mixed case without terminal punctuation does not trigger | PASS |
| 10 | Cross-rule | Blank subject triggers SUBJ-001, not SUBJ-002 | PASS |
| 11 | Cross-rule | Terminal punctuation + acronym preserves SUBJ-002 error and SUBJ-007 warning | PASS |

**Total: 11/11 PASS**

## Existing regression results

| Runner | Result |
|--------|--------|
| K.3 SUBJ-002 terminal punctuation | **11/11 PASS** |
| H.2 Subject acronym | 12/12 PASS |
| H.3 Route-010 catalog | 15/15 PASS |
| H.4 Office code validator | 18/18 PASS |
| H.6 Office code evidence | 15/15 PASS |
| H.8 Route-011 catalog | 16/16 PASS |
| H.9 From-line validator | 18/18 PASS |
| H.10 From-line evidence | 39/39 PASS |
| H.13 Config | 27/27 PASS |
| H.16 Burn-in | 96/96 PASS |
| H.24 Sanitized fixtures | 36/36 PASS |
| J.12 ROUTE-007 duplicate copy-to | 13/13 PASS |

**Full gate: ALL PASS**

## Authorizations denied (intentionally)

| Action | Authorized |
|--------|------------|
| Modify config | **NO** |
| Modify severity | **NO** |
| Add to allowlist | **NO** |
| Promote to error | **NO** |
| Modify validator | **NO** |
| Modify catalog | **NO** |
| Modify renderer/layout | **NO** |
| Modify prompt/context/intake/UI/command-flow | **NO** |
| Modify Phase F/G command layer | **NO** |
| Commit logs or unsanitized material | **NO** |

## Verdict

**APPROVE Phase K.3 implementation.**

Dedicated regression runner created and all 11 checks pass. Existing runners unaffected. Full gate passes. No config, severity, allowlist, validator, catalog, renderer, layout, prompt, context, intake, UI, or command-layer changes made. Error promotion remains unauthorized.

---

**Recommended next phase:** Phase K.4 — CCI-CH7-SUBJ-002 Regression Coverage Decision
