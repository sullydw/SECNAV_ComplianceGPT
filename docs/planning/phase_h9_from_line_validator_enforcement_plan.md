# Phase H.9 / Phase I.8 — Advisory Validator Enforcement for CCI-ROUTE-011 (From-Line Required)

**Date:** 2026-06-08  
**Latest Docs Checkpoint:** `5f4b2ac` — `Docs: Record Phase H.8 third catalog pilot checkpoint`  
**Current Functional Baseline:** `769437d` — `CCI: Add From line catalog rule (Phase H.8)`  
**Current Regression Set:** 30 suites (all PASS)  
**Target Rule:** `CCI-ROUTE-011`  
**Catalog File:** `rules_v6/CCI/cci_ch2_routing_rules.json`  
**Planning Status:** planning-only until reviewed and approved. No code may be written under this plan without separate user approval.  
**Regression Python:** `C:\Users\drryl\pinokio\bin\miniconda\python.exe`

---

## 1. Whether Advisory Validator Enforcement Is Appropriate for CCI-ROUTE-011

**Yes.**

The catalog entry `CCI-ROUTE-011` has explicit SECNAV source text, deterministic trigger conditions, and no renderer/layout implication. Adding advisory/non-blocking validator enforcement follows the established H.2 (subject-line acronym) and H.4 (office-code prefix) precedents:

| Phase | Rule | Scope | Enforcement Added | Regression Result |
|---|---|---|---|---|
| H.1 | `CCI-CH7-SUBJ-006` | Catalog only | No | 25 suites PASS |
| H.2 | `CCI-CH7-SUBJ-007` | Advisory validator | Yes — subject-line acronym | 26 suites PASS |
| H.3 | `CCI-ROUTE-010` | Catalog only | No | 27 suites PASS |
| H.4 | `CCI-ROUTE-010` | Advisory validator | Yes — office-code prefix | 28 suites PASS |
| H.8 | `CCI-ROUTE-011` | Catalog only | No | 30 suites PASS |
| **H.9** | `CCI-ROUTE-011` | **Advisory validator** | **Proposed** | **31 suites (projected)** |

### 1.1 Why Advisory Is Appropriate

- The rule has **high provenance confidence**: exact quote verified on PDF page 50.
- The rule is **deterministic**: presence/absence of `routing.from` is a boolean test.
- The rule has **narrow blast radius**: one field, one document type (`standard_letter`).
- The existing routing validator (`cci_routing`) already processes routing metadata; adding a From-line presence check is a natural extension.
- The window-envelope exception is **explicit and testable**: a single conditional flag check.
- Advisory level allows gathering feedback before any blocking enforcement.

### 1.2 Why Not Error-Level in H.9

- No real-world fixture coverage for From-line absence yet.
- The window-envelope exception requires a new payload flag (`window_envelope`) that does not exist in current payloads.
- False-positive risk on payloads where `doc_type` is incorrectly classified.
- Catalog severity remains `error`; validator enforcement is interim advisory only, matching the H.2/H.4 pattern.

---

## 2. Recommended Enforcement Level

**Advisory (non-blocking) only.**

| Level | H.9 Decision | Rationale |
|---|---|---|
| `error` (blocking) | **NO** | No real-world testing; window-envelope exception requires new payload flag; false-positive risk on doc_type misclassification. |
| `warning` | **NO** | Advisory is the established precedent for first validator rollout (H.2, H.4). Warning level risks surprising users. |
| `advisory` (non-blocking) | **YES** | Safe first step; gathers feedback; preserves existing PASS/FAIL behavior; no feature flag required. |

### 2.1 Catalog Severity vs Validator Severity

- Catalog entry `CCI-ROUTE-011` has `severity: "error"`, reflecting the long-term/manual rule severity.
- Phase H.9 validator behavior is intentionally lower as **advisory** (non-blocking).
- The catalog severity represents the intended final enforcement level; the advisory validator rollout is interim.
- No error-level enforcement is allowed in Phase H.9.
- The validator message text should label the finding as advisory for human readers, but the function return schema remains unchanged.

---

## 3. How to Detect Missing `routing.from` for `standard_letter`

### 3.1 Detection Logic

**Condition A — Missing From line:**
- Input: JSON payload.
- Trigger: `doc_type` is `standard_letter` (or `DT_STD_LTR`).
- Check: `payload.get("from")` is `None`, empty string, or whitespace-only.
- Violation: No `From:` line present.

**Condition B — From line present:**
- `payload.get("from")` is a non-empty string.
- No finding.

### 3.2 Document-Type Detection

The validator must check `payload.get("doc_type")` or infer from payload structure. The explicit `doc_type` field is preferred:

| `doc_type` value | Standard letter? |
|---|---|
| `DT_STD_LTR` | Yes |
| `"standard_letter"` | Yes (if used) |
| Any other value | No — skip check |

If `doc_type` is absent, the validator should **skip** the From-line check rather than guess. This prevents false positives on payloads with implicit document typing.

### 3.3 Field Access Pattern

The payload uses the top-level `"from"` field (confirmed in `examples/audit_c7_phase1_standard_letter.json` and other fixtures):

```json
{
  "doc_type": "DT_STD_LTR",
  "from": "Commanding Officer, Example Activity",
  ...
}
```

The validator should read:
```python
from_value = payload.get("from")
if not from_value or not str(from_value).strip():
    # missing From line
```

---

## 4. How to Respect the Window-Envelope Exception

### 4.1 Exception Logic

The SECNAV rule states: `Every standard letter must have a "From:" line, except a letter that will be used with a window envelope.`

This means:
- **If `window_envelope` is true** → From-line absence is **allowed** (no finding).
- **If `window_envelope` is false or absent** → From-line absence is **a violation** (advisory finding).

### 4.2 Payload Flag Design

The validator should accept an optional flag in the payload:

```python
window_envelope = payload.get("window_envelope", False)
if window_envelope:
    return []  # skip From-line check
```

The flag must be:
- Boolean or JSON-boolean-like (`True`, `true`, `"yes"`, `1`).
- Default to `False` if absent.
- Not required in the payload (backward compatible).

### 4.3 H.9 Boundary — Read-Only Flag Consumption

H.9 is strictly **read-only** with respect to the `window_envelope` key:

- H.9 may read `payload.get("window_envelope")` **only if the key is already present** in the payload.
- H.9 **must not** modify payload generation logic.
- H.9 **must not** modify `src/context_resolver.py`.
- H.9 **must not** modify intake behavior.
- H.9 **must not** modify prompt contracts.
- H.9 **must not** modify UI or command flows to create, populate, or prompt for the key.
- Full support for setting, populating, or prompting for `window_envelope` is **deferred to a later separately approved phase**.

If the key is absent, the validator conservatively defaults to `False` and proceeds with the From-line check. This may produce a false-positive advisory on a window-envelope letter that lacks the flag. Because H.9 is advisory/non-blocking, this is acceptable. See Section 7.3.

---

## 5. Whether the Validator Needs a `window_envelope` / `envelope_type` / Equivalent Flag

**Yes — a `window_envelope` boolean flag is required.**

Without this flag, the validator cannot distinguish a legitimate window-envelope letter (which omits the From line by rule) from a standard letter that simply forgot the From line. The flag is the only way to avoid false positives on window-envelope correspondence.

However, per Section 4.3, H.9 is read-only with respect to this flag. H.9 does not create, populate, or prompt for the key. It only reads it if already present. Full flag lifecycle support is deferred.

### 5.1 Flag Options Considered

| Option | Pros | Cons | H.9 Decision |
|---|---|---|---|
| `window_envelope: bool` | Simple, explicit, backward compatible | Requires payload producer to set it | **Adopted** |
| `envelope_type: "standard" \| "window"` | Extensible for future envelope types | More complex; only one type needed now | Deferred |
| Infer from absence of `from` + presence of `to` | No payload change | Cannot distinguish legitimate omission from error | Rejected |
| Skip check entirely if `from` is missing | Zero false positives | Rule never enforced; misses actual violations | Rejected |

### 5.2 Backward Compatibility

If `window_envelope` is absent, the validator defaults to `False` and checks for From-line presence. This means:
- **Existing payloads without the flag** will be checked as if they are standard letters.
- **No breaking change** to existing behavior.
- **New payloads** can opt out by setting `window_envelope: true`.

---

## 6. How to Avoid False Positives When Document Type Is Not `standard_letter`

### 6.1 Document-Type Exclusion

The From-line rule applies only to standard letters. The validator must **explicitly skip** all non-standard-letter document types:

| Document Type | From-Line Check? | Rationale |
|---|---|---|
| `standard_letter` / `DT_STD_LTR` | Yes | Rule explicitly applies |
| `multiple_address_letter` | **Skip** | Not confirmed as standard-letter format |
| `endorsement` | **Skip** | Endorsements have different format; no From line or different originator block |
| `joint_letter` | **Skip** | Joint letters may have From line but are not confirmed covered by 7-2.5a |
| `memorandum_for_record` | **Skip** | Memorandums do not use standard-letter format |
| `from_to_memo` / `DT_MEMO_FROM_TO_PLAIN` | **Skip** | Memorandum format; From line is part of memo header, not standard-letter From block |
| `plain_paper_memo` | **Skip** | Memorandum format |
| `letterhead_memo` | **Skip** | Memorandum format |

### 6.2 Implementation

```python
_doc_type = payload.get("doc_type", "")
if _doc_type not in ("DT_STD_LTR", "standard_letter"):
    return []  # skip From-line check for non-standard letters
```

---

## 7. How to Avoid False Positives When the Letter Is Intentionally Formatted for a Window Envelope

### 7.1 Window-Envelope Flag Check

As described in Section 4 and 5, the `window_envelope` flag is the mechanism:

```python
if payload.get("window_envelope", False):
    return []  # no From-line finding; window-envelope exception applies
```

### 7.2 Message for Human Reviewers

If a standard letter has no From line and no `window_envelope` flag, the advisory message should:
- Flag the missing From line.
- Mention the window-envelope exception.
- Guide the user to set `window_envelope: true` if applicable, or mark the payload appropriately in a future approved workflow.

Example advisory message:
```
CCI-ROUTE-011 (advisory): standard letter missing "From:" line — SECNAV M-5216.5 Ch7 Section 6 "From:" Line, subparagraph a. General. If this letter uses a window envelope, set window_envelope=true to suppress this advisory.
```

### 7.3 Advisory False-Positive Tradeoff

H.9 may emit a false-positive advisory in the following scenario:

- A real window-envelope letter is submitted without `window_envelope: true` in the payload.
- The validator sees a `DT_STD_LTR` with no `from` field and no `window_envelope` flag.
- It emits `CCI-ROUTE-011 (advisory)` because it cannot distinguish a legitimate window-envelope omission from an accidental missing From line.

This false positive is **acceptable only because H.9 is advisory/non-blocking**:

- The finding does not block rendering, submission, or any downstream action.
- The message explicitly tells the user how to suppress it (set `window_envelope=true` or mark the payload appropriately in a future approved workflow).
- No error-level or warning-level enforcement is involved.
- The user can safely ignore the advisory if they know the letter is a window-envelope format.

**H.9 must not introduce any blocking or error-level behavior** to address this tradeoff. A future separately approved phase may implement payload-generation support, UI prompts, or intake workflow changes that populate `window_envelope` automatically, eliminating this false-positive class at the source.

---

## 8. How to Avoid Applying the Rule to Memorandum, Endorsement, Joint Letter, and Multiple-Address Letter

### 8.1 Explicit Type Exclusion

The same document-type guard from Section 6 handles all these cases:

| Type | Reason for Exclusion |
|---|---|
| Memorandum (MFR, from-to, plain-paper, letterhead) | Memorandums use a different format. The From line is either part of a memo header block or absent by design. |
| Endorsement | Endorsements are routed on the original letter or a new page. They do not have a separate From line in the standard-letter sense. |
| Joint letter | Joint letters may have multiple originators. The standard-letter From-line rule has not been verified for joint letters. |
| Multiple-address letter | Multiple-address letters use To-line or Distribution formats. The From-line rule applies to "standard letter" per the manual; whether multiple-address letters are a subset is unverified. |

### 8.2 Future Expansion (Not in H.9)

If separate verification confirms that `multiple_address_letter` or `joint_letter` should be covered, a future phase can update the `applies_to` list in the catalog and widen the validator type check. H.9 must not expand scope without provenance.

---

## 9. Whether `src/cci_routing_validate.py` Is the Correct Future Target

**Yes.**

Rationale:
- The routing validator already processes routing metadata (`to`, `via`, `copy_to`, `distribution`).
- The `from` field is a routing element (originator identification).
- Adding a small helper function is lower risk than creating a new validator file.
- The existing `cci_routing` validator name is already referenced in the catalog entry (`validator: "cci_routing"`).
- No new validator registration needed.
- The H.4 office-code prefix check (`_check_office_code_prefix`) already lives in this file, establishing precedent for adding rule-specific helpers.

---

## 10. Whether a Small Helper Such as `_check_from_line_required(...)` Is Sufficient

**Yes.**

### 10.1 Proposed Helper Signature

```python
def _check_from_line_required(payload: dict[str, Any]) -> list[str]:
    """
    CCI-ROUTE-011: From-Line Required Rule (advisory/non-blocking).
    Source: SECNAV M-5216.5, Chapter 7, Section 6, "From:" Line, subparagraph a. General.
    Quote: "Every standard letter must have a 'From:' line, except a letter
    that will be used with a window envelope."

    Returns a list of advisory warning strings. Empty list means no finding.
    """
```

### 10.2 Helper Logic

```python
def _check_from_line_required(payload: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    # Scope: standard letter only
    doc_type = payload.get("doc_type", "")
    if doc_type not in ("DT_STD_LTR", "standard_letter"):
        return findings

    # Window-envelope exception
    if payload.get("window_envelope", False):
        return findings

    # Check for From line
    from_value = payload.get("from")
    if from_value is None or not str(from_value).strip():
        findings.append(
            'CCI-ROUTE-011 (advisory): standard letter missing "From:" line '
            "— SECNAV M-5216.5 Ch7 Section 6 \"From:\" Line, subparagraph a. General. "
            "If this letter uses a window envelope, set window_envelope=true to suppress this advisory."
        )

    return findings
```

### 10.3 Call Site

In `validate_cci_routing()`, after the existing checks:

```python
def validate_cci_routing(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    _check_via(payload, warnings)
    _check_copy_to(payload, warnings)
    _check_distribution(payload, warnings)

    # Phase H.4: Advisory office-code prefix checks
    to_raw = _get_field(payload, _TO_FIELD_NAMES)
    for addressee in _normalize_list(to_raw):
        for finding in _check_office_code_prefix(addressee):
            warnings.append(finding)

    via_raw = _get_field(payload, _VIA_FIELD_NAMES)
    for addressee in _normalize_list(via_raw):
        for finding in _check_office_code_prefix(addressee):
            warnings.append(finding)

    # Phase H.9: Advisory From-line required check
    for finding in _check_from_line_required(payload):
        warnings.append(finding)

    return errors, warnings
```

### 10.4 Why This Is Sufficient

- The helper is ~15 lines of deterministic logic.
- It does not modify payload, errors list, or return signature.
- It reuses existing `_get_field` / `_normalize_list` patterns if needed.
- It is independently testable.
- It does not affect any existing check (Via, Copy-to, Distribution, Office-code).

---

## 11. How to Preserve Existing Routing Validator Behavior, Including CCI-ROUTE-010

### 11.1 Preservation Requirements

| Existing Behavior | Preservation Action |
|---|---|
| `_check_via()` | Do not modify. |
| `_check_copy_to()` | Do not modify. |
| `_check_distribution()` | Do not modify. |
| `_check_office_code_prefix()` | Do not modify. |
| `validate_cci_routing()` return signature | Keep `tuple[list[str], list[str]]`. |
| `errors` list emptiness | `errors` must remain empty in H.9. |
| Existing warning messages | Existing warning text must not change. |
| `cci_routing_validate.py` CLI | CLI behavior unchanged. |

### 11.2 Isolation Guarantee

The new `_check_from_line_required()` helper:
- Reads only `payload.get("doc_type")`, `payload.get("window_envelope")`, and `payload.get("from")`.
- Does not interact with `to`, `via`, `copy_to`, `distribution`, `office_code`, or any other field.
- Appends findings to the `warnings` list only after all existing checks have run.
- Has no side effects.

---

## 12. How Advisory Findings Should Be Emitted

### 12.1 Existing `(errors, warnings)` Return Structure

The routing validator returns `(errors, warnings)` where:
- `errors` is a list of blocking error strings.
- `warnings` is a list of non-blocking warning/advisory strings.

### 12.2 Advisory Placement

Phase H.9 findings are appended to the `warnings` list:

```python
for finding in _check_from_line_required(payload):
    warnings.append(finding)
```

- `errors` list remains **empty**.
- No third advisory channel is created.
- The existing `warnings` list absorbs the new advisory.

### 12.3 Message Format

```
CCI-ROUTE-011 (advisory): standard letter missing "From:" line — SECNAV M-5216.5 Ch7 Section 6 "From:" Line, subparagraph a. General. If this letter uses a window envelope, set window_envelope=true to suppress this advisory.
```

The `(advisory)` suffix in the message text signals to human readers that this is non-blocking, consistent with the H.4 `(advisory)` suffix for `CCI-ROUTE-010`.

---

## 13. Required SECNAV Provenance in Messages and Docstrings

### 13.1 Docstring Template

```python
def _check_from_line_required(payload: dict[str, Any]) -> list[str]:
    """
    CCI-ROUTE-011: From-Line Required Rule (advisory/non-blocking).
    Source: SECNAV M-5216.5, Chapter 7, Section 6, "From:" Line, subparagraph a. General.
    Quote: "Every standard letter must have a 'From:' line, except a letter
    that will be used with a window envelope."

    Approved record: agr_20260607_49947aca.
    Implementation target: validator_update (Phase H.9).

    Checks that a standard letter has a non-empty "from" field, unless
    the letter uses a window envelope (window_envelope=true).

    Advisory (non-blocking) until separately promoted.
    """
```

### 13.2 Message Provenance

Every advisory message must include:
- Rule ID: `CCI-ROUTE-011`
- Source: `SECNAV M-5216.5`
- Source location: `Ch7 Section 6 "From:" Line, subparagraph a. General`
- `(advisory)` suffix in message text

---

## 14. Required Targeted Regression Runner and Minimum Checks

### 14.1 Runner File

- **File:** `tools/run_phase_h9_from_line_validator_regression.py`
- **Checks:** Minimum 14, recommended 16–18.
- **Scope:** Validator behavior, false-positive controls, fixture coverage, file-mutation guards.

### 14.2 Recommended Check List

| # | Check | Category | Description |
|---|---|---|---|
| 01 | Validator module loads | Infrastructure | `src/cci_routing_validate.py` imports without error. |
| 02 | Helper exists | Infrastructure | `_check_from_line_required` function is callable. |
| 03 | Missing From line triggers advisory | Positive | `DT_STD_LTR` payload with no `from` field produces `CCI-ROUTE-011 (advisory)` in warnings. |
| 04 | Empty From line triggers advisory | Positive | `DT_STD_LTR` payload with `"from": ""` produces advisory. |
| 05 | Whitespace-only From line triggers advisory | Positive | `DT_STD_LTR` payload with `"from": "   "` produces advisory. |
| 06 | Present From line passes | Negative | `DT_STD_LTR` payload with `"from": "Commanding Officer..."` produces no ROUTE-011 finding. |
| 07 | Window-envelope flag suppresses advisory | Negative | `DT_STD_LTR` with `window_envelope: true` and no `from` produces no ROUTE-011 finding. |
| 08 | Window-envelope with From line still passes | Negative | `DT_STD_LTR` with `window_envelope: true` and `from` present produces no ROUTE-011 finding. |
| 09 | Memorandum skipped | Negative | `DT_MEMO_FROM_TO_PLAIN` with no `from` produces no ROUTE-011 finding. |
| 10 | Endorsement skipped | Negative | `endorsement` payload with no `from` produces no ROUTE-011 finding. |
| 11 | Joint letter skipped | Negative | `joint_letter` payload with no `from` produces no ROUTE-011 finding. |
| 12 | Multiple-address letter skipped | Negative | `multiple_address_letter` payload with no `from` produces no ROUTE-011 finding. |
| 13 | **Both ROUTE-010 and ROUTE-011 trigger independently** | **Positive / Integration** | **`DT_STD_LTR` payload with a numeric office code missing "Code" prefix (triggers ROUTE-010 advisory) AND no `from` field (triggers ROUTE-011 advisory) produces both findings independently in warnings.** |
| 14 | **Doc_type absent skips From-line check** | **Negative / Edge** | **Payload with no `doc_type` key and no `from` field produces no ROUTE-011 finding; the check skips rather than guessing.** |
| 15 | Existing CCI-ROUTE-010 behavior preserved | Regression | Office-code prefix findings still appear on appropriate payloads; no ROUTE-010 regression. |
| 16 | Existing routing warnings preserved | Regression | Via, Copy-to, Distribution warnings still appear unchanged. |
| 17 | No renderer/layout files changed | Safety | `src/pdf_v6_render.py` and layout profiles untouched. |
| 18 | No prompt-contract files changed | Safety | `src/context_resolver.py` untouched. |

### 14.3 Fixture Requirements

- All fixtures must be synthetic.
- Minimum 8 new `examples/routing_from_*.json` fixtures:
  - `routing_from_missing.json` — `DT_STD_LTR`, no `from`
  - `routing_from_empty.json` — `DT_STD_LTR`, `"from": ""`
  - `routing_from_present.json` — `DT_STD_LTR`, `from` present
  - `routing_from_window_envelope.json` — `DT_STD_LTR`, `window_envelope: true`, no `from`
  - `routing_from_memo_skipped.json` — `DT_MEMO_FROM_TO_PLAIN`, no `from`
  - `routing_from_endorsement_skipped.json` — `endorsement`, no `from`
  - `routing_from_both_rules.json` — `DT_STD_LTR`, no `from`, To addressee with numeric office code missing "Code" (triggers both ROUTE-010 and ROUTE-011)
  - `routing_from_no_doctype.json` — no `doc_type` key, no `from` (From-line check skips)
- No real command/user data, contact information, or real names.

### 14.4 Runner Safety

- The runner must use synthetic fixtures only.
- The runner must not read or write real user data.
- The runner must not depend on local pending/approved logs.
- The runner must be runnable with the explicit Pinokio/Miniconda Python path.

---

## 15. Full Regression Expectation

### 15.1 Current Gate (No Changes)

- **Gate:** 30 suites
- **Status:** All PASS

### 15.2 If H.9 Implements Advisory Validator Enforcement

- **Gate becomes:** 31 suites
- **New runner:** `tools/run_phase_h9_from_line_validator_regression.py`
- **All existing 30 suites must still pass.**

The 31-suite set would be:

1. `tools/run_phase_h9_from_line_validator_regression.py` — NEW, ~18 checks.
2. `tools/run_phase_h8_third_rule_catalog_regression.py` — 16 checks.
3. `tools/run_phase_h6_routing_office_code_evidence_regression.py` — 15 checks.
4. `tools/run_phase_h4_routing_office_code_validator_regression.py` — 18 checks.
5. `tools/run_phase_h3_second_rule_catalog_regression.py` — 15 checks.
6. `tools/run_phase_h2_subject_acronym_validator_regression.py` — 12 checks.
7. `tools/run_pilot_subject_acronym_rule_catalog_regression.py` — 11 checks.
8. `tools/run_correction_implementation_regression.py` — 45 checks.
9. `tools/run_correction_nl_command_regression.py` — 151 checks.
10. `tools/run_correction_command_regression.py` — 45 checks.
11. `tools/run_correction_review_regression.py` — 30 checks.
12. `tools/run_correction_pending_regression.py` — 33 checks.
13. `tools/run_correction_profile_promotion_regression.py` — 33 checks.
14. `tools/run_correction_classify_regression.py` — Phase B.
15. `tools/run_intake_regression.py`
16. `tools/run_correction_regression.py`
17. `tools/run_correction_session_regression.py`
18. `tools/run_profile_regression.py`
19. `tools/run_cci_audit_regression.py`
20. `tools/run_context_schema_regression.py`
21. `tools/run_cci_subject_regression.py`
22. `tools/run_cci_ref_encl_regression.py`
23. `tools/run_cci_acronym_regression.py`
24. `tools/run_cci_date_time_regression.py`
25. `tools/run_cci_personnel_regression.py`
26. `tools/run_cci_poc_regression.py`
27. `tools/run_cci_routing_regression.py`
28. `tools/run_c7_phase1_regression.py`
29. `tools/run_c8_regression.py`
30. `tools/run_c9_regression.py`
31. `tools/run_c10_regression.py`

All 31 suites must pass before any commit.

---

## 16. Files That May Be Modified in Future Implementation

If this plan is approved and implementation proceeds:

| File | Change Type | Reason |
|---|---|---|
| `src/cci_routing_validate.py` | Append helper + call site | Add `_check_from_line_required()` and invoke it in `validate_cci_routing()`. |
| `tools/run_phase_h9_from_line_validator_regression.py` | Create new file | Targeted regression runner for H.9. |
| `examples/routing_from_*.json` | Create new fixtures (6+) | Synthetic fixtures for positive/negative/edge cases. |
| `docs/PROJECT_STATUS.md` | Update | Reflect new baseline, regression count (31), milestone. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | Update | Update baseline and next-phase target. |
| `docs/checkpoints/phase_h9_from_line_validator_checkpoint.md` | Create new file | Post-implementation checkpoint. |

---

## 17. Files That Must Not Be Modified

| File | Why |
|---|---|
| `rules_v6/CCI/cci_ch2_routing_rules.json` | H.9 is validator-only; catalog entry already exists from H.8. No catalog changes. |
| `src/pdf_v6_render.py` | No renderer/layout changes. |
| `src/context_resolver.py` | No prompt-contract runtime changes. |
| `src/intake_orchestrator.py` | No intake orchestration changes unless separately approved. |
| `src/validator_runner.py` | No validator runner contract changes unless separately approved. |
| `src/correction_commands.py` | No Phase F command-layer changes. |
| `src/correction_nl_commands.py` | No Phase G command-layer changes. |
| `src/correction_implementation_planner.py` | No planner logic changes; only `mark_implemented()` usage if local record updated. |
| `src/cci_subject_validate.py` | No subject validator changes. |
| `src/cci_acronym_validate.py` | No acronym validator changes. |
| `src/cci_ref_encl_validate.py` | No ref/encl validator changes. |
| `src/cci_date_time_validate.py` | No date/time validator changes. |
| `src/cci_personnel_validate.py` | No personnel validator changes. |
| `src/cci_poc_validate.py` | No POC validator changes. |
| `corrections/approved_rule_promotions.json` | Remains local/gitignored; do not commit. |
| `corrections/pending_corrections.jsonl` | Remains local/gitignored; do not commit. |
| `corrections/session/*.jsonl` | Remains local/gitignored; do not commit. |
| `corrections/evidence/*` | Remains local/gitignored; do not commit. |
| Any real command/user profile | Do not commit contact data or local profiles. |
| `docs/BOOTSTRAP.md` | Do not modify. |
| `docs/HERMES_INSTRUCTIONS.md` | Do not modify. |

---

## 18. What Phase H.9 Must NOT Do

Phase H.9 is a **planning-only phase** unless explicitly approved for implementation. It must NOT:

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **No renderer/layout changes** | From-line checking is about field presence, not PDF geometry, margins, fonts, or spacing. |
| 2 | **No broad routing validator rewrite** | Only add one small helper function; preserve all existing routing checks (Via numbering, copy-to overlap, distribution format, office-code prefix). |
| 3 | **No automatic enforcement from approved logs** | The validator checks the JSON payload at audit time; it does not read `corrections/approved_rule_promotions.json`. |
| 4 | **No AI-only implementation decisions** | Every detection rule must be deterministic, testable, and grounded in the SECNAV source text. |
| 5 | **No prompt-contract runtime changes** | The context resolver, intake orchestrator, and validator runner contracts remain unchanged. |
| 6 | **No Phase F/G command-layer changes** | No new slash commands or NL command mappings for From-line management or window-envelope toggling. |
| 7 | **No severity promotion of CCI-ROUTE-010** | H.7 already approved keeping `CCI-ROUTE-010` advisory-only. H.9 must not revisit or override that decision. |
| 8 | **No error-level enforcement for CCI-ROUTE-011** | Advisory only in H.9. Error promotion requires separate planning, real-world testing, and feature-flag support. |
| 9 | **No feature flag/config implementation** | Feature-flag support remains conceptual only. No config files, environment variables, or severity override mechanisms may be added. |
| 10 | **No approved/pending/session logs committed** | All correction storage remains local/gitignored. |
| 11 | **No real command/user data committed** | All fixtures must be synthetic. No real names, commands, or contact data. |
| 12 | **No background automation** | No cron jobs, watchers, or CI triggers for rule activation. |
| 13 | **No multi-record batch implementation** | H.9 is one rule (`CCI-ROUTE-011`) only. |
| 14 | **No catalog changes** | The catalog entry from H.8 remains untouched. H.9 is validator-only. |

---

## 19. Rollback Plan

If Phase H.9 causes unexpected failures:

1. **Revert the validator changes** — remove `_check_from_line_required()` and its call site from `src/cci_routing_validate.py`.
2. **Delete the runner** — remove `tools/run_phase_h9_from_line_validator_regression.py`.
3. **Delete the fixtures** — remove `examples/routing_from_*.json` if created.
4. **Revert documentation** — revert `docs/PROJECT_STATUS.md` and `docs/planning/correction_memory_and_rule_promotion_plan.md` to the pre-H.9 state.
5. **Delete the checkpoint** — remove `docs/checkpoints/phase_h9_from_line_validator_checkpoint.md` if created.
6. **Restore baseline** — ensure `769437d` (or the then-current baseline) is restored as the functional baseline in all docs.
7. **Verify regression** — run the 30 pre-H.9 suites and confirm all pass.

Rollback should require **no more than 3 file deletions/reverts and one regression run**.

---

## 20. Open Questions Needing Approval

| # | Question | Default if Unanswered |
|---|---|---|
| 1 | **Should Phase H.9 implement advisory validator enforcement for `CCI-ROUTE-011`, or remain planning-only?** | Default: planning-only until user explicitly approves implementation. |
| 2 | **Should the `window_envelope` flag name be `window_envelope`, `envelope_type`, or something else?** | Default: `window_envelope` (boolean, simplest, backward compatible). |
| 3 | **Should `multiple_address_letter` be added to the validator's type-check whitelist, or remain excluded?** | Default: excluded. Proven only for `standard_letter` per the manual text. |
| 4 | **Should the targeted runner verify interaction with existing `CCI-ROUTE-010` office-code checks?** | Default: yes — include a check that runs both ROUTE-010 and ROUTE-011 on the same payload and confirms both produce independent findings. |
| 5 | **Should the advisory message include remediation guidance ("add a From line"), or only the rule citation?** | Default: include brief remediation guidance plus the window-envelope exception note. |
| 6 | **Should `doc_type` absence cause the check to skip (conservative) or attempt inference (aggressive)?** | Default: skip. Absence of `doc_type` is ambiguous; conservative behavior prevents false positives. |
| 7 | **Should the H.9 runner include a check that the catalog entry `CCI-ROUTE-011` still exists and is unchanged?** | Default: yes — cross-phase regression protection. |
| 8 | **If false positives are detected after merge, what is the correct reversion path?** | Default: (a) `git revert` of the implementation commit as primary; (b) update the helper to skip additional edge cases as secondary. |

---

## Recommended Decision Summary

| Decision | Recommended Default |
|---|---|
| **Implement advisory validator for CCI-ROUTE-011?** | **Yes, if user approves** — follows H.2/H.4 precedent; low-risk, deterministic, narrow scope. |
| **Enforcement level** | **Advisory (non-blocking)** — no error-level in H.9. |
| **Implementation target** | `src/cci_routing_validate.py` — add `_check_from_line_required()` helper. |
| **Window-envelope flag** | `window_envelope: bool` in payload; default `False`; suppresses advisory when `True`. |
| **Document-type scope** | `DT_STD_LTR` and `"standard_letter"` only. All other types skipped. |
| **Regression coverage if implemented** | 31-suite gate (30 existing + 1 new H.9 runner with ~18 checks). |
| **Rollback risk** | Very low — one helper function (~15 lines), one runner file, 8 synthetic fixtures. |

---

## Recommended Implementation Target (If Approved)

| Attribute | Value |
|---|---|
| Implementation target | `validator_update` |
| Target file | `src/cci_routing_validate.py` |
| Helper function | `_check_from_line_required(payload)` |
| Call site | `validate_cci_routing()`, after existing checks |
| Enforcement level | `advisory` (non-blocking) |
| Message code | `CCI-ROUTE-011 (advisory)` |
| Catalog severity | `error` (unchanged from H.8) |
| Expected new runner | `tools/run_phase_h9_from_line_validator_regression.py` |
| Expected new fixtures | `examples/routing_from_*.json` (6+) |
| Expected regression gate | 31 suites |

---

## Recommended Regression Gate

- **If planning-only:** 30 suites (current gate, no changes).
- **If advisory validator implemented:** 31 suites (30 existing + 1 new H.9 runner).
- **All suites must pass before any commit.**

---

## Open Questions Needing Approval

1. Should Phase H.9 implement advisory validator enforcement for `CCI-ROUTE-011`, or remain planning-only?
2. Should the `window_envelope` flag be named `window_envelope`, `envelope_type`, or another name?
3. Should `multiple_address_letter` be included in the validator's document-type whitelist?
4. Should the advisory message include remediation guidance or only the rule citation?
5. Should `doc_type` absence cause the check to skip or attempt inference?
6. Should the H.9 runner verify catalog entry preservation (cross-phase regression)?
7. If `CCI-ROUTE-011` validator enforcement is rejected, should the project pivot to a fourth catalog pilot, feature-flag design, or keep CCI-ROUTE-010 advisory indefinitely?

---

End of Phase H.9 / Phase I.8 — Advisory Validator Enforcement for CCI-ROUTE-011 (From-Line Required) Plan.
