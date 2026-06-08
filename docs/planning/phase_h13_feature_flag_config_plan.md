# Phase H.13 / Phase I.12 — Feature-Flag/Config Support for Future CCI Severity Promotion Planning Document

**Phase:** planning-only (not yet approved for implementation)  
**Functional Baseline:** `d808cb8` — `CCI: Add From line evidence regression (Phase H.10)`  
**Current Regression Set:** 32 suites (32/32 PASS)  
**Planning Commit:** `[TBD]` — `Docs: Add Phase H.13 feature flag config plan`  
**Source H.12 Decision:** `3c56a7c` — `Docs: Record Phase H.12 no-candidate search checkpoint`  

---

## 1. Why Feature-Flag/Config Planning Is The Right Next Step After H.12

Phase H.12 completed exhaustive priority and expanded search for a fourth low-risk catalog-only pilot and found no candidate that met all 10 selection criteria. The three prior pilots (SUBJ-006/ROUTE-010/ROUTE-011) captured the most obvious deterministic structural rules. Remaining SECNAV M-5216.5 text either requires body.text parsing, semantic interpretation, or renderer/layout changes.

The immediate need is not another catalog rule but a safe mechanism to promote existing advisory rules to warning/error when the deployment context justifies it. Both:

- `CCI-ROUTE-010` (office code prefix)
- `CCI-ROUTE-011` (From line required)

are advisory-only with sufficient evidence collected (H.6/H.10) to justify promotion, but codebase safety policy requires feature-flag/config support before any severity change.

Feature-flag/config planning is therefore the right next step because:
1. It unlocks all future severity promotion regardless of which rule is promoted next.
2. It does not require finding a new rule candidate.
3. It preserves backward compatibility by default.
4. It is verifiable deterministically through config snapshots.

---

## 2. Current Advisory Rules That Might Eventually Use Config

| Rule ID | Current Catalog Severity | Current Validator Severity | Evidence Collection | Future Promotion Eligibility |
|---|---|---|---|---|
| `CCI-ROUTE-010` | `error` | Advisory/non-blocking | H.4 (validator), H.6 (evidence, 20+10 fixtures + 50 corpus) | Yes — evidence reviewed in H.7; promotion deferred pending config support |
| `CCI-ROUTE-011` | `error` | Advisory/non-blocking | H.8 (catalog), H.9 (validator), H.10 (evidence, 20+10 fixtures + 50 corpus) | Yes — evidence reviewed in H.11; promotion deferred pending config support |

Current validator behavior:
- `src/cci_routing_validate.py` hardcodes both CCI-ROUTE-010 and CCI-ROUTE-011 to always emit their findings into the `warnings` list with the `(advisory)` prefix.
- `src/validator_runner.py` collects all warnings into `warnings`; errors go into `errors`; `overall_pass` is driven by `total_errors == 0`.
- No runtime mechanism exists to redirect an advisory finding into `errors`.

---

## 3. Required Default Behavior

| Requirement | Rationale |
|---|---|
| **Default: advisory for all configured rules** | No config file means existing behavior equals default behavior. No silent promotion. |
| **Missing config file = existing behavior** | Backward compatibility for users with no local override. |
| **Omitted rule in config = catalog/validator default severity** | A rule not listed in config must behave exactly as before. |
| **No rule may silently promote itself** | Promotion must require explicit config entry + non-default severity value. |
| **No rule severity may exceed catalog severity** | Config cannot override catalog severity upward unless explicitly allowed. |
| **Config file invalid or unreadable = existing behavior** | Safe fallback on all errors. |
| **Default enforcement mode = advisory only** | First approved config snapshot should start at advisory. |

---

## 4. Config Goals

| Goal | Accept/Reject | Notes |
|---|---|---|
| Per-rule severity override | ACCEPT | Design target. |
| Global default enforcement mode | ACCEPT | Optional top-level default overrides catalog for all listed rules. |
| Explicit allowlist for promotable rules | ACCEPT | Not every rule is eligible for promotion; allowlist gates eligibility. |
| Safe fallback on missing/invalid config | ACCEPT | Core safety requirement. |
| Audit-friendly source/provenance for overrides | ACCEPT | Config snapshot records who filed the override, when, and for what rule. |
| Schema version field | ACCEPT | Supports future schema migration. |
| Validator-level severity mapping | ACCEPT | Preferred integration point (simpler, localized to validator module). |
| Central `validator_runner` mapping | ACCEPT | Alternative if per-validator integration is too invasive. |
| Context resolver integration for severity | REJECT | Would affect prompt contracts; out of H.13 scope unless separately approved. |
| Prompt-contract severity integration | REJECT | May break prompt caching; deferred to future phase if needed. |
| Command-layer severity override | REJECT | User command-layer support for dynamic severity is separately scoped. |
| Renderer/layout severity integration | REJECT | No renderer changes in H.13 scope. |

---

## 5. Severity Ladder and Promotion Criteria

| Level | Meaning | Catalog Severity Equivalent | Promotion Criteria |
|---|---|---|---|
|| `advisory` | Non-blocking warning, advisory prefix, does not affect `overall_pass` | Current validator behavior | Default for all rules unless config overrides |
|| `warning` | Blocking warning, validator emits finding directly into `errors` list (not `warnings`), affects `overall_pass` | Effective severity = warning | Requires: config override + rule in allowlist + no catalog override prohibiting it |
|| `error` | True hard error, always blocking, treated as schema/critical failure | Effective severity = error | Requires: config override + rule in allowlist + explicit separate approval + warning stage evidence |

Promotion criteria before moving up:

| From | To | Criteria |
|---|---|---|
| advisory | warning | Config override present; rule in allowlist; no known false-positive regression failure from H.6/H.10 evidence suite; config snapshot timestamped. |
| warning | error | Same as warning + 30-day burn-in period at warning level, plus explicit user review and approval. |
| Any level | lower | Immediate rollback via config update; no evidence review required. |

---

## 6. Proposed Config Shape

### File Path

```text
config/cci_enforcement_config.json
```

Path justification:
- Domain-specific (`cci_enforcement_`) rather than generic, to avoid confusion with unrelated project configs.
- JSON for schema-friendly validation in regression.
- Lives outside `src/` to avoid mixing code with configuration.
- `config/` directory does not yet exist; H.13 implementation will create it if approved.

### Proposed Schema

```json
{
  "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
  "_description": "Per-rule severity override configuration.  Default is advisory for all rules unless overridden below.",
  "_created": "YYYY-MM-DD",
  "_updated": "YYYY-MM-DD",
  "_allowlist": [
    "CCI-ROUTE-010",
    "CCI-ROUTE-011"
  ],
  "global_default": "advisory",
  "overrides": {
    "CCI-ROUTE-010": {
      "effective_severity": "advisory",
      "allow_override_up_to": "error",
      "reason": "Office code prefix rule; evidence collected in Phase H.6",
      "snapshot_id": "cfg_YYYYMMDD_..."
    },
    "CCI-ROUTE-011": {
      "effective_severity": "advisory",
      "allow_override_up_to": "error",
      "reason": "From line required rule; evidence collected in Phase H.10",
      "snapshot_id": "cfg_YYYYMMDD_..."
    }
  }
}
```

### Field Reference

| Top-level Field | Type | Required | Description |
|---|---|---|---|
| `_schema_version` | string | Yes | `"CCI_ENFORCEMENT_CONFIG_V1"`. |
| `_description` | string | No | Human-readable explanation. |
| `_created` | string | No | ISO date of first config creation. |
| `_updated` | string | No | ISO date of last update. |
| `_allowlist` | array of strings | Yes | Rule IDs eligible for override. IDs not in array cannot be overridden even if present in `overrides`. |
| `global_default` | string | Yes | `"advisory"`, `"warning"`, or `"error"`. Default is advisory for safety. |
| `overrides` | object | Yes | Map of rule_id → override object. Omitted rule uses `global_default` or catalog/validator default severity. |

### Override Object Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `effective_severity` | string | Yes | `"advisory"`, `"warning"`, or `"error"`. |
| `allow_override_up_to` | string | Yes | Maximum allowed severity for this rule. Config cannot exceed this. |
| `reason` | string | No | Human-readable rationale. |
| `snapshot_id` | string | No | Unique config snapshot identifier for audit trail. |

### Example: Out-of-phase initial config

Default for all unapproved deployments — both allowlisted rules remain advisory, with explicit entries for audit self-documentation:

```json
{
  "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
  "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
  "global_default": "advisory",
  "overrides": {
    "CCI-ROUTE-010": {
      "effective_severity": "advisory",
      "allow_override_up_to": "error",
      "reason": "Office code prefix rule; evidence collected in Phase H.6; advisory by default",
      "snapshot_id": "cfg_YYYYMMDD_default"
    },
    "CCI-ROUTE-011": {
      "effective_severity": "advisory",
      "allow_override_up_to": "error",
      "reason": "From line required rule; evidence collected in Phase H.10; advisory by default",
      "snapshot_id": "cfg_YYYYMMDD_default"
    }
  }
}
```

### Example: After H.13 approval + future promotion

```json
{
  "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
  "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
  "global_default": "advisory",
  "overrides": {
    "CCI-ROUTE-010": {
      "effective_severity": "warning",
      "allow_override_up_to": "error",
      "reason": "H.6 evidence sufficient; promoted per approved config snapshot"
    }
  }
}
```

### Disabled Rule Behavior

If a rule ID is present in `overrides` with `effective_severity = "advisory"`, the rule stays advisory. If the rule ID is completely omitted from `overrides`, the rule takes `global_default` severity (which defaults to advisory). There is no explicit `"disabled"` level — omission or advisory both mean advisory.

### Catalog Severity Ceiling and Override Limits

The rule catalog (`rules_v6/CCI/*.json`) defines the long-term/manual severity for each rule. The config override system may not exceed catalog severity:

- For `CCI-ROUTE-010` and `CCI-ROUTE-011`, the catalog severity is `"error"`. Therefore, `allow_override_up_to: "error"` in the config matches the catalog ceiling and is permitted.
- The config `effective_severity` must never be higher than `allow_override_up_to`.
- If `allow_override_up_to` were set below catalog severity, the config ceiling would still be respected and the rule would be capped at the lower level. This would require a separate catalog change to raise.
- **No rule is promoted by default.** Even though the catalog severity is `error` and the config ceiling is `error`, `effective_severity` remains `advisory` unless explicitly changed in a later approved phase.

### Local Override Gitignore Policy

- **Tracked default config:** `config/cci_enforcement_config.json` — versioned in git, deployed with the repo, contains only default (advisory) entries.
- **Optional user-local override:** `config/cci_enforcement_config.local.json` — **must be gitignored** and never committed.
- The severity mapper should prefer the local override file if present, falling back to the tracked default.
- **H.13 implementation should not require local override support** unless separately approved; the tracked default config is sufficient for the initial implementation.

---

## 7. Runtime Integration Options

### Option A: Validator-Level Severity Mapping (RECOMMENDED)

Each validator module that contains advisory-only rules imports a shared `cci_severity_mapper` module. The mapper:

1. Attempts to load `config/cci_enforcement_config.json`.
2. Returns a function `effective_severity(rule_id, catalog_severity)` → `actual_severity`.
3. Individual advisory checkers (e.g., `_check_office_code_prefix`, `_check_from_line_required`) call the mapper and append to `warnings` or `errors` accordingly.

Advantages:
- Minimal surface area — only advisory checkers affected.
- Backward compatible when no config exists.
- Easy to reason about per-rule behavior.
- No changes to validator entry points or `validator_runner` required.
- No prompt-contract changes.

Disadvantages:
- Each validator with advisory checks needs the import.
- Multiple severity decision points instead of one global map.

### Option B: Central `validator_runner` Mapping (ACCEPTABLE ALTERNATIVE)

`src/validator_runner.py` loads the config and runs a post-processing pass. After each validator returns `(errors, warnings)`, the runner:

1. For each warning with a known rule ID prefix, looks up `effective_severity`.
2. If severity > advisory, moves the warning from `warnings` to `errors`.
3. Recomputes `overall_pass` after moves.

Advantages:
- Single integration point.
- No changes to individual validators.
- Easy to audit from one location.

Disadvantages:
- Regex extraction of rule ID from message strings is fragile.
- Validator messages must have stable prefix format (currently true: `CCI-ROUTE-010 (advisory):`).
- Moving messages between lists after the fact is harder to trace than emitting to the right list initially.

### Option C: Context Resolver Integration (REJECTED)

`src/context_resolver.py` would inject severity info into the context object.

Rejected because:
- Context resolver is meant for struct payload resolution, not enforcement policy.
- Would leak enforcement policy into prompt-contract context.

### Option D: Prompt-Contract Integration (REJECTED)

Inject severity instructions into the prompt or system prompt.

Rejected because:
- Would affect all generations and may break prompt caching.
- Enforcement should be deterministic code, not LLM-mediated.

### Recommended Target: OPTION A (Validator-Level Severity Mapper)

Setup plan:
1. Create `src/cci_severity_mapper.py` (new module).
2. In `src/cci_routing_validate.py`, import mapper and call it inside `_check_office_code_prefix` and `_check_from_line_required` before deciding whether to append to `warnings` or `errors`.
3. No changes to other validators yet.
4. Future phases can extend by importing the mapper in other validator modules.

---

## 8. Backward-Compatibility Requirements

| Scenario | Required Behavior |
|---|---|
| No `config/` directory exists | Validator falls back to advisory behavior. |
| No `cci_enforcement_config.json` exists | Validator falls back to advisory behavior. |
| Config schema version mismatch | Log warning, fall back to advisory behavior. |
| Config file malformed JSON | Log warning, fall back to advisory behavior. |
| Config file has unknown `_schema_version` | Log warning, fall back to advisory behavior. |
| Rule ID in `overrides` but not in `_allowlist` | Ignore override, fall back to advisory behavior. |
| `effective_severity` exceeds `allow_override_up_to` | Clamp to `allow_override_up_to`, log warning. |
| `effective_severity` string not in `{"advisory", "warning", "error"}` | Ignore override, fall back to advisory behavior. |
| Rule ID in `_allowlist` but not in catalog | Ignore; catalog authority is the real rule definition. |
| `_allowlist` is empty or missing | All rules unlisted; no overrides permitted. |

---

## 9. Failure Behavior Summary

| Failure Mode | Action | Log Event |
|---|---|---|
| Missing config file | Use advisory fallback, return success | No log event required. |
| Invalid JSON | Use advisory fallback, return success | Optional stderr warning: "CCI config unreadable, using advisory fallback" |
| Unknown schema version | Use advisory fallback, return success | Optional stderr warning: "CCI config schema unknown, using advisory fallback" |
| Unknown rule ID in override | Ignore override, use advisory fallback | No action. |
| Unsupported severity string | Ignore override, use advisory fallback | No action. |
| Rule configured without allowlist entry | Ignore override, use advisory fallback | No action. |
| Config file unreadable (permissions) | Use advisory fallback, return success | Optional stderr warning. |

---

## 10. Regression Strategy

| Requirement | Status |
|---|---|
| Existing 32 suites must remain PASS | Required. No existing tests change behavior. |
| New targeted regression runner for config | `tools/run_phase_h13_feature_flag_config_regression.py` proposed. |
| Config-runner minimum checks | 30-40 checks (exact count TBD at implementation time). |
| Future regression gate with new runner | 33 suites (32 existing + 1 new H.13 runner). |
| Config backward-compat fixtures | Missing-config fixture, malformed-config fixture, omit-rule fixture, unknown-rule fixture, allowlist-denied fixture, schema-mismatch fixture. |
| Severity fidelity checks | Warning-stage fixture (mock config with warning for ROUTE-010), error-stage fixture, advisory-default fixture. |

---

## 11. Files That May Be Modified in Future Implementation

| File | Change |
|---|---|
| `src/cci_severity_mapper.py` | **New file** — shared severity mapper module. Reads `config/cci_enforcement_config.json`, resolves per-rule severity. |
| `src/cci_routing_validate.py` | Import `cci_severity_mapper`, call inside advisory checks to decide whether to append to `warnings` or `errors`. |
| `config/cci_enforcement_config.json` | **New file** — default config with `_allowlist`, `global_default: advisory`, and empty `overrides`. |
| `.gitignore` | Ensure `config/cci_enforcement_config.json` is NOT gitignored by default so default config is tracked and deployable. |
| `tools/run_phase_h13_feature_flag_config_regression.py` | **New file** — targeted regression runner (30-40 checks). |
| `docs/checkpoints/phase_h13_feature_flag_config_checkpoint.md` | **New file** — implementation checkpoint after H.13 implementation. |

---

## 12. Files That Must Not Be Modified

| File | Constraint |
|---|---|
| `src/validator_runner.py` | Should remain unmodified if Option A is used. If Option A proves insufficient, Option B requires minimal change here, but that must be separately reviewed. |
| `src/context_resolver.py` | No prompt-contract changes. |
| `src/letter_model_v6.py` | No model changes. |
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/intake_orchestrator.py` | No intake changes. |
| `src/correction_commands.py` | No command-layer changes. |
| `src/correction_nl_commands.py` | No command-layer changes. |
| `rules_v6/CCI/cci_ch2_routing_rules.json` | No catalog changes unless severity promotion is separately approved. |
| All existing CCI catalog files | No catalog changes. |
| All existing `tools/run_*_regression.py` | No regression runner changes except new runner addition. |

---

## 13. What Phase H.13 Must NOT Do

| Prohibition | Rationale |
|---|---|
| No severity promotion of any rule | Config defaults to advisory; overrides must be explicitly set at a later approved phase. |
| No validator behavior change unless separately approved | Only the mapper module is created; existing advisory emitters stay untouched until implementation. |
| No renderer/layout changes | Strict blocking. |
| No prompt-contract/context/intake/UI/command-flow changes | Strict blocking. |
| No Phase F/G command-layer changes | Strict blocking. |
| No automatic enforcement from approved logs | Config is human-authored, not derived from approved logs. |
| No approved/pending/session/evidence logs committed | Storage safety preserved. |
| No real command/user data committed | Storage safety preserved. |
| No background automation | Config is config file only, not a daemon or scheduler. |
| No config hard-coded into modules | Config must live in a separate JSON file, not in Python constants. |
| No migration of all rules simultaneously | Staged per-rule promotion only. |
| No breaking change on missing config | Backward compatibility by default. |

---

## 14. Rollback Plan

| Scenario | Rollback Action |
|---|---|
| Config causes validator crash | Delete or rename `config/cci_enforcement_config.json`; validators immediately fall back to advisory. |
| Config causes unexpected regression failure | Revert `config/cci_enforcement_config.json` to default (advisory, empty overrides). |
| Severity mapper causes import failure | Revert `src/cci_routing_validate.py` to advisory-only version. |
| Any unknown side effect | Git revert commits introduced by H.13 implementation. All files are tracked; untracked files (`config/cci_enforcement_config.json`) can be deleted. |

---

## 15. Open Questions Needing Approval

1. **Option A vs Option B integration?** — Validator-level mapper or central runner post-processing?
2. **Should config file be versioned in git or generated at install?** — Recommended: version the default config in git; users override locally (either in repo or in external directory).
3. **Should external config directory be supported?** — e.g., `~/.seccg/cci_enforcement_config.json` or env-var override path?
4. **Should config changes require a restart or are they auto-reload?** — Recommended: read-on-demand (no caching) for simplicity; no performance impact expected given tiny file size. But cache could be added later for high-throughput usage.
5. **Should the allowlist be a separate file or embedded?** — Current design embeds it to keep a single source of truth, but if allowlist becomes large it may merit separation.
6. **Log events: silent fallback, stderr warning, or structured log file?** — Recommended: stderr warning only; no additional logs unless separately scoped.

---

## 16. Recommended Decision

| Item | Decision | Rationale |
|---|---|---|
| **Approach** | CREATE FEATURE-FLAG/CONFIG SYSTEM | Config is the prerequisite for all future severity promotion. |
| **Config path** | `config/cci_enforcement_config.json` | Domain-specific, human-readable, deployable, git-trackable default. |
| **Integration target** | **Option A — Validator-level severity mapper** | Minimal surface area, backward compatible, preserves `validator_runner` unchanged. |
| **Severity ladder** | advisory → warning (config-driven) → error (config-driven + 30-day burn-in + explicit approval) | Staged, safe, auditable. |
| **Default severity** | Advisory for all rules | Zero breaking change on first deployment. |
| **Allowlist default** | `CCI-ROUTE-010`, `CCI-ROUTE-011` | These are the known-eligible rules with evidence already collected. Future candidates added by explicit config update. |
| **Regression gate** | 32 suites + 1 new config regression = 33 suites | All existing 32 must pass unchanged. |
| **Rollback** | Delete config file or revert git commits | Immediate advisory fallback guaranteed. |

---

## 17. Files Created by This Planning Document

- `docs/planning/phase_h13_feature_flag_config_plan.md` — this file.

## 18. Files That Will Be Created After Approval

- `src/cci_severity_mapper.py` — severity mapper module.
- `config/cci_enforcement_config.json` — default tracked config.
- `config/.gitkeep` — keeps `config/` directory visible.
- `tools/run_phase_h13_feature_flag_config_regression.py` — targeted regression runner.
- `docs/checkpoints/phase_h13_feature_flag_config_checkpoint.md` — implementation checkpoint after approval.

---

End of Phase H.13 / Phase I.12 Feature-Flag/Config Support Planning Document.
