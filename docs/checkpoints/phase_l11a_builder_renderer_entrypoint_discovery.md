# Phase L.11A Conversational Builder Renderer Entry-Point Discovery Checkpoint

**Date:** 2026-06-13  
**Commit:** `298ea685535ca826d2f1bfdfa9b87c053bfd63f6`  
**Phase:** L.11A  
**Purpose:** Identify the correct existing PDF renderer entry point before implementing the builder `/render` command.

---

## Renderer Location

| Property | Value |
|----------|-------|
| File | `src/pdf_v6_render.py` |
| Size | 75,064 bytes (1,755 lines) |
| Last modified | 2026-05-26 |

---

## Entry-Point Contract

```python
def main(input_path=None, output_path=None):
    """
    Load JSON payload from input_path, normalize via letter_model_v6,
    and render a SECNAV v6 letter PDF to output_path.
    """
```

### Input

- `input_path`: path to a JSON file containing a letter payload dict
  - If relative, resolved against repo root
  - Default: `examples/v6_sample_letter.json`
- The JSON must contain fields the renderer expects (from, to, subj, body, signature, etc.)

### Output

- `output_path`: path where the PDF will be written
  - If relative, resolved against repo root
  - Default: `output/v6_test_letter.pdf`
- Output directory is auto-created via `os.makedirs(..., exist_ok=True)`

### Return behavior

- Prints `=== PDF BUILD ===`, `PASS`, and output filename on success
- Prints `FAIL` and reason on failure
- No return value (prints to stdout)

---

## Internal Call Chain

```
main(input_path, output_path)
  → json.load(f)                    # load payload
  → normalize_payload(payload)      # from letter_model_v6
  → validate_body(normalized)       # from body_v6_validate
  → resolve_letterhead(normalized)  # from letterhead_v6_resolve
  → detect_marker_level(...)        # from body_v6_parse
  → validate_joint_letter(...)      # from joint_letter_validate
  → draw_body_block(...)
  → draw_signature_block(...)
  → draw_page_number(...)
  → canvas.save()
```

---

## Dependencies

### Python packages
- `reportlab` (required — canvas, pagesizes)
- `fitz` / PyMuPDF (optional — used by L.6 runner for verification, not by renderer itself)

### Project modules (all in `src/`)
- `letter_model_v6.normalize_payload`
- `body_v6_validate.validate_body`
- `letterhead_v6_resolve.resolve_letterhead`
- `body_v6_parse.detect_marker_level`
- `joint_letter_validate.validate_joint_letter`

---

## How L.6 Dry-Run Calls It

```python
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
    json.dump(normalized_payload, tf, indent=2)
    tmp_input = tf.name

output_pdf = str(_REPO_ROOT / "output" / "phase_l6_dry_run.pdf")
os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

subprocess.run(
    [sys.executable, str(_REPO_ROOT / "src" / "pdf_v6_render.py"),
     tmp_input, output_pdf],
    capture_output=True, text=True,
)
```

Pattern: write payload JSON to temp file, invoke renderer as subprocess with JSON path and PDF path.

---

## Builder `/render` Implementation Recommendation

Based on this discovery, the builder CLI `/render` command should:

1. Ensure payload is finalized (or auto-finalize if allowed)
2. Write finalized payload to a temp JSON file
3. Invoke `src/pdf_v6_render.py` as a subprocess:
   ```python
   subprocess.run([sys.executable, renderer_path, tmp_json, output_pdf], ...)
   ```
4. Report the output path or dependency skip
5. Clean up temp JSON file
6. Do NOT modify `src/pdf_v6_render.py` or any renderer/layout internals

---

## Risks Identified

| Risk | Mitigation |
|------|------------|
| Renderer may fail if payload shape differs from sample | Use builder's `finalize()` to ensure normalized shape |
| Signature must be dict, not list | Already fixed in L.9 |
| reportlab may be missing | Detect and report skip, do not treat as failure |
| Temp JSON cleanup on error | Use `try/finally` or `tempfile` context manager |

---

## Prohibitions Verified

- No renderer/layout files modified
- No builder behavior modified
- No CCI config/severity changes
- No validator/catalog changes
- No Phase F/G command-layer changes
- No intake policy/questions JSON changes
- No generated PDFs committed
- No logs or unsanitized material committed

---

## Recommended Next Phase

`Phase L.11B  Builder PDF Export Command Implementation`

Goal: Add `/render <output.pdf>` command to `tools/run_phase_l7_conversational_builder_cli.py` using the discovered `src/pdf_v6_render.py` entry point.

---

End of Phase L.11A checkpoint.
