#!/usr/bin/env python3
"""
CCI Subject-Line Validator

Validates subject fields against Correspondence Content Intelligence rules
for SECNAV M-5216.5 subject lines.

Public API:
    validate_cci_subject(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).

CLI:
    python src/cci_subject_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1),
    or PASS (exit 0) when there are no errors.
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

SUBJECT_REQUIRED_TYPES = frozenset([
    "standard_letter",
    "multiple_address_letter",
    "endorsement",
    "joint_letter",
])

SUBJECT_OPTIONAL_TYPES = frozenset([
    "memorandum_for_record",
    "from_to_memo",
    "plain_paper_memo",
    "letterhead_memo",
])

APPROVED_ACRONYMS = frozenset([
    "SECNAV",
    "DON",
    "USN",
    "USMC",
    "DoD",
    "NATO",
    "SSIC",
    "MCO",
    "OPNAV",
    "NAVMC",
    "CNO",
    "CMC",
    "FOIA",
    "PII",
    "CUI",
    "FOUO",
])

# Phase H.2 / Phase I.1 — Subject-line prohibited acronyms.
# Rule catalog: CCI-CH7-SUBJ-006
# Source: SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General
# Source quote: "In correspondence, do not use acronyms in the subject line."
# Approved record: agr_20260604_b69c92d9
# Implementation target: validator_update
PROHIBITED_SUBJECT_ACRONYMS = frozenset([
    "POC",  # Phase H.1 pilot correction; common Point of Contact abbreviation
    "UIC",  # Unit Identification Code; prohibited in subject lines per Ch7 para 9
    "OIC",  # Officer in Charge; prohibited in subject lines per Ch7 para 9
])

# Match probable acronyms: all-caps tokens of 2+ letters
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")

# Common English words that appear in all-caps subjects but are not acronyms
_COMMON_UPPER_WORDS = frozenset([
    "AND", "THE", "FOR", "WITH", "FROM", "TO", "OF", "IN", "ON", "AT", "BY",
    "OR", "NOT", "BUT", "AN", "A", "AS", "IS", "IT", "BE", "ARE", "WAS",
    "WERE", "BEEN", "HAVE", "HAS", "HAD", "DO", "DOES", "DID", "WILL",
    "WOULD", "SHOULD", "COULD", "MAY", "MIGHT", "CAN", "THIS", "THAT",
    "THESE", "THOSE", "UPON", "OVER", "UNDER", "INTO", "THROUGH", "DURING",
    "BEFORE", "AFTER", "ABOVE", "BELOW", "BETWEEN", "WITHIN", "WITHOUT",
])

# Match duplicated label patterns like "Subj: Subj:" or "Subject: Subj:"
_DUPLICATED_LABEL_RE = re.compile(r"(?i)(subj(?:ect)?:\s*subj(?:ect)?:)")

# Match a single embedded Subj: label
_SINGLE_LABEL_RE = re.compile(r"(?i)^subj(?:ect)?:\s*")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_doc_type(payload: dict[str, Any]) -> str:
    """Resolve canonical document type from payload fields.

    Maps the DT_* codes used in the repo to canonical names:
        DT_STD_LTR          -> standard_letter
        DT_JOINT_LTR        -> joint_letter
        DT_ENDORSEMENT      -> endorsement
        DT_MEMO_MFR         -> memorandum_for_record
        DT_MEMO_FROM_TO_PLAIN -> from_to_memo
    Also accepts lower-case or full-word correspondence_type fields.
    """
    dt = payload.get("doc_type")
    if dt is not None:
        dt = str(dt).lower().strip()
        _DT_MAP = {
            "dt_std_ltr": "standard_letter",
            "dt_joint_ltr": "joint_letter",
            "dt_endorsement": "endorsement",
            "dt_memo_mfr": "memorandum_for_record",
            "dt_memo_from_to_plain": "from_to_memo",
        }
        if dt in _DT_MAP:
            return _DT_MAP[dt]
        return dt

    ct = payload.get("correspondence_type")
    if ct is not None:
        return str(ct).lower().strip()

    return "standard_letter"


def _get_subject(payload: dict[str, Any]) -> str | None:
    """Extract subject text from payload."""
    for key in ("subj", "subject"):
        val = payload.get(key)
        if val is not None:
            return str(val).strip()
    return None


def _subject_required(doc_type: str) -> bool:
    """Return True if the doc_type requires a subject."""
    return doc_type in SUBJECT_REQUIRED_TYPES


def _subject_optional(doc_type: str) -> bool:
    """Return True if the doc_type optionally accepts a subject."""
    return doc_type in SUBJECT_OPTIONAL_TYPES


def _check_acronyms(text: str) -> list[str]:
    """Return list of likely acronyms in text that are not approved.

    Heuristic: skip common English words and approved acronyms.
    When the entire text is uppercase, every word looks like an acronym,
    so the heuristic is suppressed entirely.
    """
    # If the whole text is uppercase, we cannot distinguish acronyms from
    # normal words written in caps (subjects are required to be all-caps).
    if text.isupper():
        return []

    found: list[str] = []
    for match in _ACRONYM_RE.finditer(text):
        token = match.group(0)
        if token in APPROVED_ACRONYMS or token in _COMMON_UPPER_WORDS:
            continue
        found.append(token)
    return found


def _check_prohibited_subject_acronyms(text: str) -> list[str]:
    """Return list of prohibited subject-line acronyms.

    Scans all-caps subjects token-by-token against PROHIBITED_SUBJECT_ACRONYMS.
    Normal all-caps words that are not on the prohibited list are not flagged.
    Approved acronyms (APPROVED_ACRONYMS) always take precedence and are never
    treated as prohibited, even if they appear on both lists by mistake.

    Rule catalog: CCI-CH7-SUBJ-006
    Source: SECNAV M-5216.5, Chapter 7, paragraph 9, Subject Line, subparagraph a. General
    Source quote: "In correspondence, do not use acronyms in the subject line."
    Approved record: agr_20260604_b69c92d9
    Implementation target: validator_update
    """
    found: list[str] = []
    for token in text.split():
        # Skip non-all-caps tokens (they are caught by the existing _check_acronyms)
        if not token.isupper():
            continue
        # Skip tokens too short to be meaningful (minimum 3 chars)
        if len(token) < 3:
            continue
        # Approved acronyms are never prohibited
        if token in APPROVED_ACRONYMS:
            continue
        # Only flag exact prohibited tokens
        if token in PROHIBITED_SUBJECT_ACRONYMS:
            found.append(token)
    return found

# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_cci_subject(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for CCI subject-line checks."""
    errors: list[str] = []
    warnings: list[str] = []

    doc_type = _get_doc_type(payload)
    subject = _get_subject(payload)

    # --- Presence checks ----------------------------------------------------

    if _subject_required(doc_type):
        if subject is None or subject == "":
            errors.append(
                f"CCI-CH7-SUBJ-001: required subject is missing or blank "
                f"for doc_type={doc_type}"
            )
            return errors, warnings

    elif _subject_optional(doc_type):
        if subject is None or subject == "":
            # Optional type with no subject: PASS, no further checks
            return errors, warnings
    else:
        # Unknown doc_type: treat subject as required (fail-safe default)
        if subject is None or subject == "":
            errors.append(
                f"CCI-CH7-SUBJ-001: required subject is missing or blank "
                f"for doc_type={doc_type}"
            )
            return errors, warnings

    # subject is guaranteed non-empty from here on
    assert subject is not None and subject != ""

    # --- Label handling -----------------------------------------------------

    if _DUPLICATED_LABEL_RE.search(subject):
        errors.append(
            "CCI-CH7-SUBJ-003: subject contains duplicated label "
            f"(e.g., 'Subj: Subj:') — {subject!r}"
        )

    # Strip a single leading Subj: label for downstream content checks
    stripped_subject = _SINGLE_LABEL_RE.sub("", subject)

    if stripped_subject != subject and not _DUPLICATED_LABEL_RE.search(subject):
        warnings.append(
            "CCI-CH7-SUBJ-003: subject field includes a single 'Subj:' label; "
            "data should contain content only — stripped to "
            f"{stripped_subject!r}"
        )

    content = stripped_subject.strip()
    if content == "":
        errors.append(
            "CCI-CH7-SUBJ-001: subject content is empty after label removal"
        )
        return errors, warnings

    # --- Capitalization for required types ----------------------------------

    if _subject_required(doc_type):
        # After removing label, content should be all caps for standard letters
        if not content.isupper():
            # Allow leading/trailing whitespace to be stripped
            if content.strip().isupper():
                pass
            else:
                errors.append(
                    "CCI-CH7-SUBJ-001: subject content is not all caps "
                    f"for subject-required type {doc_type} — {content!r}"
                )

    # --- Terminal punctuation ----------------------------------------------

    if content.endswith((".", "?", "!")):
        errors.append(
            "CCI-CH7-SUBJ-002: subject ends with terminal punctuation — "
            f"{content!r}"
        )

    # --- Acronym heuristic ---------------------------------------------------

    bad_acronyms = _check_acronyms(content)
    if bad_acronyms:
        warnings.append(
            "CCI-CH7-SUBJ-004: likely acronyms detected in subject: "
            f"{', '.join(bad_acronyms)}"
        )

    # --- Prohibited subject-line acronym advisory (Phase H.2) ----------------

    prohibited_acronyms = _check_prohibited_subject_acronyms(content)
    if prohibited_acronyms:
        warnings.append(
            "CCI-CH7-SUBJ-007: prohibited subject-line acronym detected: "
            f"{', '.join(prohibited_acronyms)} — "
            "SECNAV M-5216.5 Ch7 para 9"
        )

    # --- Vague / short heuristic -------------------------------------------

    words = content.split()
    if len(words) < 4:
        warnings.append(
            "CCI-CH7-SUBJ-005: subject appears vague or too short "
            f"({len(words)} words) — {content!r}"
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/cci_subject_validate.py <payload.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate_cci_subject(payload)

    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        for e in errors:
            print(f"FAIL\n  ERROR: {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
