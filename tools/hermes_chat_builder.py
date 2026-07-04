#!/usr/bin/env python3
r"""
Hermes Chat Builder — Phase L.30S

Conversational orchestration layer over hermes_session_manager.py.
User chats naturally; the chat builder routes to safe wrapper commands
behind the scenes.

Run under the project venv:
    venv\Scripts\python tools\hermes_chat_builder.py <command>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_VENV_PYTHON = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
_FALLBACK_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_PYTHON = _VENV_PYTHON if _VENV_PYTHON.exists() else _FALLBACK_PYTHON
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"

_STATE_DIR = Path.home() / ".hermes" / "secnav_sessions" / "chat_builder_state"
_STATE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _state_path(chat_id: str) -> Path:
    safe = "".join(c for c in chat_id if c.isalnum() or c in "-_")
    return _STATE_DIR / f"{safe}.json"


def _load_state(chat_id: str) -> dict[str, Any]:
    path = _state_path(chat_id)
    if not path.exists():
        raise FileNotFoundError(f"Chat not found: {chat_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(chat_id: str, data: dict[str, Any]) -> None:
    _state_path(chat_id).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _run_manager(args: list[str]) -> dict[str, Any]:
    """Run hermes_session_manager.py via subprocess and parse JSON stdout."""
    proc = subprocess.run(
        [str(_PYTHON), str(_MANAGER)] + args,
        capture_output=True,
        text=True,
        timeout=120,
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


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

_NEW_INTENTS = {
    "new letter", "create a", "create letter", "draft a", "draft letter",
    "need a letter", "i need a", "start a letter", "write a letter",
    "generate a letter", "prepare a letter", "compose a letter",
}

_REVISE_INTENTS = {
    "revise", "edit", "change the", "change signer", "change subject",
    "make the body", "make body", "shorten", "remove", "add paragraph",
    "update the", "rewrite", "reword", "fix the", "correct the",
    "more formal", "less formal", "change date", "change to",
}

_APPROVE_INTENTS = {
    "approve", "looks good", "looks great", "approved", "good to go",
    "i approve", "sign off", "signed off", "confirm draft", "accept draft",
    "it is good", "it's good", "that works", "this works", "proceed",
}

_RENDER_INTENTS = {
    "make pdf", "make the pdf", "render", "finalize", "export",
    "create pdf", "generate pdf", "output pdf", "produce pdf",
    "pdf please", "pdf now", "export pdf", "save pdf",
}

_PREVIEW_INTENTS = {
    "show me", "view draft", "what does it look like", "current draft",
    "show draft", "preview",
}

_STATUS_INTENTS = {
    "status", "where are we", "what is the status",
    "current status", "are we ready", "check status", "progress",
}


def _classify_intent(text: str) -> str:
    t = text.lower().strip()
    # Check render first (it may overlap with approve)
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _RENDER_INTENTS):
        return "render"
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _APPROVE_INTENTS):
        return "approve"
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _REVISE_INTENTS):
        return "revise"
    # New creation patterns should win over preview/status
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _NEW_INTENTS):
        return "new"
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _PREVIEW_INTENTS):
        return "preview"
    if any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in _STATUS_INTENTS):
        return "status"
    return "say"


# ---------------------------------------------------------------------------
# Phase determination
# ---------------------------------------------------------------------------


def _determine_phase(ready_result: dict[str, Any], preview_result: dict[str, Any]) -> str:
    """Return one of: build_status, draft_preview, approved_ready, rendered, blocked."""
    if ready_result.get("approved_ready"):
        return "approved_ready"
    mode = preview_result.get("mode")
    if mode == "draft_preview":
        return "draft_preview"
    if mode == "build_status":
        return "build_status"
    if ready_result.get("validation_ready") and not ready_result.get("approved_ready"):
        return "draft_preview"  # validation ready but not approved
    return "build_status"


def _build_next_step(phase: str, ready_result: dict[str, Any], preview_result: dict[str, Any]) -> str:
    if phase == "approved_ready":
        return "Draft is approved and ready. Say 'make the PDF' to render."
    if phase == "draft_preview":
        approval = preview_result.get("approval") or {}
        if approval.get("approval_current"):
            return "Draft preview is ready and approved. Running ready now will show approved_ready."
        return "Draft preview is ready. Review it and say 'looks good' to approve."
    rg = ready_result.get("render_gate", {})
    missing = rg.get("missing", [])
    if missing:
        return f"Still building. Missing: {', '.join(missing[:5])}. Provide the missing details."
    return "Keep providing details to complete the letter."


def _build_assistant_response(
    phase: str,
    ready_result: dict[str, Any],
    preview_result: dict[str, Any],
    *,
    action: str = "",
    cleared: bool = False,
    pdf_path: str = "",
    blocked_reason: str = "",
) -> str:
    """Return plain-English text for the user."""
    if phase == "rendered":
        return (
            f"Done! Your PDF is ready at {pdf_path}. "
            "You can start a new chat if you need another letter."
        )

    if phase == "approved_ready":
        return (
            "Your draft is approved and everything looks good. "
            "When you're ready, just say 'make the PDF' and I'll generate it for you."
        )

    if phase == "draft_preview":
        approval = (preview_result.get("approval") or {}).get("approval_current", False)
        if approval:
            return (
                "Your draft is ready and already approved. "
                "You can ask me to make the PDF whenever you like."
            )
        return (
            "Your draft is ready for review. "
            "You can say 'looks good' to approve it, or tell me what you'd like to change."
        )

    if phase == "blocked" and action == "render":
        if blocked_reason:
            return (
                f"I can't make the PDF yet. {blocked_reason} "
                "Please review the draft, make any changes you need, and say 'looks good' to approve it first."
            )
        return (
            "I can't make the PDF yet. The draft needs to be approved and all required fields must be ready. "
            "Please review the draft and say 'looks good' to approve it first."
        )

    if action == "revise" and cleared:
        return (
            "I've updated the draft. Since I made a change, approval was cleared. "
            "Please review the updated preview and say 'looks good' when you're ready to approve again."
        )

    if action == "revise":
        return (
            "I've updated the draft. Please review the preview and let me know if it looks good or if you'd like more changes."
        )

    if action == "approve":
        return (
            "Your draft is approved! "
            "You can now ask me to make the PDF when you're ready."
        )

    rg = ready_result.get("render_gate", {})
    missing = rg.get("missing", [])
    next_action = ready_result.get("next_action", {})
    if missing:
        return (
            f"Your draft isn't ready yet. I'm still missing: {', '.join(missing[:5])}. "
            "You can provide the next detail, or say 'show me the preview' to see what's ready so far."
        )

    if next_action and next_action.get("field"):
        field = next_action["field"]
        question = next_action.get("question", f"Please provide {field}.")
        return (
            f"Your draft isn't ready yet. I'm still missing {field}. "
            f"{question} "
            "You can provide the next detail, or say 'show me the preview' to see what's ready so far."
        )

    return (
        "Got it. Keep providing details and I'll build the draft for you. "
        "Say 'show me the preview' anytime to check progress."
    )


# ---------------------------------------------------------------------------
# Chat action handlers
# ---------------------------------------------------------------------------


def _run_say_and_status(session_id: str, text: str) -> dict[str, Any]:
    """Run say, then preview + ready to build a user-facing response."""
    say_r = _run_manager(["say", "--session", session_id, "--text", text])
    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])

    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    assistant_response = _build_assistant_response(phase, ready_r, preview_r)

    return {
        "success": say_r.get("success", False),
        "intent": "say",
        "phase": phase,
        "message": (
            f"I've noted that. Current phase: {phase.replace('_', ' ')}. {next_step}"
            if say_r.get("success")
            else say_r.get("error", "Say failed")
        ),
        "assistant_response": assistant_response,
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "payload": say_r.get("payload"),
        "validation_summary": say_r.get("validation_summary"),
        "warning_summary": say_r.get("warning_summary"),
        "proposed_kv": say_r.get("proposed_kv"),
        "error": say_r.get("error"),
    }


def _run_revise_and_status(session_id: str, text: str) -> dict[str, Any]:
    """Run revise, then preview + ready."""
    revise_r = _run_manager(["revise", "--session", session_id, "--text", text])
    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])

    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    cleared = revise_r.get("approval_cleared", False)
    changed = revise_r.get("payload_changed", False)
    # Chat layer always tells the user approval was cleared on any revision
    assistant_response = (
        "I've updated the draft. Since I made a change, approval was cleared. "
        "Please review the updated preview and say 'looks good' when you're ready to approve again."
    )

    return {
        "success": revise_r.get("success", False),
        "intent": "revise",
        "phase": phase,
        "message": (
            f"Revised draft. Payload changed: {changed}. Approval cleared: {cleared}. "
            f"Current phase: {phase.replace('_', ' ')}. {next_step}"
            if revise_r.get("success")
            else revise_r.get("error", "Revise failed")
        ),
        "assistant_response": assistant_response,
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "payload": revise_r.get("payload"),
        "validation_summary": revise_r.get("validation_summary"),
        "warning_summary": revise_r.get("warning_summary"),
        "approval_cleared": True,
        "payload_changed": changed,
        "error": revise_r.get("error"),
    }


def _run_approve_and_status(session_id: str) -> dict[str, Any]:
    """Run approve, then ready to build response."""
    approve_r = _run_manager(["approve", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])

    approved = approve_r.get("approved_for_finalize", False)
    approved_ready = ready_r.get("approved_ready", False)

    if approved and approved_ready:
        phase = "approved_ready"
        next_step = "Draft is approved and ready. Say 'make the PDF' to render."
    elif approved:
        phase = "draft_preview"
        next_step = "Draft approved, but validation is not yet ready. Provide missing fields."
    else:
        phase = "blocked"
        next_step = approve_r.get("error", "Approval failed. Ensure preview gate is met first.")

    assistant_response = _build_assistant_response(
        phase, ready_r, {}, action="approve", blocked_reason=next_step if phase == "blocked" else ""
    )

    return {
        "success": approve_r.get("success", False),
        "intent": "approve",
        "phase": phase,
        "message": (
            f"Draft approved. Current phase: {phase.replace('_', ' ')}. {next_step}"
            if approved
            else next_step
        ),
        "assistant_response": assistant_response,
        "next_step": next_step,
        "approved_for_finalize": approved,
        "approved_ready": approved_ready,
        "approval": approve_r.get("approval"),
        "error": approve_r.get("error"),
    }


def _run_preview_status(session_id: str) -> dict[str, Any]:
    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])

    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    assistant_response = _build_assistant_response(phase, ready_r, preview_r)

    return {
        "success": preview_r.get("success", False),
        "intent": "preview",
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "assistant_response": assistant_response,
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "mode": preview_r.get("mode"),
        "approval": preview_r.get("approval"),
        "error": preview_r.get("error"),
    }


def _run_ready_status(session_id: str) -> dict[str, Any]:
    ready_r = _run_manager(["ready", "--session", session_id])
    preview_r = _run_manager(["preview", "--session", session_id])

    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    assistant_response = _build_assistant_response(phase, ready_r, preview_r)

    return {
        "success": ready_r.get("success", False),
        "intent": "ready",
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "assistant_response": assistant_response,
        "approved_ready": ready_r.get("approved_ready", False),
        "validation_ready": ready_r.get("validation_ready", False),
        "next_step": next_step,
        "approval": ready_r.get("approval"),
        "render_gate": ready_r.get("render_gate"),
        "error": ready_r.get("error"),
    }


def _run_render_gate(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """Check ready, then render if gates pass."""
    ready_r = _run_manager(["ready", "--session", session_id])
    approved_ready = ready_r.get("approved_ready", False)

    if not approved_ready:
        phase = _determine_phase(ready_r, {"mode": "build_status"})
        next_step = _build_next_step(phase, ready_r, {"mode": "build_status"})
        assistant_response = _build_assistant_response(
            "blocked", ready_r, {}, action="render",
            blocked_reason=ready_r.get("error") or "The draft isn't approved or validation isn't ready yet."
        )
        return {
            "success": False,
            "intent": "render",
            "phase": phase,
            "message": f"Cannot render yet. Current phase: {phase.replace('_', ' ')}. {next_step}",
            "assistant_response": assistant_response,
            "next_step": next_step,
            "approved_ready": False,
            "validation_ready": ready_r.get("validation_ready", False),
            "error": ready_r.get("error") or "Render blocked: not approved_ready.",
        }

    # Determine output path
    out_dir = _REPO_ROOT / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    user_out = state.get("out_path")
    pdf_path = Path(user_out) if user_out else out_dir / f"chat_{session_id}.pdf"

    render_r = _run_manager(["render", "--session", session_id, "--out", str(pdf_path)])
    if render_r.get("success") and pdf_path.exists() and pdf_path.stat().st_size > 0:
        state["last_pdf_path"] = str(pdf_path)
        state["rendered_at"] = render_r.get("message", "")
        _save_state(state["chat_id"], state)
        assistant_response = _build_assistant_response(
            "rendered", {}, {}, pdf_path=str(pdf_path)
        )
        return {
            "success": True,
            "intent": "render",
            "phase": "rendered",
            "message": f"PDF rendered successfully: {pdf_path}",
            "assistant_response": assistant_response,
            "pdf_path": str(pdf_path),
            "pdf_size": pdf_path.stat().st_size,
            "next_step": "Letter is complete. You can start a new chat for another letter.",
            "error": None,
        }
    else:
        assistant_response = _build_assistant_response(
            "blocked", {}, {}, action="render",
            blocked_reason=render_r.get("error") or "Render failed."
        )
        return {
            "success": False,
            "intent": "render",
            "phase": "blocked",
            "message": render_r.get("error", "Render failed."),
            "assistant_response": assistant_response,
            "next_step": "Check status and ensure draft is approved and validation is ready.",
            "error": render_r.get("error", "Render failed."),
        }


# ---------------------------------------------------------------------------
# CLI command handlers
# ---------------------------------------------------------------------------


def cmd_start(_args: argparse.Namespace) -> None:
    """Create a new chat and a new underlying session."""
    r = _run_manager(["new"])
    if not r.get("success"):
        _emit({
            "success": False,
            "command": "start",
            "message": f"Failed to create session: {r.get('error')}",
            "error": r.get("error"),
        })
        return

    session_id = r["session_id"]
    chat_id = f"chat-{uuid.uuid4().hex[:12]}"
    state = {
        "chat_id": chat_id,
        "session_id": session_id,
        "created_at": r.get("message", ""),
        "history": [],
        "last_pdf_path": None,
        "rendered_at": None,
    }
    _save_state(chat_id, state)

    _emit({
        "success": True,
        "command": "start",
        "chat_id": chat_id,
        "session_id": session_id,
        "message": f"Chat started. Use --chat-id {chat_id} for follow-up messages.",
        "next_step": "Tell me what letter you need.",
        "error": None,
    })


def _process_turn(chat_id: str, text: str, state: dict[str, Any]) -> dict[str, Any]:
    """Process one chat turn and return the result dict."""
    session_id = state["session_id"]
    intent = _classify_intent(text)

    state["history"].append({"role": "user", "text": text, "intent": intent})
    if len(state["history"]) > 20:
        state["history"] = state["history"][-20:]

    result: dict[str, Any]
    if intent == "revise":
        result = _run_revise_and_status(session_id, text)
    elif intent == "approve":
        result = _run_approve_and_status(session_id)
    elif intent == "preview":
        result = _run_preview_status(session_id)
    elif intent == "status":
        result = _run_ready_status(session_id)
    elif intent == "render":
        result = _run_render_gate(session_id, state)
    else:
        result = _run_say_and_status(session_id, text)

    state["history"].append({
        "role": "assistant",
        "phase": result.get("phase"),
        "message": result.get("message"),
    })
    _save_state(chat_id, state)
    return result


def cmd_chat(args: argparse.Namespace) -> None:
    """Process a natural-language chat turn."""
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        _emit({"success": False, "command": "chat", "error": "--chat-id required"})
        return

    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        _emit({"success": False, "command": "chat", "error": str(exc)})
        return

    text = getattr(args, "text", "")
    result = _process_turn(chat_id, text, state)

    _emit({
        "success": result.get("success", False),
        "command": "chat",
        "chat_id": chat_id,
        "session_id": state["session_id"],
        "intent": result.get("intent"),
        "phase": result.get("phase"),
        "message": result.get("message"),
        "assistant_response": result.get("assistant_response"),
        "preview_text": result.get("preview_text"),
        "next_step": result.get("next_step"),
        "pdf_path": result.get("pdf_path"),
        "pdf_size": result.get("pdf_size"),
        "payload_changed": result.get("payload_changed"),
        "approval_cleared": result.get("approval_cleared"),
        "error": result.get("error"),
    })


def cmd_status(args: argparse.Namespace) -> None:
    """Show current chat phase, session status, and next step."""
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        _emit({"success": False, "command": "status", "error": "--chat-id required"})
        return

    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        _emit({"success": False, "command": "status", "error": str(exc)})
        return

    session_id = state["session_id"]
    ready_r = _run_manager(["ready", "--session", session_id])
    preview_r = _run_manager(["preview", "--session", session_id])

    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)

    _emit({
        "success": True,
        "command": "status",
        "chat_id": chat_id,
        "session_id": session_id,
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "approved_ready": ready_r.get("approved_ready", False),
        "validation_ready": ready_r.get("validation_ready", False),
        "last_pdf_path": state.get("last_pdf_path"),
        "history_count": len(state.get("history", [])),
        "error": None,
    })


def cmd_reset(args: argparse.Namespace) -> None:
    """Reset chat state and start a fresh session for the same chat_id."""
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        _emit({"success": False, "command": "reset", "error": "--chat-id required"})
        return

    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        _emit({"success": False, "command": "reset", "error": str(exc)})
        return

    # Create new session
    r = _run_manager(["new"])
    if not r.get("success"):
        _emit({
            "success": False,
            "command": "reset",
            "error": f"Failed to create new session: {r.get('error')}",
        })
        return

    new_session_id = r["session_id"]
    state["session_id"] = new_session_id
    state["history"] = []
    state["last_pdf_path"] = None
    state["rendered_at"] = None
    _save_state(chat_id, state)

    _emit({
        "success": True,
        "command": "reset",
        "chat_id": chat_id,
        "session_id": new_session_id,
        "message": f"Chat reset with new session {new_session_id}.",
        "next_step": "Tell me what letter you need.",
        "error": None,
    })


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------


_EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}


def cmd_interactive(args: argparse.Namespace) -> None:
    """Run an interactive chat loop. Creates a session if --chat-id is omitted."""
    chat_id = getattr(args, "chat_id", None)
    out_path = getattr(args, "out", "")
    json_lines = getattr(args, "json_lines", False)

    if chat_id:
        try:
            state = _load_state(chat_id)
        except FileNotFoundError:
            _emit({"success": False, "command": "interactive", "error": f"Chat not found: {chat_id}"})
            return
    else:
        # auto-create
        r = _run_manager(["new"])
        if not r.get("success"):
            _emit({"success": False, "command": "interactive", "error": f"Failed to create session: {r.get('error')}"})
            return
        session_id = r["session_id"]
        chat_id = f"chat-{uuid.uuid4().hex[:12]}"
        state = {
            "chat_id": chat_id,
            "session_id": session_id,
            "created_at": r.get("message", ""),
            "history": [],
            "last_pdf_path": None,
            "rendered_at": None,
        }
        if out_path:
            state["out_path"] = str(out_path)
        _save_state(chat_id, state)
        _emit({"success": True, "command": "interactive", "chat_id": chat_id, "session_id": session_id,
               "message": "Chat started. Type your message (or 'exit' to quit).", "error": None})
        print("\n" + _build_assistant_response("build_status", {}, {}), flush=True)

    state = _load_state(chat_id)

    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        if text.lower() in _EXIT_COMMANDS:
            _emit({"success": True, "command": "interactive", "chat_id": chat_id,
                   "message": "Goodbye.", "error": None})
            break

        result = _process_turn(chat_id, text, state)

        if json_lines:
            print(json.dumps(result, indent=2, default=str), flush=True)
        else:
            print(result.get("assistant_response", result.get("message", "")), flush=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes Chat Builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("start", help="Create a new chat session")

    chat_p = subparsers.add_parser("chat", help="Send a natural-language message")
    chat_p.add_argument("--chat-id", required=True)
    chat_p.add_argument("--text", required=True)

    status_p = subparsers.add_parser("status", help="Show current chat status")
    status_p.add_argument("--chat-id", required=True)

    reset_p = subparsers.add_parser("reset", help="Reset chat and start a new session")
    reset_p.add_argument("--chat-id", required=True)

    interactive_p = subparsers.add_parser("interactive", help="Start an interactive chat loop")
    interactive_p.add_argument("--chat-id", default=None, help="Existing chat ID (auto-creates if omitted)")
    interactive_p.add_argument("--out", default=None, help="Optional output PDF path")
    interactive_p.add_argument("--json-lines", action="store_true", help="Emit JSON per turn instead of plain text")

    args = parser.parse_args(argv)

    handlers: dict[str, Any] = {
        "start": cmd_start,
        "chat": cmd_chat,
        "status": cmd_status,
        "reset": cmd_reset,
        "interactive": cmd_interactive,
    }

    try:
        handlers[args.command](args)
    except Exception as exc:
        _emit({
            "success": False,
            "command": getattr(args, "command", "unknown"),
            "chat_id": getattr(args, "chat_id", None),
            "error": str(exc),
        })
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
