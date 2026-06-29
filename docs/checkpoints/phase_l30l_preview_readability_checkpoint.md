# Phase L.30L — Preview Readability Polish

## Baseline Commit
`b684371` — `Tools: Improve draft preview readability`

## Summary
Phase L.30L improved the readability of preview output without changing any workflow behavior, gating logic, or approval mechanics.

## Changes
- `_build_preview_text` in `tools/hermes_secnav_tool.py` rewritten with structured section headers and consistent separator styling.

### BUILD STATUS sections added/improved
- **KNOWN FIELDS** — lists populated fields
- **MISSING / BLOCKING ITEMS** — distinguishes preview-required vs validation-required missing fields
- **PENDING CANDIDATES** — count and list of awaiting-confirmation candidates
- **CONFIRMED SOURCE-BACKED FACTS** — count and list of confirmed candidates
- **APPROVAL STATUS** — shows whether approved, stale, or unavailable
- **NEXT ACTION** — clear recommendation text

### DRAFT PREVIEW sections added/improved
- **DOCUMENT HEADER** — SSIC, originator_code, date
- **ADDRESSES** — from, to, via
- **SUBJECT** — standalone subject line
- **BODY** — with improved review label: `[AI-DRAFTED OR USER-PROVIDED — REVIEW REQUIRED]`
- **SIGNATURE** — name, title, role
- **PENDING CANDIDATES** and **CONFIRMED SOURCE-BACKED FACTS**
- **VALIDATION SUMMARY** — errors, warnings, block reason
- **APPROVAL STATUS** and **NEXT ACTION**
- Approval banner and footer use consistent "APPROVED FOR FINALIZE" / "NOT FINAL" wording.

## Behavior Unchanged
- Preview gate rule: still requires from, to, subj, body, date, signature
- Approval hash behavior: unchanged
- Finalize/render gate: unchanged
- Candidate confirmation behavior: unchanged
- Preview remains read-only (no save, no mutation, no candidate state change)

## Smoke Test
- `tools/run_phase_l30l_preview_readability_smoke.py` passes
  - verifies build_status and draft_preview modes still work
  - verifies approval banner (approved vs not approved)
  - verifies approval gate unaffected
  - verifies preview remains read-only
  - verifies new section headers appear

## Files Changed
- `tools/hermes_secnav_tool.py`
- `tools/run_phase_l30l_preview_readability_smoke.py`

## No Changes To
- Renderer/layout
- Validator rules
- CCI config
- Rule files
- Candidate behavior
- Approval hash mechanics
- Finalize/render gate

## Status
COMPLETE — targeted smoke tests passed; pushed to origin/main.
