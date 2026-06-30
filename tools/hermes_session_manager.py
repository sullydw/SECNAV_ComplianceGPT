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

_VERSION = "L.30B"

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
    """Show whether the session is ready for validate/finalize/render.
    Surfaces approval-gated readiness separately from validation readiness."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "ready", "error": "--session required"})
        return
    # Validation readiness from next-action
    doc_type = getattr(args, "doc_type", None)
    tool_args = ["next-action", "--session", sid]
    if doc_type:
        tool_args += ["--doc-type", doc_type]
    r = _run_tool(tool_args)
    rg = r.get("render_gate", {})
    validation_ready = rg.get("can_render", False)
    # Approval state from status
    s = _run_tool(["status", "--session", sid])
    approval = s.get("approval") or {}
    approval_current = approval.get("approval_current", False)
    approved_ready = validation_ready and approval_current
    _emit({
        "success": r.get("success", False),
        "command": "ready",
        "session_id": sid,
        "ready": approved_ready,
        "approved_ready": approved_ready,
        "validation_ready": validation_ready,
        "approval": approval,
        "approval_gate": {"approval_current": approval_current, "passed": approval_current},
        "approval_required": True,
        "render_gate": rg,
        "next_action": r.get("next_action"),
        "message": (
            "Validation and approval both ready." if approved_ready
            else ("Validation ready, but draft is not approved yet." if validation_ready
            else f"Not ready: {rg.get('reason', '')}")
        ),
        "error": r.get("error"),
    })


def cmd_finalize(args: argparse.Namespace) -> None:
    """Finalize a session via hermes_secnav_tool.py finalize."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "finalize", "error": "--session required"})
        return
    tool_args = ["finalize", "--session", sid]
    if getattr(args, "accept_warnings", False):
        tool_args.append("--accept-warnings")
    r = _run_tool(tool_args)
    _emit({
        "success": r.get("success", False),
        "command": "finalize",
        "session_id": sid,
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "findings": r.get("findings"),
        "approval": r.get("approval"),
        "approval_gate": r.get("approval_gate"),
        "message": f"Finalized session {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_render(args: argparse.Namespace) -> None:
    """Render a session via hermes_secnav_tool.py render."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "render", "error": "--session required"})
        return
    r = _run_tool(["render", "--session", sid, "--out", args.out])
    _emit({
        "success": r.get("success", False),
        "command": "render",
        "session_id": sid,
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "findings": r.get("findings"),
        "pdf_path": r.get("pdf_path"),
        "payload_json_path": r.get("payload_json_path"),
        "approval": r.get("approval"),
        "approval_gate": r.get("approval_gate"),
        "message": f"Rendered session {sid} to {r.get('pdf_path')}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_candidate_add(args: argparse.Namespace) -> None:
    """Record a candidate via candidate-add."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "candidate-add", "error": "--session required"})
        return
    r = _run_tool(["candidate-add", "--session", sid, "--json", args.json])
    _emit({
        "success": r.get("success", False),
        "command": "candidate-add",
        "session_id": sid,
        "candidate_id": r.get("candidate_id"),
        "message": f"Candidate recorded in {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_candidates(args: argparse.Namespace) -> None:
    """List all candidates via candidates."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "candidates", "error": "--session required"})
        return
    r = _run_tool(["candidates", "--session", sid])
    _emit({
        "success": r.get("success", False),
        "command": "candidates",
        "session_id": sid,
        "candidates": r.get("candidates", []),
        "message": f"Listed candidates for {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_candidate_confirm(args: argparse.Namespace) -> None:
    """Confirm and apply a candidate via candidate-confirm."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "candidate-confirm", "error": "--session required"})
        return
    r = _run_tool(["candidate-confirm", "--session", sid, "--candidate-id", args.candidate_id])
    _emit({
        "success": r.get("success", False),
        "command": "candidate-confirm",
        "session_id": sid,
        "candidate_id": args.candidate_id,
        "message": f"Confirmed candidate {args.candidate_id} in {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_candidate_reject(args: argparse.Namespace) -> None:
    """Reject a candidate via candidate-reject."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "candidate-reject", "error": "--session required"})
        return
    tool_args = ["candidate-reject", "--session", sid, "--candidate-id", args.candidate_id]
    if getattr(args, "reason", None):
        tool_args += ["--reason", args.reason]
    r = _run_tool(tool_args)
    _emit({
        "success": r.get("success", False),
        "command": "candidate-reject",
        "session_id": sid,
        "candidate_id": args.candidate_id,
        "message": f"Rejected candidate {args.candidate_id} in {sid}" if r.get("success") else r.get("error"),
        "error": r.get("error"),
    })


def cmd_apply_resolved(args: argparse.Namespace) -> None:
    """Record/confirm a resolved candidate via apply-resolved."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "apply-resolved", "error": "--session required"})
        return
    tool_args = ["apply-resolved", "--session", sid, "--json", args.json]
    if getattr(args, "confirm", False):
        tool_args.append("--confirm")
    if getattr(args, "dry_run", False):
        tool_args.append("--dry-run")
    r = _run_tool(tool_args)
    msg = f"Resolved candidate applied in {sid}" if r.get("applied") else (
        f"Dry-run preview for {sid}" if getattr(args, "dry_run", False) else r.get("error")
    )
    _emit({
        "success": r.get("success", False),
        "command": "apply-resolved",
        "session_id": sid,
        "candidate_id": r.get("candidate_id"),
        "payload": r.get("payload"),
        "preview": r.get("preview"),
        "applied": r.get("applied"),
        "applied_fields": r.get("applied_fields"),
        "message": msg,
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


def cmd_preview(args: argparse.Namespace) -> None:
    """Show read-only preview (build_status or draft_preview) via hermes_secnav_tool.py preview."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "preview", "error": "--session required"})
        return
    r = _run_tool(["preview", "--session", sid])
    _emit({
        "success": r.get("success", False),
        "command": "preview",
        "session_id": sid,
        "mode": r.get("mode"),
        "preview_gate_met": r.get("preview_gate_met"),
        "preview_text": r.get("preview_text"),
        "body_review_required": r.get("body_review_required"),
        "pending_candidates": r.get("pending_candidates"),
        "confirmed_candidates": r.get("confirmed_candidates"),
        "validation_summary": r.get("validation_summary"),
        "render_gate": r.get("render_gate"),
        "next_action": r.get("next_action"),
        "approval": r.get("approval"),
        "error": r.get("error"),
    })


def cmd_approve(args: argparse.Namespace) -> None:
    """Record approval for current draft preview via hermes_secnav_tool.py approve."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "approve", "error": "--session required"})
        return
    r = _run_tool(["approve", "--session", sid])
    _emit({
        "success": r.get("success", False),
        "command": "approve",
        "session_id": sid,
        "approved_for_finalize": r.get("approved_for_finalize"),
        "approved_at": r.get("approved_at"),
        "approved_preview_hash": r.get("approved_preview_hash"),
        "current_preview_hash": r.get("current_preview_hash"),
        "approval_current": r.get("approval_current"),
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
        "error": r.get("error"),
    })


def cmd_revise(args: argparse.Namespace) -> None:
    """Controlled revision of draft content via hermes_secnav_tool.py revise."""
    sid = _session_id_from_args(args)
    if not sid:
        _emit({"success": False, "command": "revise", "error": "--session required"})
        return
    text = getattr(args, "text", "")
    r = _run_tool(["revise", "--session", sid, "--text", text])
    _emit({
        "success": r.get("success", False),
        "command": "revise",
        "session_id": sid,
        "proposed_kv": r.get("proposed_kv"),
        "applied_answers": r.get("applied_answers"),
        "preview_hash_before": r.get("preview_hash_before"),
        "preview_hash_after": r.get("preview_hash_after"),
        "payload_changed": r.get("payload_changed"),
        "approval_cleared": r.get("approval_cleared"),
        "approval": r.get("approval"),
        "payload": r.get("payload"),
        "validation_summary": r.get("validation_summary"),
        "warning_summary": r.get("warning_summary"),
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

    finalize_p = subparsers.add_parser("finalize", help="Finalize a session")
    finalize_p.add_argument("--session", required=True)
    finalize_p.add_argument("--accept-warnings", action="store_true")

    render_p = subparsers.add_parser("render", help="Render a finalized session")
    render_p.add_argument("--session", required=True)
    render_p.add_argument("--out", required=True)

    summary_p = subparsers.add_parser("summary", help="Produce a compact session summary")
    summary_p.add_argument("--session", required=True)

    candidate_add_p = subparsers.add_parser("candidate-add", help="Record a candidate (pending)")
    candidate_add_p.add_argument("--session", required=True)
    candidate_add_p.add_argument("--json", required=True, help="Path to candidate JSON file")

    candidates_p = subparsers.add_parser("candidates", help="List all candidates")
    candidates_p.add_argument("--session", required=True)

    candidate_confirm_p = subparsers.add_parser("candidate-confirm", help="Confirm and apply a candidate")
    candidate_confirm_p.add_argument("--session", required=True)
    candidate_confirm_p.add_argument("--candidate-id", required=True)

    candidate_reject_p = subparsers.add_parser("candidate-reject", help="Reject a candidate")
    candidate_reject_p.add_argument("--session", required=True)
    candidate_reject_p.add_argument("--candidate-id", required=True)
    candidate_reject_p.add_argument("--reason", default=None)

    apply_resolved_p = subparsers.add_parser("apply-resolved", help="Record/confirm a resolved candidate")
    apply_resolved_p.add_argument("--session", required=True)
    apply_resolved_p.add_argument("--json", required=True, help="Path to candidate JSON file")
    apply_resolved_p.add_argument("--confirm", action="store_true")
    apply_resolved_p.add_argument("--dry-run", action="store_true")

    summary_p = subparsers.add_parser("summary", help="Produce a compact session summary")
    summary_p.add_argument("--session", required=True)

    preview_p = subparsers.add_parser("preview", help="Read-only preview of session state")
    preview_p.add_argument("--session", required=True)

    approve_p = subparsers.add_parser("approve", help="Approve current draft preview for finalize")
    approve_p.add_argument("--session", required=True)

    revise_p = subparsers.add_parser("revise", help="Controlled revision of draft content")
    revise_p.add_argument("--session", required=True)
    revise_p.add_argument("--text", required=True, help="Revision text (e.g. body: New text)")

    args = parser.parse_args(argv)

    handlers: dict[str, Any] = {
        "new": cmd_new,
        "resume": cmd_resume,
        "say": cmd_say,
        "next": cmd_next,
        "answer": cmd_answer,
        "ready": cmd_ready,
        "finalize": cmd_finalize,
        "render": cmd_render,
        "summary": cmd_summary,
        "preview": cmd_preview,
        "approve": cmd_approve,
        "revise": cmd_revise,
        "candidate-add": cmd_candidate_add,
        "candidates": cmd_candidates,
        "candidate-confirm": cmd_candidate_confirm,
        "candidate-reject": cmd_candidate_reject,
        "apply-resolved": cmd_apply_resolved,
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
