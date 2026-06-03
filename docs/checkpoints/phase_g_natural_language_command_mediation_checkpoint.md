# Phase G Natural-Language Command Mediation Checkpoint

**Implementation Commit:** `cb988bc` — `CCI: Add natural language command mediation (Phase G)`  
**Previous Baseline:** `4ba5cd3` — `CCI: Add command integration layer (Phase F)`  
**Branch:** `main`  
**Status:** Clean, up to date with `origin/main`  
**Regressions:** All 23 regression suites passed locally at `cb988bc`.

---

## What Was Implemented

Phase G adds a deterministic natural-language command mediation layer that converts free-form user input into canonical structured command objects, then dispatches them through the existing Phase F `CorrectionCommandDispatcher`.

### New Files

- `src/correction_nl_commands.py` — `NLCommandMediator` with keyword/phrase scoring, intent classification, and canonical command object generation.
- `tools/run_correction_nl_command_regression.py` — 151-check regression runner covering positive intents, negative tests, prompt-injection safety, guardrail violations, and dispatcher delegation.

### Design Decisions

- **Deterministic only:** No AI/LLM imports. Intent detection uses regex and keyword/phrase dictionaries.
- **Phase F remains dispatch authority:** Phase G produces canonical `CorrectionCommand` objects; `CorrectionCommandDispatcher` executes them exactly as it would for slash commands.
- **15 canonical intents supported:**
  - `correction`
  - `undo`
  - `remember` / `session`
  - `session_list`
  - `session_accept`
  - `session_reject`
  - `profile_promotion`
  - `pending_candidate_log`
  - `review_list`
  - `review_claim`
  - `review_decision`
  - `approved_list`
  - `status`
  - `unsupported`
- **Confirmation required for persistent actions:** `yes`, `y`, `confirm` to approve; `no`, `n`, `cancel` to reject.
- **Clarification on ambiguity:** Low-confidence parses, ambiguous field paths, and ambiguous body/reference targets trigger structured follow-up prompts rather than silent execution.
- **Constrained scope:** `/promote profile` and `/log candidate` remain limited to the most recent active-draft correction or the current-session correction.
- **Evidence enforcement:** Manual-rule approvals require `secnav_citation`; validator-gap approvals require `validator_evidence`.
- **Approved records remain pending:** Approved global rule records stay `implementation_status="pending_implementation"`.

### Guardrails Maintained

- No renderer imports.
- No validator imports.
- No direct file writes from the NL layer.
- No automatic global rule enforcement.
- No AI-only promotion decisions.
- No silent profile or global promotion.
- No background automation.
- No real command/user data committed.

### Regression Results at `cb988bc`

| Runner | Result |
|---|---|
| `run_correction_nl_command_regression.py` | 151/151 PASS |
| `run_correction_command_regression.py` | 45/45 PASS |
| `run_correction_review_regression.py` | 30/30 PASS |
| `run_correction_pending_regression.py` | 33/33 PASS |
| `run_correction_profile_promotion_regression.py` | 33/33 PASS |
| `run_correction_classify_regression.py` | PASS |
| `run_intake_regression.py` | PASS |
| `run_correction_regression.py` | PASS |
| `run_correction_session_regression.py` | PASS |
| `run_profile_regression.py` | PASS |
| `run_cci_audit_regression.py` | PASS |
| `run_context_schema_regression.py` | PASS |
| `run_cci_subject_regression.py` | PASS |
| `run_cci_ref_encl_regression.py` | PASS |
| `run_cci_acronym_regression.py` | PASS |
| `run_cci_date_time_regression.py` | PASS |
| `run_cci_personnel_regression.py` | PASS |
| `run_cci_poc_regression.py` | PASS |
| `run_cci_routing_regression.py` | PASS |
| `run_c7_phase1_regression.py` | PASS |
| `run_c8_regression.py` | PASS |
| `run_c9_regression.py` | PASS |
| `run_c10_regression.py` | PASS |

---

## Recommended Next Phase

### Phase H — Approved-Rule Implementation Planning

Phase H is **planning-only until reviewed and approved**. It must not automatically enforce approved global records without explicit planning and review.

Phase H planning should address:

- How approved global rule records (`implementation_status="pending_implementation"`) are promoted into actual validator code, rule catalog files, or prompt contracts.
- Which approved rules are safe to implement deterministically vs. which require human-in-the-loop testing.
- Impact on existing C7–C10 layout regressions and CCI validator regressions.
- Rollback strategy if an implemented rule causes false positives.
- Regression requirements before any validator or rule catalog changes are committed.

Keep automatic enforcement and silent global rule activation out of Phase H planning unless explicitly scoped and approved. Phase H is approved-rule implementation planning only, not automatic global rule activation.

---

## Historical Baselines

- `cb988bc` — Phase G natural-language command mediation implemented.
- `4ba5cd3` — Phase F command integration layer implemented.
- `058de87` — Phase E review/promotion utility implemented.
- `2e31892` — Phase D pending global rule candidate logging implemented.
- `8b8a95c` — Phase C local command profile promotion implemented.
- `519fad6` — Phase B correction classification implemented.
- `71ddf64` — Phase A session correction persistence implemented.
