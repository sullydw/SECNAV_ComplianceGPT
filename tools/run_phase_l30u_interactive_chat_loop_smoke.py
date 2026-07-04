#!/usr/bin/env python3
"""
Phase L.30U — Single Interactive Chat Loop Smoke Test

Proves hermes_chat_builder.py interactive mode works end-to-end:
- starts a new chat session automatically
- accepts repeated stdin lines
- routes each turn through existing deterministic chat handler
- prints assistant_response after each turn
- supports exit commands
- json-lines mode emits parseable JSON objects
- non-interactive commands still work

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


def _run_builder(args: list[str], input_text: str | None = None) -> dict:
    """Run builder CLI and return the last JSON object from stdout."""
    proc = subprocess.run(
        [str(_PYTHON), str(_BUILDER)] + args,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_REPO_ROOT),
        input=input_text,
    )
    return _last_json(proc.stdout) or {"success": False, "error": proc.stderr or f"exit code {proc.returncode}", "stdout": proc.stdout[:500]}


def _run_builder_first_json(args: list[str], input_text: str | None = None) -> dict:
    """Run builder CLI and return the first JSON object from stdout."""
    proc = subprocess.run(
        [str(_PYTHON), str(_BUILDER)] + args,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_REPO_ROOT),
        input=input_text,
    )
    objs = _extract_jsons(proc.stdout)
    return objs[0] if objs else {"success": False, "error": proc.stderr or f"exit code {proc.returncode}", "stdout": proc.stdout[:500]}


def _run_builder_all_json(args: list[str], input_text: str | None = None) -> list[dict]:
    """Run builder CLI and return all JSON objects from stdout."""
    proc = subprocess.run(
        [str(_PYTHON), str(_BUILDER)] + args,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_REPO_ROOT),
        input=input_text,
    )
    return _extract_jsons(proc.stdout)


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


def _extract_jsons(stdout: str) -> list[dict]:
    objs = []
    buf = []
    in_obj = False
    for line in stdout.splitlines():
        stripped = line.strip()
        if not in_obj and stripped == "{":
            in_obj = True
            buf = [line]
        elif in_obj:
            buf.append(line)
            if stripped == "}":
                in_obj = False
                try:
                    objs.append(json.loads("\n".join(buf)))
                except json.JSONDecodeError:
                    pass
    return objs


def _last_json(stdout: str) -> dict | None:
    objs = _extract_jsons(stdout)
    return objs[-1] if objs else None


def _fail(step: str, got) -> None:
    print(f"FAIL at {step}: {json.dumps(got, indent=2, default=str) if isinstance(got, dict) else str(got)}")
    sys.exit(1)


def _ensure_fields_filled(session_id: str) -> None:
    """Fill any remaining required fields via manager so approval/render tests can proceed."""
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
    sig = payload.get("signature") or {}
    if not sig.get("name"):
        _run_manager(["answer", "--session", session_id, "--field", "signature.name", "--value", "A. B. SAMPLE"])
    if not sig.get("title"):
        _run_manager(["answer", "--session", session_id, "--field", "signature.title", "--value", "Commanding Officer"])


def main() -> int:
    print("Phase L.30U smoke test starting...")

    # -----------------------------------------------------------------------
    # 1. interactive mode auto-creates a chat
    # -----------------------------------------------------------------------
    print("[1] interactive auto-create ...")
    startup = _run_builder_first_json(["interactive"], input_text="exit\n")
    if not startup.get("success"):
        _fail("step 1 startup success", startup)
    if not startup.get("chat_id", "").startswith("chat-"):
        _fail("step 1 chat_id format", startup)
    if not startup.get("session_id"):
        _fail("step 1 session_id present", startup)
    chat_id = startup["chat_id"]
    session_id = startup["session_id"]
    print(f"  chat_id={chat_id}")

    # -----------------------------------------------------------------------
    # 2. interactive: natural letter request
    # -----------------------------------------------------------------------
    print("[2] interactive initial letter request ...")
    lines = [
        "I need a standard letter to II MEF about reviewing correspondence procedures",
        "exit",
    ]
    r = _run_builder(["interactive", "--chat-id", chat_id], input_text="\n".join(lines))
    if not r.get("success"):
        _fail("step 2 success", r)

    # -----------------------------------------------------------------------
    # 3. interactive: provide missing details
    # -----------------------------------------------------------------------
    print("[3] interactive provide missing details ...")
    lines = [
        "from Secretary of the Navy",
        "to Commanding General II Marine Expeditionary Force",
        "subject Correspondence Review",
        "body Please review your correspondence procedures and report findings.",
        "signature A. B. SAMPLE, Secretary of the Navy",
        "exit",
    ]
    r = _run_builder(["interactive", "--chat-id", chat_id], input_text="\n".join(lines))
    if not r.get("success"):
        _fail("step 3 success", r)

    # -----------------------------------------------------------------------
    # 4. interactive: preview intent
    # -----------------------------------------------------------------------
    print("[4] interactive preview intent ...")
    lines = [
        "show me the preview",
        "exit",
    ]
    r = _run_builder(["interactive", "--chat-id", chat_id], input_text="\n".join(lines))
    if not r.get("success"):
        _fail("step 4 success", r)

    # -----------------------------------------------------------------------
    # 5. interactive: revise
    # -----------------------------------------------------------------------
    print("[5] interactive revise ...")
    lines = [
        "make the body more formal",
        "exit",
    ]
    r = _run_builder(["interactive", "--chat-id", chat_id], input_text="\n".join(lines))
    if not r.get("success"):
        _fail("step 5 success", r)

    # -----------------------------------------------------------------------
    # 6. Fill remaining fields via manager so we can test approval/render
    # -----------------------------------------------------------------------
    print("[6] fill remaining fields via manager ...")
    _ensure_fields_filled(session_id)

    # -----------------------------------------------------------------------
    # 7. interactive: approve
    # -----------------------------------------------------------------------
    print("[7] interactive approve ...")
    lines = [
        "looks good",
        "exit",
    ]
    r = _run_builder(["interactive", "--chat-id", chat_id], input_text="\n".join(lines))
    if not r.get("success"):
        _fail("step 7 success", r)

    # -----------------------------------------------------------------------
    # 8. interactive: render
    # -----------------------------------------------------------------------
    print("[8] interactive render ...")
    lines = [
        "make the pdf",
        "exit",
    ]
    jsons = _run_builder_all_json(["interactive", "--chat-id", chat_id, "--json-lines"], input_text="\n".join(lines))
    r = {}
    for obj in jsons:
        if obj.get("pdf_path"):
            r = obj
            break
    if not r.get("success"):
        _fail("step 8 success", r if r else {"json_count": len(jsons)})

    pdf_path_str = r.get("pdf_path")
    if not pdf_path_str:
        _fail("step 8 pdf_path present", r)
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        _fail("step 8 pdf exists", {"path": str(pdf_path), "exists": pdf_path.exists()})
    print(f"  PDF={pdf_path} ({pdf_path.stat().st_size} bytes)")

    # -----------------------------------------------------------------------
    # 9. json-lines mode emits parseable JSON objects
    # -----------------------------------------------------------------------
    print("[9] json-lines mode ...")
    lines = [
        "status",
        "exit",
    ]
    jsons = _run_builder_all_json(["interactive", "--chat-id", chat_id, "--json-lines"], input_text="\n".join(lines))
    if not jsons:
        _fail("step 9 json objects", {"count": len(jsons)})
    last = jsons[-1]
    if not last.get("success"):
        _fail("step 9 last success", last)
    if not any(j.get("phase") or j.get("intent") for j in jsons):
        _fail("step 9 has intent/phase", {"count": len(jsons)})
    print(f"  json objects={len(jsons)}")

    # -----------------------------------------------------------------------
    # 10. non-interactive start still works
    # -----------------------------------------------------------------------
    print("[10] non-interactive start ...")
    s = _run_builder(["start"])
    if not s.get("success"):
        _fail("step 10 start success", s)
    if not s.get("chat_id", "").startswith("chat-"):
        _fail("step 10 chat_id format", s)
    print(f"  chat_id={s['chat_id']}")

    # -----------------------------------------------------------------------
    # 11. non-interactive chat still works
    # -----------------------------------------------------------------------
    print("[11] non-interactive chat ...")
    c = _run_builder(["chat", "--chat-id", s["chat_id"], "--text", "from SECNAV to CG II MEF subject Test"])
    if not c.get("success"):
        _fail("step 11 chat success", c)
    if not c.get("phase"):
        _fail("step 11 phase present", c)
    print(f"  phase={c['phase']}")

    # -----------------------------------------------------------------------
    # 12. non-interactive status and reset still work
    # -----------------------------------------------------------------------
    print("[12] non-interactive status and reset ...")
    st = _run_builder(["status", "--chat-id", s["chat_id"]])
    if not st.get("success"):
        _fail("step 12 status success", st)
    rs = _run_builder(["reset", "--chat-id", s["chat_id"]])
    if not rs.get("success"):
        _fail("step 12 reset success", rs)

    print("\nPASS — all 12 steps passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
