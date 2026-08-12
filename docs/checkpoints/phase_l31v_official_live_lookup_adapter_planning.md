# Phase L.31V — Official Live Lookup Adapter Planning

**Baseline:** `e7f6fcd` — Docs: Record source-backed candidate resolver baseline  
**Prior functional baseline:** `266201d` — Tools: Normalize confirmed candidate missing prompt  
**Planning only:** This phase defines the live lookup adapter contract and guardrails. It does not implement live lookup.

---

## Purpose

Plan a future official-source command/unit lookup adapter for Hermes without building a giant static command list and without allowing online lookup results to silently mutate SECNAV correspondence payloads.

The accepted L.31T behavior remains the controlling safety model:

1. Controlled aliases apply directly.
2. Unknown commands remain literal.
3. Source-backed results are candidate-only.
4. Candidates require user confirmation before payload mutation.
5. Confirmed official source-backed From candidates may apply From and letterhead.
6. Rejected candidates do not apply and are not immediately re-suggested.

---

## Non-Goals

This phase must not:

- Implement live internet lookup.
- Add a broad hardcoded command database.
- Add one-off static fixes for examples.
- Modify PDF renderer/layout.
- Modify body alignment.
- Modify letterhead layout.
- Modify validator rules.
- Modify CCI configuration, severity, or rule files.
- Modify `docs/BOOTSTRAP.md`.
- Modify `docs/HERMES_INSTRUCTIONS.md`.
- Change approval hash logic.
- Auto-apply online-derived command, unit, routing, or letterhead data.

---

## Adapter Contract

Future live lookup should be exposed as an injectable adapter with the same conceptual shape as the deterministic L.31T fake resolver:

```python
def official_command_lookup(command_text: str, role: str, state: dict) -> dict | None:
    ...
```

Expected inputs:

| Input | Meaning |
|------|---------|
| `command_text` | The unresolved literal command phrase from the user |
| `role` | The field context, normally `from` or `to` |
| `state` | Current chat/session context, including rejected candidate memory |

Expected return:

```python
{
    "candidate_type": "command_expansion",
    "resolved_value": {
        "from": "Commanding Officer, Example Command",
        "letterhead_top_line": "DEPARTMENT OF THE NAVY",
        "letterhead_activity": "EXAMPLE COMMAND",
        "letterhead_address": "NORFOLK VA 23511-0000"
    },
    "source_tier": "official_live",
    "source_title": "Example Command Official Homepage",
    "source_url": "https://www.example.navy.mil/",
    "source_limitation": "Official page title/address reviewed; verify currency before use if source is ambiguous.",
    "confidence": 0.86,
    "requires_user_confirmation": True
}
```

The adapter may return `None` when no reliable result is found.

---

## Candidate-Only Rule

All live lookup results must enter Hermes as candidates only.

Before user confirmation:

- Do not change `from`.
- Do not change `to`.
- Do not set `letterhead_top_line`.
- Do not set `letterhead_activity`.
- Do not set `letterhead_address`.
- Do not mark the draft render-ready based solely on an unconfirmed candidate.

After user confirmation:

- Apply only fields included in the confirmed candidate.
- Apply letterhead only when the candidate is for the `from` command.
- Apply letterhead only when `source_tier == "official_live"` and source evidence clearly supports the originating command.
- Continue normal validation, approval, preview, and render gates.

---

## Source Tier Rules

| Tier | Definition | Candidate Behavior |
|------|------------|-------------------|
| `official_live` | Current official `.mil`, Navy, Marine Corps, DoD, or command-controlled page | May become confirmable candidate |
| `official_archived` | Official but archived, stale, or historical page | Candidate may be shown with warning; no automatic letterhead application after confirmation unless user explicitly provides/accepts letterhead |
| `secondary_credible` | Credible non-official source, such as reputable institutional reference | Candidate may be shown for discussion only; do not apply letterhead |
| `user_provided` | User supplies the information directly | Treat as user-provided field input, still validate normally |
| `unresolved` | No reliable source | Preserve literal text and ask user for full command name or letterhead |

---

## Official Source Preference

Lookup should prefer, in order:

1. Current command-controlled `.mil` page.
2. Current Navy/Marine Corps/DoD official page.
3. Current official directory page.
4. Official archived page, clearly labeled as archived/stale.
5. Credible secondary source only as a non-authoritative hint.

Hermes must not treat generic web snippets, social media pages, unofficial biographies, Wikipedia, or SEO directory pages as authority for letterhead.

---

## Confidence Gates

Suggested thresholds:

| Confidence | Behavior |
|-----------|----------|
| `>= 0.85` and `official_live` | Propose confirmable candidate |
| `0.70–0.84` or source ambiguity | Propose candidate with warning or ask clarifying question |
| `< 0.70` | Do not propose; preserve literal command and ask user for full command/letterhead |

Confidence must consider:

- Exact or near-exact command-name match.
- Source authority.
- Whether the page is current.
- Whether the page supports the command role/title.
- Whether the address/letterhead lines are explicit or inferred.
- Whether multiple sources conflict.

---

## Search Scope Guardrails

Future lookup should use narrow, official-source queries such as:

- `site:.mil "<command text>" "Commanding Officer"`
- `site:marines.mil "<command text>"`
- `site:navy.mil "<command text>"`
- `site:usmc.mil "<command text>"`

Avoid broad general-web queries as a first pass.

Do not persist results into a permanent static database. Session-level cache is acceptable only to avoid repeated lookups during the same chat.

---

## Rejection and Re-Suggestion Rules

If the user rejects a candidate:

- Move the candidate to rejected status or equivalent session memory.
- Preserve the original literal command text.
- Do not immediately re-suggest the same resolved value/source in the same session.
- Ask for the full command name, command letterhead, or user-provided source.

---

## Letterhead Guardrails

Letterhead is higher-risk than command title expansion.

Only apply source-backed letterhead after confirmation when all are true:

1. The candidate applies to the `from` command.
2. `source_tier == "official_live"`.
3. The source supports the activity name and address.
4. The authority line is valid under existing validator behavior.
5. The user confirms the candidate.

Do not infer letterhead from the `to` line.
Do not infer letterhead from unofficial or ambiguous sources.
Do not bypass existing letterhead validator behavior.

---

## Proposed Implementation Phases

### L.31W — Live Lookup Adapter Skeleton

- Add an adapter module or function stub.
- Keep default disabled unless explicitly configured.
- Preserve L.31T fake adapter test path.
- Add unit tests proving no auto-apply.

### L.31X — Official Source Search Integration

- Add actual official-source search function.
- Restrict to official domains first.
- Return provenance-rich candidates.
- Add deterministic mocked tests.

### L.31Y — Source Quality and Conflict Handling

- Add confidence scoring.
- Handle conflicting official sources.
- Handle archived/outdated results.
- Ensure ambiguous results ask the user rather than guessing.

### L.31Z — Live Lookup End-to-End Smoke

- Optional integration smoke gated behind configuration.
- Deterministic offline smoke remains the required baseline.
- Live smoke may be advisory because network conditions can vary.

---

## Acceptance Criteria for Future Implementation

A future live lookup implementation should prove:

- Controlled aliases still bypass lookup.
- Unknown unresolved commands remain literal.
- Live results are candidate-only.
- Provenance fields are present.
- No source-backed payload mutation occurs before confirmation.
- Confirmation applies only the confirmed candidate.
- Rejection prevents immediate re-suggestion.
- Letterhead applies only for confirmed `official_live` From candidates.
- Renderer, validator, approval, and regression suites remain clean.

---

## Recommended Next Phase

Proceed with **L.31W — Live Lookup Adapter Skeleton** only after this planning checkpoint is accepted.

L.31W should still avoid real web lookup until the adapter boundary and config flag are in place and tested.
