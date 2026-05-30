#!/usr/bin/env python3
"""
CCI Context Resolver

Resolves a canonical context object from a correspondence JSON payload and
optional user-supplied answers.

Public API:
    resolve_context(payload, user_answers=None) -> tuple[dict, list[str]]
        Returns (context, warnings).

    The context dict follows the CCI Context Schema V1 documented in
    rules_v6/CCI/cci_context_schema.json.

    Warnings are non-blocking informational strings describing inferred or
    missing context.

CLI:
    python src/context_resolver.py <payload.json>

    Prints resolved context JSON (pretty) and warnings (if any), then PASS.
    Exit 0 in all v1 cases.  No hard errors are returned.

Design choices:
    - Read-only.  Does not modify payload.
    - user_answers is optional.  When provided, explicit answers take priority
      over inference, but payload fields take priority over everything.
    - Unknown or null fields are represented as null (JSON) / None (Python).
    - Inference uses keyword heuristics only; false positives are possible,
      hence every inference is accompanied by a warning.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = "CCI_CONTEXT_V1"

_DOC_TYPE_ALIASES = {
    "dt_std_ltr": "standard_letter",
    "standard_letter": "standard_letter",
    "dt_mul_ltr": "multiple_address_letter",
    "multiple_address_letter": "multiple_address_letter",
    "dt_endorsement": "endorsement",
    "endorsement": "endorsement",
    "joint_letter": "joint_letter",
    "memorandum_for_record": "memorandum_for_record",
    "mfr": "memorandum_for_record",
    "from_to_memo": "from_to_memo",
    "plain_paper_memo": "plain_paper_memo",
    "letterhead_memo": "letterhead_memo",
    "decision_memo": "decision_memo",
    "memo_of_agreement": "memo_of_agreement",
    "moa": "memo_of_agreement",
    "memo_of_understanding": "memo_of_understanding",
    "mou": "memo_of_understanding",
}

_COMPONENT_ALIASES = {
    "navy": "navy",
    "usn": "navy",
    "naval": "navy",
    "marine_corps": "marine_corps",
    "usmc": "marine_corps",
    "marines": "marine_corps",
    "joint": "joint",
    "don_secretariat": "don_secretariat",
    "secretariat": "don_secretariat",
    "don": "don_secretariat",
}

_MARINE_CORPS_KEYWORDS = [
    "usmc", "marine corps", "marines", "sgt", "sgtmaj", "master gunnery sergeant",
    "gunnery sergeant", "first sergeant", "lance corporal", "staff sergeant",
]

_NAVY_KEYWORDS = [
    "usn", "navy", "sailor", "cdr", "lcdr", "ltjg", "ens", "opnav",
    "navsea", "navsup", "bupers",
]

_REPLY_ACTION_KEYWORDS = [
    "reply", "respond", "answer", "inquiry", "further information",
    "information request", "respond to", "reply to", "take action",
    "action required", "complete action", "follow up", "coordinate",
    "coordination", "feedback", "comment", "input", "confirmation",
    "verify", "submit", "send", "provide", "forward", "distribute",
    "review", "evaluate", "assess", "approve", "endorse", "signature",
    "contact", "reach out",
]

_DEADLINE_KEYWORDS = [
    "deadline", "due by", "no later than", "submit by", "complete by",
    "not later than", "by ", "not to exceed", "nlt",
]

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EDPI_RE = re.compile(r"\b\d{10}\b")
_EDPI_CONTEXT_RE = re.compile(r"\b(EDIPI|DoD ID|DOD ID|dodi)\b", re.IGNORECASE)
_PII_PHRASES = ["personally identifiable information", "PII", "social security", "ssn"]
_CLASSIFIED_RE = re.compile(r"\b(classified|SECRET|TOP SECRET|CONFIDENTIAL|TS//)\b", re.IGNORECASE)
_CUI_FOUO_RE = re.compile(r"\b(CUI|FOUO|FOR OFFICIAL USE ONLY)\b", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b(e[-\s]?mail|email)\b", re.IGNORECASE)
_FAX_RE = re.compile(r"\b(fax)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return "\n".join(str(v) for v in value if v)
    text = str(value)
    return text.strip() or None


def _extract_body_text(payload: dict[str, Any]) -> str:
    """Extract body text from payload body or body_paragraphs."""
    raw = payload.get("body") or payload.get("body_paragraphs") or ""
    if isinstance(raw, list):
        return "\n".join(str(v) for v in raw if v)
    return str(raw)


def _resolve_doc_type(payload: dict[str, Any], user_answers: dict[str, Any] | None) -> tuple[str | None, list[str]]:
    warnings = []
    # Priority: payload explicit
    for key in ("doc_type", "correspondence_type", "type"):
        raw = payload.get(key)
        if raw is not None:
            normalized = _DOC_TYPE_ALIASES.get(str(raw).strip().lower())
            if normalized:
                return normalized, warnings
            else:
                warnings.append(f"Unknown doc_type value '{raw}'; normalizing to 'unknown'")
                return "unknown", warnings
    # Priority: user_answers
    if user_answers:
        for key in ("doc_type", "correspondence_type", "type"):
            raw = user_answers.get(key)
            if raw is not None:
                normalized = _DOC_TYPE_ALIASES.get(str(raw).strip().lower())
                if normalized:
                    warnings.append(f"doc_type inferred from user_answers: '{raw}' -> '{normalized}'")
                    return normalized, warnings
                else:
                    warnings.append(f"Unknown user_answers doc_type '{raw}'; normalizing to 'unknown'")
                    return "unknown", warnings
    warnings.append("doc_type not found in payload or user_answers; setting to unknown")
    return "unknown", warnings


def _resolve_service(payload: dict[str, Any], user_answers: dict[str, Any] | None, body_text: str) -> tuple[str | None, list[str]]:
    warnings = []
    body_lower = body_text.lower()

    # Priority: payload explicit component
    raw_component = payload.get("component")
    if raw_component is not None and isinstance(raw_component, dict):
        raw = raw_component.get("service") or raw_component.get("component")
        if raw is not None:
            normalized = _COMPONENT_ALIASES.get(str(raw).strip().lower())
            if normalized:
                return normalized, warnings
            else:
                warnings.append(f"Unknown payload component.service '{raw}'; normalizing to unknown")
                return "unknown", warnings

    # Priority: user_answers explicit
    if user_answers:
        for key in ("component", "service"):
            raw = user_answers.get(key)
            if raw is not None:
                normalized = _COMPONENT_ALIASES.get(str(raw).strip().lower())
                if normalized:
                    warnings.append(f"component.service inferred from user_answers: '{raw}' -> '{normalized}'")
                    return normalized, warnings
                else:
                    warnings.append(f"Unknown user_answers component '{raw}'; normalizing to unknown")
                    return "unknown", warnings

    # Inference from body text
    marine_score = sum(1 for kw in _MARINE_CORPS_KEYWORDS if kw in body_lower)
    navy_score = sum(1 for kw in _NAVY_KEYWORDS if kw in body_lower)

    if marine_score > 0 and navy_score > 0:
        warnings.append(f"component.service inferred as 'joint' from mixed Navy ({navy_score}) and Marine Corps ({marine_score}) keywords in body")
        return "joint", warnings
    elif marine_score > 0:
        warnings.append(f"component.service inferred as 'marine_corps' from body keywords (score={marine_score})")
        return "marine_corps", warnings
    elif navy_score > 0:
        warnings.append(f"component.service inferred as 'navy' from body keywords (score={navy_score})")
        return "navy", warnings

    warnings.append("component.service could not be determined from payload or body; setting to unknown")
    return "unknown", warnings


def _resolve_classification_context(payload: dict[str, Any], body_text: str) -> str | None:
    body_lower = body_text.lower()
    if _CLASSIFIED_RE.search(body_text):
        return "classified"
    if _CUI_FOUO_RE.search(body_text):
        return "fouo_cui"
    if payload.get("classification") or payload.get("classified"):
        return "classified"
    if payload.get("cui") or payload.get("fouo"):
        return "fouo_cui"
    return "unclassified"


def _resolve_routing(payload: dict[str, Any]) -> dict[str, Any]:
    via_raw = payload.get("via")
    copy_to_raw = payload.get("copy_to") or payload.get("copyto") or payload.get("copy")
    distribution_raw = payload.get("distribution")
    to_raw = payload.get("to")
    mode = payload.get("distribution_mode")

    def _count(value: Any) -> int | None:
        if value is None:
            return 0
        if isinstance(value, list):
            return len([v for v in value if v])
        text = str(value).strip()
        return 1 if text else 0

    via_count = _count(via_raw)
    copy_to_count = _count(copy_to_raw)
    action_count = _count(to_raw) + via_count

    distribution_mode = None
    if mode:
        m = str(mode).strip().lower()
        if m in ("to_only",):
            distribution_mode = "to_only"
        elif m in ("distribution_only",):
            distribution_mode = "distribution_only"
        elif m in ("to_plus_distribution",):
            distribution_mode = "to_plus_distribution"

    return {
        "via_required": None,
        "chain_of_command_expected": None,
        "dirlauth_authorized": None,
        "tv5_tasker_used": None,
        "distribution_mode": distribution_mode,
        "action_addressee_count": action_count,
        "copy_to_count": copy_to_count,
        "via_count": via_count,
    }


def _resolve_response(body_text: str) -> dict[str, Any]:
    body_lower = body_text.lower()
    reply_expected = False
    action_required = False
    deadline_required = False
    deadline_date = None
    poc_required = False

    for keyword in _REPLY_ACTION_KEYWORDS:
        if keyword.lower() in body_lower:
            reply_expected = True
            action_required = True
            poc_required = True
            break

    for keyword in _DEADLINE_KEYWORDS:
        if keyword.lower() in body_lower:
            deadline_required = True
            break

    # Try to extract a date near deadline keywords
    if deadline_required:
        match = _DATE_RE.search(body_text)
        if match:
            deadline_date = match.group(1)

    return {
        "reply_expected": reply_expected or None,
        "action_required": action_required or None,
        "deadline_required": deadline_required or None,
        "deadline_date": deadline_date,
        "point_of_contact_required": poc_required or None,
    }


def _resolve_privacy_security(payload: dict[str, Any], body_text: str) -> tuple[dict[str, Any], list[str]]:
    warnings = []
    body_lower = body_text.lower()

    contains_ssn = bool(_SSN_RE.search(body_text))
    contains_edipi = bool(_EDPI_RE.search(body_text) and _EDPI_CONTEXT_RE.search(body_text))
    contains_pii = contains_ssn or contains_edipi or any(p.lower() in body_lower for p in _PII_PHRASES)
    classified_or_sensitive = bool(_CLASSIFIED_RE.search(body_text))
    cui_fouo = bool(_CUI_FOUO_RE.search(body_text))
    email_transmission = bool(_EMAIL_RE.search(body_text)) or bool(payload.get("email")) or bool(payload.get("e_mail"))
    fax_transmission = bool(_FAX_RE.search(body_text)) or bool(payload.get("fax"))

    if contains_ssn:
        warnings.append("Privacy/security: SSN pattern detected in body")
    if contains_edipi:
        warnings.append("Privacy/security: EDIPI / DoD ID pattern detected in body")
    if classified_or_sensitive:
        warnings.append("Privacy/security: classification or sensitive wording detected")
    if cui_fouo:
        warnings.append("Privacy/security: CUI or FOUO wording detected")

    return {
        "contains_pii": contains_pii or None,
        "contains_ssn": contains_ssn or None,
        "contains_edipi": contains_edipi or None,
        "classified_or_sensitive": classified_or_sensitive or None,
        "cui_fouo": cui_fouo or None,
        "email_transmission": email_transmission or None,
        "fax_transmission": fax_transmission or None,
    }, warnings


def _resolve_audience(payload: dict[str, Any], body_text: str) -> tuple[dict[str, Any], list[str]]:
    warnings = []
    body_lower = body_text.lower()

    congressional = bool(re.search(r"\b(congress|congressional|senator|representative|house of representatives)\b", body_text, re.IGNORECASE))
    civilian_agency = bool(re.search(r"\b(civilian agency|federal agency|government agency)\b", body_text, re.IGNORECASE))
    business = bool(re.search(r"\b(business|company|vendor|contractor|contract)\b", body_text, re.IGNORECASE))
    individual = bool(re.search(r"\b(individual|personal matter)\b", body_text, re.IGNORECASE))
    nato = bool(re.search(r"\b(nato)\b", body_text, re.IGNORECASE))

    primary = "unknown"
    if congressional:
        primary = "congress"
    elif civilian_agency:
        primary = "civilian_agency"
    elif business:
        primary = "business"
    elif nato:
        primary = "nato"
    elif individual:
        primary = "individual"

    external = primary in ("congress", "civilian_agency", "business", "individual", "nato")

    if congressional:
        warnings.append("Audience: congressional correspondence detected")
    if civilian_agency:
        warnings.append("Audience: civilian agency reference detected")
    if business:
        warnings.append("Audience: business/vendor reference detected")

    return {
        "primary_audience": primary,
        "external_release": external or None,
        "congressional_correspondence": congressional or None,
        "foia_expected": congressional or None,
    }, warnings


def _resolve_correction_memory(payload: dict[str, Any], user_answers: dict[str, Any] | None) -> dict[str, Any]:
    profile = None
    corrections = []
    conflicts = []

    cm = payload.get("correction_memory") or {}
    if isinstance(cm, dict):
        profile = cm.get("active_profile") or cm.get("profile")
        corrections = cm.get("session_corrections_applied") or []
        conflicts = cm.get("pending_conflicts") or []

    if user_answers:
        cm2 = user_answers.get("correction_memory") or {}
        if isinstance(cm2, dict):
            if cm2.get("active_profile"):
                profile = cm2["active_profile"]
            if cm2.get("session_corrections_applied"):
                corrections = cm2["session_corrections_applied"]
            if cm2.get("pending_conflicts"):
                conflicts = cm2["pending_conflicts"]

    return {
        "active_profile": profile,
        "session_corrections_applied": corrections if isinstance(corrections, list) else [],
        "pending_conflicts": conflicts if isinstance(conflicts, list) else [],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_context(payload: dict[str, Any], user_answers: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    """Resolve a canonical CCI context object from payload and optional user answers."""
    warnings: list[str] = []
    body_text = _extract_body_text(payload)

    doc_type, w1 = _resolve_doc_type(payload, user_answers)
    warnings.extend(w1)

    service, w2 = _resolve_service(payload, user_answers, body_text)
    warnings.extend(w2)

    classification_context = _resolve_classification_context(payload, body_text)

    routing = _resolve_routing(payload)
    response = _resolve_response(body_text)
    privacy_security, w3 = _resolve_privacy_security(payload, body_text)
    warnings.extend(w3)
    audience, w4 = _resolve_audience(payload, body_text)
    warnings.extend(w4)
    correction_memory = _resolve_correction_memory(payload, user_answers)

    # POC warning if response expects action but no explicit POC field exists
    if response.get("point_of_contact_required"):
        poc_field = payload.get("point_of_contact") or payload.get("poc") or payload.get("contact") or payload.get("pointOfContact")
        if not poc_field:
            warnings.append("Response: action/reply keywords detected but no point_of_contact field present")

    context = {
        "schema_version": _SCHEMA_VERSION,
        "document": {
            "doc_type": doc_type,
            "classification_context": classification_context,
            "ssic": payload.get("ssic") or None,
            "originator_code": payload.get("originator_code") or None,
            "serial_number": payload.get("serial_number") or None,
        },
        "component": {
            "service": service,
            "origin_activity_type": None,
            "activity_name": payload.get("unit_identity") or None,
            "activity_address_source": None,
        },
        "routing": routing,
        "audience": audience,
        "privacy_security": privacy_security,
        "response": response,
        "correction_memory": correction_memory,
    }

    return context, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python src/context_resolver.py <payload.json>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    context, warnings = resolve_context(payload)

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    print(json.dumps(context, indent=2))
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
