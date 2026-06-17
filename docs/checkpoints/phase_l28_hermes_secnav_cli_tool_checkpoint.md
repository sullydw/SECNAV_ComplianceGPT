# Phase L.28 Checkpoint — Hermes SECNAV CLI Tool Integration

## Objective
Create a thin deterministic CLI bridge so Hermes can drive SECNAV_ComplianceGPT without a web UI.

## Root Cause
After retiring the Streamlit UI path (Phase L.27A), there was no entry point for Hermes to:
- start a BuilderSession
- ingest natural language and extract fields
- validate, finalize, and render PDF
- persist session state across multi-turn interaction

The existing `src/conversational_builder.py` interactive CLI is human-oriented (stdin prompts) and does not emit machine-readable JSON.

## Solution
Added `tools/hermes_secnav_tool.py` — a subcommand-driven CLI wrapper around `BuilderSession` + `MockLLMBuilderMediator`.

### Commands
- `start` — creates a new session, persists JSON state
- `ingest --session <id> --text "..." [--no-apply]` — runs mock mediator, proposes kv, auto-applies by default
- `apply --session <id> --kv "key: value lines"` — feeds kv into BuilderSession.ingest_user_message()
- `status --session <id>` — returns payload + validation + next question
- `validate --session <id>` — returns validation_summary + findings
- `finalize --session <id> [--accept-warnings]` — finalizes draft
- `render --session <id> --out <path>` — finalizes, writes JSON, invokes pdf_v6_render.py
- `list` — lists persisted sessions
- `reset --session <id>` — deletes session state

### Design Decisions
- `MockLLMBuilderMediator` only (offline, deterministic, no LLM API)
- Session state persisted to `~/.hermes/secnav_sessions/<id>.json` as JSON (not pickle)
- All stdout is machine-readable JSON; stderr reserved for debug/human messages
- PDF rendered via subprocess call to `src/pdf_v6_render.py` using the venv Python
- User answers stored alongside payload so fields remain editable on reload

## Files Changed
- `tools/hermes_secnav_tool.py` (new)
- `tools/run_phase_l28_hermes_secnav_cli_tool_regression.py` (new)

## Files Not Changed
- No renderer/layout module touched
- No CCI config/severity module touched
- `docs/BOOTSTRAP.md` untouched
- `docs/HERMES_INSTRUCTIONS.md` untouched
- `src/llm_provider_config.py` and `src/llm_builder_mediator.py` reused, not modified

## Regression Results
- L.28: 25/25 PASS
- L.27A: 10/10 PASS
- H.4: 18/18 PASS
- H.13: 27/27 PASS
- K.3: 11/11 PASS
- H.24: 36/36 PASS

## Commit Hash
`TODO` — to be filled after commit

## Manual Retest Steps
1. Ensure venv is present:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py start
   ```
2. Ingest the sample request:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py ingest --session <id> --text "I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN"
   ```
3. Apply remaining required fields (date, signature, uppercase subject) if needed.
4. Validate:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py validate --session <id>
   ```
5. Finalize:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py finalize --session <id>
   ```
6. Render PDF:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py render --session <id> --out output\test.pdf
   ```
7. Clean up:
   ```
   venv\Scripts\python tools\hermes_secnav_tool.py reset --session <id>
   ```

## Recommended Next Phase
Phase L.29 — Ollama-backed LLM ingest for richer NL extraction. Swap `MockLLMBuilderMediator` for `LLMBuilderMediatorAdapter` with an Ollama backend when available, keeping the same CLI contract and the same `BuilderSession` source of truth.
