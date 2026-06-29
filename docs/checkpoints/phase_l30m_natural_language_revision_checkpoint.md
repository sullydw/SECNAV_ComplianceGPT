# Phase L.30M — Natural-Language Draft Revisions

## Baseline Commit
`6486e79` — `Tools: Improve natural-language draft revisions`

## Summary
Phase L.30M extended the `revise` command to support deterministic natural-language revision phrases while preserving the existing key:value revise behavior and all safety guarantees.

## Supported Natural-Language Phrases
- **remove the attachment sentence** / **remove the sentence about the attachment**  
  Removes body paragraphs or lines containing the word "attachment".
- **change the subject to ...**  
  Updates the `subj` field.
- **change the signer to ...**  
  Updates `signature.name`.
- **change the date to ...**  
  Updates the `date` field.
- **change the to line to ...**  
  Updates the `to` field.
- **change the from line to ...**  
  Updates the `from` field.
- **make the body more direct**  
  Removes hedging phrases ("I believe that", "It is suggested that", "In my opinion").
- **make the body more formal**  
  Expands contractions (can't→cannot, won't→will not, don't→do not, i'm→I am, we're→we are).
- **shorten the body**  
  Keeps only the first sentence of each paragraph.

## Behavior Preserved
- Existing `key:value` revise format continues to work unchanged.
- Only allowed draft fields (`subj`, `body`, `date`, `from`, `to`, `signature.name`, `ssic`, `originator_code`) are affected.
- Any draft-relevant payload change clears the preview approval.
- Unsupported instructions fail safely with:  
  `"Unsupported revision instruction. Use key:value format or a supported revision phrase."`
- No broad LLM/freeform rewriting is used — only deterministic regex-based helpers.
- No candidate changes, live lookup, finalize, or render occurs inside revise.
- Unsupported instructions do **not** clear approval (command returns before touching payload).

## Smoke Tests
- `tools/run_phase_l30m_natural_revision_smoke.py` — PASS
  - key:value body revision still works
  - change subject to ... works
  - change signer to ... works
  - remove attachment sentence works
  - approval clears after draft-relevant change
  - unsupported instruction fails safely
  - no candidate change, finalize, render, or lookup occurs

## Files Changed
- `tools/hermes_secnav_tool.py` — added `_apply_natural_revision` helper and regex patterns; updated `cmd_revise` to try natural-language before failing unsupported
- `tools/run_phase_l30m_natural_revision_smoke.py` — new

## Notes
- No renderer/layout changes.
- No validator rule changes.
- No approval gate behavior changes.
- No candidate confirmation behavior changes.
- No CCI config, rule files, or docs modified.
- Commit pushed to origin/main.
