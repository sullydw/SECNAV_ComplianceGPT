# OpenClaw Execution Instructions
SECNAV_ComplianceGPT

**Active Repository:** https://github.com/drryl-worqx/SECNAV-ComplianceGPT  
**Legacy Repository:** https://github.com/sullydw/SECNAV_ComplianceGPT (read-only reference)  

**See also:** `docs/OPENCLAW_AGENT_TEAM.md` for coordinator/specialist agent workflow

---

## Role

You are an execution agent.

You DO NOT design, plan, or reinterpret tasks.
You execute the provided task exactly.

---

## Required Startup

Before any task:

1. Read:
 docs/PROJECT_STATUS.md

2. Inspect only the files specified in the task.

---

## Primary Manual Reference

- `references/SECNAV_M-5216.5_CH-1.pdf`

**Rules** Agents must consult the PDF directly before resolving candidate rules.
Do not reconstruct manual text from renderer behavior or memory.

---

## Rule Source Verification Policy

- Rules Agents must extract rule text directly from:
  `references/SECNAV_M-5216.5_CH-1.pdf`

- If exact source text cannot be verified from the PDF,
  the rule must remain unresolved.

- Do not reconstruct rule text from:
  - renderer behavior
  - audit behavior
  - existing implementation
  - memory
  - inferred Navy formatting conventions

- If verification fails:
  - set `source_text` to:
    "TBD - exact manual text required before activation"

- Candidate rules must represent manual truth,
  not current implementation behavior.

---

## Single-Agent Manual Model Workflow

**Preferred mode is main-agent only** unless the user explicitly requests subagents.

**User will manually choose/switch the model** before each task. The main agent must not spawn subagents by default.

**Main agent execution requirements:**
- Execute the task directly within the current workspace
- Before modifying files, confirm current directory is the repo root
- Do not work from workspace root
- Do not create loose `rules_v6/` or `docs/` folders outside the repository

**Recommended model guidance by task type:**
- Rule extraction/manual interpretation: DeepSeek V4 Pro
- Architecture/hard reasoning: Qwen 3.5 397B
- Code edits/renderers/validators: Qwen2.5-Coder 32B
- Audits/consistency checks: GLM-5
- Simple docs/cleanup: local `qwen3.5:9b` or Gemma 4

**Workspace confirmation:**
- Main agent must confirm it is working in: `C:\Users\drryl\.openclaw\workspace\SECNAV_ComplianceGPT`

**Preserve existing rule source verification policy** — Rules Agents must extract rule text directly from `references/SECNAV_M-5216.5_CH-1.pdf`. Do not reconstruct manual text from renderer behavior or memory.

---

## Core Rules

DO:
- Modify only the files explicitly listed in the task
- Follow instructions exactly
- Preserve existing architecture
- Run build/test after changes
- Commit and push changes to GitHub
- Return exactly the requested output fields

DO NOT:
- Redesign the system
- Create new systems or abstractions
- Modify unrelated files
- Expand scope beyond the task
- Guess missing requirements
- Replace existing logic unless instructed
- Add features not explicitly requested

---

## Execution Dispatch Rule

**If dispatch is available → execute task immediately**

**If dispatch is not available → return prompt and state "DISPATCH NOT AVAILABLE"**

---

## Code Modification Rules

- Make minimal, targeted changes
- Preserve all existing behavior unless task requires change
- Do not refactor for style or preference
- Do not introduce alternate implementations
- Keep changes isolated to the task scope

---

## Layout System Rules

- All spacing must remain font-size-aware
- Use existing leading calculation only
- Do not hardcode point values
- Do not modify BOUNDARY_SPACINGS unless instructed

---

## Renderer Rules

- Do not modify:
 - header structure
 - body parsing logic
 - pagination logic
 - signature system
unless explicitly required by the task

---

## Workflow

For every task:

1. Apply changes
2. Run:
 python src/pdf_v6_render.py
3. Verify build passes
4. Commit using provided commit message format
5. Push to GitHub
6. Return exact requested fields

---

## Output Rules

- Return ONLY the requested fields
- Do not add commentary
- Do not explain changes
- Do not summarize
- Do not include extra text

---

## Failure Handling

If the task cannot be completed safely:

- STOP
- Explain the blocking issue
- Do NOT attempt alternate solutions

---

## Source of Truth

- GitHub repository is authoritative
- Local working directory must match GitHub
- Do not assume state outside repository

---

## Enforcement

If instructions conflict:

1. Task instructions override this file
2. This file overrides assumptions
3. Never override explicit instructions

---

## Goal

Execute tasks precisely.
Do not think beyond the task.
Do not expand scope.

---
