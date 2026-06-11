# Phase L.3 — Conversational Builder Payload Schema and Question Flow

**Status:** Planning-only. No implementation code created.  
**Commit:** `[TBD]` — `Docs: Define conversational builder schema and question flow`  
**Latest Verified Baseline:** `2f2ba95` — Current HEAD  
**Active Warning Pilots:** `CCI-ROUTE-010 = warning`, `CCI-ROUTE-011 = warning`, `CCI-CH7-SUBJ-002 = warning`  
**Global Default:** `advisory`  
**Error Promotion:** Unauthorized  
**Regression Gate:** 37 suites PASS at `2f2ba95`

---

## 1. BuilderSession State Model

A `BuilderSession` is a thin, in-memory state machine above `IntakeOrchestrator`. It holds everything needed to conduct a multi-turn conversation that results in a renderer-ready payload.

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Unique identifier for this builder session. Not persisted to disk in L.3–L.6. |
| `current_step` | `str` | One of: `intake`, `routing`, `body`, `refs_encls`, `signature`, `validation`, `finalize`. |
| `accumulated_payload` | `dict` | Merged payload built progressively. Source of truth for renderer input. |
| `missing_required` | `list[str]` | Required fields still absent, computed by orchestrator. |
| `missing_recommended` | `list[str]` | Recommended fields still absent. |
| `missing_optional` | `list[str]` | Optional fields still absent. |
| `warnings` | `list[dict]` | Active CCI warnings with user decisions: `accepted`, `revised`, `ignored`. |
| `user_decisions` | `dict` | Explicit user choices: e.g., `skip_signature: true`, `window_envelope: true`. |
| `draft_final_status` | `str` | `draft` or `final`. Draft allows empty signature; final requires it unless explicitly skipped. |
| `history` | `list[dict]` | Ordered log of questions asked and answers received (for audit trail, not for training). |
| `orchestrator` | `IntakeOrchestrator` | Existing orchestrator instance; builder delegates to it. |
| `last_audit` | `dict \| None` | Most recent `CCI_AUDIT_V1` result. |

**State transition rules:**
- `intake` → `routing` once `doc_type`, `from`, `to`, `subj` are present (or `window_envelope` suppresses `from`).
- `routing` → `body` once routing fields are resolved.
- `body` → `refs_encls` once body is non-empty.
- `refs_encls` → `signature` once refs/encls are resolved (empty is valid).
- `signature` → `validation` once signature is provided or explicitly skipped.
- `validation` → `finalize` once user accepts or explicitly overrides all `warning`-level findings.
- Any step can backtrack to an earlier step if the user provides new information that changes requirements (e.g., switching `doc_type`).

---

## 2. Minimum Letter Payload Fields

The builder produces a payload that maps 1:1 to the existing v6 renderer schema. No new renderer-facing fields are introduced.

### Core Fields (present in every completed builder session)

| Field | Type | Notes |
|---|---|---|
| `doc_type` | `string` | Canonical value from `_DOC_TYPE_ALIASES` (e.g., `standard_letter`). |
| `ssic` | `int \| string \| null` | Optional; renderer accepts `null`. |
| `originator_code` | `string \| null` | Optional. |
| `date` | `string` | Military format: `01 May 2026`. |
| `unit_identity` | `object \| null` | Letterhead block; can be `null` for plain-paper memo. |
| `from` | `string \| null` | Activity head title. `null` when `window_envelope: true`. |
| `to` | `string \| list` | Primary addressee(s). |
| `via` | `list` | Empty list default. |
| `subj` | `string` | ALL CAPS for letters; no terminal punctuation per `SUBJ-002`. |
| `ref` | `list` | Empty list default. |
| `encl` | `list` | Empty list default. |
| `body` | `list[str]` | Numbered paragraphs as strings. |
| `signature` | `object \| null` | `{name, role, title, authority, activity_head_title, affects_pay_or_allowances}`. |
| `copy_to` | `list` | Empty list default. |
| `distribution` | `list \| null` | Only for multiple-address letters. |

### New Builder-Specific Metadata Fields (not passed to renderer)

| Field | Type | Description |
|---|---|---|
| `window_envelope` | `boolean` | Default `false`. When `true`, suppresses `from` requirement and `CCI-ROUTE-011`. |
| `draft_final_status` | `string` | `draft` or `final`. |
| `builder_version` | `string` | e.g., `L.3`. For traceability. |

---

## 3. Required versus Optional Fields

### Required for Standard Letter

| Field | Why Required | Can Default? |
|---|---|---|
| `doc_type` | Determines all downstream questions. | No — must ask user. |
| `to` | Every letter needs a primary addressee. | No — must ask user. |
| `from` | Every standard letter needs a sender (unless window envelope). | No — must ask user; can be suppressed by `window_envelope`. |
| `subj` | Every letter needs a subject. | No — must ask user. |
| `body` | Every letter needs content. | No — must ask user. |
| `date` | Every letter needs a date. | **Yes** — can default to current date with user confirmation. |
| `signature` | Every final letter needs a signature block. | No — must ask user; draft mode allows skip. |

### Recommended (asked, but user can skip)

| Field | Why Recommended | Affects Validation? |
|---|---|---|
| `ssic` | Standard practice; not strictly required by renderer. | No. |
| `originator_code` | Standard practice. | No. |
| `point_of_contact` | Good practice; inferred by context resolver if body contains contact keywords. | No. |

### Optional (asked only if user has not provided; always skippable)

| Field | Notes |
|---|---|
| `via` | Empty list is valid. |
| `copy_to` | Empty list is valid. |
| `ref` | Empty list is valid. |
| `encl` | Empty list is valid. |
| `distribution` | Only relevant for `multiple_address_letter`. |
| `window_envelope` | Default `false`. Builder asks once if `from` is missing. |
| `classification` | Optional marking; not required for unclassified letters. |

### Fields That Affect Validation

| Field | Affected CCI Rules |
|---|---|
| `subj` | `CCI-CH7-SUBJ-002` (terminal punctuation warning pilot) |
| `to`, `via` | `CCI-ROUTE-010` (office-code warning pilot) |
| `from` + `window_envelope` | `CCI-ROUTE-011` (From-line warning pilot) |
| `copy_to` | `CCI-ROUTE-007` (duplicate To/Via+Copy-to, advisory) |
| `ref`, `encl` | `CCI-REF-*`, `CCI-ENCL-*` |
| `body` | `CCI-ACR-*`, `CCI-PER-*`, `CCI-DTM-*`, `CCI-POC-*` |

---

## 4. Question Flow

The builder uses `IntakeOrchestrator.next_questions(limit=1)` in a loop. After each answer, it calls `apply_answers()`, rebuilds status, and asks the next missing field. The flow below is the canonical order; the orchestrator may skip steps if fields are already present.

### Step 1 — Document Intake
1. Ask `doc_type` (required).
2. Ask `from` (required; skip if `window_envelope` is set).
3. Ask `date` (required; default to today, confirm).
4. Ask `subj` (required).
5. Ask `ssic` (recommended; allow skip).
6. Ask `originator_code` (recommended; allow skip).

### Step 2 — Routing
7. Ask `to` (required).
8. Ask `via` (optional; allow empty).
9. Ask `copy_to` (optional; allow empty).
10. Ask `distribution` (only if `doc_type == multiple_address_letter`).
11. Ask `window_envelope` (if `from` is still missing after Step 1; boolean).

### Step 3 — Body Drafting
12. Ask `body` (required; accept multi-paragraph text, split into numbered paragraphs).

### Step 4 — References and Enclosures
13. Ask `ref` (optional; allow empty).
14. Ask `encl` (optional; allow empty).

### Step 5 — Signature
15. Ask `signature` (required for final; allow skip for draft).

### Step 6 — Validation Pass
16. Run `orchestrator.run_audit()`.
17. Present `warning`-level findings in plain English.
18. Ask user: **Accept**, **Revise**, or **Ignore** each warning.
19. Present `advisory`-level findings as suggestions.
20. Ask user: **Dismiss** or **View details**.

### Step 7 — Finalize
21. Set `draft_final_status` based on whether signature was skipped.
22. Call `letter_model_v6.normalize_payload()` on `accumulated_payload`.
23. Produce final structured JSON.
24. Optionally render PDF via `pdf_v6_render.py` (not in L.3; deferred to L.6).
25. Produce optional validation summary.

---

## 5. Clarifying-Question Rules

1. **Ask only for missing required fields.**
   - If `to` is already in the payload, do not ask "Who is this letter to?"
2. **Do not ask for fields already provided.**
   - If the user pasted a full letter body, do not ask for body text again.
3. **Combine related questions where safe.**
   - Ask SSIC + originator_code in one turn if both are missing and both are recommended.
4. **Never invent official command data.**
   - Do not generate unit names, office codes, or SSICs. Use user input or leave blank.
5. **Allow user to skip optional fields.**
   - Every optional field question must include an explicit skip path.
6. **Explain warning findings without blocking unless error-level.**
   - `warning` → "Please fix or accept to continue."
   - `advisory` → "Suggestion only; you can dismiss this."
7. **Infer safe defaults only where allowed.**
   - `date` → current date, confirmed.
   - `window_envelope` → `false`, unless user explicitly says otherwise.
   - List fields → `[]` when absent.

---

## 6. Plain-English Audit/Warning Formatter Map

The builder needs a formatter that converts `CCI_AUDIT_V1` validator output into user-facing sentences. No changes to `validator_runner.py`.

### Active Warning Pilots

| Rule Code | Severity | Plain-English Message |
|---|---|---|
| `CCI-ROUTE-010` | `warning` | "An office code in the To or Via line is written as numbers only. SECNAV guidance recommends adding the word 'Code' before it. Example: '123' should be 'Code 123'." |
| `CCI-ROUTE-011` | `warning` | "This standard letter is missing a 'From:' line. Add one, or mark it as a window-envelope letter if it will use a window envelope." |
| `CCI-CH7-SUBJ-002` | `warning` | "The subject line ends with punctuation. SECNAV guidance recommends no terminal punctuation in the subject line." |

### Generic Advisory Fallback

| Rule Code | Severity | Plain-English Message |
|---|---|---|
| `CCI-ROUTE-007` | `advisory` | "One or more addressees appear in both the To/Via lines and the Copy-to list. This is allowed, but verify it is intentional." |
| `CCI-REF-*` | `advisory` | "A reference may be formatted incorrectly. Verify numbering and punctuation." |
| `CCI-ENCL-*` | `advisory` | "An enclosure may be formatted incorrectly. Verify numbering and punctuation." |
| `CCI-ACR-*` | `advisory` | "An acronym in the body may need its full form defined on first use." |
| `CCI-PER-*` | `advisory` | "A personnel identifier or name may need verification." |
| `CCI-DTM-*` | `advisory` | "A date or time format may not follow military conventions." |
| `CCI-POC-*` | `advisory` | "Consider adding a point of contact if the letter requests action or a reply." |

### User Actions per Severity

- `warning`: Present three buttons/prompts:
  - "Revise now" → route back to relevant question.
  - "Accept and keep my wording" → record `accepted` in `user_decisions`.
  - "Ignore this warning" → record `ignored` in `user_decisions`.
- `advisory`: Present one button:
  - "Dismiss" → remove from active display; no blocking.

---

## 7. Separate Builder Module/Interface Proposal

### Proposed Module

- **Path:** `src/conversational_builder.py`
- **Role:** Thin multi-turn wrapper around `IntakeOrchestrator`. No renderer, validator, or config changes.

### Proposed Class

```python
class BuilderSession:
    """
    Multi-turn conversational builder for SECNAV correspondence.
    Delegates to IntakeOrchestrator for policy, questions, and audit.
    """

    def __init__(self, session_id: str | None = None):
        ...

    def start(self, initial_payload: dict | None = None) -> dict:
        """Initialize the session and return the first question/status."""

    def ingest_user_message(self, text: str) -> dict:
        """Process a free-text user response; extract answers, update payload, return next question or status."""

    def next_question(self) -> dict | None:
        """Return the next missing-field question, or None if all required fields are present."""

    def build_payload(self) -> dict:
        """Return the current merged payload (pass-through to orchestrator)."""

    def run_validation(self) -> dict:
        """Run CCI audit and return CCI_AUDIT_V1 result."""

    def warning_summary(self) -> list[dict]:
        """Return plain-English warning items with user decision states."""

    def finalize(self, accept_warnings: bool = False) -> dict:
        """Normalize payload, set draft/final status, return structured output. Does not render PDF."""
```

### Design Notes

- `ingest_user_message()` does **not** do natural-language parsing. In L.3–L.6 it is a simple key-value extractor or direct pass-through for body text. NL mediation can be added later without changing this interface.
- `BuilderSession` does **not** persist to disk. All state is in-memory. Future phases may add session persistence if needed.
- `BuilderSession` does **not** call `pdf_v6_render.py`. The caller (future CLI/API layer) decides when to render.
- `BuilderSession` does **not** modify `cci_intake_questions.json` or `cci_intake_field_policy.json` at runtime. It reads them via the orchestrator.

---

## 8. Schema Gaps Addressed in This Phase

### `window_envelope`

**Gap:** `window_envelope` is not present in `cci_intake_field_policy.json` or `cci_intake_questions.json`, but the renderer and `CCI-ROUTE-011` validator reference it.

**Resolution for L.3:**
- Add `window_envelope` as an `optional` field in `cci_intake_field_policy.json` under `standard_letter`.
- Add a `q_window_envelope` question in `cci_intake_questions.json`:
  - `field_path`: `window_envelope`
  - `importance`: `optional`
  - `applies_to_doc_types`: `["standard_letter"]`
  - `data_type`: `boolean`
  - `prompt_text`: "Will this letter use a window envelope? (If yes, the 'From:' line is not required.)"

**Safety:** This is a JSON-only addition. No renderer, validator, or command-layer changes. The validator already checks `window_envelope`; the policy/questions merely expose it to the builder.

---

## 9. Non-Goals

The following are **not authorized** in Phase L.3 or any L.4–L.7 implementation without separate explicit approval:

1. **No renderer or layout changes.** `src/pdf_v6_render.py` remains read-only.
2. **No CCI severity or config changes.** `config/cci_enforcement_config.json` untouched.
3. **No rule promotion.** No rule may be promoted to `warning` or `error`.
4. **No Phase F or Phase G command-layer changes.** `correction_commands.py` and `correction_nl_commands.py` remain read-only.
5. **No logs or unsanitized material committed.** All fixtures must be synthetic.
6. **Do not read or modify `docs/BOOTSTRAP.md`.**
7. **Do not modify `docs/HERMES_INSTRUCTIONS.md`.**
8. **No natural-language parsing in `ingest_user_message()`.** Keep it simple: key-value or direct text pass-through.
9. **No persistent draft state.** Session interruption = restart in L.3–L.6.
10. **No preview/HTML output.** PDF is the only final output in L.6.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Over-asking questions | `IntakeOrchestrator.next_questions()` already skips present fields; builder limits to `limit=1` per turn. |
| Hallucinating official data | Builder never invents unit names, codes, or SSICs. |
| Changing user intent | Builder is a collector, not a rewriter. Body text is preserved exactly. |
| Over-blocking advisory findings | Advisory findings are non-blocking; only `warning` pilots block finalization. |
| Confusing warning with mandatory error | Plain-English labels distinguish "Warning — must fix or accept" from "Advisory — suggestion only." |
| Breaking renderer behavior | Builder JSON maps 1:1 to existing renderer schema; `letter_model_v6.normalize_payload()` is the final gate. |
| `window_envelope` addition breaks policy loader | The policy loader is a simple JSON read; adding one optional field is safe. |

---

## 11. Recommended Next Phase

**Phase L.4 — Conversational Builder Prototype Module**

Scope:
1. Create `src/conversational_builder.py` stub with `BuilderSession` class and method signatures.
2. Wire `BuilderSession` to `IntakeOrchestrator` for `next_questions()`, `apply_answers()`, and `run_audit()`.
3. Implement a minimal CLI or interactive loop that runs through the question flow above.
4. Add `window_envelope` to `cci_intake_field_policy.json` and `cci_intake_questions.json`.
5. Write a plain-English `warning_summary()` formatter that maps the three active warning pilots.
6. Produce synthetic fixture tests for builder state transitions.

No renderer, validator, config, or command-layer changes.

---

End of Phase L.3 Conversational Builder Payload Schema and Question Flow.
