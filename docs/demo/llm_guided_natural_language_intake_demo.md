# LLM-Guided Natural-Language Intake Demo

This document walks through a conversational, natural-language-style builder session using the mock mediator (deterministic, no real LLM/API calls).

---

## Goal

Show how a user can create a SECNAV-compliant standard letter by speaking naturally, with the system translating each message into structured fields.

---

## Prerequisites

- Python environment with project dependencies
- ReportLab installed (optional, for PDF render step)
- No API keys or network access required

---

## Demo Script

### 1. Start the session

```
User: I need to write a standard letter.
System: Started session l21_nl_demo. Current step: intake.
```

### 2. Provide fields conversationally

| Step | User Says | System Detects | Applied As |
|------|-----------|--------------|------------|
| 1 | `from Commanding Officer, Example Command` | from field | `from: Commanding Officer, Example Command` |
| 2 | `to Commander, Example Group` | to field | `to: Commander, Example Group` |
| 3 | `subject Training Plan` | subject field | `subj: Training Plan` |
| 4 | `ssic 5216` | SSIC code | `ssic: 5216` |
| 5 | `body This letter provides the proposed training plan.` | body field | `body: This letter provides the proposed training plan.` |
| 6 | `signed by J. Q. Sample` | signature name | `signature.name: j. q. sample` |
| 7 | `window envelope false` | window envelope | `window_envelope: false` |

### 3. View validation results

```
Total findings: 2
Errors: 1
Advisories: 1
Pending decisions: 0

[ADVISORY] CCI-CH7-SUBJ-005: Please verify content follows SECNAV conventions.
[ERROR]    CCI-CH7-SUBJ-001: Subject not all caps for standard_letter.
```

### 4. Accept warnings

```
User: Accept the warnings.
System: Warnings accepted. Finalize allowed.
```

### 5. Finalize

```
User: Finalize.
System: Finalized successfully. Draft/Final status: draft.
```

### 6. Render PDF

```
System: PDF rendered (1665 bytes).
System: Generated PDF cleaned up.
```

---

## How It Works

1. **MediatorInput** is built from current BuilderSession state (payload, missing fields, validation summary)
2. **MockLLMBuilderMediator** parses the user message with regex patterns
3. **MediatorOutput** contains `proposed_key_value_lines` (never direct payload mutation)
4. **BuilderSession.ingest_user_message()** applies KV lines through the normal intake pipeline
5. **Adapter (LLMBuilderMediatorAdapter)** validates mediator output in parallel as a safety net
6. **Validation** runs automatically after each ingestion
7. **Finalize** is blocked until warnings are explicitly accepted
8. **Render** creates PDF then immediately deletes it (demo only)

---

## Safety Boundaries

- No real LLM API calls (mock mediator only)
- No network calls
- No renderer/layout changes
- No CCI config/severity changes
- No unsafe keys in payload
- All updates through `ingest_user_message()`

---

## Running the Demo

```bash
python tools/run_phase_l21_llm_guided_natural_language_intake_demo.py
```

Expected: 17/17 checks PASS, exit 0.
