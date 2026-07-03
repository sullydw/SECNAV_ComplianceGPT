#!/usr/bin/env python3
"""
Phase L.30T — Friendly Chat Responses Smoke Test

Proves hermes_chat_builder.py returns friendly assistant_response text
alongside existing machine-readable fields, for every major phase.

Does NOT modify production code, renderer, validator, or rules.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_BUILDER = _TOOL_ROOT / "hermes_chat_builder.py"
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"


def _run_builder(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_BUILDER)] + args,
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


def _fail(step: str, got: dict) -> None:
    print(f"FAIL at {step}: {json.dumps(got, indent=2, default=str)}")
    sys.exit(1)


def _assert_contains(haystack: str, needle: str, step: str) -> None:
    if not haystack or needle.lower() not in haystack.lower():
        print(f"FAIL {step}: expected '{needle}' in assistant_response")
        sys.exit(1)


def main() -> int:
    # -----------------------------------------------------------------------
    # 1. start
    # -----------------------------------------------------------------------
    r = _run_builder(["start"])
    if not r.get("success"):
        _fail("start", r)
    chat_id = r.get("chat_id")
    session_id = r.get("session_id")
    if not chat_id or not session_id:
        _fail("start - missing ids", r)
    print(f"OK: start -> chat_id={chat_id}, session_id={session_id}")

    # -----------------------------------------------------------------------
    # 2. initial incomplete chat -> build_status, friendly missing/next-step language
    # -----------------------------------------------------------------------
    text_incomplete = "I need a standard letter to II MEF about reviewing correspondence procedures."
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", text_incomplete])
    if not r.get("success"):
        _fail("chat (initial incomplete)", r)
    phase = r.get("phase")
    if phase not in ("build_status", "draft_preview"):
        _fail(f"chat phase unexpected: {phase}", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "missing", "initial incomplete chat assistant_response mentions missing")
    print(f"OK: chat(incomplete) phase={phase} assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 3. complete the draft with full details
    # -----------------------------------------------------------------------
    text1 = (
        "I need a standard letter to II MEF about reviewing correspondence procedures. "
        "SSIC 5216. Originator code CG. "
        "From Commanding Officer, Marine Corps Air Station New River. "
        "To Commanding General, II Marine Expeditionary Force. "
        "Subject ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW. "
        "Date 1 July 2026. "
        "Body Paragraph 1. This letter reviews administrative correspondence procedures currently in use at Marine Corps Air Station New River. "
        "Paragraph 2. We request coordination with II MEF to update joint administrative correspondence processes to ensure standardization across commands. "
        "Signed by A. B. SAMPLE. Commanding Officer."
    )
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", text1])
    if not r.get("success"):
        _fail("chat (full details)", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "draft", "full details assistant_response mentions draft")
    print(f"OK: chat(full) phase={r.get('phase')} assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 4. fill remaining fields via manager so we can test preview/approve/revise
    # -----------------------------------------------------------------------
    mgr_status = _run_manager(["status", "--session", session_id])
    payload = mgr_status.get("payload", {})
    if not payload.get("ssic"):
        _run_manager(["answer", "--session", session_id, "--field", "ssic", "--value", "5216"])
    if not payload.get("originator_code"):
        _run_manager(["answer", "--session", session_id, "--field", "originator_code", "--value", "CG"])
    if not payload.get("from"):
        _run_manager(["answer", "--session", session_id, "--field", "from", "--value", "Commanding Officer, Marine Corps Air Station New River"])
    if not payload.get("to"):
        _run_manager(["answer", "--session", session_id, "--field", "to", "--value", "Commanding General, II Marine Expeditionary Force"])
    if not payload.get("subj"):
        _run_manager(["answer", "--session", session_id, "--field", "subj", "--value", "ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW"])
    if not payload.get("date"):
        _run_manager(["answer", "--session", session_id, "--field", "date", "--value", "1 July 2026"])
    if not payload.get("body"):
        _run_manager(["answer", "--session", session_id, "--field", "body", "--value", "1. Review procedures. 2. Coordinate updates."])
    if not (payload.get("signature") or {}).get("name"):
        _run_manager(["answer", "--session", session_id, "--field", "signature.name", "--value", "A. B. SAMPLE"])
    if not (payload.get("signature") or {}).get("title"):
        _run_manager(["answer", "--session", session_id, "--field", "signature.title", "--value", "Commanding Officer"])

    # -----------------------------------------------------------------------
    # 5. preview -> friendly "review/approve/change" language
    # -----------------------------------------------------------------------
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "show me the preview"])
    if not r.get("success"):
        _fail("chat (preview)", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "review", "preview assistant_response invites review")
    print(f"OK: chat(preview) assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 6. approve -> friendly "draft is approved" language
    # -----------------------------------------------------------------------
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "Looks good"])
    if not r.get("success"):
        _fail("chat (approve)", r)
    if r.get("intent") != "approve":
        _fail(f"chat approve intent expected 'approve', got {r.get('intent')}", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "approved", "approve assistant_response says approved")
    print(f"OK: chat(approve) assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 7. revise -> friendly "approval was cleared" language
    # -----------------------------------------------------------------------
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "Change the subject to REVISED ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW"])
    if not r.get("success"):
        _fail("chat (revise)", r)
    if r.get("intent") != "revise":
        _fail(f"chat revise intent expected 'revise', got {r.get('intent')}", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "approval", "revise assistant_response mentions approval cleared")
    print(f"OK: chat(revise) assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 8. re-approve (to get back to approved_ready)
    # -----------------------------------------------------------------------
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "Looks good"])
    if not r.get("success"):
        _fail("chat (re-approve)", r)
    if r.get("phase") != "approved_ready":
        _fail(f"chat re-approve phase expected approved_ready, got {r.get('phase')}", r)
    print(f"OK: chat(re-approve) phase={r.get('phase')}")

    # -----------------------------------------------------------------------
    # 9. render blocked before approval (reset, fill, request render without approve)
    # -----------------------------------------------------------------------
    r = _run_builder(["reset", "--chat-id", chat_id])
    if not r.get("success"):
        _fail("reset", r)
    # Quick fill after reset
    new_session = r.get("session_id")
    _run_manager(["answer", "--session", new_session, "--field", "ssic", "--value", "5216"])
    _run_manager(["answer", "--session", new_session, "--field", "originator_code", "--value", "CG"])
    _run_manager(["answer", "--session", new_session, "--field", "from", "--value", "CO MCAS New River"])
    _run_manager(["answer", "--session", new_session, "--field", "to", "--value", "CG II MEF"])
    _run_manager(["answer", "--session", new_session, "--field", "subj", "--value", "TEST"])
    _run_manager(["answer", "--session", new_session, "--field", "date", "--value", "1 July 2026"])
    _run_manager(["answer", "--session", new_session, "--field", "body", "--value", "test"])
    _run_manager(["answer", "--session", new_session, "--field", "signature.name", "--value", "A. B. SAMPLE"])
    _run_manager(["answer", "--session", new_session, "--field", "signature.title", "--value", "Commanding Officer"])
    # Request render without approval
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "make the PDF"])
    if r.get("success"):
        _fail("render without approval should fail", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "PDF", "blocked render assistant_response mentions PDF")
    print(f"OK: blocked render assistant_response={ar[:80]}...")

    # -----------------------------------------------------------------------
    # 10. successful render after approval -> friendly "PDF is ready" + path
    # -----------------------------------------------------------------------
    # Approve on the reset session
    _run_builder(["chat", "--chat-id", chat_id, "--text", "Looks good"])
    r = _run_builder(["chat", "--chat-id", chat_id, "--text", "Make the PDF"])
    if not r.get("success"):
        _fail("chat (render)", r)
    if r.get("phase") != "rendered":
        _fail(f"chat render phase expected rendered, got {r.get('phase')}", r)
    ar = r.get("assistant_response", "")
    _assert_contains(ar, "PDF", "rendered assistant_response mentions PDF")
    pdf_path = r.get("pdf_path")
    pdf_size = r.get("pdf_size", 0)
    if not pdf_path or pdf_size == 0:
        _fail("chat render missing valid PDF path/size", r)
    print(f"OK: chat(render) assistant_response={ar[:80]}... pdf={pdf_path} size={pdf_size}")

    # -----------------------------------------------------------------------
    # 11. machine-readable fields still present
    # -----------------------------------------------------------------------
    required_fields = {
        "success", "command", "chat_id", "session_id", "intent",
        "phase", "message", "next_step",
    }
    missing = required_fields - set(r.keys())
    if missing:
        _fail(f"machine-readable fields missing: {missing}", r)
    print("OK: machine-readable fields preserved")

    print("PASS: L.30T friendly chat response smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
