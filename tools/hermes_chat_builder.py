#!/usr/bin/env python3
r"""
Hermes Chat Builder — callable backend tool for Hermes.

Thin chat wrapper for Hermes/SECNAV sessions.  It performs controlled natural
field extraction, delegates session work to hermes_session_manager.py, and keeps
source-backed command resolution candidate-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

try:
    from ssic_resolver import resolve_ssic
except ModuleNotFoundError:  # pragma: no cover
    def resolve_ssic(subject: str, body_text: str = "") -> dict[str, str] | None:
        return None

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_VENV_PYTHON = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
_FALLBACK_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_PYTHON = _VENV_PYTHON if _VENV_PYTHON.exists() else _FALLBACK_PYTHON
_MANAGER = _TOOL_ROOT / "hermes_session_manager.py"
_STATE_DIR = Path.home() / ".hermes" / "secnav_sessions" / "chat_builder_state"
_STATE_DIR.mkdir(parents=True, exist_ok=True)

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
_CONFIRM_CANDIDATE_INTENTS = {"confirm candidate", "apply candidate", "use candidate", "yes use it", "yes apply it", "confirm it"}
_REJECT_CANDIDATE_INTENTS = {"reject candidate", "do not use", "don't use", "no don't", "reject it"}

_OPTIONAL_FIELDS = {"ssic", "originator_code", "originator code", "office_code", "office code"}
_PLAIN_MISSING = {
    "letterhead_top_line": "command letterhead", "letterhead_activity": "command letterhead",
    "letterhead_address": "command letterhead", "letterhead": "command letterhead",
    "unit_identity": "command letterhead", "from": "who the letter is from", "to": "who the letter is to",
    "subj": "subject", "subject": "subject", "body": "body text", "signature": "who will sign it", "date": "date",
}

_UNIT_ALIASES = {
    "mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    "new river air station": "Commanding Officer, Marine Corps Air Station New River",
    "marine corps air station new river": "Commanding Officer, Marine Corps Air Station New River",
    "commanding officer mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    "co mcas new river": "Commanding Officer, Marine Corps Air Station New River",
    "ii mef": "Commanding General, II Marine Expeditionary Force",
    "2d mef": "Commanding General, II Marine Expeditionary Force",
    "second mef": "Commanding General, II Marine Expeditionary Force",
    "second marine expeditionary force": "Commanding General, II Marine Expeditionary Force",
    "cg ii mef": "Commanding General, II Marine Expeditionary Force",
    "commanding general ii mef": "Commanding General, II Marine Expeditionary Force",
    "commanding general, ii mef": "Commanding General, II Marine Expeditionary Force",
    "mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "cherry point air station": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "marine corps air station cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "commanding officer mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "co mcas cherry point": "Commanding Officer, Marine Corps Air Station Cherry Point",
    "camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "mcb camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "marine corps base camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "commanding officer camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "co camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "co mcb camp lejeune": "Commanding Officer, Marine Corps Base Camp Lejeune",
    "marforcom": "Commander, Marine Forces Command",
    "marine forces command": "Commander, Marine Forces Command",
    "commander marine forces command": "Commander, Marine Forces Command",
    "hqmc": "Commandant of the Marine Corps",
    "headquarters marine corps": "Commandant of the Marine Corps",
    "commandant of the marine corps": "Commandant of the Marine Corps",
    "cmc": "Commandant of the Marine Corps",
}
_LETTERHEAD_ALIASES = {
    "mcas new river": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER", "letterhead_address": "JACKSONVILLE NC 28545-0000"},
    "new river air station": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER", "letterhead_address": "JACKSONVILLE NC 28545-0000"},
    "marine corps air station new river": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER", "letterhead_address": "JACKSONVILLE NC 28545-0000"},
    "mcas cherry point": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT", "letterhead_address": "CHERRY POINT NC 28533-0000"},
    "cherry point air station": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT", "letterhead_address": "CHERRY POINT NC 28533-0000"},
    "marine corps air station cherry point": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS AIR STATION CHERRY POINT", "letterhead_address": "CHERRY POINT NC 28533-0000"},
    "camp lejeune": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE", "letterhead_address": "CAMP LEJEUNE NC 28542-0000"},
    "mcb camp lejeune": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE", "letterhead_address": "CAMP LEJEUNE NC 28542-0000"},
    "marine corps base camp lejeune": {"letterhead_top_line": "UNITED STATES MARINE CORPS", "letterhead_activity": "MARINE CORPS BASE CAMP LEJEUNE", "letterhead_address": "CAMP LEJEUNE NC 28542-0000"},
}
_LETTERHEAD_BY_FROM = {
    "Commanding Officer, Marine Corps Air Station New River": _LETTERHEAD_ALIASES["mcas new river"],
    "Commanding Officer, Marine Corps Air Station Cherry Point": _LETTERHEAD_ALIASES["mcas cherry point"],
    "Commanding Officer, Marine Corps Base Camp Lejeune": _LETTERHEAD_ALIASES["camp lejeune"],
}
_KEY_ALIASES = {"subject": "subj", "signer": "signature", "signature_name": "signature", "originator": "originator_code", "originator_code": "originator_code", "originator code": "originator_code", "office code": "originator_code", "office_code": "originator_code", "orig": "originator_code"}
_KEY_VALUE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_. -]*\s*:\s*", re.MULTILINE)
_DATE_RE = re.compile(r"\b(?:use\s+the\s+date|date)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", re.IGNORECASE)
_USE_DATE_RE = re.compile(r"\buse\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", re.IGNORECASE)

_CommandLookupAdapter = Callable[[str, str, dict[str, Any]], dict[str, Any] | None]
_SOURCE_BACKED_LOOKUP_ADAPTER: _CommandLookupAdapter | None = None


def set_source_backed_command_lookup_adapter(adapter: _CommandLookupAdapter | None) -> None:
    """Inject a deterministic source-backed lookup adapter. Production default is no live lookup."""
    global _SOURCE_BACKED_LOOKUP_ADAPTER
    _SOURCE_BACKED_LOOKUP_ADAPTER = adapter


# L.31W — wire the no-op official live lookup adapter as the default.
# The adapter always returns None (no internet, no guessing, no mutation).
# Future phases will replace it with a real implementation.
try:
    from official_command_lookup_adapter import official_command_lookup as _official_lookup  # type: ignore[import-untyped]
    set_source_backed_command_lookup_adapter(_official_lookup)
except ImportError:
    pass  # adapter module not present — safe to continue without it


def _state_path(chat_id: str) -> Path:
    return _STATE_DIR / ("".join(c for c in chat_id if c.isalnum() or c in "-_") + ".json")


def _load_state(chat_id: str) -> dict[str, Any]:
    p = _state_path(chat_id)
    if not p.exists():
        raise FileNotFoundError(f"Chat not found: {chat_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def _save_state(chat_id: str, data: dict[str, Any]) -> None:
    _state_path(chat_id).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _run_manager(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run([str(_PYTHON), str(_MANAGER)] + args, capture_output=True, text=True, timeout=120, cwd=str(_REPO_ROOT))
    if proc.returncode != 0 and not proc.stdout.strip():
        return {"success": False, "error": proc.stderr or f"exit code {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON: {proc.stdout[:200]}"}


def _emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, default=str))


def _contains_any(text: str, needles: set[str]) -> bool:
    return any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in needles)


def _classify_intent(text: str) -> str:
    t = text.lower().strip()
    if _contains_any(t, _CONFIRM_CANDIDATE_INTENTS):
        return "confirm_candidate"
    if _contains_any(t, _REJECT_CANDIDATE_INTENTS):
        return "reject_candidate"
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


def _clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v).strip(" \t\r\n,.;\"'"))


def _unit_key(v: str) -> str:
    return re.sub(r"\s+", " ", _clean(v).lower().replace("c.g.", "cg")).strip()


def _is_controlled_alias(v: str) -> bool:
    return _unit_key(v) in _UNIT_ALIASES


def _expand_unit(v: str) -> str:
    return _UNIT_ALIASES.get(_unit_key(v), _clean(v))


def _infer_letterhead(from_line: str) -> dict[str, str]:
    clean = _clean(from_line)
    if clean in _LETTERHEAD_BY_FROM:
        return dict(_LETTERHEAD_BY_FROM[clean])
    low = clean.lower()
    for k, fields in _LETTERHEAD_ALIASES.items():
        if k in low:
            return dict(fields)
    return {}


def _normalize_subject(v: str) -> str:
    v = _clean(v)
    return v if v.isupper() else v.upper()


def _normalize_body(v: str) -> str:
    v = re.sub(r"^(?:about|that)\s+", "", _clean(v), flags=re.IGNORECASE).strip()
    if not v:
        return v
    if re.match(r"^(implementing|reviewing|updating|establishing|creating)\b", v, re.IGNORECASE):
        v = f"This letter addresses {v}"
    else:
        v = v[0].upper() + v[1:]
    return v if v[-1] in ".!?" else v + "."


def _subject_from_topic(topic: str) -> str:
    clean = re.sub(r"^(reviewing|review|implementing|implementation of|about)\s+", "", _clean(topic).lower()).strip()
    if "correspondence" in clean and ("procedure" in clean or "review" in clean):
        return "REVIEW OF CORRESPONDENCE PROCEDURES"
    return _normalize_subject(clean) if clean else ""


def _canonical_key(k: str) -> str:
    compact = re.sub(r"\s+", " ", k.strip().lower().replace("-", "_"))
    return _KEY_ALIASES.get(compact, _KEY_ALIASES.get(compact.replace(" ", "_"), compact.replace(" ", "_")))


def _looks_like_key_value(text: str) -> bool:
    s = text.strip()
    return not (s.startswith("(") or s.startswith("[")) and bool(_KEY_VALUE_RE.search(s))


def _parse_explicit_key_values(text: str) -> tuple[dict[str, str], str]:
    fields: dict[str, str] = {}
    prose: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z][A-Za-z0-9_. -]*)\s*:\s*(.*?)\s*$", line)
        if not m:
            prose.append(line)
            continue
        key, val = _canonical_key(m.group(1)), _clean(m.group(2))
        if not val:
            continue
        if key == "subj":
            val = _normalize_subject(val)
        elif key == "body":
            val = _normalize_body(val)
        elif key in {"ssic", "originator_code"}:
            val = val.upper()
        fields[key] = val
    return fields, "\n".join(prose).strip()


def _extract_first_turn_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    if not any(k in raw.lower() for k in _NEW_INTENTS):
        return fields
    m = re.search(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?=(?:\s+about\b|\s+regarding\b|\s+concerning\b|[,.;]\s*(?:use|signer|signature|subject|ssic|originator|make|body)\b|$))", raw, re.I | re.S)
    if m:
        fields["from"] = _expand_unit(m.group(1))
        fields["to"] = _expand_unit(m.group(2))
        fields.update({k: v for k, v in _infer_letterhead(fields["from"]).items() if k not in fields})
    m = re.search(r"\b(?:about|regarding|concerning)\s+(.+?)(?=(?:[,.;]\s*(?:use|signer|signature|subject|ssic|originator|make|body)\b|$))", raw, re.I | re.S)
    if m and "subj" not in fields:
        subj = _subject_from_topic(m.group(1))
        if subj:
            fields["subj"] = subj
    m = _DATE_RE.search(raw) or _USE_DATE_RE.search(raw)
    if m:
        fields["date"] = _clean(m.group(1))
    m = re.search(r"\bSSIC\s*:?\s*([A-Za-z0-9.-]+)\b", raw, re.I)
    if m:
        fields["ssic"] = _clean(m.group(1)).upper()
    m = re.search(r"\b(?:originator|office)\s+code\s*:?\s*([A-Za-z0-9-]+)\b", raw, re.I)
    if m:
        fields["originator_code"] = _clean(m.group(1)).upper()
    m = re.search(r"\b(?:signer|signature)\s*:?\s*(.+?)(?=(?:,\s*(?:and\s+)?(?:subject|ssic|originator|date|make|body|use)\b|[.;]\s*$|$))", raw, re.I | re.S)
    if m:
        fields["signature"] = _clean(m.group(1))
    m = re.search(r"\bsubject\s*:?\s+(.+?)(?=(?:,\s*(?:and\s+)?(?:make|body|use|signer|signature|ssic|originator|date)\b|[.;]\s*$|$))", raw, re.I | re.S)
    if m:
        fields["subj"] = _normalize_subject(m.group(1))
    m = re.search(r"\b(?:make\s+the\s+body\s+about|body\s+about|body\s*:)\s+(.+?)(?=(?:\n\s*[A-Za-z][A-Za-z0-9_. -]*\s*:|[.;]\s*$|$))", raw, re.I | re.S)
    if m:
        fields["body"] = _normalize_body(m.group(1))
    return {k: v for k, v in fields.items() if v}


def _extract_followup_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    m = _DATE_RE.search(raw) or _USE_DATE_RE.search(raw)
    if m:
        fields["date"] = _clean(m.group(1))
    m = re.search(r"\b([A-Z](?:\.\s*)?(?:[A-Z](?:\.\s*)?)*[A-Z][A-Z .'-]*)\s+will\s+sign\s+it\b", raw, re.I)
    if m:
        fields["signature"] = _clean(m.group(1)).upper()
    m = re.search(r"\b(?:the\s+)?body\s+(?:should\s+)?(?:say|state|read)\s+(.+?)(?=(?:$|[.;]\s*$))", raw, re.I | re.S)
    if m:
        fields["body"] = _normalize_body(m.group(1))
    return {k: v for k, v in fields.items() if v}


def _extract_revision_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    raw = text.strip()
    m = re.search(r"\b(?:change|update|revise|rewrite|make)\s+(?:the\s+)?body\s+(?:to\s+)?(?:say|state|read|be)?\s*(.+?)(?=(?:$|[.;]\s*$))", raw, re.I | re.S) or re.search(r"\bbody\s*:\s*(.+)$", raw, re.I | re.S)
    if m:
        fields["body"] = _normalize_body(m.group(1))
    m = re.search(r"\b(?:change|update|revise)\s+(?:the\s+)?subject\s+(?:to\s+)?(.+?)(?=(?:$|[.;]\s*$))", raw, re.I | re.S)
    if m:
        fields["subj"] = _normalize_subject(m.group(1))
    m = re.search(r"\b(?:change|update)\s+(?:the\s+)?date\s+(?:to\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", raw, re.I)
    if m:
        fields["date"] = _clean(m.group(1))
    m = re.search(r"\b(?:change|update)\s+(?:the\s+)?(?:signer|signature)\s+(?:to\s+)?(.+?)(?=(?:$|[.;]\s*$))", raw, re.I | re.S)
    if m:
        fields["signature"] = _clean(m.group(1))
    return {k: v for k, v in fields.items() if v}


def _merge_mixed_intake_fields(text: str) -> dict[str, str]:
    explicit, prose = _parse_explicit_key_values(text)
    base = prose or text
    return {k: v for k, v in {**_extract_followup_fields(base), **_extract_first_turn_key_values(base), **explicit}.items() if v}


def _key_values_to_text(fields: dict[str, str]) -> str:
    order = ["letterhead_top_line", "letterhead_activity", "letterhead_address", "ssic", "originator_code", "from", "to", "date", "subj", "body", "signature"]
    lines = [f"{k}: {fields[k]}" for k in order if k in fields]
    lines.extend(f"{k}: {v}" for k, v in fields.items() if k not in order)
    return "\n".join(lines)


def _payload_body_text(payload: dict[str, Any]) -> str:
    body = payload.get("body") or payload.get("body_paragraphs") or ""
    return "\n".join(str(x) for x in body) if isinstance(body, list) else str(body or "")


def _maybe_infer_and_apply_ssic(session_id: str, payload: dict[str, Any] | None) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    if not isinstance(payload, dict) or payload.get("ssic"):
        return None, None
    resolved = resolve_ssic(str(payload.get("subj") or payload.get("subject") or ""), _payload_body_text(payload))
    code = str((resolved or {}).get("code") or "").strip() if isinstance(resolved, dict) else ""
    if not code:
        return None, None
    return {"code": code, "description": str((resolved or {}).get("description") or "")}, _run_manager(["apply", "--session", session_id, "--kv", f"ssic: {code}"])


def _ensure_cands(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    c = state.setdefault("source_backed_candidates", {})
    for k in ("pending", "confirmed", "rejected"):
        c.setdefault(k, [])
    return c


def _candidate_id(role: str, text: str, url: str = "") -> str:
    return "src-" + hashlib.sha1(f"{role}|{_clean(text).lower()}|{url}".encode()).hexdigest()[:12]


def _maybe_add_source_candidate(state: dict[str, Any], fields: dict[str, str]) -> dict[str, Any] | None:
    text = fields.get("from")
    if not text or _is_controlled_alias(text) or _SOURCE_BACKED_LOOKUP_ADAPTER is None:
        return None
    try:
        res = _SOURCE_BACKED_LOOKUP_ADAPTER(text, "from", state)
    except Exception:
        return None
    if not isinstance(res, dict) or not isinstance(res.get("resolved_value"), dict):
        return None
    cand = {
        "candidate_id": res.get("candidate_id") or _candidate_id("from", text, str(res.get("source_url") or "")),
        "candidate_type": res.get("candidate_type") or "command_expansion",
        "input_text": _clean(text), "field": "from", "resolved_value": dict(res.get("resolved_value") or {}),
        "source_title": res.get("source_title") or "Source-backed command result", "source_url": str(res.get("source_url") or ""),
        "source_tier": res.get("source_tier") or "unresolved", "source_limitation": res.get("source_limitation") or "Candidate requires user confirmation before applying.",
        "confidence": res.get("confidence", 0), "requires_user_confirmation": True, "status": "pending",
    }
    cands = _ensure_cands(state)
    if any(c.get("candidate_id") == cand["candidate_id"] for c in cands["rejected"]):
        return None
    if not any(c.get("candidate_id") == cand["candidate_id"] for c in cands["pending"]):
        cands["pending"].append(cand)
    return cand


def _pending(state: dict[str, Any]) -> dict[str, Any] | None:
    p = _ensure_cands(state).get("pending", [])
    return p[-1] if p else None


def _apply_candidate(session_id: str, state: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(cand.get("resolved_value") or {})
    if cand.get("field") != "from" or cand.get("source_tier") != "official_live":
        for k in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
            resolved.pop(k, None)
    r = _run_manager(["apply", "--session", session_id, "--kv", _key_values_to_text({k: str(v) for k, v in resolved.items() if v})])
    if r.get("success"):
        cands = _ensure_cands(state)
        cands["pending"] = [c for c in cands["pending"] if c.get("candidate_id") != cand.get("candidate_id")]
        cand = dict(cand); cand["status"] = "confirmed"
        if not any(c.get("candidate_id") == cand["candidate_id"] for c in cands["confirmed"]):
            cands["confirmed"].append(cand)
    return r


def _reject_candidate(state: dict[str, Any], cand: dict[str, Any]) -> None:
    cands = _ensure_cands(state)
    cands["pending"] = [c for c in cands["pending"] if c.get("candidate_id") != cand.get("candidate_id")]
    rej = dict(cand); rej["status"] = "rejected"
    if not any(c.get("candidate_id") == rej["candidate_id"] for c in cands["rejected"]):
        cands["rejected"].append(rej)


def _plain_missing(missing: list[Any]) -> list[str]:
    out: list[str] = []
    for item in missing:
        raw = str(item)
        if raw.lower() in _OPTIONAL_FIELDS:
            continue
        val = _PLAIN_MISSING.get(raw, raw.replace("_", " "))
        if val not in out:
            out.append(val)
    return out


def _missing_prompt(missing: list[Any]) -> str:
    plain = _plain_missing(missing)
    if not plain:
        return "I have the optional routing details handled. Provide any remaining required details in plain English."
    if set(plain) == {"date", "who will sign it", "body text"}:
        return "I have the routing basics. What date should I use, who will sign it, and what should the body say?"
    return f"I have part of the letter. I still need: {', '.join(plain[:5])}."


def _phase(ready: dict[str, Any], preview: dict[str, Any]) -> str:
    if ready.get("approved_ready"):
        return "approved_ready"
    if preview.get("mode") == "draft_preview" or (ready.get("validation_ready") and not ready.get("approved_ready")):
        return "draft_preview"
    if preview.get("mode") == "build_status":
        return "build_status"
    return "build_status"


def _next_step(phase: str, ready: dict[str, Any], preview: dict[str, Any]) -> str:
    if phase == "approved_ready":
        return "Draft is approved and ready. Say 'make the PDF' to render."
    if phase == "draft_preview":
        return "Draft is approved. Say 'make the PDF' to render." if (preview.get("approval") or {}).get("approval_current") else "Draft preview is ready. Review it and say 'looks good' to approve."
    missing = (ready.get("render_gate") or {}).get("missing", [])
    if missing:
        return _missing_prompt(missing)
    q = (ready.get("next_action") or {}).get("question")
    if q:
        if "ssic" in str(q).lower() or "originator" in str(q).lower():
            return "I have the optional routing details handled. Provide any remaining required details in plain English."
        return str(q)
    return "Keep providing details to complete the letter."


def _assistant_response(phase: str, ready: dict[str, Any], preview: dict[str, Any], *, action: str = "", pdf_path: str = "", blocked_reason: str = "", pending_candidate: dict[str, Any] | None = None) -> str:
    if pending_candidate:
        title = pending_candidate.get("source_title") or "source-backed result"
        res = pending_candidate.get("resolved_value") or {}
        field = pending_candidate.get("field") or "from"
        val = res.get(field) or res.get("unit_identity") or "the command"
        limitation = pending_candidate.get("source_limitation") or "Confirm before I apply it, or reject it and provide the full command name."
        return f"I found a source-backed {field.capitalize()} candidate from {title}: {val}. {limitation}"
    if phase == "rendered":
        return f"Done! Your PDF is ready at {pdf_path}. You can start a new chat if you need another letter."
    if phase == "approved_ready":
        return "Your draft is approved and everything looks good. Say 'make the PDF' and I'll generate it."
    if phase == "draft_preview":
        return "Your draft is approved. Say 'make the PDF' and I'll generate it." if (preview.get("approval") or {}).get("approval_current") else "Your draft is ready for review. You can say 'looks good' to approve it, or tell me what you'd like to change."
    if action == "approve":
        return "Your draft is approved! You can now say 'make the PDF' and I'll generate it."
    if action == "render":
        return f"I can't make the PDF yet. {blocked_reason or 'The draft needs approval and all required fields must be ready.'} Review the draft and say 'looks good' to approve it first."
    if action == "revise":
        return "I've updated the draft. Please review the preview and say 'looks good' when you're ready to approve it."
    missing = (ready.get("render_gate") or {}).get("missing", [])
    if missing:
        return _missing_prompt(missing)
    return "Got it. Keep providing details and I'll build the draft for you."


def _status(session_id: str) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    preview = _run_manager(["preview", "--session", session_id])
    ready = _run_manager(["ready", "--session", session_id])
    ph = _phase(ready, preview)
    return preview, ready, ph, _next_step(ph, ready, preview)


def _digest(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _run_say(session_id: str, text: str, state: dict[str, Any]) -> dict[str, Any]:
    fields = _merge_mixed_intake_fields(text)
    pending = _maybe_add_source_candidate(state, fields) if fields else None
    if fields:
        r = _run_manager(["apply", "--session", session_id, "--kv", _key_values_to_text(fields)])
    elif _looks_like_key_value(text):
        r = _run_manager(["apply", "--session", session_id, "--kv", text])
    else:
        r = _run_manager(["say", "--session", session_id, "--text", text])
    ssic, ssic_r = _maybe_infer_and_apply_ssic(session_id, r.get("payload"))
    if ssic_r and ssic_r.get("success"):
        r = ssic_r
    preview, ready, ph, step = _status(session_id)
    return {"success": r.get("success", False), "intent": "say", "phase": ph, "message": f"I've noted that. Current phase: {ph.replace('_', ' ')}. {step}" if r.get("success") else r.get("error", "Say failed"), "assistant_response": _assistant_response(ph, ready, preview, pending_candidate=pending), "preview_text": preview.get("preview_text"), "next_step": step, "payload": r.get("payload"), "validation_summary": r.get("validation_summary"), "warning_summary": r.get("warning_summary"), "proposed_kv": r.get("proposed_kv"), "extracted_kv": fields or None, "ssic_inference": ssic, "source_backed_candidate": pending, "source_backed_candidates": _ensure_cands(state), "validation_ready": ready.get("validation_ready", False), "approved_ready": ready.get("approved_ready", False), "render_gate": ready.get("render_gate"), "error": r.get("error")}


def _run_revise(session_id: str, text: str) -> dict[str, Any]:
    before_ready = _run_manager(["ready", "--session", session_id])
    before_preview = _run_manager(["preview", "--session", session_id])
    before_hash = _digest(before_preview.get("payload") or {})
    fields = _extract_revision_fields(text)
    r = _run_manager(["apply", "--session", session_id, "--kv", _key_values_to_text(fields)]) if fields else _run_manager(["revise", "--session", session_id, "--text", text])
    preview, ready, ph, step = _status(session_id)
    after_payload = r.get("payload") or preview.get("payload") or {}
    changed = r.get("payload_changed")
    if changed is None:
        changed = _digest(after_payload) != before_hash
    cleared = r.get("approval_cleared")
    if cleared is None:
        cleared = bool(before_ready.get("approved_ready") and changed and not ready.get("approved_ready", False))
    resp = "I wasn't able to apply that change to the draft. Try a supported change such as changing the body, subject, signer, or date." if not r.get("success") else ("I understood the request, but nothing in the draft was changed. Try changing the body, subject, signer, or date." if not changed else _assistant_response(ph, ready, preview, action="revise"))
    return {"success": r.get("success", False), "intent": "revise", "phase": ph, "message": f"Revised draft. Payload changed: {changed}. Approval cleared: {cleared}. Current phase: {ph.replace('_', ' ')}. {step}" if r.get("success") else r.get("error", "Revise failed"), "assistant_response": resp, "preview_text": preview.get("preview_text"), "next_step": step, "payload": after_payload, "approval_cleared": cleared, "payload_changed": changed, "validation_ready": ready.get("validation_ready", False), "approved_ready": ready.get("approved_ready", False), "error": r.get("error")}


def _run_confirm_candidate(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    cand = _pending(state)
    if not cand:
        preview, ready, ph, step = _status(session_id)
        return {"success": False, "intent": "confirm_candidate", "phase": ph, "message": "No pending source-backed candidate to confirm.", "assistant_response": "I don't have a pending source-backed command candidate to apply.", "next_step": step, "source_backed_candidates": _ensure_cands(state), "error": "No pending candidate."}
    r = _apply_candidate(session_id, state, cand)
    ssic, ssic_r = _maybe_infer_and_apply_ssic(session_id, r.get("payload"))
    if ssic_r and ssic_r.get("success"):
        r = ssic_r
    preview, ready, ph, step = _status(session_id)
    # Normalize missing-detail prompt after candidate confirmation:
    # when date, signer, and body are all still missing, use the
    # accepted combined plain-English prompt instead of the raw
    # next_action question (which may only mention body).
    payload = r.get("payload") or {}
    if ph == "build_status" and not payload.get("date") and not payload.get("signature") and not payload.get("body"):
        step = "I have the routing basics. What date should I use, who will sign it, and what should the body say?"
    return {"success": r.get("success", False), "intent": "confirm_candidate", "phase": ph, "message": f"Confirmed source-backed candidate. Current phase: {ph.replace('_', ' ')}. {step}" if r.get("success") else r.get("error", "Candidate apply failed"), "assistant_response": "I've applied the confirmed source-backed command result. " + step if r.get("success") else "I couldn't apply that source-backed candidate.", "preview_text": preview.get("preview_text"), "next_step": step, "payload": payload, "confirmed_candidate": cand, "source_backed_candidates": _ensure_cands(state), "ssic_inference": ssic, "validation_ready": ready.get("validation_ready", False), "approved_ready": ready.get("approved_ready", False), "error": r.get("error")}


def _run_reject_candidate(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    cand = _pending(state)
    if cand:
        _reject_candidate(state, cand)
    preview, ready, ph, step = _status(session_id)
    msg = "Rejected source-backed candidate. Please provide the full command name or letterhead." if cand else "No pending source-backed candidate to reject."
    return {"success": bool(cand), "intent": "reject_candidate", "phase": ph, "message": msg, "assistant_response": msg, "preview_text": preview.get("preview_text"), "next_step": step, "rejected_candidate": cand, "source_backed_candidates": _ensure_cands(state), "validation_ready": ready.get("validation_ready", False), "approved_ready": ready.get("approved_ready", False), "error": None if cand else "No pending candidate."}


def _run_approve(session_id: str) -> dict[str, Any]:
    r = _run_manager(["approve", "--session", session_id])
    ready = _run_manager(["ready", "--session", session_id])
    approved = r.get("approved_for_finalize", False)
    ar = ready.get("approved_ready", False)
    ph = "approved_ready" if approved and ar else ("draft_preview" if approved else "blocked")
    step = "Draft is approved and ready. Say 'make the PDF' to render." if ph == "approved_ready" else ("Draft approved, but validation is not yet ready. Provide missing fields." if approved else r.get("error", "Approval failed. Ensure preview gate is met first."))
    return {"success": r.get("success", False), "intent": "approve", "phase": ph, "message": f"Draft approved. Current phase: {ph.replace('_', ' ')}. {step}" if approved else step, "assistant_response": _assistant_response(ph, ready, {}, action="approve", blocked_reason=step if ph == "blocked" else ""), "next_step": step, "approved_for_finalize": approved, "approved_ready": ar, "validation_ready": ready.get("validation_ready", False), "approval": r.get("approval"), "payload": r.get("payload"), "error": r.get("error")}


def _run_preview(session_id: str) -> dict[str, Any]:
    preview, ready, ph, step = _status(session_id)
    return {"success": preview.get("success", False), "intent": "preview", "phase": ph, "message": f"Current phase: {ph.replace('_', ' ')}. {step}", "assistant_response": _assistant_response(ph, ready, preview), "preview_text": preview.get("preview_text"), "next_step": step, "mode": preview.get("mode"), "approval": preview.get("approval"), "approved_ready": ready.get("approved_ready", False), "validation_ready": ready.get("validation_ready", False), "payload": preview.get("payload"), "error": preview.get("error")}


def _run_ready(session_id: str) -> dict[str, Any]:
    preview, ready, ph, step = _status(session_id)
    return {"success": ready.get("success", False), "intent": "ready", "phase": ph, "message": f"Current phase: {ph.replace('_', ' ')}. {step}", "assistant_response": _assistant_response(ph, ready, preview), "approved_ready": ready.get("approved_ready", False), "validation_ready": ready.get("validation_ready", False), "next_step": step, "approval": ready.get("approval"), "render_gate": ready.get("render_gate"), "payload": ready.get("payload"), "error": ready.get("error")}


def _run_render(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    ready = _run_manager(["ready", "--session", session_id])
    if not ready.get("approved_ready", False):
        ph = _phase(ready, {"mode": "build_status"}); step = _next_step(ph, ready, {"mode": "build_status"})
        return {"success": False, "intent": "render", "phase": ph, "message": f"Cannot render yet. Current phase: {ph.replace('_', ' ')}. {step}", "assistant_response": _assistant_response("blocked", ready, {}, action="render", blocked_reason=ready.get("error") or "The draft isn't approved or validation isn't ready yet."), "next_step": step, "approved_ready": False, "validation_ready": ready.get("validation_ready", False), "error": ready.get("error") or "Render blocked: not approved_ready."}
    out = _REPO_ROOT / "tmp"; out.mkdir(parents=True, exist_ok=True)
    pdf = Path(state.get("out_path")) if state.get("out_path") else out / f"chat_{session_id}.pdf"
    r = _run_manager(["render", "--session", session_id, "--out", str(pdf)])
    if r.get("success") and pdf.exists() and pdf.stat().st_size > 0:
        state["last_pdf_path"] = str(pdf); state["rendered_at"] = r.get("message", ""); _save_state(state["chat_id"], state)
        return {"success": True, "intent": "render", "phase": "rendered", "message": f"PDF rendered successfully: {pdf}", "assistant_response": _assistant_response("rendered", {}, {}, pdf_path=str(pdf)), "pdf_path": str(pdf), "pdf_size": pdf.stat().st_size, "next_step": "Letter is complete. You can start a new chat for another letter.", "payload": r.get("payload"), "error": None}
    return {"success": False, "intent": "render", "phase": "blocked", "message": r.get("error", "Render failed."), "assistant_response": _assistant_response("blocked", {}, {}, action="render", blocked_reason=r.get("error") or "Render failed."), "next_step": "Check status and ensure draft is approved and validation is ready.", "error": r.get("error", "Render failed.")}


def _process_turn(chat_id: str, text: str, state: dict[str, Any]) -> dict[str, Any]:
    sid = state["session_id"]
    intent = _classify_intent(text)
    state.setdefault("history", []).append({"role": "user", "text": text, "intent": intent})
    state["history"] = state["history"][-20:]
    if intent == "confirm_candidate": result = _run_confirm_candidate(sid, state)
    elif intent == "reject_candidate": result = _run_reject_candidate(sid, state)
    elif intent == "revise": result = _run_revise(sid, text)
    elif intent == "approve": result = _run_approve(sid)
    elif intent == "preview": result = _run_preview(sid)
    elif intent == "status": result = _run_ready(sid)
    elif intent == "render": result = _run_render(sid, state)
    else: result = _run_say(sid, text, state)
    result.setdefault("source_backed_candidates", _ensure_cands(state))
    state["history"].append({"role": "assistant", "phase": result.get("phase"), "message": result.get("message")})
    _save_state(chat_id, state)
    return result


def _start_chat(out: str | None = None) -> dict[str, Any]:
    r = _run_manager(["new"])
    if not r.get("success"):
        return {"success": False, "command": "start", "message": f"Failed to create session: {r.get('error')}", "error": r.get("error")}
    chat_id = f"chat-{uuid.uuid4().hex[:12]}"
    state = {"chat_id": chat_id, "session_id": r["session_id"], "created_at": r.get("message", ""), "history": [], "last_pdf_path": None, "rendered_at": None, "source_backed_candidates": {"pending": [], "confirmed": [], "rejected": []}}
    if out: state["out_path"] = str(out)
    _save_state(chat_id, state)
    return {"success": True, "command": "start", "chat_id": chat_id, "session_id": r["session_id"], "message": "Chat started.", "next_step": "Tell me what letter you need.", "source_backed_candidates": state["source_backed_candidates"], "error": None}


def _send_chat_turn(chat_id: str, text: str, out: str | None = None) -> dict[str, Any]:
    try: state = _load_state(chat_id)
    except FileNotFoundError as exc: return {"success": False, "command": "chat", "error": str(exc)}
    _ensure_cands(state)
    if out is not None:
        state["out_path"] = str(out); _save_state(chat_id, state)
    r = _process_turn(chat_id, text, state)
    keys = ["intent", "phase", "message", "assistant_response", "preview_text", "next_step", "pdf_path", "pdf_size", "payload_changed", "approval_cleared", "validation_ready", "approved_ready", "payload", "extracted_kv", "ssic_inference", "source_backed_candidate", "confirmed_candidate", "rejected_candidate", "source_backed_candidates", "error"]
    return {"success": r.get("success", False), "command": "chat", "chat_id": chat_id, "session_id": state["session_id"], **{k: r.get(k) for k in keys}}


def _get_chat_status(chat_id: str) -> dict[str, Any]:
    try: state = _load_state(chat_id)
    except FileNotFoundError as exc: return {"success": False, "command": "status", "error": str(exc)}
    _ensure_cands(state)
    preview, ready, ph, step = _status(state["session_id"])
    return {"success": True, "command": "status", "chat_id": chat_id, "session_id": state["session_id"], "phase": ph, "message": f"Current phase: {ph.replace('_', ' ')}. {step}", "assistant_response": _assistant_response(ph, ready, preview, pending_candidate=_pending(state)), "preview_text": preview.get("preview_text"), "next_step": step, "approved_ready": ready.get("approved_ready", False), "validation_ready": ready.get("validation_ready", False), "last_pdf_path": state.get("last_pdf_path"), "history_count": len(state.get("history", [])), "source_backed_candidates": state.get("source_backed_candidates"), "error": None}


def _reset_chat(chat_id: str) -> dict[str, Any]:
    try: state = _load_state(chat_id)
    except FileNotFoundError as exc: return {"success": False, "command": "reset", "error": str(exc)}
    r = _run_manager(["new"])
    if not r.get("success"): return {"success": False, "command": "reset", "error": f"Failed to create new session: {r.get('error')}"}
    state.update({"session_id": r["session_id"], "history": [], "last_pdf_path": None, "rendered_at": None, "source_backed_candidates": {"pending": [], "confirmed": [], "rejected": []}})
    _save_state(chat_id, state)
    return {"success": True, "command": "reset", "chat_id": chat_id, "session_id": r["session_id"], "message": f"Chat reset with new session {r['session_id']}.", "assistant_response": "I've reset the chat. You can start a new letter request whenever you're ready.", "next_step": "Tell me what letter you need.", "source_backed_candidates": state["source_backed_candidates"], "error": None}


def start_secnav_chat(chat_id: str | None = None, out: str | None = None) -> dict[str, Any]:
    if chat_id:
        try: _load_state(chat_id); return _get_chat_status(chat_id)
        except FileNotFoundError: pass
    return _start_chat(out=out)


def send_secnav_chat_turn(chat_id: str, text: str, out: str | None = None) -> dict[str, Any]:
    return _send_chat_turn(chat_id, text, out=out)


def get_secnav_chat_status(chat_id: str) -> dict[str, Any]:
    return _get_chat_status(chat_id)


def reset_secnav_chat(chat_id: str) -> dict[str, Any]:
    return _reset_chat(chat_id)


def format_tool_response_for_hermes(result: dict[str, Any]) -> str:
    if not result.get("success"):
        return f"I couldn't complete that. {result.get('error') or 'Something went wrong.'}"
    lines: list[str] = []
    if result.get("assistant_response"): lines.append(result["assistant_response"])
    if result.get("phase") == "rendered":
        if result.get("pdf_path"): lines.append(f"PDF: {result['pdf_path']}" + (f" ({result['pdf_size']} bytes)" if result.get("pdf_size") else ""))
        return "\n".join(lines)
    if result.get("preview_text"): lines.append(f"Preview:\n{result['preview_text']}")
    if result.get("next_step") and not lines: lines.append(result["next_step"])
    return "\n".join(lines) if lines else result.get("message", "Done.")


def cmd_start(_args: argparse.Namespace) -> None: _emit(_start_chat())

def cmd_chat(args: argparse.Namespace) -> None:
    if not getattr(args, "chat_id", None): _emit({"success": False, "command": "chat", "error": "--chat-id required"}); return
    _emit(_send_chat_turn(args.chat_id, getattr(args, "text", "")))

def cmd_status(args: argparse.Namespace) -> None:
    if not getattr(args, "chat_id", None): _emit({"success": False, "command": "status", "error": "--chat-id required"}); return
    _emit(_get_chat_status(args.chat_id))

def cmd_reset(args: argparse.Namespace) -> None:
    if not getattr(args, "chat_id", None): _emit({"success": False, "command": "reset", "error": "--chat-id required"}); return
    _emit(_reset_chat(args.chat_id))

_EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}

def cmd_interactive(args: argparse.Namespace) -> None:
    chat_id = getattr(args, "chat_id", None)
    if not chat_id:
        r = _start_chat(out=getattr(args, "out", None)); chat_id = r.get("chat_id"); _emit(r)
    state = _load_state(chat_id)
    for line in sys.stdin:
        text = line.strip()
        if not text: continue
        if text.lower() in _EXIT_COMMANDS: _emit({"success": True, "command": "interactive", "chat_id": chat_id, "message": "Goodbye.", "error": None}); break
        r = _process_turn(chat_id, text, state)
        print(json.dumps(r, indent=2, default=str) if getattr(args, "json_lines", False) else r.get("assistant_response", r.get("message", "")), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes Chat Builder")
    sp = parser.add_subparsers(dest="command", required=True)
    sp.add_parser("start")
    p = sp.add_parser("chat"); p.add_argument("--chat-id", required=True); p.add_argument("--text", required=True)
    p = sp.add_parser("status"); p.add_argument("--chat-id", required=True)
    p = sp.add_parser("reset"); p.add_argument("--chat-id", required=True)
    p = sp.add_parser("interactive"); p.add_argument("--chat-id", default=None); p.add_argument("--out", default=None); p.add_argument("--json-lines", action="store_true")
    args = parser.parse_args(argv)
    try:
        {"start": cmd_start, "chat": cmd_chat, "status": cmd_status, "reset": cmd_reset, "interactive": cmd_interactive}[args.command](args)
    except Exception as exc:
        _emit({"success": False, "command": getattr(args, "command", "unknown"), "chat_id": getattr(args, "chat_id", None), "error": str(exc)})
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
