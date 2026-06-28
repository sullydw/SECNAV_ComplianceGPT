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
from unresolved_fact_detector import detect_unresolved_facts

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSION_DIR = Path.home() / ".hermes" / "secnav_sessions"
_SESSION_DIR.mkdir(parents=True, exist_ok=True)

_VERSION = "L.29C"

_ALLOWED_CANDIDATE_TYPES = {
    "command_expansion",
    "unit_identity",
    "ssic_candidate",
    "routing_interpretation",
    "signature_block",
    "date_confirmation",
    "subject_draft",
    "body_draft",
}

# Unsafe payload keys that candidates must never set directly
_UNSAFE_PAYLOAD_KEYS = {
    "cci_severity",
    "cci_config",
    "rule_promotion",
    "severity_override",
    "renderer_directive",
    "layout_override",
    "pdf_engine",
    "font_settings",
    "page_margins",
    "header_format",
    "footer_format",
}

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

    # Restore approval state (L.30K-2)
    builder._approved_for_finalize = data.get("approved_for_finalize", False)
    builder._approved_at = data.get("approved_at")
    builder._approved_preview_hash = data.get("approved_preview_hash")

    # Restore candidates (L.29C)
    candidates_data = data.get("candidates")
    if candidates_data:
        builder._candidates = {
            "pending": {c["candidate_id"]: c for c in candidates_data.get("pending", [])},
            "confirmed": {c["candidate_id"]: c for c in candidates_data.get("confirmed", [])},
            "rejected": {c["candidate_id"]: c for c in candidates_data.get("rejected", [])},
        }

    return builder


def _save_session(builder: BuilderSession) -> None:
    payload = builder.build_payload()
    # Persist user_answers so future loads are editable (override works)
    user_answers = getattr(getattr(builder, "_orchestrator", None), "_user_answers", payload)

    # Serialize candidates (L.29C)
    candidates_data = {}
    if hasattr(builder, "_candidates"):
        candidates_data = {
            "pending": list(builder._candidates.get("pending", {}).values()),
            "confirmed": list(builder._candidates.get("confirmed", {}).values()),
            "rejected": list(builder._candidates.get("rejected", {}).values()),
        }

    data = {
        "version": _VERSION,
        "saved_at": datetime.now().isoformat(),
        "session_id": builder._session_id,
        "payload": payload,
        "user_answers": user_answers,
        "draft_final_status": builder._draft_final_status,
        "user_decisions": getattr(builder, "_user_decisions", {}),
        "candidates": candidates_data,
        # Approval state (L.30K-2)
        "approved_for_finalize": getattr(builder, "_approved_for_finalize", False),
        "approved_at": getattr(builder, "_approved_at", None),
        "approved_preview_hash": getattr(builder, "_approved_preview_hash", None),
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
# Next-action selection helper
# ---------------------------------------------------------------------------

def select_next_action(
    unresolved_facts: dict[str, Any],
    validation_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the next recommended action from unresolved facts.

    Deterministic, testable, read-only helper.
    Returns a dict matching the NEXT_ACTION_V1 shape.
    """
    summary = unresolved_facts.get("summary", {})
    facts = unresolved_facts.get("facts", [])
    val_summary = validation_summary or {}

    blocking = summary.get("blocking", 0)
    recommended = summary.get("recommended", 0)
    optional = summary.get("optional", 0)

    finalize_allowed = val_summary.get("finalize_allowed", True)
    validator_errors = val_summary.get("errors", 0)

    pri_map = {"blocking": 0, "recommended": 1, "optional": 2}

    def _sort(facts_list: list[dict]) -> list[dict]:
        return sorted(facts_list, key=lambda f: (pri_map.get(f.get("priority", ""), 9), f.get("fact_id", "")))

    if blocking > 0:
        blocking_facts = [f for f in facts if f.get("priority") == "blocking"]
        if not blocking_facts:
            return {
                "action": "blocked_by_validation",
                "priority": "ready",
                "field": None,
                "question": None,
                "rule_id": None,
                "source_file": None,
                "recommended_action": None,
                "candidate_type": None,
                "reason": f"Blocking count is {blocking} but no blocking facts found in list",
            }
        blocking_facts = _sort(blocking_facts)
        chosen = blocking_facts[0]
        action = chosen.get("recommended_action", "ask_user") or "ask_user"
        return {
            "action": action,
            "priority": "blocking",
            "field": chosen.get("field"),
            "question": chosen.get("question"),
            "rule_id": chosen.get("rule_id"),
            "source_file": chosen.get("source_file"),
            "recommended_action": action,
            "candidate_type": chosen.get("candidate_type"),
            "reason": f"blocking fact {chosen.get('fact_id')}: {chosen.get('field')}",
        }

    if validator_errors > 0:
        return {
            "action": "blocked_by_validation",
            "priority": "ready",
            "field": None,
            "question": None,
            "rule_id": None,
            "source_file": None,
            "recommended_action": None,
            "candidate_type": None,
            "reason": f"{validator_errors} validation error(s) present; cannot render",
        }

    if not finalize_allowed:
        return {
            "action": "blocked_by_validation",
            "priority": "ready",
            "field": None,
            "question": None,
            "rule_id": None,
            "source_file": None,
            "recommended_action": None,
            "candidate_type": None,
            "reason": "finalize not allowed by validation gate",
        }

    if recommended > 0:
        rec_facts = [f for f in facts if f.get("priority") == "recommended"]
        rec_facts = _sort(rec_facts)
        chosen = rec_facts[0] if rec_facts else None
        if chosen:
            action = chosen.get("recommended_action", "ask_user") or "ask_user"
            return {
                "action": action,
                "priority": "recommended",
                "field": chosen.get("field"),
                "question": chosen.get("question"),
                "rule_id": chosen.get("rule_id"),
                "source_file": chosen.get("source_file"),
                "recommended_action": action,
                "candidate_type": chosen.get("candidate_type"),
                "reason": f"recommended fact {chosen.get('fact_id')}: {chosen.get('field')}",
            }

    if optional > 0:
        opt_facts = [f for f in facts if f.get("priority") == "optional"]
        opt_facts = _sort(opt_facts)
        chosen = opt_facts[0] if opt_facts else None
        if chosen:
            return {
                "action": chosen.get("recommended_action", "leave_blank") or "leave_blank",
                "priority": "optional",
                "field": chosen.get("field"),
                "question": chosen.get("question"),
                "rule_id": chosen.get("rule_id"),
                "source_file": chosen.get("source_file"),
                "recommended_action": chosen.get("recommended_action", "leave_blank") or "leave_blank",
                "candidate_type": chosen.get("candidate_type"),
                "reason": f"optional fact {chosen.get('fact_id')}: {chosen.get('field')}",
            }

    return {
        "action": "render_ready",
        "priority": "ready",
        "field": None,
        "question": None,
        "rule_id": None,
        "source_file": None,
        "recommended_action": None,
        "candidate_type": None,
        "reason": "blocking facts resolved and validation gate passed",
    }


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_start(args: argparse.Namespace) -> None:
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


def _check_approval_gate(builder) -> tuple[bool, dict[str, Any], str | None]:
    """Return (ok, approval_state, error_message)."""
    state = builder.approval_state()
    if not state["approved_for_finalize"]:
        return False, state, "Draft preview not approved. Run 'approve' first."
    if not state["approval_current"]:
        return False, state, "Draft changed after approval. Re-run 'approve' after reviewing changes."
    return True, state, None


def cmd_finalize(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    ok, astate, err = _check_approval_gate(builder)
    if not ok:
        _emit({
            "success": False,
            "command": "finalize",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": builder.validation_summary(),
            "warning_summary": builder.warning_summary(),
            "next_question": None,
            "proposed_kv": None,
            "findings": None,
            "pdf_path": None,
            "payload_json_path": None,
            "approval": astate,
            "approval_gate": {"passed": False, "reason": err},
            "error": err,
        })
        return

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
        "approval": astate,
        "approval_gate": {"passed": True, "reason": None},
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
            "approval": builder.approval_state(),
            "approval_gate": {"passed": False, "reason": f"Cannot render: {v_summary.get('block_reason', ['validation blocked'])}"},
            "error": f"Cannot render: {v_summary.get('block_reason', ['validation blocked'])}",
        })
        return

    # Approval gate (L.30K-4)
    ok, astate, err = _check_approval_gate(builder)
    if not ok:
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
            "approval": astate,
            "approval_gate": {"passed": False, "reason": err},
            "error": err,
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
            "approval": astate,
            "approval_gate": {"passed": True, "reason": None},
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
        "approval": astate,
        "approval_gate": {"passed": True, "reason": None},
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
# Candidate commands (L.29C)
# ---------------------------------------------------------------------------


def _validate_candidate(cand: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate candidate shape and security constraints. Returns (ok, errors)."""
    errors: list[str] = []
    if not isinstance(cand, dict):
        errors.append("Candidate must be a dict.")
        return False, errors
    ctype = cand.get("candidate_type")
    if not ctype:
        errors.append("candidate_type is required.")
    elif ctype not in _ALLOWED_CANDIDATE_TYPES:
        errors.append(f"Unknown candidate_type: {ctype}.")
    if not cand.get("input_text"):
        errors.append("input_text is required.")
    resolved = cand.get("resolved_value")
    if not isinstance(resolved, dict):
        errors.append("resolved_value must be a dict.")
    else:
        # Block unsafe payload keys
        bad_keys = set(resolved.keys()) & _UNSAFE_PAYLOAD_KEYS
        if bad_keys:
            errors.append(f"Unsafe keys in resolved_value: {sorted(bad_keys)}")
    if not isinstance(cand.get("confidence", 0), (int, float)):
        errors.append("confidence must be numeric.")
    requires = cand.get("requires_user_confirmation", True)
    if requires is False:
        errors.append("requires_user_confirmation cannot be false.")
    return not bool(errors), errors


def cmd_candidate_add(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    cand_data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    ok, errors = _validate_candidate(cand_data)
    if not ok:
        _emit({
            "success": False,
            "command": "candidate-add",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": builder.validation_summary(),
            "warning_summary": builder.warning_summary(),
            "candidate_id": None,
            "candidate_status": None,
            "error": "; ".join(errors),
        })
        return
    recorded = builder.record_candidate(cand_data)
    _save_session(builder)
    _emit({
        "success": True,
        "command": "candidate-add",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "candidate_id": recorded.get("candidate_id"),
        "candidate_status": "pending",
        "error": None,
    })


def cmd_candidates(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    summary = builder.get_candidates()
    _emit({
        "success": True,
        "command": "candidates",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "candidates": summary,
        "error": None,
    })


def cmd_candidate_confirm(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    result = builder.confirm_candidate(args.candidate_id)
    _save_session(builder)
    _emit({
        "success": result.get("success", False),
        "command": "candidate-confirm",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "candidate_id": result.get("candidate_id"),
        "applied_fields": result.get("applied_fields"),
        "error": result.get("error"),
    })


def cmd_candidate_reject(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    result = builder.reject_candidate(args.candidate_id, reason=args.reason or "")
    _save_session(builder)
    _emit({
        "success": result.get("success", False),
        "command": "candidate-reject",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "candidate_id": result.get("candidate_id"),
        "error": result.get("error"),
    })


def cmd_apply_resolved(args: argparse.Namespace) -> None:
    builder = _load_session(args.session)
    cand_data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    ok, errors = _validate_candidate(cand_data)
    if not ok:
        _emit({
            "success": False,
            "command": "apply-resolved",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": builder.validation_summary(),
            "warning_summary": builder.warning_summary(),
            "preview": None,
            "applied": False,
            "candidate_id": None,
            "error": "; ".join(errors),
        })
        return

    if args.dry_run:
        # Preview only: do not store or apply
        preview = {
            "would_record": True,
            "would_apply": False,
            "candidate": cand_data,
            "dry_run": True,
        }
        _emit({
            "success": True,
            "command": "apply-resolved",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": builder.validation_summary(),
            "warning_summary": builder.warning_summary(),
            "preview": preview,
            "applied": False,
            "candidate_id": None,
            "error": None,
        })
        return

    # Record as pending first
    recorded = builder.record_candidate(cand_data)
    candidate_id = recorded["candidate_id"]

    if args.confirm:
        # Apply immediately
        result = builder.confirm_candidate(candidate_id)
        _save_session(builder)
        _emit({
            "success": result.get("success", False),
            "command": "apply-resolved",
            "session_id": args.session,
            "payload": builder.build_payload(),
            "validation_summary": builder.validation_summary(),
            "warning_summary": builder.warning_summary(),
            "preview": None,
            "applied": result.get("success", False),
            "candidate_id": candidate_id,
            "applied_fields": result.get("applied_fields"),
            "error": result.get("error"),
        })
        return

    # Without --confirm: store as pending only
    _save_session(builder)
    _emit({
        "success": True,
        "command": "apply-resolved",
        "session_id": args.session,
        "payload": builder.build_payload(),
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "preview": None,
        "applied": False,
        "candidate_id": candidate_id,
        "candidate_status": "pending",
        "error": None,
    })


def cmd_detect_facts(args: argparse.Namespace) -> None:
    """
    Run the unresolved-fact detector on the current session payload.
    Does not mutate the session, create candidates, or apply anything.
    """
    builder = _load_session(args.session)
    payload = builder.build_payload()
    user_text = args.text if args.text else None
    doc_type = args.doc_type if args.doc_type else None

    unresolved_facts = detect_unresolved_facts(
        payload=payload,
        user_text=user_text,
        doc_type=doc_type,
    )

    _emit({
        "success": True,
        "command": "detect-facts",
        "session_id": args.session,
        "payload": payload,
        "unresolved_facts": unresolved_facts,
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "error": None,
    })


def _has_usable_signature(payload: dict[str, Any]) -> bool:
    sig = payload.get("signature")
    if isinstance(sig, dict):
        return bool(sig.get("name"))
    if isinstance(sig, list) and sig:
        return bool(str(sig[0]).strip())
    if isinstance(sig, str):
        return bool(sig.strip())
    return False


def _preview_gate_met(payload: dict[str, Any]) -> bool:
    """Check if minimum fields exist for draft_preview mode."""
    required_for_preview = {"from", "to", "subj", "body", "date"}
    for field in required_for_preview:
        val = payload.get(field)
        if val in (None, "", [], {}):
            return False
    return _has_usable_signature(payload)


def _build_preview_text(payload: dict[str, Any], mode: str, v_summary: dict[str, Any],
                        candidates: dict[str, Any], next_action: dict[str, Any],
                        approval_state: dict[str, Any] | None = None) -> str:
    lines: list[str] = []
    if mode == "build_status":
        lines.append("=" * 50)
        lines.append("BUILD STATUS")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Session: {payload.get('session_id', 'N/A')}")
        lines.append(f"Status:  Incomplete — more information needed")
        lines.append("")
        known = [k for k, v in payload.items() if v not in (None, "", [], {})]
        lines.append(f"Known fields ({len(known)}): {', '.join(known) if known else 'none'}")
        missing = v_summary.get("missing_required", [])
        lines.append(f"Missing required fields ({len(missing)}): {', '.join(missing) if missing else 'none'}")
        p_count = candidates.get("counts", {}).get("pending", 0)
        c_count = candidates.get("counts", {}).get("confirmed", 0)
        lines.append(f"Pending candidates: {p_count}")
        lines.append(f"Confirmed candidates: {c_count}")
        lines.append("")
        na = next_action.get("recommended_action") or next_action.get("action")
        if na:
            lines.append(f"Next action: {na}")
        lines.append("=" * 50)
    else:
        ap = approval_state or {}
        if ap.get("approval_current"):
            lines.append("=" * 50)
            lines.append("DRAFT PREVIEW  APPROVED FOR FINALIZE")
            lines.append("=" * 50)
        else:
            lines.append("=" * 50)
            lines.append("DRAFT PREVIEW  NOT FINAL")
            lines.append("=" * 50)
        lines.append("")
        ssic = payload.get("ssic")
        lines.append(f"SSIC: {ssic if ssic else '[SSIC NEEDED]'}")
        oc = payload.get("originator_code")
        lines.append(f"Originator Code: {oc if oc else '[ORIGINATOR CODE NEEDED]'}")
        lines.append(f"Date: {payload.get('date', '[DATE NEEDED]')}")
        lines.append("")
        lines.append(f"From: {payload.get('from', '[FROM NEEDED]')}")
        lines.append(f"To:   {payload.get('to', '[TO NEEDED]')}")
        lines.append("")
        lines.append(f"Subj: {payload.get('subj', '[SUBJ NEEDED]')}")
        lines.append("")
        lines.append("-" * 50)
        lines.append("[AI-DRAFTED OR USER-PROVIDED BODY  REVIEW REQUIRED]")
        lines.append("-" * 50)
        body = payload.get("body", [])
        if isinstance(body, list):
            for para in body:
                lines.append(str(para))
                lines.append("")
        elif body:
            lines.append(str(body))
            lines.append("")
        lines.append("-" * 50)
        lines.append("")
        sig = payload.get("signature")
        if isinstance(sig, dict):
            lines.append(f"Signature: {sig.get('name', '[NAME NEEDED]')}")
            if sig.get("title"):
                lines.append(f"  Title: {sig['title']}")
            if sig.get("role"):
                lines.append(f"  Role: {sig['role']}")
        elif isinstance(sig, (list, str)):
            lines.append(f"Signature: {sig}")
        else:
            lines.append("Signature: [SIGNATURE NEEDED]")
        lines.append("")
        if ap.get("approval_current"):
            lines.append("=" * 50)
            lines.append("END DRAFT PREVIEW  APPROVED FOR FINALIZE")
            lines.append("=" * 50)
        else:
            lines.append("=" * 50)
            lines.append("END DRAFT PREVIEW  NOT FINAL")
            lines.append("=" * 50)
    return "\n".join(lines)


def cmd_preview(args: argparse.Namespace) -> None:
    """
    Read-only preview: shows BUILD STATUS when incomplete, DRAFT PREVIEW when ready.
    Does NOT save, mutate, finalize, render, or change candidates.
    """
    builder = _load_session(args.session)
    payload = builder.build_payload()
    v_summary = builder.validation_summary()
    w_summary = builder.warning_summary()
    candidates = builder.get_candidates()

    unresolved_facts = detect_unresolved_facts(
        payload=payload,
        user_text=None,
        doc_type=payload.get("doc_type"),
    )
    next_action = select_next_action(unresolved_facts, v_summary)

    # Build render gate
    blocking = unresolved_facts.get("summary", {}).get("blocking", 0)
    recommended = unresolved_facts.get("summary", {}).get("recommended", 0)
    optional = unresolved_facts.get("summary", {}).get("optional", 0)
    errors = v_summary.get("errors", 0)
    finalize_allowed = v_summary.get("finalize_allowed", True)
    blocking_resolved = blocking == 0
    can_render = blocking_resolved and errors == 0 and finalize_allowed

    if not blocking_resolved:
        rg_reason = f"{blocking} blocking fact(s) remain unresolved"
    elif errors > 0:
        rg_reason = f"{errors} validation error(s) present"
    elif not finalize_allowed:
        rg_reason = "finalize not allowed by validation gate"
    else:
        rg_reason = "blocking facts resolved and validation gate passed"

    render_gate = {
        "blocking_resolved": blocking_resolved,
        "recommended_remaining": recommended,
        "optional_remaining": optional,
        "validator_errors": errors,
        "finalize_allowed": finalize_allowed,
        "can_render": can_render,
        "reason": rg_reason,
    }

    # Determine next action recommendation
    known_fields = [k for k, v in payload.items() if v not in (None, "", [], {})]
    missing_preview = []
    for f in ("from", "to", "subj", "body", "date"):
        if payload.get(f) in (None, "", [], {}):
            missing_preview.append(f)
    if not _has_usable_signature(payload):
        missing_preview.append("signature")

    gate_met = _preview_gate_met(payload)

    if gate_met:
        approval_state = builder.approval_state()
        preview_text = _build_preview_text(payload, "draft_preview", v_summary, candidates, next_action, approval_state)
        # Recommended next action for draft_preview
        if not can_render:
            rec_next = "Fix validation errors or missing fields before proceeding."
        else:
            if approval_state.get("approval_current"):
                rec_next = "Draft preview is approved for finalize. Use finalize when ready."
            else:
                rec_next = "Review the draft preview. Use the approve command when satisfied."
        _emit({
            "success": True,
            "command": "preview",
            "session_id": args.session,
            "mode": "draft_preview",
            "preview_gate_met": True,
            "preview_text": preview_text,
            "body_review_required": True,
            "pending_candidates": candidates.get("counts", {}).get("pending", 0),
            "confirmed_candidates": candidates.get("counts", {}).get("confirmed", 0),
            "pending_candidates_list": candidates.get("pending", []),
            "confirmed_candidates_list": candidates.get("confirmed", []),
            "validation_summary": v_summary,
            "render_gate": render_gate,
            "next_action": rec_next,
            "approval": approval_state,
            "error": None,
        })
    else:
        approval_state = builder.approval_state()
        preview_text = _build_preview_text(payload, "build_status", v_summary, candidates, next_action, approval_state)
        if missing_preview:
            rec_next = f"Provide the next missing field: {missing_preview[0]}"
        elif next_action.get("question"):
            rec_next = next_action["question"]
        else:
            rec_next = next_action.get("recommended_action") or next_action.get("action") or "Continue providing missing information."
        _emit({
            "success": True,
            "command": "preview",
            "session_id": args.session,
            "mode": "build_status",
            "known_fields": known_fields,
            "missing_for_preview": missing_preview,
            "missing_required": v_summary.get("missing_required", []),
            "pending_candidates": candidates.get("counts", {}).get("pending", 0),
            "confirmed_candidates": candidates.get("counts", {}).get("confirmed", 0),
            "pending_candidates_list": candidates.get("pending", []),
            "confirmed_candidates_list": candidates.get("confirmed", []),
            "validation_summary": v_summary,
            "render_gate": render_gate,
            "next_action": rec_next,
            "approval": approval_state,
            "preview_text": preview_text,
            "error": None,
        })


def cmd_approve(args: argparse.Namespace) -> None:
    """
    Record explicit user approval of the current draft preview.
    Saves session but does NOT finalize, render, or change candidates.
    """
    builder = _load_session(args.session)
    result = builder.record_approval()
    _save_session(builder)
    payload = builder.build_payload()
    _emit({
        "success": True,
        "command": "approve",
        "session_id": args.session,
        "approved_for_finalize": result["approved_for_finalize"],
        "approved_at": result["approved_at"],
        "approved_preview_hash": result["approved_preview_hash"],
        "current_preview_hash": result["current_preview_hash"],
        "approval_current": result["approval_current"],
        "payload": payload,
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "error": None,
    })


def _is_allowed_revise_target(field: str) -> bool:
    allowed = {
        "subj", "body", "date", "from", "to", "via",
        "signature", "signature.name", "signature.role", "signature.title",
        "ssic", "originator_code", "ref", "encl", "copy_to", "distribution",
    }
    return field in allowed


def _proposed_kv_from_text(text: str) -> dict[str, str] | None:
    """
    Simple key-value extraction for controlled revision text.
    Supports lines like: body: New text here.
    """
    text = text.strip()
    if ":" not in text:
        return None
    # Take first colon as field separator
    field, _, value = text.partition(":")
    field = field.strip()
    value = value.strip()
    if not field or not value:
        return None
    if not _is_allowed_revise_target(field):
        return None
    return {field: value}


def cmd_revise(args: argparse.Namespace) -> None:
    """
    Controlled revise command for final-review edits.
    Applies draft-relevant changes and clears approval if payload hash changes.
    """
    builder = _load_session(args.session)
    payload_before = builder.build_payload()
    hash_before = builder.compute_preview_hash()

    text = args.text if hasattr(args, "text") else ""
    proposed_kv = _proposed_kv_from_text(text)
    applied_answers: list[dict[str, Any]] = []

    if proposed_kv:
        # Apply through existing safe mediator path
        kv_raw = text.replace("\\n", "\n")
        result = builder.ingest_user_message(kv_raw)
        applied_answers = result.get("applied_answers", [])
    else:
        # No direct KV match; still record the revision text as user_message
        result = builder.ingest_user_message(text)
        applied_answers = result.get("applied_answers", [])

    payload_after = builder.build_payload()
    hash_after = builder.compute_preview_hash()
    payload_changed = hash_before != hash_after
    approval_cleared: dict[str, Any] | None = None

    if payload_changed:
        approval_cleared = builder.clear_approval(reason="Draft-relevant revision applied")

    _save_session(builder)

    _emit({
        "success": True,
        "command": "revise",
        "session_id": args.session,
        "proposed_kv": proposed_kv,
        "applied_answers": applied_answers,
        "preview_hash_before": hash_before,
        "preview_hash_after": hash_after,
        "payload_changed": payload_changed,
        "approval_cleared": payload_changed,
        "approval": builder.approval_state(),
        "payload": payload_after,
        "validation_summary": builder.validation_summary(),
        "warning_summary": builder.warning_summary(),
        "error": None,
    })


def cmd_next_action(args: argparse.Namespace) -> None:
    """
    Tell Hermes the next recommended action for the current session.
    Read-only: does not mutate the session, create candidates, or apply anything.
    """
    builder = _load_session(args.session)
    payload = builder.build_payload()
    user_text = args.text if args.text else None
    doc_type = args.doc_type if args.doc_type else None

    unresolved_facts = detect_unresolved_facts(
        payload=payload,
        user_text=user_text,
        doc_type=doc_type,
    )

    val_summary = builder.validation_summary()
    next_action = select_next_action(unresolved_facts, val_summary)

    # Build render gate from val_summary
    blocking = unresolved_facts.get("summary", {}).get("blocking", 0)
    recommended = unresolved_facts.get("summary", {}).get("recommended", 0)
    optional = unresolved_facts.get("summary", {}).get("optional", 0)
    errors = val_summary.get("errors", 0)
    finalize_allowed = val_summary.get("finalize_allowed", True)
    blocking_resolved = blocking == 0
    can_render = blocking_resolved and errors == 0 and finalize_allowed

    if not blocking_resolved:
        rg_reason = f"{blocking} blocking fact(s) remain unresolved"
    elif errors > 0:
        rg_reason = f"{errors} validation error(s) present"
    elif not finalize_allowed:
        rg_reason = "finalize not allowed by validation gate"
    else:
        rg_reason = "blocking facts resolved and validation gate passed"

    render_gate = {
        "blocking_resolved": blocking_resolved,
        "recommended_remaining": recommended,
        "optional_remaining": optional,
        "validator_errors": errors,
        "finalize_allowed": finalize_allowed,
        "can_render": can_render,
        "reason": rg_reason,
    }

    _emit({
        "success": True,
        "command": "next-action",
        "session_id": args.session,
        "payload": payload,
        "unresolved_summary": unresolved_facts.get("summary", {}),
        "next_action": next_action,
        "render_gate": render_gate,
        "error": None,
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

    # L.29C candidate commands
    cand_add_p = subparsers.add_parser("candidate-add", help="Record a candidate (pending)")
    cand_add_p.add_argument("--session", required=True)
    cand_add_p.add_argument("--json", required=True, help="Path to candidate JSON file")

    cands_p = subparsers.add_parser("candidates", help="List all candidates")
    cands_p.add_argument("--session", required=True)

    cand_confirm_p = subparsers.add_parser("candidate-confirm", help="Confirm and apply a candidate")
    cand_confirm_p.add_argument("--session", required=True)
    cand_confirm_p.add_argument("--candidate-id", required=True)

    cand_reject_p = subparsers.add_parser("candidate-reject", help="Reject a candidate")
    cand_reject_p.add_argument("--session", required=True)
    cand_reject_p.add_argument("--candidate-id", required=True)
    cand_reject_p.add_argument("--reason", default="", help="Rejection reason")

    apply_resolved_p = subparsers.add_parser("apply-resolved", help="Record/confirm a resolved candidate")
    apply_resolved_p.add_argument("--session", required=True)
    apply_resolved_p.add_argument("--json", required=True, help="Path to candidate JSON file")
    apply_resolved_p.add_argument("--confirm", action="store_true", help="Apply immediately after recording")
    apply_resolved_p.add_argument("--dry-run", action="store_true", help="Preview only, do not store or apply")

    detect_p = subparsers.add_parser("detect-facts", help="Detect unresolved facts from current payload")
    detect_p.add_argument("--session", required=True)
    detect_p.add_argument("--text", default=None, help="Optional user text for assisted detection")
    detect_p.add_argument("--doc-type", default=None, help="Override doc_type for detection")

    next_p = subparsers.add_parser("next-action", help="Tell Hermes the next recommended action")
    next_p.add_argument("--session", required=True)
    next_p.add_argument("--text", default=None, help="Optional user text for assisted detection")
    next_p.add_argument("--doc-type", default=None, help="Override doc_type for detection")

    preview_p = subparsers.add_parser("preview", help="Read-only preview of current session state")
    preview_p.add_argument("--session", required=True)

    approve_p = subparsers.add_parser("approve", help="Approve current draft preview for finalize")
    approve_p.add_argument("--session", required=True)

    revise_p = subparsers.add_parser("revise", help="Controlled revision of draft content")
    revise_p.add_argument("--session", required=True)
    revise_p.add_argument("--text", required=True, help="Revision text (e.g. body: New text)")

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
        "candidate-add": cmd_candidate_add,
        "candidates": cmd_candidates,
        "candidate-confirm": cmd_candidate_confirm,
        "candidate-reject": cmd_candidate_reject,
        "apply-resolved": cmd_apply_resolved,
        "detect-facts": cmd_detect_facts,
        "next-action": cmd_next_action,
        "preview": cmd_preview,
        "approve": cmd_approve,
        "revise": cmd_revise,
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
