# Chapter 10 Phase 0A — Memorandum for the Record (MFR) Scope

**Phase:** 0A (Documentation and Fixtures Only)  
**Date:** 2026-05-18  
**Status:** Scope Definition

---

## Objective

Define the scope and create initial fixtures for Memorandum for the Record (MFR) rendering support in Chapter 10. This phase is **documentation and fixtures only** — no renderer, validator, or model changes.

---

## MFR Structural Characteristics

The Memorandum for the Record is structurally different from a standard letter (Chapter 7) and multiple-address letter (Chapter 8):

### What MFR Does NOT Have
- ❌ No letterhead block (H-series letterhead rules do not apply)
- ❌ No SSIC/originator code block
- ❌ No From/To/Via address stack
- ❌ No standard-letter signature block (role/title block)
- ❌ No Distribution or Copy to blocks

### What MFR DOES Have
- ✅ Date line (typically top-left or top-center)
- ✅ Centered title: `MEMORANDUM FOR THE RECORD`
- ✅ Optional `Subj:` line (subject)
- ✅ Numbered body paragraphs (same marker system as standard letters)
- ✅ Simple signer name + organizational code (not a full signature block)

---

## Fixture Scope

This phase creates two audit fixtures:

1. **audit_c10_mfr_with_subject.json** — Full MFR with subject line
2. **audit_c10_mfr_short_no_subject.json** — Minimal MFR without subject, with `file_copy_mfr: true`

Both fixtures use:
- `doc_type: "DT_MEMO_MFR"`
- Standard numbered paragraph body structure

---

## Out of Scope (Future Phases)

The following are explicitly **not** part of Phase 0A:

- Plain-paper memorandums (From-To memos)
- Memorandum of Agreement (MOA)
- Memorandum of Understanding (MOU)
- Same-page endorsement support
- Renderer implementation
- Validator implementation
- Regression runner integration

---

## Next Phase (0B)

After fixture review and scope approval, Phase 0B will implement:
- MFR renderer support (date, title, optional subject, body, signer)
- MFR-specific layout rules
- Visual audit checklist

---

## References

- SECNAV M-5216.5 Chapter 10 (Memorandums)
- Figure 10-1 through 10-7 (Memorandum formats)
