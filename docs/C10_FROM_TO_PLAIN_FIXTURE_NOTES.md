# C10 Plain-Paper From-To Memorandum Fixture Notes

**Phase:** 2A (Fixtures Only)  
**Date:** 2026-05-19

---

## Fixture Design Principles

These fixtures are designed to:
1. Capture the structural essence of Plain-Paper From-To format (Figure 10-3)
2. Test doc_type discrimination (DT_MEMO_FROM_TO_PLAIN vs DT_MEMO_MFR vs DT_STANDARD_LETTER)
3. Validate required From/To/Subj fields
4. Support future validator and renderer implementation

---

## Body Format Convention

Fixtures use the C7/C9/C10-MFR project style for body paragraphs:

```json
"body": [
  "1. This memorandum records...",
  "2. Action items...",
  "3. a. Subparagraphs use standard marker format..."
]
```

- Body is a list of strings (not nested objects)
- Each string includes its paragraph marker inline (e.g., "1. ", "a. ", "(1) ")
- No level/marker/text/children structure in Phase 2A

---

## Reference and Enclosure Format

References and enclosures follow C7/C9 marker style:

**References:**
```json
"ref": [
  "(a)  COMNAVAIRFORINST 5216.5A",
  "(b)  Smith Industries letter Ser 123/45 of 15 Mar 2025"
]
```

**Enclosures:**
```json
"encl": [
  "(1)  List of Reserve Officers",
  "(2)  CMC ltr 5216 Ser 00/451 of 5 Sep 09"
]
```

---

## Signature Block Format

From-To memo uses full signature block (compatible with C7 standard letters):

```json
"signature": {
  "name": "John Doe",
  "title": "Chief of Staff",
  "organization": "OPC123"
}
```

---

## audit_c10_from_to_plain_basic.json

**Purpose:** Basic From-To with all required elements

**Key fields:**
```json
{
  "doc_type": "DT_MEMO_FROM_TO_PLAIN",
  "date": "19 May 2026",
  "from": "Commanding Officer, Example Activity",
  "to": "Commanding Officer, Example Receiving Activity",
  "subj": "Subject line required",
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signature": {
    "name": "John Doe",
    "title": "Chief of Staff",
    "organization": "OPC123"
  }
}
```

**Expected validator behavior (Phase 2B):**
- Validate From, To, Subj presence (all required)
- Validate signature block presence
- Validate body paragraph marker format

**Expected renderer behavior (Phase 3):**
- Date at top-left
- MEMORANDUM FOR centered or left-aligned
- From line below title
- To line below From
- Subj line below To
- Body paragraphs with standard numbering
- Full signature block at bottom

---

## audit_c10_from_to_plain_with_refs.json

**Purpose:** From-To with references

**Key fields:**
```json
{
  "doc_type": "DT_MEMO_FROM_TO_PLAIN",
  "date": "19 May 2026",
  "from": "Commanding Officer, Example Activity",
  "to": "Commanding Officer, Example Receiving Activity",
  "subj": "Subject with references",
  "ref": [
    "(a)  COMNAVAIRFORINST 5216.5A",
    "(b)  NAVADMIN 123/25"
  ],
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signature": {
    "name": "Jane Smith",
    "title": "Director",
    "organization": "S-1"
  }
}
```

**Notes:**
- References use C7/C9 marker style: (a), (b), (c)...
- Ref line appears below Subj (if present)

---

## audit_c10_from_to_plain_with_encls.json

**Purpose:** From-To with enclosures

**Key fields:**
```json
{
  "doc_type": "DT_MEMO_FROM_TO_PLAIN",
  "date": "19 May 2026",
  "from": "Commanding Officer, Example Activity",
  "to": "Commanding Officer, Example Receiving Activity",
  "subj": "Subject with enclosures",
  "encl": [
    "(1)  List of Reserve Officers",
    "(2)  CMC ltr 5216 Ser 00/451 of 5 Sep 09"
  ],
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signature": {
    "name": "Bob Johnson",
    "title": "Assistant Chief of Staff",
    "organization": "N1"
  }
}
```

**Notes:**
- Enclosures use C7/C9 marker style: (1), (2), (3)...
- Encl line appears below Subj (or below Ref if both present)

---

## Schema Conventions

All fixtures follow the v6 payload schema:
- `doc_type` discriminates document type
- `body` is a list of strings with inline markers (C7/C9/C10-MFR style)
- `signature` is an object with name, title, organization (C7-compatible)
- `ref` and `encl` are lists of strings with marker prefixes

---

## Do Not Modify

These fixtures are baseline for Phase 2A. Do not modify until:
- Phase 2A scope is reviewed and approved
- Phase 2B validator implementation begins

---

## Future Validation Rules (Phase 2B)

Planned validator checks:
- C10-101: From-To memo must have From, To, and Subj (all required)
- C10-102: From-To memo must not have Distribution line
- C10-103: From-To memo references must follow C7/C9 marker style
- C10-104: From-To memo enclosures must follow C7/C9 marker style
- C10-105: From-To memo must not include MFR-only fields (file_copy_mfr, title)

---

**Note:** This is not rendered yet. This is not validated yet. C10 MFR remains protected and must not be modified. C9 same-page endorsements remain deferred.
