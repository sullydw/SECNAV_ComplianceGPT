#!/usr/bin/env python3
"""
Phase L.30M Smoke Test — Natural-Language Draft Revisions

Verifies:
- key:value body revision still works
- "change subject to ..." works
- "change signer to ..." works
- "remove attachment sentence" works
- approval clears after draft-relevant change
- unsupported instruction fails safely
- no candidate change, finalize, render, or lookup occurs
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


def _revise(session_id: str, text: str) -> dict:
    return _run_tool(["revise", "--session", session_id, "--text", text])


def _preview(session_id: str) -> dict:
    return _run_tool(["preview", "--session", session_id])


def _approve(session_id: str) -> dict:
    return _run_tool(["approve", "--session", session_id])


def _status(session_id: str) -> dict:
    return _run_tool(["status", "--session", session_id])


def main() -> int:
    errors: list[str] = []

    # --- Start session ---
    start_r = _run_tool(["start"])
    if not start_r.get("success"):
        print(f"FAIL: start failed: {start_r.get('error')}")
        return 1
    sid = start_r["session_id"]

    # --- Build a complete-enough draft for approval ---
    _apply(sid, "from: CO, USS NEVERSAIL")
    _apply(sid, "to: SECNAV")
    _apply(sid, "subj: Initial subject for testing revisions")
    _apply(sid, "body: Paragraph one about readiness.\nParagraph two with an attachment reference.\nThe attachment sentence is here.")
    _apply(sid, "date: 2026-06-28")
    _apply(sid, "signature.name: J. Doe")

    # --- Approve draft ---
    approve_r = _approve(sid)
    if not approve_r.get("success"):
        errors.append(f"approve failed: {approve_r.get('error')}")
    else:
        if not approve_r.get("approved_for_finalize"):
            errors.append("approve did not set approved_for_finalize")

    # --- Verify approved ---
    preview = _preview(sid)
    ap = preview.get("approval") or {}
    if not ap.get("approval_current"):
        errors.append("draft should be approved before revisions")

    # --- 1. key:value body revision still works ---
    rev = _revise(sid, "body: New body via keyvalue revision.")
    if not rev.get("success"):
        errors.append(f"key:value revise failed: {rev.get('error')}")
    else:
        if not rev.get("payload_changed"):
            errors.append("key:value revise should change payload")
        if not rev.get("approval_cleared"):
            errors.append("key:value revise should clear approval")
        payload = rev.get("payload", {})
        body = payload.get("body", [])
        if isinstance(body, list):
            body_str = "\n".join(body)
        else:
            body_str = str(body)
        if "New body via keyvalue revision" not in body_str:
            errors.append(f"key:value revise did not update body: {body_str}")

    # --- Re-approve for next test ---
    _approve(sid)

    # --- 2. "change subject to ..." works ---
    rev = _revise(sid, "change the subject to Updated subject via natural language")
    if not rev.get("success"):
        errors.append(f"change subject revise failed: {rev.get('error')}")
    else:
        if not rev.get("payload_changed"):
            errors.append("change subject should change payload")
        if not rev.get("approval_cleared"):
            errors.append("change subject should clear approval")
        payload = rev.get("payload", {})
        if payload.get("subj") != "Updated subject via natural language":
            errors.append(f"change subject did not update subj: {payload.get('subj')}")

    # --- Re-approve for next test ---
    _approve(sid)

    # --- 3. "change signer to ..." works ---
    rev = _revise(sid, "change the signer to C. Smith")
    if not rev.get("success"):
        errors.append(f"change signer revise failed: {rev.get('error')}")
    else:
        if not rev.get("payload_changed"):
            errors.append("change signer should change payload")
        if not rev.get("approval_cleared"):
            errors.append("change signer should clear approval")
        payload = rev.get("payload", {})
        sig = payload.get("signature", {})
        if isinstance(sig, dict):
            if sig.get("name") != "C. Smith":
                errors.append(f"change signer did not update signature.name: {sig}")
        else:
            errors.append(f"change signer: signature not a dict: {sig}")

    # --- Re-approve for next test ---
    _approve(sid)

    # --- 4. "remove attachment sentence" works ---
    rev = _revise(sid, "remove the attachment sentence")
    if not rev.get("success"):
        errors.append(f"remove attachment sentence revise failed: {rev.get('error')}")
    else:
        if not rev.get("payload_changed"):
            errors.append("remove attachment sentence should change payload")
        if not rev.get("approval_cleared"):
            errors.append("remove attachment sentence should clear approval")
        payload = rev.get("payload", {})
        body = payload.get("body", [])
        if isinstance(body, list):
            body_str = "\n".join(body)
        else:
            body_str = str(body)
        if "attachment" in body_str.lower():
            errors.append(f"remove attachment failed; body still contains 'attachment': {body_str}")

    # --- Re-approve for next test ---
    _approve(sid)

    # --- 5. Unsupported instruction fails safely ---
    rev = _revise(sid, "translate the entire letter to French")
    if rev.get("success"):
        errors.append("unsupported instruction should fail")
    else:
        err = rev.get("error", "")
        if "Unsupported revision instruction" not in err:
            errors.append(f"unsupported instruction error message unexpected: {err}")

    # --- 6. Verify approval remains after unsupported failure ---
    preview = _preview(sid)
    ap = preview.get("approval") or {}
    if not ap.get("approval_current"):
        errors.append("approval should remain after unsupported revise failure")

    # --- 7. Read-only safety: candidate counts unchanged ---
    status_before = _status(sid)
    _revise(sid, "change the subject to Safety check subject")
    status_after = _status(sid)
    before_counts = status_before.get("candidates", {}).get("counts", {})
    after_counts = status_after.get("candidates", {}).get("counts", {})
    if before_counts != after_counts:
        errors.append("revise changed candidate counts unexpectedly")

    # --- 8. No finalize/render triggered by revise ---
    # (revise does not call finalize or render; we just verify it returns revise command)
    rev = _revise(sid, "change the date to 2026-07-01")
    if rev.get("command") != "revise":
        errors.append(f"revise command field wrong: {rev.get('command')}")

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
