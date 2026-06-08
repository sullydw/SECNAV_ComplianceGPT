# Phase H.10 / Phase I.9 — From-Line Evidence Collection and Regression Hardening Checkpoint

**Commit:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Previous Baseline:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Infrastructure Fix:** `49577d9` — `Test: Fix H.8 runner baseline comparison`  
**Planning Commits:** `8735461` — `Docs: Add Phase H.10 From line evidence plan`; `310fd3a` — `Docs: Refine Phase H.10 From line evidence plan`  
**Full Regression Gate:** 32/32 PASS  
**Correct Python:** `C:\\Users\\drryl\\pinokio\\bin\\miniconda\\python.exe`

---

## 1. What Was Implemented

Phase H.10 / Phase I.9 added evidence fixtures, local corpus patterns, and regression hardening for the advisory validator rule `CCI-ROUTE-011` (standard letters must have a From line, except with window envelope).

### Evidence Fixtures Added

- **20 negative-control fixtures** (`examples/routing_from_h10_neg_01.json` through `routing_from_h10_neg_20.json`):
  - Standard letter with From present (must NOT trigger)
  - Window envelope `true` suppresses (must NOT trigger)
  - Window envelope `"yes"` string truthy suppresses (must NOT trigger)
  - Window envelope `1` int truthy suppresses (must NOT trigger)
  - Missing `doc_type` skips (must NOT trigger)
  - Memorandum, MFR, endorsement, joint letter, multiple-address letter skip (must NOT trigger)
  - From with comma/parenthesis present (must NOT trigger)
  - Null/empty/whitespace From with window envelope (must NOT trigger)
  - Minimal single-char From (must NOT trigger)
  - Numeric string From (must NOT trigger)
  - Full payload with all fields (must NOT trigger)
  - Explicit `window_envelope: false` with From present (must NOT trigger)
  - `standard_letter` doc_type with From present (must NOT trigger)

- **10 positive-control fixtures** (`examples/routing_from_h10_pos_01.json` through `routing_from_h10_pos_10.json`):
  - Missing From field (must trigger)
  - Empty From string (must trigger)
  - Whitespace-only From (must trigger)
  - Tab/newline From (must trigger)
  - `standard_letter` doc_type missing From (must trigger)
  - Null From (must trigger)
  - Dual rule trigger: missing From + numeric office code without `Code` prefix (must trigger both ROUTE-010 and ROUTE-011)
  - Missing From with complex `via` (must trigger)
  - Missing From with complex `copy_to` (must trigger)
  - Missing From with complex `distribution` (must trigger)

- **Local corpus:** `corrections/evidence/from_line_patterns.jsonl` with 50 synthetic patterns covering present/missing From, window envelope variations, and standard-letter vs non-standard document types. **Gitignored; not committed.**

### New Runner Added

- `tools/run_phase_h10_from_line_evidence_regression.py` — 39 checks covering:
  1. All 20 negative-control fixtures exist.
  2. All 10 positive-control fixtures exist.
  3. Negative controls do NOT trigger CCI-ROUTE-011.
  4. Positive controls DO trigger CCI-ROUTE-011.
  5. `errors` list remains empty.
  6. Findings go to `warnings` only.
  7. `window_envelope: true` suppresses.
  8. `window_envelope: "yes"` suppresses (Python truthy).
  9. `window_envelope: 1` suppresses (Python truthy).
  10. Missing `doc_type` skips.
  11. Non-standard doc types skip.
  12. CCI-ROUTE-010 behavior preserved.
  13. H.9 runner still passes (embedded check).
  14. H.8 runner still passes (embedded check).
  15. Local corpus path is gitignored and untracked.
  16. No forbidden files changed (validator, catalog, renderer, prompt, command).

---

## 2. Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No validator logic changes | **PRESERVED** — `src/cci_routing_validate.py` untouched |
| No rule catalog changes | **PRESERVED** — `rules_v6/CCI/cci_ch2_routing_rules.json` untouched |
| No renderer/layout changes | **PRESERVED** — `src/pdf_v6_render.py` untouched |
| No prompt-contract changes | **PRESERVED** — `src/context_resolver.py` untouched |
| No Phase F/G command-layer changes | **PRESERVED** — `src/correction_commands.py`, `src/correction_nl_commands.py` untouched |
| No severity promotion | **PRESERVED** — `CCI-ROUTE-011` remains advisory-only |
| No feature flag/config implementation | **PRESERVED** |
| No approved/pending/session logs committed | **PRESERVED** — all local/gitignored |
| No real data committed | **PRESERVED** |
| CCI-ROUTE-010 preserved | **PRESERVED** — still advisory-only |

---

## 3. Regression Results

| Runner | Checks | Result |
|---|---|---|
| H.10 evidence regression | 39 | **PASS** |
| H.9 From-line validator regression | 18 | **PASS** (embedded in H.10) |
| H.8 third catalog-pilot regression | 16 | **PASS** (embedded in H.10) |
| Full 32-suite gate | 32 | **PASS** |

All runners executed with `C:\Users\drryl\pinokio\bin\miniconda\python.exe`.

---

## 4. Notable Notes

- **Git CRLF warnings:** 30 harmless auto-convert warnings for new JSON fixtures during commit. LF normalized on next touch; all checks passed regardless.
- **H.8 runner infrastructure fix:** Commit `49577d9` corrected cross-phase false positives in H.8 and H.6 baseline-comparison checks by narrowing diff ranges to compare only the implementation commit itself.
- **Window-envelope truthiness:** Current validator uses `payload.get("window_envelope", False)` which treats string `"yes"` and int `1` as truthy. H.10 plan correctly reframed these as current behavior, not failures.

---

## 5. Open Items

| Item | Status |
|---|---|
| Real-world From-line patterns (Navy/Marine Corps) | Deferred — currently synthetic only |
| Strict type checking for `window_envelope` | Deferred — reserved for future validator-hardening phase |
| Severity promotion of CCI-ROUTE-011 | Deferred — requires separate approval + config support |
| Feature flag / config support design | Deferred — conceptual only |
| Fourth catalog pilot candidate | Not yet identified — requires Phase H.11 planning |

---

## 6. Recommended Next Work

Phase H.11 / Phase I.10 should decide **one** of:

1. **Review H.10 evidence** and decide whether `CCI-ROUTE-011` stays advisory-only indefinitely.
2. **Start a fourth low-risk catalog pilot** in subject, ref/encl, date/time, personnel, or acronym domains.
3. **Design feature flag / config support** for future severity promotion.
4. **Keep all advisory rules advisory indefinitely** and maintain 32-suite regression.
5. **Improve rule-catalog governance** (schema validation, audit trails, change review workflow).

All choices are **planning-only until approved**. No code changes without approved planning document.

---

## 7. Files That Changed in This Phase

| File | Action |
|---|---|
| `examples/routing_from_h10_neg_*.json` | Created (20 files) |
| `examples/routing_from_h10_pos_*.json` | Created (10 files) |
| `tools/run_phase_h10_from_line_evidence_regression.py` | Created |
| `corrections/evidence/from_line_patterns.jsonl` | Created (gitignored, not committed) |

### Files That Must Not Be Modified Without Separate Approval

- `src/cci_routing_validate.py`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `src/pdf_v6_render.py`
- `src/context_resolver.py`
- `src/intake_orchestrator.py`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`

---

End of Phase H.10 / Phase I.9 checkpoint.
