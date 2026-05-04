# Rules v6 — Compact Coded Rule Records

## Overview

v6 of the SECNAV ComplianceGPT rule schema uses **compact coded rule records** — short, machine-friendly codes for document types, rule types, sections, severities, actions, and sources. This keeps rule definitions dense, greppable, and easy to diff while remaining human-readable with the help of `lookup_tables.json`.

## File Structure

```
rules_v6/
├── lookup_tables.json      # Code-to-description mappings for all coded fields
├── README_rules_v6.md      # This file
└── authoring/              # Human-authored CSV rule files
    ├── source_rules.csv    # Rules for source/reference validation
    ├── layout_rules.csv    # Rules for page layout and formatting
    ├── behavior_rules.csv  # Rules for conditional behavior and logic
    └── marker_rules.csv    # Rules for structural markers and anchors
```

## CSV Format

All authoring CSV files share the same header:

```
id,type,dt,sec,condition,action,target,severity,source,status,enabled,notes
```

| Column    | Description                                           |
|-----------|-------------------------------------------------------|
| `id`      | Unique rule identifier (e.g., `SRC-001`, `LO-042`)    |
| `type`    | Rule type code — see `rule_types` in lookup table     |
| `dt`      | Document type code — see `doc_types` in lookup table  |
| `sec`     | Target section code — see `sections` in lookup table  |
| `condition`| Rule condition / expression                           |
| `action`  | Action code — see `actions` in lookup table           |
| `target`  | Target element, field, or pattern                     |
| `severity`| Severity code — see `severity` in lookup table        |
| `source`  | Authority source code — see `sources` in lookup table |
| `status`  | Rule lifecycle status — see `status` in lookup table  |
| `enabled` | `true` or `false` — whether the rule is active       |
| `notes`   | Free-text notes, rationale, or cross-reference        |

## Lookup Tables

`lookup_tables.json` contains the full code-to-description mapping for every coded field. Any new code added to a CSV **must** have a corresponding entry in the lookup table.

### Available Lookup Tables

- **doc_types** — Recognized document types (DD, DI, SECNAVINST, FAR, etc.)
- **rule_types** — Categories of rules (validation, calculation, anomaly, etc.)
- **status** — Rule lifecycle statuses (active, draft, deprecated, disabled, retired)
- **severity** — Impact levels (Error, Warning, Info, Critical)
- **sections** — Document sections (S1-S9, appendices, cover, TOC, etc.)
- **actions** — Actions to take when a rule matches (flag, reject, warn, transform, etc.)
- **sources** — Authoritative sources for rule requirements

## Rule Lifecycle — Retire, Don't Delete

Rules should **never be deleted** from the CSV files. Instead, change their lifecycle state:

- **Disabled** (`status=disabled`, `enabled=false`) — temporarily turned off, intent is to re-enable later.
- **Retired** (`status=retired`, `enabled=false`) — permanently removed from evaluation. Add a note explaining why.
- **Deprecated** (`status=deprecated`, `enabled=false`) — superseded by another rule. Reference the replacement in `notes`.

This preserves audit history, allows rollback, and keeps the rule corpus complete for documentation and training purposes.

## Generating Runtime Formats

The CSV files are for **human authoring and review**. For runtime use, a generation script can:

1. Read all CSV files from `authoring/`
2. Validate codes against `lookup_tables.json`
3. Filter out disabled/retired/deprecated rules
4. Resolve codes to their expanded descriptions
5. Emit a flattened **JSONL** file for the compliance engine

The exact generation script and JSONL schema will be defined separately.

## Quick Start

1. Copy the shared header into a new CSV if you add a rule category file.
2. Define or verify codes in `lookup_tables.json` before using them in rules.
3. Write rules one per row, using the codes from the lookup tables.
4. Review the CSV as a spreadsheet (Excel, Numbers, Google Sheets) for easy collaboration.
5. Run the generation script to produce the runtime JSONL.
