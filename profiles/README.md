# Local Command Profiles

This directory contains only the **example/template** profile:

- `example_local_profile.json` — fake data only. Do not store real command information in this file.

## Real Profile Storage

Real local command profiles must **not** be stored in this repository.

Use an external directory outside version control:

- **Windows:** `%USERPROFILE%\.secnav\profiles\`
- **Linux/macOS:** `~/.config/secnav/profiles/`

The `src/local_profile.py` module accepts direct file paths, so external profiles are compatible with the existing API.

## Why External?

Real profiles may contain:

- Command names and addresses
- Point-of-contact names, phone numbers, and emails
- Unit identifiers and originator codes
- Local command-specific defaults

These should never be committed to a public repository.

## Example Profile

The committed `example_local_profile.json` is intentionally fake:

- Fake command name: "Example Activity"
- Fake address: "123 Example Road, Example Base, EX 00000"
- Fake phone: "703-555-0100"
- Fake email: "j.doe@example.mil"

## Profile Promotion

When corrections are promoted to a real profile:

- Corrections are written to the profile's `override_rules` array with `source: "user_promoted_correction"`.
- Backups are created automatically (last 10 retained).
- Writes are atomic (temp file + rename).
- No automatic promotion without explicit user confirmation.

## Safety Checklist

- [ ] Real profiles live outside the repository.
- [ ] Real profiles are not gitignored (they are simply not in the repo).
- [ ] Example profile contains only fake/example data.
- [ ] No `--auto-approve` flag exists in promotion logic.
