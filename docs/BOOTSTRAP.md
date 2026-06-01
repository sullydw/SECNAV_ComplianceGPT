# SECNAV ComplianceGPT - Bootstrap Guide

**For New Chats / Session Continuity**

---

## Start Here

This is the first file a new OpenAI chat, coding agent, or developer should read before continuing work on this repository.

**Project:** SECNAV_ComplianceGPT  
**Purpose:** Rule-driven SECNAV M-5216.5 correspondence generation and compliance checking.  
**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT  
**Local path used in recent work:** `C:\Users\drryl\Projects\SECNAV_ComplianceGPT`  
**Branch:** `main`

Read these files in this order:

1. `docs/BOOTSTRAP.md` — this quick session-start guide.
2. `docs/PROJECT_STATUS.md` — current handoff/status tracker and next planned work.
3. `docs/checkpoints/phase_a_session_persistence_checkpoint.md` — latest correction/session persistence checkpoint.
4. `docs/checkpoints/cci_content_compliance_checkpoint.md` — detailed CCI/intake/correction history.

---

## Current Verified Baseline

**Latest documentation checkpoint commit:** `8c863ff` — `Docs: Add Phase A session persistence checkpoint`  
**Current verified functional baseline:** `71ddf64` — `CCI: Add session correction persistence (Phase A)`  
**Previous functional baseline:** `2e643db` — `CCI: Integrate correction memory with intake`  
**GitHub Actions / regressions:** all 18 regression suites manually verified PASS after `71ddf64`  
**Expected repo state:** clean and up to date with `origin/main`

The current system supports:

- C7-C10 layout/render regression baseline.
- Seven Correspondence Content Intelligence (CCI) validators.
- Context resolver.
- Consolidated CCI audit runner.
- Intake orchestrator.
- Local command profile defaults.
- Active-draft correction memory.
- Correction memory integrated into intake.
- Opt-in session correction persistence using gitignored JSONL session stores.

The next planned phase is **Phase B correction classification planning**. Do not implement classification, profile promotion, pending global rule logs, or global rule promotion until the design is explicitly planned and approved.

---

## Core Rule For Future Work

New work should be additive whenever possible.

Do not modify renderer/layout behavior unless explicitly requested.
Do not skip regressions before committing.
Do not commit real command/user profile data to the public repository.
Do not promote user corrections to profiles or global SECNAV rules without a manual review/promotion design.

---

## Current Architecture

### Renderer / Layout Baseline

- `src/pdf_v6_render.py` — ReportLab-based PDF renderer.
- `src/c7_validate.py` — Chapter 7 validation support.
- `src/c8_validate.py` — Chapter 8 multiple-address validation support.
- `src/c9_validate.py` — Chapter 9 endorsement validation support.
- `src/c10_validate.py` — Chapter 10 memorandum validation support.
- `tools/audit_pdf_layout.py` — coordinate/layout audit tool.
- `docs/layout_profiles/` — layout audit profiles.

### CCI Content-Compliance Layer

Seven CCI validators are currently implemented:

1. Subject-line validator.
2. Reference/enclosure validator.
3. Acronym first-use validator.
4. Date and military-time validator.
5. Personnel identification validator.
6. Point-of-contact expectation validator.
7. Routing / Via / Copy-to intelligence validator.

Key files:

- `src/validator_runner.py` — consolidated CCI audit entry point.
- `src/context_resolver.py` — canonical context resolver.
- `src/intake_orchestrator.py` — intake, profile, audit, active-draft correction orchestration, and opt-in session correction persistence.
- `src/local_profile.py` — local command profile loading and default merge support.
- `src/correction_apply.py` — active-draft correction application/undo primitives.
- `src/correction_capture.py` — correction record capture, including `active_draft` and `current_session` scopes.
- `src/correction_store.py` — JSONL session correction persistence store.
- `docs/checkpoints/phase_a_session_persistence_checkpoint.md` — latest Phase A checkpoint.
- `docs/checkpoints/cci_content_compliance_checkpoint.md` — detailed CCI history checkpoint.

---

## Current Intake and Correction Capabilities

The intake layer can currently:

- Identify required/recommended/optional missing fields.
- Ask only for missing information.
- Use active local profile defaults.
- Suppress questions for fields filled by profile defaults.
- Run the consolidated CCI audit.
- Capture active-draft corrections.
- Apply active-draft corrections.
- Undo corrections.
- Rerun audit after correction.
- Track audit conflicts as advisory only.
- Persist corrections to a session JSONL store when a caller explicitly provides `session_id` and the correction is scoped to `current_session`.
- Pre-apply matching session corrections when `doc_type`, `component`, and `field_path` match.
- Soft-mark rejected session corrections with `user_rejected=True` and exclude them from future matching.

### Current Correction Memory Limits

Correction memory is deliberately limited in the current baseline:

- Session persistence is opt-in only; `session_id=None` preserves in-memory-only behavior.
- Session JSONL files are local and gitignored.
- 30-day retention is advisory only; no automatic cleanup is implemented.
- No automatic correction classification.
- No local command profile promotion.
- No pending global rule candidate log.
- No global SECNAV rule promotion.
- No renderer changes.
- Conflicts are advisory only.

---

## Local Profile and Session Store Safety

`profiles/example_local_profile.json` contains fake/example data only.

Real user or command profiles may contain contact information or local command data. Real profiles should **not** be committed to this public repository. Future real profiles should live outside the repo or be gitignored.

Session correction JSONL files under `corrections/session/*.jsonl` are gitignored and may contain original/corrected draft values. Do not commit them.

---

## Build & Regression Commands

Run the full current regression set before committing changes:

```bash
python tools/run_intake_regression.py
python tools/run_correction_regression.py
python tools/run_correction_session_regression.py
python tools/run_profile_regression.py
python tools/run_cci_audit_regression.py
python tools/run_context_schema_regression.py
python tools/run_cci_subject_regression.py
python tools/run_cci_ref_encl_regression.py
python tools/run_cci_acronym_regression.py
python tools/run_cci_date_time_regression.py
python tools/run_cci_personnel_regression.py
python tools/run_cci_poc_regression.py
python tools/run_cci_routing_regression.py
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
python tools/run_c9_regression.py
python tools/run_c10_regression.py
```

GitHub Actions workflow:

- Workflow: `Regression`
- Job: `compliance-regression`
- The workflow should run the CCI, context, audit, intake, profile, correction, session correction, and C7-C10 regression suite.

---

## Session Startup Checklist

For a new chat/session:

1. Read `docs/BOOTSTRAP.md`.
2. Read `docs/PROJECT_STATUS.md`.
3. Read `docs/checkpoints/phase_a_session_persistence_checkpoint.md`.
4. Read `docs/checkpoints/cci_content_compliance_checkpoint.md` if detailed CCI history is needed.
5. Pull latest from GitHub: `git pull origin main`.
6. Check clean working tree: `git status`.
7. Verify current HEAD against `docs/PROJECT_STATUS.md`.
8. Continue from the **Recommended Next Work** section in `docs/PROJECT_STATUS.md`.

Suggested prompt for a new OpenAI chat:

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, and `docs/checkpoints/phase_a_session_persistence_checkpoint.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Run all regressions before committing.

---

## DO NOT

- Do not redesign the architecture without explicit direction.
- Do not create parallel renderers.
- Do not edit renderer/layout casually.
- Do not hardcode spacing values; preserve font-size-aware layout behavior.
- Do not modify rules without updating provenance.
- Do not implement Phase B correction classification without approved planning.
- Do not promote corrections to local profiles or global SECNAV rules yet.
- Do not commit real command profiles, contact data, or session JSONL stores publicly.
- Do not skip regressions.
- Do not assume Navy and Marine Corps conventions are identical.
- Do not ignore rules hidden inside manual figures, captions, or example text.

---

## Compliance Reference

**Primary Source:** SECNAV M-5216.5.  
Always verify generated correspondence against the current manual and the user's local command administrative procedures.

---

**Last Updated:** 2026-06-01  
**Current handoff baseline:** `8c863ff` documentation checkpoint / `71ddf64` verified functional baseline
