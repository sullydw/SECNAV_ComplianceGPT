# Phase K.7 CCI-CH7-SUBJ-002 Warning Pilot Observation Decision

**Date:** 2026-06-11
**Rule:** `CCI-CH7-SUBJ-002` — Subject line terminal punctuation
**Phase type:** Observation decision checkpoint
**Commit constraint:** No config, severity, allowlist, validator, catalog, renderer, prompt, or command-layer changes.

---

## 1. K.6 Activation Summary

`d5c7c47` — `CCI: Start K.6 SUBJ-002 warning pilot`

Activation type: Config-only.

## 2. Exact Active Config State

| Attribute | Value |
|-----------|-------|
| `CCI-ROUTE-010` | `warning` — unchanged |
| `CCI-ROUTE-011` | `warning` — unchanged |
| `CCI-CH7-SUBJ-002` | **`warning`** — activated in K.6 |
| `global_default` | `advisory` — unchanged |
| `_updated` | `2026-06-11` |
| Error promotion | Unauthorized |

## 3. Post-Activation Regression Results

**Full 37-suite gate: ALL PASS**

| Runner | Checks | Result |
|--------|--------|--------|
| K.3 SUBJ-002 terminal punctuation | 11 | PASS |
| H.2 Subject/acronym | 12 | PASS |
| H.13 Config regression | 27 | PASS |
| H.10 From-line evidence | 39 | PASS |
| H.16 Burn-in | 96 | PASS |
| H.24 Sanitized fixtures | 36 | PASS |
| J.12 ROUTE-007 duplicate copy-to | 13 | PASS |
| + all others | — | PASS |

**Total: 37/37 suites PASS.**

## 4. Code Change Summary

| Layer | Changed in K.6? |
|-------|-----------------|
| Config | Yes — allowlist + severity override only |
| Validator logic | No |
| Rule catalog | No |
| Renderer/layout | No |
| Prompt contracts | No |
| Command layer | No |
| Fixtures | No |
| Runners | No |

## 5. Observation Decision

### Decision: Continue `CCI-CH7-SUBJ-002` warning pilot.

**Rationale:**
- Rule is deterministic with explicit source support (Chapter 7, para 7-2.9 and Figure 7-1).
- Full 37-suite gate passed immediately after activation.
- No code, validator, catalog, renderer, prompt, or command-layer changes were required.
- Low false-positive risk confirmed by 6 negative cases in K.3 runner.
- No rollback warranted.

### Do NOT perform repeated synthetic burn-in checkpoints unless one of the following triggers occurs:

1. Sanitized operator feedback appears suggesting false positives or unexpected behavior.
2. Regression anomaly appears (any suite fails unexpectedly).
3. Config/severity changes again for SUBJ-002 or any other rule.
4. User explicitly requests renewed observation.

This follows the same paused-observation posture established for ROUTE-010/011 after I.43.

## 6. Rollback Path

If the warning pilot must be reversed:

1. Remove `CCI-CH7-SUBJ-002` from the `_allowlist`, OR set `effective_severity` back to `advisory`.
2. Re-run K.3, H.2, H.13, and full 37-suite gate.
3. All must PASS before rollback is considered complete.
4. Document rollback decision in a checkpoint file.

## 7. Explicit Prohibitions (This Phase)

- No config changes.
- No severity changes.
- No allowlist changes.
- No error promotion.
- No validator logic changes.
- No catalog changes.
- No renderer/layout changes.
- No prompt/context/intake/UI/command-flow changes.
- No Phase F/G command-layer changes.
- No fixture or runner modifications.
- No logs or unsanitized material committed.
- Do not read or modify `docs/BOOTSTRAP.md`.
- Do not modify `docs/HERMES_INSTRUCTIONS.md`.

## 8. Recommended Next Work

**Shift focus from CCI rule expansion to user-facing conversational builder workflow.**

The CCI-CH7-SUBJ-002 warning pilot is stable. The three active warning pilots (ROUTE-010, ROUTE-011, SUBJ-002) are all in paused-observation posture. Further rule promotion requires:

1. Explicit user request, OR
2. Sanitized operator feedback triggering a new candidate scan, OR
3. Completion of a 30-day burn-in period for existing pilots with evidence review.

**Alternative:** Run a new explicit-source candidate scan (K.8) only if user wants additional rules (e.g., REF-005 or DTM-003).

---

**Decision authority:** Hermes Agent recommendation; user may override.
