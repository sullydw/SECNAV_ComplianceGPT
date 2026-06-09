# H.24 Sanitized Fixture Directory

This directory contains 32 sanitized/synthetic JSON fixtures for CCI-ROUTE-011 burn-in regression.

## Contents

- `manifest.json` — Single source of truth for expected outcomes.
- 32 fixture payloads (naming: `<category>_<NNN>.json`).

## Categories

| Prefix | Count | Purpose |
|---|---|---|
| `valid_from_` | 4 | Standard letters with valid From line (should not trigger) |
| `missing_from_` | 3 | Missing From field (should trigger) |
| `null_from_` | 2 | Null From value (should trigger) |
| `empty_from_` | 2 | Empty From string (should trigger) |
| `whitespace_from_` | 2 | Whitespace-only From (should trigger) |
| `window_envelope_tagged_` | 3 | Tagged window_envelope=true (should suppress) |
| `window_envelope_missing_flag_` | 3 | Looks like window envelope but untagged (should trigger) |
| `nonstandard_doc_` | 3 | Non-standard document types (should not trigger) |
| `navy_routing_` | 3 | Navy-style routing missing From (should trigger) |
| `marine_routing_` | 3 | Marine Corps-style routing missing From (should trigger) |
| `distribution_combo_` | 4 | Distribution/via/copy-to combos missing From (should trigger) |

## Data Handling

All content is synthetic/sanitized. No real names, units, hull numbers, dates, addresses, phone numbers, emails, signatures, or identifiers are used.

## Expectations

All expected outcomes live in `manifest.json`. Payloads contain only renderer/audit-compatible data.
