#!/usr/bin/env python3
"""
Correction Classification Regression Runner — Phase B (isolated)

Exercises src/correction_classify.py via capture_correction() using a
TEMPORARY session store only.  Never touches the real corrections/session/
directory.

Regression checks:
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
 12b. one_time_wording with user_override persists
 13. capture+apply roundtrip smoke
 14. intake regression smoke
 15. session correction regression smoke
 16. local_command_preference + current_session persists
 17. possible_secnav_manual_rule + current_session persists
 18. bug_validator_gap + current_session persists
 19. validator_conflict=True without reason keywords -> bug_validator_gap (medium)
 20. Nested indexed body path body[0].text -> one_time_wording (medium)
 21. Unindexed body path -> possible_secnav_manual_rule (medium)

Exit 0 if all expectations met.
Exit 1 on any failure.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

# Ensure src/ is on path (repo root is one up from tools/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from correction_capture import capture_correction
from correction_store import save_session_correction, load_session_corrections, _SESSION_DIR as _ORIGINAL_SESSION_DIR
from intake_orchestrator import IntakeOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_eq(label: str, actual: Any, expected: Any) -> list[str]:
    if actual != expected:
        return [f"FAIL {label}: expected {expected!r}, got {actual!r}"]
    return [f"PASS {label}"]


def _assert_true(label: str, actual: Any) -> list[str]:
    if not actual:
        return [f"FAIL {label}: expected truthy, got {actual!r}"]
    return [f"PASS {label}"]


def _assert_in(label: str, needle: str, haystack: list[str]) -> list[str]:
    if any(needle in h for h in haystack):
        return [f"PASS {label}"]
    return [f"FAIL {label}: expected string containing {needle!r} in {haystack!r}"]


def _mk_orch(payload: dict[str, Any], session_id: str, temp_session_dir: Path) -> IntakeOrchestrator:
    """Create an IntakeOrchestrator that writes to the temp session dir."""
    import correction_store
    correction_store._SESSION_DIR = temp_session_dir  # type: ignore[attr-defined]
    correction_store._ensure_session_dir()  # type: ignore[attr-defined]
    return IntakeOrchestrator(payload, session_id=session_id)


def _restore_session_dir() -> None:
    import correction_store
    correction_store._SESSION_DIR = _ORIGINAL_SESSION_DIR  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    failures: list[str] = []
    results: list[str] = []

    # Use a temporary directory for ALL session I/O; never touch real corrections/session/
    temp_dir = Path(tempfile.mkdtemp(prefix="classify_reg_"))
    temp_session_dir = temp_dir / "session"
    temp_session_dir.mkdir(parents=True, exist_ok=True)

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
    r9_cs = copy.deepcopy(r9)
    r9_cs["scope"] = "current_session"
    orch = _mk_orch(payload, session_id, temp_session_dir)
    persisted = orch.persist_correction(r9_cs)
    failures.extend(_assert_eq("persist unknown", persisted, False))
    failures.extend(_assert_in("session notes mention unknown", "unknown", orch.get_status().get("session_notes", [])))

    # ------------------------------------------------------------------
    # 12. one_time_wording blocks session persistence unless user overrides
    # ------------------------------------------------------------------
    results.append("[12] one_time_wording blocks persistence without override")
    r1_cs = copy.deepcopy(r1)
    r1_cs["scope"] = "current_session"
    orch2 = _mk_orch(payload, session_id, temp_session_dir)
    persisted2 = orch2.persist_correction(r1_cs)
    failures.extend(_assert_eq("persist one_time_wording", persisted2, False))
    failures.extend(_assert_in("session notes mention one_time_wording", "one_time_wording", orch2.get_status().get("session_notes", [])))

    # ------------------------------------------------------------------
    # 12b. one_time_wording with user_override persists
    # ------------------------------------------------------------------
    results.append("[12b] one_time_wording with user_override persists")
    r1b, _ = capture_correction(payload, field_path="body[2]", corrected_value="new text", correction_type="one_time_wording", scope="current_session")
    orch2b = _mk_orch(payload, session_id, temp_session_dir)
    persisted2b = orch2b.persist_correction(r1b)
    failures.extend(_assert_eq("persist one_time_wording override", persisted2b, True))

    # ------------------------------------------------------------------
    # 13. capture+apply roundtrip smoke
    # ------------------------------------------------------------------
    results.append("[13] capture+apply roundtrip smoke")
    from correction_apply import apply_correction
    record, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE", correction_type="possible_secnav_manual_rule")
    new_payload, apply_warnings = apply_correction(payload, record)
    failures.extend(_assert_eq("apply subj changed", new_payload["subj"], "POLICY UPDATE"))
    failures.extend(_assert_eq("apply warnings empty", apply_warnings, []))

    # ------------------------------------------------------------------
    # 14. intake regression smoke
    # ------------------------------------------------------------------
    results.append("[14] intake regression smoke")
    orch3 = IntakeOrchestrator(payload)
    status = orch3.get_status()
    failures.extend(_assert_eq("status schema", status["schema_version"], "CCI_INTAKE_V2"))
    failures.extend(_assert_true("status has audit", isinstance(status.get("audit_summary"), dict)))

    # ------------------------------------------------------------------
    # 15. session correction regression smoke
    # ------------------------------------------------------------------
    results.append("[15] session correction regression smoke")
    orch4 = _mk_orch(payload, session_id, temp_session_dir)
    status4 = orch4.get_status()
    failures.extend(_assert_eq("session_id", status4.get("session_id"), session_id))

    # ------------------------------------------------------------------
    # 16. local_command_preference + current_session persists
    # ------------------------------------------------------------------
    results.append("[16] local_command_preference + current_session persists")
    r16, _ = capture_correction(payload, field_path="from", corrected_value="CO, USS TEST", reason="local command preference", scope="current_session")
    orch16 = _mk_orch(payload, session_id, temp_session_dir)
    p16 = orch16.persist_correction(r16)
    failures.extend(_assert_eq("persist local_command_preference", p16, True))
    loaded16, _ = load_session_corrections(session_id, exclude_rejected=True)
    failures.extend(_assert_true("loaded local_command_preference", any(c.get("field_path") == "from" for c in loaded16)))

    # ------------------------------------------------------------------
    # 17. possible_secnav_manual_rule + current_session persists
    # ------------------------------------------------------------------
    results.append("[17] possible_secnav_manual_rule + current_session persists")
    r17, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE", reason="SECNAV requires no punctuation", scope="current_session")
    orch17 = _mk_orch(payload, session_id, temp_session_dir)
    p17 = orch17.persist_correction(r17)
    failures.extend(_assert_eq("persist possible_secnav_manual_rule", p17, True))
    loaded17, _ = load_session_corrections(session_id, exclude_rejected=True)
    failures.extend(_assert_true("loaded possible_secnav_manual_rule", any(c.get("field_path") == "subj" and c.get("correction_type") == "possible_secnav_manual_rule" for c in loaded17)))

    # ------------------------------------------------------------------
    # 18. bug_validator_gap + current_session persists
    # ------------------------------------------------------------------
    results.append("[18] bug_validator_gap + current_session persists")
    r18, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE.", reason="false positive", validator_conflict=True, scope="current_session")
    orch18 = _mk_orch(payload, session_id, temp_session_dir)
    p18 = orch18.persist_correction(r18)
    failures.extend(_assert_eq("persist bug_validator_gap", p18, True))
    loaded18, _ = load_session_corrections(session_id, exclude_rejected=True)
    failures.extend(_assert_true("loaded bug_validator_gap", any(c.get("field_path") == "subj" and c.get("correction_type") == "bug_validator_gap" for c in loaded18)))

    # ------------------------------------------------------------------
    # 19. validator_conflict=True without reason keywords -> bug_validator_gap (medium)
    # ------------------------------------------------------------------
    results.append("[19] validator_conflict=True without reason keywords")
    r19, _ = capture_correction(payload, field_path="subj", corrected_value="POLICY UPDATE.", reason="", validator_conflict=True)
    failures.extend(_assert_eq("correction_type", r19.get("correction_type"), "bug_validator_gap"))
    failures.extend(_assert_eq("confidence", r19.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 20. Nested indexed body path body[0].text -> one_time_wording (medium)
    # ------------------------------------------------------------------
    results.append("[20] nested indexed body path body[0].text")
    r20, _ = capture_correction(payload, field_path="body[0].text", corrected_value="updated paragraph")
    failures.extend(_assert_eq("correction_type", r20.get("correction_type"), "one_time_wording"))
    failures.extend(_assert_eq("confidence", r20.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # 21. Unindexed body path -> possible_secnav_manual_rule (medium)
    # ------------------------------------------------------------------
    results.append("[21] unindexed body path")
    r21, _ = capture_correction(payload, field_path="body", corrected_value="updated body text")
    failures.extend(_assert_eq("correction_type", r21.get("correction_type"), "possible_secnav_manual_rule"))
    failures.extend(_assert_eq("confidence", r21.get("classification_confidence"), "medium"))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 72)
    print("CORRECTION CLASSIFICATION REGRESSION")
    print("=" * 72)
    for r in results:
        print(f"  {r}")
    print()
    for f in failures:
        print(f"  {f}")
    print()

    # Cleanup
    _restore_session_dir()
    shutil.rmtree(temp_dir, ignore_errors=True)

    fail_count = sum(1 for f in failures if f.startswith("FAIL"))
    if fail_count:
        print(f"classify_regression: FAIL ({fail_count} failure(s))")
        return 1

    print("classify_regression: PASS (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
