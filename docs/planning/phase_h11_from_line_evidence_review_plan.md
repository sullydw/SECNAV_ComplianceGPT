# Phase H.11 / Phase I.10 — From-Line Evidence Review and Next-Action Decision

**Date:** 2026-06-08  
**Latest Docs Checkpoint:** `d4c7654` — `Docs: Record Phase H.10 From line evidence checkpoint`  
**Current Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Previous Functional Baseline:** `6f320af` — `CCI: Add From line advisory validator (Phase H.9)`  
**Current Regression Set:** 32 suites (all PASS)  
**Target Rule:** `CCI-ROUTE-011`  
**Planning Status:** planning-only until reviewed and approved. No code may be written under this plan without separate user approval.  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`

---

## 1. Current CCI-ROUTE-011 Catalog + Advisory Behavior

`CCI-ROUTE-011` is now both cataloged and advisory-enforced.

| Attribute | Current State |
|---|---|
| Rule ID | `CCI-ROUTE-011` |
| Catalog file | `rules_v6/CCI/cci_ch2_routing_rules.json` |
| Validator file | `src/cci_routing_validate.py` |
| Helper | `_check_from_line_required(...)` |
| Catalog severity | `error` |
| Validator behavior | advisory/non-blocking |
| Applies to | `DT_STD_LTR` and `standard_letter` only |
| Exclusions | missing `doc_type`, memorandum, endorsement, joint_letter, multiple_address_letter, and all other non-standard-letter types |
| Window-envelope exception | `window_envelope` truthy suppresses advisory |
| Return structure | existing `(errors, warnings)` tuple |
| Advisory placement | findings append to `warnings`; `errors` remains empty |

The rule remains advisory at runtime even though the catalog severity is `error`. This mirrors the established H.2/H.4/H.9 pattern: catalog severity records the manual rule posture, while validator rollout starts as non-blocking advisory behavior.

---

## 2. Summary of H.10 Evidence

Phase H.10 added evidence collection and regression hardening only. It did not modify validator logic, catalogs, renderer/layout, prompt contracts, command-layer behavior, or correction logs.

### 2.1 Evidence Fixtures

- **20 negative-control fixtures**: `examples/routing_from_h10_neg_*.json`
  - These must not trigger `CCI-ROUTE-011`.
  - They cover From present, window-envelope suppression, missing `doc_type`, non-standard document types, truthy `window_envelope` values, minimal From values, and full payloads.

- **10 positive-control fixtures**: `examples/routing_from_h10_pos_*.json`
  - These must trigger `CCI-ROUTE-011`.
  - They cover missing, empty, whitespace-only, tab/newline, null From values, alternate `standard_letter` doc_type, dual ROUTE-010/ROUTE-011 triggering, and complex payloads with Via/Copy-to/Distribution present.

- **50 local corpus patterns**: `corrections/evidence/from_line_patterns.jsonl`
  - Gitignored and not committed.
  - Used for synthetic-realistic local comparison only.

### 2.2 Regression Results Carried Forward

| Runner | Result |
|---|---|
| H.10 From-line evidence runner | `39/39 PASS` |
| H.9 From-line validator runner | `18/18 PASS` |
| H.8 third catalog-pilot runner | `16/16 PASS` |
| Full gate | `32/32 PASS` |

---

## 3. What Evidence Is Sufficient For Now

The current evidence is sufficient to keep `CCI-ROUTE-011` advisory and to treat the H.9 validator behavior as regression-protected.

The following thresholds are met:

1. **Positive coverage exists** — at least 10 fixtures prove missing/empty/whitespace/null From-line patterns trigger.
2. **Negative coverage exists** — at least 20 fixtures prove valid or out-of-scope cases do not trigger.
3. **Window-envelope behavior is covered** — boolean `true`, string `"yes"`, and int `1` truthy values suppress in current implementation.
4. **Missing `doc_type` is covered** — missing `doc_type` skips rather than infers.
5. **Non-standard document types are covered** — memorandum, MFR, endorsement, joint letter, and multiple-address letter skip.
6. **Dual-rule behavior is covered** — ROUTE-010 and ROUTE-011 can trigger independently on the same payload.
7. **Advisory-only behavior is protected** — `errors` remains empty and findings append to `warnings` only.
8. **Cross-phase protections pass** — H.8 and H.9 targeted runners continue to pass.
9. **Full gate passes** — the 32-suite regression gate is clean.

This is enough evidence to maintain the advisory validator safely.

---

## 4. What Evidence Is Still Missing

The current evidence is not enough to justify warning-level or error-level promotion.

Missing evidence includes:

1. **Real-world Navy/Marine Corps From-line patterns.** Current committed fixtures and local corpus are synthetic.
2. **Observed user feedback.** No sustained usage data exists showing whether the advisory is helpful or noisy.
3. **Window-envelope workflow support.** The validator only reads an optional `window_envelope` key; no approved schema, intake, prompt-contract, UI, or command workflow populates it.
4. **Strict type-policy decision for `window_envelope`.** Current behavior follows Python truthiness. Strict boolean handling is deferred.
5. **Feature flag/config mechanism.** No severity override or staged rollout mechanism exists.
6. **Severity-risk review.** Blocking/error behavior would affect standard letters and must be reviewed separately.
7. **Expanded manual scope.** Multiple-address letters, endorsements, joint letters, and memorandums remain excluded unless separately sourced.

---

## 5. Whether CCI-ROUTE-011 Should Remain Advisory

**Recommended: yes.**

`CCI-ROUTE-011` should remain advisory after H.11 unless a later phase explicitly approves a staged severity-promotion plan.

Reasons:

- The evidence is synthetic, not operational.
- The window-envelope exception can create false-positive advisories if the payload lacks `window_envelope: true`.
- The validator currently has no upstream payload-support mechanism for setting the window-envelope flag.
- The full gate proves the advisory is stable, not that it is ready to block output.
- Advisory behavior is useful and low-risk while future evidence accumulates.

---

## 6. Whether Severity Promotion Should Remain Deferred

**Recommended: yes.**

Severity promotion should remain deferred because:

1. No feature flag/config support exists.
2. No real-world false-positive/false-negative review has been completed.
3. The window-envelope exception depends on an optional payload key that is not formally generated by upstream workflows.
4. The current catalog severity already records the long-term manual importance of the rule.
5. Runtime enforcement can safely remain advisory until operational evidence supports a higher level.

No H.11 action should promote `CCI-ROUTE-011` to warning or error.

---

## 7. Whether Feature Flag/Config Support Should Be Planned Before Severity Promotion

**Yes.**

Before any future warning or error rollout, the project should plan feature flag/config support. That work should be separate from H.11 unless the user explicitly chooses it as the next direction.

A future feature-flag/config plan should decide:

- whether severity overrides live in `config/`, `profiles/`, or another location;
- whether overrides apply globally or per command/profile;
- how advisory, warning, and error levels are represented;
- how regression runners verify default behavior remains unchanged;
- how rollback works if severity creates false positives.

No feature flag/config implementation is authorized by this H.11 plan.

---

## 8. Whether Window-Envelope Handling Should Remain Read-Only or Get Future Schema/Payload Support

**Recommended default:** keep `window_envelope` read-only for now.

H.9 and H.10 correctly avoided upstream payload-generation changes. The validator reads `window_envelope` only if already present. That keeps the scope narrow and avoids prompt-contract or intake risk.

Future schema/payload support may be useful, but it should be planned separately because it could touch:

- payload schema expectations;
- intake behavior;
- context resolver behavior;
- UI or command flows;
- documentation for users creating window-envelope letters;
- test coverage across C7 standard letters and figure 7-3 behavior.

H.11 should not implement schema or payload support.

---

## 9. Whether More Real-World or Synthetic-Realistic Evidence Should Be Collected

More real-world evidence would be valuable before any severity work, but more synthetic evidence is optional.

The H.10 set already gives good synthetic coverage. Additional synthetic fixtures may have diminishing returns unless they target a known gap.

High-value future evidence would include:

- anonymized user-reported standard-letter payloads;
- window-envelope letter payloads with and without `window_envelope` set;
- examples from Navy and Marine Corps correspondence templates;
- false-positive reports from real usage;
- false-negative reports where a missing From line was not caught.

Any real-world evidence must be sanitized and must not be committed unless it is synthetic and approved for repository use.

---

## 10. Whether a Fourth Low-Risk Catalog Pilot Should Be Selected Instead

A fourth low-risk catalog pilot is the preferred productive alternative if the user does not want to continue deepening `CCI-ROUTE-011`.

Reasons:

- The catalog-only pilot pattern is proven and low risk.
- It grows the CCI rule base without changing runtime behavior.
- It avoids premature severity escalation.
- It can target a different domain such as references/enclosures, date/time, personnel, POC, or acronym usage.

Candidate selection should still require source verification, duplicate checks, deterministic scope review, and Phase D → Phase E → Phase H workflow discipline.

---

## 11. Decision Options

| Option | Action | Pros | Cons | When to Choose |
|---|---|---|---|---|
| A | Keep `CCI-ROUTE-011` advisory indefinitely | Safest; no new work; preserves current value | Does not increase enforcement strength | Choose if advisory output is enough |
| B | Collect more evidence | Builds confidence before severity | More fixtures may have diminishing returns | Choose if real-world patterns are available |
| C | Design window-envelope payload/schema support | Addresses the main exception workflow | Could touch prompt/context/intake/UI contracts | Choose if window-envelope letters are common |
| D | Design feature flag/config support | Prerequisite for staged severity promotion | Adds configuration complexity | Choose before warning/error rollout |
| E | Plan warning-level rollout | Moves toward stronger enforcement | Premature without C/D and real-world evidence | Choose only after evidence and config planning |
| F | Plan fourth catalog pilot | Expands CCI coverage safely | Does not deepen From-line rule | Choose if continuing the proven catalog-pilot path |

---

## 12. Recommended Default Decision

**Recommended default:** Option A — keep `CCI-ROUTE-011` advisory indefinitely for now.

**Recommended productive alternative:** Option F — plan a fourth low-risk catalog-only pilot.

Rationale:

- H.10 evidence is sufficient for advisory maintenance.
- H.10 evidence is not sufficient for severity promotion.
- The most practical next value is either preserving the current advisory posture or adding another catalog-only rule with proven workflow controls.
- Feature flag/config and window-envelope schema work should happen only if the user specifically wants to move toward severity or richer payload support.

---

## 13. Regression Expectations

### 13.1 Planning-Only H.11

If H.11 remains planning-only:

- Current gate remains **32 suites**.
- No new runner is added.
- No implementation commit is made.

### 13.2 If a Future H.11 Runner Is Added

If H.11 later adds a new review/evidence runner:

- Gate becomes **33 suites**.
- All existing 32 suites must still pass.
- The new runner must not require validator, catalog, renderer, prompt-contract, command-layer, or log changes unless separately approved.

### 13.3 If Next Phase Is Fourth Catalog Pilot

If the next phase becomes a fourth catalog pilot:

- A new targeted runner would likely make the gate **33 suites**.
- The new runner should follow the H.1/H.3/H.8 pattern.
- The pilot must pass the full gate before any commit.

---

## 14. Files That May Be Modified in Future Implementation

Depending on the selected future direction, possible files include:

| Future Direction | Files That May Be Modified |
|---|---|
| More evidence for ROUTE-011 | `examples/routing_from_h11_*.json`, optional new runner, docs/checkpoint files |
| Window-envelope payload/schema support | Only after separate approval: schema/context/intake/UI/command docs or code as explicitly scoped |
| Feature flag/config planning | planning docs only; implementation files only after separate approval |
| Fourth catalog pilot | relevant `rules_v6/CCI/*.json`, new runner, planning/checkpoint docs |
| Planning-only H.11 checkpoint | `docs/PROJECT_STATUS.md`, `docs/planning/correction_memory_and_rule_promotion_plan.md`, new checkpoint doc |

No future implementation may use this plan as blanket authorization. Each direction requires separate approval.

---

## 15. Files That Must Not Be Modified

Unless separately approved, H.11 must not modify:

- `src/cci_routing_validate.py`
- `rules_v6/CCI/cci_ch2_routing_rules.json`
- `src/pdf_v6_render.py`
- `src/context_resolver.py`
- `src/intake_orchestrator.py`
- `src/validator_runner.py`
- `src/correction_commands.py`
- `src/correction_nl_commands.py`
- `src/correction_implementation_planner.py`
- `corrections/pending_corrections.jsonl`
- `corrections/approved_rule_promotions.json`
- `corrections/session/*.jsonl`
- `corrections/evidence/*`
- real profiles or real command/user data
- `docs/BOOTSTRAP.md`
- `docs/HERMES_INSTRUCTIONS.md`

---

## 16. What Phase H.11 Must NOT Do

Phase H.11 must not:

1. Promote `CCI-ROUTE-011` severity.
2. Promote `CCI-ROUTE-010` severity.
3. Modify validator logic unless separately approved.
4. Modify renderer/layout behavior.
5. Automatically enforce rules from approved logs.
6. Make AI-only implementation decisions.
7. Modify runtime prompt contracts.
8. Modify context resolver, intake, UI, or command flows.
9. Modify Phase F/G command-layer behavior.
10. Commit approved, pending, session, or evidence logs.
11. Commit real command/user data.
12. Implement feature flag/config support.
13. Add background automation.
14. Treat synthetic evidence as sufficient for error-level enforcement.
15. Expand `CCI-ROUTE-011` scope to multiple-address letters, endorsements, joint letters, or memorandums without separate source verification.

---

## 17. Rollback Plan

If a future H.11 implementation causes unexpected problems:

1. Revert the H.11 implementation commit.
2. Restore the prior functional baseline, currently `d808cb8`, unless a later approved baseline supersedes it.
3. Preserve H.10 fixtures and runner unless the H.11 change directly modified them.
4. Re-run the 32-suite gate.
5. Confirm `CCI-ROUTE-011` remains advisory-only.
6. Confirm `CCI-ROUTE-010` remains advisory-only.
7. Confirm local logs and evidence corpus remain gitignored/uncommitted.
8. Document the rollback in the next checkpoint.

For planning-only H.11, rollback is simply deleting or reverting the planning document.

---

## 18. Open Questions Needing Approval

| # | Question | Recommended Default |
|---|---|---|
| 1 | Should `CCI-ROUTE-011` remain advisory indefinitely? | Yes, for now. |
| 2 | Should the next phase collect more real-world From-line evidence? | Only if sanitized real patterns are available. |
| 3 | Should window-envelope payload/schema support be planned? | Defer unless the user expects frequent window-envelope letters. |
| 4 | Should feature flag/config support be planned before any future severity promotion? | Yes, if severity promotion becomes a goal. |
| 5 | Should warning-level rollout be planned now? | No. Defer until evidence + config planning exists. |
| 6 | Should the project pivot to a fourth catalog-only pilot? | Yes, if the user wants the safest productive next step. |
| 7 | Should H.11 add a new runner? | No, not for planning-only review. Add only if a future implementation needs it. |
| 8 | Should multiple-address letters or joint letters be considered for From-line scope? | No, unless separate SECNAV source verification supports it. |
| 9 | Should strict boolean handling for `window_envelope` be planned? | Defer to a future validator-hardening phase. |
| 10 | Should rule-catalog governance/provenance tooling be improved? | Reasonable future option, but not part of this plan unless selected. |

---

## Recommended Decision

**Keep `CCI-ROUTE-011` advisory-only and treat the H.10 evidence as sufficient for advisory maintenance, not severity promotion.**

The best next implementation target, if the user wants to continue adding value, is a **fourth low-risk catalog-only pilot**. The best next infrastructure target, if the user wants to prepare for future severity work, is **feature flag/config planning**. The best next From-line-specific target is **window-envelope payload/schema planning**, but that should be deferred unless it is operationally needed.

---

## Recommended Next Implementation Target, If Any

| Priority | Target | Rationale |
|---|---|---|
| 1 | Fourth catalog-only pilot planning | Safest productive path; no runtime behavior change. |
| 2 | Feature flag/config planning | Required before warning/error rollout. |
| 3 | Window-envelope payload/schema planning | Useful only if window-envelope workflow matters operationally. |
| 4 | More From-line evidence | Useful if real-world patterns are available. |
| 5 | Warning-level rollout | Not recommended now. |

---

## Recommended Regression Gate

- **Current gate:** 32 suites.
- **Planning-only H.11:** remains 32 suites.
- **Future H.11 runner:** 33 suites.
- **Fourth catalog pilot with runner:** likely 33 suites.
- Any future implementation must run the full gate before commit.

---

## Open Questions Needing Approval Before Any Next Implementation

1. Proceed with a fourth catalog-only pilot, feature flag/config planning, window-envelope payload/schema planning, or no implementation?
2. If fourth catalog pilot, which domain should be searched first?
3. If feature flag/config planning, should it cover both `CCI-ROUTE-010` and `CCI-ROUTE-011`?
4. If window-envelope support, should it touch payload schema, intake, UI, context resolver, or documentation only?
5. Should `CCI-ROUTE-011` be explicitly declared advisory-indefinite in project status after H.11 review approval?

---

End of Phase H.11 / Phase I.10 — From-Line Evidence Review and Next-Action Decision Plan.
