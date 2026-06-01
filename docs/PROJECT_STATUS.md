# SECNAV ComplianceGPT - Project Status

**Last Updated:** 2026-05-31  
**GitHub (Active):** https://github.com/sullydw/SECNAV_ComplianceGPT  
**GitHub (Invalid/Nonexistent):** https://github.com/drryl-worqx/SECNAV-ComplianceGPT — DO NOT USE  
**Renderer:** v6 PDF (ReportLab)  
**Branch:** `main`

---

## Current Handoff Summary

This is the main status tracker for SECNAV_ComplianceGPT. A new OpenAI chat or developer agent should read this file after `docs/BOOTSTRAP.md` and before starting new work.

**Latest documentation checkpoint commit:** `8efdff6` — `Docs: Record correction intake integration baseline`  
**Current verified functional baseline:** `2e643db` — `CCI: Integrate correction memory with intake`  
**GitHub Actions:** manually verified PASS by user for commit `2e643db`  
**Expected repository state:** clean and up to date with `origin/main`

### Start Here For New Chat

1. Read `docs/BOOTSTRAP.md`.
2. Read this file: `docs/PROJECT_STATUS.md`.
3. Read `docs/checkpoints/cci_content_compliance_checkpoint.md` for detailed CCI/intake/correction status.
4. Do not modify renderer/layout unless explicitly asked.
5. Continue from the **Recommended Next Work** section below.
6. Run all regressions before committing.

Suggested startup prompt:

> Read `docs/BOOTSTRAP.md`, `docs/PROJECT_STATUS.md`, and `docs/checkpoints/cci_content_compliance_checkpoint.md` first. Then help continue from the recommended next phase. Do not modify renderer/layout unless explicitly asked. Run all regressions before committing.

---

## Current Implemented Architecture

### Protected Renderer/Layout Baseline

Chapters 7-10 of SECNAV M-5216.5 are implemented and regression-protected for the current project scope:

- C7 standard letters, continuation pages, and joint letters.
- C8 multiple-address letters using To-line, Distribution, and To-plus-Distribution formats.
- C9 new-page endorsements.
- C10 Memorandums for the Record and plain-paper From-To memorandums.

Figure 9-1 same-page endorsements and additional C10 memorandum types remain deferred or outside the current scope unless explicitly reopened.

### Correspondence Content Intelligence Layer

The CCI layer is now a deterministic and heuristic content-compliance layer above the renderer. It validates the JSON payload before rendering and does not change layout behavior.

Implemented CCI validators:

1. Subject-line validator.
2. Reference/enclosure validator.
3. Acronym first-use validator.
4. Date and military-time validator.
5. Personnel identification validator.
6. Point-of-contact expectation validator.
7. Routing / Via / Copy-to intelligence validator.

### Context, Audit, Intake, Profiles, and Correction Memory

Implemented support now includes:

- `src/context_resolver.py` — canonical CCI context object.
- `src/validator_runner.py` — consolidated CCI audit entry point.
- `src/intake_orchestrator.py` — missing-field intake, active profile support, CCI audit, active-draft correction integration.
- `src/local_profile.py` — local command profile loading and default merging.
- `src/correction_apply.py` — active-draft correction application and undo primitives.
- `src/correction_capture.py` — active-draft correction record capture.

Current intake capabilities:

- Identifies missing required/recommended/optional fields.
- Asks only for missing information.
- Uses active local profile defaults.
- Suppresses questions for fields filled by profile defaults.
- Runs the consolidated CCI audit.
- Captures active-draft corrections.
- Applies active-draft corrections.
- Undoes corrections.
- Reruns audit after correction.
- Tracks conflicts as advisory only.

---

## Current Correction Memory Limits

Correction memory is intentionally limited in the current verified baseline:

- Active-draft/in-memory only.
- No disk persistence.
- No local profile promotion.
- No global SECNAV rule promotion.
- No automatic correction classification.
- No renderer changes.
- Conflicts are advisory only.

Do not implement persistence, profile promotion, or global rule promotion without a separate planning step and user approval.

---

## Local Profile Safety

`profiles/example_local_profile.json` is fake example data only.

Real user or command profiles may contain contact information or local command data. Real profiles should **not** be committed to this public repository. Future real profiles should live outside the repository or be gitignored.

---

## CI / Regression Coverage

GitHub Actions workflow:

- Workflow: `Regression`
- Job: `compliance-regression`
- Verified PASS for current functional baseline commit `2e643db`

Run the full current regression suite before committing changes:

```bash
python tools/run_intake_regression.py
python tools/run_correction_regression.py
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

The CI suite covers:

- 7 CCI validator regressions.
- Context schema regression.
- Consolidated CCI audit regression.
- Intake regression.
- Local profile regression.
- Active-draft correction memory regression.
- C7-C10 layout/render regressions.

---

## Key Files

- `docs/BOOTSTRAP.md` — first-read guide for new chats/sessions.
- `docs/PROJECT_STATUS.md` — current status and handoff tracker.
- `docs/checkpoints/cci_content_compliance_checkpoint.md` — detailed CCI checkpoint.
- `.github/workflows/regression.yml` — GitHub Actions regression workflow.
- `src/pdf_v6_render.py` — renderer; do not modify casually.
- `src/validator_runner.py` — one-call CCI audit runner.
- `src/intake_orchestrator.py` — intake, profiles, correction memory orchestration.
- `src/context_resolver.py` — CCI context resolver.
- `src/local_profile.py` — local profile support.
- `src/correction_apply.py` and `src/correction_capture.py` — active-draft correction support.
- `profiles/example_local_profile.json` — fake/template profile only.

---

## What Not To Do

- Do not edit renderer/layout casually.
- Do not create a parallel renderer.
- Do not persist corrections yet.
- Do not promote corrections to local profiles or global SECNAV rules yet.
- Do not commit real command profiles or contact data publicly.
- Do not skip regressions.
- Do not assume Navy and Marine Corps conventions are identical.
- Do not ignore rules hidden inside manual figures, captions, or example text.
- Do not modify rules without preserving/updating provenance.

---

## Recommended Next Work

### Next Phase: Persistent Correction / Session Storage Planning

The next recommended phase is planning only at first.

Goals:

- Decide what may be stored beyond the active draft.
- Separate session memory from local command profile promotion.
- Protect against bad corrections becoming permanent behavior.
- Design a review/promotion workflow.
- Keep global SECNAV rule promotion manual and reviewed.
- Avoid writing real command/user profile data to the public repo.

Recommended planning target:

- Persistent session storage for active draft corrections.
- Clear distinction between:
  - one-draft corrections,
  - reusable session corrections,
  - local command profile candidates,
  - possible global rule bugs or SECNAV interpretation issues.

Do **not** implement persistence before the storage model and safety rules are reviewed.

---

## Historical Milestones

### Chapters 7, 8, 9, and 10 Rule/Layout Baseline

- C7 candidate rules created and audited.
- C8 candidate rules created and audited.
- C9 new-page endorsement support implemented and guarded by regression.
- C10 MFR and plain-paper From-To memorandum support implemented and guarded by regression.
- Figure 9-1 same-page endorsements remain deferred.
- Additional C10 memorandum types remain outside current scope.

### Automated Layout Audit Coverage

The project has automated PDF layout audits wired into each chapter regression suite. These are profile-based coordinate checks, not pixel-image comparisons. Manual visual review remains required for final compliance.

Covered figures include:

- C7: Figure 7-1 Standard Letter, Figure 7-2 Continuation Page, Figure 7-4 Joint Letter.
- C8: Figure 8-1 Multiple-Address To-line, Figure 8-2 Distribution-line, Figure 8-3 To + Distribution.
- C9: Figure 9-2 New Page Endorsement.
- C10: Figure 10-1 MFR and Figure 10-3 Plain-Paper From-To variants.

### Manual-and-Figure Source Standard

Every new layout profile and rule interpretation must be grounded in all available manual guidance, including:

1. Chapter/section text surrounding the figure.
2. Figure title/caption.
3. Instructional text inside the figure example itself.
4. Actual visual/layout geometry.
5. Existing project rule files and renderer behavior.

Figures are rule-bearing and must be reviewed when referenced.

---

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and the user's command administrative procedures.
