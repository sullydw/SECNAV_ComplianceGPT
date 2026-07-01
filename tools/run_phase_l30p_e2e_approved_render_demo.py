#!/usr/bin/env python3
"""
Phase L.30P Realistic End-to-End Approved Render Demo

Proves the approved-render workflow works from intake through PDF render,
including source-backed candidate display and approval hardening.
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

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"
_PDF_OUT = _REPO_ROOT / "tmp" / "l30p_e2e_approved_render_demo.pdf"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_tool(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_TOOL)] + args,
        capture_output=True,
        text=True,
        timeout=120,
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
        timeout=120,
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    errors: list[str] = []
    tmp_files: list[Path] = []
    session_id: str | None = None

    try:
        # --- 1. Start a fresh session ---
        start_r = _run_tool(["start"])
        if not start_r.get("success"):
            print(f"FAIL: start failed: {start_r.get('error')}")
            return 1
        session_id = start_r["session_id"]

        # --- 2. Confirm approve fails before required preview fields exist ---
        approve_incomplete = _run_tool(["approve", "--session", session_id])
        if approve_incomplete.get("success"):
            errors.append("approve on incomplete session should fail")
        err_msg = approve_incomplete.get("error", "")
        if "Cannot approve" not in err_msg:
            errors.append(f"incomplete approve error should say 'Cannot approve', got: {err_msg}")

        # --- 3. Apply realistic SECNAV letter fields ---
        fields = [
            ("doc_type", "standard_letter"),
            ("ssic", "5216"),
            ("originator_code", "CG"),
            ("from", "Commanding Officer, Marine Corps Air Station New River"),
            ("to", "Commanding General, II Marine Expeditionary Force"),
            ("subj", "ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW"),
            ("date", "1 July 2026"),
            ("body", (
                "1. We can't proceed with current administrative correspondence procedures "
                "without reviewing established Department of the Navy guidance. "
                "We're requesting that all units don't delay necessary updates.\n\n"
                "2. Coordinate with the appropriate staff sections to update local standing "
                "operating procedures and report any discrepancies or recommended changes "
                "through the chain of command."
            )),
            ("signature.name", "A. B. SAMPLE"),
            ("signature.title", "Commanding Officer"),
        ]
        for field, value in fields:
            r = _apply(session_id, f"{field}: {value}")
            if not r.get("success"):
                errors.append(f"apply '{field}' failed: {r.get('error')}")

        # --- 4. Add L.30J-style official-live unit_identity candidate ---
        unit_candidate = {
            "candidate_type": "unit_identity",
            "input_text": "Marine Corps Air Station New River is the originator unit.",
            "resolved_value": {
                "unit": "Marine Corps Air Station New River",
                "command": "Commanding Officer",
                "source_tier": "official_live",
                "source_url": "https://www.newriver.marines.mil/",
                "source_title": "Marine Corps Air Station New River",
                "source_limitation": "Official public unit website used for unit identity only.",
            },
            "confidence": 0.97,
            "requires_user_confirmation": True,
        }
        cand_path = _TOOL_ROOT / f"l30p_unit_cand_{uuid.uuid4().hex[:8]}.json"
        cand_path.write_text(json.dumps(unit_candidate, indent=2), encoding="utf-8")
        tmp_files.append(cand_path)

        add_cand = _add_candidate(session_id, cand_path)
        if not add_cand.get("success"):
            errors.append(f"candidate-add failed: {add_cand.get('error')}")

        # --- 5. Run preview and verify source display + read-only ---
        prev = _preview(session_id)
        if not prev.get("success"):
            errors.append(f"preview failed: {prev.get('error')}")
        else:
            if prev.get("mode") != "draft_preview":
                errors.append(f"expected mode draft_preview, got {prev.get('mode')}")

            pt = prev.get("preview_text", "")

            # Verify [OFFICIAL SOURCE] appears
            if "[OFFICIAL SOURCE]" not in pt:
                errors.append("preview_text missing [OFFICIAL SOURCE]")

            # Verify source_url appears
            if "https://www.newriver.marines.mil/" not in pt:
                errors.append("preview_text missing source_url")

            # Verify source_title appears
            if "Marine Corps Air Station New River" not in pt:
                errors.append("preview_text missing source_title")

            # Verify source_limitation appears
            if "Official public unit website used for unit identity only." not in pt:
                errors.append("preview_text missing source_limitation")

            # Verify preview remains read-only (body review required)
            if prev.get("body_review_required") is not True:
                errors.append("preview should be read-only (body_review_required=True)")

            # Approval should NOT be current yet
            approval = prev.get("approval") or {}
            if approval.get("approval_current") is not False:
                errors.append(f"approval_current should be False before approve, got {approval.get('approval_current')}")

        # --- 6. Approve the draft ---
        apr = _run_tool(["approve", "--session", session_id])
        if not apr.get("success"):
            errors.append(f"approve failed: {apr.get('error')}")
        elif apr.get("approval_current") is not True:
            errors.append(f"approve approval_current not True: {apr.get('approval_current')}")

        # --- 7. Run ready through manager and verify readiness ---
        ready_r = _run_manager(["ready", "--session", session_id])
        if ready_r.get("validation_ready") is not True:
            errors.append(f"ready validation_ready not True: {ready_r.get('validation_ready')}")
        if ready_r.get("approved_ready") is not True:
            errors.append(f"ready approved_ready not True: {ready_r.get('approved_ready')}")
        if ready_r.get("ready") is not True:
            errors.append(f"ready overall ready not True: {ready_r.get('ready')}")

        # --- 8. Revise the body using natural-language revise: make the body more formal ---
        rev = _run_tool(["revise", "--session", session_id, "--text", "make the body more formal"])
        if not rev.get("success"):
            errors.append(f"revise failed: {rev.get('error')}")
        else:
            # --- 9. Verify approval is cleared ---
            if rev.get("approval_cleared") is not True:
                errors.append(f"revise approval_cleared not True: {rev.get('approval_cleared')}")
            if rev.get("payload_changed") is not True:
                errors.append(f"revise payload_changed not True: {rev.get('payload_changed')}")

        # --- 10. Run preview again ---
        prev2 = _preview(session_id)
        if not prev2.get("success"):
            errors.append(f"preview after revise failed: {prev2.get('error')}")
        else:
            approval2 = prev2.get("approval") or {}
            if approval2.get("approval_current") is not False:
                errors.append(f"approval_current should be False after revise, got {approval2.get('approval_current')}")

        # --- 11. Re-approve ---
        apr2 = _run_tool(["approve", "--session", session_id])
        if not apr2.get("success"):
            errors.append(f"re-approve failed: {apr2.get('error')}")
        elif apr2.get("approval_current") is not True:
            errors.append(f"re-approve approval_current not True: {apr2.get('approval_current')}")

        # --- 12. Run ready again and verify approved_ready is true ---
        ready2 = _run_manager(["ready", "--session", session_id])
        if ready2.get("approved_ready") is not True:
            errors.append(f"ready after re-approve approved_ready not True: {ready2.get('approved_ready')}")

        # --- 13. Finalize successfully ---
        fin = _run_tool(["finalize", "--session", session_id])
        if not fin.get("success"):
            errors.append(f"finalize failed: {fin.get('error')}")
        else:
            gate = fin.get("approval_gate") or {}
            if gate.get("passed") is not True:
                errors.append(f"finalize approval_gate.passed not True: {gate}")

        # --- 14. Render successfully ---
        _PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
        ren = _run_tool(["render", "--session", session_id, "--out", str(_PDF_OUT)])
        if not ren.get("success"):
            errors.append(f"render failed: {ren.get('error')}")
        else:
            ren_gate = ren.get("approval_gate") or {}
            if ren_gate.get("passed") is not True:
                errors.append(f"render approval_gate.passed not True: {ren_gate}")

        # --- 15. Verify PDF exists and has nonzero size ---
        if not _PDF_OUT.exists():
            errors.append(f"PDF not found at {_PDF_OUT}")
        elif _PDF_OUT.stat().st_size == 0:
            errors.append(f"PDF at {_PDF_OUT} has zero size")

        # --- 16. Cleanup temporary candidate JSON files only ---
        for p in tmp_files:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

        if errors:
            print(f"FAIL: {len(errors)} error(s)")
            for e in errors:
                print(f"  - {e}")
            return 1

        print("PASS: L.30P end-to-end approved render demo passed")
        return 0

    except Exception as exc:
        print(f"FAIL: unexpected exception: {exc}")
        return 1

    finally:
        # Always reset the session to avoid leaving stale demo data
        if session_id:
            try:
                _run_tool(["reset", "--session", session_id])
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
