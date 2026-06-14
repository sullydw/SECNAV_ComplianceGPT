# Phase L.16 LLM Mediator Adapter Boundary Design

**Date:** 2026-06-13  
**Commit:** `c500da4`  
**Phase:** L.16  
**Purpose:** Design the adapter boundary where a real LLM can replace the mock mediator's intent detection and field extraction while preserving the L.14/L.15 contract and BuilderSession handoff invariant.

---

## 1. Current Proven Contract

### MediatorInput (11 fields)
- `session_id`, `current_step`, `payload_snapshot`
- `missing_required_fields`, `missing_recommended_fields`
- `validation_summary`, `warning_summary`, `error_summary`
- `user_message`, `conversation_history_summary`
- `available_commands`, `safety_flags`

### MediatorOutput (10 fields)
- `intent`, `proposed_payload_update`, `proposed_key_value_lines`
- `next_question`, `explanation`, `requires_user_confirmation`
- `warnings_to_surface`, `blocked_reason`, `confidence`, `safety_notes`

### Allowed Intents (8)
`start_letter`, `provide_field`, `revise_field`, `accept_warnings`, `request_warning_explanation`, `finalize`, `render_pdf`, `unknown`

### Confirmation Policy
- Direct user-provided simple fields: no confirmation
- Inferred values, official data: confirmation required
- Warning acceptance, finalization, rendering: confirmation required

### BuilderSession Handoff Invariant
**All proposed updates must pass through `builder.ingest_user_message()`.** The mediator (mock or LLM) may only emit `proposed_payload_update` or `proposed_key_value_lines`. BuilderSession is the only component that may mutate payload, run validation, or allow finalize/render.

### Safety Boundaries (L.13, reinforced L.14–L.15)
1. LLM may not bypass validation
2. LLM may not modify CCI severity/config
3. LLM may not invent official data
4. LLM may not silently ignore warnings
5. LLM may not directly control renderer layout
6. LLM output is proposed, not final

---

## 2. Adapter Role

The `LLMBuilderMediatorAdapter` is a thin boundary layer:

- **Calls a real LLM or local model** in future (not now — see §9)
- **Requests structured JSON** matching the MediatorOutput schema
- **Validates LLM output** before returning anything to the caller
- **Degrades safely** to `unknown` intent + clarification `next_question` on bad output
- **Never passes through** raw LLM output without schema validation
- **Never permits** the LLM to mutate BuilderSession directly
- **Maintains** the L.14/L.15 contract exactly

---

## 3. Proposed Adapter Interface

### `LLMBuilderMediatorAdapter`

```python
class LLMBuilderMediatorAdapter:
    """
    Thin boundary between a real LLM backend and the BuilderSession.
    
    Injected backend: a callable that takes a prompt string and returns
    raw text (expected to be JSON matching MediatorOutput schema).
    The backend may be a mock, a local model, or a cloud API.
    """

    def __init__(
        self,
        backend: Callable[[str], str] | None = None,
        allowed_intents: list[str] | None = None,
        max_confidence: float = 1.0,
        min_confidence: float = 0.0,
        safety_filter: SafetyFilter | None = None,
    ) -> None:
        ...

    def mediate(self, input_data: dict) -> dict:
        """
        Adapter entry point. Mirrors MockLLMBuilderMediator.mediate().
        
        Flow:
          1. Build prompt from input_data (builder state + user message)
          2. Call backend(prompt) → raw text
          3. Parse raw text as JSON
          4. Validate against MediatorOutput schema
          5. Run safety filters
          6. Return sanitized MediatorOutput dict
          7. On any failure → return degraded unknown/clarification output
        """
        ...
```

### Backend Interface

```python
def example_backend(prompt: str) -> str:
    """
    Backend contract: accept prompt string, return JSON text.
    Must NOT be hardcoded to any vendor.
    
    May be:
      - MockBackend (returns deterministic JSON for tests)
      - LocalBackend (llama.cpp, vLLM, etc.)
      - CloudBackend (OpenAI, Anthropic, etc.)
    """
    ...
```

### No Hardcoded Vendor Dependency

The adapter knows only about the `backend: Callable[[str], str]` signature. It does not import `openai`, `anthropic`, `httpx`, or any vendor-specific module. Vendor integration is injected at runtime.

---

## 4. Strict Output Validation

### Required-Keys Check
If any of these are missing from the LLM's JSON output, the adapter degrades to `unknown`:
- `intent`
- `proposed_payload_update`
- `proposed_key_value_lines`
- `confidence`

### Intent Validation
- Must be one of the 8 allowed intents.
- Unsupported intent → replaced with `unknown` + `explanation`.

### Payload Update Validation
- `proposed_payload_update` must be a `dict`.
- Non-dict → empty dict + `safety_note`.

### Key-Value Lines Validation
- `proposed_key_value_lines` must be a `list`.
- Every element must be a `str`.
- Non-conforming elements → filtered out + `safety_note`.

### Confidence Bounding
- `confidence` must be a `float` (or int).
- Clamp to `[0.0, 1.0]` if outside range.
- Non-numeric → set to `0.5` + `safety_note`.

### Prohibited Fields Rejection
The adapter must reject (clear to empty/null with `safety_note`) any of the following in `proposed_payload_update`:
- `cci_severity`
- `cci_config`
- `rule_promotion`
- `renderer_directive`
- `layout_override`
- `pdf_engine`
- `font_settings`
- `page_margins`

---

## 5. Prompt Contract

### System Instructions (must appear in prompt)

The adapter builds a prompt containing these system-level instructions to constrain the LLM:

```
You are a translator, not the source of truth.
Your role: interpret user natural-language input and propose structured field updates.
You do NOT own final state, validation, or rendering.

Rules:
1. Do not invent official data (SSIC, command names, routing, references).
2. Output must be valid JSON matching the schema below — no markdown, no prose outside JSON.
3. Use only the allowed intents listed below.
4. Warnings and errors from the validation system must be surfaced, not suppressed.
5. All field updates are proposals only; they will be reviewed before application.
6. Do not include renderer/layout instructions.
7. Do not include CCI configuration or severity directives.
8. If the user asks for something ambiguous, ask a clarifying question.
9. If the user asks for official data you do not have, do not guess — set next_question.
```

### Schema Snippet in Prompt

The prompt must include a JSON schema snippet describing MediatorOutput fields so the LLM knows the exact expected structure.

### Dynamic Context in Prompt

The prompt must include:
- Current `payload_snapshot` (sanitized — no PII/SSN/EDIPI)
- `missing_required_fields`
- `missing_recommended_fields`
- `validation_summary` (summary counts only, not full audit)
- `warning_summary` (plain-English warning messages)
- `error_summary` (plain-English error messages)
- `user_message` (the current turn)
- `current_step`

### What Must NOT Appear in Prompt
- Renderer/layout directives
- CCI severity configuration
- Validator catalog internals
- Phase F/G command-layer details
- Unsanitized logs or raw audit dumps

---

## 6. Safety Filters

### Filter: CCI Config/Severity Modification
- Reject any `proposed_payload_update` containing keys matching `cci_severity`, `cci_config`, `rule_promotion`, `severity_override`.
- Clear value to null + add `safety_note`.

### Filter: Renderer/Layout Directives
- Reject any keys matching `renderer_directive`, `layout_override`, `pdf_engine`, `font_settings`, `page_margins`, `header_format`, `footer_format`.
- Clear value to null + add `safety_note`.

### Filter: Invented Official Data
- If `proposed_payload_update` contains `ssic` and it was not in the user's message or prior payload → mark for confirmation + add `safety_note`.
- If `proposed_payload_update` contains command-like routing that was not provided → mark for confirmation + add `safety_note`.

### Filter: Silent Warning Acceptance
- If LLM output sets `accept_warnings` intent but the `warning_summary` is empty → degrade to `unknown` + add `safety_note`.
- If LLM output sets `accept_warnings` but user message did not explicitly request warning acceptance → degrade to `unknown` + require confirmation.

### Filter: Direct Finalization/Render
- If LLM output has `finalize` or `render_pdf` intent but `requires_user_confirmation` is `False` → force `requires_user_confirmation = True` + add `safety_note`.
- The adapter may never allow the LLM to finalize or render without explicit user confirmation.

### Filter: Low Confidence
- If `confidence < 0.3` → degrade to `unknown` intent + set `next_question`.
- Add `safety_note` explaining low-confidence degradation.

---

## 7. Failure Handling

| Failure Mode | Adapter Behavior |
|---|---|
| **Model unavailable** | Degrade to `unknown` + `next_question` asking user to retry |
| **Invalid JSON** | Degrade to `unknown` + `explanation` about parse failure |
| **Missing keys** | Degrade to `unknown` + fill missing with safe defaults |
| **Unsupported intent** | Replace with `unknown` + `safety_note` |
| **Unsafe field update** | Clear unsafe fields + add `safety_note` |
| **Low confidence** | Degrade to `unknown` + `next_question` |
| **Conflicting user instructions** | Degrade to `unknown` + ask for clarification |
| **Pending warnings** | If intent is `finalize`/`render_pdf` and warnings exist, block with `blocked_reason` |

All degradation paths must still return a valid `MediatorOutput` dict — never raise an exception to the caller.

---

## 8. Test Strategy for L.17

The L.17 regression runner should test the adapter with **fake backends** only:

### Fake Backend: Valid JSON
- Returns well-formed MediatorOutput
- Adapter passes through cleanly
- Proposed updates go through BuilderSession

### Fake Backend: Malformed JSON
- Returns broken JSON
- Adapter degrades to `unknown`
- No crash

### Fake Backend: Missing Keys
- Returns JSON missing `intent` or `confidence`
- Adapter fills safe defaults
- No crash

### Fake Backend: Unsupported Intent
- Returns intent `delete_everything`
- Adapter replaces with `unknown` + safety note

### Fake Backend: Config/Severity Tamper Attempt
- Returns `proposed_payload_update` with `cci_severity` key
- Adapter clears key + safety note

### Fake Backend: Hallucinated SSIC
- Returns `proposed_payload_update` with invented `ssic`
- Adapter marks for confirmation + safety note

### Fake Backend: Silent Warning Suppression
- Returns `accept_warnings` intent when warnings exist but user did not request it
- Adapter degrades to `unknown` or forces confirmation

### Fake Backend: Unauthorized Finalize
- Returns `finalize` intent with `requires_user_confirmation = False`
- Adapter forces confirmation = True + safety note

### Fake Backend: Renderer Directive
- Returns `proposed_payload_update` with `layout_override`
- Adapter clears key + safety note

### Invariant Check
- All proposed updates from adapter output must still go through `builder.ingest_user_message()` before any payload mutation.

---

## 9. Implementation Recommendation

### L.17 Scope
- Implement `LLMBuilderMediatorAdapter` class
- Implement `MockBackend` for deterministic testing
- Wire adapter + mock backend to `BuilderSession` via `ingest_user_message`
- Run regression with fake backends only
- **No real LLM API calls yet**

### Real LLM Integration Delayed Until
- L.17 adapter validation passes with fake backends
- L.18 prompt contract validated with real LLM in isolated test environment
- L.19 safety filter coverage confirmed against real LLM outputs

---

## 10. Explicit Non-Goals

- No real LLM API integration (OpenAI, Anthropic, local model)
- No network calls
- No renderer/layout changes
- No CCI config/severity changes
- No rule promotion
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- No generated PDFs or logs committed
- No reading or modifying `docs/BOOTSTRAP.md`
- No modifying `docs/HERMES_INSTRUCTIONS.md`

---

## Recommended Next Phase

`Phase L.17  Fake-Backend LLM Mediator Adapter Prototype`

Goal: Implement the `LLMBuilderMediatorAdapter` class with a `MockBackend` that returns deterministic JSON. Validate the adapter's strict output validation and safety filters against fake backend outputs. Prove that all proposed updates still go through `BuilderSession.ingest_user_message()`.

---

## Risks

| Risk | Mitigation |
|---|---|
| Real LLM ignores JSON schema in prompt | Strict adapter validation catches malformed output; degrade safely |
| Real LLM hallucinates official data | Safety filter marks invented data for confirmation; never auto-apply |
| Real LLM tries to suppress warnings | Silent-warning filter catches and degrades to unknown |
| Real LLM emits low-confidence output | Confidence filter degrades to unknown + asks question |
| Adapter adds too much latency | Backend is injected and swappable; mock backend is instant |
| Vendor lock-in | Adapter knows only `Callable[[str], str]`; no hardcoded vendor imports |
