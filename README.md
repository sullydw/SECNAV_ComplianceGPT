# SECNAV_ComplianceGPT

Generate SECNAV M-5216.5 compliant military correspondence as PDF.

## Current Scope

Chapters 7-10 of SECNAV M-5216.5 are implemented and regression-protected for the current project scope:

- C7 standard letters, continuation pages, and joint letters
- C8 multiple-address letters using To-line, Distribution, and To-plus-Distribution formats
- C9 new-page endorsements
- C10 Memorandums for the Record and plain-paper From-To memorandums

Figure 9-1 same-page endorsements and additional C10 memorandum types are deferred or outside the current scope. See `docs/PROJECT_STATUS.md` for the full milestone tracker.

## Quick Start

Render a sample PDF:

```bash
python src/pdf_v6_render.py examples/v6_sample_letter.json output/v6_test_letter.pdf
```

## Regressions

```bash
python tools/run_c7_phase1_regression.py
python tools/run_c8_regression.py
python tools/run_c9_regression.py
python tools/run_c10_regression.py
```

## Documentation

- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) — detailed status, audit results, and deferred work
- [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md) — system philosophy and interaction model
- [docs/checkpoints/](docs/checkpoints/) — per-figure layout checkpoint notes
- [docs/layout_profiles/](docs/layout_profiles/) — PDF layout audit profiles

## Architecture

- **Renderer:** `src/pdf_v6_render.py` (single ReportLab-based PDF renderer)
- **Validators:** `src/c7_validate.py`, `src/c8_validate.py`, `src/c9_validate.py`, `src/c10_validate.py`
- **Layout audits:** `tools/audit_pdf_layout.py` with JSON profiles for coordinate-based checks
- **Rules catalog:** `rules_v6/C7/`, `rules_v6/C8/`, `rules_v6/C9/`, `rules_v6/C10/` with standardized schema and index files

## Disclaimer

This is an independent compliance tooling project and is not official United States Department of Defense software. Always verify generated correspondence against the current SECNAV M-5216.5 manual and your command's administrative procedures.
