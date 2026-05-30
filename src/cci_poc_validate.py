#!/usr/bin/env python3
"""
CCI Point-of-Contact (POC) Validator

Validates that correspondence requiring a point of contact includes one
when body text suggests action/response/request/inquiry expectation.

Public API:
    validate_cci_poc(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).

CLI:
    python src/cci_poc_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1),
    or PASS (exit 0) when there are no errors.

Scope:
    - Body text (body / body_paragraphs) only.
    - Top-level fields: point_of_contact, poc, contact, pointOfContact (aliases accepted).
    - Does NOT inspect rendered PDF layout or signature block content.
    - Does NOT inspect From/To/Via lines for POC (those are header fields).
    - Only body text + top-level POC fields are examined.

Design choices (first version, conservative):
    - Warn, not fail, when missing or incomplete POC is detected.
    - Scan body for keywords suggesting reply/action/inquiry/follow-up.
    - Accept multiple top-level field aliases (point_of_contact, poc, contact, pointOfContact).
    - Accept dict or string POC fields (strings are weakly scanned for contact markers).
    - Does NOT scan every rendered PDF layout or signatures.
    - Does NOT validate complete phone/e-mail format (out of scope).
    - Does NOT require POC on every letter (only when expectation keywords appear).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

# Actions/expectations that trigger need for POC
_ACTION_EXPECTATIONS = frozenset([
    "reply", "respond", "answer",
    "inquiry", "further information", "information request",
    "respond to", "reply to",
    "take action", "action required", "complete action",
    "follow up", "coordinate", "coordination",
    "feedback", "comment", "input",
    "confirmation", "verify",
    "submit", "send", "provide",
    "forward", "distribute",
    "review", "evaluate", "assess",
    "approve", "endorse", "signature",
    "contact", "reach out",
])

# Top-level field names we accept for POC (in priority order)
_POC_FIELD_NAMES = frozenset([
    "point_of_contact",
    "poc",
    "contact",
    "pointOfContact",
])

# Phone-like patterns for weak body contact detection (just need enough
# numeric mass to suggest a phone number after stripping punctuation).
_PHONE_PUNCT_RE = re.compile(r"[\(\)\-/\s.]")

# Keys we treat as telephone/email when POC is a dict
_PHONE_KEYS = frozenset([
    "telephone", "phone", "tel", "office_phone", "work_phone",
    "dsn", "commercial", "cell",
])

_EMAIL_KEYS = frozenset([
    "email", "e_mail", "e-mail", "mail", "e_mail_address", "email_address",
])


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _body_text(payload: dict[str, Any]) -> str:
    """Extract all body text into a single string for scanning."""
    for key in ("body", "body_paragraphs"):
        val = payload.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            return " ".join(str(item) for item in val)
        text = str(val)
        if text:
            return text
    return ""


def _has_action_expectation(text: str) -> bool:
    """Detect if body text suggests action/response/request/inquiry expectation."""
    text_lower = text.lower()
    for pattern in _ACTION_EXPECTATIONS:
        if pattern.lower() in text_lower:
            return True
    return False


def _get_poc_obj(payload: dict[str, Any]) -> Any:
    """Return the first encountered top-level POC field value, or None."""
    for key in _POC_FIELD_NAMES:
        val = payload.get(key)
        if val is not None:
            return val
    return None


def _poc_has_telephone(poc: Any) -> bool:
    """Check whether the POC value contains a telephone marker."""
    if isinstance(poc, dict):
        for k in poc:
            k_clean = k.lower().strip().replace("-", "_").replace(" ", "_")
            if k_clean in _PHONE_KEYS or any(pk in k_clean for pk in ("phone", "tel", "dsn")):
                v = str(poc[k]).strip()
                if v and v.lower() not in ("n/a", "na", "none", "null", "" ):
                    return True
        return False
    if isinstance(poc, str):
        text = poc.lower()
        if any(t in text for t in ("phone", "tel", "dsn", "commercial", "703", "202", "800")):
            return True
        # Look for a raw digit cluster that could be a phone number
        digits_only = re.sub(r"\D", "", poc)
        if len(digits_only) >= 7:
            return True
    return False


def _poc_has_email(poc: Any) -> bool:
    """Check whether the POC value contains an email marker."""
    if isinstance(poc, dict):
        for k in poc:
            k_clean = k.lower().strip().replace("-", "_").replace(" ", "_")
            if k_clean in _EMAIL_KEYS or "email" in k_clean or "mail" in k_clean:
                v = str(poc[k]).strip()
                if v and v.lower() not in ("n/a", "na", "none", "null", ""):
                    return True
        return False
    if isinstance(poc, str):
        if "@" in poc:
            return True
        text = poc.lower()
        if "email" in text or "e-mail" in text or "mail" in text:
            return True
    return False


def _body_has_contact_markers(text: str) -> bool:
    """Weak heuristic: does body text contain evidence of contact info?"""
    text_lower = text.lower()
    # Explicit lexical markers
    if any(term in text_lower for term in ("phone", "telephone", "e-mail", "email", "tel", "dsn", "commercial")):
        return True
    # Raw email-like symbol
    if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        return True
    # Phone-like numeric mass (7+ digits after stripping non-digits)
    digits_only = re.sub(r"\D", "", text)
    if len(digits_only) >= 7:
        return True
    return False


# -------------------------------------------------------------------------
# Core checks
# -------------------------------------------------------------------------

def _check_poc_compliance(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """
    Check POC compliance.

    Rules (v1 conservative, warnings only):
    1. If action expectation detected AND no POC field AND no contact
       markers in body -> warn about missing POC.
    2. If POC field present but lacks telephone OR e-mail -> warn.
    3. If action expected and body lacks contact markers (even if POC
       field is absent) -> warn.
    """
    body = _body_text(payload)
    has_action = _has_action_expectation(body)
    poc_obj = _get_poc_obj(payload)
    has_top_poc = poc_obj is not None and bool(poc_obj)
    has_body_contact = _body_has_contact_markers(body)

    # Rule 1: action expected, no top-level POC field, no body contact
    if has_action and not has_top_poc and not has_body_contact:
        warnings.append(
            "CCI-POC-001: correspondence suggests a reply or inquiry expectation based "
            "on body text but no point of contact block or field detected; "
            "add telephone number and e-mail as appropriate for follow-up"
        )

    # Rule 2: POC field present but missing telephone OR email
    if has_top_poc:
        has_phone = _poc_has_telephone(poc_obj)
        has_email = _poc_has_email(poc_obj)
        if not has_phone or not has_email:
            details = []
            if not has_phone:
                details.append("telephone number")
            if not has_email:
                details.append("e-mail address")
            warnings.append(
                f"CCI-POC-002: point-of-contact field is present but appears incomplete "
                f"(missing {', '.join(details)}); include telephone and e-mail as appropriate"
            )

    # Rule 3: action expected and body contains no telephone/email markers.
    # In v1 we keep the rule catalogged (cci_ch2_poc_rules.json) but do not emit
    # it at runtime because it overlaps with Rule 1 when no POC exists and is noisy
    # when a complete top-level POC is present. Future versions can refine the
    # heuristic and re-enable it.
    pass


# -------------------------------------------------------------------------
# Public function
# -------------------------------------------------------------------------

def validate_cci_poc(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI point-of-contact checks."""
    errors: list[str] = []
    warnings: list[str] = []

    _check_poc_compliance(payload, errors, warnings)

    return errors, warnings


# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_poc_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_poc(payload)

    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
