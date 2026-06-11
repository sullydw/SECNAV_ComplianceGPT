# Phase K.6 CCI-CH7-SUBJ-002 Warning Pilot Activation Checkpoint

**Date:** 2026-06-11
**Rule:** `CCI-CH7-SUBJ-002` — Subject line terminal punctuation
**Phase type:** Activation checkpoint
**Activation type:** Config-only

---

## 1. K.5 Plan Reference

`docs/planning/phase_k5_subject_terminal_punctuation_warning_pilot_plan.md` — Approved for activation.

## 2. Config-Only Activation

**File modified:** `config/cci_enforcement_config.json`

### Exact config diff

```diff
   "_updated": "2026-06-08",
+  "_updated": "2026-06-11",

   "_allowlist": [
     "CCI-ROUTE-010",
-    "CCI-ROUTE-011"
+    "CCI-ROUTE-011",
+    "CCI-CH7-SUBJ-002"
   ],

     "CCI-ROUTE-011": { ... }
+    },
+    "CCI-CH7-SUBJ-002": {
+      "effective_severity": "warning",
+      "allow_override_up_to": "error",
+      "reason": "Subject line terminal punctuation rule; evidence collected in Phase K.3; warning pilot active in Phase K.6",
+      "snapshot_id": "cfg_20260611_warning"
     }
```

## 3. Config State After Activation

| Rule | Allowlist | Severity | Notes |
|------|-----------|----------|-------|
| `CCI-ROUTE-010` | Yes | `warning` | Unchanged |
| `CCI-ROUTE-011` | Yes | `warning` | Unchanged |
| `CCI-CH7-SUBJ-002` | **Yes** | **`warning`** | **Activated in this phase** |
| `global_default` | — | `advisory` | Unchanged |
| Error promotion | — | Unauthorized | Unchanged |

## 4. Targeted Regression Results

| Runner | Checks | Result |
|--------|--------|--------|
| K.3 SUBJ-002 terminal punctuation | 11 | **PASS** |
| H.2 Subject/acronym | 12 | **PASS** |
| H.13 Config regression | 27 | **PASS** |

## 5. Full 37-Suite Gate Result

**ALL PASS — 37/37 suites**

| Suite | Checks | Result |
|-------|--------|--------|
| H.2 Subject/acronym | 12 | PASS |
| H.3 Second catalog | 15 | PASS |
| H.4 Office-code validator | 18 | PASS |
| H.6 Office-code evidence | 15 | PASS |
| H.8 Third catalog | 16 | PASS |
| H.9 From-line validator | 18 | PASS |
| H.10 From-line evidence | 39 | PASS |
| H.13 Config | 27 | PASS |
| H.16 Burn-in | 96 | PASS |
| H.24 Sanitized fixtures | 36 | PASS |
| J.12 ROUTE-007 duplicate copy-to | 13 | PASS |
| K.3 SUBJ-002 terminal punctuation | 11 | PASS |

## 6. Suite Count

**37 suites** (36 prior + 0 new; config-only activation)

## 7. Decision

**ACTIVATE `CCI-CH7-SUBJ-002` warning pilot.** Config-only change approved per K.5 plan. All regression gates pass. No validator, catalog, renderer, prompt, or command-layer changes.

## 8. Rollback Path

If the warning pilot causes unacceptable behavior:

1. Remove `CCI-CH7-SUBJ-002` from the `_allowlist`, OR set `effective_severity` back to `advisory`.
2. Re-run K.3, H.2, H.13, and full 37-suite gate.
3. All must PASS before rollback is considered complete.
4. Document rollback decision in a checkpoint file.

## 9. Explicit Prohibitions (This Phase)

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

## 10. Recommended Next Phase

**Phase K.7 — CCI-CH7-SUBJ-002 Warning Pilot Observation Decision**

Purpose: Decide whether to continue the warning pilot, pause observation, or proceed to burn-in checkpoint(s).

---

**Activation authority:** Hermes Agent execution per approved K.5 plan.
