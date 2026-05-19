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
  "(a) SECNAV M-5216.5",
  "(b) COMNAVAIRFORINST 5216.5A"
]
```

**Enclosures:**
```json
"encl": [
  "(1) Annual Training Schedule FY2026",
  "(2) Department Training Requirements Matrix"
]
```

---

## Signature Block Format

From-To memo uses full signature block (compatible with C7 standard letters):

```json
"signature": {
  "name": "J. DOE",
  "role": "principal_subordinate_by_title",
  "title": "Chief of Staff",
  "authority": null,
  "activity_head_title": null,
  "affects_pay_or_allowances": false
}
```

- `name`: Signer's last name in initials format (e.g., "J. DOE")
- `role`: Signer's role type (e.g., "principal_subordinate_by_title")
- `title`: Signer's title (e.g., "Chief of Staff")
- `authority`: null for standard signatures
- `activity_head_title`: null unless signing as activity head
- `affects_pay_or_allowances`: false for standard correspondence

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
    "name": "J. DOE",
    "role": "principal_subordinate_by_title",
    "title": "Chief of Staff",
    "authority": null,
    "activity_head_title": null,
    "affects_pay_or_allowances": false
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
    "(a) SECNAV M-5216.5",
    "(b) COMNAVAIRFORINST 5216.5A"
  ],
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signature": {
    "name": "J. SMITH",
    "role": "principal_subordinate_by_title",
    "title": "Director",
    "authority": null,
    "activity_head_title": null,
    "affects_pay_or_allowances": false
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
    "(1) Annual Training Schedule FY2026",
    "(2) Department Training Requirements Matrix"
  ],
  "body": ["1. First paragraph...", "2. Second paragraph..."],
  "signature": {
    "name": "B. JOHNSON",
    "role": "principal_subordinate_by_title",
    "title": "Assistant Chief of Staff",
    "authority": null,
    "activity_head_title": null,
    "affects_pay_or_allowances": false
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
- `signature` is a C7-compatible structured object (name, role, title, authority, activity_head_title, affects_pay_or_allowances)
- `ref` and `encl` are lists of strings with marker prefixes (one space after marker)

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
