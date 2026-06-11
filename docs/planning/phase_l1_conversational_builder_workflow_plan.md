# Phase L.1 — Conversational Builder Workflow Plan

**Status:** Planning-only. No implementation code created.  
**Commit:** `[TBD]` — `Docs: Add conversational builder workflow plan`  
**Latest Verified Baseline:** `2f2ba95` — Current HEAD  
**Active Warning Pilots:** `CCI-ROUTE-010 = warning`, `CCI-ROUTE-011 = warning`, `CCI-CH7-SUBJ-002 = warning`  
**Global Default:** `advisory`  
**Error Promotion:** Unauthorized  
**CCI Rule Expansion:** Paused unless explicitly requested  
**Regression Gate:** 37 suites PASS at `2f2ba95`

---

## 1. Goal

Enable a user to create a SECNAV M-5216.5 compliant Navy or Marine Corps letter through a guided, conversational interface.

Requirements:
- System asks only the minimum clarifying questions needed to produce a valid letter payload.
- System does not re-ask for information the user already provided.
- System infers safe defaults only where SECNAV conventions allow and the user has not expressed a preference.
- System produces a structured JSON letter payload suitable for the v6 renderer.
- System runs CCI validation before final PDF generation and surfaces findings in plain English.
- System keeps the user in control of all final content; no automatic rewriting without explicit approval.

---

## 2. Current Known Capabilities

| Capability | Status | Notes |
|---|---|---|
| v6 PDF renderer | Stable, regression-protected | `src/pdf_v6_render.py` — C7-C10 coverage |
| Header / SSIC / subject / body / signature / distribution / copy-to | Implemented | Protected by C7-C10 regressions |
| CCI validator infrastructure | Active | `src/validator_runner.py` one-call entry point |
| Severity config mapper | Stable | `src/cci_severity_mapper.py` + `config/cci_enforcement_config.json` |
| Warning pilots | Active | ROUTE-010, ROUTE-011, SUBJ-002 all at `warning`; global default `advisory` |
| Intake orchestrator | Implemented | `src/intake_orchestrator.py` — missing-field intake, profile support, CCI audit |
| Context resolver | Implemented | `src/context_resolver.py` — canonical CCI context object |
| Correction memory (A-H) | Implemented | Session, profile, pending, review, command, NL mediation layers |

What is **not** currently implemented:
- Dedicated conversational builder schema / state machine above intake.
- Progressive clarification logic that skips already-known fields.
- Plain-English CCI warning summary formatter for end-user display.
- Structured "builder JSON" abstraction distinct from raw renderer payload.

---

## 3. Proposed Conversation Flow

The builder is a single-session guided workflow with deterministic phases. Each phase populates fields; later phases may backfill earlier ones if the user provides new information.

### Phase 1 — Document Intake
- Ask: document type (standard letter, memo, endorsement, joint letter, etc.).
- Ask: originating organization / From line (if applicable and not window envelope).
- Ask: SSIC (if known; allow skip with advisory note).
- Ask: subject line.
- Ask: purpose / classification (if user wants it noted; optional).

### Phase 2 — Routing
- Ask: primary addressee (To line).
- Ask: Via lines (if any; allow empty).
- Ask: Copy-to addressees (if any; allow empty).
- Ask: distribution list (if separate from Copy-to; allow empty).
- Infer or warn: if an addressee appears in both To/Via and Copy-to, surface `CCI-ROUTE-007` warning (already implemented in validator; currently advisory).

### Phase 3 — Body Drafting
- Ask: body text or upload / paste.
- Allow: multi-paragraph input.
- Do not: auto-paraphrase official policy; preserve user wording exactly.

### Phase 4 — References and Enclosures
- Ask: references (if any; allow empty).
- Ask: enclosures (if any; allow empty).
- Validate: ref/encl numbering and formatting via existing `CCI-REF-*` / `CCI-ENCL-*` validators.

### Phase 5 — Signature
- Ask: signer name and title.
- Ask: signature block elements the user wants included (rank, designation, etc.).
- Allow: skip if user intends to sign manually later; mark as draft.

### Phase 6 — Validation Pass
- Run `validator_runner.py` against the populated payload.
- Surface findings grouped by severity:
  - `error` — block generation; require user fix or explicit override (no current error pilots are active; this path exists for future rules and hard renderer constraints).
  - `warning` — present in plain English; allow user to accept, revise, or ignore.
  - `advisory` — present as "suggestion"; user can dismiss without action.
- Do not auto-correct findings.

### Phase 7 — Preview / Final PDF Generation
- Render preview (optional HTML or image view if available; otherwise skip to PDF).
- Generate final PDF via existing `src/pdf_v6_render.py`.
- Deliver: final structured JSON, final PDF, optional validation summary.

---

## 4. Clarifying-Question Policy

1. **Ask only for missing required fields.**
   - Required fields are those the renderer needs to produce a minimally valid document of the selected type.
   - Example: a standard letter requires `To`, `From` (unless window envelope), `Subject`, `Body`.
2. **Do not ask for things already provided.**
   - If the user included a Via line in their initial description, do not ask "Do you want a Via line?"
3. **Infer safe defaults only where allowed.**
   - If the user said "standard Navy letter" and did not specify page margins, do not ask about margins; use renderer defaults.
   - If the user provided an office code that starts with a letter, do not prepend "Code" (per `CCI-ROUTE-010`).
4. **Surface warnings without blocking unless the rule is error-level.**
   - Current active warning pilots block generation; the user must accept or revise.
   - Advisory findings are shown but do not block.
5. **Keep user in control of final content.**
   - The builder is a collector and validator, not a rewriter.
   - Any proposed wording change requires explicit user approval.

---

## 5. Data Model

### Minimum Structured Fields (Required for Standard Letter)

| Field | Type | Source |
|---|---|---|
| `doc_type` | string | User selection or inference |
| `to` | array of objects | User input |
| `from` | object or null | User input; null if window envelope |
| `subject` | string | User input |
| `body` | string or array of strings | User input |
| `signature` | object | User input (may be empty for draft) |

### Optional Fields

| Field | Type | Notes |
|---|---|---|
| `ssic` | string | Optional; advisory if blank |
| `via` | array of objects | Optional; empty array default |
| `copy_to` | array of objects | Optional; empty array default |
| `distribution` | array of objects | Optional; empty array default |
| `references` | array of objects | Optional |
| `enclosures` | array of objects | Optional |
| `window_envelope` | boolean | Default `false`; suppresses `From` requirement and `CCI-ROUTE-011` warning |
| `classification` | string | Optional marking |
| `continuation_pages` | boolean | Default `false` |
| `joint_letter` | boolean | Default `false` |
| `multiple_address` | boolean | Default `false` |

### Fields That Affect Validation

| Field | Affected CCI Rules |
|---|---|
| `subject` | `CCI-CH7-SUBJ-*`, `CCI-CH7-SUBJ-002` (terminal punctuation warning pilot) |
| `to`, `via` | `CCI-ROUTE-010` (office-code warning pilot), `CCI-ROUTE-011` (From-line warning pilot) |
| `copy_to` | `CCI-ROUTE-007` (duplicate To/Via+Copy-to detection, currently advisory) |
| `references`, `enclosures` | `CCI-REF-*`, `CCI-ENCL-*` |
| `body` | `CCI-ACR-*`, `CCI-PER-*`, `CCI-DTM-*`, `CCI-POC-*` |
| `window_envelope` | Suppresses `CCI-ROUTE-011` |

---

## 6. Validation Integration

### Before Final PDF
1. Assemble the structured payload from all collected phases.
2. Call `src/validator_runner.py` or equivalent entry point with the payload.
3. Receive `errors`, `warnings`, and `advisory` arrays.
4. Group findings by rule code for readability.

### Plain-English Display Rules
- Do not emit raw rule codes unless the user asks.
- Map each finding to a short sentence:
  - `CCI-ROUTE-011` warning → "This standard letter is missing a 'From:' line. Add one, or mark it as a window-envelope letter."
  - `CCI-CH7-SUBJ-002` warning → "The subject line ends with punctuation. SECNAV guidance recommends no terminal punctuation."
  - `CCI-ROUTE-010` warning → "An office code is written as numbers only. Consider adding the word 'Code' before it."
- Provide explicit actions:
  - "Accept and keep my wording."
  - "Revise now."
  - "Ignore this advisory."

### No Error Promotion
- No rule may be silently elevated to `error` in this phase.
- The builder respects the existing config severity map exactly.
- If a future rule is promoted to `error` later, the builder blocks generation and asks the user to fix it.

---

## 7. Output

At the end of a successful builder session, the system produces:

1. **Final Structured JSON** — a renderer-ready payload with all populated fields.
2. **Final PDF** — generated by the existing v6 renderer.
3. **Optional Validation Summary** — a human-readable list of warnings and advisories encountered, with user decisions recorded (accepted / revised / ignored).

The validation summary is a view-only artifact; it does not modify the payload or the PDF.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Over-asking questions | Strict missing-field-only policy; skip known fields; phase-gate design |
| Hallucinating official data | Never invent office codes, SSICs, or addressee names; require user input |
| Changing user intent | No auto-rewrite; preserve exact wording; propose, do not apply |
| Over-blocking advisory findings | Builder respects config severity; advisory never blocks; warning blocks only for active warning pilots |
| Confusing warning with mandatory error | Plain-English labels: "Warning — must fix or accept" vs "Advisory — suggestion only" |
| Breaking renderer behavior | Builder JSON maps 1:1 to existing renderer schema; no renderer changes in this phase |
| Session state loss | Single-session workflow; if interrupted, user restarts; no persistent draft state in L.1 |

---

## 9. Proposed Implementation Phases

| Phase | Name | Scope | Deliverable |
|---|---|---|---|
| **L.2** | Conversational Builder Entry-Point Review | Inspect current UI/CLI/chat entry points (`src/intake_orchestrator.py`, `src/correction_nl_commands.py`, any existing builder paths) | Review document listing entry points, gaps, and integration points |
| **L.3** | Conversational Intake Schema Definition | Define the builder state machine, schema, and phase transition rules | `docs/planning/phase_l3_conversational_intake_schema.md` |
| **L.4** | Guided Intake Prototype | Implement a lightweight prototype that runs through the seven phases above, collecting input and producing structured JSON | Prototype module + synthetic fixture tests |
| **L.5** | Validation Summary Integration | Wire `validator_runner.py` into the builder; add plain-English formatter | Builder validation pass + summary display |
| **L.6** | PDF Generation from Guided Payload | Feed builder JSON into `src/pdf_v6_render.py`; verify no renderer changes needed | End-to-end builder-to-PDF pipeline |
| **L.7** | Regression Tests for Guided Builder | Add targeted regression suite for builder states, edge cases, and warning pilot interactions | New regression runner under `tools/` |

### Gating Rules Between Phases
- Each phase requires a planning document approved before implementation.
- All 37 existing regression suites must pass before any commit.
- No renderer/layout changes in L.2–L.7 without separate planning and explicit approval.
- No CCI severity/config changes in L.2–L.7.
- No rule promotion in L.2–L.7.

---

## 10. Explicit Prohibitions

The following are **not authorized** in Phase L.1 or any L.2–L.7 implementation without separate explicit approval:

1. **No renderer or layout changes.** `src/pdf_v6_render.py` remains read-only for this track.
2. **No CCI severity or config changes.** `config/cci_enforcement_config.json` untouched.
3. **No rule promotion.** No rule may be promoted to `warning` or `error` as part of builder work.
4. **No Phase F or Phase G command-layer changes.** `src/correction_commands.py` and `src/correction_nl_commands.py` may be read for integration analysis but not modified unless later approved.
5. **No logs or unsanitized material committed.** All fixtures must be synthetic; all evidence corpora remain gitignored.
6. **Do not read or modify `docs/BOOTSTRAP.md`.**
7. **Do not modify `docs/HERMES_INSTRUCTIONS.md`.**

---

## Recommended Next Phase

**Phase L.2 — Conversational Builder Entry-Point Review**

Read `src/intake_orchestrator.py`, `src/correction_nl_commands.py`, and any existing builder or wizard code paths. Produce a lean review document that identifies:
- Where a conversational builder hook should attach.
- What intake fields are already collected.
- What schema gaps exist between the current intake JSON and a full letter payload.
- Whether the existing NL command mediator can host builder intent detection without modification.

No code changes. Planning and review only.

---

End of Phase L.1 Conversational Builder Workflow Plan.
