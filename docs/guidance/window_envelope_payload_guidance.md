# Window Envelope Payload Guidance

**Version:** H.16  
**Date:** 2026-06-08  
**Rule:** `CCI-ROUTE-011` — Every standard letter must have a `"From:"` line, except a letter that will be used with a window envelope.  
**Source:** SECNAV M-5216.5, Chapter 7, Section 6, `"From:" Line`, subparagraph a. General (PDF page 50).

---

## Summary

During the active H.15/H.16 warning pilot, `CCI-ROUTE-011` is enforced at **warning** level. This means a standard letter missing a `from` line will produce a **blocking** finding in the `errors` list.

A standard letter that **intentionally** omits the `from` line because it will use a **window envelope** must be explicitly marked with:

```json
"window_envelope": true
```

Without this flag, the validator treats the missing `from` as a rule violation.

---

## Quick Reference

| Payload type | `from` present | `window_envelope` | Result |
|---|---|---|---|
| Standard letter | Yes | absent or false | **PASS** — no finding |
| Standard letter | No | absent or false | **FAIL** — `CCI-ROUTE-011` in `errors` |
| Window-envelope letter | Yes | `true` | **PASS** — no finding |
| Window-envelope letter | No | `true` | **PASS** — no finding |
| Window-envelope-like letter | No | **missing** | **FAIL** — `CCI-ROUTE-011` in `errors` |

---

## Operator/Data-Quality Risk

If a letter is intended to use a window envelope but the operator forgets to set `"window_envelope": true`, the validator will flag it as missing a `from` line. This is **intentional** — the validator cannot distinguish a genuine window-envelope letter from a standard letter that simply forgot the `from` field.

**Mitigation:** Always tag window-envelope letters explicitly in the payload.

---

## Examples

### 1. Standard Letter with Valid `from`

```json
{
  "doc_type": "DT_STD_LTR",
  "from": "Commanding Officer, USS EXAMPLE",
  "to": ["Chief of Naval Operations (N00)"],
  "subject": "Operational Report",
  "date": "2026-06-08",
  "body": "1. Submit operational report."
}
```

**Result:** PASS — no `CCI-ROUTE-011` finding.

---

### 2. Standard Letter Missing `from`

```json
{
  "doc_type": "DT_STD_LTR",
  "to": ["Chief of Naval Operations (N00)"],
  "subject": "Operational Report",
  "date": "2026-06-08",
  "body": "1. Submit operational report."
}
```

**Result:** FAIL — `CCI-ROUTE-011` appears in `errors`.

---

### 3. Window-Envelope Letter with `window_envelope: true`

```json
{
  "doc_type": "DT_STD_LTR",
  "to": ["Chief of Naval Operations (N00)"],
  "subject": "Administrative Notice",
  "date": "2026-06-08",
  "body": "1. Routine administrative notice.",
  "window_envelope": true
}
```

**Result:** PASS — `CCI-ROUTE-011` is suppressed.

---

### 4. Window-Envelope Letter with `from` and `window_envelope: true`

```json
{
  "doc_type": "DT_STD_LTR",
  "from": "Commanding Officer, USS EXAMPLE",
  "to": ["Chief of Naval Operations (N00)"],
  "subject": "Administrative Notice",
  "date": "2026-06-08",
  "body": "1. Routine administrative notice.",
  "window_envelope": true
}
```

**Result:** PASS — `from` is allowed; the flag simply confirms window-envelope intent.

---

### 5. Window-Envelope-Like Letter Without the Flag (Operator Risk)

```json
{
  "doc_type": "DT_STD_LTR",
  "to": ["Chief of Naval Operations (N00)"],
  "subject": "Administrative Notice",
  "date": "2026-06-08",
  "body": "1. Routine administrative notice."
}
```

**Result:** FAIL — `CCI-ROUTE-011` in `errors`. The operator must add `"window_envelope": true` if this is genuinely a window-envelope letter.

---

## Excluded Document Types

`CCI-ROUTE-011` only applies to **standard letters**. The following document types are **not checked** for a `from` line:

- Memorandums (`DT_MEMO_FROM_TO_PLAIN`, `DT_MEMO_FROM_TO_MEMORANDUM`)
- Memorandum for the Record (`DT_MFR`)
- Endorsements
- Joint letters
- Multiple-address letters
- Any payload with a missing or unknown `doc_type`

---

## Current Config State

| Rule | Effective Severity | Status |
|---|---|---|
| `CCI-ROUTE-011` (From line required) | `warning` | Active warning pilot (H.15/H.16) |
| `CCI-ROUTE-010` (Office code prefix) | `advisory` | Unchanged |

No error-level promotion is authorized for any rule.

---

## Rollback

If the warning pilot must be deactivated immediately, edit `config/cci_enforcement_config.json` and change:

```json
"CCI-ROUTE-011": {
  "effective_severity": "warning",
  ...
}
```

to:

```json
"CCI-ROUTE-011": {
  "effective_severity": "advisory",
  ...
}
```

No validator, catalog, renderer, or command-layer changes are required. The change takes effect on the next validation call because the config is re-read every time.

---

## Related Documents

- `docs/planning/phase_h15_route011_warning_pilot_plan.md` — H.15 warning pilot plan
- `docs/planning/phase_h16_route011_warning_burnin_plan.md` — H.16 burn-in plan
- `docs/checkpoints/phase_h16_route011_burnin_regression_checkpoint.md` — H.16 burn-in checkpoint
- `examples/burnin_h16_route011/` — 90 synthetic burn-in fixtures for testing

---

End of guidance.
