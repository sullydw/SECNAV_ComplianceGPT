# C7 Phase 1 Implementation Plan

**Purpose:** Plan Phase 1 implementation for Chapter 7 standard-letter renderer and validator support without activating rules yet.

---

## 1. Scope

- Chapter 7 standard-letter core only.
- No Chapter 8 distribution implementation.
- No Chapter 9 endorsements.
- No Chapter 10 memorandums.
- No advisory assembly/tabbing implementation.
- No validator activation yet.

---

## 2. Rules Included

- C7-003 Date
- C7-004 Sender symbols / From-line area
- C7-005 To line
- C7-006 Via line
- C7-007 Subject line
- C7-008 Reference line
- C7-009 Enclosure line
- C7-014 Paragraphs
- C7-015 Signature block
- C7-016 Copy to line
- C7-017 Continuation page identification
- C7-018 Page numbering

---

## 3. Implementation Sequence

**Batch 1 — Stabilize structured data model**
- Confirm model fields needed for C7 header/body/signature/copy-to
- Validate schema compatibility with existing renderer

**Batch 2 — Header block rendering**
- SSIC, Date, Sender symbols
- From/To/Via/Subj/Ref/Encl layout
- Blank line semantics verification

**Batch 3 — Body paragraph renderer/validator**
- Paragraph nesting and indentation
- Marker detection (1, a, (1), (a))
- Two-digit paragraph numbering support
- Spacing consistency with next-baseline cursor semantics

**Batch 4 — Signature and post-signature blocks**
- Signature block placement and orphan protection
- Copy to list rendering
- Distribution vs Copy to semantics

**Batch 5 — Continuation pages and page numbering**
- Continuation header with repeated subject
- Page number centering on page 2+
- Classification-aware numbering (TOP SECRET, etc.)

---

## 4. Model/Schema Additions

Fields to confirm/add to the letter model:

- letter.date
- letter.ssic
- letter.originator_code
- letter.serial
- letter.from_line
- letter.to_line
- letter.via[]
- letter.subject
- letter.references[]
- letter.enclosures[]
- letter.body_blocks[]
- letter.signature
- letter.copy_to[]
- letter.classification
- letter.is_top_secret
- letter.internal_copy_options

---

## 5. Test Fixtures Needed

- Basic one-page standard letter
- Standard letter with Via, Ref, Encl, Copy to
- Long subject requiring wrap
- Long Ref/Encl lines requiring continuation
- Paragraph nesting through 1a(1)(a)
- Invalid unpaired subdivision: 1a without 1b
- Two-digit paragraph numbering
- Long body forcing continuation page
- Continuation page with repeated subject
- Multi-page letter with centered page numbers
- Signature block near page bottom to test orphan protection
- Copy to list with multiple addressees requiring alphabetical order

---

## 6. Risks and Open Questions

- Avoid rewriting working renderer code.
- Figure-derived continuation rules require visual PDF comparison.
- Subject abbreviation judgment is partly contextual.
- Via routing is outside renderer scope.
- TOP SECRET page numbering requires classification support.
- Blind copy/internal copy behavior should not be mixed into normal visible Copy to rendering too early.
- Paragraph depth and two-digit indentation need visual regression tests.
- Existing spacing uses next-baseline cursor semantics; do not reintroduce pre-subtraction layout bugs.

---

## 7. Do-Not-Do List

- Do not activate all C7 rules at once.
- Do not implement Chapter 8 distribution in Phase 1.
- Do not implement Chapter 9 endorsements in Phase 1.
- Do not implement Chapter 10 memorandum templates in Phase 1.
- Do not rewrite the whole renderer.
- Do not hardcode manual examples as universal behavior.
- Do not convert advisory assembly/tabbing rules into renderer requirements.
- Do not let ReportLab-specific variable names leak back into rule files.
- Do not rely only on text extraction when figures affect layout.
- Do not change spacing semantics without visual PDF comparison.

---

## 8. Recommended First Code Batch

1. Confirm model fields needed for C7 header/body/signature/copy-to
2. Add or update one C7 test fixture:
   `examples/audit_c7_phase1_standard_letter.json`
3. Run existing renderer without behavior changes
4. Compare generated PDF visually before making layout changes

---

**Status:** Planning phase — no code changes yet

**Next:** Execute Recommended First Code Batch after stakeholder review
