# Phase L.11B Conversational Builder PDF Export Command Checkpoint

**Date:** 2026-06-13  
**Commit:** `485aa03` (L.11A baseline)  
**Phase:** L.11B  
**Purpose:** Add `/render <output.pdf>` command to the conversational builder CLI using the existing `src/pdf_v6_render.py` entry point.

---

## Files Changed

| File | Change |
|------|--------|
| `tools/run_phase_l7_conversational_builder_cli.py` | Added `_render_finalized_payload()` helper; added `/render <output.pdf>` interactive command; added `--render` CLI arg for scripted mode; updated banner/help text |
| `tools/run_phase_l11_builder_pdf_export_regression.py` | **New** — 12-test regression runner |
| `docs/checkpoints/phase_l11b_conversational_builder_pdf_export_command_checkpoint.md` | **New** — This checkpoint doc |

---

## `/render` Command Behavior

### Interactive mode
- User types: `/render output.pdf`
- CLI checks if finalize is allowed via `validation_summary()`
- If blocked (missing fields or pending warnings), prints block reason(s) and aborts
- If allowed, calls `finalize(accept_warnings=...)`
- Writes finalized payload JSON to a temp file (`tempfile.NamedTemporaryFile`)
- Invokes `src/pdf_v6_render.py` as subprocess with JSON path and output PDF path
- Deletes temp JSON in `finally` block
- Prints:
  - `success`: `PDF written: path (size bytes)`
  - `skipped`: `PDF generation skipped: reason` (e.g., reportlab missing)
  - `failed`: `PDF generation failed: reason` + stderr snippet

### Scripted mode
- Added `--render PDF_PATH` CLI arg (requires `--scripted-sample`)
- After `run_scripted_sample()`, if `--render` is provided:
  - Skips render if sample did not finalize
  - Calls `_render_finalized_payload(payload, args.render)`
  - Reports status same as interactive

### Helper: `_render_finalized_payload(payload, output_path)`
- Returns structured dict:
  ```python
  {
      "status": "success" | "skipped" | "failed",
      "output_path": str,
      "reason": str,
      "stdout": str,
      "stderr": str,
  }
  ```
- Checks for `reportlab` import before attempting render
- Creates output directory if missing
- Cleans up temp JSON unconditionally in `finally`

---

## Renderer Invocation Pattern

```python
subprocess.run(
    [sys.executable, str(_REPO_ROOT / "src" / "pdf_v6_render.py"), tmp_json, output_pdf],
    capture_output=True, text=True,
)
```

This is identical to the L.6 dry-run invocation pattern. No renderer code was modified.

---

## PDF Output Behavior

- PDF written to user-specified path or default `output/builder_render.pdf`
- Output directory auto-created
- Generated PDFs are **not committed** (deleted by regression runner or left in ignored `output/`)

---

## Dependency/Failure Handling

| Condition | Behavior |
|-----------|----------|
| reportlab unavailable | Skip with clear message |
| Renderer exits non-zero | Report failure with stderr |
| Finalize not allowed | Block render with reason |
| Warnings pending + not accepted | Block render (same as finalize) |

---

## Regression Results

| Runner | Result |
|--------|--------|
| L.11 PDF export | **12/12 PASS** |
| L.10 demo script | **14/14 PASS** |
| L.9 signature capture | **11/11 PASS** |
| L.7 CLI regression | **26/26 PASS** |
| L.6 PDF dry-run | **7/7 PASS** (PDF generated, 1749 bytes) |
| H.13 config | **27/27 PASS** |
| K.3 SUBJ-002 | **11/11 PASS** |
| Intake regression | **45/45 PASS** |

---

## Prohibitions Verified

- No renderer/layout changes (`src/pdf_v6_render.py` untouched)
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- No error promotion
- No generated PDFs committed (cleaned up after regression)
- No logs or unsanitized material committed

---

## Recommended Next Phase

`Phase L.12  Conversational Builder End-to-End User Demo`

Goal: Create a polished end-to-end demo showing a user going from blank session → key-value input → warning review → finalize → `/render` → finished PDF, suitable for operator review or stakeholder presentation.

---

End of Phase L.11B checkpoint.
