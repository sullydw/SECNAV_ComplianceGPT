# Phase H.36 / Phase I.35 — Sanitized Operator Feedback Observation Plan

**Date:** 2026-06-09  
**Status:** Planning only  
**Rule:** `CCI-ROUTE-011`  
**Observation posture:** Paused fixture observation; awaiting operator feedback

---

## 1. Purpose

This document defines how future sanitized operator feedback about the `CCI-ROUTE-011` warning pilot will be captured, classified, and reviewed. It supports continued warning pilot monitoring without repeating the static fixture-only burn-in checkpoints that were paused after H.34.

This plan does **not** collect or commit any real operator feedback. It defines the framework for handling feedback when it arrives.

---

## 2. Current Baseline

| Item | Value | Commit |
|---|---|---|
| H.28 fixture/runner | Stable | `ee4f3a2` |
| H.31/H.32/H.33 burn-in | Identical clean results | `973c868`, `6dc5a45`, `a9f6b90` |
| H.34 decision | Paused repeated fixture-only observation | `9bcd4c5` |
| H.35 posture | Confirmed paused-observation posture | `19542bd` |
| Regression suites | 35 active | Current |
| `CCI-ROUTE-011.effective_severity` | `warning` | Stable |
| `CCI-ROUTE-010.effective_severity` | `advisory` | Stable |
| `global_default` | `advisory` | Stable |
| Error promotion | **Unauthorized** | Unchanged |

---

## 3. Feedback Eligibility

Operator feedback may only be committed in sanitized or synthetic form. Real operational details must remain local unless fully sanitized.

**Prohibited in committed feedback records:**
- Names of personnel, commands, or units
- Phone numbers, emails, or addresses
- Unit-specific identifiers or organization codes
- Real dates tied to specific events
- Signatures or signed block content
- Hull numbers or vessel identifiers
- Unique identifiers of any kind
- Classified or controlled unclassified information

**Allowed in committed feedback records:**
- Category of issue (false positive, false negative, guidance, etc.)
- Document type and routing format
- Whether `window_envelope` was tagged or not
- Whether `from` was present, null, empty, or missing
- Severity level observed (advisory / warning / error)
- Operator impact rating (none / low / moderate / high)
- Sanitized summary using placeholder data only
- Recommended action (none / guidance / update fixtures / review validator / rollback review)

---

## 4. Suggested Feedback Categories

| Category | Description | Example |
|---|---|---|
| `false_positive` | Rule warned when it should not have | Standard letter with valid From line triggered warning |
| `false_negative` | Rule did not warn when it should have | Standard letter missing From line was not flagged |
| `window_envelope_confusion` | Operator unsure whether window envelope suppresses correctly | Operator unsure why a standard letter without From line was not flagged because it was tagged window-envelope |
| `missing_from_confusion` | Operator unsure why warning fired | Operator does not understand why a document missing From line triggered warning |
| `nonstandard_warned` | Non-standard document incorrectly triggered warning | Memo, endorsement, or NAVGRAM incorrectly flagged for missing From line |
| `standard_warned_correctly` | Standard letter missing From line correctly warned | Positive confirmation that warning behaves as expected |
| `usability_note` | Operator experience note unrelated to correctness | Message wording unclear, severity label confusing |
| `no_feedback` | No issue observed; operator confirms pilot is silent | Routine confirmation that no problems detected |

---

## 5. Suggested Feedback Record Fields

Each feedback record should include the following fields:

| Field | Type | Description |
|---|---|---|
| `feedback_id` | string | Unique identifier (e.g., `H36_FEEDBACK_001`) |
| `date_captured` | ISO-8601 | Date feedback was received locally |
| `sanitized_marker` | boolean | `true` if record contains only synthetic/sanitized data |
| `category` | enum | One of the 8 categories listed in section 4 |
| `rule_id` | string | `CCI-ROUTE-011` |
| `document_type` | string | `standard_letter`, `memo`, `endorsement`, `NAVGRAM`, `report`, etc. |
| `expected_behavior` | string | What the operator expected to happen |
| `observed_behavior` | string | What actually happened |
| `severity_observed` | enum | `advisory`, `warning`, `error`, or `none` |
| `operator_impact` | enum | `none`, `low`, `moderate`, `high` |
| `sanitized_summary` | string | Brief sanitized description; use placeholder names/dates only |
| `recommended_action` | enum | `none`, `guidance_update`, `fixture_update`, `validator_review`, `rollback_review` |
| `regression_rerun_required` | boolean | Whether the H.24/H.28 runner and full 35-suite gate must be re-run |

---

## 6. Review Workflow

When operator feedback arrives:

1. **Collect locally** — Gather the feedback in a local non-committed working note.
2. **Sanitize** — Remove all real identifiers, dates, names, and operational details. Replace with placeholder data.
3. **Classify** — Assign one of the 8 categories from section 4.
4. **Assess** — Determine whether the feedback indicates:
   - False positive
   - False negative
   - Guidance / usability issue
   - No issue (confirmation)
5. **Decide action** — Based on the decision thresholds in section 7.
6. **Document** — Create a sanitized feedback record if useful for the project record.
7. **Gate check** — If the feedback suggests a behavior change, re-run the full 35-suite regression gate before any commit.
8. **Checkpoint** — If warranted, create `phase_h37_route011_operator_feedback_observation_checkpoint.md`.

**Do not change severity without a separate planning phase and explicit user approval.**

---

## 7. Decision Thresholds

| Condition | Decision | Action |
|---|---|---|
| Feedback is absent, minor, or guidance-only | Continue warning pilot | No checkpoint needed; note in local log |
| Operator confusion repeats (same category ≥2 times) | Create guidance update plan | Plan document only; no code changes until approved |
| New sanitized edge case is useful | Create fixture update plan | Plan document only; implementation requires separate approval |
| Credible false positive reported | Create rollback review plan | Rerun regression gate; create checkpoint; present to user |
| Credible false negative reported | Create rollback review plan | Rerun regression gate; create checkpoint; present to user |
| Non-standard document incorrectly warned | Create rollback review plan | Rerun regression gate; create checkpoint; present to user |
| Window-envelope suppression failure | Create rollback review plan | Rerun regression gate; create checkpoint; present to user |
| Operator impact rated high | Immediate escalation | Pause pilot; create emergency review; alert user |

---

## 8. Proposed Future Checkpoint

If and when sanitized operator feedback exists, or if a no-feedback observation checkpoint is explicitly desired:

- **Checkpoint file:** `docs/checkpoints/phase_h37_route011_operator_feedback_observation_checkpoint.md`
- **Contents:**
  - Number of feedback items received
  - Category distribution
  - Severity of each item
  - Whether any false positives or false negatives were reported
  - Decision: continue, pause, or rollback review
  - Full 35-suite gate result (if rerun)

This checkpoint is **not created** in H.36. It is created only when feedback exists or when explicitly requested.

---

## 9. Explicit Prohibitions

The following are explicitly prohibited during any H.36-related activity:

- No config changes.
- No severity changes.
- No error promotion.
- No rollback of any rule.
- No fixture changes.
- No runner changes.
- No validator/catalog/renderer/prompt/context/intake/UI/command-layer changes.
- No Phase F/G command-layer changes.
- No logs or unsanitized material committed.
- No reading or modification of `docs/BOOTSTRAP.md`.
- No modification of `docs/HERMES_INSTRUCTIONS.md`.

---

## 10. What This Plan Does Not Do

This plan does **not**:
- Collect real operator feedback
- Commit any feedback records
- Change any code
- Change any severity
- Create any checkpoint files
- Rerun any regression suite

It exists solely as a documented framework so that, if and when feedback arrives, there is a clear process for handling it safely.

---

## 11. Recommended Next Phase

**Phase H.37 / Phase I.36 — Operator Feedback Observation Checkpoint**

- Only created if sanitized operator feedback is available.
- If no feedback is available, the warning pilot remains in its current steady state.
- No action is required until feedback arrives or user direction changes.

Alternative: **Hold the warning pilot steady** and await user direction.
