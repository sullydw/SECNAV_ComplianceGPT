# Phase L.9 — Conversational Builder Question Text and Signature Capture Improvements

**Checkpoint Date:** Saturday, June 13, 2026  
**Commit:** (to be recorded)  
**Phase Goal:** Improve builder question text and enable structured signature capture so the CLI collects renderer-compatible dict signatures.

---

## Files Changed

| File | Change |
|------|--------|
| `src/conversational_builder.py` | Bumped `_BUILDER_VERSION` to `"L.9"`. Added `is_signature_field()` helper. Modified `_coerce_value()` to detect structured signature fields (`signature.name`, `signature.role`, `signature.title`) and store them as a dict, avoiding list coercion. Added `_expand_dot_fields()` to expand nested `signature.*` keys before coercing other list fields. Added signature-specific question templates with clearer wording. Added `_signature_questions` list for structured capture. Added `set_signature_field(name, value)` API. Updated `_step_to_field_name()` to map `signature` step to structured fields. Updated `next_question()` to ask structured questions before generic signature. |
| `tools/run_phase_l7_conversational_builder_cli.py` | Updated `signature:` example text to show structured capture instructions: `signature.name: J. Q. Sample` with optional `signature.role` and `signature.title`. |
| `tools/run_phase_l9_conversational_builder_question_text_signature_capture_regression.py` | **New** — 14 synthetic tests covering `signature.name` ingestion, `signature.role` ingestion, `signature.title` ingestion, plain `signature:` mapping to dict, multi-field signature dict, finalize produces renderer-compatible shape, signature not in list coercion, question text improved, `set_signature_field()` API, signature dict survives finalize, signature step mapping, `signature.name` only dict, signature dict with trailing spaces |

---

## Signature Capture Behavior

| Scenario | Behavior |
|----------|----------|
| `signature.name: J. Q. Sample` | Stores `{"signature": {"name": "J. Q. Sample"}}` as dict |
| `signature.role: Commanding Officer` | Stores `{"signature": {"role": "Commanding Officer"}}` as dict |
| `signature.title: Commanding Officer` | Stores `{"signature": {"title": "Commanding Officer"}}` as dict |
| Multi-field `signature.name:` then `signature.role:` | Merges into single dict: `{"signature": {"name": "J. Q. Sample", "role": "Commanding Officer"}}` |
| Plain `signature: J. Q. Sample` | Maps to `{"signature": {"name": "J. Q. Sample"}}` via `_coerce_value()` special case |
| Non-signature field (e.g. `to:`) | Uses existing list/string coercion logic unchanged |
| Existing structured dict passed directly | Preserved as-is (no transformation) |

**Key implementation detail:** `_coerce_value()` now checks for `.` (dot) in field name and any of `is_signature_field()` matches before applying list coercion. The `signature` field name is removed from the generic `list_fields` coercion set logic; instead it receives its own branch that creates a dict.

---

## Question Text Improvements

| Step | Before | After |
|------|--------|-------|
| `subject` | `"Please provide the subject."` | `"What is the subject of this letter?"` |
| `from` | `"Please provide the sender."` | `"Who is sending this letter (name or office)?"` |
| `to` | `"Please provide the recipient."` | `"Who is receiving this letter (name or office)?"` |
| `body` | `"Please provide the body text."` | `"Enter the body text of the letter."` |
| `copy_to` | `"Please provide the copy_to list."` | `"Who else should receive a copy (optional, e.g., copy_to: CNO)?"` |
| `distribution` | `"Please provide the distribution list."` | `"Add distribution entries if needed (optional)."` |
| `window_envelope` | `"Please provide window envelope info."` | `"Will this letter use a window envelope (yes/no)?"` |
| `signature` | `"Please provide the signature."` | `"Provide signer details:"` followed by `signature.name:`, `signature.role:`, `signature.title:` prompts |

---

## Regression Results

| Suite | Result |
|-------|--------|
| L.4 conversational builder | **41/41 PASS** |
| L.5 validation summary | **36/36 PASS** |
| L.6 PDF dry-run | **7/7 PASS** (PDF skipped environmentally) |
| L.7 CLI regression | **26/26 PASS** |
| L.9 signature capture regression | **14/14 PASS** |
| H.13 config regression | **27/27 PASS** |
| K.3 subject punctuation | **11/11 PASS** |
| H.4 routing office-code | **18/18 PASS** |
| H.6 routing evidence | **15/15 PASS** |
| H.16 ROUTE-011 burn-in | **96/96 PASS** |
| H.24 ROUTE-011 sanitized fixtures | **36/36 PASS** |
| Non-PDF gate | **35/35 PASS** |
| Intake regression | **All PASS** |

---

## Non-PDF Gate Result

`tools/run_all_regressions_non_pdf_gate.py` — **35/35 PASS**

---

## Change Summary

### Renderer / Layout
- **No changes.** `src/pdf_v6_render.py` untouched.

### CCI Config / Severity
- **No changes.** Warning pilots remain active:
  - `CCI-ROUTE-010 = warning`
  - `CCI-ROUTE-011 = warning`
  - `CCI-CH7-SUBJ-002 = warning`
  - `global_default = advisory`

### Validator / Catalog
- **No changes.** No validator code modified.

### Phase F / G Command Layer
- **No changes.** No command-layer files modified.

### Error Promotion
- **Unauthorized.** No rule promotion performed.

---

## Risk Notes

- Signature dict is stored under key `"signature"` and merged if multiple `signature.*` keys arrive sequentially.
- Plain `signature: <value>` maps to `signature.name` to maintain backward compatibility with existing CLI examples.
- `signature` removed from `list_fields` coercion set — other list fields (`to`, `via`, `ref`, `encl`, `copy_to`, `distribution`, `body`, `commands`) remain coerced to list.
- Structured signature dict shape matches `examples/audit_c7_phase1_standard_letter.json` (`{"name": ..., "role": ..., "title": ...}`).

---

## Recommended Next Phase

`Phase L.10  Conversational Builder Demo Script and Operator Walkthrough`

- Goal: create a step-by-step operator walkthrough document showing how to run the builder CLI end-to-end
- Produce a clean demo script with sample input/output and expected validation results
- Validate that a new operator can follow the script without prior domain knowledge
