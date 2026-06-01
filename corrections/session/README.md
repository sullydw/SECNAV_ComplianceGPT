Session Correction Stores (Phase A)
======================================

This directory contains per-session JSONL files that store user corrections
temporarily within a single CLI or chat session. Files here are local-only and
must NOT be committed to version control.

Rules:
- Each file is named `{session_id}.jsonl`.
- Each line is a self-contained JSON correction record.
- Files may contain PII (names, commands, routing info). Protect accordingly.
- Retention is advisory (30 days); no automatic cleanup in Phase A.
- Rejected corrections remain in the file but are soft-marked `user_rejected=true`.

Do not manually edit `.jsonl` files while a session is active.
