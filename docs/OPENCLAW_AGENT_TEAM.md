# OpenClaw Agent Team - SECNAV_ComplianceGPT

**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT

---

## Overview

This project uses a coordinator + specialist agent model for precise, bounded task execution.

**Core Principle:** One agent per task. Exact file scope required. No vague exploratory changes.

---

## Coordinator Agent

**Role:** Task routing and orchestration

**Responsibilities:**
- Reads `docs/PROJECT_STATUS.md` for current system state
- Reads `docs/OPENCLAW_INSTRUCTIONS.md` for execution rules
- Selects the correct specialist agent based on task scope
- Produces bounded task prompts with explicit file lists
- Does NOT make code changes unless explicitly instructed

**Forbidden:**
- Editing source files directly
- Redesigning architecture without explicit instruction
- Expanding task scope beyond user request

---

## Renderer Agent

**Scope:** `src/pdf_v6_render.py` only

**Responsibilities:**
- Layout and spacing fixes
- ReportLab canvas rendering
- Pagination logic
- Signature block placement
- Distribution/Copy to rendering

**Forbidden:**
- Editing `rules_v6/*.json`
- Editing `src/letter_model_v6.py`
- Editing `docs/*.md`
- Editing `examples/*.json`
- Modifying BOUNDARY_SPACINGS unless explicitly instructed

**Required after changes:**
- Run: `python src/run_audit_cases.py`
- Verify all audit PDFs generate successfully

---

## Rules Agent

**Scope:** `rules_v6/*.json` only

**Responsibilities:**
- Adding/updating rule entries (H-series, F-series, P-series, S-series, V-series)
- Ensuring rule schema consistency
- Maintaining provenance tracking

**Forbidden:**
- Editing `src/pdf_v6_render.py`
- Editing `src/letter_model_v6.py`
- Editing `docs/*.md`
- Editing `examples/*.json`

**Required after changes:**
- Validate JSON syntax
- Run: `python src/pdf_v6_render.py`
- Verify renderer loads rules without errors

---

## Model Agent

**Scope:** `src/letter_model_v6.py` only

**Responsibilities:**
- Payload normalization logic
- Default value handling
- Derived field computation

**Forbidden:**
- Editing `src/pdf_v6_render.py`
- Editing `rules_v6/*.json`
- Editing `docs/*.md`
- Editing `examples/*.json`

**Required after changes:**
- Run: `python src/letter_model_v6.py`
- Verify normalization produces expected output

---

## Audit Agent

**Scope:** `src/run_audit_cases.py`, `output/*.pdf`, `examples/audit_*.json`

**Responsibilities:**
- Running audit test suites
- Inspecting generated PDFs
- Measuring layout spacing
- Reporting exact findings with debug output

**Forbidden:**
- Modifying any files unless explicitly instructed
- Changing renderer behavior

**Required after audit:**
- Report: PDF timestamps, spacing measurements, pass/fail status

---

## Docs Agent

**Scope:** `docs/*.md` only

**Responsibilities:**
- Updating `PROJECT_STATUS.md` with current behavior
- Maintaining `OPENCLAW_INSTRUCTIONS.md`
- Writing `CHANGELOG.md` entries
- Creating/updating architecture documentation

**Forbidden:**
- Editing `src/*.py`
- Editing `rules_v6/*.json`
- Editing `examples/*.json`

**Required after changes:**
- Verify markdown syntax
- Ensure consistency with actual code behavior

---

## Strict Rules (All Agents)

1. **One agent per task** - Do not switch roles mid-task
2. **Exact file scope required** - Only modify files explicitly listed
3. **No redesign unless explicitly instructed** - Preserve existing architecture
4. **No vague exploratory changes** - Every change must trace to a specific requirement
5. **GitHub is authoritative** - Local working directory must match GitHub
6. **Run required tests/builds after changes** - Verify before committing
7. **Return only requested fields** - No commentary, no summaries

---

## Task Handoff Protocol

When a task requires multiple agents:

1. Coordinator completes routing, yields to specialist
2. Specialist completes scoped work, runs tests
3. Specialist commits with provided message
4. Coordinator verifies, may route to next specialist if needed

**Example:**
```
Task: "Fix body spacing and update docs"
1. Coordinator → Renderer Agent (fix spacing in pdf_v6_render.py)
2. Renderer Agent → runs audit, commits
3. Coordinator → Docs Agent (update PROJECT_STATUS.md)
4. Docs Agent → commits
```

---

## Failure Handling

If any agent cannot complete the task safely:

1. STOP immediately
2. Explain the blocking issue
3. Do NOT attempt alternate solutions
4. Wait for coordinator or user direction

---

**Last Updated:** 2026-05-07  
**Source of Truth:** GitHub repository
