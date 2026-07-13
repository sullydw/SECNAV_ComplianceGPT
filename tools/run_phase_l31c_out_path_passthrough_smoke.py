#!/usr/bin/env python3
"""
Phase L.31C — Out-Path Pass-Through Smoke Test

Proves send_secnav_chat_turn(..., out=...) stores the path
and later render uses it, while turns without out leave the
existing path unchanged.
"""

import json
import subprocess
import sys
import io
import tempfile
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"

sys.path.insert(0, str(_TOOL_ROOT))
from hermes_chat_builder import (
    start_secnav_chat,
    send_secnav_chat_turn,
    get_secnav_chat_status,
    reset_secnav_chat,
)


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


def _capture_stdout(fn, *args, **kwargs):
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = fn(*args, **kwargs)
    finally:
        captured = sys.stdout.getvalue()
        sys.stdout = old
    return result, captured


def main() -> int:
    failures = []

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "phase_l31c_letter.pdf"
        alt_path = Path(tmpdir) / "alt_letter.pdf"

        # 1) start without out
        r1, cap1 = _capture_stdout(start_secnav_chat)
        if cap1:
            failures.append("start_secnav_chat printed stdout")
        if not r1.get("success"):
            failures.append(f"start failed: {r1}")
        chat_id = r1["chat_id"]
        session_id = r1["session_id"]
        print("[PASS] start_secnav_chat without out works and is silent")

        # 2) send turn WITH out updates state
        r2, cap2 = _capture_stdout(send_secnav_chat_turn, chat_id, "I need a letter", out=str(out_path))
        if cap2:
            failures.append("send_secnav_chat_turn(out=...) printed stdout")
        if not r2.get("success"):
            failures.append(f"send_turn failed: {r2}")
        print("[PASS] send_secnav_chat_turn with out is silent")

        # 3) fill fields, approve, render — should use out_path
        _fill_session(session_id)
        _run_manager(["approve", "--session", session_id])

        rr, capr = _capture_stdout(send_secnav_chat_turn, chat_id, "make the pdf")
        if capr:
            failures.append("render turn printed stdout")
        if not rr.get("success"):
            failures.append(f"render failed: {rr}")
        if rr.get("pdf_path") != str(out_path):
            failures.append(f"render used wrong path: {rr.get('pdf_path')} != {out_path}")
        if not out_path.exists():
            failures.append(f"PDF not created at expected path: {out_path}")
        print(f"[PASS] render used passed-through out path: {out_path}")

        # 4) start new chat, set out via turn 1, send turn 2 without out,
        #    fill, approve, render — should still use first out path
        r3, _ = _capture_stdout(start_secnav_chat)
        chat_id2 = r3["chat_id"]
        session_id2 = r3["session_id"]

        r4, _ = _capture_stdout(send_secnav_chat_turn, chat_id2, "I need a letter", out=str(alt_path))
        if not r4.get("success"):
            failures.append(f"second chat first turn failed: {r4}")

        # send turn without out
        r5, _ = _capture_stdout(send_secnav_chat_turn, chat_id2, "to Commanding General")
        if not r5.get("success"):
            failures.append(f"second chat no-out turn failed: {r5}")

        _fill_session(session_id2)
        _run_manager(["approve", "--session", session_id2])

        rr2, _ = _capture_stdout(send_secnav_chat_turn, chat_id2, "make the pdf")
        if not rr2.get("success"):
            failures.append(f"second chat render failed: {rr2}")
        if rr2.get("pdf_path") != str(alt_path):
            failures.append(f"second chat render used wrong path: {rr2.get('pdf_path')} != {alt_path}")
        print(f"[PASS] out path persists when later turn omits out: {alt_path}")

        # 5) all callable functions remain silent
        for fn, args in [
            (start_secnav_chat, ()),
            (send_secnav_chat_turn, (chat_id2, "test")),
            (get_secnav_chat_status, (chat_id2,)),
            (reset_secnav_chat, (chat_id2,)),
        ]:
            _, cap = _capture_stdout(fn, *args)
            if cap:
                failures.append(f"{fn.__name__} printed stdout: {cap!r}")
        print("[PASS] all callable functions remain silent")

    # 6) existing L.31A smoke still passes
    p = subprocess.run(
        [str(_PYTHON), str(_TOOL_ROOT / "run_phase_l31a_tool_interface_smoke.py")],
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=300,
    )
    if p.returncode != 0:
        failures.append(f"L.31A smoke failed (rc={p.returncode})\nstdout: {p.stdout[:500]}\nstderr: {p.stderr[:500]}")
    else:
        print("[PASS] L.31A smoke still passes")

    if failures:
        print("\n=== L.31C Smoke FAILURES ===")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\n=== L.31C Smoke Results ===")
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
