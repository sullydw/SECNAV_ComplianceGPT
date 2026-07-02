#!/usr/bin/env python3
"""
Phase L.30R — Hermes Session Manager Wrapper Smoke Test

Exercises every required wrapper command (new, say, preview, revise, approve,
ready, finalize, render, candidates, candidate-confirm, candidate-reject) and
verifies pass-through fields, message clarity, approval hardening, and
natural-language revise.

Does NOT modify production code, renderer, validator, or rules.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_VENV_PYTHON = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"
_TMP_DIR = _REPO_ROOT / "tmp"
_TMP_DIR.mkdir(parents=True, exist_ok=True)

def _run_manager(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_VENV_PYTHON), str(_MANAGER)] + args,
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


def _fail(step: str, got: dict) -> None:
    print(f"FAIL at {step}: {json.dumps(got, indent=2, default=str)}")
    sys.exit(1)


def main() -> None:
    # 1. new creates a session
    r = _run_manager(["new"])
    if not r.get("success"):
        _fail("new", r)
    sid = r["session_id"]
    if not sid:
        _fail("new - no session_id", r)
    print(f"OK: new -> session {sid}")

    # 2. say applies realistic letter info (mediator extracts some fields)
    say_text = (
        "Create a standard letter. SSIC 5216. Originator code CG. "
        "From Commanding Officer, Marine Corps Air Station New River. "
        "To Commanding General, II Marine Expeditionary Force. "
        "Subject ADMINISTRATIVE CORRESPONDENCE PROCESS REVIEW. "
        "Date 1 July 2026. "
        "Body Paragraph 1. This letter reviews administrative correspondence procedures currently in use at Marine Corps Air Station New River. "
        "Paragraph 2. We request coordination with II MEF to update joint administrative correspondence processes to ensure standardization across commands. "
        "Signed by A. B. SAMPLE. Commanding Officer."
    )
    r = _run_manager(["say", "--session", sid, "--text", say_text])
    if not r.get("success"):
        _fail("say", r)
    print(f"OK: say applied fields")

    # Supplement any fields the mediator may have missed via direct answer
    payload = r.get("payload", {}) or {}
    missing = []
    if not payload.get("from"):
        missing.append(("from", "Commanding Officer, Marine Corps Air Station New River"))
    if not payload.get("date"):
        missing.append(("date", "1 July 2026"))
    if not payload.get("signature") or not (payload.get("signature") or {}).get("name"):
        missing.append(("signature.name", "A. B. SAMPLE"))
    if not payload.get("signature") or not (payload.get("signature") or {}).get("title"):
        missing.append(("signature.title", "Commanding Officer"))
    if not payload.get("originator_code"):
        missing.append(("originator_code", "CG"))
    if not payload.get("ssic"):
        missing.append(("ssic", "5216"))

    for field, value in missing:
        r = _run_manager(["answer", "--session", sid, "--field", field, "--value", value])
        if not r.get("success"):
            _fail(f"answer {field}", r)
        print(f"OK: answer applied {field}")

    # 3. preview returns draft_preview and preview_text
    r = _run_manager(["preview", "--session", sid])
    if not r.get("success"):
        _fail("preview", r)
    mode = r.get("mode")
    if mode != "draft_preview":
        _fail(f"preview mode expected draft_preview, got {mode}", r)
    if not r.get("preview_text"):
        _fail("preview missing preview_text", r)
    if "message" not in r:
        _fail("preview missing message field", r)
    print(f"OK: preview mode={mode}, has preview_text and message")

    # 4. approve succeeds after preview gate
    r = _run_manager(["approve", "--session", sid])
    if not r.get("success"):
        _fail("approve", r)
    if not r.get("approved_for_finalize"):
        _fail("approve approved_for_finalize false", r)
    if not r.get("current_preview_hash"):
        _fail("approve missing current_preview_hash", r)
    if "message" not in r:
        _fail("approve missing message field", r)
    print(f"OK: approve approved_for_finalize={r['approved_for_finalize']}")

    # 5. ready shows approved_ready=true
    r = _run_manager(["ready", "--session", sid])
    if not r.get("success"):
        _fail("ready", r)
    if not r.get("validation_ready"):
        _fail("ready validation_ready false", r)
    if not r.get("approved_ready"):
        _fail("ready approved_ready false", r)
    if not r.get("approval_required"):
        _fail("ready approval_required false", r)
    if "approval_gate" not in r:
        _fail("ready missing approval_gate", r)
    if "render_gate" not in r:
        _fail("ready missing render_gate", r)
    print(f"OK: ready validation_ready={r['validation_ready']} approved_ready={r['approved_ready']}")

    # 6. revise clears approval
    # Seed informal contractions so "make more formal" produces a real delta
    r = _run_manager(["revise", "--session", sid, "--text", "body: Paragraph 1. We can't proceed without reviewing current correspondence procedures. Paragraph 2. We'll coordinate updates with the local command as it's essential for standardization."])
    if not r.get("success"):
        _fail("revise (seed)", r)

    r = _run_manager(["revise", "--session", sid, "--text", "make the body more formal"])
    if not r.get("success"):
        _fail("revise", r)
    if not r.get("payload_changed"):
        _fail("revise payload_changed false", r)
    if not r.get("approval_cleared"):
        _fail("revise approval_cleared false", r)
    if "proposed_kv" not in r:
        _fail("revise missing proposed_kv", r)
    if "approval" not in r:
        _fail("revise missing approval", r)
    if "validation_summary" not in r:
        _fail("revise missing validation_summary", r)
    if "message" not in r:
        _fail("revise missing message field", r)
    print(f"OK: revise payload_changed={r['payload_changed']} approval_cleared={r['approval_cleared']}")

    # 7. approve succeeds again
    r = _run_manager(["approve", "--session", sid])
    if not r.get("success"):
        _fail("re-approve", r)
    if not r.get("approved_for_finalize"):
        _fail("re-approve approved_for_finalize false", r)
    print(f"OK: re-approve approved_for_finalize={r['approved_for_finalize']}")

    # 8. candidates command works
    r = _run_manager(["candidates", "--session", sid])
    if not r.get("success"):
        _fail("candidates", r)
    if "candidates" not in r:
        _fail("candidates missing candidates field", r)
    if "message" not in r:
        _fail("candidates missing message field", r)
    print(f"OK: candidates returned list")

    # 9. candidate-confirm/reject wrappers call through safely using a test candidate
    # Use a unit_identity candidate that does NOT change required payload fields,
    # so it does not invalidate the already-approved preview hash.
    cand = {
        "candidate_type": "unit_identity",
        "input_text": "Unit is Marine Corps Air Station New River.",
        "resolved_value": {
            "unit_identity": "Marine Corps Air Station New River",
            "source_tier": "official_live",
            "source_url": "https://www.newriver.marines.mil/",
            "source_title": "Marine Corps Air Station New River",
            "source_limitation": "Official public unit website used for unit identity only.",
        },
        "source_tier": "official_live",
        "confidence": 0.95,
        "requires_user_confirmation": True,
        "rationale": "Smoke test candidate",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=_TMP_DIR) as fh:
        json.dump(cand, fh)
        cand_path = fh.name

    r = _run_manager(["candidate-add", "--session", sid, "--json", cand_path])
    if not r.get("success"):
        _fail("candidate-add", r)
    cid = r.get("candidate_id")
    if not cid:
        _fail("candidate-add missing candidate_id", r)
    print(f"OK: candidate-add got candidate_id={cid}")

    r = _run_manager(["candidate-confirm", "--session", sid, "--candidate-id", cid])
    if not r.get("success"):
        _fail("candidate-confirm", r)
    if "message" not in r:
        _fail("candidate-confirm missing message field", r)
    print(f"OK: candidate-confirm succeeded")

    # Add another candidate to test reject
    cand2 = {
        "candidate_type": "subject_draft",
        "input_text": "Use test subject.",
        "resolved_value": {"subj": "TEST SUBJECT"},
        "source_tier": "user_input",
        "confidence": 0.5,
        "requires_user_confirmation": True,
        "rationale": "Smoke test reject candidate",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=_TMP_DIR) as fh:
        json.dump(cand2, fh)
        cand2_path = fh.name

    r = _run_manager(["candidate-add", "--session", sid, "--json", cand2_path])
    if not r.get("success"):
        _fail("candidate-add (2)", r)
    cid2 = r.get("candidate_id")
    if not cid2:
        _fail("candidate-add (2) missing candidate_id", r)

    r = _run_manager(["candidate-reject", "--session", sid, "--candidate-id", cid2, "--reason", "Smoke test rejection"])
    if not r.get("success"):
        _fail("candidate-reject", r)
    if "message" not in r:
        _fail("candidate-reject missing message field", r)
    print(f"OK: candidate-reject succeeded")

    # Cleanup temp candidate files
    try:
        os.remove(cand_path)
        os.remove(cand2_path)
    except OSError:
        pass

    # 10. finalize wrapper succeeds after approval
    r = _run_manager(["finalize", "--session", sid])
    if not r.get("success"):
        _fail("finalize", r)
    if "message" not in r:
        _fail("finalize missing message field", r)
    print(f"OK: finalize succeeded")

    # 11. render wrapper succeeds to tmp\l30r_manager_wrapper_smoke.pdf
    pdf_path = _TMP_DIR / "l30r_manager_wrapper_smoke.pdf"
    r = _run_manager(["render", "--session", sid, "--out", str(pdf_path)])
    if not r.get("success"):
        _fail("render", r)
    if not pdf_path.exists():
        _fail("render PDF not created", r)
    size = pdf_path.stat().st_size
    if size == 0:
        _fail("render PDF is empty", r)
    print(f"OK: render -> {pdf_path} ({size} bytes)")

    print("PASS: L.30R manager wrapper smoke passed")


if __name__ == "__main__":
    raise SystemExit(main())
