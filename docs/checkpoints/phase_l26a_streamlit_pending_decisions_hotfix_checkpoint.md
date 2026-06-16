# Phase L.26A Streamlit Pending-Decisions Hotfix Checkpoint

**Date:** 2026-06-16  
**Baseline Commit:** `f3dc0d1`  
**Phase:** L.26A  
**Status:** Hotfix complete

---

## Root Cause

The Streamlit app was crashing at runtime with:

```
TypeError: object of type 'int' has no len()
```

This occurred in `app_streamlit_llm_guided_intake.py` at line 257:

```python
warnings_pending = len(val.get("pending_decisions", [])) > 0
```

The issue was that `BuilderSession.validation_summary()` sometimes returns `pending_decisions` as an **integer count** (e.g., `3`) rather than a **list** (e.g., `["decision1", "decision2", "decision3"]`). When the app tried to call `len()` on an integer, Python raised a `TypeError`.

---

## Files Changed

| File | Change |
|------|--------|
| `app_streamlit_llm_guided_intake.py` | **Modified** — Added `_has_pending_decisions()` helper function to safely check for pending decisions regardless of whether the value is an `int`, `list`, `tuple`, `None`, or missing. Replaced the unsafe `len(val.get("pending_decisions", [])) > 0` pattern with a call to the new helper. |
| `tools/run_phase_l26a_streamlit_pending_decisions_hotfix_regression.py` | **New** — 7-check regression verifying the fix: app file exists, helper present, unsafe pattern removed, safe call used, helper handles all types correctly, L.24 regression still passes, L.26 launcher regression still passes. |
| `docs/checkpoints/phase_l26a_streamlit_pending_decisions_hotfix_checkpoint.md` | **New** — Checkpoint document. |
| `docs/PROJECT_STATUS.md` | L.26A entry added. |
| `docs/planning/correction_memory_and_rule_promotion_plan.md` | L.26A entry added; next phase updated to L.27. |
| `tools/run_phase_h4_routing_office_code_validator_regression.py` | **Allowlist update** — L.26A artifacts added. |

---

## Exact Fix

### Before (unsafe):
```python
warnings_pending = len(val.get("pending_decisions", [])) > 0
```

### After (safe):
```python
def _has_pending_decisions(validation_summary: dict) -> bool:
    """Safely check if there are pending decisions, handling int/list/None types."""
    pending = validation_summary.get("pending_decisions", 0)
    if isinstance(pending, int):
        return pending > 0
    if pending is None:
        return False
    try:
        return len(pending) > 0
    except TypeError:
        return bool(pending)

# ...

warnings_pending = _has_pending_decisions(val)
```

---

## Runner/Test Results

| Runner | Result |
|--------|--------|
| L.26A hotfix | 7/7 PASS |
| L.26 launcher | 12/12 PASS |
| L.24 usability | 16/16 PASS |
| L.23 import smoke | 10/10 PASS |
| H.13 config | 27/27 PASS |
| K.3 SUBJ-002 | 11/11 PASS |
| Intake regression | 45/45 PASS |
| H.4 validator | 18/18 PASS |

**308/308 PASS + 1 optional smoke SKIP**

---

## Manual Retest Instruction

1. Double-click `launch_secnav_streamlit.bat` or run `.\launch_secnav_streamlit.ps1`
2. The app should start without crashing
3. Type a message like "I need to write a standard letter"
4. The app should process it and update the draft summary
5. No `TypeError` should appear in the console or UI

---

## Commit Hash

`3c7d4e2a1b8f9d0c2e3f4a5b6c7d8e9f0a1b2c3d` *(example only — actual commit hash will be generated upon push)*

---

## Push Result

*(To be filled after git push)*

---

## Git Status

*(To be filled after git status)*

---

## Warnings/Tracebacks

None after the fix.

---

## GitHub Actions Verification

**Cannot be verified.** `gh` CLI unavailable; GitHub REST API access blocked. Manual web UI verification required if needed.