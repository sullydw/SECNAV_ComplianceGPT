# Phase H.10 / Phase I.9 — Evidence Collection and Regression Hardening for CCI-ROUTE-011

**Date:** 2026-06-08  
**Latest Docs Checkpoint:** `13e77e9` — `Docs: Record Phase H.9 From line validator checkpoint`  
**Current Functional Baseline:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Previous Planning Baseline:** `17bae2f` — Phase H.9 From-line validator plan approved  
**Current Regression Set:** 31 suites (all PASS)  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`  
**Planning Status:** planning-only until reviewed and approved  
**Implementation Gate:** 31 suites if extending H.9 runner only; 32 suites if adding a new H.10 targeted runner

---

## 1. Purpose

Phase H.10 collects evidence and hardens regression coverage for `CCI-ROUTE-011` **without** changing its severity.

Phase H.9 added advisory/non-blocking From-line validator enforcement. Phase H.10 now closes evidence gaps before any future severity promotion or feature-flag work. It adds fixtures, hardens runners, and populates a local gitignored evidence corpus.

**This plan does not authorize severity promotion. It does not authorize config implementation. It plans only fixtures, runner hardening, and safe storage.**

---

## 2. Current Behavior Summary

### Advisory Validator for `CCI-ROUTE-011`

- **Validator file:** `src/cci_routing_validate.py`
- **Helper:** `_check_from_line_required()` — added in Phase H.9
- **Integration:** called inside `validate_cci_routing()` without signature change
- **Return type:** `tuple[list[str], list[str]]` as `(errors, warnings)` — preserved
- **Enforcement level:** advisory/non-blocking only
- **Errors list:** remains empty for this rule
- **Warnings list:** advisory findings appended as formatted strings

### Detection Scope

- Checked on: `routing.from` field
- Checked only when: `doc_type` is `DT_STD_LTR` or `"standard_letter"`
- Not checked when: `doc_type` is missing, memorandum, endorsement, joint_letter, multiple_address_letter, or any other type
- Suppressed when: `window_envelope: true` in payload

### Detection Patterns

| Scenario | Current Result |
|---|---|
| `DT_STD_LTR`, `from` absent | Advisory warning — missing `From:` |
| `DT_STD_LTR`, `from: ""` | Advisory warning — empty `From:` |
| `DT_STD_LTR`, `from: "   "` | Advisory warning — whitespace-only `From:` |
| `DT_STD_LTR`, `from: "Commanding Officer"` | OK — present |
| `DT_STD_LTR`, `window_envelope: true`, no `from` | OK — suppressed |
| `DT_STD_LTR`, `from` present | OK — no finding |
| Missing `doc_type`, no `from` | OK — skipped |
| Memorandum, no `from` | OK — skipped |
| Endorsement, no `from` | OK — skipped |
| Joint letter, no `from` | OK — skipped |
| Multiple-address letter, no `from` | OK — skipped |

---

## 3. Why Phase H.10 Should Collect Evidence Before Severity Promotion

Phase H.9 added advisory validator enforcement for these reasons:

1. **Provenance confidence is high** — exact quote verified on PDF page 50.
2. **Detection is deterministic** — presence/absence of `routing.from` is a boolean test.
3. **Blast radius is narrow** — one field, one document type.
4. **Advisory level allows gathering feedback** before any blocking enforcement.

However, these gaps remain:

1. **False-positive risk is unmeasured on real-world patterns.** Current coverage is only 8 synthetic fixtures. We need more negative controls for edge cases (partial From fields, unusual doc_type strings, mixed payloads).
2. **No real-world From-line corpus exists.** All current coverage is synthetic. Evidence collection is required before any severity promotion.
3. **H.9 runner does not verify errors-list emptiness explicitly.** Hardening the runner is required to prove advisory-only behavior is preserved.
4. **H.9 runner does not test all skip conditions exhaustively.** Missing `doc_type`, mixed document types, and edge-case `window_envelope` values need coverage.

Phase H.10 closes these gaps without changing severity.

---

## 4. Evidence Collection Plan

### 4.1 Negative-Control Fixtures (must NOT trigger)

At least **20** synthetic negative-control fixtures.

These patterns must NOT produce warnings. If the validator flags any, it is a false positive.

| # | Pattern | Category |
|---|---|---|
| 1 | `DT_STD_LTR` with `from` present | Standard pass |
| 2 | `DT_STD_LTR` with `window_envelope: true`, no `from` | Window-envelope suppression |
| 3 | No `doc_type`, no `from` | Missing doc_type skip |
| 4 | `DT_MEMO_FROM_TO_PLAIN`, no `from` | Memorandum skip |
| 5 | `DT_MFR`, no `from` | MFR skip |
| 6 | `endorsement`, no `from` | Endorsement skip |
| 7 | `joint_letter`, no `from` | Joint letter skip |
| 8 | `multiple_address_letter`, no `from` | Multiple-address letter skip |
| 9 | `DT_STD_LTR` with `from: "C O, USS EXAMPLE"` | Normal From with comma |
| 10 | `DT_STD_LTR` with `from: "Commanding Officer (Acting)"` | From with parenthesis |
| 11 | `DT_STD_LTR` with `window_envelope: "yes"` (string), no `from` | Non-boolean window_envelope — not true |
| 12 | `DT_STD_LTR` with `window_envelope: 1` (int), no `from` | Non-boolean window_envelope — not true |
| 13 | `DT_STD_LTR` with `from: null` and `window_envelope: true` | Suppressed despite null |
| 14 | `DT_STD_LTR` with `from: ""` and `window_envelope: true` | Suppressed despite empty |
| 15 | `DT_STD_LTR` with `from: "   "` and `window_envelope: true` | Suppressed despite whitespace |
| 16 | `standard_letter` with `from` present | Alternate doc_type pass |
| 17 | `DT_STD_LTR` with `from: "X"` | Minimal valid From |
| 18 | `DT_STD_LTR` with `from: "0"` | Numeric From — still present |
| 19 | `DT_STD_LTR` with extra fields (`via`, `copy_to`) and `from` present | Full payload pass |
| 20 | `DT_STD_LTR` with `from` and `window_envelope: false` | Explicit false, From present |

### 4.2 Positive-Control Fixtures (must trigger)

At least **10** synthetic positive-control fixtures.

These patterns MUST produce exactly one `CCI-ROUTE-011` advisory warning. If any fail to trigger, it is a false negative.

| # | Pattern | Category |
|---|---|---|
| 1 | `DT_STD_LTR`, no `from` field | Missing From — baseline |
| 2 | `DT_STD_LTR`, `from: ""` | Empty From |
| 3 | `DT_STD_LTR`, `from: "   "` | Whitespace-only From |
| 4 | `DT_STD_LTR`, `from: "\t\n"` | Tab/newline From |
| 5 | `standard_letter`, no `from` | Alternate doc_type missing From |
| 6 | `DT_STD_LTR`, `from: null` | Null From |
| 7 | `DT_STD_LTR` with numeric `to` addressee (also triggers ROUTE-010) | Dual-rule trigger |
| 8 | `DT_STD_LTR` with `from` missing and `via` present | Complex payload missing From |
| 9 | `DT_STD_LTR` with `from` missing and `copy_to` present | Complex payload missing From |
| 10 | `DT_STD_LTR` with `from` missing and `distribution` present | Complex payload missing From |

### 4.3 Synthetic-Realistic Patterns in Local Storage

A local gitignored corpus of at least **50** synthetic-realistic From-line and window-envelope patterns under `corrections/evidence/from_line_patterns.jsonl`.

These patterns represent plausible Navy/Marine Corps payload shapes:

- Standard letter with full command From line.
- Standard letter with abbreviated From line.
- Window-envelope letter without From line.
- Memorandum (From-To) without From line (should be skipped).
- Endorsement without From line (should be skipped).
- Joint letter with single From line.
- Multiple-address letter with single From line.
- Standard letter with `from` but missing `to`.
- Standard letter with `from` and multiple `via` entries.
- Standard letter with `from` and parenthetical enclosure in `to`.

The corpus is **gitignored** and is not committed to the repository. It is used for local developer reference and future real-world pattern comparison.

---

## 5. H.9 Runner Hardening

Phase H.9 introduced `tools/run_phase_h9_from_line_validator_regression.py` with 18 checks. Phase H.10 should extend or supplement this runner with the following hardening checks:

### 5.1 Required Explicit Checks

| # | Check | Expected Result |
|---|---|---|
| 1 | `_check_from_line_required` helper exists in `src/cci_routing_validate.py` | PASS |
| 2 | Missing `from` on `DT_STD_LTR` triggers advisory | PASS |
| 3 | Empty `from` on `DT_STD_LTR` triggers advisory | PASS |
| 4 | Whitespace-only `from` on `DT_STD_LTR` triggers advisory | PASS |
| 5 | Present `from` on `DT_STD_LTR` produces no advisory | PASS |
| 6 | `window_envelope: true` suppresses advisory even when `from` absent | PASS |
| 7 | `window_envelope: false` does NOT suppress advisory when `from` absent | PASS |
| 8 | Memorandum doc_type skips (no advisory) | PASS |
| 9 | Endorsement doc_type skips (no advisory) | PASS |
| 10 | Joint letter doc_type skips (no advisory) | PASS |
| 11 | Multiple-address letter doc_type skips (no advisory) | PASS |
| 12 | Missing `doc_type` skips (no advisory) | PASS |
| 13 | `errors` list is empty after validation | PASS |
| 14 | `warnings` list contains only advisory findings | PASS |
| 15 | Advisory message includes `CCI-ROUTE-011` | PASS |
| 16 | Advisory message includes `SECNAV M-5216.5` | PASS |
| 17 | Advisory message includes `(advisory)` | PASS |
| 18 | CCI-ROUTE-010 and CCI-ROUTE-011 can trigger independently on same payload | PASS |
| 19 | H.8 targeted runner still passes after any H.10 changes | PASS |
| 20 | No forbidden files modified | PASS |

### 5.2 Extended Hardening Checks (if runner is extended or new runner added)

| # | Check | Expected Result |
|---|---|---|
| 21 | Null `from` on `DT_STD_LTR` triggers advisory | PASS |
| 22 | Tab/newline `from` on `DT_STD_LTR` triggers advisory | PASS |
| 23 | `window_envelope: "yes"` (string) does NOT suppress | PASS |
| 24 | `window_envelope: 1` (int) does NOT suppress | PASS |
| 25 | `standard_letter` doc_type triggers same as `DT_STD_LTR` | PASS |
| 26 | H.4 targeted runner still passes | PASS |
| 27 | H.6 targeted runner still passes | PASS |
| 28 | Full 31/31 (or 32/32) regression gate passes | PASS |
| 29 | New negative-control fixtures all pass (no false positives) | PASS |
| 30 | New positive-control fixtures all trigger (no false negatives) | PASS |

---

## 6. Runner Strategy: Extend H.9 vs Add New H.10

### 6.1 Option A — Extend H.9 Runner

- Add new negative/positive fixture checks to the existing `tools/run_phase_h9_from_line_validator_regression.py`.
- Add corpus verification check.
- Keep runner count at 18+ checks but same runner file.
- **Regression gate stays 31 suites.**

### 6.2 Option B — Add New H.10 Runner

- Create `tools/run_phase_h10_from_line_evidence_regression.py`.
- H.10 runner focuses on fixture existence, false-positive/negative coverage, corpus presence, and cross-runner compatibility.
- H.9 runner remains focused on core validator behavior.
- **Regression gate becomes 32 suites (31 existing + 1 new H.10 runner).**

### 6.3 Recommended Approach

**Option B — Add a new H.10 runner.**

Rationale:
- H.9 runner already has a clear scope: core validator behavior (18 checks).
- H.10 runner should have a clear scope: evidence hardening, fixture coverage, corpus validation, and cross-phase compatibility.
- Separating them matches the H.4/H.6 pattern (H.4 added validator; H.6 added evidence regression separately).
- 32 suites is still fast to run (~3–4 minutes on current hardware).
- Future H.11 (if any) would not need to modify H.9 runner semantics.

Tradeoff: one additional runner file to maintain; one additional suite in the full gate. The benefit is cleaner scope separation and easier future maintenance.

---

## 7. Full Regression Gate Expectation

### 7.1 If Extending H.9 Runner Only

- Gate: **31 suites** (no new runner)
- All 31 existing runners must pass.
- H.9 runner must pass with extended checks.

### 7.2 If Adding New H.10 Runner (Recommended)

- Gate: **32 suites** (31 existing + 1 new H.10 runner)
- All 32 runners must pass.
- H.9 runner must still pass unchanged (or with minor extensions).
- H.10 runner must pass with evidence checks.

---

## 8. Files That May Be Modified in Future Implementation

| File | Scope of Change | Notes |
|---|---|---|
| `tools/run_phase_h9_from_line_validator_regression.py` | Extend with additional checks | Only if Option A is chosen |
| `tools/run_phase_h10_from_line_evidence_regression.py` | Create new runner | Only if Option B is chosen |
| `examples/routing_from_h10_negative_*.json` | Add 20+ negative-control fixtures | Synthetic only |
| `examples/routing_from_h10_positive_*.json` | Add 10+ positive-control fixtures | Synthetic only |
| `corrections/evidence/from_line_patterns.jsonl` | Add 50+ synthetic-realistic patterns | Gitignored; not committed |
| `corrections/evidence/README.md` | Document evidence storage | If needed |

---

## 9. Files That Must NOT Be Modified

| File | Why Protected |
|---|---|
| `src/pdf_v6_render.py` | Renderer baseline — no layout changes |
| `src/context_resolver.py` | Prompt-contract baseline — no runtime changes |
| `src/intake_orchestrator.py` | Intake baseline — no flow changes |
| `src/correction_commands.py` | Phase F command layer — no command changes |
| `src/correction_nl_commands.py` | Phase G command layer — no command changes |
| `rules_v6/CCI/cci_ch2_routing_rules.json` | Catalog baseline — no rule changes |
| `rules_v6/CCI/cci_ch7_subject_rules.json` | Catalog baseline — no rule changes |
| `src/cci_subject_validate.py` | Subject validator — unrelated |
| `src/cci_acronym_validate.py` | Acronym validator — unrelated |
| `src/cci_date_time_validate.py` | Date-time validator — unrelated |
| `src/cci_personnel_validate.py` | Personnel validator — unrelated |
| `src/cci_poc_validate.py` | POC validator — unrelated |
| `profiles/example_local_profile.json` | Example profile — no data changes |
| `corrections/pending_corrections.jsonl` | Pending log — gitignored |
| `corrections/approved_rule_promotions.json` | Approved log — gitignored |
| `corrections/session/*.jsonl` | Session logs — gitignored |
| `docs/BOOTSTRAP.md` | Bootstrap guide — read-only |
| `docs/HERMES_INSTRUCTIONS.md` | Hermes instructions — read-only |

---

## 10. What Phase H.10 Must NOT Do

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **No severity promotion** — `CCI-ROUTE-011` stays advisory-only | Evidence collection phase; severity promotion requires separate approval and config support |
| 2 | **No renderer/layout changes** | Out of scope for evidence collection |
| 3 | **No broad routing validator rewrite** | Helper must remain narrow and isolated |
| 4 | **No automatic enforcement from approved logs** | Approved logs are local/gitignored; no runtime rule generation |
| 5 | **No AI-only implementation decisions** | All fixture patterns must be deterministic and human-reviewed |
| 6 | **No prompt-contract runtime changes** | `src/context_resolver.py` untouched |
| 7 | **No Phase F/G command-layer changes** | Command dispatchers untouched |
| 8 | **No feature flag/config implementation** | Config support is conceptual only; separate planning required |
| 9 | **No approved/pending/session/evidence logs committed** | All correction storage remains local/gitignored |
| 10 | **No real command/user data committed** | All fixtures must be synthetic |
| 11 | **No background automation** | No cron, no auto-triggered validation |
| 12 | **No rule catalog changes** | `rules_v6/CCI/cci_ch2_routing_rules.json` untouched |
| 13 | **No validator logic changes** | `_check_from_line_required()` behavior must not change |
| 14 | **No payload generation changes** | `window_envelope` remains read-only consumption |

---

## 11. Rollback Plan

If any regression fails during H.10 implementation:

1. Revert to commit `6f320af` (Phase H.9 baseline).
2. Verify 31/31 gate passes at `6f320af`.
3. Re-examine fixtures for correctness.
4. Re-examine runner logic for false assumptions.
5. Do not commit partial or broken evidence collection.
6. Re-plan if the scope exceeds the original intent.

---

## 12. Open Questions Needing Approval

| # | Question | Default if Unanswered |
|---|---|---|
| 1 | Should H.10 add a new targeted runner (Option B) or extend H.9 only (Option A)? | **Option B — new H.10 runner** |
| 2 | Is 20 negative + 10 positive + 50 corpus patterns sufficient for Phase H.10, or should counts be higher? | **20/10/50 as specified** |
| 3 | Should H.10 also collect evidence for `CCI-ROUTE-010` (office-code), or stay focused on `CCI-ROUTE-011` only? | **Focus on ROUTE-011 only** |
| 4 | Should any real-world Navy/Marine Corps patterns be sourced, or remain fully synthetic? | **Fully synthetic for fixtures; real-world may inform corpus later** |
| 5 | Should `window_envelope` be added to the payload generation layer in a future phase, or remain read-only? | **Remain read-only in H.10; payload generation deferred** |
| 6 | After H.10 evidence collection, is the next phase severity promotion, a fourth catalog pilot, or feature-flag design? | **No default — requires separate planning** |

---

## 13. Recommended Decision

| Item | Recommendation |
|---|---|
| **Decision** | Evidence collection and regression hardening only — no severity promotion |
| **Runner strategy** | **Option B** — add new `tools/run_phase_h10_from_line_evidence_regression.py`; keep H.9 runner focused on core behavior |
| **Fixture count** | 20 negative-control fixtures, 10 positive-control fixtures, 50 synthetic-realistic corpus patterns |
| **Regression gate** | 32 suites (31 existing + 1 new H.10 runner) |
| **Open questions** | See Section 12 — 6 questions needing approval before implementation |

---

End of Phase H.10 / Phase I.9 Evidence Collection and Regression Hardening Plan.
