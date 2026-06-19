# Phase L.29H — General Live Lookup Candidate Workflow Checkpoint

Date: 2026-06-18  
Commit: `5df26fd`  
Status: Complete — Documentation-only design phase

---

## Summary

Phase L.29H defines a reusable, general workflow for live lookup candidate creation that works for any SECNAV letter. It corrects the previous L.29H approach which incorrectly created one-off hardcoded candidates for a sample request.

No live lookup was implemented. No static command/unit database was added. No source code was modified. No renderer/layout/validator/CCI changes. No hardcoded MISSA/MCAS behavior was added.

---

## Files Added

1. `docs/live_lookup_candidate_workflow.md`
   - General workflow document covering dynamic per-letter candidate creation.
   - Unresolved fact categories, lookup decision table, source tiering, candidate creation rules.
   - User confirmation flow, letterhead/SSIC/routing rules.
   - Sample request illustration (fixture-only, not hardcoded).
   - Do-not-hardcode warning.
   - Browser-agent runtime prerequisites.
   - CLI command usage for candidate-confirm, candidate-reject, apply-resolved.

2. `docs/checkpoints/phase_l29h_general_live_lookup_candidate_workflow_checkpoint.md`
   - This checkpoint document.

---

## Files Modified

1. `docs/PROJECT_STATUS.md`
   - Added L.29H entry with description and recommended next phase.

2. `docs/planning/correction_memory_and_rule_promotion_plan.md`
   - Added L.29H section documenting the workflow design and safety boundaries.

---

## Why the Previous Approach Was Wrong

The initial L.29H execution created three hardcoded candidate JSON files (`candidate_missa_v1.json`, `candidate_mcas_newriver_v1.json`, `candidate_ssic_v1.json`) for a single sample request. This violated the core principle that candidates are session-specific, not permanent. The corrected approach defines a **general workflow** that any future session can follow independently, without carrying forward artifacts from this sample.

---

## Design Decisions

### Generic Unresolved Fact Detection
- Defined 11 fact categories with detection methods.
- Hermes inspects payload + user request for each category per session.

### Lookup Decision Table
- Six-tier priority: ask user → live lookup → safe inference → leave blank → low-confidence candidate → refuse.
- Routing ambiguity defaults to "ask user"; no silent assumption.

### Source Tiering
- Five tiers (Tier 1 official live through Tier 5 unresolved).
- Confidence ranges mapped to tiers.
- Tier 5 results trigger user-directed fallback.

### Candidate Type Rules
- Eight candidate types with per-type resolved_value rules.
- unit_identity omits address fields not source-retrieved.
- ssic_candidate sets specific_ssic to null when no code is found.
- routing_interpretation requires user selection among options.

### Do-Not-Hardcode Enforcement
- Seven explicit prohibitions listed.
- No static database, no hardcoded unit behavior, no reusable candidate files for samples.

---

## Safety Boundaries Preserved

- [x] No source code changes.
- [x] No renderer/layout changes.
- [x] No CCI config/severity changes.
- [x] No validator changes.
- [x] No static command/unit database added.
- [x] No hardcoded MISSA/MCAS logic added.
- [x] `docs/BOOTSTRAP.md` unchanged.
- [x] `docs/HERMES_INSTRUCTIONS.md` unchanged.
- [x] All changes are documentation-only.

---

## Regression Status

No regression run performed — this is a documentation-only phase with no executable changes.
Full regression suite remains at previous baseline (L.29C + earlier).

---

## Recommended Next Phase

**Phase L.29I — General Live Lookup Candidate Workflow Verification**

Use a different sample request (not the MISSA/MCAS sample) to verify that the general workflow produces appropriate candidates without hardcoding. The new sample should exercise a different set of unresolved facts (e.g., a Navy unit, a different acronym, a different subject domain) to confirm workflow generality.

Alternatively:

**Phase L.29J — Automated Unresolved Fact Detection Prototype**

Implement the detection logic in `src/llm_builder_mediator.py` or a new lightweight scanner that inspects a BuilderSession payload and emits a list of unresolved facts for Hermes to act on. This would automate Step 2 of the general workflow.

---

End of Phase L.29H Checkpoint.
