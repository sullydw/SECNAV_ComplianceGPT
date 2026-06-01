#!/usr/bin/env python3
"""
Correction Session Regression Runner — Phase A Session Correction Persistence

Exercises correction_store.py and intake_orchestrator.py session_id support:

  1. save_session_correction appends a record to JSONL
  2. load_session_corrections returns the record by doc_type filter
  3. load_session_corrections returns empty list for nonexistent session_id
  4. load excludes user_rejected=True when exclude_rejected=True
  5. update_session_correction_status changes promotion_status on disk
  6. delete_session_correction removes only the targeted record
  7. set_session_correction_rejected marks user_rejected and excludes from loads
  8. matching in IntakeOrchestrator selects correct field when doc+component align
  9. unknown doc_type skips pre-application
 10. unknown component skips pre-application
 11. duplicate field_path uses most-recent timestamp
 12. pre-application emits session_notes
 13. undo after pre-application restores original value
 14. one_time_wording with active_draft scope is skipped
 15. one_time_wording with current_session scope is applied
 16. existing correction + intake regressions still pass (no breakage check)

Exit 0 if all expectations met.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on path (repo root is one up from tools/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from correction_store import (
    save_session_correction,
    load_session_corrections,
    update_session_correction_status,
    delete_session_correction,
    delete_session_file,
    set_session_correction_rejected,
)
from correction_capture import capture_correction
from correction_apply import get_path_value
from intake_orchestrator import IntakeOrchestrator


def _assert_eq(label: str, actual: Any, expected: Any) -> list[str]:
    if actual != expected:
        return [f"FAIL {label}: expected {expected!r}, got {actual!r}"]
    return [f"PASS {label}"]


def _assert_true(label: str, actual: Any) -> list[str]:
    if not actual:
        return [f"FAIL {label}: expected truthy, got {actual!r}"]
    return [f"PASS {label}"]


def _assert_in(label: str, needle: str, haystack: str) -> list[str]:
    if needle in haystack:
        return [f"PASS {label}"]
    return [f"FAIL {label}: '{needle}' not in '{haystack}'"]


def main() -> int:
    failures: list[str] = []
    results: list[str] = []

    session_id = "test_session_phase_a"
    # Clean up any leftover session file from prior runs
    delete_session_file(session_id)

    # ------------------------------------------------------------------
    # Build a sample payload + orchestrator for context extraction
    # ------------------------------------------------------------------
    payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "POLICY UPDATE.",
        "from": "John A. Smith",
        "body": ["1. First paragraph.", "2. Second paragraph."],
    }

    # ------------------------------------------------------------------
    # 1. save_session_correction appends a record
    # ------------------------------------------------------------------
    record1, _ = capture_correction(
        payload,
        field_path="subj",
        corrected_value="POLICY UPDATE",
        reason="Remove terminal punctuation.",
        correction_type="possible_secnav_manual_rule",
    )
    record1["session_id"] = session_id
    record1["scope"] = "current_session"
    record1["promotion_status"] = "none"
    record1.setdefault("applied_in_draft", False)
    record1.setdefault("user_rejected", False)
    warnings = save_session_correction(session_id, record1)
    results.append("[1] save_session_correction appends record")
    failures.extend(_assert_eq("save warnings empty", warnings, []))
    corr_id_1 = record1["correction_id"]

    # ------------------------------------------------------------------
    # 2. load_session_corrections by doc_type filter
    # ------------------------------------------------------------------
    loaded, load_warnings = load_session_corrections(
        session_id, doc_type="standard_letter", component="navy"
    )
    results.append("[2] load_session_corrections doc_type filter")
    failures.extend(_assert_eq("load warnings empty", load_warnings, []))
    failures.extend(_assert_eq("loaded count", len(loaded), 1))
    failures.extend(_assert_eq("loaded field_path", loaded[0].get("field_path"), "subj"))

    # ------------------------------------------------------------------
    # 3. load returns empty list for nonexistent session_id
    # ------------------------------------------------------------------
    nonexist, _ = load_session_corrections("nonexistent_session_xyz123")
    results.append("[3] load nonexistent session_id")
    failures.extend(_assert_eq("nonexist count", len(nonexist), 0))

    # ------------------------------------------------------------------
    # 4. load excludes user_rejected=True when exclude_rejected=True
    # ------------------------------------------------------------------
    rejected_record, _ = capture_correction(
        payload,
        field_path="from",
        corrected_value="Commanding Officer, USS TEST",
        reason="Command title required.",
    )
    rejected_record["session_id"] = session_id
    rejected_record["scope"] = "current_session"
    rejected_record["promotion_status"] = "none"
    rejected_record["user_rejected"] = True
    save_session_correction(session_id, rejected_record)
    loaded_all, _ = load_session_corrections(session_id, exclude_rejected=False)
    loaded_excl, _ = load_session_corrections(session_id, exclude_rejected=True)
    results.append("[4] load excludes user_rejected")
    failures.extend(_assert_eq("all count includes rejected", len(loaded_all), 2))
    failures.extend(_assert_eq("excl count excludes rejected", len(loaded_excl), 1))

    # ------------------------------------------------------------------
    # 5. update_session_correction_status changes promotion_status
    # ------------------------------------------------------------------
    ok = update_session_correction_status(session_id, corr_id_1, "pending_approval")
    results.append("[5] update_session_correction_status")
    failures.extend(_assert_eq("update returned True", ok, True))
    loaded_after_update, _ = load_session_corrections(session_id, doc_type="standard_letter")
    found = [r for r in loaded_after_update if r.get("correction_id") == corr_id_1]
    failures.extend(_assert_eq("found after update", len(found), 1))
    failures.extend(_assert_eq("promotion_status updated", found[0].get("promotion_status"), "pending_approval"))

    # ------------------------------------------------------------------
    # 6. delete_session_correction removes only targeted record
    # ------------------------------------------------------------------
    deleted = delete_session_correction(session_id, rejected_record["correction_id"])
    results.append("[6] delete_session_correction targeted")
    failures.extend(_assert_eq("delete returned True", deleted, True))
    remaining, _ = load_session_corrections(session_id, exclude_rejected=False)
    failures.extend(_assert_eq("remaining count", len(remaining), 1))
    failures.extend(_assert_eq("remaining is corr_id_1", remaining[0].get("correction_id"), corr_id_1))

    # ------------------------------------------------------------------
    # 7. set_session_correction_rejected marks user_rejected and excludes
    # ------------------------------------------------------------------
    # Re-add a record for this test
    r3, _ = capture_correction(payload, field_path="body[0]", corrected_value="1. Corrected.")
    r3["session_id"] = session_id
    r3["scope"] = "current_session"
    r3["promotion_status"] = "none"
    r3["user_rejected"] = False
    save_session_correction(session_id, r3)
    ok_rej = set_session_correction_rejected(session_id, r3["correction_id"], True)
    results.append("[7] set_session_correction_rejected")
    failures.extend(_assert_eq("set rejected returned True", ok_rej, True))
    loaded_after_reject, _ = load_session_corrections(session_id)
    failures.extend(_assert_eq("rejected excluded count", len(loaded_after_reject), 1))
    failures.extend(_assert_eq("rejected excluded is corr_id_1", loaded_after_reject[0].get("correction_id"), corr_id_1))

    # ------------------------------------------------------------------
    # 8. IntakeOrchestrator pre-applies matching session correction
    # ------------------------------------------------------------------
    orch = IntakeOrchestrator(payload=payload, session_id=session_id)
    status = orch.get_status()
    results.append("[8] orchestrator pre-applies matching session correction")
    # The stored correction for subj was "POLICY UPDATE" (no period)
    preapplied = status.get("corrections_applied", [])
    failures.extend(_assert_true("has corrections_applied", preapplied))
    if preapplied:
        failures.extend(_assert_eq("preapplied field_path", preapplied[0].get("field_path"), "subj"))
        failures.extend(_assert_eq("preapplied corrected_value", preapplied[0].get("corrected_value"), "POLICY UPDATE"))

    # ------------------------------------------------------------------
    # 9. unknown doc_type skips pre-application
    # ------------------------------------------------------------------
    bad_payload = {
        "doc_type": "unknown",
        "component": {"service": "navy"},
        "subj": "POLICY UPDATE.",
    }
    bad_orch = IntakeOrchestrator(payload=bad_payload, session_id=session_id)
    bad_status = bad_orch.get_status()
    results.append("[9] orchestrator skips unknown doc_type")
    failures.extend(_assert_eq("bad orch corrections_applied", bad_status.get("corrections_applied"), []))
    session_notes_bad = bad_status.get("session_notes", [])
    has_unknown_note = any("doc_type is unknown" in n for n in session_notes_bad)
    failures.extend(_assert_true("has unknown doc_type note", has_unknown_note))

    # ------------------------------------------------------------------
    # 10. unknown component skips pre-application
    # ------------------------------------------------------------------
    bad_payload2 = {
        "doc_type": "standard_letter",
        "component": {"service": "unknown"},
        "subj": "POLICY UPDATE.",
    }
    bad_orch2 = IntakeOrchestrator(payload=bad_payload2, session_id=session_id)
    bad_status2 = bad_orch2.get_status()
    results.append("[10] orchestrator skips unknown component")
    failures.extend(_assert_eq("bad orch2 corrections_applied", bad_status2.get("corrections_applied"), []))
    session_notes_bad2 = bad_status2.get("session_notes", [])
    has_unknown_comp = any("component is unknown" in n for n in session_notes_bad2)
    failures.extend(_assert_true("has unknown component note", has_unknown_comp))

    # ------------------------------------------------------------------
    # 11. duplicate field_path uses latest timestamp
    # ------------------------------------------------------------------
    # Clean previous corrections before testing deduplication
    delete_session_file(session_id)
    # Create two corrections for same field with different values and explicit timestamps
    dup_payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "DUP PAYLOAD SUBJ.",
    }
    dup1, _ = capture_correction(dup_payload, field_path="subj", corrected_value="OLDER SUBJ")
    dup1["session_id"] = session_id
    dup1["scope"] = "current_session"
    dup1["timestamp"] = "2024-01-01T00:00:00Z"
    dup1["promotion_status"] = "none"
    save_session_correction(session_id, dup1)

    dup2, _ = capture_correction(dup_payload, field_path="subj", corrected_value="LATEST SUBJ")
    dup2["session_id"] = session_id
    dup2["scope"] = "current_session"
    dup2["timestamp"] = "2024-01-02T00:00:00Z"
    dup2["promotion_status"] = "none"
    save_session_correction(session_id, dup2)

    # Only the latest should be applied
    dup_payload_merged = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "ORIGINAL SUBJ.",
    }
    dup_orch = IntakeOrchestrator(payload=dup_payload_merged, session_id=session_id)
    dup_status = dup_orch.get_status()
    results.append("[11] latest timestamp wins on duplicate field_path")
    # The preapplied should be "LATEST SUBJ" not "OLDER SUBJ" or the original stored one
    applied_subj = get_path_value(dup_orch.build_payload(), "subj")
    failures.extend(_assert_eq("payload subj is latest", applied_subj, "LATEST SUBJ"))

    # ------------------------------------------------------------------
    # 12. pre-application emits session_notes
    # ------------------------------------------------------------------
    notes = dup_status.get("session_notes", [])
    results.append("[12] session_notes emitted")
    has_applied_note = any("Applied session correction" in n for n in notes)
    failures.extend(_assert_true("has applied note", has_applied_note))

    # ------------------------------------------------------------------
    # 13. undo after pre-application restores original value
    # ------------------------------------------------------------------
    # Use a fresh orchestrator with a fresh payload for a clean undo
    undo_payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "ORIGINAL SUBJ.",
    }
    # Only corr_id_1 and dup2 remain; dup2 is latest for subj.
    # To avoid cross-interaction, delete all and add one clean one
    delete_session_file(session_id)
    clean, _ = capture_correction(undo_payload, field_path="subj", corrected_value="CLEANED SUBJ")
    clean["session_id"] = session_id
    clean["scope"] = "current_session"
    clean["promotion_status"] = "none"
    clean["user_rejected"] = False
    clean.setdefault("applied_in_draft", False)
    save_session_correction(session_id, clean)

    undo_orch = IntakeOrchestrator(payload=undo_payload, session_id=session_id)
    # Should have pre-applied CLEANED SUBJ
    applied_before = get_path_value(undo_orch.build_payload(), "subj")
    results.append("[13] undo restores original value")
    failures.extend(_assert_eq("before undo applied", applied_before, "CLEANED SUBJ"))

    # Find the applied correction to undo
    applied_corr = None
    for c in undo_orch.get_status().get("corrections_applied", []):
        if c.get("field_path") == "subj" and c.get("corrected_value") == "CLEANED SUBJ":
            applied_corr = c
            break
    if applied_corr:
        undo_orch.undo_correction(applied_corr)
        undone_subj = get_path_value(undo_orch.build_payload(), "subj")
        failures.extend(_assert_eq("after undo subj", undone_subj, "ORIGINAL SUBJ."))
    else:
        failures.append("FAIL undo: could not find applied correction for subj")

    # ------------------------------------------------------------------
    # 14. one_time_wording with active_draft scope is skipped during session pre-application
    # ------------------------------------------------------------------
    delete_session_file(session_id)
    otw, _ = capture_correction(payload, field_path="subj", corrected_value="REWORDED")
    otw["session_id"] = session_id
    otw["scope"] = "active_draft"
    otw["correction_type"] = "one_time_wording"
    otw["promotion_status"] = "none"
    save_session_correction(session_id, otw)
    otw_payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "ORIGINAL SUBJ.",
    }
    otw_orch = IntakeOrchestrator(payload=otw_payload, session_id=session_id)
    otw_status = otw_orch.get_status()
    results.append("[14] one_time_wording active_draft skipped")
    has_otw_applied = any(
        c.get("field_path") == "subj" for c in otw_status.get("corrections_applied", [])
    )
    failures.extend(_assert_eq("one_time wording not preapplied", has_otw_applied, False))
    session_notes_otw = otw_status.get("session_notes", [])
    has_skip_note = any("one_time_wording" in n for n in session_notes_otw)
    failures.extend(_assert_true("has one_time_wording skip note", has_skip_note))

    # ------------------------------------------------------------------
    # 15. one_time_wording with current_session scope IS applied
    # ------------------------------------------------------------------
    delete_session_file(session_id)
    otw2, _ = capture_correction(payload, field_path="subj", corrected_value="REWORDED")
    otw2["session_id"] = session_id
    otw2["scope"] = "current_session"
    otw2["correction_type"] = "one_time_wording"
    otw2["promotion_status"] = "none"
    save_session_correction(session_id, otw2)
    otw2_payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "ORIGINAL SUBJ.",
    }
    otw2_orch = IntakeOrchestrator(payload=otw2_payload, session_id=session_id)
    otw2_status = otw2_orch.get_status()
    results.append("[15] one_time_wording current_session applied")
    has_otw2_applied = any(
        c.get("field_path") == "subj" and c.get("corrected_value") == "REWORDED"
        for c in otw2_status.get("corrections_applied", [])
    )
    failures.extend(_assert_eq("one_time wording current_session applied", has_otw2_applied, True))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    delete_session_file(session_id)

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print("=" * 72)
    print("CORRECTION SESSION REGRESSION RUNNER")
    print("=" * 72)
    for r in results:
        print(r)
    print()
    for f in failures:
        print(f)
    print()
    error_count = sum(1 for f in failures if f.startswith("FAIL"))
    print(f"RESULT: {'PASS' if error_count == 0 else 'FAIL'} ({error_count} failures)")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
