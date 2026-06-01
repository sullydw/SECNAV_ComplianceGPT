#!/usr/bin/env python3
"""
Correction Classification — Deterministic/heuristic classifier for correction types.

Public API:
    classify_correction(
        field_path: str,
        reason: str = "",
        scope: str = "active_draft",
        correction_type: str = "unknown",
    ) -> tuple[str, str, list[str]]

Returns (type, confidence, reasons).
Pure helper, no side effects, no AI/LLM calls.

Confidence levels:
    user_override — caller passed explicit non-unknown correction_type
    high        — field-path signal and reason-keyword signal agree
    medium      — only one signal exists, or strong local-command reason overrides
                  a conflicting body-field one_time_wording signal
    low         — ambiguous/conflicting indicators that cannot be resolved;
                  defaults to unknown
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_CORRECTION_TYPES = frozenset({
    "one_time_wording",
    "local_command_preference",
    "possible_secnav_manual_rule",
    "bug_validator_gap",
    "unknown",
})

# Field path substrings that trigger each type (ANY match triggers)
_FIELD_TRIGGERS: dict[str, tuple[str, ...]] = {
    "one_time_wording": (
        "body[", "ref[", "encl[", "via[",
    ),
    "local_command_preference": (
        "from", "signature", "originator_code", "unit_identity",
        "copy_to[", "distribution[", "point_of_contact",
    ),
    "possible_secnav_manual_rule": (
        "subj", "date", "body",
    ),
}

# Reason keyword groups (case-insensitive)
_REASON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "one_time_wording": (
        "reword", "rephrase", "better wording", "one-time",
        "this letter only", "just for this draft",
        "minor wording change", "example text", "placeholder",
    ),
    "local_command_preference": (
        "our sop", "local command", "standard for our unit",
        "we always use", "unit preference", "per local instructions",
        "local policy", "command preference", "unit standard",
    ),
    "possible_secnav_manual_rule": (
        "secnav", "manual", "5216.5", "paragraph",
        "figure", "regulation", "required by", "must be",
    ),
    "bug_validator_gap": (
        "validator is wrong", "false positive", "should not flag",
        "allowed by", "permitted", "exception", "gap",
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Case-insensitive substring search of any keyword in text."""
    lowered = text.lower()
    return any(kw in lowered for kw in keywords)


def _detect_type(field_path: str, reason: str) -> str | None:
    """Detect which single type the inputs suggest, or None if none detected."""
    field_path_lower = str(field_path).strip().lower()
    reason_lower = str(reason).strip().lower()

    detected: list[str] = []

    for ctype in _FIELD_TRIGGERS:
        for trigger in _FIELD_TRIGGERS[ctype]:
            # body[n] is indexed; unindexed body is handled separately
            if ctype == "one_time_wording" and trigger == "body[":
                if re.search(r"body\[", field_path_lower):
                    detected.append(ctype)
                    break
            elif ctype == "possible_secnav_manual_rule" and trigger == "body":
                # only trigger if body is NOT indexed (no body[n])
                if "body" in field_path_lower and not re.search(r"body\[", field_path_lower):
                    detected.append(ctype)
                    break
            else:
                if trigger in field_path_lower:
                    detected.append(ctype)
                    break

    for ctype in _REASON_KEYWORDS:
        if _contains_keyword(reason_lower, _REASON_KEYWORDS[ctype]):
            if ctype not in detected:
                detected.append(ctype)

    if not detected:
        return None

    if len(detected) == 1:
        return detected[0]

    # multiple detected: conflict resolution needed
    return None


def _resolve_conflict(detected: list[str], reason_lower: str) -> tuple[str, list[str]] | None:
    """Attempt to resolve conflicting detected types."""
    reasons: list[str] = []

    local_indicators = _REASON_KEYWORDS["local_command_preference"]
    has_local_reason = _contains_keyword(reason_lower, local_indicators)

    # If one_time_wording and possible_secnav_manual_rule both detected from field,
    # that's actually the body/body[n] ambiguity — but we shouldn't see that because
    # of the indexed vs unindexed check above. So if both detected, they must come
    # from mixed signals.
    if has_local_reason and "local_command_preference" not in detected:
        # body[n] + "our SOP" triggers this
        detected.append("local_command_preference")

    if len(detected) == 1:
        return detected[0], reasons

    # If local_command_preference is involved due to strong reason keywords, prefer it
    if has_local_reason and "local_command_preference" in detected:
        reasons.append("Conflict resolved by strong local-command reason keywords")
        return "local_command_preference", reasons

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_correction(
    field_path: str,
    reason: str = "",
    scope: str = "active_draft",
    correction_type: str = "unknown",
    validator_conflict: bool = False,
) -> tuple[str, str, list[str]]:
    """
    Classify a correction into one of the approved types.
    Returns (type, confidence, reasons).

    If caller passes explicit non-unknown correction_type, return that type
    with confidence 'user_override'.
    """
    reasons: list[str] = []
    user_type = str(correction_type).strip().lower() if correction_type else "unknown"

    if user_type and user_type != "unknown" and user_type in _ALLOWED_CORRECTION_TYPES:
        reasons.append(f"Explicit correction_type provided: {user_type}")
        return user_type, "user_override", reasons

    fp = str(field_path).strip()
    r = str(reason).strip()

    # Handle validator_conflict signal first (Section 4.4)
    if validator_conflict:
        if _contains_keyword(r.lower(), _REASON_KEYWORDS["bug_validator_gap"]):
            reasons.append("validator_conflict=True and reason keywords agree: bug_validator_gap")
            return "bug_validator_gap", "high", reasons
        # validator_conflict alone is a signal for bug_validator_gap
        reasons.append("validator_conflict=True signals bug_validator_gap")
        return "bug_validator_gap", "medium", reasons

    detected_type = _detect_type(fp, r)

    if detected_type:
        # check if both field and reason agree
        fp_lower = fp.lower()
        r_lower = r.lower()

        field_matches: set[str] = set()
        for ctype, triggers in _FIELD_TRIGGERS.items():
            for tr in triggers:
                if ctype == "one_time_wording" and tr == "body[":
                    if re.search(r"body\[", fp_lower):
                        field_matches.add(ctype)
                        break
                elif ctype == "possible_secnav_manual_rule" and tr == "body":
                    if "body" in fp_lower and not re.search(r"body\[", fp_lower):
                        field_matches.add(ctype)
                        break
                else:
                    if tr in fp_lower:
                        field_matches.add(ctype)
                        break

        reason_matches: set[str] = set()
        for ctype, keywords in _REASON_KEYWORDS.items():
            if _contains_keyword(r_lower, keywords):
                reason_matches.add(ctype)

        agreed = field_matches & reason_matches

        if detected_type in agreed and len(agreed) == 1:
            reasons.append(f"Field-path and reason-text signals agree on {detected_type}")
            return detected_type, "high", reasons
        elif detected_type in field_matches or detected_type in reason_matches:
            reasons.append(f"Only one signal for {detected_type}")
            return detected_type, "medium", reasons
        else:
            # Should not reach here because detected_type must come from somewhere
            reasons.append(f"Signal source unclear for {detected_type}; defaulting medium")
            return detected_type, "medium", reasons

    # No single type resolved — try conflict resolution
    field_path_lower = fp.lower()
    reason_lower = r.lower()

    # Build full detected list for conflict handling
    all_detected: list[str] = []
    for ctype in _FIELD_TRIGGERS:
        for trigger in _FIELD_TRIGGERS[ctype]:
            if ctype == "one_time_wording" and trigger == "body[":
                if re.search(r"body\[", field_path_lower):
                    if ctype not in all_detected:
                        all_detected.append(ctype)
                    break
            elif ctype == "possible_secnav_manual_rule" and trigger == "body":
                if "body" in field_path_lower and not re.search(r"body\[", field_path_lower):
                    if ctype not in all_detected:
                        all_detected.append(ctype)
                    break
            else:
                if trigger in field_path_lower:
                    if ctype not in all_detected:
                        all_detected.append(ctype)
                    break

    for ctype in _REASON_KEYWORDS:
        if _contains_keyword(reason_lower, _REASON_KEYWORDS[ctype]):
            if ctype not in all_detected:
                all_detected.append(ctype)

    resolved = _resolve_conflict(all_detected, reason_lower)
    if resolved:
        ctype, rsn = resolved
        reasons.extend(rsn)
        return ctype, "medium", reasons

    reasons.append("Could not confidently classify correction. Type remains 'unknown'. User may override.")
    return "unknown", "low", reasons
