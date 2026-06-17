#!/usr/bin/env python3
"""
Hermes SECNAV CLI Bridge — Phase L.28

Thin deterministic command-line wrapper for BuilderSession + MockLLMBuilderMediator.
Emits machine-readable JSON to stdout; human/debug messages go to stderr.

Run under the project venv where ReportLab is installed:
    venv\Scripts\python tools\hermes_secnav_tool.py <command>
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from conversational_builder import BuilderSession
from intake_orchestrator import IntakeOrchestrator
from llm_builder_mediator import MediatorInput, create_mock_mediator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSION_DIR = Path.home() / ".hermes" / "secnav_sessions"
_SESSION_DIR.mkdir(parents=True, exist_ok=True)

_VERSION = "L.28.1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_path(session_id: str) -> Path:
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return _SESSION_DIR / f"{safe_id}.json"


def _load_session(session_id: str) -> BuilderSession:
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    data = json.loads(path.read_text(encoding="utf-8"))

    # Restore by creating fresh session, then injecting saved user_answers
    builder = BuilderSession(session_id=session_id)
    user_answers = data.get("user_answers", data.get("payload", {}))
    builder._orchestrator = IntakeOrchestrator(user_answers=user_answers)
    builder.start()

    # Replay user decisions
    for rule_code, decision in data.get("user_decisions", {}).items():
        builder.record_user_decision(rule_code, decision)

    builder.set_draft_final_status(data.get("draft_final_status", "draft"))
    return builder


def _save_session(builder: BuilderSession) -> None:
    payload = builder.build_payload()
    # Persist user_answers so future loads are editable (override works)
    user_answers = getattr(getattr(builder, "_orchestrator", None), "_user_answers", payload)
    data = {
        "version": _VERSION,
        "saved_at": datetime.now().isoformat(),
        "session_id": builder._session_id,
        "payload": payload,
        "user_answers": user_answers,
        "draft_final_status": builder._draft_final_status,
        "user_decisions": getattr(builder, "_user_decisions", {}),
    }
    path = _session_path(builder._session_id)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, default=str))


def _gather_mediator_input(builder: BuilderSession, text: str) -> dict[str, Any]:
    payload = builder.build_payload()
    v_summary = builder.validation_summary()
    audit = builder.run_validation()

    # Build error/warning summaries for mediator context
    error_summary: list[dict[str, Any]] = []
    warning_summary: list[dict[str, Any]] = []
    for f in v_summary.get("findings", []):
        if f["severity"] == "error":
            error_summary.append({"code": f["rule_code"], "message": f["message"]})
        elif f["severity"] == "warning":
            warning_summary.append({"code": f["rule_code"], "message": f["message"]})

    # Missing fields from orchestrator status
    status = builder._orchestrator.get_status()
    missing_required = status.get("missing_required", [])
    missing_recommended = status.get("missing_recommended", [])

    return MediatorInput(
        session_id=builder._session_id,
        current_step=getattr(builder, "_current_step", "intake"),
        payload_snapshot=payload,
        missing_required_fields=missing_required,
        missing_recommended_fields=missing_recommended,
        validation_summary={"errors": v_summary["errors"], "warnings": v_summary["warnings"]},
        warning_summary=warning_summary,
        error_summary=error_summary,
        user_message=text,
    )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_start(_args: argparse.Namespace) -> None:
    builder = BuilderSession()
    result = builder.start()
    _save_session(builder)
    _emit({
        "success": True,
        "command": "start",
        "session_id": builder._session_id,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "next_question": result.get("next_question"),
        "proposed_kv": None,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_ingest(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    inp = _gather_mediator_input(builder, args.text)
    mediator = create_mock_mediator()
    out = mediator.mediate(inp)

    proposed_kv = out.get("proposed_key_value_lines", []) or []

    if not args.no_apply and proposed_kv:
        kv_text = "\n".join(proposed_kv)
        builder.ingest_user_message(kv_text)
        _save_session(builder)

    _emit({
        "success": True,
        "command": "ingest",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "next_question": out.get("next_question"),
        "proposed_kv": proposed_kv,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_apply(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    kv_raw = args.kv.replace("\\n", "\n")
    result = builder.ingest_user_message(kv_raw)
    _save_session(builder)
    _emit({
        "success": True,
        "command": "apply",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "next_question": result.get("next_question"),
        "proposed_kv": None,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_status(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    _emit({
        "success": True,
        "command": "status",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "next_question": builder.next_question(),
        "proposed_kv": None,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_validate(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    v_summary = builder.validation_summary()
    _emit({
        "success": True,
        "command": "validate",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": v_summary,
        "warning_summary": builder.warning_summary(),
        "next_question": builder.next_question(),
        "proposed_kv": None,
        "findings": v_summary.get("findings"),
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_finalize(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    result = builder.finalize(accept_warnings=args.accept_warnings)
    _save_session(builder)
    _emit({
        "success": True,
        "command": "finalize",
        "session_id": args.session,
        "payload": result.get("payload"),
        "validation_summary": result.get("validation_summary"),
        "warning_summary": result.get("warning_summary"),
        "next_question": None,
        "proposed_kv": None,
        "findings": result.get("validation_summary", {}).get("findings"),
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
    })


def cmd_render(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    v_summary = builder.validation_summary()

    if not v_summary["finalize_allowed"]:
        _emit({
            "success": False,
            "command": "render",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": v_summary,
            "warning_summary": builder.warning_summary(),
            "next_question": builder.next_question(),
            "proposed_kv": None,
            "findings": v_summary.get("findings"),
            "pdf_path": None,
            "payload_json_path": None,
            "error": f"Cannot render: {v_summary.get('block_reason', ['validation blocked'])}",
        })
        return

    result = builder.finalize()
    payload = result["payload"]

    # Write temporary payload JSON
    tmp_json = _SESSION_DIR / f"{args.session}_payload.json"
    tmp_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Resolve output path
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Render PDF via subprocess to isolate stdout pollution
    proc = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "src" / "pdf_v6_render.py"), str(tmp_json), str(out_path)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        _emit({
            "success": False,
            "command": "render",
            "session_id": args.session,
            "payload": payload,
            "validation_summary": result.get("validation_summary"),
            "warning_summary": result.get("warning_summary"),
            "next_question": None,
            "proposed_kv": None,
            "findings": result.get("validation_summary", {}).get("findings"),
            "pdf_path": None,
            "payload_json_path": str(tmp_json),
            "error": f"PDF render failed: {proc.stderr}",
        })
        return

    _save_session(builder)
    _emit({
        "success": True,
        "command": "render",
        "session_id": args.session,
        "payload": payload,
        "validation_summary": result.get("validation_summary"),
        "warning_summary": result.get("warning_summary"),
        "next_question": None,
        "proposed_kv": None,
        "findings": result.get("validation_summary", {}).get("findings"),
        "pdf_path": str(out_path),
        "payload_json_path": str(tmp_json),
        "error": None,
    })


def cmd_list(_args: argparse.Namespace) -> None:
    sessions: list[dict[str, Any]] = []
    for p in _SESSION_DIR.glob("*.json"):
        if p.name.endswith("_payload.json"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id", p.stem),
                "saved_at": data.get("saved_at", ""),
                "draft_final_status": data.get("draft_final_status", "draft"),
            })
        except Exception:
            pass
    _emit({
        "success": True,
        "command": "list",
        "session_id": None,
        "payload": None,
        "validation_summary": None,
        "warning_summary": None,
        "next_question": None,
        "proposed_kv": None,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None,
        "sessions": sessions,
    })


def cmd_reset(args: argparse.Namespace) -> None:
    path = _session_path(args.session)
    payload_json = _SESSION_DIR / f"{args.session}_payload.json"
    deleted = False
    if path.exists():
        path.unlink()
        deleted = True
    if payload_json.exists():
        payload_json.unlink()
    _emit({
        "success": deleted,
        "command": "reset",
        "session_id": args.session,
        "payload": None,
        "validation_summary": None,
        "warning_summary": None,
        "next_question": None,
        "proposed_kv": None,
        "findings": None,
        "pdf_path": None,
        "payload_json_path": None,
        "error": None if deleted else "Session not found",
    })


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes SECNAV CLI Bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("start", help="Create a new session")

    ingest_p = subparsers.add_parser("ingest", help="Ingest natural language and optionally apply")
    ingest_p.add_argument("--session", required=True)
    ingest_p.add_argument("--text", required=True)
    ingest_p.add_argument("--no-apply", action="store_true", help="Preview only, do not apply")

    apply_p = subparsers.add_parser("apply", help="Apply key-value lines")
    apply_p.add_argument("--session", required=True)
    apply_p.add_argument("--kv", required=True, help="Key:value lines (newline separated)")

    status_p = subparsers.add_parser("status", help="Show session status")
    status_p.add_argument("--session", required=True)

    validate_p = subparsers.add_parser("validate", help="Run validation")
    validate_p.add_argument("--session", required=True)

    finalize_p = subparsers.add_parser("finalize", help="Finalize the draft")
    finalize_p.add_argument("--session", required=True)
    finalize_p.add_argument("--accept-warnings", action="store_true")

    render_p = subparsers.add_parser("render", help="Render PDF")
    render_p.add_argument("--session", required=True)
    render_p.add_argument("--out", required=True)

    subparsers.add_parser("list", help="List sessions")

    reset_p = subparsers.add_parser("reset", help="Delete a session")
    reset_p.add_argument("--session", required=True)

    args = parser.parse_args(argv)

    handlers: dict[str, Any] = {
        "start": cmd_start,
        "ingest": cmd_ingest,
        "apply": cmd_apply,
        "status": cmd_status,
        "validate": cmd_validate,
        "finalize": cmd_finalize,
        "render": cmd_render,
        "list": cmd_list,
        "reset": cmd_reset,
    }

    try:
        handlers[args.command](args)
    except Exception as exc:
        _emit({
            "success": False,
            "command": args.command,
            "session_id": getattr(args, "session", None),
            "payload": None,
            "validation_summary": None,
            "warning_summary": None,
            "next_question": None,
            "proposed_kv": None,
            "findings": None,
            "pdf_path": None,
            "payload_json_path": None,
            "error": str(exc),
        })
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
