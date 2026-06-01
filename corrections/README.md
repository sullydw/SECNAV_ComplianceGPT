# Correction Storage Directory

This directory contains local-only correction memory stores. Nothing in this directory should be committed to the remote repository.

## Session Corrections (`session/`)

Per-session JSONL files that store user corrections for draft reuse within a single session. See `corrections/session/README.md` for details.

- Files: `{session_id}.jsonl`
- Gitignored: `corrections/session/*.jsonl`
- May contain PII and local command data.

## Pending Global Rule Candidate Log

`corrections/pending_corrections.jsonl` is an **append-only** log of corrections classified as `possible_secnav_manual_rule` or `bug_validator_gap`. It captures sanitized candidate records for future human or AI-assisted review.

- **Never committed.** It is gitignored.
- **Never auto-applied.** Every entry requires explicit two-step user confirmation before writing.
- **Sanitized before write.** Raw command names, personnel names, EDIPI, SSN, DoD ID, UIC, hull/tail/building/room numbers, emails, phones, and addresses are abstracted or redacted.
- **Local-only.** It exists on the user's machine only.
- **Phase D scope only.** This log does not implement global rule promotion, validator changes, or renderer changes.

For lifecycle details, see `docs/planning/phase_d_pending_global_rule_candidate_log_plan.md`.

## Approved Rule Promotions

Future: `corrections/approved_rule_promotions.json` (gitignored, not yet implemented).
