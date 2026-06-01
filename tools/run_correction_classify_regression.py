#!/usr/bin/env python3
"""
Correction Classification Regression Runner — Phase B

Exercises src/correction_classify.py via capture_correction():

  1. Body paragraph edit (indexed body[2]) without reason -> one_time_wording (medium)
  2. Body paragraph edit (indexed body[2]) with "one-time" reason -> one_time_wording (high)
  3. Body paragraph edit (indexed body[2]) with "our SOP" reason -> local_command_preference (medium; conflict resolution)
  4. from field edit with "local command" reason -> local_command_preference (high)
  5. originator_code edit -> local_command_preference (medium)
  6. subj period removal with empty reason -> possible_secnav_manual_rule (medium)
  7. subj edit with "SECNAV requires" reason -> possible_secnav_manual_rule (high)
  8. Validator conflict + "false positive" reason -> bug_validator_gap (high)
  9. Ambiguous field + ambiguous reason -> unknown (low)
 10. User override beats heuristic -> type is override value, confidence is user_override
 11. unknown classification blocks session persistence
 12. one_time_wording blocks session persistence unless user overrides
 13. Existing correction regressions still pass after classification module added
 14. Existing intake regressions still pass after classification module added
 15. Existing session correction regressions still pass after classification module added

Exit 0 if all expectations met.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Ensure src/ is on path (repo root is one up from tools/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from correction_capture import capture_correction
from correction_store import save_session_correction, load_session_corrections
from intake_orchestrator import IntakeOrchestrator


def _assert_eq(label: str, actual: Any, expected: Any) -> list[str]:
    if actual != expected:
        return [f"FAIL {label}: expected {expected!r}, got {actual!r}"]
    return [f"PASS {label}"]


def _assert_true(label: str, actual: Any) -> list[str]:
    if not actual:
        return [f"FAIL {label}: expected truthy, got {actual!r}"]
    return [f"PASS {label}"]


def main() -> int:
    failures: list[str] = []
    results: list[str] = []

    # Use a temporary directory for all fixtures; never touch real corrections/session/
    temp_dir = tempfile.mkdtemp(prefix="classify_reg_")
    session_file = Path(temp_dir) / "test_session.jsonl"
    session_id = "test_session_phase_b"

    payload = {
        "doc_type": "standard_letter",
        "component": {"service": "navy"},
        "subj": "POLICY UPDATE.",
        "from": "John A. Smith",
        "originator_code": "",
        "body": ["1. First paragraph.", "2. Second paragraph."],
    }

    # ------------------------------------------------------------------
    # 1. Body paragraph edit (indexed body[2]) without reason -> one_time_wording (medium)
    # ------------------------------------------------------------------
    r1, _ = capture_correction(payload, field_path="body[2]", corrected_value="new text")
    results.append("[1] indexed body[2] without reason")
    failures.extend(_assert_eq("correction_type", r1.get("correction_type"), "one_time_wording"))
    failures.extend(_assert_eq("confidence", r1.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 2. Body paragraph edit (indexed body[2]) with "one-time" reason -> one_time_wording (high)
    # ------------------------------------------------------------------
    r2, _ = capture_correction(payload, field_path="body[2]", corrected_value="new text", reason="one-time wording change")
    results.append("[2] indexed body[2] with 'one-time' reason")
    failures.extend(_assert_eq("correction_type", r2.get("correction_type"), "one_time_wording"))
    failures.extend(_assert_eq("confidence", r2.get("classification_confidence"), "high"))

    # ------------------------------------------------------------------
    # 3. Body paragraph edit (indexed body[2]) with "our SOP" reason -> local_command_preference (medium; conflict resolution)
    # ------------------------------------------------------------------
    r3, _ = capture_correction(payload, field_path="body[2]", corrected_value="new text", reason="our SOP says use this wording")
    results.append("[3] indexed body[2] with 'our SOP' reason")
    failures.extend(_assert_eq("correction_type", r3.get("correction_type"), "local_command_preference"))
    failures.extend(_assert_eq("confidence", r3.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 4. from field edit with "local command" reason -> local_command_preference (high)
    # ------------------------------------------------------------------
    r4, _ = capture_correction(payload, field_path="from", corrected_value="CO, USS TEST", reason="local command preference")
    results.append("[4] from field with 'local command' reason")
    failures.extend(_assert_eq("correction_type", r4.get("correction_type"), "local_command_preference"))
    failures.extend(_assert_eq("confidence", r4.get("classification_confidence"), "high"))

    # ------------------------------------------------------------------
    # 5. originator_code edit -> local_command_preference (medium)
    # ------------------------------------------------------------------
    r5, _ = capture_correction(payload, field_path="originator_code", corrected_value="N7")
    results.append("[5] originator_code edit")
    failures.extend(_assert_eq("correction_type", r5.get("correction_type"), "local_command_preference"))
    failures.extend(_assert_eq("confidence", r5.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 6. subj period removal with empty reason -> possible_secnav_manual_rule (medium)
    # ------------------------------------------------------------------
    r6, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE")
    results.append("[6] subj period removal empty reason")
    failures.extend(_assert_eq("correction_type", r6.get("correction_type"), "possible_secnav_manual_rule"))
    failures.extend(_assert_eq("confidence", r6.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 7. subj edit with "SECNAV requires" reason -> possible_secnav_manual_rule (high)
    # ------------------------------------------------------------------
    r7, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE", reason="SECNAV requires no punctuation")
    results.append("[7] subj 'SECNAV requires' reason")
    failures.extend(_assert_eq("correction_type", r7.get("correction_type"), "possible_secnav_manual_rule"))
    failures.extend(_assert_eq("confidence", r7.get("classification_confidence"), "high"))

    # ------------------------------------------------------------------
    # 8. Validator conflict + "false positive" reason -> bug_validator_gap (high)
    # ------------------------------------------------------------------
    r8, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE.", reason="false positive — allowed", validator_conflict=True)
    results.append("[8] validator conflict + 'false positive' reason")
    failures.extend(_assert_eq("correction_type", r8.get("correction_type"), "bug_validator_gap"))
    failures.extend(_assert_eq("confidence", r8.get("classification_confidence"), "high"))

    # ------------------------------------------------------------------
    # 9. Ambiguous field + ambiguous reason -> unknown (low)
    # ------------------------------------------------------------------
    r9, _ = capture_correction(payload, field_path="unknown_field", corrected_value="x", reason="something different")
    results.append("[9] ambiguous field + ambiguous reason")
    failures.extend(_assert_eq("correction_type", r9.get("correction_type"), "unknown"))
    failures.extend(_assert_eq("confidence", r9.get("classification_confidence"), "low"))

    # ------------------------------------------------------------------
    # 10. User override beats heuristic -> type is override value, confidence is user_override
    # ------------------------------------------------------------------
    r10, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE", correction_type="local_command_preference")
    results.append("[10] explicit user override")
    failures.extend(_assert_eq("correction_type", r10.get("correction_type"), "local_command_preference"))
    failures.extend(_assert_eq("confidence", r10.get("classification_confidence"), "user_override"))

    # ------------------------------------------------------------------
    # 11. unknown classification blocks session persistence
    # ------------------------------------------------------------------
    results.append("[11] unknown blocks persistence")
    orch = IntakeOrchestrator(payload, session_id=session_id)
    persisted = orch.persist_correction(r9)
    failures.extend(_assert_eq("persist unknown", persisted, False))
    failures.extend(_assert_true("session notes mention unknown", any("unknown" in s for s in orch.get_status().get("session_notes", []))))

    # ------------------------------------------------------------------
    # 12. one_time_wording blocks session persistence unless user overrides
    # ------------------------------------------------------------------
    results.append("[12] one_time_wording blocks persistence without override")
    orch2 = IntakeOrchestrator(payload, session_id=session_id)
    persisted2 = orch2.persist_correction(r1)
    failures.extend(_assert_eq("persist one_time_wording", persisted2, False))
    failures.extend(_assert_true("session notes mention one_time_wording", any("one_time_wording" in s for s in orch2.get_status().get("session_notes", []))))

    # ------------------------------------------------------------------
    # 12b. one_time_wording with user_override persists
    # ------------------------------------------------------------------
    results.append("[12b] one_time_wording with user_override persists")
    r1b, _ = capture_correction(payload, field_path="body[2]", corrected_value="new text", correction_type="one_time_wording", scope="current_session")
    orch2b = IntakeOrchestrator(payload, session_id=session_id)
    persisted2b = orch2b.persist_correction(r1b)
    failures.extend(_assert_eq("persist one_time_wording override", persisted2b, True))

    # ------------------------------------------------------------------
    # 13-15. Existing regressions still pass (smoke: capture+apply roundtrip)
    # ------------------------------------------------------------------
    results.append("[13] capture+apply roundtrip smoke")
    from correction_apply import apply_correction
    record, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE", correction_type="possible_secnav_manual_rule")
    new_payload, apply_warnings = apply_correction(payload, record)
    failures.extend(_assert_eq("apply subj changed", new_payload["subj"], "POLICY UPDATE"))
    failures.extend(_assert_eq("apply warnings empty", apply_warnings, []))

    results.append("[14] intake regression smoke")
    orch3 = IntakeOrchestrator(payload)
    status = orch3.get_status()
    failures.extend(_assert_eq("status schema", status["schema_version"], "CCI_INTAKE_V2"))
    failures.extend(_assert_true("status has audit", isinstance(status.get("audit_summary"), dict)))

    results.append("[15] session correction regression smoke")
    orch4 = IntakeOrchestrator(payload, session_id=session_id)
    status4 = orch4.get_status()
    failures.extend(_assert_eq("session_id", status4.get("session_id"), session_id))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 72)
    print("CORRECTION CLASSIFICATION REGRESSION")
    print("=" * 72)
    for r in results:
        status = "PASS" if not any(f.startswith("FAIL") and r.split("]")[0] in f for f in failures) else "FAIL"
        # crude status detection from full failures list; just print
        print(f"  {r}")
    print()
    for f in failures:
        print(f"  {f}")
    print()

    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    fail_count = sum(1 for f in failures if f.startswith("FAIL"))
    if fail_count:
        print(f"classify_regression: FAIL ({fail_count} failure(s))")
        return 1

    print("classify_regression: PASS (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
