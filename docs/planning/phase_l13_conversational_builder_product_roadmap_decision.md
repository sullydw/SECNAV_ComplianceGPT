# Phase L.13 Conversational Builder Product Roadmap Decision

**Date:** 2026-06-13  
**Commit:** `ded164b`  
**Phase:** L.13  
**Purpose:** Commit the product direction toward a safe LLM mediator layer in front of the existing deterministic builder.

---

## 1. Current Achievement

The conversational builder now works end-to-end as a developer/operator CLI prototype:

- `BuilderSession` supports guided key-value intake, validation, finalize, and render.
- CLI supports `/status`, `/warnings`, `/accept-warnings`, `/revise`, `/finalize`, `/render`, `/quit`.
- Structured signature capture works (`signature.name`, `signature.role`, `signature.title`).
- CCI validation runs before finalization and surfaces warnings, errors, and advisories.
- PDF generation works via `src/pdf_v6_render.py` with no renderer modifications.
- L.12A verified the full path: 204/204 regression checks PASS.
- Generated PDFs are not committed; temporary JSON is cleaned up after render.

---

## 2. Product Goal

The builder must evolve from a developer CLI into a user-facing conversational experience:

- A normal user should not need to know key-value field names (`from:`, `to:`, `subj:`).
- The user should be able to describe the letter in natural language:
  *"I need to send a training plan from Commander Sample to CNO."*
- The system should ask natural clarifying questions only for missing required fields.
- The output must still be: structured payload → CCI validation → compliant PDF.
- The user must remain in control of final content and warnings.

---

## 3. Architecture Decision

**Decision: Add an LLM mediator layer in front of `BuilderSession`.**

| Layer | Responsibility | Must Not |
|-------|---------------|----------|
| **LLM Mediator** | Interpret NL input, propose field updates, generate questions, explain warnings | Bypass validation, modify config, invent official data, control renderer layout |
| **BuilderSession** | Own payload state, enforce required fields, run CCI validation, finalize, render | Be replaced by LLM heuristics |
| **Renderer** (`pdf_v6_render.py`) | Consume finalized payload dict and produce PDF | Be modified for builder features |
| **CCI Validator** | Run rules against payload, return findings with severity | Have severity changed by LLM |

**Key principle:** The LLM is a translator and proposal engine. `BuilderSession` remains the source of truth for payload, validation, finalization, and the render path.

---

## 4. Safety Boundaries

The LLM mediator must be constrained by explicit boundaries:

1. **May not bypass validation.** All proposed updates must pass through `BuilderSession.ingest_user_message()` or equivalent structured API.
2. **May not modify CCI severity/config.** Rule severity is fixed by the CCI configuration. The LLM may surface warnings but may not reclassify them.
3. **May not invent official data.** No hallucinated SSICs, command names, references, enclosures, or routing paths. The LLM may suggest common values (e.g., "5216 is a common SSIC for training") but must mark them as user-supplied.
4. **May not silently ignore warnings.** If warnings exist, the LLM must present them to the user and request explicit acceptance (`/accept-warnings`) before finalization.
5. **May not directly control renderer layout.** The LLM may invoke `/render` but may not modify `pdf_v6_render.py` or canvas drawing logic.
6. **LLM output is proposed, not final.** Every payload update must be stored in `BuilderSession` and subject to the same validation as manual key-value input.

---

## 5. Proposed Mediator Contract

### Input

```python
{
    "builder_state": {
        "session_id": str,
        "current_step": str,
        "payload": dict,
        "missing_required": list[str],
        "missing_recommended": list[str],
        "current_warnings": list[dict],
        "current_errors": list[dict],
    },
    "user_message": str,
}
```

### Output

```python
{
    "intent": "fill_field" | "ask_question" | "revise" | "finalize" | "render" | "explain_warning",
    "proposed_payload_update": dict | None,
    "next_question": {
        "field_path": str,
        "prompt_text": str,
        "bucket": "required" | "recommended",
    } | None,
    "explanation": str,
    "requires_user_confirmation": bool,
    "warnings_to_surface": list[dict],
}
```

### Invariant

All `proposed_payload_update` values must be passed through:

```python
builder.ingest_user_message(f"{field_path}: {value}")
```

This ensures the LLM cannot inject arbitrary JSON into the payload without the builder's validation, normalization, and question logic.

---

## 6. Recommended Next Phase

`Phase L.14  LLM Builder Mediator Contract Design`

Goal: Design the concrete mediator interface (function signatures, data schemas, error cases, confirmation flows). Document the contract between LLM output and `BuilderSession` input. No LLM API integration yet.

---

## 7. Later Roadmap

| Phase | Goal |
|-------|------|
| L.15 | Mediator prototype with mock/deterministic LLM output (no real API) |
| L.16 | Real LLM adapter boundary (OpenAI, local, or gateway provider) |
| L.17 | Guided natural-language intake demo |
| L.18 | Validation/revise loop with LLM explanations |
| L.19 | User-facing interface decision (web UI, TUI, chatbot, etc.) |

---

## 8. Explicit Non-Goals

- No NL parser implementation in L.13.
- No real LLM API integration in L.13.
- No renderer/layout changes.
- No CCI config/severity changes.
- No rule promotion.
- No validator/catalog changes.
- No Phase F/G command-layer changes.
- No intake policy/questions JSON changes.
- No generated PDFs or logs committed.
- Do not read or modify `docs/BOOTSTRAP.md`.
- Do not modify `docs/HERMES_INSTRUCTIONS.md`.

---

## Decision

The builder track will proceed toward an LLM mediator layer. The deterministic `BuilderSession` backend is preserved as the source of truth. Safety boundaries are explicit and enforceable. The next step is contract design (L.14), not implementation.
