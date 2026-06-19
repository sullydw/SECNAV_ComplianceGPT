# General Live Lookup Candidate Workflow

**Version:** L.29H  
**Date:** 2026-06-18  
**Status:** Design / Documentation  
**Precedent:** Phase L.29C (candidate confirmation infrastructure), Phase L.29E (browser requirement), Phase L.29G-2 (browser agent retest)

---

## 1. Purpose

This document defines a **reusable, general workflow** for live lookup candidate creation that works for **any** SECNAV letter, not a specific sample.

The sample request:

> I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN

may be used **only as a test fixture** to prove the general workflow. No hardcoded behavior for this sample shall be added to source code, candidate files, or lookup logic.

---

## 2. Core Principle: Candidates Are Session-Specific, Not Permanent

- A candidate is a **temporary proposal** tied to one builder session.
- A candidate is **not a unit database entry**.
- A candidate is **not reusable across letters** unless the user confirms it again.
- A candidate with a source URL is still not authoritative until the user confirms it.
- The only source of truth for the payload is the **user** or the **SECNAV deterministic engine** after confirmation.

---

## 3. Dynamic Per-Letter Workflow

For each new letter request, Hermes executes this loop:

```
Step 1: Ingest user request into a BuilderSession
Step 2: Inspect payload for unresolved facts
Step 3: For each unresolved fact, decide: lookup / ask user / infer safely / leave blank
Step 4: If lookup: choose source, retrieve, classify tier
Step 5: Package retrieved data as CANDIDATE_V1
Step 6: Add candidate via candidate-add --session <id> --json <file>
Step 7: List candidates via candidates --session <id>
Step 8: Present to user for confirmation
Step 9: If confirmed: apply via candidate-confirm or apply-resolved --confirm
Step 10: If rejected: reject via candidate-reject
Step 11: Re-evaluate unresolved facts and repeat until user finalizes or Hermes stops
```

---

## 4. Unresolved Fact Categories

Hermes inspects the session payload and user request for these categories:

| Category | Examples | Detection Method |
|----------|----------|---------------|
| Unknown acronyms | "MISSA", "MITSM", "HQ BN" | Pattern: all-caps token not in known-acronym whitelist |
| Raw unit/command names | "MCAS new river" | Pattern: informal casing, missing "Commanding Officer" prefix |
| Informal location names | "Quantico" without full address | Pattern: geographic mention without structured address |
| Ambiguous routing phrases | "HQ BN" as recipient vs context | Pattern: trailing noun phrase after comma in To line |
| Missing SSIC | no `ssic` field in payload | Field absence check |
| Missing originator code | no `originator_code` or `from_code` | Field absence check |
| Missing letterhead/unit_identity | no `unit_identity` in payload | Field absence check |
| Missing signature block | no `signature` in payload | Field absence check |
| Missing dates | no `date` in payload | Field absence check + validation CCI-DTM-* |
| Missing references/enclosures | user mentions "REF A" but no `refs` field | Keyword scan for "reference", "enclosure", "REF" |
| Subject formatting | lowercase subject triggering CCI-CH7-SUBJ-001 | Validation error presence |

---

## 5. Lookup Decision Table

For each unresolved fact, Hermes decides per this priority:

| Priority | Strategy | When Used |
|----------|----------|-----------|
| 1 | Ask user directly | When the fact is subjective (signer name, specific date, routing intent) |
| 2 | Live lookup | When an official/public source likely exists (unit website, DONI, manpower directory) |
| 3 | Infer safely | When inference is low-risk and reversible (e.g., "MCAS" → "Marine Corps Air Station") |
| 4 | Leave blank | When no source exists and user prefers to fill later |
| 5 | Low-confidence candidate | When partial match exists but confidence < 0.7; presented with alternatives |
| 6 | Refuse to infer | When invention risk is high (specific CO name, exact address, SSIC code) |

---

## 6. Source Quality Tiers

All live lookup results are classified:

| Tier | Name | Criteria | Confidence Range |
|------|------|----------|-----------------|
| 1 | Official live source | `.mil` or `.gov` domain, HTTPS, active, verified banner/seal | 0.90–1.00 |
| 2 | Official archived/mirrored source | Official domain but archived page, redirect, or mirror | 0.80–0.89 |
| 3 | Credible secondary source | Wikipedia, reputable military reference, verified directory | 0.70–0.79 |
| 4 | User-provided source | User supplies URL or text; not independently verified | 0.50–0.69 |
| 5 | Unresolved | No source found, or source inaccessible | < 0.50 |

Candidates below 0.50 confidence should not be submitted. Candidates below 0.30 must be rejected by Hermes before packaging.

---

## 7. Candidate Creation Rules

### 7.1 General Rules

1. Every candidate must have `candidate_version`: "CANDIDATE_V1".
2. Every candidate must have `requires_user_confirmation`: true.
3. Every candidate must include `source_url` and `source_title` when source-backed.
4. Every candidate must include `lookup_timestamp` in ISO-8601 format.
5. Every candidate must include `confidence` in [0.0, 1.0].
6. `resolved_value` must contain only safe, schema-compliant fields.
7. `recommended_kv` must use the exact key:value format expected by `BuilderSession.ingest_user_message()`.
8. `explanation` must describe how the result was derived, not just state the fact.
9. `alternatives` must list other possible interpretations if ambiguity exists.
10. Unknown `candidate_type` values are rejected by the CLI bridge.

### 7.2 Type-Specific Rules

#### command_expansion
- Use when: user writes an acronym or shorthand that needs expansion.
- Resolved value: `{"expanded": "...", "parent_organization": "..."}`.
- Recommended KV: `["to: Commanding Officer, <expanded>", "from: <expanded>"]`.
- Source requirement: Tier 1–3 preferred; Tier 4 accepted if user-supplied.
- Example: "MCAS New River" → "Marine Corps Air Station New River".

#### unit_identity
- Use when: Hermes has enough data to populate letterhead fields.
- Resolved value: structured dict with `letterhead_family`, `UNIT_OR_ACTIVITY_NAME`, `SHORT_NAME`, `MOTTO`, `OFFICIAL_WEBSITE`.
- Address fields (`STREET_ADDRESS`, `CITY_STATE_ZIP`) are **omitted** if not retrieved from source.
- Do NOT invent address, ZIP, or commanding officer name.
- Source requirement: Tier 1 strongly preferred.
- Only confirmed unit_identity feeds letterhead rendering.

#### ssic_candidate
- Use when: user request implies a subject category that may have an SSIC.
- Hermes must NOT invent a specific SSIC code.
- Hermes may locate the official SSIC manual (SECNAV M-5210.2) and cite it.
- If no specific code is source-supported:
  - `specific_ssic`: null
  - `ssic_resolution_status`: "SOURCE_IDENTIFIED_NOT_CODE"
  - Recommended KV: empty
- SSIC is optional; missing SSIC does not block finalization.
- Source requirement: Tier 1 (secnav.navy.mil/doni/ or doncio.navy.mil).

#### routing_interpretation
- Use when: user text contains ambiguous routing phrases ("via CMC", "copy to HQMC", "HQ BN").
- Hermes must NOT assume whether a phrase is To, Via, or Copy-to.
- Hermes may propose options with alternatives.
- User must select one option or provide their own.
- If no source resolves the ambiguity, create NO candidate. Ask user directly.

#### signature_block
- Use when: Hermes infers signer from context or user provides name.
- Only include fields explicitly confirmed by user.
- Safe keys: `name`, `role`, `title`, `authority`, `activity_head_title`, `affects_pay_or_allowances`.
- Do NOT invent "By direction of" or "Acting" without user confirmation.

#### date_confirmation
- Use when: user mentions changing a date but does not specify the original or new date.
- Ask user directly; do not invent dates.
- Once confirmed, package as candidate.

#### subject_draft
- Use when: user provides a natural-language subject that triggers CCI-CH7-SUBJ-001.
- Draft ALL-CAPS subject from user text.
- Set `requires_user_confirmation: true`.
- Recommended KV: `["subj: <DRAFTED SUBJECT>"]`.

#### body_draft
- Use when: user describes body content in natural language.
- Draft body as list of strings.
- Set `requires_user_confirmation: true`.

---

## 8. User Confirmation Flow

Hermes must present each pending candidate with:

1. What was found.
2. The source (URL or "inferred from your message").
3. The source tier.
4. The confidence score.
5. How applying it would change the draft.
6. Any alternatives.
7. Explicit choices:
   - **[1] Apply to draft**
   - **[2] Edit before applying**
   - **[3] Skip — I'll provide my own**
   - **[4] Show alternatives** (if any)

Hermes must NOT apply a candidate silently.

---

## 9. Letterhead Rule

- Letterhead should only be generated from a **confirmed** `unit_identity` candidate.
- Hermes may propose `unit_identity` from live lookup.
- SECNAV renders letterhead only after user confirmation.
- Address fields that were not source-retrieved remain blank in the rendered letterhead.

---

## 10. SSIC Rule

- Hermes must not invent a code.
- Hermes may locate official SSIC source material.
- Hermes may propose a candidate only if the code is source-supported.
- Otherwise, Hermes asks user: "Should SSIC be left blank, or should we continue source-backed lookup?"

---

## 11. Routing Rule

- Hermes must not guess whether an ambiguous phrase is To, Via, Copy-to, or context.
- Hermes may propose options: "Is HQ BN a recipient, a via addressee, a copy-to, or just context?"
- User selection determines how the KV line is constructed.
- If user chooses "context only", no routing KV is created.

---

## 12. Sample Request Illustration (Fixture Only)

The following illustrates how the general workflow applies to the sample request. **This sample shall not be hardcoded.**

### Sample Request

> I need to request to change a date for software release brief to a open TBD date. it is from MISSA to MCAS new river, HQ BN

### Step-by-Step Application

**Step 1: Ingest**
- Payload: `from: MISSA`, `to: MCAS new river, HQ BN`, `subj: change a date...`

**Step 2: Unresolved Facts Detected**
- "MISSA" — unknown acronym (likely command_expansion)
- "MCAS new river" — raw unit name (likely unit_identity)
- "HQ BN" — ambiguous routing phrase (routing_interpretation needed)
- No date field (date_confirmation needed)
- Lowercase subject (subject_draft needed)
- No SSIC (ssic_candidate optional)

**Step 3: Lookup Decisions**
- MISSA → Live lookup on manpower.marines.mil
- MCAS New River → Live lookup on newriver.marines.mil
- HQ BN → Ask user directly (no official source for routing intent)
- Date → Ask user directly
- Subject → Infer safely (draft ALL-CAPS version)
- SSIC → Locate official source; no specific code

**Step 4: Source Retrieval (Actual Results from L.29G-2)**
- MISSA: Found as "System Support Activity Branch (MISSA)" on manpower.marines.mil — Tier 1
- MCAS New River: Found official site newriver.marines.mil — Tier 1
- SSIC: Found SECNAV Manual M-5210.2 on secnav.navy.mil/doni/ — Tier 1, no specific code
- HQ BN: No official source resolved routing role — Tier 5

**Step 5: Candidate Packaging**
Three candidates created (illustration only):
1. command_expansion for MISSA
2. unit_identity for MCAS New River
3. ssic_candidate for SSIC source

No candidate created for HQ BN (unresolved, ask user).
No candidate created for date (ask user directly).

**Step 6–7: Store and List**
```bash
venv/Scripts/python tools/hermes_secnav_tool.py candidate-add --session <id> --json missa.json
venv/Scripts/python tools/hermes_secnav_tool.py candidate-add --session <id> --json mcas.json
venv/Scripts/python tools/hermes_secnav_tool.py candidate-add --session <id> --json ssic.json
venv/Scripts/python tools/hermes_secnav_tool.py candidates --session <id>
```

**Step 8: User Presentation**

- MISSA candidate: "I found MISSA as 'System Support Activity Branch (MISSA)' under Manpower Information. Source: manpower.marines.mil. Tier 1. Confidence 0.92. Apply to From line?"
- MCAS New River candidate: "I found official MCAS New River. Source: newriver.marines.mil. Tier 1. Confidence 0.95. Apply to To line?"
- SSIC candidate: "I located the official SSIC manual (SECNAV M-5210.2). No specific code found for this topic. Leave SSIC blank?"
- HQ BN question: "Is HQ BN a recipient, via, copy-to, or context only?"
- Date question: "What is the original scheduled date?"

**Step 9–10: User Acts**
User confirms/rejects/edits each candidate. Hermes calls candidate-confirm or candidate-reject accordingly.

---

## 13. Do-Not-Hardcode Warning

The following are **explicitly prohibited**:

- Creating a static command/unit database.
- Adding hardcoded MISSA expansion logic to source code.
- Adding hardcoded MCAS New River behavior to source code.
- Creating reusable candidate JSON files for this sample.
- Embedding this sample into test fixtures that are not clearly marked as generic workflow tests.
- Adding specific unit addresses or commanding officer names that were not source-retrieved.
- Building an SSIC lookup table from this session's results.

Every session must independently evaluate its own unresolved facts and perform its own lookups.

---

## 14. Hermes Browser-Agent Runtime Prerequisites

For live lookup to work, the environment must satisfy:

| Prerequisite | How to Verify |
|-------------|---------------|
| Node.js visible in PATH | `node --version` returns version |
| `BROWSER_CDP_URL` set | `echo $BROWSER_CDP_URL` shows `http://127.0.0.1:9222` |
| Edge CDP healthy | `curl http://127.0.0.1:9222/json/version` returns browser version JSON |
| Edge remote debugging enabled | Launch with `--remote-debugging-port=9222` |
| Clean session preferred | Use `--user-data-dir="%TEMP%\edge-lookup-<session>"` to avoid tab contamination |

If prerequisites are missing, Hermes must:
- Report the missing prerequisite.
- Fall back to asking the user directly.
- Do NOT silently skip lookup and invent data.

---

## 15. How candidate-confirm / apply-resolved Should Be Used

### candidate-confirm

```bash
venv/Scripts/python tools/hermes_secnav_tool.py \
  candidate-confirm --session <id> --candidate-id <cand_id>
```

- Moves candidate from pending → confirmed.
- Applies candidate fields to payload via safe setters.
- Runs validation after application.
- Returns updated payload and validation summary.

### candidate-reject

```bash
venv/Scripts/python tools/hermes_secnav_tool.py \
  candidate-reject --session <id> --candidate-id <cand_id> --reason "..."
```

- Moves candidate from pending → rejected.
- Does NOT modify payload.
- Records rejection reason for audit.

### apply-resolved (with --confirm)

```bash
venv/Scripts/python tools/hermes_secnav_tool.py \
  apply-resolved --session <id> --json <file> --confirm
```

- Stores candidate as pending.
- Immediately confirms and applies.
- Use only when user has already given explicit confirmation.

### apply-resolved (without --confirm)

```bash
venv/Scripts/python tools/hermes_secnav_tool.py \
  apply-resolved --session <id> --json <file>
```

- Stores candidate as pending only.
- Does NOT apply to payload.
- Use when user has not yet confirmed.

### apply-resolved --dry-run

```bash
venv/Scripts/python tools/hermes_secnav_tool.py \
  apply-resolved --session <id> --json <file> --dry-run
```

- Previews what would change without storing or applying.
- Returns proposed payload diff and validation forecast.

---

## 16. Failure Modes

| Failure | Hermes Response |
|---------|----------------|
| Browser/CDP not available | Report to user; fall back to asking directly |
| Source returns DNS error | Classify as Tier 5; try alternatives; ask user |
| Source requires authentication | Classify as Tier 5; do not attempt login |
| Source blocks bot/WAF | Classify as Tier 5; try alternative source |
| Multiple possible expansions | Create candidate with alternatives; low confidence |
| No source found | Classify as Tier 5; ask user directly |
| Candidate rejected by CLI | Present error to user; suggest edit or rejection |
| Unknown candidate_type | Rejected by SECNAV; Hermes should only use allowed types |
| Unsafe key in resolved_value | Rejected by SECNAV; Hermes must avoid unsafe keys |

---

## 17. Summary

| Layer | Responsibility |
|-------|---------------|
| **Hermes** | Detect unresolved facts, decide lookup strategy, retrieve sources, classify tiers, package candidates, present for confirmation, drive CLI commands |
| **SECNAV CLI Bridge** | Validate candidate schema, store candidates, enforce safe field mapping, apply only after confirmation, run validation, track audit trail |
| **BuilderSession** | Maintain payload state, track pending/confirmed/rejected candidates, run deterministic validation |
| **User** | Provide original request, confirm/reject candidates, answer direct questions, is the ultimate source of truth |

---

End of General Live Lookup Candidate Workflow.
