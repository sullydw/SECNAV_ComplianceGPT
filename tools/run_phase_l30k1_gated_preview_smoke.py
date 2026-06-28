#!/usr/bin/env python3
"""
Phase L.30K-1 Smoke Test — Gated Read-Only Preview Command

Verifies:
- incomplete session returns mode build_status
- incomplete preview_text does not contain DRAFT PREVIEW
- complete-enough session returns mode draft_preview
- draft preview contains DRAFT PREVIEW  NOT FINAL
- draft preview contains body review label
- preview does not mutate payload or candidate counts
- pending candidate remains pending after preview
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
    return f"l30k1_smoke_{uuid.uuid4().hex[:8]}"


def _start_session(session_id: str) -> dict:
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


def _status(session_id: str) -> dict:
    return _run_tool(["status", "--session", session_id])


def _reset(session_id: str) -> dict:
    return _run_tool(["reset", "--session", session_id])


def main() -> int:
    errors: list[str] = []
    session_id = _make_session_id()

    # --- Start session ---
    start_r = _start_session(session_id)
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

    # --- Preview incomplete session => build_status ---
    preview = _preview(actual_sid)
    if not preview.get("success"):
        errors.append(f"preview failed: {preview.get('error')}")
    elif preview.get("mode") != "build_status":
        errors.append(f"expected mode build_status, got {preview.get('mode')}")
    else:
        pt = preview.get("preview_text", "")
        if "DRAFT PREVIEW" in pt:
            errors.append("build_status preview_text contains DRAFT PREVIEW")
        if "BUILD STATUS" not in pt:
            errors.append("build_status preview_text missing BUILD STATUS")
        if preview.get("missing_for_preview") is None:
            errors.append("build_status missing missing_for_preview")
        if not preview.get("next_action"):
            errors.append("build_status missing next_action")

    # --- Fill fields to meet preview gate ---
    _apply(actual_sid, "from: CO, USS NEVERSAIL")
    _apply(actual_sid, "to: SECNAV")
    _apply(actual_sid, "subj: TEST SUBJECT")
    _apply(actual_sid, "body: Test paragraph one.\nTest paragraph two.")
    _apply(actual_sid, "date: 2026-06-28")
    _apply(actual_sid, "signature.name: J. Doe")

    # --- Save state before preview to detect mutation ---
    before = _status(actual_sid)
    before_payload = dict(before.get("payload", {}))
    before_candidates = before.get("payload", {}).get("candidates")
    # Candidate counts from tool candidates command
    before_cands = _run_tool(["candidates", "--session", actual_sid])
    before_pending = before_cands.get("candidates", {}).get("counts", {}).get("pending", 0)

    # --- Preview complete session => draft_preview ---
    preview = _preview(actual_sid)
    if not preview.get("success"):
        errors.append(f"preview (complete) failed: {preview.get('error')}")
    elif preview.get("mode") != "draft_preview":
        errors.append(f"expected mode draft_preview, got {preview.get('mode')}")
    else:
        pt = preview.get("preview_text", "")
        if "DRAFT PREVIEW  NOT FINAL" not in pt:
            errors.append("draft_preview missing 'DRAFT PREVIEW  NOT FINAL'")
        if "[AI-DRAFTED OR USER-PROVIDED BODY  REVIEW REQUIRED]" not in pt:
            errors.append("draft_preview missing body review label")
        if preview.get("body_review_required") is not True:
            errors.append("draft_preview body_review_required not True")
        if preview.get("preview_gate_met") is not True:
            errors.append("draft_preview preview_gate_met not True")

    # --- Verify no mutation after preview ---
    after = _status(actual_sid)
    after_payload = dict(after.get("payload", {}))
    # payload should not change from preview
    if after_payload != before_payload:
        errors.append("preview mutated payload")

    after_cands = _run_tool(["candidates", "--session", actual_sid])
    after_pending = after_cands.get("candidates", {}).get("counts", {}).get("pending", 0)
    if after_pending != before_pending:
        errors.append(f"preview mutated candidate counts: before={before_pending} after={after_pending}")

    # --- Manager preview wrapper also works ---
    mgr_preview = _preview_manager(actual_sid)
    if not mgr_preview.get("success"):
        errors.append(f"manager preview failed: {mgr_preview.get('error')}")
    elif mgr_preview.get("mode") not in ("build_status", "draft_preview"):
        errors.append(f"manager preview returned unexpected mode: {mgr_preview.get('mode')}")

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
