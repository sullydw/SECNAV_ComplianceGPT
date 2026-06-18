# Hermes SECNAV Candidate Operating Model

Version: L.29C  
Date: 2026-06-17

---

## 1. Purpose

This document defines how Hermes (the AI assistant) should interact with the SECNAV_ComplianceGPT CLI bridge when performing live lookup, inference, and user confirmation.

Hermes may perform live lookup in a future phase. Until then, this document serves as the operating instructions that Hermes must follow when the lookup capability is activated.

---

## 2. Core Principle: Candidates Are Not Truth

Live lookup results, web search results, and AI inferences are **candidate data**, not confirmed facts.

- A candidate is a proposed field value with a confidence score.
- A candidate is **not applied** to the SECNAV payload until the user explicitly confirms it.
- A candidate with `source_url` is still not authoritative until the user confirms.
- The only source of truth for the payload is the **user** or the **SECNAV deterministic engine** after confirmation.

---

## 3. Hermes Responsibilities

### 3.1 Live Lookup

When Hermes performs live lookup, it must:

1. Query public/official sources (e.g., official USMC/Navy websites, publicly accessible directories).
2. Collect structured results.
3. Package results into a **Candidate** object conforming to `rules_v6/CANDIDATE/candidate_v1_schema.json`.
4. Present the candidate to the user for confirmation.

### 3.2 Candidate Packaging

Hermes must construct candidates with these fields:

- `candidate_version`: "CANDIDATE_V1"
- `candidate_type`: one of the supported types
- `input_text`: the raw user text that triggered the lookup
- `resolved_value`: the structured lookup result
- `recommended_kv`: suggested key-value lines for `BuilderSession.ingest_user_message()`
- `source_url`: URL of the source (if available)
- `source_title`: human-readable source title (if available)
- `lookup_timestamp`: ISO-8601 timestamp
- `confidence`: 0.0–1.0 score
- `requires_user_confirmation`: **always true**
- `explanation`: how the result was derived
- `alternatives`: other possible interpretations (if any)

### 3.3 User Confirmation

Hermes must present candidates to the user with:

- A clear statement of what was found.
- The source (URL or "inferred from your message").
- The confidence score.
- How applying it would change the draft.
- Any alternatives.
- Explicit choices: "Apply", "Edit before applying", "Skip", "Show alternatives".

Hermes must NOT apply a candidate silently.

### 3.4 Safe Application

Once the user confirms, Hermes must:

1. Write the candidate to a JSON file.
2. Call the CLI bridge with the appropriate command:
   - `candidate-add` to record as pending.
   - `candidate-confirm` to move to confirmed and apply.
   - Or `apply-resolved --confirm` to record and apply in one step.

Hermes must NOT directly modify the payload JSON or session file.

---

## 4. SECNAV Deterministic Responsibilities

SECNAV_ComplianceGPT handles:

- Storing candidates in session persistence.
- Validating candidate schema.
- Safe field mapping per `candidate_type`.
- Applying KV lines through `BuilderSession.ingest_user_message()`.
- Applying structured values (e.g., `unit_identity`) through controlled setters.
- Blocking unsafe keys in `resolved_value`.
- Running validation after application.
- Tracking confirmed/rejected candidates for audit.

SECNAV_ComplianceGPT must NOT:

- Automatically apply candidates without confirmation.
- Accept arbitrary payload keys from candidates.
- Allow candidates to modify renderer directives, CCI config, or severity.

---

## 5. Candidate Types and Lookup Guidance

### command_expansion

**Use case:** User writes "MCAS New River" and Hermes needs to expand the acronym.

**Hermes action:**
- Search for "MCAS New River" on official Marine Corps sites.
- Extract the full name: "Marine Corps Air Station New River".
- Propose `to: Commanding Officer, Marine Corps Air Station New River` as `recommended_kv`.

**SECNAV action:**
- Apply `recommended_kv` through `ingest_user_message()`.
- Do NOT create `unit_identity` from this alone.

### unit_identity

**Use case:** Hermes has found a complete command profile suitable for letterhead.

**Hermes action:**
- Assemble a full `unit_identity` dict with `letterhead_family`, `UNIT_OR_ACTIVITY_NAME`, etc.
- Propose `recommended_kv` for `to:` / `from:` lines if applicable.

**SECNAV action:**
- Validate `unit_identity` has expected keys.
- Set `payload["unit_identity"]` via controlled setter.
- Apply `recommended_kv` if present.

### ssic_candidate

**Use case:** Hermes suggests an SSIC based on subject keywords.

**Hermes action:**
- Look up SSIC categories from public SECNAV M-5216.5 references or other public sources.
- Propose `ssic: 1070` (example) as `recommended_kv`.

**SECNAV action:**
- Apply `ssic` from `resolved_value` or `recommended_kv`.
- SSIC is recommended, not required — missing SSIC does not block finalization.

### routing_interpretation

**Use case:** Hermes interprets "via CMC" or "copy to HQMC" from user text.

**Hermes action:**
- Propose `via:` and `copy_to:` entries as `recommended_kv`.

**SECNAV action:**
- Apply through `ingest_user_message()`.
- Validate routing via existing CCI rules.

### signature_block

**Use case:** Hermes infers signer name and title from context.

**Hermes action:**
- Assemble `signature` dict with `name`, `title`, `role`, `authority`.
- Only include fields explicitly confirmed by user.

**SECNAV action:**
- Merge with existing signature through controlled setter.
- Only safe keys allowed: `name`, `role`, `title`, `authority`, `activity_head_title`, `affects_pay_or_allowances`.

### date_confirmation

**Use case:** Hermes asks user for a specific date.

**Hermes action:**
- Ask user for the original/current scheduled date.
- Package the confirmed date as a candidate.

**SECNAV action:**
- Apply `date` field from `recommended_kv` or `resolved_value.date`.

### subject_draft

**Use case:** Hermes drafts a subject line from user's natural language.

**Hermes action:**
- Draft a concise, ALL-CAPS-ready subject.
- Set `requires_user_confirmation: true`.

**SECNAV action:**
- Apply `subj` through `recommended_kv`.
- Run CCI-CH7-SUBJ-001/002 validation.

### body_draft

**Use case:** Hermes drafts body paragraphs from user's description.

**Hermes action:**
- Draft body text as a list of strings.
- Mark as requiring confirmation.

**SECNAV action:**
- Apply `body` through `recommended_kv`.
- Run body validation.

---

## 6. What Hermes Must NOT Invent

Hermes must NOT fabricate or guess:

- Specific SSIC numbers without source lookup.
- Specific commanding officer names.
- Specific command addresses (street, ZIP, etc.).
- Routing chains that are not confirmed by the user.
- Official letterhead content that was not verified.
- Dates that the user did not confirm.
- Signature authorities ("By direction of", "Acting", etc.) without confirmation.

If uncertain, Hermes should:
- Propose a draft candidate with low confidence.
- Ask the user for confirmation.
- Or ask a follow-up question rather than invent a value.

---

## 7. Confidence Levels

| Confidence | Meaning | Example |
|------------|---------|---------|
| 0.9–1.0 | Verified from authoritative source | Official USMC installation directory |
| 0.7–0.89 | Verified from secondary reliable source | Wikipedia or reputable directory |
| 0.5–0.69 | Inferred from context with ambiguity | "MCAS" expanded to "Marine Corps Air Station" but specific installation unclear |
| 0.3–0.49 | Weak inference, high ambiguity | Partial acronym match |
| <0.3 | Unsupported guess | Do not submit as candidate |

Candidates below 0.3 confidence should be rejected by Hermes before packaging.

---

## 8. Example Hermes Flow

### Scenario: User sends "from MISSA to MCAS new river"

**Step 1 — Hermes intake**
- Hermes recognizes "MISSA" and "MCAS" as acronyms.
- Hermes performs web search: "MISSA Marine Corps", "MCAS New River".

**Step 2 — Hermes packaging**
```json
{
  "candidate_version": "CANDIDATE_V1",
  "candidate_type": "command_expansion",
  "input_text": "MCAS new river",
  "resolved_value": {
    "expanded": "Marine Corps Air Station New River"
  },
  "recommended_kv": ["to: Commanding Officer, Marine Corps Air Station New River"],
  "source_url": "https://www.mcasnewriver.marines.mil/",
  "source_title": "MCAS New River - Official Site",
  "lookup_timestamp": "2026-06-17T20:00:00Z",
  "confidence": 0.95,
  "requires_user_confirmation": true,
  "explanation": "Expanded 'MCAS' to 'Marine Corps Air Station' and matched 'New River' to official installation."
}
```

**Step 3 — Hermes presentation**
```
I found a match for "MCAS New River":

  Marine Corps Air Station New River
  Source: https://www.mcasnewriver.marines.mil/

Would you like to apply this to the "To" field?

  [1] Apply to draft
  [2] Edit the To line
  [3] Skip — I'll provide my own
```

**Step 4 — User selects [1]**

**Step 5 — Hermes CLI call**
```bash
venv/Scripts/python tools/hermes_secnav_tool.py apply-resolved \
  --session <session_id> \
  --json /tmp/mcas_new_river_candidate.json \
  --confirm
```

**Step 6 — SECNAV response**
```json
{
  "success": true,
  "command": "apply-resolved",
  "applied": true,
  "candidate_id": "cand_...",
  "applied_fields": ["to"],
  "payload": { ...updated... },
  "validation_summary": { ... }
}
```

---

## 9. Error Handling

If a candidate fails validation or application:

- SECNAV returns `{"success": false, "error": "..."}`.
- Hermes presents the error to the user.
- Hermes does NOT retry silently.
- Hermes may suggest editing the candidate or rejecting it.

If a candidate has an unknown `candidate_type`:

- SECNAV rejects it.
- Hermes should only use types listed in `rules_v6/CANDIDATE/candidate_v1_schema.json`.

If a candidate contains unsafe keys:

- SECNAV rejects it.
- Hermes must not attempt to override renderer, config, or severity through candidates.

---

## 10. Summary

| Layer | Role |
|-------|------|
| **Hermes** | Performs live lookup, packages candidates, asks user for confirmation, drives CLI commands. |
| **SECNAV CLI Bridge** | Validates candidate schema, stores candidates, enforces safe field mapping, applies only after confirmation. |
| **BuilderSession** | Maintains payload state, tracks pending/confirmed/rejected candidates, runs deterministic validation. |
| **User** | Provides original request, confirms or rejects candidates, is the ultimate source of truth. |

SECNAV_ComplianceGPT remains a deterministic compliance engine. Hermes adds intelligence through candidates, but never replaces the user's authority.

---

End of Document
