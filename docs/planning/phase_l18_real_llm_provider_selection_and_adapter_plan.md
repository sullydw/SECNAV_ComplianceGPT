# Phase L.18 — Real LLM Provider Selection and Adapter Plan

## 1. Purpose

Phase L.18 selects the real LLM provider strategy for the conversational builder mediator track and defines how future live provider integration must remain bounded by the existing L.14/L.15/L.17 mediator contract.

This phase is planning and design only. It does not add real LLM API calls, network calls, model dependencies, API keys, renderer changes, validator changes, catalog changes, CCI configuration changes, or Phase F/G command-layer changes.

The strategic product path remains:

```text
Natural-language user message
  -> LLM mediator or mock mediator
  -> proposed structured updates
  -> BuilderSession
  -> CCI validation and warning review
  -> finalize
  -> PDF renderer
```

BuilderSession remains the source of truth. The LLM provider is only a translator and proposal engine.

## 2. Current Baseline

Current repo baseline before this document:

- Latest completed phase: L.17 Fake-Backend LLM Mediator Adapter Prototype.
- Adapter module: `src/llm_builder_mediator.py`.
- Adapter behavior: validates model-like JSON, applies safety filters, and safely degrades malformed or unsafe output to `intent="unknown"` with a clarifying question.
- Fake backend: deterministic and regression-safe.
- Live LLM integration: not yet implemented.
- BuilderSession handoff invariant: all proposed updates must pass through `builder.ingest_user_message()`.
- Error promotion: unauthorized.

## 3. Provider Options

### 3.1 OpenAI API

OpenAI is the likely best first live-provider option for quality, instruction following, structured JSON output, and future production reliability.

Expected strengths:

- Strong natural-language understanding.
- Better structured-output discipline than small local models.
- Better warning explanation and rewrite assistance.
- Better ability to handle incomplete or messy user input.

Expected risks:

- Requires network access.
- Requires an API key.
- Adds cost and provider availability concerns.
- Must never be required for offline regression tests.
- Must be isolated behind the adapter contract.

OpenAI integration should use official OpenAI client/API paths only when implemented in a future phase. API keys must come from environment variables only and must never be committed.

### 3.2 Local Ollama Model

Ollama or another local model provider is useful for offline experimentation and privacy-focused workflows.

Expected strengths:

- Runs locally.
- Avoids live network dependency after model installation.
- Useful for development experimentation.
- Can support users who prefer local-only workflows.

Expected risks:

- JSON reliability may be weaker.
- Smaller local models may hallucinate fields or ignore strict schema instructions.
- Prompt adherence may vary by model.
- Additional retry/repair logic may be required.
- Should remain optional and non-blocking.

Ollama should not become a hard dependency. If added later, it should be another backend callable behind the same adapter contract.

### 3.3 Future Swappable Provider

The adapter should stay provider-agnostic so future backends can be added without modifying BuilderSession.

Potential future providers:

- OpenAI-compatible local servers.
- Enterprise/private model gateways.
- Fine-tuned local models.
- Other hosted model providers.

The adapter should not encode vendor-specific assumptions into BuilderSession or the renderer.

### 3.4 No-Provider / Mock-Only Mode

Mock-only mode must remain the safe default for tests and CI-style regression.

Requirements:

- No API key required.
- No network required.
- No live provider required.
- Regression tests use deterministic fake backend output.
- Live-provider smoke tests are optional/manual only.

## 4. Recommended Strategy

Use a provider-agnostic backend interface with fake/mock backend as the default.

Recommended path:

1. Keep `LLMBuilderMediatorAdapter` as the only component that talks to model-like output.
2. Keep backend injection as `Callable[[str], str]`.
3. Keep fake backend as default for tests.
4. Add provider configuration plumbing in a future phase without making live providers mandatory.
5. Add OpenAI and/or Ollama backends behind optional configuration.
6. Fail closed to safe `unknown` output if provider configuration is missing, provider call fails, output is invalid JSON, or safety filters reject the output.

This gives the project live-LLM capability later without weakening deterministic builder behavior.

## 5. Provider Boundary Contract

A live backend must obey this narrow interface:

```python
backend(prompt: str) -> str
```

The backend receives a prompt string and returns raw text.

The adapter then:

1. Parses the raw text as JSON.
2. Validates the JSON against the MediatorOutput schema.
3. Rejects malformed or unsafe output.
4. Enforces safety rules.
5. Returns a valid MediatorOutput dict.

The backend must not:

- Mutate BuilderSession.
- Call `builder.ingest_user_message()` directly.
- Run validation.
- Finalize payloads.
- Render PDFs.
- Modify CCI configuration or severity.
- Modify renderer layout.
- Write files.

## 6. Configuration Plan

Future live-provider configuration should be environment-variable driven.

Proposed environment variables:

```text
SECNAV_LLM_PROVIDER=mock|openai|ollama
SECNAV_LLM_MODEL=<model name>
SECNAV_LLM_TIMEOUT_SECONDS=30
SECNAV_LLM_MAX_TOKENS=1200
SECNAV_LLM_TEMPERATURE=0
OPENAI_API_KEY=<not committed>
OLLAMA_BASE_URL=http://localhost:11434
```

Safe defaults:

```text
SECNAV_LLM_PROVIDER=mock
SECNAV_LLM_TEMPERATURE=0
```

Rules:

- No API keys committed.
- No secrets in docs except placeholder variable names.
- If provider is unset, use mock mode.
- If provider is configured but unavailable, degrade safely.
- Live-provider tests must be optional/manual.
- Regression suites must not require external services.

## 7. OpenAI Option

Future OpenAI backend should:

- Use official OpenAI API/client only.
- Read API key from `OPENAI_API_KEY` only.
- Use a model selected through `SECNAV_LLM_MODEL`.
- Request JSON-only output following the MediatorOutput contract.
- Set low temperature for deterministic behavior.
- Apply adapter validation after every response.
- Treat refusals, non-JSON, partial JSON, or unsafe output as failure modes that degrade safely.

OpenAI is recommended as the first live smoke-test provider because it is more likely to follow strict JSON instructions and preserve safety constraints.

## 8. Ollama / Local Provider Option

Future Ollama backend should:

- Use `OLLAMA_BASE_URL` if configured.
- Use a model selected through `SECNAV_LLM_MODEL`.
- Remain optional.
- Never be required for regression tests.
- Use the same prompt contract and adapter validation.
- Expect stricter retry/repair behavior may be needed because local models may produce looser JSON.

Ollama is useful for local experimentation but should not be the first required provider path.

## 9. Safety Requirements

The provider layer must preserve all L.13/L.14/L.17 safety boundaries.

The LLM may not:

1. Bypass validation.
2. Modify CCI severity or configuration.
3. Invent official data.
4. Silently ignore warnings.
5. Control renderer layout.
6. Own final state.
7. Declare finalization or render success directly.

The adapter must reject or degrade outputs that attempt to modify:

- CCI severity.
- CCI configuration.
- Renderer directives.
- Layout overrides.
- Validation results.
- Finalization status.
- Render success status.
- Hidden/system control fields.

Official data policy:

- If the user provides a command, SSIC, routing entry, reference, or signature title directly, it may be proposed as an update.
- If the model infers or guesses official-looking data, it must require confirmation or be rejected.
- If the user asks the model to choose an SSIC or routing path without source data, the mediator should ask a clarifying question instead of inventing.

Warning policy:

- Warnings must be surfaced.
- Warning acceptance requires user confirmation.
- The model may explain or recommend revisions.
- The model may not downgrade, suppress, or mark warnings as accepted by itself.

Finalize/render policy:

- Finalize requires confirmation.
- Render requires confirmation.
- The model may propose the intent but cannot execute it directly.
- BuilderSession remains the authority on whether finalize/render is allowed.

## 10. Failure Handling

The provider adapter must fail closed.

Failure modes:

1. No API key.
2. Provider not configured.
3. Network failure.
4. Timeout.
5. Invalid JSON.
6. Missing required output keys.
7. Unsupported intent.
8. Unsafe field update.
9. Low confidence.
10. Refusal or non-answer.
11. Conflicting user instructions.
12. Pending warnings.
13. Provider unavailable.

Safe degradation behavior:

```json
{
  "intent": "unknown",
  "proposed_payload_update": {},
  "proposed_key_value_lines": [],
  "next_question": "I could not safely interpret that. Please provide the next field directly or clarify your request.",
  "explanation": "The model output could not be safely applied.",
  "requires_user_confirmation": false,
  "warnings_to_surface": [],
  "blocked_reason": "provider_output_invalid_or_unsafe",
  "confidence": 0.0,
  "safety_notes": ["degraded safely"]
}
```

## 11. Test Strategy for L.19

L.19 should implement provider interface and configuration plumbing without requiring live model calls.

Required test categories:

1. Default provider is mock.
2. Missing provider configuration falls back safely.
3. No API key produces safe degradation.
4. Fake backend valid JSON passes validation.
5. Fake backend invalid JSON degrades safely.
6. Fake backend tries CCI severity change and is rejected.
7. Fake backend tries renderer/layout directive and is rejected.
8. Fake backend hallucinates SSIC and is rejected or confirmation-forced.
9. Fake backend omits warnings and is rejected or corrected by adapter surface behavior.
10. Fake backend requests finalize/render and confirmation is forced.
11. Adapter output still passes through BuilderSession.
12. No network calls are required in regression.

Optional/manual live-provider smoke tests may be added later, but must not gate normal regression.

## 12. Recommendation

Recommended provider path:

1. Keep fake/mock backend as default.
2. Implement provider configuration plumbing in L.19.
3. Add backend interface wrappers for `mock`, `openai`, and `ollama`, but keep live providers optional.
4. Do not require OpenAI or Ollama for regression tests.
5. Use OpenAI as the recommended first manual live-provider smoke test because strict JSON reliability is likely better.
6. Keep Ollama as optional local/offline experimentation.
7. Delay production live-provider reliance until adapter validation and optional smoke tests are stable.

Recommended next phase:

**Phase L.19 — LLM Provider Interface and Configuration Plumbing**

L.19 should add configuration and provider selection plumbing while preserving mock-only regression safety. It should not make real API calls mandatory.

## 13. Explicit Non-Goals

This phase does not:

- Add real LLM API integration.
- Add network calls.
- Add API keys.
- Commit secrets.
- Modify renderer/layout.
- Modify CCI config/severity.
- Promote any rule.
- Modify validators/catalogs.
- Modify Phase F/G command layer.
- Modify intake policy/questions JSON.
- Commit generated PDFs/logs.
- Read or modify `docs/BOOTSTRAP.md`.
- Modify `docs/HERMES_INSTRUCTIONS.md`.

## 14. Decision

Phase L.18 chooses a provider-agnostic live-LLM strategy with fake/mock backend as the default and OpenAI as the recommended first optional manual smoke-test provider.

The real provider must be injected behind the existing adapter boundary and must preserve the MediatorOutput contract. The live model is never the source of truth. BuilderSession remains the authority for state, validation, finalization, and rendering.
