#!/usr/bin/env python3
"""
Phase L.30K-4 Smoke Test — Enforce Preview Approval Gate

Verifies:
- finalize blocked before approval
- render blocked before approval (no PDF created)
- approve then finalize succeeds
- approve then revise clears approval and finalize blocks again
- re-approve then render succeeds
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"
_SESSION_DIR = Path.home() / ".hermes" / "secnav_sessions"

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"


def _run_tool(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_TOOL)] + args,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(_REPO_ROOT),
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return {"success": False, "error": proc.stderr or f"exit code {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON: {proc.stdout[:200]}"}


def _run_manager(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_MANAGER)] + args,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(_REPO_ROOT),
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return {"success": False, "error": proc.stderr or f"exit code {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON: {proc.stdout[:200]}"}


def _make_session_id() -> str:
    return f"l30k4_smoke_{uuid.uuid4().hex[:8]}"


def _start_session() -> dict:
    return _run_tool(["start"])


def _apply(session_id: str, kv: str) -> dict:
    return _run_tool(["apply", "--session", session_id, "--kv", kv])


def _add_candidate(session_id: str, candidate: dict) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(candidate, f)
        path = f.name
    try:
        return _run_tool(["candidate-add", "--session", session_id, "--json", path])
    finally:
        Path(path).unlink(missing_ok=True)


def _preview(session_id: str) -> dict:
    return _run_tool(["preview", "--session", session_id])


def _approve(session_id: str) -> dict:
    return _run_tool(["approve", "--session", session_id])


def _revise(session_id: str, text: str) -> dict:
    return _run_tool(["revise", "--session", session_id, "--text", text])


def _finalize(session_id: str) -> dict:
    return _run_tool(["finalize", "--session", session_id])


def _finalize_manager(session_id: str) -> dict:
    return _run_manager(["finalize", "--session", session_id])


def _render(session_id: str, out: str) -> dict:
    return _run_tool(["render", "--session", session_id, "--out", out])


def _render_manager(session_id: str, out: str) -> dict:
    return _run_manager(["render", "--session", session_id, "--out", out])


def _status(session_id: str) -> dict:
    return _run_tool(["status", "--session", session_id])


def _reset(session_id: str) -> dict:
    return _run_tool(["reset", "--session", session_id])


def main() -> int:
    errors: list[str] = []
    session_id = _make_session_id()

    # --- Start session ---
    start_r = _start_session()
    if not start_r.get("success"):
        print(f"FAIL: start failed: {start_r.get('error')}")
        return 1
    actual_sid = start_r["session_id"]

    # Add a candidate
    _add_candidate(actual_sid, {
        "candidate_type": "ssic_candidate",
        "input_text": "5510",
        "resolved_value": {"ssic": "5510"},
        "confidence": 0.95,
        "requires_user_confirmation": True,
    })

    # --- Fill fields cleanly so validation passes ---
    _apply(actual_sid, "from: CO, USS NEVERSAIL")
    _apply(actual_sid, "to: SECNAV")
    _apply(actual_sid, "subj: REQUEST FOR TEST SUBJECT LINE VERIFICATION")
    _apply(actual_sid, "body: Test paragraph one.\nTest paragraph two.")
    _apply(actual_sid, "date: 28 June 2026")
    _apply(actual_sid, "signature.name: J. Doe")

    # Verify validation is clean before gating on approval
    st = _status(actual_sid)
    v_sum = st.get("validation_summary", {}) or {}
    if not v_sum.get("finalize_allowed"):
        # If validation still blocks, accept-warnings to isolate approval gate
        pass  # We will use finalize without accept-warnings; if validation blocks, that's fine

    # --- finalize blocked before approval ---
    fin1 = _finalize(actual_sid)
    if fin1.get("success"):
        errors.append("finalize before approval succeeded unexpectedly")
    else:
        gate1 = fin1.get("approval_gate") or {}
        if gate1.get("passed") is not False:
            errors.append(f"finalize before approval gate.passed not False: {gate1}")
        err1 = fin1.get("error", "")
        if "not approved" not in err1.lower():
            errors.append(f"finalize before approval error missing 'not approved': {err1}")

    # --- render blocked before approval ---
    out_path = str(_SESSION_DIR / f"{actual_sid}_test.pdf")
    ren1 = _render(actual_sid, out_path)
    if ren1.get("success"):
        errors.append("render before approval succeeded unexpectedly")
        Path(out_path).unlink(missing_ok=True)
    else:
        # Render checks validation first, then approval; either block is acceptable.
        err2 = ren1.get("error", "")
        gate2 = ren1.get("approval_gate") or {}
        blocked = (gate2.get("passed") is False) or ("not approved" in err2.lower())
        if not blocked:
            errors.append(f"render before approval not blocked: error={err2} gate={gate2}")
    if Path(out_path).exists():
        errors.append("PDF created despite render being blocked before approval")
        Path(out_path).unlink(missing_ok=True)

    # --- Approve ---
    apr = _approve(actual_sid)
    if not apr.get("success"):
        errors.append(f"approve failed: {apr.get('error')}")
    elif apr.get("approval_current") is not True:
        errors.append(f"approve approval_current not True: {apr.get('approval_current')}")

    # --- finalize after approve should succeed ---
    fin2 = _finalize(actual_sid)
    if not fin2.get("success"):
        errors.append(f"finalize after approve failed: {fin2.get('error')}")
    else:
        gate3 = fin2.get("approval_gate") or {}
        if gate3.get("passed") is not True:
            errors.append(f"finalize after approve gate.passed not True: {gate3}")

    # --- Start second session for render path (finalize already happened above) ---
    session_id2 = _make_session_id()
    start_r2 = _start_session()
    if not start_r2.get("success"):
        errors.append(f"second start failed: {start_r2.get('error')}")
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    sid2 = start_r2["session_id"]

    _apply(sid2, "from: CO, USS NEVERSAIL")
    _apply(sid2, "to: SECNAV")
    _apply(sid2, "subj: REQUEST FOR TEST SUBJECT LINE VERIFICATION")
    _apply(sid2, "body: Test paragraph one.\nTest paragraph two.")
    _apply(sid2, "date: 28 June 2026")
    _apply(sid2, "signature.name: J. Doe")

    _approve(sid2)

    # --- render after approve should succeed (manager wrapper) ---
    out_path2 = str(_SESSION_DIR / f"{sid2}_test.pdf")
    ren2 = _render_manager(sid2, out_path2)
    if not ren2.get("success"):
        errors.append(f"render after approve failed: {ren2.get('error')}")
    else:
        gate4 = ren2.get("approval_gate") or {}
        if gate4.get("passed") is not True:
            errors.append(f"render after approve gate.passed not True: {gate4}")
        pdf = ren2.get("pdf_path")
        if not pdf or not Path(pdf).exists():
            errors.append("render after approve did not produce a PDF file")
    # cleanup pdf if created
    if Path(out_path2).exists():
        Path(out_path2).unlink(missing_ok=True)

    # --- revise clears approval and finalize blocks again ---
    rev = _revise(sid2, "body: Changed body text.")
    if not rev.get("success"):
        errors.append(f"revise failed: {rev.get('error')}")
    else:
        if rev.get("approval_cleared") is not True:
            errors.append(f"revise approval_cleared not True: {rev.get('approval_cleared')}")

    fin3 = _finalize(sid2)
    if fin3.get("success"):
        errors.append("finalize after revise succeeded unexpectedly")
    else:
        gate5 = fin3.get("approval_gate") or {}
        if gate5.get("passed") is not False:
            errors.append(f"finalize after revise gate.passed not False: {gate5}")
        err3 = fin3.get("error", "")
        if "not approved" not in err3.lower():
            errors.append(f"finalize after revise error missing 'not approved': {err3}")

    # --- re-approve then finalize succeeds again ---
    apr2 = _approve(sid2)
    if not apr2.get("success"):
        errors.append(f"re-approve after revise failed: {apr2.get('error')}")
    elif apr2.get("approval_current") is not True:
        errors.append(f"re-approve after revise approval_current not True: {apr2.get('approval_current')}")

    fin4 = _finalize(sid2)
    if not fin4.get("success"):
        errors.append(f"finalize after re-approve failed: {fin4.get('error')}")
    else:
        gate6 = fin4.get("approval_gate") or {}
        if gate6.get("passed") is not True:
            errors.append(f"finalize after re-approve gate.passed not True: {gate6}")

    # --- Cleanup ---
    _reset(actual_sid)
    _reset(sid2)

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
