# Chapter 10 Phase 2A — Plain-Paper From-To Memorandum Scope

**Phase:** 2A (Documentation and Fixtures Only)  
**Date:** 2026-05-19  
**Status:** Scope Definition

---

## Objective

Define the scope and create initial fixtures for Plain-Paper From-To Memorandum support in Chapter 10. This phase is **documentation and fixtures only** — no renderer, validator, or model changes.

---

## Plain-Paper From-To Memorandum Characteristics

The Plain-Paper From-To Memorandum (SECNAV M-5216.5 Figure 10-3) is structurally different from:
- MFR (Memorandum for the Record)
- Standard letters (Chapter 7)
- Multiple-address letters (Chapter 8)
- Endorsements (Chapter 9)

### What Plain-Paper From-To Memo Does NOT Have
- ❌ No letterhead block (H-series letterhead rules do not apply)
- ❌ No SSIC/originator code block
- ❌ No Distribution line (uses To line only for action addressees)

### What Plain-Paper From-To Memo DOES Have
- ✅ Date line (top-left, with From line)
- ✅ `MEMORANDUM FOR` title
- ✅ From line (originator below title)
- ✅ To line (action addressee below From)
- ✅ Required `Subj:` line
- ✅ Optional references (Ref: line)
- ✅ Optional enclosures (Encl: line)
- ✅ Numbered body paragraphs (same marker system as standard letters)
- ✅ Full signature block (name, title, organization)
- ✅ Optional Copy to addressees

---

## Fixture Scope

This phase creates three audit fixtures:

1. **audit_c10_from_to_plain_basic.json** — Basic From-To with From/To/Subj only
2. **audit_c10_from_to_plain_with_refs.json** — From-To with references
3. **audit_c10_from_to_plain_with_encls.json** — From-To with enclosures

All fixtures use:
- `doc_type: "DT_MEMO_FROM_TO_PLAIN"`
- Standard numbered paragraph body structure (list of strings with inline markers)
- Signature block compatible with existing standard-letter format

---

## Out of Scope (Future Phases)

The following are explicitly **not** part of Phase 2A:

- Printed From-To Memorandum (Figure 10-2)
- Letterhead Memorandum (Figure 10-4)
- MOA (Memorandum of Agreement)
- MOU (Memorandum of Understanding)
- Decision memorandum
- Renderer implementation
- Validator implementation
- Regression runner integration

---

## Protected Scope — Do Not Modify

**C10 MFR (DT_MEMO_MFR):**
- MFR rendering remains protected under Phase 1F
- MFR validator remains protected under Phase 0B
- MFR regression runner remains protected under Phase 1C
- Do not modify any MFR code or fixtures in future From-To phases

**C9 Same-Page Endorsements:**
- Same-page endorsements remain deferred (see `docs/C9_SAME_PAGE_ENDORSEMENT_DEFERRED.md`)
- Do not implement same-page endorsement logic

**C7/C8/C9 Protected:**
- C7 Phase 1 standard letters remain protected
- C8 core address formats remain protected
- C9 new-page endorsements remain protected
- All C7/C8/C9 regression guards must remain stable

---

## Next Phases (2B, 2C, 3)

After fixture review and scope approval, subsequent phases will proceed in this order:

**Phase 2B: Validator Only**
- C10-101: From-To memo must have From, To, and Subj
- C10-102: From-To memo must not have Distribution line
- C10-103: From-To memo references must follow C7/C9 marker style
- C10-104: From-To memo enclosures must follow C7/C9 marker style

**Phase 2C: Regression Runner Only**
- Add From-To fixture validates to regression suite
- Guard C7/C8/C9/C10-MFR regressions during From-To development

**Phase 3: Renderer Support (DT_MEMO_FROM_TO_PLAIN only)**
- From-To renderer (date, From, To, Subj, body, signature)
- From-To-specific layout rules (plain-paper format)
- Visual audit checklist

---

## References

- SECNAV M-5216.5 Chapter 10 (Memorandums)
- Figure 10-3 (Plain-Paper From-To Memorandum)

---

**Note:** This is not rendered yet. This is not validated yet. Future validator/renderer work must be separate phases.
