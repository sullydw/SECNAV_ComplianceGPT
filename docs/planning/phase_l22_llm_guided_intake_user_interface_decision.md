# Phase L.22 — LLM-Guided Intake User Interface Decision

**Date:** 2026-06-14  
**Baseline Commit:** `bc68cdeb4b90297cc46acc9e94237ff99c7bd5c1`  
**Phase Type:** Planning / Decision  
**Status:** Decision reached

---

## Purpose

Decide how the LLM-guided conversational intake flow (proven in Phase L.21) should be exposed to users going forward.

---

## Context

Phase L.21 proved:
- Natural-language messages translate to structured field updates through the mock mediator
- All updates route through `BuilderSession.ingest_user_message()` (no direct mutation)
- Adapter safety filters (`LLMBuilderMediatorAdapter`) operate transparently
- Validation, warning acceptance, finalize, and PDF render all work end-to-end
- No real LLM/API/network calls required for full regression
- Total verification: 265/265 PASS + 1 optional smoke SKIP

The system now has three proven layers:
1. **BuilderSession** — source of truth for payload, validation, finalize, render
2. **LLMBuilderMediatorAdapter** — safety boundary on mediator outputs
3. **LLMProviderConfig / build_llm_backend_from_config** — pluggable backend (mock default, optional live)

---

## Options Evaluated

### Option 1: Enhanced CLI Chat Mode

**Pros**
- Easiest next step from existing CLI (`tools/run_phase_l7_conversational_builder_cli.py`)
- Keeps local testing simple (no additional dependencies)
- Good for Hermes/operator workflow
- Fast iteration for developer/regression use

**Cons**
- Weak for end-user usability (terminal input is intimidating for non-technical users)
- Hard to visualize structured draft, warnings, and PDF status simultaneously
- Not shareable as a demo

**Verdict:** Keep as regression/operator fallback. Do not remove. Not the primary user-facing path.

---

### Option 2: Streamlit Web UI

**Pros**
- Likely best near-term user-facing prototype
- Easy local form/chat hybrid (single Python file, `streamlit run`)
- Can show payload, warnings, finalize/render buttons side-by-side
- Native file download widget for generated PDF
- Large community and rapid prototyping ecosystem
- No separate frontend build step needed

**Cons**
- Slightly heavier dependency (Streamlit package)
- Long-term scaling beyond single-user local use may require rewrite
- Less control over UI layout than custom React/Vue

**Verdict:** **Recommended next implementation phase.** Best balance of speed-to-prototype and user-facing value.

---

### Option 3: Flask/FastAPI Backend + Separate Frontend

**Pros**
- Stronger long-term architecture
- Better if multi-user/web deployment becomes a goal
- Clean separation of concerns
- Frontend can evolve independently

**Cons**
- Significantly more work (two codebases, API contract, CORS, auth)
- Overkill for a single-user local prototype
- Slows iteration while UX is still stabilizing

**Verdict:** Defer until core UX stabilizes. Not needed for immediate prototype.

---

### Option 4: ChatGPT/Project-Only Workflow

**Pros**
- Useful for design and prompt orchestration experiments
- No local infrastructure required

**Cons**
- Not enough as standalone local product (cannot guarantee renderer/file behavior without local harness)
- Cannot directly validate PDF output, SECNAV formatting, or CCI compliance
- No offline capability
- API costs and rate limits

**Verdict:** May be used for prompt design experiments only. Not a shipping UI path.

---

### Option 5: Hybrid Recommendation (Chosen)

| Layer | Tool | Purpose |
|-------|------|---------|
| Regression / Operator | Enhanced CLI | Developer testing, automated regressions, quick checks |
| User-Facing Prototype | Streamlit | Guided intake, draft preview, warnings, finalize, PDF download |
| Future Production | Flask/FastAPI + Frontend | Multi-user, hosted, API-driven (deferred) |
| Prompt Design | ChatGPT/Projects | Experimental prompt refinement (manual, non-blocking) |

---

## Decision

**Recommended next phase: `Phase L.23  Streamlit LLM-Guided Intake Prototype`**

### Rationale
- Streamlit offers the fastest path to a usable, visible prototype
- The BuilderSession + Adapter + Provider layers are already proven; Streamlit is just a thin presentation layer
- Can be built incrementally: chat input → draft panel → warnings → finalize → render → download
- No renderer/layout/CCI/config changes required
- Mock backend remains the default; optional live provider stays manual-only
- If Streamlit proves inadequate later, the backend logic (BuilderSession, adapter, provider) migrates cleanly to Flask/FastAPI

---

## Streamlit Prototype Scope (L.23)

### UI Elements

| Element | Purpose |
|---------|---------|
| **Chat-style user input box** | User types natural-language field updates or commands |
| **Current draft summary panel** | Shows payload snapshot (from, to, subj, ssic, body, signature, etc.) |
| **Missing fields panel** | Lists `missing_required_fields` and `missing_recommended_fields` |
| **Validation / warnings panel** | Displays validator findings with color coding (advisory/warning/error) |
| **Accept warnings button** | Explicit user confirmation to proceed despite warnings |
| **Finalize button** | Triggers `builder.finalize()` when `finalize_allowed=True` |
| **Render PDF button** | Triggers PDF render on finalized payload; offers download |
| **Provider status indicator** | Shows: `mock/default`, `optional live/manual`, or `unavailable/fail-closed` |

### Out of Scope for L.23

- Direct renderer/layout controls (not exposed to user)
- CCI severity/config toggles (read-only display only)
- Raw API key display (never shown)
- Multi-user auth or persistence
- Deployment packaging (Docker, etc.)

---

## Safety Requirements for L.23

1. UI must **not mutate payload directly** from LLM output
2. UI must **pass mediator output through adapter validation** (`LLMBuilderMediatorAdapter`)
3. UI must **pass accepted field updates through BuilderSession ingestion** (`ingest_user_message()`)
4. **BuilderSession owns final payload** — UI is a viewer, not a mutator
5. **Validation remains required** before finalize/render are enabled
6. **Warning acceptance must be explicit** — button click or typed command
7. **Render must only operate on finalized payload** — button disabled otherwise
8. **Generated PDFs/logs should not be committed** — `.gitignore` enforced

---

## Testing Recommendations for L.23

| Test | Method |
|------|--------|
| Streamlit app import smoke test | `python -c "import app; print('ok')"` |
| Non-UI logic unit runner | Standalone script exercising `BuilderSession` + `Adapter` through simulated Streamlit callbacks |
| No browser automation required initially | Streamlit's `st.run` or direct function testing is sufficient |
| Normal regressions remain offline | No live LLM calls; mock backend default |
| Optional live provider not required | Smoke harness (`SECNAV_LLM_LIVE_SMOKE=1`) already covers this |
| Generated PDF cleanup required | Test teardown removes `output/*.pdf` and `output/*.log` |

---

## Explicit Non-Goals (L.22)

- No Streamlit implementation in this phase (planning only)
- No real LLM/API/network calls
- No API keys/secrets committed or printed
- No renderer/layout changes
- No CCI config/severity changes
- No rule promotion
- No validator/catalog changes
- No Phase F/G command layer changes
- No intake policy/questions JSON changes
- No generated PDFs/logs committed
- No changes to `docs/BOOTSTRAP.md` or `docs/HERMES_INSTRUCTIONS.md`

---

## Next Phase

`Phase L.23  Streamlit LLM-Guided Intake Prototype`

Goal: Build a lightweight Streamlit app (`streamlit_app.py` or `app.py`) that wraps the BuilderSession + Adapter + Provider layers in a user-friendly web interface.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Streamlit dependency conflicts | Pin version in requirements; test import smoke |
| Users expect real LLM by default | Clear mock-default indicator; optional live clearly labeled |
| UI bypasses adapter/session | Enforce all paths through existing proven functions |
| Over-exposing internal state | Display read-only summaries; mutations only through ingest |
| PDF accumulation in output/ | `.gitignore` + test teardown |
