# Phase L.32A — Official Provider Interface Planning

**Status:** accepted
**Baseline:** e26e472 (Tools: Fix L.31Z smoke test assertions for reject/confirm response shapes)
**Date:** 2026-08-14

## 1. Provider Purpose

The provider supplies source-backed command identity candidates to the
`official_command_lookup_adapter`.  It does **not** mutate Hermes state, does
**not** apply fields to a letter payload, and does **not** bypass the
confirmation gate.  Every result is a *candidate* — the adapter decides
whether to propose it, and the user must confirm before any field is applied.

## 2. Provider Callable Contract

```python
SearchProvider = Callable[[str, str, dict[str, Any]], Iterable[dict[str, Any]]]
```

**Signature:**

```python
provider(command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]
```

**Parameters:**

| Parameter      | Type                | Description                                      |
|----------------|---------------------|--------------------------------------------------|
| `command_text` | `str`               | Raw command text from the user (e.g. `"Naval Example Command"`) |
| `role`         | `str`               | `"from"` or `"to"`                               |
| `state`        | `dict[str, Any]`    | Current Hermes chat state (read-only for provider) |

**Returns:** zero or more raw source result dictionaries.

The provider is a **pure data source**.  It must not mutate `state`, must not
call Hermes tools, and must not produce side effects.

## 3. Required Raw Result Fields

Every raw result dictionary that the adapter may turn into an apply-ready
candidate **must** include all of:

| Field              | Type                | Description                                      |
|--------------------|---------------------|--------------------------------------------------|
| `resolved_value`   | `dict[str, str]`    | The resolved command identity fields             |
| `source_tier`      | `str`               | One of the accepted source tiers (see §4)        |
| `source_title`     | `str`               | Human-readable source label                      |
| `source_url`       | `str`               | URL of the source page                           |
| `confidence`       | `float`             | 0.0–1.0 confidence score                        |

**`resolved_value` requirements by role:**

| Role   | Required field | Optional fields (From only)                       |
|--------|---------------|----------------------------------------------------|
| `from` | `from`        | `letterhead_top_line`, `letterhead_activity`, `letterhead_address` |
| `to`   | `to`          | *(none)*                                           |

**Forbidden in `resolved_value` for To candidates:**

- `letterhead_top_line`
- `letterhead_activity`
- `letterhead_address`
- `unit_identity`

If any required provenance field is missing, the adapter must **not** propose
the candidate.  The literal user text is preserved and no letterhead is
invented.

## 4. Source Tiers

| Tier                  | Description                                           | Apply-ready? |
|-----------------------|-------------------------------------------------------|--------------|
| `official_live`       | Current official .mil / .gov page                     | Yes, if confidence ≥ 0.85 and URL is official |
| `official_archived`   | Archived official source (e.g. Wayback, cached .mil)  | Yes, with caution — limitation must explain archival/current-validity concern |
| `secondary_credible`  | Credible non-official source (e.g. .edu, .org)        | **No** — must not become an apply-ready official candidate |
| `user_provided`       | Explicitly supplied by user or test state             | Yes, but requires confirmation; must **never** be treated as `official_live`; must not auto-apply letterhead unless user explicitly provided all three letterhead fields and confirmed |
| `unresolved`          | Lookup failed, timed out, or produced conflicting results | **No** — must not become an apply-ready candidate |

**Apply-ready candidate rules:**

- `official_live` may propose if `confidence >= 0.85` **and** source URL is
  an official domain (see §5).
- `official_archived` may propose only with caution if confidence/source
  quality passes **and** limitation text explains the archival/current-validity
  concern.
- `user_provided` may be recorded/proposed only when deliberately supplied
  and must **never** be treated as `official_live`.  It does not outrank
  `official_live`.
- `secondary_credible` and `unresolved` must **not** become apply-ready
  official candidates.
- Conflicting results (two or more official results with different resolved
  command titles for the same field) must **not** produce an apply-ready
  candidate.

## 5. Allowed Official Domains

This is a **source class** definition, not a static command database.  No
hardcoded list of commands, units, or letterhead values is permitted.

**Allowed as official sources:**

- `*.mil` (all .mil domains)
- `navy.mil`
- `marines.mil`
- `usmc.mil`
- `defense.gov`
- `dod.mil`
- Official command-hosted pages under the above domains

**Disallowed as official sources:**

- Wikipedia
- Social media (Twitter/X, Facebook, LinkedIn, etc.)
- Generic commercial directories
- Unofficial base guides
- News articles (unless used only as non-apply-ready context)
- Cached snippets without accessible provenance
- **Static local command database** (explicitly prohibited)

## 6. Provider Ranking Rules

When a provider returns multiple results, the adapter ranks them by:

1. **Source tier** — `official_live` > `official_archived` > `secondary_credible` > `user_provided` > `unresolved`
2. **Confidence** — higher confidence ranks higher within the same tier
3. **Domain authority** — `.mil` > `.gov` > other official domains
4. **Exact command-name match** — exact match on the input text ranks higher than partial
5. **Current/contact/about page relevance** — pages explicitly about the command rank higher than pages that merely mention it
6. **Address completeness for From letterhead** — results with all three letterhead fields rank higher for From candidates

**Conflict rule:** Never choose between conflicting official results with
different resolved command titles.  If two `official_live` results disagree on
the resolved `from` or `to` value, produce a conflict report (see §10), not
an apply-ready candidate.

## 7. Letterhead Rules

### From Candidates

- May include letterhead **only** when **all three** fields are source-backed:
  - `letterhead_top_line`
  - `letterhead_activity`
  - `letterhead_address`
- **Incomplete letterhead must be omitted** from the candidate's
  `resolved_value`.
- The `source_limitation` must explain that letterhead was not complete or
  source-confirmed.
- Confirmation applies From only when letterhead is incomplete; Hermes must
  still ask for missing letterhead details before render.

### To Candidates

- **Never** carry letterhead fields.
- `source_limitation` should state: *"To-line candidates do not set
  letterhead; confirmation mutates only the To field."*
- Confirmation mutates only the `to` field; all other fields (From,
  letterhead, etc.) are preserved.

## 8. Timeout / Error Behavior

The provider must **fail closed**:

| Condition        | Behavior                                                    |
|------------------|-------------------------------------------------------------|
| Timeout          | Return no results, or return `unresolved` metadata only     |
| Network error    | Return no results, or return `unresolved` metadata only     |
| Parse error      | Return no results, or return `unresolved` metadata only     |
| Incomplete provenance | Do not propose candidate; preserve literal user text   |
| Missing letterhead   | Do not invent letterhead                                |

**Recommended timeouts:**

- Per-source/search attempt: short, bounded (e.g. 5–10 seconds)
- Total lookup budget: suitable for interactive chat (e.g. 15–30 seconds
  aggregate)
- The adapter itself does not enforce timeouts; the provider is responsible
  for its own timeout behavior.

## 9. Fixture / Deterministic Mode

All smoke tests use a **fixture mode** with these properties:

- **Injected provider** — `set_official_command_search_provider(fake_provider)`
  replaces the real search provider with a deterministic fake.
- **No internet** — the fake provider returns hardcoded result dictionaries;
  no network calls are made.
- **Deterministic result dictionaries** — every test controls exactly what
  results the provider returns.
- **No static command database** — the fake provider is a simple list of
  result dicts, not a lookup table of real commands.
- **All live behavior gated** — `SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP`
  controls whether the adapter calls the provider at all.  When unset, the
  adapter returns `None` without calling the provider.

## 10. Conflict Metadata

When two or more official results conflict on the resolved `from` or `to`
value, the adapter may produce a **non-apply-ready conflict report** with this
shape:

```json
{
  "candidate_type": "command_lookup_conflict",
  "input_text": "Naval Example Command",
  "field": "from",
  "source_tier": "unresolved",
  "conflicts": [
    {
      "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
      "source_title": "Official .mil Page A",
      "source_url": "https://www.example.navy.mil/A/",
      "confidence": 0.91
    },
    {
      "resolved_value": {"from": "Commander, Naval Example Command"},
      "source_title": "Official .mil Page B",
      "source_url": "https://www.example.navy.mil/B/",
      "confidence": 0.90
    }
  ],
  "source_limitation": "Source conflict detected; user must provide or confirm the correct command."
}
```

**Rules:**

- This must **not** be treated as an apply-ready candidate.
- It must **not** appear in `source_backed_candidates.pending`.
- It may be returned as metadata for future UI use.
- The user-facing message must ask the user to provide or confirm the correct
  command, and must **not** imply a result was selected.

## 11. User-Facing Prompt Requirements

### Pending Candidate Prompt

When a candidate is pending, the assistant response must include:

- **Field:** "From" or "To"
- **Source title:** the human-readable source label
- **Resolved value:** the proposed command identity
- **Source limitation:** why confirmation is required
- **Confirmation language:** "Confirm" or "confirmation required"

Example:

> I found an official-source From candidate from *Naval Example Command
> Official .mil Page*: **Commanding Officer, Naval Example Command**.
> Official-source candidate from .mil page; user confirmation required before
> applying.  Reply "confirm candidate" to apply or "reject candidate" to
> decline.

### Conflict Prompt

When a conflict is detected, the prompt must **not** imply a result was
selected:

> I found conflicting official sources for "Naval Example Command".  Please
> provide or confirm the correct command name and any letterhead details.

## 12. Acceptance Criteria

- [x] This document exists at `docs/checkpoints/phase_l32a_official_provider_interface_planning.md`
- [x] Document explicitly prohibits static command database behavior (§5)
- [x] Document preserves candidate-only confirmation behavior (§1, §3, §11)
- [x] Document preserves live gate (§9, adapter `SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP`)
- [x] Document distinguishes `official_live`, `official_archived`, `secondary_credible`, `user_provided`, `unresolved` (§4)
- [x] Document defines To letterhead stripping (§3, §7)
- [x] Document defines incomplete From letterhead behavior (§7)
- [x] Document defines timeout/error fail-closed behavior (§8)
- [x] Document defines fixture mode (§9)
- [x] Document defines provider callable contract (§2)
- [x] Document defines source tiers and allowed/disallowed sources (§4, §5)
- [x] Document defines conflict metadata shape (§10)
- [x] All existing smokes pass (L.31Z, L.31Y, L.31X-1, L.31X, and 11 regression suites)
