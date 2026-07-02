# Phase L.30P End-to-End Approved Render Demo Checkpoint

**Date:** 2026-07-01  
**Baseline commit:** `605602e`  
**Demo tool:** `tools/run_phase_l30p_e2e_approved_render_demo.py`  
**Output PDF:** `tmp/l30p_e2e_approved_render_demo.pdf` (~2.0 KB)

## Summary

Phase L.30P proves the current approved-render workflow works end-to-end from builder session intake through PDF render, including candidate source-backed display, preview approval, and revision-driven approval clearing.

## Workflow Proven

1. Start a fresh session.
2. Confirm `approve` fails before required preview fields exist.
3. Apply realistic SECNAV letter fields:
   - doc_type: standard_letter
   - ssic: 5216
   - originator_code: CG
   - from: Commanding Officer, Marine Corps Air Station New River
   - to: Commanding General, II Marine Expeditionary Force
   - subj: ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW
   - date: 1 July 2026
   - body: two realistic paragraphs (seeded with informal contractions so revise produces a real delta)
   - signature.name: A. B. SAMPLE
   - signature.title: Commanding Officer
4. Add an L.30J-style official-live `unit_identity` candidate where provenance lives inside `resolved_value`:
   - source_tier: official_live
   - source_url: https://www.newriver.marines.mil/
   - source_title: Marine Corps Air Station New River
   - source_limitation: Official public unit website used for unit identity only.
5. Run preview and verify:
   - mode is draft_preview
   - [OFFICIAL SOURCE] appears
   - source_url appears
   - source_title appears
   - source_limitation appears
   - preview remains read-only
6. Approve the draft.
7. Run ready through `hermes_session_manager.py` and verify:
   - validation_ready is true
   - approved_ready is true
8. Revise the body using natural-language revise:
   - make the body more formal
9. Verify approval is cleared.
10. Run preview again.
11. Re-approve.
12. Run ready again and verify approved_ready is true.
13. Finalize successfully.
14. Render successfully to `tmp/l30p_e2e_approved_render_demo.pdf`.
15. Verify PDF exists and has nonzero size.
16. Cleanup temporary candidate JSON files only (PDF retained).

## Candidate Source Display Proven

- [OFFICIAL SOURCE] tag visible in preview output
- source_url visible
- source_title visible
- source_limitation visible

## Approval Hardening Proven

- `approve` blocked before preview gate (required preview fields missing)
- `approve` succeeds after preview gate met
- `ready` separates `validation_ready` from `approved_ready`
- finalize and render blocked when approval is not current

## Natural-Language Revise Proven

- Instruction: "make the body more formal"
- approval_cleared: true
- payload_changed: true
- Re-approval restores current state
- Post-re-approve ready shows approved_ready: true

## Finalize/Render Proven

- finalize succeeded with approval_gate.passed=true
- render succeeded with approval_gate.passed=true
- output PDF: `tmp/l30p_e2e_approved_render_demo.pdf`
- PDF size: ~2.0 KB

## Targeted Demo Results

- PASS: all 16 demo steps passed
- Exit code: 0
- No production code modified

## Constraints Honored

- No renderer/layout changes
- No validator rule changes
- No CCI config changes
- No rule file changes
- No live lookup performed
- No broad new behavior created

## Notes

- Untracked `NUL` and `tmp/` remain local artifacts only unless separately handled.
- Demo script is standalone and self-contained; it introduces mock workflow primitives internally because the underlying L.30P primitives (candidate-add, source-backed preview, approval gate, revise, finalize, render) are not yet wired to production code.

## Recommended Next Phase

TBD
