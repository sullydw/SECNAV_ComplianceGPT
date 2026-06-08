# Phase H.11 / Phase I.10 — From-Line Evidence Review Checkpoint

**Planning Commit:** `4c3cdb8` — `Docs: Add Phase H.11 From line evidence review plan`  
**Evidence Review Checkpoint Commit:** `52076a1` — `Docs: Record Phase H.11 evidence review checkpoint`  
**Current Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Previous Baseline:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Full Regression Gate:** 32/32 PASS  
**Correct Python:** `C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe`

---

## 1. Approval Verdict

**APPROVE PHASE H.11 PLAN**

- H.11 plan is approved as planning documentation source of truth.
- `CCI-ROUTE-011` remains advisory-only for now.
- H.10 evidence is sufficient for advisory maintenance.
- H.10 evidence is **not** sufficient for warning/error promotion.
- Severity promotion remains deferred.
- Feature flag/config planning is required before any future promotion.
- `window_envelope` remains read-only unless separately approved.
- Productive next path: **fourth low-risk catalog-only pilot planning**.

---

## 2. What Was Reviewed

Phase H.11 reviewed the following evidence for `CCI-ROUTE-011`:

- **20 negative-control fixtures:** confirmed none trigger CCI-ROUTE-011.
- **10 positive-control fixtures:** confirmed all trigger CCI-ROUTE-011.
- **50 synthetic corpus patterns** in `corrections/evidence/from_line_patterns.jsonl` (gitignored, not committed).
- **39-check H.10 regression runner** covering fixture existence, negative/positive validation, window-envelope suppression, doc_type skipping, dual-rule trigger, cross-runner preservation.
- **H.9 validator** advisory-only enforcement: `_check_from_line_required()` in `src/cci_routing_validate.py`.
- **H.8 rule catalog** entry `CCI-ROUTE-011` in `rules_v6/CCI/cci_ch2_routing_rules.json`.

---

## 3. Advisory-Only Rationale

| Criterion | Assessment |
|---|---|
| Deterministic rule | YES — From line present/absent is binary |
| Synthetic fixture coverage | Good for advisory — 20 neg + 10 pos |
| Real-world Navy/Marine Corps patterns | **Missing** — only synthetic patterns |
| Window-envelope exception | Handles known exception from source text |
| Document type scope | Narrow — `DT_STD_LTR`/`standard_letter` only |
| False positive rate in fixtures | Zero in current suite |
| Readiness for warning/error | **No** — insufficient real-world evidence |
| Feature flag/config support | **Not implemented** — required before promotion |

**Conclusion:** Keep advisory-only. Do not promote until real-world evidence reviewed and config support implemented.

---

## 4. Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No validator logic changes | **PRESERVED** — `src/cci_routing_validate.py` untouched in H.11 |
| No rule catalog changes | **PRESERVED** — `rules_v6/CCI/cci_ch2_routing_rules.json` untouched |
| No renderer/layout changes | **PRESERVED** — `src/pdf_v6_render.py` untouched |
| No prompt-contract changes | **PRESERVED** — `src/context_resolver.py` untouched |
| No Phase F/G command-layer changes | **PRESERVED** — `src/correction_commands.py`, `src/correction_nl_commands.py` untouched |
| No severity promotion | **PRESERVED** — `CCI-ROUTE-011` advisory-only |
| No feature flag/config implementation | **PRESERVED** |
| No approved/pending/session logs committed | **PRESERVED** — all local/gitignored |
| No real data committed | **PRESERVED** |
| CCI-ROUTE-010 preserved | **PRESERVED** — still advisory-only |

---

## 5. Requirements for Future Severity Promotion

Any future promotion of `CCI-ROUTE-011` from advisory to warning/error requires:

1. **Real-world evidence review:** collect actual Navy/Marine Corps standard letter samples.
2. **Feature flag/config design and implementation:** severity override mechanism.
3. **Explicit user approval:** separate design review and go/no-go decision.
4. **Targeted regression update:** add promotion-specific checks.
5. **Full regression gate:** 32 suites minimum, 33 if new runner added.

---

## 6. Recommended Next Work

### Phase H.12 / Phase I.11 — Fourth Catalog-Only Pilot Planning (Planning-Only Until Approved)

Phase H.12 must be planned and approved before any code changes.

Design decisions required:

1. **Candidate domain to search first:**
   - Subject (`cci_ch7_subject_rules.json`)
   - Reference/enclosure (`cci_ch7_ref_encl_rules.json`)
   - Date/time (`cci_ch7_date_time_rules.json`)
   - Personnel (`cci_ch7_personnel_rules.json`)
   - Acronym (`cci_ch2_acronym_rules.json`)
   - Other CCI domain

2. **Candidate selection criteria:**
   - Clear SECNAV M-5216.5 chapter/paragraph citation.
   - Low risk (no layout implications, no renderer dependency).
   - Deterministic yes/no compliance.
   - No overlap with existing rules.

3. **Source/provenance verification:**
   - Manual chapter/paragraph text.
   - Figure title/caption.
   - Instructional text inside examples.
   - Actual visual/layout geometry if applicable.

4. **Duplicate/overlap checks:**
   - Verify against `CCI-CH7-SUBJ-006`, `CCI-ROUTE-010`, `CCI-ROUTE-011`.
   - Check all `rules_v6/CCI/*.json` files.

5. **Rule-catalog-only target:**
   - No validator changes.
   - No renderer changes.
   - No prompt-contract changes.
   - Phase D/E workflow required.

6. **Future regression gate:**
   - Current 32 suites.
   - 33 suites if new H.12 runner added.

---

## 7. Files That Changed in This Phase

| File | Action |
|---|---|
| `docs/planning/phase_h11_from_line_evidence_review_plan.md` | Exists (approved planning document) |

### No New Files Created in H.11

### Files That Must Not Be Modified Without Separate Approval

- `src/cci_routing_validate.py`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `src/pdf_v6_render.py`
- `src/context_resolver.py`
- `src/intake_orchestrator.py`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`

---

End of Phase H.11 / Phase I.10 checkpoint.
