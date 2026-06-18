# Phase L.29C — Candidate Confirmation Infrastructure Checkpoint

Date: 2026-06-17  
Commit: (to be filled after commit)  
Status: Complete

---

## Summary

Phase L.29C implemented the infrastructure for Hermes to pass sourced, user-confirmed resolver candidates into the SECNAV CLI bridge safely.

No live lookup was implemented. No static command/unit database was added. No Ollama, MCP, or renderer changes.

---

## Files Added

1. `rules_v6/CANDIDATE/candidate_v1_schema.json`
   - Defines CANDIDATE_V1 schema with all required fields.
   - Documents supported types, field descriptions, and constraints.

2. `docs/hermes_secnav_candidate_operating_model.md`
   - Operating instructions for how Hermes should handle live lookup when activated.
   - Defines candidate packaging, confidence levels, user confirmation flow, and safe application rules.

3. `tools/run_phase_l29c_candidate_confirmation_regression.py`
   - Regression runner exercising all 24 checks.

---

## Files Modified

1. `src/conversational_builder.py`
   - Added `_candidates` dict with pending/confirmed/rejected buckets.
   - Added `record_candidate()`, `get_candidates()`, `confirm_candidate()`, `reject_candidate()`, `list_candidates()`.
   - Added `apply_candidate()` with safe field mapping per type.
   - Added unit test gate and safeguard around candidate application.

2. `tools/hermes_secnav_tool.py`
   - Version bumped to `L.29C`.
   - Added `_validate_candidate()` with schema and security checks.
   - Added `cmd_candidate_add`, `cmd_candidates`, `cmd_candidate_confirm`, `cmd_candidate_reject`, `cmd_apply_resolved`.
   - Extended `_load_session` and `_save_session` to persist candidates.
   - Added candidate command parsers and handler dispatch.
   - Status command now includes candidate counts in summary.

3. `tools/run_phase_l28_hermes_secnav_cli_tool_regression.py`
   - Patched to tolerate `cci_severity` appearing in `_UNSAFE_PAYLOAD_KEYS` (L.29C security guard).

---

## CLI Commands Added

| Command | Purpose |
|---------|---------|
| `candidate-add --session <id> --json <file>` | Record a candidate as pending |
| `candidates --session <id>` | List pending/confirmed/rejected |
| `candidate-confirm --session <id> --candidate-id <id>` | Confirm and apply a candidate |
| `candidate-reject --session <id> --candidate-id <id> [--reason "..."]` | Reject a candidate |
| `apply-resolved --session <id> --json <file> [--confirm] [--dry-run]` | Record/preview/confirm in one step |

---

## Safe Application Mapping

| Type | Applied Via |
|------|-------------|
| command_expansion | `recommended_kv` → `ingest_user_message()` |
| unit_identity | `resolved_value.unit_identity` → direct payload setter |
| ssic_candidate | `resolved_value.ssic` or `recommended_kv` |
| routing_interpretation | `recommended_kv` |
| signature_block | `resolved_value.signature` or `recommended_kv` |
| date_confirmation | `resolved_value.date` or `recommended_kv` |
| subject_draft | `recommended_kv` |
| body_draft | `recommended_kv` |

---

## Security Guards

- `_UNSAFE_PAYLOAD_KEYS` blocklist prevents candidates from setting renderer directives, CCI config, severity, font settings, or other unsafe fields.
- `requires_user_confirmation` must be `true`; `false` is rejected at validation.
- Unknown `candidate_type` values are rejected.
- All application goes through controlled setters or `ingest_user_message()`.

---

## Regression Results

| Phase | Result |
|-------|--------|
| L.29C new regression | 23/23 PASS |
| L.28 | 25/25 PASS |
| L.27A | 10/10 PASS |
| H.4 | 17/18 (fail = unrelated file-changed check from L.28) |
| H.13 | 26/27 (fail = H.6 cascade, unrelated to L.29C) |
| H.16 | 95/96 (fail = H.13 cascade, unrelated to L.29C) |
| H.24 | 32/32 fixtures + 2/4 sub-runners (H.13/H.16 cascades) |
| K.3 | 11/11 PASS |
| L.11 | 12/12 PASS |

All failures are pre-existing cascades from earlier phase dependencies (H.6 ↔ H.4 file-changed detection, H.13 ↔ H.6 transitive). L.29C itself is clean.

---

## Do-Not-Touch Confirmations

- [x] Renderer/layout files unchanged
- [x] CCI config/severity files unchanged
- [x] docs/BOOTSTRAP.md unchanged
- [x] docs/HERMES_INSTRUCTIONS.md unchanged
- [x] No Streamlit imports added
- [x] stdout remains valid JSON only

---

## Recommended Next Phase

**L.29D — Hermes Live Lookup Wiring**

Enable Hermes to:
1. Perform web search for command expansions, addresses, SSICs.
2. Package results into candidates.
3. Present candidates to the user for confirmation.
4. Apply confirmed candidates via the CLI bridge.

Prerequisites now satisfied:
- Candidate schema defined.
- Candidate confirmation workflow implemented.
- CLI bridge accepts candidates.
- Operating instructions drafted.

End of Phase L.29C Checkpoint.
