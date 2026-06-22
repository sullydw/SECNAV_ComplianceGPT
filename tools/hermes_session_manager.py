#!/usr/bin/env python3
r"""
Hermes Session Manager — Phase L.29Q

Thin deterministic coordinator that drives the existing hermes_secnav_tool.py
CLI commands to make multi-turn Hermes-driven SECNAV correspondence sessions
easier to run.

Does NOT duplicate renderer, validator, detector, candidate, or BuilderSession
logic. Delegates to hermes_secnav_tool.py for all heavy lifting.

Run under the project venv:
    venv\Scripts\python tools\hermes_session_manager.py <command>
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"
_VENV_PYTHON = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
_HERMES_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VERSION = "L.29Q"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_tool(args: list[str]) -> dict[str, Any]:
    """Run hermes_secnav_tool.py via subprocess and parse JSON stdout."""
    proc = subprocess.run(
        [str(_VENV_PYTHON), str(_HERMES_TOOL)] + args,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(_REPO_ROOT),
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            "success": False,
            "error": proc.stderr or f"exit code {proc.returncode}",
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid JSON: {proc.stdout[:200]}",
        }


def _emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, default=str))


def _session_id_from_args(args: argparse.Namespace) -> str | None:
    sid: str | None = getattr(args, "session", None)
    return sid


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_new(_args: argparse.Namespace) -> None:
    """Create a new session via hermes_secnav_tool.py start."""
    r = _run_tool(["start"])
    _emit({
        "success": r.get("success", False),
        "command": "new",
        "session_id": r.get("session_id"),
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "message": f"Created session {r.get('session_id')}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_resume(args: argparse.Namespace) -> None:
    """Resume an existing session."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "resume", "error": "--session required"})
        return
    r = _run_tool(["status", "--session", sid])
    _emit({
        "success": r.get("success", False),
        "command": "resume",
        "session_id": sid,
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "message": f"Resumed session {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_say(args: argparse.Namespace) -> None:
    """Ingest user text into a session."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "say", "error": "--session required"})
        return
    r = _run_tool(["ingest", "--session", sid, "--text", args.text])
    _emit({
        "success": r.get("success", False),
        "command": "say",
        "session_id": sid,
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "proposed_kv": r.get("proposed_kv"),
        "message": f"Ingested into {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_next(args: argparse.Namespace) -> None:
    """Show the current next action via next-action."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "next", "error": "--session required"})
        return
    doc_type = getattr(args, "doc_type", None)
    tool_args = ["next-action", "--session", sid]
    if doc_type:
        tool_args += ["--doc-type", doc_type]
    r = _run_tool(tool_args)
    _emit({
        "success": r.get("success", False),
        "command": "next",
        "session_id": sid,
        "next_action": r.get("next_action"),
        "unresolved_summary": r.get("unresolved_summary"),
        "render_gate": r.get("render_gate"),
        "validation_summary": r.get("validation_summary"),
        "message": r.get("next_action", {}).get("reason", ""),
        "error": r.get("error"),
    })


def cmd_answer(args: argparse.Namespace) -> None:
    """Apply a user answer to a specific field."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "answer", "error": "--session required"})
        return
    kv = f"{args.field}: {args.value}"
    r = _run_tool(["apply", "--session", sid, "--kv", kv])
    _emit({
        "success": r.get("success", False),
        "command": "answer",
        "session_id": sid,
        "field": args.field,
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "message": f"Applied {args.field}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_ready(args: argparse.Namespace) -> None:
    """Show whether the session is ready for validate/finalize/render."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "ready", "error": "--session required"})
        return
    doc_type = getattr(args, "doc_type", None)
    tool_args = ["next-action", "--session", sid]
    if doc_type:
        tool_args += ["--doc-type", doc_type]
    r = _run_tool(tool_args)
    rg = r.get("render_gate", {})
    ready = rg.get("can_render", False)
    _emit({
        "success": r.get("success", False),
        "command": "ready",
        "session_id": sid,
        "ready": ready,
        "render_gate": rg,
        "next_action": r.get("next_action"),
        "message": rg.get("reason", "") if ready else f"Not ready: {rg.get('reason', '')}",
        "error": r.get("error"),
    })


def cmd_summary(args: argparse.Namespace) -> None:
    """Produce a compact user-facing session summary."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "summary", "error": "--session required"})
        return
    r = _run_tool(["status", "--session", sid])
    payload = r.get("payload", {}) or {}
    v_summary = r.get("validation_summary", {}) or {}
    w_summary = r.get("warning_summary", {}) or {}

    filled_fields = [k for k, v in payload.items() if v not in (None, "", [], {})]
    missing_required = v_summary.get("missing_required", [])
    errors = v_summary.get("errors", 0)
    warnings = v_summary.get("warnings", 0)

    compact = {
        "doc_type": payload.get("doc_type", "unknown"),
        "filled_fields_count": len(filled_fields),
        "missing_required_count": len(missing_required),
        "errors": errors,
        "warnings": warnings,
        "draft_final_status": payload.get("draft_final_status", "draft"),
        "filled_fields": filled_fields,
        "missing_required": missing_required,
    }

    _emit({
        "success": r.get("success", False),
        "command": "summary",
        "session_id": sid,
        "compact": compact,
        "payload": payload,
        "validation_summary": v_summary,
        "warning_summary": w_summary,
        "message": f"Session {sid}: {len(filled_fields)} fields filled, {len(missing_required)} required missing, {errors} errors, {warnings} warnings.",
        "error": r.get("error"),
    })


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes Session Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("new", help="Create a new session")

    resume_p = subparsers.add_parser("resume", help="Resume an existing session")
    resume_p.add_argument("--session", required=True)

    say_p = subparsers.add_parser("say", help="Ingest user text into a session")
    say_p.add_argument("--session", required=True)
    say_p.add_argument("--text", required=True)

    next_p = subparsers.add_parser("next", help="Show the current next action")
    next_p.add_argument("--session", required=True)
    next_p.add_argument("--doc-type", default=None)

    answer_p = subparsers.add_parser("answer", help="Apply a user answer to a field")
    answer_p.add_argument("--session", required=True)
    answer_p.add_argument("--field", required=True)
    answer_p.add_argument("--value", required=True)

    ready_p = subparsers.add_parser("ready", help="Show whether session is ready for finalize/render")
    ready_p.add_argument("--session", required=True)
    ready_p.add_argument("--doc-type", default=None)

    summary_p = subparsers.add_parser("summary", help="Produce a compact session summary")
    summary_p.add_argument("--session", required=True)

    args = parser.parse_args(argv)

    handlers: dict[str, Any] = {
        "new": cmd_new,
        "resume": cmd_resume,
        "say": cmd_say,
        "next": cmd_next,
        "answer": cmd_answer,
        "ready": cmd_ready,
        "summary": cmd_summary,
    }

    try:
        handlers[args.command](args)
    except Exception as exc:
        _emit({
            "success": False,
            "command": getattr(args, "command", "unknown"),
            "session_id": getattr(args, "session", None),
            "error": str(exc),
        })
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
