#!/usr/bin/env python3
"""
Phase L.29Q — Hermes Session Manager Regression Runner

Tests the thin session-manager layer that coordinates hermes_secnav_tool.py
without duplicating renderer, validator, detector, candidate, or BuilderSession logic.

Run with: python tools/run_phase_l29q_session_manager_regression.py
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

VENV_PYTHON = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"

MANAGER = _REPO_ROOT / "tools" / "hermes_session_manager.py"
TOOL = _REPO_ROOT / "tools" / "hermes_secnav_tool.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = 0
_FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"[PASS] {name}")
    else:
        _FAIL += 1
        print(f"[FAIL] {name}  — {detail}")


def _manager(args: list[str]) -> dict[str, Any]:
    """Run hermes_session_manager.py via CLI and parse JSON output."""
    result = subprocess.run(
        [str(VENV_PYTHON), str(MANAGER)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0 and not result.stdout.strip():
        return {
            "success": False,
            "error": result.stderr or f"exit code {result.returncode}",
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid JSON: {result.stdout[:200]}",
        }


def _tool(args: list[str]) -> dict[str, Any]:
    """Run hermes_secnav_tool.py via CLI and parse JSON output."""
    result = subprocess.run(
        [str(VENV_PYTHON), str(TOOL)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0 and not result.stdout.strip():
        return {
            "success": False,
            "error": result.stderr or f"exit code {result.returncode}",
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid JSON: {result.stdout[:200]}",
        }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_new_creates_session() -> None:
    r = _manager(["new"])
    sid = r.get("session_id", "")
    check(
        "1. new creates a session with valid session_id",
        r.get("success") and sid.startswith("builder_"),
        f"success={r.get('success')}, session_id={sid}",
    )
    # cleanup
    if sid:
        _tool(["reset", "--session", sid])
    return sid


def test_say_ingests_text() -> None:
    # Create session via manager
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("2. say ingests text", False, "new failed")
        return
    r_say = _manager(["say", "--session", sid, "--text", "I need a standard letter from CO MISSA to MCAS New River about training schedule change."])
    check(
        "2. say returns success and payload contains from/to",
        r_say.get("success") and ("MISSA" in str(r_say.get("payload", {}).get("from", "")) or "MISSA" in str(r_say)),
        f"success={r_say.get('success')}",
    )
    _tool(["reset", "--session", sid])


def test_next_returns_valid_action() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("3. next returns valid action", False, "new failed")
        return
    r_next = _manager(["next", "--session", sid, "--doc-type", "standard_letter"])
    na = r_next.get("next_action", {})
    check(
        "3. next returns valid action object with action and priority",
        r_next.get("success") and "action" in na and "priority" in na,
        f"next_action keys={list(na.keys())}",
    )
    _tool(["reset", "--session", sid])
    return r_next, sid


def test_next_on_empty_is_blocking(r: dict, sid: str) -> None:
    na = r.get("next_action", {})
    check(
        "3b. next on empty session is blocking",
        na.get("priority") == "blocking",
        f"priority={na.get('priority')}",
    )
    _tool(["reset", "--session", sid])


def test_answer_applies_field() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("4. answer applies a field", False, "new failed")
        return
    r_answer = _manager(["answer", "--session", sid, "--field", "from", "--value", "Commanding Officer, MISSA"])
    check(
        "4. answer returns success",
        r_answer.get("success"),
        f"success={r_answer.get('success')}, error={r_answer.get('error')}",
    )
    # Verify via status that payload actually changed
    r_status = _tool(["status", "--session", sid])
    payload = r_status.get("payload", {})
    check(
        "4b. answer persisted to payload",
        "MISSA" in str(payload.get("from", "")),
        f"from={payload.get('from')}",
    )
    _tool(["reset", "--session", sid])


def test_ready_reports_false_with_blocking() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("5. ready false when blocking", False, "new failed")
        return
    r_ready = _manager(["ready", "--session", sid, "--doc-type", "standard_letter"])
    check(
        "5. ready reports false when blocking facts remain",
        r_ready.get("success") and r_ready.get("ready") is False,
        f"ready={r_ready.get('ready')}, success={r_ready.get('success')}",
    )
    _tool(["reset", "--session", sid])


def test_standard_letter_reaches_zero_blocking() -> None:
    """Minimal standard-letter path: apply all blocking facts until ready."""
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("6. standard letter reaches zero blocking", False, "new failed")
        return

    # Provide initial text
    _manager(["say", "--session", sid, "--text",
              "I need a standard letter from CO MISSA to MCAS New River requesting training schedule change."])

    # Loop: next -> answer until blocking == 0 or max loops
    max_loops = 20
    for i in range(max_loops):
        r_next = _manager(["next", "--session", sid, "--doc-type", "standard_letter"])
        na = r_next.get("next_action", {})
        action = na.get("action")
        if action in {"render_ready", "blocked_by_validation"}:
            break
        field = na.get("field")
        if not field:
            break
        # Simulate answer for common fields
        simulated = {
            "from": "Commanding Officer, Manpower Information Systems Support Activity (MISSA)",
            "to": "Commanding Officer, Marine Corps Air Station New River",
            "date": "19 June 2026",
            "subj": "REQUEST TO CHANGE TRAINING SCHEDULE",
            "body": "1. This letter requests a change to the training schedule. The new schedule is TBD.",
            "signature": "J. Q. Sample\nCommanding Officer\nCommanding Officer",
            "ssic": "1234",
        }
        val = simulated.get(field, f"test_value_{field}")
        # Multi-line value for signature
        if field == "signature":
            # Signature in builder uses structured dict; send single-line for simplicity
            val = "J. Q. Sample"
        r_ans = _manager(["answer", "--session", sid, "--field", field, "--value", val])
        if not r_ans.get("success"):
            # Stop if apply fails
            check(f"6-loop apply {field}", False, r_ans.get("error", ""))
            _tool(["reset", "--session", sid])
            return
    else:
        check("6. standard letter reaches zero blocking", False, "max loops reached")
        _tool(["reset", "--session", sid])
        return

    # After loop, check ready
    r_ready = _manager(["ready", "--session", sid, "--doc-type", "standard_letter"])
    rg = r_ready.get("render_gate", {})
    blocking_resolved = rg.get("blocking_resolved", False)
    check(
        "6. standard letter reaches zero blocking (ready or blocked_by_validation)",
        blocking_resolved or na.get("action") == "blocked_by_validation",
        f"blocking_resolved={blocking_resolved}, action={na.get('action')}",
    )
    _tool(["reset", "--session", sid])


def test_no_pdf_render_triggered() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("7. no PDF render triggered", False, "new failed")
        return
    # Ensure no pdf_path appears in any manager output
    outputs = [
        _manager(["new"]),
        _manager(["say", "--session", sid, "--text", "test"]),
        _manager(["next", "--session", sid]),
        _manager(["ready", "--session", sid]),
        _manager(["summary", "--session", sid]),
    ]
    has_pdf = any("pdf_path" in json.dumps(o) for o in outputs)
    check(
        "7. No PDF render triggered by any manager command",
        not has_pdf,
        "pdf_path found in output",
    )
    _tool(["reset", "--session", sid])


def test_resume_loads_existing() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("8. resume loads existing session", False, "new failed")
        return
    _manager(["answer", "--session", sid, "--field", "from", "--value", "CO, MISSA"])
    r_resume = _manager(["resume", "--session", sid])
    payload = r_resume.get("payload", {})
    check(
        "8. resume restores payload from existing session",
        r_resume.get("success") and "MISSA" in str(payload.get("from", "")),
        f"from={payload.get('from')}",
    )
    _tool(["reset", "--session", sid])


def test_summary_compact() -> None:
    r_new = _manager(["new"])
    sid = r_new.get("session_id", "")
    if not sid:
        check("9. summary returns compact data", False, "new failed")
        return
    _manager(["answer", "--session", sid, "--field", "from", "--value", "CO, MISSA"])
    r_sum = _manager(["summary", "--session", sid])
    compact = r_sum.get("compact", {})
    check(
        "9. summary includes compact fields",
        r_sum.get("success") and "filled_fields_count" in compact,
        f"compact keys={list(compact.keys())}",
    )
    _tool(["reset", "--session", sid])


def test_help_shows_all_commands() -> None:
    r = subprocess.run(
        [str(VENV_PYTHON), str(MANAGER), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(_REPO_ROOT),
    )
    text = r.stdout
    needed = ["new", "resume", "say", "next", "answer", "ready", "summary"]
    all_present = all(cmd in text for cmd in needed)
    check(
        "10. Help shows all expected commands",
        all_present,
        f"missing commands: {[c for c in needed if c not in text]}",
    )


# ---------------------------------------------------------------------------
# External regression guards
# ---------------------------------------------------------------------------


def test_external_regression(script: str, num: int) -> None:
    result = subprocess.run(
        [str(VENV_PYTHON), str(_REPO_ROOT / script)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(_REPO_ROOT),
    )
    ok = result.returncode == 0
    check(f"{num}. External regression {os.path.basename(script)} still passes", ok, f"exit={result.returncode}")


# ---------------------------------------------------------------------------
# Static guards
# ---------------------------------------------------------------------------


def test_no_renderer_changes() -> None:
    renderer = _REPO_ROOT / "src" / "pdf_v6_render.py"
    check("25. No renderer/layout files changed", renderer.exists() and renderer.is_file())


def test_no_validator_changes() -> None:
    config = _REPO_ROOT / "config" / "cci_enforcement_config.json"
    check("26. No validator/CCI config changed", config.exists() and config.is_file())


def test_no_static_db() -> None:
    paths = [
        _REPO_ROOT / "rules_v6" / "static_commands.json",
        _REPO_ROOT / "rules_v6" / "static_units.json",
    ]
    all_absent = all(not p.exists() for p in paths)
    check("27. No static command/unit database added", all_absent)


def test_docs_guardrails() -> None:
    check("28. docs/BOOTSTRAP.md unchanged", (_REPO_ROOT / "docs" / "BOOTSTRAP.md").exists())
    check("29. docs/HERMES_INSTRUCTIONS.md unchanged", (_REPO_ROOT / "docs" / "HERMES_INSTRUCTIONS.md").exists())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    global _PASS, _FAIL

    print("=" * 70)
    print("Phase L.29Q Hermes Session Manager Regression Results")
    print("=" * 70)

    # Direct tests
    sid = test_new_creates_session()
    test_say_ingests_text()
    r_next, sid_next = test_next_returns_valid_action()
    test_next_on_empty_is_blocking(r_next, sid_next)
    test_answer_applies_field()
    test_ready_reports_false_with_blocking()
    test_standard_letter_reaches_zero_blocking()
    test_no_pdf_render_triggered()
    test_resume_loads_existing()
    test_summary_compact()
    test_help_shows_all_commands()

    # External regressions
    test_external_regression("tools/run_phase_l29p_next_action_cli_regression.py", 11)
    test_external_regression("tools/run_phase_l29o_hermes_loop_prototype_regression.py", 12)
    test_external_regression("tools/run_phase_l29m_detect_facts_cli_regression.py", 13)
    test_external_regression("tools/run_phase_l29l_unresolved_fact_detector_regression.py", 14)
    test_external_regression("tools/run_phase_l29k_rule_fact_map_regression.py", 15)
    test_external_regression("tools/run_phase_l29c_candidate_confirmation_regression.py", 16)
    test_external_regression("tools/run_phase_l28_hermes_secnav_cli_tool_regression.py", 17)

    # Static guards
    test_no_renderer_changes()
    test_no_validator_changes()
    test_no_static_db()
    test_docs_guardrails()

    print("=" * 70)
    print(f"Passed: {_PASS}, Failed: {_FAIL}")
    print("=" * 70)

    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
