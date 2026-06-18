# Live Lookup Browser Integration Requirement

Version: L.29E  
Date: 2026-06-17

---

## 1. Why Live Lookup Is Needed

SECNAV correspondence frequently references units, commands, addresses, and official publications that change over time:

- Unit names and designations are reorganized, deactivated, or renamed.
- Commanding officers rotate on regular schedules.
- Installations update their mailing addresses and ZIP codes.
- SECNAV Manuals and Directives are revised.
- SSIC codes and definitions evolve.

**SECNAV_ComplianceGPT must not maintain a static command or unit database.** Such a database would become stale, would require ongoing manual curation, and would carry the risk of producing letters with outdated or incorrect routing information.

Instead, Hermes should retrieve current source evidence from official or credible public sources and package that evidence as structured `CANDIDATE_V1` objects. The user then confirms or rejects each candidate before it ever modifies the draft payload. This keeps the builder honest, traceable, and current without imposing a maintenance burden.

---

## 2. What L.29D-2 Proved

L.29D-2 tested live lookup capability in the current Hermes/Windows environment:

| Capability | Result |
|---|---|
| Candidate infrastructure (L.29C) | Works correctly |
| curl HTTPS | Functional |
| Wikipedia retrieval | Works |
| archive.org retrieval | Works (PDFs downloadable) |
| Official `.mil` sites (raw curl) | **Blocked by WAF/CDN** |
| `secnav.navy.mil` | **Anti-bot challenge page** |
| Browser automation (CDP) | **Unavailable in this environment** |
| SSIC official source retrieval | **Blocked — no retrievable content** |
| MCAS New River official `.mil` | **Empty response / HTTP 0** |
| MISSA direct `.mil` verification | **Access Denied by Akamai EdgeSuite** |

**Key finding:** Wikipedia and archive.org can be reached, but the most authoritative sources — `.mil` command pages, SECNAV Directives, and DoD directories — are inaccessible without a real browser that can execute JavaScript and pass WAF challenges.

---

## 3. Required Lookup Capability

To support production-quality live lookup candidates, the following capabilities are required:

### 3.1 Real Browser Session
- JavaScript execution to pass anti-bot challenges.
- Cookie and TLS handling compatible with CDN/WAF front-ends.
- Ability to render pages and extract visible text.

### 3.2 Official Source Access
- Must reach `.mil`, `navy.mil`, `marines.mil`, and `secnav.navy.mil` pages.
- Must handle PDF downloads from official repositories.

### 3.3 Structured Extraction
- Page title.
- Canonical source URL.
- Relevant text snippet or quoted passage.
- Retrieval timestamp (`lookup_timestamp`).

### 3.4 Fallback Strategy
- When official live page is blocked, attempt `web.archive.org` snapshot.
- When archive is unavailable, degrade to known public reference (clearly marked).

### 3.5 Source Quality Tracking
Every retrieved source must be tagged with a tier so that candidates present confidence appropriately.

---

## 4. Source Quality Tiers

| Tier | Label | Description | Example |
|---|---|---|---|
| 1 | Official live | Direct `.mil` or `navy.mil` / `secnav.navy.mil` source, retrieved live | `www.mcasnewriver.marines.mil/` |
| 2 | Official archived | Archive.org snapshot or `.mil` PDF mirror | `archive.org/.../manpower.usmc.mil_*.pdf` |
| 3 | Secondary credible | Wikipedia, officially-affiliated reference pages | `en.wikipedia.org/wiki/MCAS_New_River` |
| 4 | User-provided | Information supplied by the operator, not externally sourced | Typed directly by user |
| 5 | Unresolved | No source could be found; requires user to provide | N/A |

**Rules:**
- Tier 1 → confidence ≥ 0.90, confirmation still required.
- Tier 2 → confidence 0.75–0.90.
- Tier 3 → confidence 0.60–0.80, visibly marked as secondary.
- Tier 4 → confidence 0.40–0.70, always confirmed by user.
- Tier 5 → no candidate created.

---

## 5. Candidate Creation Rules

1. **No source URL → no source-backed candidate.**
2. Every candidate must include:
   - `source_url`
   - `source_title`
   - `lookup_timestamp`
   - `confidence`
   - `requires_user_confirmation`: always `true`
3. Tier 3 or lower must include a visible note: *"This candidate is based on a secondary source and requires user confirmation."*
4. **Never auto-apply live lookup results.**
5. Use `candidate-add` → user review → `candidate-confirm` / `apply-resolved` only after explicit approval.
6. Do not populate `signature_block` or `commanding_officer` from unverified lookups.

---

## 6. Browser / Tooling Options to Evaluate

| Option | Pros | Cons |
|---|---|---|
| **Playwright / Playwright MCP** | Full browser automation, JS execution, stealth, supports Chromium/Firefox/WebKit | Requires browser binary and Node dependency |
| **Chrome/Edge Remote Debugging (CDP)** | Native browser, minimal footprint | Needs running browser instance; CDP port config |
| **Hermes existing browser tools** | Already integrated in environment | Availability depends on profile/environment |
| **Archive.org fallback** | No WAF blocking, persistent snapshots | Snapshots may lag behind live data |
| **Local reference cache** | Fast, offline, no network dependency | Can become stale; must be refreshed periodically |

**Recommended evaluation order:**
1. Test whether Hermes' built-in browser/MCP tooling can reach a `.mil` page.
2. If not, evaluate Playwright MCP skill installation.
3. If still blocked, formalize archive.org fallback as primary path for official data.
4. Local reference cache may supplement but must never replace live lookup.

---

## 7. Out of Scope

- **Static command/unit database:** Do not build or commit a curated list of units, commands, or SSIC codes.
- **WAF bypass:** Do not attempt to circumvent security controls on official sites.
- **Private/non-public scraping:** Do not target portals requiring authentication or CAC.
- **Sensitive data storage:** Do not cache PII, roster data, or classified information.
- **Renderer changes:** No modification to `src/pdf_v6_render.py` or layout files.
- **CCI severity/config changes:** No modification to `rules_v6/CCI/`, `cci_severity_mapper.py`, or `config/cci_enforcement_config.json`.

---

## 8. Recommended Next Implementation Phase

**Phase L.29F — Browser-Capable Lookup Harness Discovery**

Purpose: Determine which browser/MCP/CDP option Hermes can actually use locally to retrieve official public sources and return structured source evidence.

Scope:
1. Evaluate Hermes native `browser` toolset for `.mil` page access.
2. Evaluate `playwright-mcp` skill availability and installation.
3. If both fail, document archive.org fallback as the working path.
4. Produce a minimal reproducible lookup test against one known `.mil` page (e.g., `marines.mil` homepage).
5. Do not modify source code unless a working browser path is confirmed.
6. Do not create candidates from unverified sources.

Deliverable: `docs/checkpoints/phase_l29f_browser_capable_lookup_harness_checkpoint.md`

---

*End of document.*
