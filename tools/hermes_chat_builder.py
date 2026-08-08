#!/usr/bin/env python3
r"""
Hermes Chat Builder — callable backend tool for Hermes.

This module keeps lightweight chat state, classifies natural turns, performs
controlled natural-language field extraction, delegates SECNAV session work to
hermes_session_manager.py, and returns user-facing responses for Hermes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    from ssic_resolver import resolve_ssic
except ModuleNotFoundError:  # pragma: no cover - defensive local fallback
    def resolve_ssic(subject: str, body_text: str = "") -> dict[str, str] | None:
        return None


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
# State and manager helpers
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


def _emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

_NEW_INTENTS = {
    "new letter", "create a", "create letter", "draft a", "draft letter",
    "need a letter", "i need a", "start a letter", "write a letter",
    "generate a letter", "prepare a letter", "prepare a standard letter",
    "compose a letter", "standard letter",
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
_PREVIEW_INTENTS = {"show me", "view draft", "what does it look like", "current draft", "show draft", "preview"}
_STATUS_INTENTS = {"status", "where are we", "what is the status", "current status", "are we ready", "check status", "progress"}


def _contains_any(text: str, needles: set[str]) -> bool:
    return any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in needles)


def _classify_intent(text: str) -> str:
    t = text.lower().strip()
    new_match = _contains_any(t, _NEW_INTENTS)
    revise_match = _contains_any(t, _REVISE_INTENTS)
    if new_match and revise_match:
        return "say"
    if _contains_any(t, _RENDER_INTENTS):
        return "render"
    if _contains_any(t, _APPROVE_INTENTS):
        return "approve"
    if revise_match:
        return "revise"
    if new_match:
        return "new"
    if _contains_any(t, _PREVIEW_INTENTS):
        return "preview"
    if _contains_any(t, _STATUS_INTENTS):
        return "status"
    return "say"


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

_PLAIN_MISSING = {
    "letterhead_top_line": "command letterhead",
    "letterhead_activity": "command letterhead",
    "letterhead_address": "command letterhead",
    "letterhead": "command letterhead",
    "unit_identity": "command letterhead",
    "from": "who the letter is from",
    "to": "who the letter is to",
    "subj": "subject",
    "subject": "subject",
    "body": "body text",
    "signature": "who will sign it",
    "date": "date",
}
_OPTIONAL_FIELDS = {"ssic", "originator_code", "originator code", "office_code", "office code"}


def _plain_missing_items(missing: list[Any]) -> list[str]:
    seen: list[str] = []
    for item in missing:
        raw = str(item)
        if raw.lower() in _OPTIONAL_FIELDS:
            continue
        plain = _PLAIN_MISSING.get(raw, raw.replace("_", " "))
        if plain not in seen:
            seen.append(plain)
    return seen


def _missing_prompt(missing: list[Any]) -> str:
    plain = _plain_missing_items(missing)
    if not plain:
        return "I have the optional routing details handled. Provide any remaining required details in plain English."
    if set(plain) == {"date", "who will sign it", "body text"}:
        return "I have the routing basics. What date should I use, who will sign it, and what should the body say?"
    return f"I have part of the letter. I still need: {', '.join(plain[:5])}."


def _determine_phase(ready_result: dict[str, Any], preview_result: dict[str, Any]) -> str:
    if ready_result.get("approved_ready"):
        return "approved_ready"
    if preview_result.get("mode") == "draft_preview":
        return "draft_preview"
    if preview_result.get("mode") == "build_status":
        return "build_status"
    if ready_result.get("validation_ready") and not ready_result.get("approved_ready"):
        return "draft_preview"
    return "build_status"


def _build_next_step(phase: str, ready_result: dict[str, Any], preview_result: dict[str, Any]) -> str:
    if phase == "approved_ready":
        return "Draft is approved and ready. Say 'make the PDF' to render."
    if phase == "draft_preview":
        approval = preview_result.get("approval") or {}
        if approval.get("approval_current"):
            return "Draft is approved. Say 'make the PDF' to render."
        return "Draft preview is ready. Review it and say 'looks good' to approve."
    missing = (ready_result.get("render_gate") or {}).get("missing", [])
    if missing:
        return _missing_prompt(missing)
    next_action = ready_result.get("next_action") or {}
    if next_action.get("question"):
        question = str(next_action["question"])
        if "ssic" in question.lower() or "originator" in question.lower():
            return "I have the optional routing details handled. Provide any remaining required details in plain English."
        return question
    return "Keep providing details to complete the letter."


def _build_assistant_response(
    phase: str,
    ready_result: dict[str, Any],
    preview_result: dict[str, Any],
    *,
    action: str = "",
    pdf_path: str = "",
    blocked_reason: str = "",
) -> str:
    if phase == "rendered":
        return f"Done! Your PDF is ready at {pdf_path}. You can start a new chat if you need another letter."
    if phase == "approved_ready":
        return "Your draft is approved and everything looks good. Say 'make the PDF' and I'll generate it."
    if phase == "draft_preview":
        approval = (preview_result.get("approval") or {}).get("approval_current", False)
        if approval:
            return "Your draft is approved. Say 'make the PDF' and I'll generate it."
        return "Your draft is ready for review. You can say 'looks good' to approve it, or tell me what you'd like to change."
    if action == "approve":
        return "Your draft is approved! You can now say 'make the PDF' and I'll generate it."
    if action == "render" and phase == "blocked":
        reason = blocked_reason or "The draft needs approval and all required fields must be ready."
        return f"I can't make the PDF yet. {reason} Review the draft and say 'looks good' to approve it first."
    if action == "revise":
        return "I've updated the draft. Please review the preview and say 'looks good' when you're ready to approve it."
    missing = (ready_result.get("render_gate") or {}).get("missing", [])
    if missing:
        return _missing_prompt(missing)
    next_action = ready_result.get("next_action") or {}
    if next_action.get("field"):
        field = str(next_action.get("field", ""))
        if field.lower() in _OPTIONAL_FIELDS:
            return "I have the optional routing details handled. Provide any remaining required details in plain English."
        return f"I still need {_PLAIN_MISSING.get(field, field.replace('_', ' '))}. {next_action.get('question', '')}".strip()
    return "Got it. Keep providing details and I'll build the draft for you."


# ---------------------------------------------------------------------------
# Intake parsing, natural assisted resolution, and SSIC inference
# ---------------------------------------------------------------------------

_KEY_VALUE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_. -]*\s*:\s*", re.MULTILINE)
_DATE_RE = re.compile(r"\b(?:use\s+the\s+date|date)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", re.IGNORECASE)
_USE_DATE_RE = re.compile(r"\buse\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", re.IGNORECASE)
_KEY_ALIASES = {
    "subject": "subj",
    "signer": "signature",
    "signature_name": "signature",
    "originator": "originator_code",
    "originator_code": "originator_code",
    "originator code": "originator_code",
    "office code": "originator_code",
    "office_code": "originator_code",
    "orig": "originator_code",
}

_UNIT_ALIASES = {
    # MCAS New River (existing)
    "mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    "new river air station": "Commanding Officer, Marine Corps Air Station New River",
    "marine corps air station new river": "Commanding Officer, Marine Corps Air Station New River",
    "commanding officer mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    "commanding officer marine corps air station new river": "Commanding Officer, Marine Corps Air Station New River",
    "co mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    # II MEF (existing)
    "ii mef": "Commanding General, II Marine Expeditionary Force",
    "2d mef": "Commanding General, II Marine Expeditionary Force",
    "second mef": "Commanding General, II Marine Expeditionary Force",
    "second marine expeditionary force": "Commanding General, II Marine Expeditionary Force",
    "cg ii mef": "Commanding General, II Marine Expeditionary Force",
    "commanding general ii mef": "Commanding General, II Marine Expeditionary Force",
    "commanding general, ii mef": "Commanding General, II Marine Expeditionary Force",
    # MCAS Cherry Point (L.31S)
    "mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "cherry point air station": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "marine corps air station cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "commanding officer mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "co mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    # Camp Lejeune / MCB Camp Lejeune (L.31S)
    "camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "mcb camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "marine corps base camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "commanding officer camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "commanding officer mcb camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "co camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "co mcb camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    # MARFORCOM (L.31S)
    "marforcom": "Commander, Marine Forces Command",
    "marine forces command": "Commander, Marine Forces Command",
    "commander marine forces command": "Commander, Marine Forces Command",
    "commander, marine forces command": "Commander, Marine Forces Command",
    # HQMC / Headquarters Marine Corps (L.31S)
    "hqmc": "Commandant of the Marine Corps",
    "headquarters marine corps": "Commandant of the Marine Corps",
    "commandant of the marine corps": "Commandant of the Marine Corps",
    "cmc": "Commandant of the Marine Corps",
}

_LETTERHEAD_ALIASES = {
    # MCAS New River (existing)
    "mcas new river": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address": "JACKSONVILLE NC 28545-0000",
    },
    "new river air station": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address": "JACKSONVILLE NC 28545-0000",
    },
    "marine corps air station new river": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
        "letterhead_address": "JACKSONVILLE NC 28545-0000",
    },
    # MCAS Cherry Point (L.31S)
    "mcas cherry point": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT",
        "letterhead_address": "CHERRY POINT NC 28533-0000",
    },
    "cherry point air station": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT",
        "letterhead_address": "CHERRY POINT NC 28533-0000",
    },
    "marine corps air station cherry point": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT",
        "letterhead_address": "CHERRY POINT NC 28533-0000",
    },
    # Camp Lejeune / MCB Camp Lejeune (L.31S)
    "camp lejeune": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE",
        "letterhead_address": "CAMP LEJEUNE NC 28542-0000",
    },
    "mcb camp lejeune": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE",
        "letterhead_address": "CAMP LEJEUNE NC 28542-0000",
    },
    "marine corps base camp lejeune": {
        "letterhead_top_line": "UNITED STATES MARINE CORPS",
        "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE",
        "letterhead_address": "CAMP LEJEUNE NC 28542-0000",
    },
}


def _looks_like_key_value(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("(") or stripped.startswith("["):
        return False
    return bool(_KEY_VALUE_RE.search(stripped))


def _clean_extracted_value(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip(" \t\r\n,.;\"'"))


def _normalize_subject(value: str) -> str:
    value = _clean_extracted_value(value)
    return value if value.isupper() else value.upper()


def _normalize_body(value: str) -> str:
    value = _clean_extracted_value(value)
    value = re.sub(r"^(?:about|that)\s+", "", value, flags=re.IGNORECASE).strip()
    if not value:
        return value
    if re.match(r"^(implementing|reviewing|updating|establishing|creating)\b", value, re.IGNORECASE):
        value = f"This letter addresses {value}"
    else:
        value = value[0].upper() + value[1:]
    if value[-1] not in ".!?":
        value += "."
    return value


def _canonical_key(key: str) -> str:
    compact = re.sub(r"\s+", " ", key.strip().lower().replace("-", "_"))
    underscored = compact.replace(" ", "_")
    return _KEY_ALIASES.get(compact, _KEY_ALIASES.get(underscored, underscored))


def _expand_unit(value: str) -> str:
    clean = _clean_extracted_value(value)
    key = re.sub(r"\s+", " ", clean.lower().replace("c.g.", "cg")).strip()
    return _UNIT_ALIASES.get(key, clean)


def _infer_letterhead_from_from_line(from_line: str) -> dict[str, str]:
    low = from_line.lower()
    for key, fields in _LETTERHEAD_ALIASES.items():
        if key in low:
            return dict(fields)
    return {}


def _subject_from_topic(topic: str) -> str:
    clean = _clean_extracted_value(topic).lower()
    clean = re.sub(r"^(reviewing|review|implementing|implementation of|about)\s+", "", clean).strip()
    if "correspondence" in clean and ("procedure" in clean or "review" in clean):
        return "REVIEW OF CORRESPONDENCE PROCEDURES"
    if clean:
        return _normalize_subject(clean)
    return ""


def _parse_explicit_key_values(text: str) -> tuple[dict[str, str], str]:
    fields: dict[str, str] = {}
    prose_lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_. -]*)\s*:\s*(.*?)\s*$", line)
        if not match:
            prose_lines.append(line)
            continue
        key = _canonical_key(match.group(1))
        value = _clean_extracted_value(match.group(2))
        if not value:
            continue
        if key == "subj":
            value = _normalize_subject(value)
        elif key == "body":
            value = _normalize_body(value)
        elif key in {"ssic", "originator_code"}:
            value = value.upper()
        fields[key] = value
    return fields, "\n".join(prose_lines).strip()


def _extract_first_turn_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    lower = raw.lower()
    if not any(k in lower for k in _NEW_INTENTS):
        return fields

    from_to = re.search(
        r"\bfrom\s+(.+?)\s+to\s+(.+?)(?=(?:\s+about\b|\s+regarding\b|\s+concerning\b|[,.;]\s*(?:use|signer|signature|subject|ssic|originator|make|body)\b|$))",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if from_to:
        fields["from"] = _expand_unit(from_to.group(1))
        fields["to"] = _expand_unit(from_to.group(2))
        fields.update({k: v for k, v in _infer_letterhead_from_from_line(fields["from"]).items() if k not in fields})

    topic_match = re.search(r"\b(?:about|regarding|concerning)\s+(.+?)(?=(?:[,.;]\s*(?:use|signer|signature|subject|ssic|originator|make|body)\b|$))", raw, re.IGNORECASE | re.DOTALL)
    if topic_match and "subj" not in fields:
        subject = _subject_from_topic(topic_match.group(1))
        if subject:
            fields["subj"] = subject

    date_match = _DATE_RE.search(raw) or _USE_DATE_RE.search(raw)
    if date_match:
        fields["date"] = _clean_extracted_value(date_match.group(1))

    ssic_match = re.search(r"\bSSIC\s*:?\s*([A-Za-z0-9.-]+)\b", raw, re.IGNORECASE)
    if ssic_match:
        fields["ssic"] = _clean_extracted_value(ssic_match.group(1)).upper()

    originator_match = re.search(r"\b(?:originator|office)\s+code\s*:?\s*([A-Za-z0-9-]+)\b", raw, re.IGNORECASE)
    if originator_match:
        fields["originator_code"] = _clean_extracted_value(originator_match.group(1)).upper()

    signer_match = re.search(
        r"\b(?:signer|signature)\s*:?\s*(.+?)(?=(?:,\s*(?:and\s+)?(?:subject|ssic|originator|date|make|body|use)\b|[.;]\s*$|$))",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if signer_match:
        fields["signature"] = _clean_extracted_value(signer_match.group(1))

    subject_match = re.search(
        r"\bsubject\s*:?\s+(.+?)(?=(?:,\s*(?:and\s+)?(?:make|body|use|signer|signature|ssic|originator|date)\b|[.;]\s*$|$))",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if subject_match:
        fields["subj"] = _normalize_subject(subject_match.group(1))

    body_match = re.search(
        r"\b(?:make\s+the\s+body\s+about|body\s+about|body\s*:)\s+(.+?)(?=(?:\n\s*[A-Za-z][A-Za-z0-9_. -]*\s*:|[.;]\s*$|$))",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if body_match:
        body = _normalize_body(body_match.group(1))
        if body:
            fields["body"] = body
    return {key: value for key, value in fields.items() if value}


def _extract_followup_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    date_match = _DATE_RE.search(raw) or _USE_DATE_RE.search(raw)
    if date_match:
        fields["date"] = _clean_extracted_value(date_match.group(1))
    signer_match = re.search(r"\b([A-Z](?:\.\s*)?(?:[A-Z](?:\.\s*)?)*[A-Z][A-Z .'-]*)\s+will\s+sign\s+it\b", raw, re.IGNORECASE)
    if signer_match:
        fields["signature"] = _clean_extracted_value(signer_match.group(1)).upper()
    body_match = re.search(r"\b(?:the\s+)?body\s+(?:should\s+)?(?:say|state|read)\s+(.+?)(?=(?:$|[.;]\s*$))", raw, re.IGNORECASE | re.DOTALL)
    if body_match:
        fields["body"] = _normalize_body(body_match.group(1))
    return {key: value for key, value in fields.items() if value}


def _extract_revision_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    body_match = re.search(
        r"\b(?:change|update|revise|rewrite|make)\s+(?:the\s+)?body\s+(?:to\s+)?(?:say|state|read)?\s*(.+?)(?=(?:$|[.;]\s*$))",
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    if body_match:
        body = _normalize_body(body_match.group(1))
        if body:
            fields["body"] = body
    return fields


def _merge_mixed_intake_fields(text: str) -> dict[str, str]:
    explicit_fields, prose_text = _parse_explicit_key_values(text)
    prose_fields = _extract_first_turn_key_values(prose_text or text)
    followup_fields = _extract_followup_fields(prose_text or text)
    merged = {**followup_fields, **prose_fields, **explicit_fields}
    return {key: value for key, value in merged.items() if value}


def _key_values_to_text(fields: dict[str, str]) -> str:
    ordered = [
        "letterhead_top_line",
        "letterhead_activity",
        "letterhead_address",
        "ssic",
        "originator_code",
        "from",
        "to",
        "date",
        "subj",
        "body",
        "signature",
    ]
    lines = [f"{key}: {fields[key]}" for key in ordered if key in fields]
    lines.extend(f"{key}: {value}" for key, value in fields.items() if key not in ordered)
    return "\n".join(lines)


def _payload_body_text(payload: dict[str, Any]) -> str:
    body = payload.get("body") or payload.get("body_paragraphs") or ""
    if isinstance(body, list):
        return "\n".join(str(item) for item in body)
    return str(body or "")


def _coerce_ssic_result(resolved: Any) -> dict[str, str] | None:
    if isinstance(resolved, dict):
        code = str(resolved.get("code") or "").strip()
        if code:
            return {"code": code, "description": str(resolved.get("description") or "")}
    if isinstance(resolved, tuple) and resolved:
        code = str(resolved[0] or "").strip()
        if code:
            desc = str(resolved[1]) if len(resolved) > 1 else ""
            return {"code": code, "description": desc}
    return None


def _maybe_infer_and_apply_ssic(session_id: str, payload: dict[str, Any] | None) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    if not isinstance(payload, dict) or payload.get("ssic"):
        return None, None
    subject = str(payload.get("subj") or payload.get("subject") or "")
    body_text = _payload_body_text(payload)
    resolved = _coerce_ssic_result(resolve_ssic(subject, body_text))
    if not resolved or not resolved.get("code"):
        return None, None
    code = str(resolved["code"]).strip()
    if not code:
        return None, None
    apply_r = _run_manager(["apply", "--session", session_id, "--kv", f"ssic: {code}"])
    return resolved, apply_r


def _body_from_result(result: dict[str, Any]) -> str:
    payload = result.get("payload") if isinstance(result, dict) else {}
    if isinstance(payload, dict):
        return _payload_body_text(payload)
    return ""


# ---------------------------------------------------------------------------
# Chat action handlers
# ---------------------------------------------------------------------------


def _run_say_and_status(session_id: str, text: str) -> dict[str, Any]:
    extracted_fields = _merge_mixed_intake_fields(text)
    if extracted_fields:
        say_r = _run_manager(["apply", "--session", session_id, "--kv", _key_values_to_text(extracted_fields)])
    elif _looks_like_key_value(text):
        say_r = _run_manager(["apply", "--session", session_id, "--kv", text])
    else:
        say_r = _run_manager(["say", "--session", session_id, "--text", text])

    ssic_inference, ssic_apply_r = _maybe_infer_and_apply_ssic(session_id, say_r.get("payload"))
    if ssic_apply_r and ssic_apply_r.get("success"):
        say_r = ssic_apply_r

    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])
    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    assistant_response = _build_assistant_response(phase, ready_r, preview_r)
    return {
        "success": say_r.get("success", False),
        "intent": "say",
        "phase": phase,
        "message": f"I've noted that. Current phase: {phase.replace('_', ' ')}. {next_step}" if say_r.get("success") else say_r.get("error", "Say failed"),
        "assistant_response": assistant_response,
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "payload": say_r.get("payload"),
        "validation_summary": say_r.get("validation_summary"),
        "warning_summary": say_r.get("warning_summary"),
        "proposed_kv": say_r.get("proposed_kv"),
        "extracted_kv": extracted_fields or None,
        "ssic_inference": ssic_inference,
        "validation_ready": ready_r.get("validation_ready", False),
        "approved_ready": ready_r.get("approved_ready", False),
        "render_gate": ready_r.get("render_gate"),
        "error": say_r.get("error"),
    }


def _run_revise_and_status(session_id: str, text: str) -> dict[str, Any]:
    revision_fields = _extract_revision_fields(text)
    if revision_fields:
        before_r = _run_manager(["resume", "--session", session_id])
        before_ready = _run_manager(["ready", "--session", session_id])
        before_body = _body_from_result(before_r)
        apply_r = _run_manager(["apply", "--session", session_id, "--kv", _key_values_to_text(revision_fields)])
        preview_r = _run_manager(["preview", "--session", session_id])
        ready_r = _run_manager(["ready", "--session", session_id])
        phase = _determine_phase(ready_r, preview_r)
        next_step = _build_next_step(phase, ready_r, preview_r)
        after_body = _body_from_result(apply_r)
        changed = bool(apply_r.get("success") and after_body and after_body != before_body)
        was_approved = bool(before_ready.get("approved_ready") or (before_ready.get("approval") or {}).get("approval_current"))
        cleared = bool(changed and was_approved and not ready_r.get("approved_ready", False))
        assistant_response = _build_assistant_response(phase, ready_r, preview_r, action="revise") if changed else "I understood the request, but nothing in the draft was changed. Try changing the body, subject, signer, or date."
        return {
            "success": apply_r.get("success", False),
            "intent": "revise",
            "phase": phase,
            "message": f"Revised draft. Payload changed: {changed}. Approval cleared: {cleared}. Current phase: {phase.replace('_', ' ')}. {next_step}" if apply_r.get("success") else apply_r.get("error", "Revise failed"),
            "assistant_response": assistant_response,
            "preview_text": preview_r.get("preview_text"),
            "next_step": next_step,
            "payload": apply_r.get("payload"),
            "validation_summary": apply_r.get("validation_summary"),
            "warning_summary": apply_r.get("warning_summary"),
            "approval_cleared": cleared,
            "payload_changed": changed,
            "applied_revision_kv": revision_fields,
            "validation_ready": ready_r.get("validation_ready", False),
            "approved_ready": ready_r.get("approved_ready", False),
            "error": apply_r.get("error"),
        }

    revise_r = _run_manager(["revise", "--session", session_id, "--text", text])
    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])
    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    changed = revise_r.get("payload_changed", False)
    cleared = revise_r.get("approval_cleared", False)
    if not revise_r.get("success"):
        assistant_response = "I wasn't able to apply that change to the draft. Try a supported change such as changing the body, subject, signer, or date."
    elif not changed:
        assistant_response = "I understood the request, but nothing in the draft was changed. Try changing the body, subject, signer, or date."
    else:
        assistant_response = _build_assistant_response(phase, ready_r, preview_r, action="revise")
    return {
        "success": revise_r.get("success", False),
        "intent": "revise",
        "phase": phase,
        "message": f"Revised draft. Payload changed: {changed}. Approval cleared: {cleared}. Current phase: {phase.replace('_', ' ')}. {next_step}" if revise_r.get("success") else revise_r.get("error", "Revise failed"),
        "assistant_response": assistant_response,
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "payload": revise_r.get("payload"),
        "validation_summary": revise_r.get("validation_summary"),
        "warning_summary": revise_r.get("warning_summary"),
        "approval_cleared": cleared,
        "payload_changed": changed,
        "validation_ready": ready_r.get("validation_ready", False),
        "approved_ready": ready_r.get("approved_ready", False),
        "error": revise_r.get("error"),
    }


def _run_approve_and_status(session_id: str) -> dict[str, Any]:
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
    return {
        "success": approve_r.get("success", False),
        "intent": "approve",
        "phase": phase,
        "message": f"Draft approved. Current phase: {phase.replace('_', ' ')}. {next_step}" if approved else next_step,
        "assistant_response": _build_assistant_response(phase, ready_r, {}, action="approve", blocked_reason=next_step if phase == "blocked" else ""),
        "next_step": next_step,
        "approved_for_finalize": approved,
        "approved_ready": approved_ready,
        "validation_ready": ready_r.get("validation_ready", False),
        "approval": approve_r.get("approval"),
        "error": approve_r.get("error"),
    }


def _run_preview_status(session_id: str) -> dict[str, Any]:
    preview_r = _run_manager(["preview", "--session", session_id])
    ready_r = _run_manager(["ready", "--session", session_id])
    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    return {
        "success": preview_r.get("success", False),
        "intent": "preview",
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "assistant_response": _build_assistant_response(phase, ready_r, preview_r),
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "mode": preview_r.get("mode"),
        "approval": preview_r.get("approval"),
        "approved_ready": ready_r.get("approved_ready", False),
        "validation_ready": ready_r.get("validation_ready", False),
        "error": preview_r.get("error"),
    }


def _run_ready_status(session_id: str) -> dict[str, Any]:
    ready_r = _run_manager(["ready", "--session", session_id])
    preview_r = _run_manager(["preview", "--session", session_id])
    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    return {
        "success": ready_r.get("success", False),
        "intent": "ready",
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "assistant_response": _build_assistant_response(phase, ready_r, preview_r),
        "approved_ready": ready_r.get("approved_ready", False),
        "validation_ready": ready_r.get("validation_ready", False),
        "next_step": next_step,
        "approval": ready_r.get("approval"),
        "render_gate": ready_r.get("render_gate"),
        "error": ready_r.get("error"),
    }


def _run_render_gate(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    ready_r = _run_manager(["ready", "--session", session_id])
    if not ready_r.get("approved_ready", False):
        phase = _determine_phase(ready_r, {"mode": "build_status"})
        next_step = _build_next_step(phase, ready_r, {"mode": "build_status"})
        return {
            "success": False,
            "intent": "render",
            "phase": phase,
            "message": f"Cannot render yet. Current phase: {phase.replace('_', ' ')}. {next_step}",
            "assistant_response": _build_assistant_response("blocked", ready_r, {}, action="render", blocked_reason=ready_r.get("error") or "The draft isn't approved or validation isn't ready yet."),
            "next_step": next_step,
            "approved_ready": False,
            "validation_ready": ready_r.get("validation_ready", False),
            "error": ready_r.get("error") or "Render blocked: not approved_ready.",
        }
    out_dir = _REPO_ROOT / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(state.get("out_path")) if state.get("out_path") else out_dir / f"chat_{session_id}.pdf"
    render_r = _run_manager(["render", "--session", session_id, "--out", str(pdf_path)])
    if render_r.get("success") and pdf_path.exists() and pdf_path.stat().st_size > 0:
        state["last_pdf_path"] = str(pdf_path)
        state["rendered_at"] = render_r.get("message", "")
        _save_state(state["chat_id"], state)
        return {
            "success": True,
            "intent": "render",
            "phase": "rendered",
            "message": f"PDF rendered successfully: {pdf_path}",
            "assistant_response": _build_assistant_response("rendered", {}, {}, pdf_path=str(pdf_path)),
            "pdf_path": str(pdf_path),
            "pdf_size": pdf_path.stat().st_size,
            "next_step": "Letter is complete. You can start a new chat for another letter.",
            "error": None,
        }
    return {
        "success": False,
        "intent": "render",
        "phase": "blocked",
        "message": render_r.get("error", "Render failed."),
        "assistant_response": _build_assistant_response("blocked", {}, {}, action="render", blocked_reason=render_r.get("error") or "Render failed."),
        "next_step": "Check status and ensure draft is approved and validation is ready.",
        "error": render_r.get("error", "Render failed."),
    }


def _process_turn(chat_id: str, text: str, state: dict[str, Any]) -> dict[str, Any]:
    session_id = state["session_id"]
    intent = _classify_intent(text)
    state["history"].append({"role": "user", "text": text, "intent": intent})
    if len(state["history"]) > 20:
        state["history"] = state["history"][-20:]
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
    state["history"].append({"role": "assistant", "phase": result.get("phase"), "message": result.get("message")})
    _save_state(chat_id, state)
    return result


# ---------------------------------------------------------------------------
# Pure internal backends
# ---------------------------------------------------------------------------


def _start_chat(out: str | None = None) -> dict[str, Any]:
    result = _run_manager(["new"])
    if not result.get("success"):
        return {"success": False, "command": "start", "message": f"Failed to create session: {result.get('error')}", "error": result.get("error")}
    session_id = result["session_id"]
    chat_id = f"chat-{uuid.uuid4().hex[:12]}"
    state: dict[str, Any] = {
        "chat_id": chat_id,
        "session_id": session_id,
        "created_at": result.get("message", ""),
        "history": [],
        "last_pdf_path": None,
        "rendered_at": None,
    }
    if out:
        state["out_path"] = str(out)
    _save_state(chat_id, state)
    return {"success": True, "command": "start", "chat_id": chat_id, "session_id": session_id, "message": "Chat started.", "next_step": "Tell me what letter you need.", "error": None}


def _send_chat_turn(chat_id: str, text: str, out: str | None = None) -> dict[str, Any]:
    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        return {"success": False, "command": "chat", "error": str(exc)}
    if out is not None:
        state["out_path"] = str(out)
        _save_state(chat_id, state)
    result = _process_turn(chat_id, text, state)
    return {
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
        "validation_ready": result.get("validation_ready"),
        "approved_ready": result.get("approved_ready"),
        "payload": result.get("payload"),
        "extracted_kv": result.get("extracted_kv"),
        "ssic_inference": result.get("ssic_inference"),
        "error": result.get("error"),
    }


def _get_chat_status(chat_id: str) -> dict[str, Any]:
    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        return {"success": False, "command": "status", "error": str(exc)}
    session_id = state["session_id"]
    ready_r = _run_manager(["ready", "--session", session_id])
    preview_r = _run_manager(["preview", "--session", session_id])
    phase = _determine_phase(ready_r, preview_r)
    next_step = _build_next_step(phase, ready_r, preview_r)
    return {
        "success": True,
        "command": "status",
        "chat_id": chat_id,
        "session_id": session_id,
        "phase": phase,
        "message": f"Current phase: {phase.replace('_', ' ')}. {next_step}",
        "assistant_response": _build_assistant_response(phase, ready_r, preview_r),
        "preview_text": preview_r.get("preview_text"),
        "next_step": next_step,
        "approved_ready": ready_r.get("approved_ready", False),
        "validation_ready": ready_r.get("validation_ready", False),
        "last_pdf_path": state.get("last_pdf_path"),
        "history_count": len(state.get("history", [])),
        "error": None,
    }


def _reset_chat(chat_id: str) -> dict[str, Any]:
    try:
        state = _load_state(chat_id)
    except FileNotFoundError as exc:
        return {"success": False, "command": "reset", "error": str(exc)}
    result = _run_manager(["new"])
    if not result.get("success"):
        return {"success": False, "command": "reset", "error": f"Failed to create new session: {result.get('error')}"}
    state["session_id"] = result["session_id"]
    state["history"] = []
    state["last_pdf_path"] = None
    state["rendered_at"] = None
    _save_state(chat_id, state)
    return {
        "success": True,
        "command": "reset",
        "chat_id": chat_id,
        "session_id": result["session_id"],
        "message": f"Chat reset with new session {result['session_id']}.",
        "assistant_response": "I've reset the chat. You can start a new letter request whenever you're ready.",
        "next_step": "Tell me what letter you need.",
        "error": None,
    }


# ---------------------------------------------------------------------------
# Public callable functions for Hermes
# ---------------------------------------------------------------------------


def start_secnav_chat(chat_id: str | None = None, out: str | None = None) -> dict[str, Any]:
    if chat_id:
        try:
            _load_state(chat_id)
            return _get_chat_status(chat_id)
        except FileNotFoundError:
            pass
    return _start_chat(out=out)


def send_secnav_chat_turn(chat_id: str, text: str, out: str | None = None) -> dict[str, Any]:
    return _send_chat_turn(chat_id, text, out=out)


def get_secnav_chat_status(chat_id: str) -> dict[str, Any]:
    return _get_chat_status(chat_id)


def reset_secnav_chat(chat_id: str) -> dict[str, Any]:
    return _reset_chat(chat_id)


def format_tool_response_for_hermes(result: dict[str, Any]) -> str:
    if not result.get("success"):
        err = result.get("error") or "Something went wrong."
        return f"I couldn't complete that. {err}"
    lines: list[str] = []
    if result.get("assistant_response"):
        lines.append(result["assistant_response"])
    if result.get("phase") == "rendered":
        pdf_path = result.get("pdf_path", "")
        pdf_size = result.get("pdf_size")
        if pdf_path:
            size_str = f" ({pdf_size} bytes)" if pdf_size else ""
            lines.append(f"PDF: {pdf_path}{size_str}")
        return "\n".join(lines)
    if result.get("preview_text"):
        lines.append(f"Preview:\n{result['preview_text']}")
    if result.get("next_step") and not lines:
        lines.append(result["next_step"])
    return "\n".join(lines) if lines else result.get("message", "Done.")


# ---------------------------------------------------------------------------
# CLI command handlers and interactive mode
# ---------------------------------------------------------------------------


def cmd_start(_args: argparse.Namespace) -> None:
    _emit(_start_chat())


def cmd_chat(args: argparse.Namespace) -> None:
    chat_id = getattr(args, "chat_id", None)
    text = getattr(args, "text", "")
    if not chat_id:
        _emit({"success": False, "command": "chat", "error": "--chat-id required"})
        return
    _emit(_send_chat_turn(chat_id, text))


def cmd_status(args: argparse.Namespace) -> None:
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        _emit({"success": False, "command": "status", "error": "--chat-id required"})
        return
    _emit(_get_chat_status(chat_id))


def cmd_reset(args: argparse.Namespace) -> None:
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        _emit({"success": False, "command": "reset", "error": "--chat-id required"})
        return
    _emit(_reset_chat(chat_id))


_EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}


def cmd_interactive(args: argparse.Namespace) -> None:
    chat_id = getattr(args, "chat_id", None)
    out_path = getattr(args, "out", "")
    json_lines = getattr(args, "json_lines", False)
    if chat_id:
        try:
            _load_state(chat_id)
        except FileNotFoundError:
            _emit({"success": False, "command": "interactive", "error": f"Chat not found: {chat_id}"})
            return
    else:
        result = _start_chat(out=str(out_path) if out_path else None)
        if not result.get("success"):
            _emit({"success": False, "command": "interactive", "error": result.get("error", "Start failed.")})
            return
        chat_id = result["chat_id"]
        _emit(result)
        print("\n" + _build_assistant_response("build_status", {}, {}), flush=True)
    state = _load_state(chat_id)
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        if text.lower() in _EXIT_COMMANDS:
            _emit({"success": True, "command": "interactive", "chat_id": chat_id, "message": "Goodbye.", "error": None})
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
    interactive_p = subparsers.add_parser("interactive", help="Start an interactive chat loop (local test/debug only)")
    interactive_p.add_argument("--chat-id", default=None, help="Existing chat ID, auto-creates if omitted")
    interactive_p.add_argument("--out", default=None, help="Optional output PDF path")
    interactive_p.add_argument("--json-lines", action="store_true", help="Emit JSON per turn instead of plain text")
    args = parser.parse_args(argv)
    handlers: dict[str, Any] = {"start": cmd_start, "chat": cmd_chat, "status": cmd_status, "reset": cmd_reset, "interactive": cmd_interactive}
    try:
        handlers[args.command](args)
    except Exception as exc:
        _emit({"success": False, "command": getattr(args, "command", "unknown"), "chat_id": getattr(args, "chat_id", None), "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
