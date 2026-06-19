# Hermes Agent Integration Loop

**Phase:** L.29N  
**Purpose:** Define how the Hermes conversational agent should use `detect-facts` after ingest to drive the builder loop.  
**Baseline:** Commit `2584eaf` — `Tools: Wire unresolved fact detector into CLI`

---

## 1. Overview

The Hermes agent should no longer guess what is missing from a correspondence request. It should ask the SECNAV CLI (`hermes_secnav_tool.py`) via the `detect-facts` command, then use the returned `UNRESOLVED_FACTS_V1` to decide what to ask the user, what to look up, or what to infer safely.

This document is a design specification. No source code changes are made in this phase.

---

## 2. Hermes Builder Loop

```
[User request]
   |
   v
start ............................................... creates BuilderSession
   |
   v
ingest ............................................. sends user text + KV lines to BuilderSession
   |
   v
detect-facts ....................................... polls CLI with current payload + user text
   |
   v
choose next action ................................. reads unresolved_facts.summary
   |
   +-- blocking > 0 ................................. ask highest-priority blocking question
   |
   +-- blocking == 0, recommended exists ............ ask, skip, or suggest lookup based on recommended_action
   |
   +-- blocking == 0, no recommended ................ validate → finalize → render (with gate)
   |
   v
ask user / suggest lookup / present candidate
   |
   v
user answer / lookup result / candidate decision
   |
   v
ingest answer ...................................... or apply-resolved --confirm
   |
   v
rerun detect-facts ................................. loop until blocking == 0
   |
   v
render gate ........................................ validate, finalize, render only when ready
```

---

## 3. Step Definitions

### 3.1 start

Hermes calls:

```
python tools/hermes_secnav_tool.py start --id <session_id>
```

Creates a `BuilderSession` with `doc_type` default or inferred from user message. Session persisted to `~/.hermes/secnav_sessions/<id>.json`.

### 3.2 ingest

Hermes calls:

```
python tools/hermes_secnav_tool.py ingest --session <id> --text "..."
```

The CLI uses `MockLLMBuilderMediator` to convert natural language to key-value lines, then feeds them into `BuilderSession.ingest_user_message()`. Returns the updated payload.

### 3.3 detect-facts

Hermes calls immediately after ingest:

```
python tools/hermes_secnav_tool.py detect-facts --session <id> [--text "..."] [--doc-type ...]
```

Returns `UNRESOLVED_FACTS_V1` JSON with:

- `version`: `"UNRESOLVED_FACTS_V1"`
- `doc_type`: resolved doc_type
- `rule_profile`: `"RULE_FACT_MAP_V1"`
- `facts[]`: list of unresolved fact records
- `summary`: `{blocking: N, recommended: M, optional: P}`

### 3.4 choose next action

Hermes reads `unresolved_facts.summary` and the individual `facts[]` array.

**Decision table:**

| Condition | Next Action |
|-----------|-------------|
| `blocking > 0` | Pick highest-priority blocking fact; ask user the `question` field |
| `blocking == 0` and `recommended > 0` | Evaluate each recommended fact by `recommended_action`; may ask, suggest lookup, or skip |
| `blocking == 0` and `recommended == 0` and `optional > 0` | Skip optional facts unless user explicitly asks |
| All zero | Proceed to render gate |

### 3.5 ask user

When a fact requires user input:

- Use the `question` field from the unresolved fact record.
- Prefer the highest-priority blocking fact first.
- Ask one or two questions at a time. Do not dump a giant checklist.
- For cognitively heavy workflows (military correspondence), keep each question simple and specific.

### 3.6 apply answer through ingest/apply-resolved

When the user answers:

- If the answer is a direct field value, Hermes calls `ingest` with the KV line.
- If the answer resolves a candidate (e.g., user confirms a unit name found by lookup), Hermes calls `apply-resolved --confirm` or `candidate-confirm`.

### 3.7 rerun detect-facts

After every ingestion or application, Hermes must rerun `detect-facts` to get the updated unresolved fact summary. The loop continues until `blocking == 0`.

### 3.8 candidate-add for live lookup results

When `recommended_action == "live_lookup"` and the browser-agent finds source evidence:

1. Hermes packages the result as a `CANDIDATE_V1` record.
2. Hermes calls `candidate-add` with the candidate JSON.
3. The candidate is stored as `pending` in the session.
4. The payload is not modified.

### 3.9 candidate-confirm / candidate-reject

After presenting a candidate to the user:

- If user confirms: `candidate-confirm <candidate_id>` → value applied to payload.
- If user rejects: `candidate-reject <candidate_id>` → candidate marked rejected, payload unchanged.

### 3.10 validate / finalize / render

Only proceed when the render gate conditions are met (see Section 8).

---

## 4. Action Handling by recommended_action

Each unresolved fact record has a `recommended_action` field. Hermes must handle each as follows:

### 4.1 ask_user

- Ask the `question` from the unresolved fact.
- Prefer the highest-priority blocking fact.
- Do not answer it yourself. Wait for user response.
- Example: missing `from` field → "Who is this letter from?"

### 4.2 live_lookup

- Use browser-agent only when source-backed lookup is appropriate (official .mil sites, SECNAV manuals, etc.).
- Package the lookup result as a `CANDIDATE_V1` with `source_tier` and `source_url`.
- Store with `candidate-add`.
- Ask user to confirm the candidate.
- Do not auto-apply.
- Example: unknown unit identity → browser lookup → candidate "MCAS New River" with source URL.

### 4.3 candidate_low_confidence

- Present as an option only, not a command.
- Require explicit user confirmation.
- Do not auto-apply.
- Example: Hermes thinks the SSIC might be 5216 but is unsure → present as candidate with confidence note.

### 4.4 safe_infer

- Only apply if the inference is deterministic formatting and no operational fact is invented.
- Example: subject all-caps formatting may be safely normalized ("UPDATE POLICY" → "Update Policy").
- Still report what changed to the user.
- If there is any doubt, degrade to `ask_user`.

### 4.5 leave_blank

- Leave the field blank and continue if it is not blocking.
- Do not ask the user.
- Example: optional `copy_to` on a short memorandum.

### 4.6 refuse_to_infer

- Ask the user or explain why the value cannot be inferred.
- Do not guess.
- Example: user message is too vague to determine the recipient command.

---

## 5. Priority Order

When multiple unresolved facts exist, Hermes resolves them in this order:

1. **Blocking facts before recommended facts.**
   - A missing `from` line blocks progress; a subject formatting suggestion does not.

2. **Required doc_type fields before formatting polish.**
   - `from`, `to`, `date`, `subject` come before acronym warnings or terminal punctuation.

3. **User-provided operational facts before live lookup.**
   - If the user already stated the command name, do not look it up.

4. **Live lookup before low-confidence candidates.**
   - Prefer source-backed evidence over guessing.

5. **No render until blocking == 0.**
   - Finalize and render are gated behind zero blocking facts.

---

## 6. Question Selection Rules

### 6.1 Use the question field

When `unresolved_facts.facts[].question` is present, use it verbatim. Do not rephrase unless the user asks for clarification.

### 6.2 Prefer unlock-progress questions

If multiple blocking facts exist, prefer the one whose resolution unlocks the most downstream progress. Example: resolving `doc_type` unlocks all doc_type-specific field policies.

### 6.3 Avoid overwhelming the user

- Ask **one** question at a time for blocking facts.
- Ask **at most two** questions at a time for recommended facts.
- Never present a giant checklist in the chat.

### 6.4 Keep questions simple

Military correspondence is already cognitively demanding. Each question should be:

- Short (one sentence)
- Specific (asks for one piece of information)
- Actionable (user knows how to answer)

---

## 7. Candidate Rules

### 7.1 Session-specific only

Candidates are tied to the current `session_id`. They must never be written to a static database, shared across sessions, or promoted to global knowledge.

### 7.2 Source evidence required

When `recommended_action == "live_lookup"`, the candidate must include:

- `source_tier`: official_live, official_archived, secondary_credible, user_provided, or unresolved
- `source_url`: actual URL where evidence was found
- `source_snippet`: brief visible text that supports the claim
- `lookup_timestamp`: ISO-8601 timestamp of retrieval

### 7.3 Pending until confirmed

Candidates remain in `pending` status until the user explicitly confirms. Confirmed candidates apply through `candidate-confirm` or `apply-resolved --confirm`.

### 7.4 Rejected candidates remain in history

Rejected candidates are marked `rejected` in session history but do not affect the payload. They may be referenced in future conversation for context.

---

## 8. Render Gate

Hermes may call `validate`, `finalize`, or `render` only when ALL of the following are true:

1. `detect-facts.summary.blocking == 0`
2. `validation_summary.errors == 0` (or user has explicitly accepted warnings)
3. All required candidate confirmations are resolved (confirmed or explicitly skipped)
4. User has either approved the final draft or explicitly requested render

**Gate enforcement:**

- If `blocking > 0`: refuse render, ask the highest-priority blocking question.
- If `errors > 0` and not accepted: refuse render, surface error.
- If pending candidates exist: refuse render, ask user to confirm or skip each candidate.

---

## 9. Example Workflows

### Example A: Standard Letter with Missing Subject / Signature / Date

**User:** "Draft a letter from HQ BN to MCAS New River about the new policy."

**Step 1: start + ingest**
- Hermes calls `start` with inferred `doc_type: standard_letter`.
- Hermes calls `ingest` with user text.

**Step 2: detect-facts**
- Returns blocking facts:
  - `from` — missing (HQ BN mentioned but not structured)
  - `date` — missing
  - `subject` — missing
  - `signature` — missing
- Returns recommended facts:
  - `ssic` — recommended (user did not provide)

**Step 3: first question**
- Hermes asks: "What is the date of this letter? (e.g., 19 June 2026)"
- (date is often easiest for the user to provide first)

**Step 4: next actions**
- User provides date → ingest → detect-facts → blocking count drops.
- Next ask: "Who should sign this letter? Provide name, role, and title."
- Next ask: "What is the subject line?"
- Next ask: "What is the From line? (e.g., Commanding Officer, Headquarters Battalion)"

**Step 5: SSIC**
- After blocking facts resolved, Hermes notes `ssic` is recommended.
- `recommended_action` for SSIC is `live_lookup` or `ask_user`.
- Hermes asks: "Do you know the SSIC for this topic? If not, I can try to look it up."

**Step 6: render gate**
- After all blocking == 0 and user approves draft, Hermes calls `finalize` then `render`.

---

### Example B: Memorandum for Record (from/to/signature not blocking)

**User:** "Write a MFR about the training event on 15 June."

**Step 1: start + ingest**
- Hermes calls `start` with `doc_type: memorandum_for_record`.
- Hermes calls `ingest` with user text.

**Step 2: detect-facts**
- MFR field policy may mark `from` and `to` as recommended rather than blocking.
- Blocking facts:
  - `subject` — missing
  - `body` — missing
- Recommended facts:
  - `from` — recommended
  - `signature` — recommended

**Step 3: first question**
- Hermes asks: "What is the subject of this MFR?"

**Step 4: next actions**
- User provides subject → ingest → detect-facts.
- Next ask: "Please provide the body text of the MFR."
- After blocking == 0, Hermes may ask: "Who is this MFR from?" (recommended, not blocking)

**Step 5: render gate**
- MFR may render with blocking == 0 even if `from` is blank, depending on doc_type policy.
- Hermes still asks user for confirmation before render.

---

### Example C: Endorsement Requiring basic_letter_id and endorsement_ordinal

**User:** "Draft an endorsement to the letter from last month."

**Step 1: start + ingest**
- Hermes calls `start` with `doc_type: endorsement`.
- Hermes calls `ingest` with user text.

**Step 2: detect-facts**
- Endorsement policy marks `basic_letter_id` and `endorsement_ordinal` as blocking.
- Blocking facts:
  - `basic_letter_id` — missing
  - `endorsement_ordinal` — missing
  - `from` — missing

**Step 3: first question**
- Hermes asks: "What is the Basic Letter ID of the letter being endorsed? (e.g., Ser HQBN 001/26)"

**Step 4: next actions**
- User provides basic letter ID → ingest → detect-facts.
- Next ask: "What is the endorsement ordinal? (e.g., First Endorsement)"
- Next ask: "Who is this endorsement from?"

**Step 5: render gate**
- Endorsement has strict blocking policy. All three must be resolved before render.
- Hermes validates, asks user to confirm, then renders.

---

## 10. Error Handling and Degradation

### 10.1 detect-facts fails

If `detect-facts` returns `success: false`:

- Log the error (do not show raw traceback to user).
- Degrade to asking the user directly for required fields.
- Fall back to the L.28 behavior (Hermes asks based on static knowledge) only as last resort.

### 10.2 Empty facts but validation errors

If `detect-facts` returns `blocking == 0` but `validation_summary.errors > 0`:

- This is a detector/validator mismatch.
- Surface the validation errors to the user.
- Do not proceed to render.
- Log the mismatch for future detector tuning.

### 10.3 User refuses to answer

If the user refuses to provide a blocking field:

- Explain why the field is required for the selected doc_type.
- Offer to change doc_type if appropriate.
- If still refused, refuse to render and explain the gate.

---

## 11. Safety Boundaries

Hermes must never:

1. **Guess official data.** No invented SSICs, unit names, or routing codes.
2. **Auto-apply candidates.** Every candidate requires user confirmation.
3. **Bypass validation.** No render until errors/warnings are handled.
4. **Modify CCI config/severity.** Detector output is read-only.
5. **Invent renderer directives.** No layout or format commands injected.
6. **Store candidates globally.** All candidates are session-scoped.
7. **Dump giant checklists.** One or two questions at a time.

---

## 12. Files Changed in This Phase

| File | Action |
|------|--------|
| `docs/hermes_agent_integration_loop.md` | **Created** (this file) |
| `docs/checkpoints/phase_l29n_hermes_agent_integration_loop_checkpoint.md` | **Created** |
| `docs/PROJECT_STATUS.md` | **Modified** |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | **Modified** |

**No source code, renderer, validator, CCI config, detector, or candidate schema changes.**
