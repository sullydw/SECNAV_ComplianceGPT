#!/usr/bin/env python3
"""
Phase L.31A — Tool Interface Smoke Test

Proves the callable backend functions in hermes_chat_builder.py work
end-to-end without requiring stdin or printing to stdout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import io
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"

# Make sure imports work
sys.path.insert(0, str(_TOOL_ROOT))

from hermes_chat_builder import (
    start_secnav_chat,
    send_secnav_chat_turn,
    get_secnav_chat_status,
    reset_secnav_chat,
    format_tool_response_for_hermes,
)


fails: list[str] = []


def _assert(desc: str, cond: bool) -> None:
    if not cond:
        fails.append(desc)
        print(f"FAIL: {desc}")
    else:
        print(f"OK: {desc}")


def _assert_key(desc: str, obj: dict, key: str, expected=None) -> None:
    if key not in obj:
        fails.append(f"{desc} missing key {key}")
        print(f"FAIL: {desc} missing key {key}")
        return
    val = obj[key]
    if expected is not None and val != expected:
        fails.append(f"{desc} {key}={val} expected {expected}")
        print(f"FAIL: {desc} {key}={val} expected {expected}")
        return
    print(f"OK: {desc} has {key}")


def _run_manager(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_MANAGER)] + args,
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=120,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": proc.stdout[:200]}


def _fill_session(session_id: str) -> None:
    for field, value in [
        ("ssic", "5216"),
        ("originator_code", "CG"),
        ("from", "Commanding Officer, Marine Corps Air Station New River"),
        ("to", "Commanding General, II Marine Expeditionary Force"),
        ("subj", "ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW"),
        ("date", "1 July 2026"),
        ("body", "1. Review procedures. 2. Coordinate updates."),
        ("signature.name", "A. B. SAMPLE"),
        ("signature.title", "Commanding Officer"),
        # L.31I: letterhead required for standard letters
        ("letterhead_top_line", "UNITED STATES MARINE CORPS"),
        ("letterhead_activity", "MARINE CORPS AIR STATION NEW RIVER"),
        ("letterhead_address", "JACKSONVILLE NC 28545-0000"),
    ]:
        _run_manager(["answer", "--session", session_id, "--field", field, "--value", value])


def main() -> int:
    print("Phase L.31A smoke test starting...")

    # -----------------------------------------------------------------------
    # 1. start_secnav_chat returns dict, no print
    # -----------------------------------------------------------------------
    print("[1] start_secnav_chat returns dict, does not print ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    start_result = start_secnav_chat()
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("start returns dict", isinstance(start_result, dict))
    _assert("start success", start_result.get("success") is True)
    _assert("start has chat_id", bool(start_result.get("chat_id")))
    _assert("start chat_id starts with chat-", str(start_result.get("chat_id", "")).startswith("chat-"))
    _assert("start has session_id", bool(start_result.get("session_id")))
    _assert("start does not print", captured == "")
    chat_id = start_result["chat_id"]
    session_id = start_result["session_id"]
    print(f"  chat_id={chat_id}")

    # -----------------------------------------------------------------------
    # 2. send_secnav_chat_turn (say)
    # -----------------------------------------------------------------------
    print("[2] send_secnav_chat_turn (say) ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r = send_secnav_chat_turn(chat_id, "I need a standard letter to II MEF about correspondence procedures")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("say returns dict", isinstance(r, dict))
    _assert("say success", r.get("success") is True)
    _assert("say has assistant_response", bool(r.get("assistant_response")))
    _assert("say does not print", captured == "")

    # -----------------------------------------------------------------------
    # 3. get_secnav_chat_status
    # -----------------------------------------------------------------------
    print("[3] get_secnav_chat_status ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    s = get_secnav_chat_status(chat_id)
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("status returns dict", isinstance(s, dict))
    _assert("status success", s.get("success") is True)
    _assert("status has phase", bool(s.get("phase")))
    _assert("status has assistant_response", bool(s.get("assistant_response")))
    _assert("status does not print", captured == "")

    # -----------------------------------------------------------------------
    # 4. send_secnav_chat_turn (supported revise)
    # -----------------------------------------------------------------------
    print("[4] supported revise ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r = send_secnav_chat_turn(chat_id, "Change the subject to REVISED ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("revise returns dict", isinstance(r, dict))
    _assert("revise does not print", captured == "")
    _assert_key("revise supported", r, "intent", "revise")
    _assert_key("revise supported", r, "payload_changed", True)
    _assert_key("revise supported", r, "approval_cleared", True)

    # -----------------------------------------------------------------------
    # 5. send_secnav_chat_turn (unsupported revise does not falsely claim changes)
    # -----------------------------------------------------------------------
    print("[5] unsupported revise does not falsely claim changes ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r = send_secnav_chat_turn(chat_id, "Make the body more formal using iambic pentameter")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("unsupported revise returns dict", isinstance(r, dict))
    _assert("unsupported revise does not print", captured == "")
    # Either payload_changed is False/None, or assistant_response mentions nothing changed
    if r.get("payload_changed"):
        _assert("unsupported revise payload_changed false", False)
    else:
        _assert("unsupported revise payload_changed false", True)

    # -----------------------------------------------------------------------
    # 6. Fill session fields so we can test approval/render
    # -----------------------------------------------------------------------
    print("[6] fill session fields via manager ...")
    _fill_session(session_id)
    print("  filled")

    # -----------------------------------------------------------------------
    # 7. Approve
    # -----------------------------------------------------------------------
    print("[7] approve ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r = send_secnav_chat_turn(chat_id, "looks good")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("approve returns dict", isinstance(r, dict))
    _assert("approve does not print", captured == "")

    # -----------------------------------------------------------------------
    # 8. Render blocked before approval (simulate by resetting and trying early)
    # -----------------------------------------------------------------------
    print("[8] render blocked before approval ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r2 = start_secnav_chat()
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("start2 does not print", captured == "")
    chat_id2 = r2["chat_id"]

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    r = send_secnav_chat_turn(chat_id2, "make the pdf")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("early render does not print", captured == "")
    # Either success=False, or intent!=render, or no pdf_path
    if r.get("success") and r.get("intent") == "render" and r.get("pdf_path"):
        _assert("early render blocked", False)
    else:
        _assert("early render blocked", True)

    # -----------------------------------------------------------------------
    # 9. reset_secnav_chat
    # -----------------------------------------------------------------------
    print("[9] reset_secnav_chat ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    rs = reset_secnav_chat(chat_id)
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("reset returns dict", isinstance(rs, dict))
    _assert("reset success", rs.get("success") is True)
    _assert("reset has assistant_response", bool(rs.get("assistant_response")))
    _assert("reset does not print", captured == "")

    # -----------------------------------------------------------------------
    # 10. Render succeeds after approval/ready (reuse chat_id, fill, approve, render)
    # -----------------------------------------------------------------------
    print("[10] render succeeds after approval/ready ...")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    start_r = start_secnav_chat()
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("start3 does not print", captured == "")
    chat_id3 = start_r["chat_id"]
    session_id3 = start_r["session_id"]
    _fill_session(session_id3)

    # Approve via manager directly to keep it simple
    _run_manager(["approve", "--session", session_id3])

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    render_r = send_secnav_chat_turn(chat_id3, "make the pdf")
    captured = sys.stdout.getvalue()
    sys.stdout = old_stdout

    _assert("render does not print", captured == "")
    _assert("render success", render_r.get("success") is True)
    _assert("render intent", render_r.get("intent") == "render")
    _assert("render pdf_path", bool(render_r.get("pdf_path")))
    pdf_path = Path(render_r["pdf_path"])
    _assert("render pdf exists", pdf_path.exists() and pdf_path.stat().st_size > 0)
    print(f"  PDF={pdf_path} ({pdf_path.stat().st_size} bytes)")

    # -----------------------------------------------------------------------
    # 11. format_tool_response_for_hermes
    # -----------------------------------------------------------------------
    print("[11] format_tool_response_for_hermes ...")
    formatted = format_tool_response_for_hermes(render_r)
    _assert("format returns str", isinstance(formatted, str))
    _assert("format mentions PDF", "PDF" in formatted)
    _assert("format mentions path", str(pdf_path) in formatted)

    # Error case formatting
    err_formatted = format_tool_response_for_hermes({"success": False, "error": "test error"})
    _assert("format error mentions test error", "test error" in err_formatted)

    # -----------------------------------------------------------------------
    # 12. Old CLI smoke tests still pass
    # -----------------------------------------------------------------------
    print("[12] old L.30X smoke test still passes ...")
    p = subprocess.run(
        [str(_PYTHON), str(_TOOL_ROOT / "run_phase_l30x_chat_response_consistency_smoke.py")],
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=300,
    )
    _assert("L.30X smoke exit 0", p.returncode == 0)
    if p.returncode != 0:
        print(f"    stdout: {p.stdout[:500]}")
        print(f"    stderr: {p.stderr[:500]}")

    print("[13] old L.30U smoke test still passes ...")
    p = subprocess.run(
        [str(_PYTHON), str(_TOOL_ROOT / "run_phase_l30u_interactive_chat_loop_smoke.py")],
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=300,
    )
    _assert("L.30U smoke exit 0", p.returncode == 0)
    if p.returncode != 0:
        print(f"    stdout: {p.stdout[:500]}")
        print(f"    stderr: {p.stderr[:500]}")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    if fails:
        print(f"\nFAIL — {len(fails)} issue(s)")
        for f in fails:
            print(f"  - {f}")
        return 1
    else:
        print("\nPASS — all checks passed")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
