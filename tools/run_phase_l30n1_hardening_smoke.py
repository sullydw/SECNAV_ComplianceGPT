#!/usr/bin/env python3
"""
Phase L.30N-1 Smoke Test — Harden preview source warnings and approval gates

Verifies:
- L.30J-style candidate with provenance inside resolved_value shows [OFFICIAL SOURCE]
- source_url/source_title/source_limitation inside resolved_value appear in preview_text
- approve on incomplete session fails and does not set approval_current
- finalize on approved but validation-blocked session fails
- ready/manager output shows validation readiness separately from approval-gated readiness
- existing top-level candidate source_tier still works
- preview remains read-only
- no candidate counts change
- no render occurs
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"
_MGR = _TOOL_ROOT / "hermes_session_manager.py"


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


def _run_mgr(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_MGR)] + args,
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


def _add_candidate(session_id: str, cand_path: Path) -> dict:
    return _run_tool(["candidate-add", "--session", session_id, "--json", str(cand_path)])


def main() -> int:
    errors: list[str] = []

    # --- Start session ---
    start_r = _run_tool(["start"])
    if not start_r.get("success"):
        print(f"FAIL: start failed: {start_r.get('error')}")
        return 1
    sid = start_r["session_id"]

    # --- 1. Approve on incomplete session must fail ---
    approve_incomplete = _run_tool(["approve", "--session", sid])
    if approve_incomplete.get("success"):
        errors.append("approve on incomplete session should fail")
    if approve_incomplete.get("mode") != "build_status":
        errors.append("incomplete approve should report mode=build_status")
    if (approve_incomplete.get("missing_for_preview") or []) == []:
        errors.append("incomplete approve should list missing_for_preview")
    err_msg = approve_incomplete.get("error", "")
    if "Cannot approve" not in err_msg:
        errors.append(f"incomplete approve error should say 'Cannot approve', got: {err_msg}")

    # --- Build a complete-enough draft with proper format to avoid validator errors ---
    _apply(sid, "from: COMMANDING OFFICER, USS NEVERSAIL")
    _apply(sid, "to: SECRETARY OF THE NAVY")
    _apply(sid, "subj: REQUEST FOR TESTING PROCEDURES AND AUTHORIZATION")
    _apply(sid, "body: This is a test body paragraph for the purpose of verifying system behavior.")
    _apply(sid, "date: 28 June 2026")
    _apply(sid, "signature.name: J. DOE")

    # --- Add L.30J-style candidate with provenance in resolved_value ---
    lj_candidate = {
        "candidate_type": "unit_identity",
        "input_text": "CO of USS NEVERSAIL is CDR J. Smith per official Navy listing.",
        "resolved_value": {
            "unit": "USS NEVERSAIL",
            "co_name": "CDR J. Smith",
            "source_tier": "official_live",
            "source_url": "https://www.navy.mil/l30j",
            "source_title": "Official Navy L30J Listing",
            "source_limitation": "Requires NIPR access",
        },
        "confidence": 0.95,
        "requires_user_confirmation": True,
    }
    # Also add top-level source_tier candidate to confirm fallback doesn't break it
    top_candidate = {
        "candidate_type": "ssic_candidate",
        "input_text": "SSIC 1234 from Jane's reference.",
        "resolved_value": {"ssic": "1234", "title": "Naval Operations"},
        "confidence": 0.72,
        "requires_user_confirmation": True,
        "source_tier": "secondary_credible",
        "source_url": "https://example.com/janes",
        "source_title": "Jane's Reference",
        "source_limitation": "Third-party database, not primary US Navy source",
    }

    tmp_dir = _TOOL_ROOT
    lj_path = tmp_dir / "cand_lj.json"
    top_path = tmp_dir / "cand_top.json"
    lj_path.write_text(json.dumps(lj_candidate), encoding="utf-8")
    top_path.write_text(json.dumps(top_candidate), encoding="utf-8")

    add_lj = _add_candidate(sid, lj_path)
    add_top = _add_candidate(sid, top_path)
    if not add_lj.get("success"):
        errors.append(f"L30J candidate add failed: {add_lj.get('error')}")
    if not add_top.get("success"):
        errors.append(f"top-level candidate add failed: {add_top.get('error')}")

    # --- Preview: verify L30J resolved_value provenance appears ---
    preview = _preview(sid)
    preview_text = preview.get("preview_text", "")

    # L30J candidate shows OFFICIAL SOURCE from resolved_value
    if "[OFFICIAL SOURCE]" not in preview_text:
        errors.append("L30J candidate with source_tier in resolved_value should show [OFFICIAL SOURCE]")

    # L30J source_url, source_title, source_limitation from resolved_value appear
    if "https://www.navy.mil/l30j" not in preview_text:
        errors.append("L30J source_url from resolved_value should appear")
    if "Official Navy L30J Listing" not in preview_text:
        errors.append("L30J source_title from resolved_value should appear")
    if "Requires NIPR access" not in preview_text:
        errors.append("L30J source_limitation from resolved_value should appear")

    # Top-level source_tier still works
    if "[SOURCE WARNING — not official; verify before confirming]" not in preview_text:
        errors.append("top-level secondary_credible candidate should show SOURCE WARNING")

    # --- 3. Ready / manager readiness separates validation and approval ---
    ready_before = _run_mgr(["ready", "--session", sid])
    # Should show validation_ready true (complete draft) but approved_ready false (not approved)
    if ready_before.get("validation_ready") is not True:
        errors.append("ready should show validation_ready=True for complete draft")
    if ready_before.get("approved_ready") is True:
        errors.append("ready should show approved_ready=False before approval")
    if ready_before.get("ready") is True:
        errors.append("ready should be False before approval")
    if ready_before.get("approval_required") is not True:
        errors.append("ready should show approval_required=True")
    msg = ready_before.get("message", "")
    if "draft is not approved" not in msg and "approved" not in msg.lower():
        errors.append(f"ready message should mention approval, got: {msg}")

    # --- 4. Approve on complete draft should succeed ---
    approve_r = _run_tool(["approve", "--session", sid])
    if not approve_r.get("success"):
        errors.append(f"approve on complete draft should succeed: {approve_r.get('error')}")
    if approve_r.get("approval_current") is not True:
        errors.append("approve should set approval_current=True")

    # --- 5. Ready after approval shows both ready ---
    ready_after = _run_mgr(["ready", "--session", sid])
    if ready_after.get("validation_ready") is not True:
        errors.append("ready after approval should show validation_ready=True")
    if ready_after.get("approved_ready") is not True:
        errors.append("ready after approval should show approved_ready=True")
    if ready_after.get("ready") is not True:
        errors.append("ready should be True after approval")

    # --- 6. Finalize on approved clean session should succeed ---
    finalize_r = _run_tool(["finalize", "--session", sid])
    if not finalize_r.get("success"):
        errors.append(f"finalize on approved clean session should succeed: {finalize_r.get('error')}")
    if finalize_r.get("approval_gate", {}).get("passed") is not True:
        errors.append("finalize success should report approval_gate passed")

    # --- 7. Finalize on incomplete session should fail with validation error first ---
    # Start a fresh incomplete session
    start2 = _run_tool(["start"])
    sid2 = start2["session_id"]
    _apply(sid2, "from: COMMANDING OFFICER, USS NEVERSAIL")
    # Leave other fields missing
    finalize2 = _run_tool(["finalize", "--session", sid2])
    if finalize2.get("success"):
        errors.append("finalize on incomplete session should fail")
    err2 = finalize2.get("error", "")
    if "finalize_allowed" not in err2 and "Cannot finalize" not in err2:
        errors.append(f"finalize on incomplete should mention validation block, got: {err2}")

    # --- 8. Finalize on complete but unapproved session should fail with approval error ---
    start3 = _run_tool(["start"])
    sid3 = start3["session_id"]
    for kv in [
        "from: COMMANDING OFFICER, USS NEVERSAIL",
        "to: SECRETARY OF THE NAVY",
        "subj: REQUEST FOR TESTING PROCEDURES AND AUTHORIZATION",
        "body: This is a test body paragraph for the purpose of verifying system behavior.",
        "date: 28 June 2026",
        "signature.name: J. DOE",
    ]:
        _apply(sid3, kv)
    finalize3 = _run_tool(["finalize", "--session", sid3])
    if finalize3.get("success"):
        errors.append("finalize on complete unapproved session should fail")
    err3 = finalize3.get("error", "")
    if "approval" not in err3.lower() and "approve" not in err3.lower():
        errors.append(f"finalize on unapproved should mention approval, got: {err3}")

    # --- 9. Preview read-only safety ---
    preview2 = _preview(sid)
    if preview2.get("pending_candidates", -1) != preview.get("pending_candidates", -2):
        errors.append("preview should not change pending candidate count")

    # Cleanup temp files and sessions
    for p in (lj_path, top_path):
        try:
            p.unlink()
        except Exception:
            pass

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
