# Phase L.14 LLM Builder Mediator Contract Design

**Date:** 2026-06-13  
**Commit:** `2b9527e`  
**Phase:** L.14  
**Purpose:** Design the concrete LLM mediator interface and contract between natural-language user input and the deterministic `BuilderSession` backend.

---

## 1. Mediator Role

The LLM mediator is a translation and proposal layer. It does not own final state.

| Responsibility | Description |
|----------------|-------------|
| **Translate NL** | Convert user natural language into proposed structured field updates |
| **Ask questions** | Generate natural clarifying questions for missing required fields |
| **Explain findings** | Interpret validation warnings/errors in plain English |
| **Propose revisions** | Suggest corrections when validation blocks progress |
| **Never own state** | All updates pass through `BuilderSession`; LLM may not bypass validation |

---

## 2. Input Schema

```python
{
    "session_id": str,                    # BuilderSession identifier
    "current_step": str,                  # e.g., "intake", "routing", "body", "signature"
    "payload_snapshot": dict,             # Current payload dict from BuilderSession
    "missing_required_fields": list[str], # Field paths still required before finalize
    "missing_recommended_fields": list[str], # Optional fields the builder recommends
    "validation_summary": dict,           # Full validation_summary from BuilderSession
    "warning_summary": list[dict],        # Pending warning findings
    "error_summary": list[dict],          # Pending error findings (blocks finalize)
    "user_message": str,                  # Raw NL input from user
    "conversation_history_summary": str,  # Condensed prior turns for LLM context
    "available_commands": list[str],      # ["/status", "/warnings", "/finalize", "/render", ...]
    "safety_flags": {                     # Explicit guardrails for this turn
        "block_invented_official_data": bool,
        "require_confirmation_for_inferred": bool,
        "require_confirmation_before_finalize": bool,
        "require_confirmation_before_render": bool,
    },
}
```

---

## 3. Output Schema

```python
{
    "intent": str,                        # See Allowed Intents below
    "proposed_payload_update": dict,      # Nested dict of fields to update (may be empty)
    "proposed_key_value_lines": list[str], # Equivalent key-value strings for BuilderSession
    "next_question": {                    # If asking for missing data
        "field_path": str,
        "prompt_text": str,
        "bucket": "required" | "recommended",
    } | None,
    "explanation": str,                   # Plain-English explanation of what the mediator understood
    "requires_user_confirmation": bool,   # True if user must explicitly approve before applying
    "warnings_to_surface": list[dict],    # Warnings the user should see now
    "blocked_reason": str | None,         # Why this turn cannot proceed (e.g., missing field, error)
    "confidence": float,                  # 0.0–1.0; mediator confidence in intent detection
    "safety_notes": list[str],            # Any safety concerns raised (e.g., "Inferred SSIC 5216")
}
```

---

## 4. Allowed Intents

| Intent | Description | Typical User Message |
|--------|-------------|----------------------|
| `start_letter` | Begin a new letter session | "I need to write a letter" |
| `provide_field` | User supplies one or more field values | "From is Commander Smith" |
| `revise_field` | User corrects a previously provided field | "Change the subject to TRAINING" |
| `accept_warnings` | User explicitly accepts pending warnings | "Accept the warnings and continue" |
| `request_warning_explanation` | User asks what a warning means | "Why is SUBJ-002 flagged?" |
| `finalize` | User wants to finalize the payload | "Finalize the letter" |
| `render_pdf` | User wants to render a PDF | "Generate the PDF" |
| `unknown` | Intent could not be determined | Ambiguous or off-topic input |

---

## 5. Confirmation Policy

| Condition | Confirmation Required? | Reason |
|-----------|------------------------|--------|
| Direct user-provided simple field (`from`, `to`, `body`) | **No** | User stated the value explicitly |
| Inferred value (e.g., LLM guessed SSIC from context) | **Yes** | Must not silently assume accuracy |
| Official data (SSIC, command name, routing path) | **Yes** | LLM may not invent official data |
| Warning acceptance | **Yes** | Requires explicit `/accept-warnings` equivalent |
| Finalization | **Yes** | Irreversible; must confirm payload is correct |
| PDF rendering | **Yes** | Produces artifact; must confirm before render |
| Signature update | **No** if user-provided; **Yes** if inferred | Same as other fields |

---

## 6. Field Update Rules

1. **Direct facts → proposed updates.** If the user says *"The subject is TRAINING PLAN"*, the mediator proposes `{"subj": "TRAINING PLAN"}`.

2. **Inferred values → marked for confirmation.** If the user says *"It's about training"* and the mediator infers `ssic: 5216`, the update must set `requires_user_confirmation: true` and add a `safety_note`.

3. **Official data → never invented.** The mediator may suggest common values (e.g., *"5216 is often used for training"*) but must present them as proposals, not facts.

4. **Ambiguous references → trigger `next_question`.** If the user says *"Send it to CNO"* without a `to` field, the mediator may propose `{"to": "CNO"}` or ask *"Do you mean Chief of Naval Operations?"*.

5. **Signature → structured fields only.** Proposed signature updates must use dotted keys:
   - `signature.name: J. Q. Sample`
   - `signature.role: Commanding Officer`
   - `signature.title: Commanding Officer`

---

## 7. Warning/Error Explanation Rules

| Rule | Description |
|------|-------------|
| Explain, don't suppress | The LLM may explain what `CCI-CH7-SUBJ-002` means; it may not remove the finding |
| Recommend revisions | The LLM may suggest: *"You could revise the subject to remove the period."* |
| Never downgrade | Warning → advisory or error → warning is prohibited |
| Errors block | If errors exist, finalization is blocked regardless of LLM explanation |
| Warnings require action | User must accept or revise; LLM may not auto-accept |

---

## 8. BuilderSession Handoff

Every proposed update must pass through `BuilderSession`:

```python
# Mediator generates proposed_key_value_lines
for line in mediator_output["proposed_key_value_lines"]:
    result = builder.ingest_user_message(line)
    # BuilderSession validates, normalizes, updates payload

# Mediator checks validation_summary
summary = builder.validation_summary()
# Mediator surfaces warnings/errors to user
# User decides: revise, accept warnings, or continue

# Finalize only when BuilderSession allows
if summary["finalize_allowed"]:
    finalize_result = builder.finalize(accept_warnings=user_accepted)
```

**Invariant:** `BuilderSession` is the only component that may mutate `payload`, run validation, or allow finalize/render.

---

## 9. Failure Modes

| Failure | Handling |
|---------|----------|
| **Malformed mediator JSON** | Fallback to `unknown` intent; ask user to rephrase |
| **Unsupported intent** | Return `unknown`; present available commands |
| **Ambiguous user instruction** | Set `requires_user_confirmation: true`; ask clarifying question |
| **Prohibited official-data invention** | Block update; set `blocked_reason`; surface safety note |
| **Validation error** | Surface error via `warnings_to_surface`; block finalize |
| **Pending warnings** | Require explicit `accept_warnings` intent; do not auto-accept |
| **Renderer failure** | Report `render_pdf` failure cleanly; preserve payload |

---

## 10. Test Strategy for Phase L.15

Phase L.15 will use **mock mediator outputs** — no real LLM required.

| Test Type | Approach |
|-----------|----------|
| **Contract validation** | Feed mock `MediatorOutput` dicts into a contract validator; assert schema compliance |
| **Deterministic updates** | Scripted NL-style messages → expected `proposed_key_value_lines` |
| **Confirmation gating** | Inferred values must set `requires_user_confirmation: true` |
| **Safety boundary tests** | Mock output with invented SSIC → must be blocked or flagged |
| **BuilderSession handoff** | Mock output piped through `BuilderSession.ingest_user_message()` → assert payload state |
| **Warning surfacing** | Mock output with warnings → assert user sees plain-English explanation |

All tests will run against the **existing** `BuilderSession` with no LLM API calls.

---

## 11. Explicit Non-Goals

- No LLM API integration in L.14.
- No NL parser implementation in L.14.
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

## Recommended Next Phase

`Phase L.15  Mock LLM Mediator Contract Prototype`

Goal: Build a mock mediator that produces deterministic `MediatorOutput` dicts according to the L.14 contract. Wire it to `BuilderSession` for end-to-end handoff testing. No real LLM required.
