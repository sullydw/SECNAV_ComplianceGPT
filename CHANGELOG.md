# Changelog

All notable changes to SECNAV ComplianceGPT are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Changed
- Body paragraph spacing: switched from "spacing after" to "spacing before" approach
- HEADER → BODY boundary: reduced from 1 line to 0 lines

### Fixed
- Removed double-spacing effect between body paragraphs (issue: still visually too large)

---

## 2026-05-04

### Added
- GitHub repository: https://github.com/sullydw/SECNAV_ComplianceGPT
- Initial commit: 44 files (src/, rules_v6/, examples/)
- `docs/PROJECT_STATUS.md` - persistent project context

### Changed
- `src/pdf_v6_render.py` - BOUNDARY_SPACINGS[("HEADER", "BODY")] = 0
- `src/pdf_v6_render.py` - Body spacing now applied before paragraph (i > 0)

### Fixed
- GitHub authentication and remote push workflow
- PDF build passing with debug output

---

## 2026-05-01

### Added
- Initial v6 PDF renderer prototype (`src/pdf_v6_render.py`)
- ReportLab-based PDF generation
- H-series letterhead rendering
- Body paragraph parsing and validation
