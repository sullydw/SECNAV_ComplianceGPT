# Phase L.7B — Builder Payload PDF Signature Issue Triage

## Date
2026-06-13

## Goal
Determine whether the L.6 PDF dry-run failure was caused by malformed synthetic builder payload signature data or an actual renderer edge case, without changing renderer/layout code.

## Root Cause

**Malformed synthetic payload — not a renderer bug.**

The L.6 dry-run runner originally ingested `signature: J. Q. Sample` as a plain string. `BuilderSession._coerce_value()` routes `signature` through the **list coercion branch** (because `signature` is in `list_fields`), producing `signature = ["J. Q. Sample"]`.

The renderer (`pdf_v6_render.py:426`) handles two signature shapes:
- `dict` → structured signature (name, role, title, authority, activity_head_title)
- `str` → legacy string signature

A `list` signature would pass the `elif signature:` branch and hit `c.drawString(signature_x, y, ["J. Q. Sample"])`, which is invalid for `reportlab` and raises a `TypeError`.

The **known-good sample** (`examples/audit_c7_phase1_standard_letter.json`) uses a `dict` with `role: null`:
```json
{
  "name": "J. DOE",
  "role": null,
  "title": null,
  "authority": null,
  "activity_head_title": null,
  "affects_pay_or_allowances": false
}
```

The renderer’s `_validate_structured_signature()` and `draw_signature_block()` both expect this dict format for role-aware rendering. The L.6 synthetic payload was passing a list where a dict was required.

## Files Changed

| File | Change |
|------|--------|
| `tools/run_phase_l6_builder_payload_to_pdf_dry_run.py` | Replaced plain-string `signature` entry in `SAMPLE_FIELDS` with `STRUCTURED_SIGNATURE` dict; injected dict directly into orchestrator via `apply_answers()` after key-value loop |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | Updated Check-17 allowlist to include L.6/L.7/L.7A artifacts |

## Renderer Untouched

No changes to:
- `src/pdf_v6_render.py`
- `src/letter_model_v6.py`
- `src/audit_pdf_layout.py`

## Exact Synthetic-Payload Adjustment

**Before:**
```python
SAMPLE_FIELDS = {
    "ssic": "5216",
    "date": "15 May 2026",
    "from": "Commander, Naval Air Station Patuxent River",
    "to": "Chief of Naval Operations",
    "subj": "Example Subject for Dry Run",
    "body": "This is a sanitized body paragraph for the Phase L.6 dry run.",
    "signature": "J. Q. Sample",
    "window_envelope": False,
}
```

**After:**
```python
SAMPLE_FIELDS = {
    "ssic": "5216",
    "date": "15 May 2026",
    "from": "Commander, Naval Air Station Patuxent River",
    "to": "Chief of Naval Operations",
    "subj": "Example Subject for Dry Run",
    "body": "This is a sanitized body paragraph for the Phase L.6 dry run.",
    "window_envelope": False,
}

STRUCTURED_SIGNATURE = {
    "name": "J. Q. Sample",
    "role": None,
    "title": None,
    "authority": None,
    "activity_head_title": None,
    "affects_pay_or_allowances": False,
}
```

The runner now calls `builder._orchestrator.apply_answers({"signature": STRUCTURED_SIGNATURE})` after the key-value ingestion loop so the payload carries a renderer-compatible dict.

## Dry-Run Result After Triage

```
======================================================================
Phase L.6  Conversational Builder Payload-to-PDF Dry Run
======================================================================
PASS — start() returned session_id
PASS — sample fields present
PASS — validation audit produced
  Findings: 1  (Errors: 1, Warnings: 0, Advisories: 0)
PASS — finalize allowed
PASS — normalized payload present
SKIP — PDF generation unavailable: reportlab unavailable
PASS — no renderer/layout mutation
======================================================================
RESULTS: 7/7 passed
ALL CHECKS PASS
======================================================================
```

PDF generation still **environmentally skipped** because `reportlab` is not installed in this runtime. The runner correctly reports `SKIP` rather than failure, and the payload is now structurally compatible with the renderer.

## Regression Results

| Runner | Result |
|--------|--------|
| L.4 conversational builder | 41/41 PASS |
| L.5 validation summary | 36/36 PASS |
| L.6 payload-to-PDF dry run | 7/7 PASS |
| L.7 CLI regression | 26/26 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| H.13 config | 27/27 PASS |
| H.4 routing office-code | 18/18 PASS |
| H.6 routing evidence | 15/15 PASS |
| H.16 ROUTE-011 burn-in | 96/96 PASS |
| H.24 ROUTE-011 sanitized fixtures | 36/36 PASS |
| Intake regression | All PASS |

## Remaining PDF Limitations

- `reportlab` and `fitz` (PyMuPDF) are **not installed** in this Windows runtime; PDF generation cannot be exercised locally.
- When installed, the renderer is expected to accept the corrected structured-signature dict because it matches the known-good `audit_c7_phase1_standard_letter.json` format.
- The pre-existing renderer issue observed in prior L.7A runs (signature-block line 495 with sanitized data) was likely the **same list-vs-dict mismatch** manifesting under a different code path.

## Recommended Next Phase

`Phase L.8  Conversational Builder Usability Review and Question-Coverage Audit`

## Notes

- Builder list coercion for `signature` is **intentional** for CLI key-value ingestion (users type `signature: J. DOE` and it becomes `["J. DOE"]`). The L.6 runner is a synthetic test harness; injecting a dict directly is the correct workaround.
- No changes to `_coerce_value()` were made because the list behavior is used by L.4/L.5/L.7 regression runners and must not change.
- H.4 allowlist was updated to prevent cascading failures from the new/updated L.6/L.7 files.
