# Phase L.29E — Live Lookup Browser Requirement Checkpoint

Date: 2026-06-17  
Commit: (documentation-only; commit hash TBD)

---

## Summary

Phase L.29E is a documentation-only phase that documents the external tooling gap preventing Hermes from reliably retrieving official `.mil` / SECNAV sources for live candidate creation.

No source code was modified. No renderer, validator, CCI config, or command layer changed.

---

## What Was Documented

### 1. Live Lookup Need
Unit names, command relationships, addresses, COs, and SSIC codes change. The project must not maintain a static database.

### 2. L.29D-2 Findings
- Wikipedia retrieval: works
- archive.org retrieval: works  
- curl HTTPS: works
- Official `.mil` / SECNAV: **blocked by WAF/CDN/anti-bot**
- Browser automation: **CDP unavailable**
- SSIC: **no retrievable official source**
- MCAS New River: only Wikipedia reachable
- MISSA: direct `.mil` verification failed

### 3. Required Capability
- Real browser with JavaScript execution
- Official `.mil` / `navy.mil` / `secnav.navy.mil` access
- Structured extraction (URL, title, snippet, timestamp)
- Archive.org fallback
- Five-tier source quality tracking

### 4. Source Quality Tiers
| Tier | Label |
|---|---|
| 1 | Official live `.mil` |
| 2 | Official archived / archive.org |
| 3 | Secondary credible (Wikipedia, etc.) |
| 4 | User-provided |
| 5 | Unresolved |

### 5. Candidate Creation Rules
- No source URL = no source-backed candidate
- `requires_user_confirmation=true` always
- Tier 3+ must be visibly marked as secondary
- Never auto-apply

### 6. Browser/Tooling Options
- Playwright / Playwright MCP
- Chrome/Edge remote debugging (CDP)
- Hermes built-in browser tools
- Archive.org fallback
- Local reference cache (supplement only)

### 7. Out of Scope
- Static command/unit database
- WAF bypass
- Non-public scraping
- Sensitive data storage
- Renderer/CCI changes

### 8. Recommended Next Phase
**Phase L.29F — Browser-Capable Lookup Harness Discovery**
Evaluate which browser/MCP/CDP option Hermes can use to reach official sources.

---

## Files Changed

- `docs/live_lookup_browser_requirement.md` — new requirement document
- `docs/PROJECT_STATUS.md` — updated with L.29E entry
- `docs/planning/correction_memory_and_rule_promotion_plan.md` — updated next phase to L.29F
- `docs/checkpoints/phase_l29e_live_lookup_browser_requirement_checkpoint.md` — this file

## Files NOT Changed

- No Python/JavaScript source code
- No renderer files
- No CCI config/severity files
- No static database
- `docs/BOOTSTRAP.md` — untouched
- `docs/HERMES_INSTRUCTIONS.md` — untouched

---

*End of checkpoint.*
