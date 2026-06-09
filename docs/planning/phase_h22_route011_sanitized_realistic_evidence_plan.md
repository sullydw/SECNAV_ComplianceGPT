# Phase H.22 / Phase I.21 — Sanitized Realistic Evidence Plan

**Status:** Planning only  
**Rule:** `CCI-ROUTE-011`  
**Current state:** `CCI-ROUTE-011 = warning`; `CCI-ROUTE-010 = advisory`; `global_default = advisory`  
**Regression baseline:** 34 suites  
**Error promotion:** Not authorized

## 1. Purpose

Phase H.22 pauses repeated static synthetic burn-in checkpoints and defines the next evidence step for the active `CCI-ROUTE-011` warning pilot.

The goal is to improve confidence with sanitized realistic payloads before any future severity discussion. This document does not authorize implementation, config changes, severity changes, rollback, validator changes, catalog changes, renderer changes, prompt/context/intake/UI changes, or command-layer changes.

## 2. Why Synthetic Repetition Is Paused

H.19, H.20, and H.21 all used the same H.16 synthetic batch and produced the same result:

- 90 payloads reviewed per checkpoint.
- 45 expected `CCI-ROUTE-011` triggers.
- 0 false positives.
- 0 false negatives.
- No regression changes.
- No new risk.
- Full 34-suite gate remained passing.

This supports continued warning status but has diminishing returns. The next useful step is sanitized realistic evidence.

## 3. Current Pilot State

- `CCI-ROUTE-011` remains active at warning by config.
- `CCI-ROUTE-010` remains advisory.
- `global_default` remains advisory.
- No rule is promoted to error.
- Rollback remains config-only by restoring `CCI-ROUTE-011.effective_severity` to `advisory`.

## 4. Evidence Goal

The evidence goal is to collect or construct sanitized realistic Navy/Marine Corps-style payloads that test:

- standard letters with a valid `from` field;
- standard letters missing `from`;
- standard letters with null, empty, or whitespace-only `from` values;
- correctly tagged window-envelope letters;
- window-envelope-like letters missing the `window_envelope` flag;
- non-standard documents that must not trigger `CCI-ROUTE-011`;
- realistic routing, via, copy-to, and distribution combinations.

## 5. Data Handling Rules

Only sanitized or synthetic material may be committed. Operational notes, logs, session stores, pending records, approved-record logs, user-specific data, and real correspondence content must remain local unless separately approved and sanitized.

Sanitized examples must remove names, addresses, phone numbers, emails, dates tied to actual events, signatures, unique identifiers, and any details that identify a person, unit action, or real correspondence.

All examples must be clearly labeled synthetic or sanitized.

## 6. Suggested Evidence Categories

| Category | Expected behavior |
|---|---|
| Standard letters with valid `from` | No `CCI-ROUTE-011` finding |
| Standard letters missing `from` | `CCI-ROUTE-011` warning/blocking finding |
| Null/empty/whitespace `from` | `CCI-ROUTE-011` warning/blocking finding |
| Window-envelope with `window_envelope: true` | Suppressed; no `CCI-ROUTE-011` finding |
| Window-envelope-like without flag | `CCI-ROUTE-011` warning/blocking finding |
| Non-standard documents | No `CCI-ROUTE-011` finding |
| Routing/via/copy-to/distribution combinations | From-line behavior only; no unrelated side effects |
| Navy/Marine Corps-style examples | Expected pass/fail by payload |

## 7. Minimum Evidence Target

A later implementation phase should target 25 to 50 sanitized realistic payloads.

Suggested mix:

- 8 to 12 valid standard letters with `from`.
- 5 to 8 standard letters missing `from`.
- 5 to 8 null/empty/whitespace `from` cases.
- 4 to 6 correctly tagged window-envelope cases.
- 4 to 6 window-envelope-like cases missing the flag.
- 4 to 6 non-standard document exclusions.
- 4 to 6 mixed Navy/Marine Corps routing examples.

Each payload should record expected pass/fail behavior and expected `CCI-ROUTE-011` behavior.

## 8. Metrics for Review

Future review should record:

- total payloads reviewed;
- expected `CCI-ROUTE-011` triggers;
- actual `CCI-ROUTE-011` triggers;
- unexpected triggers;
- false positives;
- false negatives;
- window-envelope tagging issues;
- regression failures;
- rollback triggers;
- items needing operator-guidance updates.

## 9. Decision Thresholds

Continue warning pilot if the full gate remains passing, expected triggers remain correct, non-standard documents do not trigger, valid standard letters do not trigger, and window-envelope suppression works when tagged.

Rollback to advisory if repeated false positives occur, non-standard documents block, correctly tagged window-envelope letters fail to suppress, the regression gate fails, or operator confusion cannot be corrected through guidance.

Extend observation if the evidence is clean but sample size or realism is insufficient.

Block future error promotion if unresolved false positives, false negatives, window-envelope risk, exotic-whitespace risk, or insufficient sanitized realistic evidence remain.

Future error-readiness review requires separate approval. Synthetic checkpoints alone are not sufficient.

## 10. Future Implementation Possibility

A later phase may add sanitized realistic fixtures and a new runner. If that occurs, the regression gate may become 35 suites.

Potential future files:

- `examples/burnin_h22_route011_sanitized/`
- `tools/run_phase_h22_route011_sanitized_evidence_regression.py`
- `docs/checkpoints/phase_h22_route011_sanitized_evidence_checkpoint.md`

This planning document does not create those artifacts.

## 11. Explicit Prohibitions

This phase does not authorize config changes, severity changes, error promotion, rollback, validator changes, catalog changes, renderer/layout changes, prompt/context/intake/UI/command-flow changes, Phase F/G command-layer changes, or committing logs or unsanitized material.

## 12. Recommended Decision

Keep `CCI-ROUTE-011` at warning, keep `CCI-ROUTE-010` advisory, keep error promotion unauthorized, pause repeated static synthetic checkpoints, and seek sanitized realistic examples before the next observation checkpoint.

## 13. Recommended Next Phase

Recommended next phase:

**Phase H.23 / Phase I.22 — Sanitized Realistic Evidence Fixture Planning or Review**

The next phase should decide whether to create sanitized realistic fixtures and a new runner, or continue manual observation without adding repository artifacts.
