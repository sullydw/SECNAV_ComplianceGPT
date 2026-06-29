#!/usr/bin/env python3
"""
Phase L.30L Smoke Test — Preview Readability Improvements

Verifies:
- build_status still works
- draft_preview still works
- approval banner still works (approved vs not approved)
- approval gate still unaffected
- preview remains read-only
- expected new section headers appear
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"


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


def _apply(session_id: str, kv: str) -> dict:
    return _run_tool(["apply", "--session", session_id, "--kv", kv])


def _preview(session_id: str) -> dict:
    return _run_tool(["preview", "--session", session_id])


def _approve(session_id: str) -> dict:
    return _run_tool(["approve", "--session", session_id])


def _finalize(session_id: str) -> dict:
    return _run_tool(["finalize", "--session", session_id])


def _status(session_id: str) -> dict:
    return _run_tool(["status", "--session", session_id])


def main() -> int:
    errors: list[str] = []
    session_id = f"l30l_smoke_{uuid.uuid4().hex[:8]}"

    # --- Start session ---
    start_r = _run_tool(["start"])
    if not start_r.get("success"):
        print(f"FAIL: start failed: {start_r.get('error')}")
        return 1
    sid = start_r["session_id"]

    # --- Incomplete preview => build_status ---
    preview = _preview(sid)
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
        # New section headers
        if "KNOWN FIELDS" not in pt:
            errors.append("build_status missing KNOWN FIELDS header")
        if "MISSING / BLOCKING ITEMS" not in pt:
            errors.append("build_status missing MISSING / BLOCKING ITEMS header")
        if "PENDING CANDIDATES" not in pt:
            errors.append("build_status missing PENDING CANDIDATES header")
        if "CONFIRMED SOURCE-BACKED FACTS" not in pt:
            errors.append("build_status missing CONFIRMED SOURCE-BACKED FACTS header")
        if "APPROVAL STATUS" not in pt:
            errors.append("build_status missing APPROVAL STATUS header")
        if "NEXT ACTION" not in pt:
            errors.append("build_status missing NEXT ACTION header")
        if not preview.get("next_action"):
            errors.append("build_status missing next_action")

    # --- Fill fields for draft_preview ---
    _apply(sid, "from: CO, USS NEVERSAIL")
    _apply(sid, "to: SECNAV")
    _apply(sid, "subj: TEST SUBJECT for readability smoke")
    _apply(sid, "body: Test paragraph one.\nTest paragraph two.")
    _apply(sid, "date: 2026-06-28")
    _apply(sid, "signature.name: J. Doe")

    # --- Draft preview before approval ---
    preview = _preview(sid)
    if not preview.get("success"):
        errors.append(f"draft_preview failed: {preview.get('error')}")
    elif preview.get("mode") != "draft_preview":
        errors.append(f"expected mode draft_preview, got {preview.get('mode')}")
    else:
        pt = preview.get("preview_text", "")
        if "DRAFT PREVIEW  NOT FINAL" not in pt:
            errors.append("draft_preview missing NOT FINAL banner")
        if "BUILD STATUS" in pt:
            errors.append("draft_preview should not contain BUILD STATUS")
        # New section headers
        if "DOCUMENT HEADER" not in pt:
            errors.append("draft_preview missing DOCUMENT HEADER")
        if "ADDRESSES" not in pt:
            errors.append("draft_preview missing ADDRESSES")
        if "SUBJECT" not in pt:
            errors.append("draft_preview missing SUBJECT")
        if "BODY  [AI-DRAFTED OR USER-PROVIDED — REVIEW REQUIRED]" not in pt:
            errors.append("draft_preview missing body review label")
        if "SIGNATURE" not in pt:
            errors.append("draft_preview missing SIGNATURE")
        if "PENDING CANDIDATES" not in pt:
            errors.append("draft_preview missing PENDING CANDIDATES")
        if "CONFIRMED SOURCE-BACKED FACTS" not in pt:
            errors.append("draft_preview missing CONFIRMED SOURCE-BACKED FACTS")
        if "VALIDATION SUMMARY" not in pt:
            errors.append("draft_preview missing VALIDATION SUMMARY")
        if "APPROVAL STATUS" not in pt:
            errors.append("draft_preview missing APPROVAL STATUS")
        if "NEXT ACTION" not in pt:
            errors.append("draft_preview missing NEXT ACTION")
        if not preview.get("body_review_required"):
            errors.append("draft_preview missing body_review_required flag")

        # Approval state check
        ap = preview.get("approval") or {}
        if ap.get("approved_for_finalize"):
            errors.append("draft_preview should not show approved_for_finalize yet")

    # --- Read-only check: payload should not change from preview ---
    status_before = _status(sid)
    _preview(sid)
    status_after = _status(sid)
    if status_before.get("payload") != status_after.get("payload"):
        errors.append("preview mutated payload")
    if (status_before.get("candidates", {}).get("counts", {}).get("pending", 0) !=
            status_after.get("candidates", {}).get("counts", {}).get("pending", 0)):
        errors.append("preview mutated candidate counts")

    # --- Approve and verify approved banner ---
    approve_r = _approve(sid)
    if not approve_r.get("success"):
        errors.append(f"approve failed: {approve_r.get('error')}")
    else:
        if not approve_r.get("approved_for_finalize"):
            errors.append("approve did not set approved_for_finalize")

    preview = _preview(sid)
    pt = preview.get("preview_text", "")
    if "DRAFT PREVIEW  APPROVED FOR FINALIZE" not in pt:
        errors.append("approved draft_preview missing APPROVED FOR FINALIZE banner")
    if "END DRAFT PREVIEW  APPROVED FOR FINALIZE" not in pt:
        errors.append("approved draft_preview missing approved footer")
    ap = preview.get("approval") or {}
    if not ap.get("approval_current"):
        errors.append("approved draft_preview should show approval_current=true")

    # --- Approval gate still enforced: finalize should succeed after approve ---
    fin = _finalize(sid)
    if not fin.get("success"):
        errors.append(f"finalize after approve failed: {fin.get('error')}")
    else:
        gate = fin.get("approval_gate") or {}
        if not gate.get("passed"):
            errors.append("finalize after approve: approval_gate should pass")

    # --- Report ---
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
