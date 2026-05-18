# C10 MFR Fixture Notes

**Phase:** 0A (Fixtures Only)  
**Date:** 2026-05-18

---

## Fixture Design Principles

These fixtures are designed to:
1. Capture the structural essence of MFR format
2. Test doc_type discrimination (DT_MEMO_MFR vs DT_STANDARD_LETTER)
3. Validate optional subject handling
4. Support future validator and renderer implementation

---

## Body Format Convention

Fixtures use the C7/C9 project style for body paragraphs:

```json
"body": [
  "1. This memorandum records...",
  "2. Action items...",
  "3. a. Subparagraphs use standard marker format..."
]
```

- Body is a list of strings (not nested objects)
- Each string includes its paragraph marker inline (e.g., "1. ", "a. ", "(1) ")
- No level/marker/text/children structure in Phase 0A

---

## audit_c10_mfr_with_subject.json

**Purpose:** Full MFR with all standard elements

**Key fields:**
```json
{
  "doc_type": "DT_MEMO_MFR",
  "date": "18 May 2026",
  "title": "MEMORANDUM FOR THE RECORD",
  "subj": "Subject line present",
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signer_name": "John Doe",
  "signer_org_code": "OPC123"
}
```

**Expected validator behavior (Phase 0B):**
- Validate date and title presence
- Validate signer name and org code presence
- Validate body paragraph marker format

**Expected renderer behavior (Phase 1):**
- Date at top-left
- Title centered
- Subject line (if present) below title
- Body paragraphs with standard numbering
- Signer name and org code at bottom

---

## audit_c10_mfr_short_no_subject.json

**Purpose:** Minimal MFR without subject line

**Key fields:**
```json
{
  "doc_type": "DT_MEMO_MFR",
  "date": "18 May 2026",
  "title": "MEMORANDUM FOR THE RECORD",
  "file_copy_mfr": true,
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signer_name": "Jane Smith",
  "signer_org_code": "S-1"
}
```

**Notes:**
- `subj` field omitted (not present in JSON)
- `file_copy_mfr: true` indicates this is a file copy (no distribution)
- Minimal body (1-2 paragraphs)

---

## Schema Conventions

Both fixtures follow the v6 payload schema:
- `doc_type` discriminates document type
- `body` is a list of strings with inline markers (C7/C9 style)
- Signer fields are simple strings (not full signature block objects)

---

## Do Not Modify

These fixtures are baseline for Phase 0A. Do not modify until:
- Phase 0A scope is reviewed and approved
- Phase 0B validator implementation begins

---

## Future Validation Rules (Phase 0B)

Planned validator checks:
- C10-001: MFR must have date and title
- C10-003: MFR signer must include name and org code
- C10-004: MFR subject is optional; if omitted, no blank placeholder
- C10-005: MFR body paragraphs must use standard marker format
