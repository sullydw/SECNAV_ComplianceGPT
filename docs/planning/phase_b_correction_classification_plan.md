# Phase B Correction Classification Planning

## Status
Planning only — not yet implemented.  
Source baseline: `71ddf64` — CCI: Add session correction persistence (Phase A)  
Documentation checkpoint: `8c863ff` — Docs: Add Phase A session persistence checkpoint

## Scope
Design a deterministic/heuristic classifier that maps captured corrections into the four approved correction types. Do not implement code yet. Do not modify renderer/layout behavior.

---

## 1. Why Classification Matters

Today every correction captured via `capture_correction()` carries `correction_type="unknown"` unless the caller manually passes one of the four types. Phase B will automatically assign the correct type based on field path, reason text, and optional validator conflict metadata.

Classification determines:
- Whether a session correction is safe to persist beyond the active draft.
- Whether a correction is a candidate for local command profile promotion (Phase C).
- Whether a correction is a candidate for global SECNAV rule promotion (Phase D).
- Whether a correction should be blocked from auto-reuse until reviewed.

---

## 2. Approved Correction Types

| Type | Safe for session persistence | Promotable to profile | Promotable to global rule |
|---|---|---|---|
| `one_time_wording` | Only if explicitly `current_session` | No | No |
| `local_command_preference` | Yes | Phase C after approval | No |
| `possible_secnav_manual_rule` | Yes | No | Phase D after review |
| `bug_validator_gap` | Yes | No | Phase D after review |

These four types are already encoded in `src/correction_capture.py` `_ALLOWED_CORRECTION_TYPES`.

---

## 3. Classifier Inputs

The classifier receives exactly the following at capture time:

| Input | Source | Required? |
|---|---|---|
| `field_path` | Caller or captured from payload | Yes |
| `reason` | Caller-provided free text | Optional but strongly recommended |
| `original_value` | Snapshot from payload at field_path | Yes |
| `corrected_value` | Caller-provided replacement | Yes |
| `doc_type` | Resolved from payload context | Yes |
| `component` | Resolved from payload context | Yes |
| `correction_scope` | `active_draft` or `current_session` | Yes |
| `validator_conflict` | Did the correction increase error count? | Optional |

The classifier does NOT require AI or LLM inference. It uses regex, keyword matching, and field-name heuristics.

---

## 4. Heuristic Classification Rules

### 4.1 `one_time_wording` indicators

A correction is classified as `one_time_wording` if ANY of the following match:

**Field path triggers:**
- `body[` — any indexed body paragraph. Body rewording is almost always one-time.
- `ref[` — reference text edits that do not change citation order or structure.
- `encl[` — enclosure text edits that do not change sequence or format.
- `via[` — adding a specific Via addressee for a single letter (context-specific).

**Reason text triggers (case-insensitive keyword match):**
- Contains "reword", "rephrase", "better wording", "one-time", "this letter only", "just for this draft"
- Contains "minor wording change", "example text", "placeholder"

**Safe persistence:** Only if scope is explicitly `current_session` AND user overrides.

---

### 4.2 `local_command_preference` indicators

A correction is classified as `local_command_preference` if ANY of the following match:

**Field path triggers:**
- `from` — correcting a From line that the user expects to match their local command.
- `signature` — standardizing a signature block for their command.
- `originator_code` — local originator code or sender symbol preference.
- `unit_identity` — unit-specific identity block.
- `copy_to[`, `distribution[` — local distribution list preferences.
- `point_of_contact` — local contact information.

**Reason text triggers:**
- Contains "our SOP", "local command", "standard for our unit", "we always use", "unit preference", "per local instructions"

**Safe persistence:** Yes to `current_session` scope automatically.
**Profile promotion candidate:** Yes (Phase C).

---

### 4.3 `possible_secnav_manual_rule` indicators

A correction is classified as `possible_secnav_manual_rule` if ANY of the following match:

**Field path triggers:**
- `subj` — punctuation removal, all-caps enforcement, acronym handling.
- `date` — date format corrections (`day Month year` vs civilian).
- `body` — pluralization, capitalization, or formatting corrections that apply to all similar documents.

**Reason text triggers:**
- Contains "SECNAV", "manual", "5216.5", "paragraph", "Figure", "regulation", "required by", "must be"

**Validator conflict signal:**
- If a validator error existed BEFORE the correction and the correction FIXES it, this strongly suggests a manual rule the system should already know.

**Safe persistence:** Yes to `current_session` scope automatically.
**Profile promotion candidate:** No (not command-specific).
**Global rule candidate:** Yes (Phase D).

---

### 4.4 `bug_validator_gap` indicators

A correction is classified as `bug_validator_gap` if ANY of the following match:

**Primary signal:**
- The user says the validator was wrong, OR the correction contradicts validator output and the user insists on it.
- `validator_conflict = True` (correction increased errors or contradicted existing validator findings).

**Reason text triggers:**
- Contains "validator is wrong", "false positive", "should not flag", "allowed by", "permitted", "exception", "gap"

**Field path triggers:**
- Any field where the validator flagged an error and the user overrode it.
- Corrections that add content validators would reject (e.g., adding punctuation to subject when subject validator says no terminal punctuation).

**Safe persistence:** Yes to `current_session` scope automatically.
**Profile promotion candidate:** No.
**Global rule candidate:** No direct promotion — this goes to a BUG REVIEW queue, not a rule-candidate queue.

---

## 5. Classification Confidence

Each classification receives a `confidence` score: `high`, `medium`, `low`.

| Type | High confidence rule |
|---|---|
| `one_time_wording` | Field path starts with `body[` AND reason contains "one-time" or "this letter" |
| `local_command_preference` | Field path is `from`, `originator_code`, `unit_identity` AND reason contains "our SOP" or "local" |
| `possible_secnav_manual_rule` | Field path is `subj` or `date` AND validator error existed before correction AND correction resolves it |
| `bug_validator_gap` | `validator_conflict` is True AND reason contains "validator" or "false positive" |

Medium/low confidence triggers:
- Only field path matches, reason is empty.
- Only reason keyword matches, field is ambiguous.
- Multiple type indicators conflict (e.g., body edit + "our SOP" reason).

When confidence is `low`, the classifier defaults to `unknown` and emits a warning: "Could not confidently classify correction for {field_path}. Type remains 'unknown'. User may override."

---

## 6. User Override Behavior

The classifier is advisory only.

1. **Classification runs automatically at capture time** if no explicit `correction_type` is passed by the caller.
2. **The user may override the classification** before persistence. This requires a UI affordance or an optional parameter on `capture_correction(..., correction_type="local_command_preference")`.
3. **If the user overrides, the override wins** and confidence is recorded as `user_override`.
4. **If correction remains `unknown`, session persistence is blocked** for safety. Only corrections with a non-unknown type may be persisted to `current_session`.
5. **One-time wording always requires user confirmation** even when classified automatically.

---

## 7. Interaction with Session Persistence

Today `correction_capture.py` and `correction_store.py` already support session persistence. Phase B classification affects what gets persisted:

| Classification | Auto-persist to session JSONL | Condition |
|---|---|---|
| `one_time_wording` | No | Blocked unless user explicitly overrides type or scope |
| `local_command_preference` | Yes | User explicitly scoped to `current_session` |
| `possible_secnav_manual_rule` | Yes | User explicitly scoped to `current_session` |
| `bug_validator_gap` | Yes | User explicitly scoped to `current_session` |
| `unknown` | No | Classification required before persistence |

The `IntakeOrchestrator.persist_correction()` method already checks type before writing to disk. Phase B adds a `classify_correction()` helper that runs inside `capture_correction()` or as a pre-persist step.

---

## 8. Interaction with Validator Conflicts

If a correction is classified as `bug_validator_gap`, the system must preserve the conflict for review:
- The conflict record in `_correction_conflicts` already captures before/after error counts.
- Phase B adds `classification` and `confidence` to the conflict record.
- A future Phase D review utility will surface all `bug_validator_gap` conflicts for triage.

If a correction is classified as `possible_secnav_manual_rule` and the validator originally missed it (no conflict), this is a pure rule-candidate: the validator should have caught it but did not. These also go to Phase D.

---

## 9. Required Regression Coverage

Phase B requires a new regression runner: `tools/run_correction_classify_regression.py`

Minimum test matrix:

1. Body paragraph edit without reason -> `one_time_wording` (high)
2. Body paragraph edit with "one-time" reason -> `one_time_wording` (high)
3. Body paragraph edit with "our SOP" reason -> `local_command_preference` (medium/high)
4. `from` field edit with "local command" reason -> `local_command_preference` (high)
5. `originator_code` edit -> `local_command_preference` (high)
6. `subj` period removal with empty reason -> `possible_secnav_manual_rule` (medium)
7. `subj` edit with "SECNAV requires" reason -> `possible_secnav_manual_rule` (high)
8. Validator conflict + "false positive" reason -> `bug_validator_gap` (high)
9. Ambiguous field + ambiguous reason -> `unknown` (low)
10. User override beats heuristic -> type is `user_override`
11. `unknown` classification blocks session persistence
12. `one_time_wording` blocks session persistence unless user overrides
13. Existing correction regressions still pass after classification module added
14. Existing intake regressions still pass after classification module added
15. Existing session correction regressions still pass after classification module added

Exit 0 if all checks pass. Exit 1 on any failure.

---

## 10. Future Implementation Plan (Not Approved Yet)

When the design is approved:

Step 1 — Add `classify_correction()` to `src/correction_classify.py`
- Pure helper, no side effects.
- Returns `(type, confidence, reasons)`.

Step 2 — Integrate classification into `src/correction_capture.py`
- If `correction_type` is "unknown" at call time, run classifier before recording.
- Add `classification_confidence` field to correction record.

Step 3 — Add type gate to `src/intake_orchestrator.py` `persist_correction()`
- Block persistence if classification is `unknown`.
- Block persistence if classification is `one_time_wording` unless user explicitly overrides.

Step 4 — Add `tools/run_correction_classify_regression.py`
- Exercise all 15 checks above.

Step 5 — Run full regression suite (18 runners)
- Verify no existing behavior breaks.

Step 6 — Commit with message: "CCI: Add correction classification (Phase B)"

Step 7 — Update checkpoint doc: `docs/checkpoints/phase_b_correction_classification_checkpoint.md`

---

## 11. Implementation Boundaries

What Phase B will do:
- Add deterministic classification logic.
- Update capture records with classification + confidence.
- Gate session persistence by classification.
- Provide user override paths.
- Add regression runner.

What Phase B will NOT do:
- Modify renderer or layout behavior.
- Automatically promote corrections to profiles (Phase C).
- Automatically log pending global rules (Phase D).
- Change correction scope definitions.
- Add automatic cleanup or session management.
- Require AI/LLM inference.

---

## 12. Safety Summary

- Classification is advisory, not mandatory.
- User may always override the classifier.
- `unknown` corrections cannot persist to session JSONL.
- `one_time_wording` corrections cannot persist without explicit user confirmation.
- All classification decisions are auditable (reasons recorded in correction record).
- Existing scopes (`active_draft`, `current_session`) remain unchanged.
- Unreviewed corrections never become global SECNAV rules.

---

**Plan created:** 2026-06-01  
**Planning baseline:** `89f7016` — Docs: Update correction memory plan after Phase A  
**Next step:** Await review and approval before implementing Phase B.
