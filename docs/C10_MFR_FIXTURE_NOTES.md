# C10 MFR Fixture Notes

**Phase:** 0A (Fixtures Only)  
**Date:** 2026-05-18

---

## Fixture Design Principles

These fixtures are designed to:
1. Capture the structural essence of MFR format
2. Test doc_type discrimination (DT_MEMO_MFR vs DT_STANDARD_LETTER)
3. Validate optional subject handling
4. Support future renderer implementation

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
  "body": [...],
  "signer_name": "John Doe",
  "signer_org_code": "OPC123"
}
```

**Expected renderer behavior (future):**
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
  "body": [...],
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
- `body` uses standard paragraph structure (level 1-4 markers)
- Signer fields are simple strings (not full signature block objects)

---

## Do Not Modify

These fixtures are baseline for Phase 0A. Do not modify until:
- Phase 0A scope is reviewed and approved
- Phase 0B renderer implementation begins

---

## Future Validation Rules (Phase 0B+)

Anticipated validator checks:
- C10-001: MFR must have date and title
- C10-002: MFR title must be centered (renderer rule)
- C10-003: MFR signer must include name and org code
- C10-004: MFR subject is optional; if omitted, no blank placeholder
