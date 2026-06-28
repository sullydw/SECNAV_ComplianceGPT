#!/usr/bin/env python3
"""
Phase L.30K-2 Smoke Test — Preview Approval State

Verifies:
- complete-enough session preview starts with approval_current false
- approve command records approval
- approval survives reload
- preview after approve returns approval_current true
- preview_text indicates APPROVED FOR FINALIZE
- approve does not finalize or render
- approve does not mutate payload except approval metadata
- candidate counts unchanged
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
    return f"l30k2_smoke_{uuid.uuid4().hex[:8]}"


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


def _preview_manager(session_id: str) -> dict:
    return _run_manager(["preview", "--session", session_id])


def _approve(session_id: str) -> dict:
    return _run_tool(["approve", "--session", session_id])


def _approve_manager(session_id: str) -> dict:
    return _run_manager(["approve", "--session", session_id])


def _status(session_id: str) -> dict:
    return _run_tool(["status", "--session", session_id])


def _candidates(session_id: str) -> dict:
    return _run_tool(["candidates", "--session", session_id])


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

    # Add a candidate so we can verify it stays pending
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

    # --- Capture state before approve ---
    before_status = _status(actual_sid)
    before_payload = dict(before_status.get("payload", {}))
    before_cands = _candidates(actual_sid)
    before_pending = before_cands.get("candidates", {}).get("counts", {}).get("pending", 0)

    # --- Preview before approve => approval_current false ---
    prev = _preview(actual_sid)
    if not prev.get("success"):
        errors.append(f"preview failed: {prev.get('error')}")
    elif prev.get("mode") != "draft_preview":
        errors.append(f"expected mode draft_preview, got {prev.get('mode')}")
    else:
        approval = prev.get("approval") or {}
        if approval.get("approval_current") is not False:
            errors.append(f"expected approval_current False before approve, got {approval.get('approval_current')}")
        if "DRAFT PREVIEW  NOT FINAL" not in prev.get("preview_text", ""):
            errors.append("draft_preview before approve missing 'DRAFT PREVIEW  NOT FINAL'")

    # --- Approve command ---
    apr = _approve(actual_sid)
    if not apr.get("success"):
        errors.append(f"approve failed: {apr.get('error')}")
    else:
        if apr.get("approved_for_finalize") is not True:
            errors.append(f"approve approved_for_finalize not True: {apr.get('approved_for_finalize')}")
        if not apr.get("approved_at"):
            errors.append("approve missing approved_at")
        if not apr.get("approved_preview_hash"):
            errors.append("approve missing approved_preview_hash")
        if apr.get("approval_current") is not True:
            errors.append(f"approve approval_current not True: {apr.get('approval_current')}")
        if apr.get("current_preview_hash") != apr.get("approved_preview_hash"):
            errors.append("approve current_preview_hash mismatch with approved_preview_hash")

    # --- Approval survives reload: preview after approve ---
    prev2 = _preview(actual_sid)
    if not prev2.get("success"):
        errors.append(f"preview after approve failed: {prev2.get('error')}")
    else:
        approval2 = prev2.get("approval") or {}
        if approval2.get("approval_current") is not True:
            errors.append(f"approval did not survive reload: approval_current={approval2.get('approval_current')}")
        if prev2.get("mode") != "draft_preview":
            errors.append(f"preview after approve mode not draft_preview: {prev2.get('mode')}")
        pt = prev2.get("preview_text", "")
        if "APPROVED FOR FINALIZE" not in pt:
            errors.append("preview_text after approve missing 'APPROVED FOR FINALIZE'")
        if "NOT FINAL" in pt:
            errors.append("preview_text after approve still contains 'NOT FINAL'")

    # --- Approve does not finalize or render ---
    after_status = _status(actual_sid)
    if after_status.get("payload", {}).get("finalized") is True:
        errors.append("approve unexpectedly finalized the session")
    pdf_path = after_status.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        errors.append("approve unexpectedly rendered a PDF")

    # --- Approve does not mutate payload except approval metadata ---
    after_payload = dict(after_status.get("payload", {}))
    if after_payload != before_payload:
        errors.append("approve mutated payload")

    # --- Candidate counts unchanged ---
    after_cands = _candidates(actual_sid)
    after_pending = after_cands.get("candidates", {}).get("counts", {}).get("pending", 0)
    if after_pending != before_pending:
        errors.append(f"approve mutated candidate counts: before={before_pending} after={after_pending}")

    # --- Manager approve wrapper works ---
    mgr_apr = _approve_manager(actual_sid)
    if not mgr_apr.get("success"):
        errors.append(f"manager approve failed: {mgr_apr.get('error')}")
    elif mgr_apr.get("approval_current") is not True:
        errors.append(f"manager approve approval_current not True: {mgr_apr.get('approval_current')}")

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
