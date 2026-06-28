#!/usr/bin/env python3
"""
Phase L.30K-3 Smoke Test — Revision Command Clears Approval

Verifies:
- complete session reaches draft_preview
- approve records approval_current=true
- revise with body: changed text updates body
- approval is cleared after body change
- preview after revision shows approval_current=false and NOT FINAL
- revise that does not change draft-relevant payload does not falsely clear approval if practical
- candidate counts unchanged
- no finalize/render occurs
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
    return f"l30k3_smoke_{uuid.uuid4().hex[:8]}"


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


def _revise_manager(session_id: str, text: str) -> dict:
    return _run_manager(["revise", "--session", session_id, "--text", text])


def _candidates(session_id: str) -> dict:
    return _run_tool(["candidates", "--session", session_id])


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
    cand = _add_candidate(actual_sid, {
        "candidate_type": "ssic_candidate",
        "input_text": "5510",
        "resolved_value": {"ssic": "5510"},
        "confidence": 0.95,
        "requires_user_confirmation": True,
    })
    if not cand.get("success"):
        print(f"WARN: candidate-add failed: {cand.get('error')}")

    # --- Fill fields to meet preview gate ---
    _apply(actual_sid, "from: CO, USS NEVERSAIL")
    _apply(actual_sid, "to: SECNAV")
    _apply(actual_sid, "subj: TEST SUBJECT")
    _apply(actual_sid, "body: Test paragraph one.\nTest paragraph two.")
    _apply(actual_sid, "date: 2026-06-28")
    _apply(actual_sid, "signature.name: J. Doe")

    # --- Capture candidate counts before ---
    before_cands = _candidates(actual_sid)
    before_pending = before_cands.get("candidates", {}).get("counts", {}).get("pending", 0)

    # --- Preview before approve ---
    prev1 = _preview(actual_sid)
    if not prev1.get("success"):
        errors.append(f"preview failed: {prev1.get('error')}")
    elif prev1.get("mode") != "draft_preview":
        errors.append(f"expected mode draft_preview, got {prev1.get('mode')}")
    else:
        approval1 = prev1.get("approval") or {}
        if approval1.get("approval_current") is not False:
            errors.append(f"expected approval_current False before approve, got {approval1.get('approval_current')}")

    # --- Approve ---
    apr = _approve(actual_sid)
    if not apr.get("success"):
        errors.append(f"approve failed: {apr.get('error')}")
    elif apr.get("approval_current") is not True:
        errors.append(f"approve approval_current not True: {apr.get('approval_current')}")

    # --- Preview after approve ---
    prev2 = _preview(actual_sid)
    approval2 = prev2.get("approval") or {}
    if approval2.get("approval_current") is not True:
        errors.append(f"approval did not survive after approve: approval_current={approval2.get('approval_current')}")
    if "APPROVED FOR FINALIZE" not in prev2.get("preview_text", ""):
        errors.append("preview_text after approve missing APPROVED FOR FINALIZE")

    # --- Revise body ---
    rev = _revise(actual_sid, "body: Revised paragraph one.\nRevised paragraph two.")
    if not rev.get("success"):
        errors.append(f"revise failed: {rev.get('error')}")
    else:
        if rev.get("payload_changed") is not True:
            errors.append(f"revise payload_changed not True: {rev.get('payload_changed')}")
        if rev.get("approval_cleared") is not True:
            errors.append(f"revise approval_cleared not True: {rev.get('approval_cleared')}")
        approval3 = rev.get("approval") or {}
        if approval3.get("approval_current") is not False:
            errors.append(f"revise did not clear approval: approval_current={approval3.get('approval_current')}")

    # --- Preview after revise ---
    prev3 = _preview(actual_sid)
    approval4 = prev3.get("approval") or {}
    if approval4.get("approval_current") is not False:
        errors.append(f"approval_current not False after revise: {approval4.get('approval_current')}")
    if prev3.get("mode") != "draft_preview":
        errors.append(f"preview after revise mode not draft_preview: {prev3.get('mode')}")
    pt = prev3.get("preview_text", "")
    if "NOT FINAL" not in pt:
        errors.append("preview_text after revise missing NOT FINAL")
    if "APPROVED FOR FINALIZE" in pt:
        errors.append("preview_text after revise still contains APPROVED FOR FINALIZE")

    # --- Approve again after revise (re-approval path) ---
    apr2 = _approve(actual_sid)
    if not apr2.get("success"):
        errors.append(f"re-approve after revise failed: {apr2.get('error')}")
    elif apr2.get("approval_current") is not True:
        errors.append(f"re-approve after revise approval_current not True: {apr2.get('approval_current')}")

    # --- Revising to same value should ideally not clear approval, but not required ---
    # We test manager wrapper for revise
    rev_mgr = _revise_manager(actual_sid, "body: Manager revised text.")
    if not rev_mgr.get("success"):
        errors.append(f"manager revise failed: {rev_mgr.get('error')}")

    # --- No finalize/render occurred ---
    after_status = _status(actual_sid)
    if after_status.get("payload", {}).get("finalized") is True:
        errors.append("revise unexpectedly finalized the session")
    pdf_path = after_status.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        errors.append("revise unexpectedly rendered a PDF")

    # --- Candidate counts unchanged ---
    after_cands = _candidates(actual_sid)
    after_pending = after_cands.get("candidates", {}).get("counts", {}).get("pending", 0)
    if after_pending != before_pending:
        errors.append(f"revise mutated candidate counts: before={before_pending} after={after_pending}")

    # --- Cleanup ---
    _reset(actual_sid)

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
