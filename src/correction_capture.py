#!/usr/bin/env python3
"""
Correction Capture — Build a structured correction record for active-draft corrections.

Public API:
    capture_correction(
        payload: dict,
        field_path: str,
        corrected_value: Any,
        reason: str = "",
        doc_type: str | None = None,
        component: str | None = None,
        correction_type: str = "unknown",
        scope: str = "active_draft",
        source: str = "user",
    ) -> tuple[dict, list[str]]

    Deep-snapshots original_value from payload at field_path.
    Builds correction record with all required fields, validates constraints,
    returns (correction_record, warnings).
    No disk I/O.  Never mutates payload.

Correction record schema (v1 active_draft only):
    correction_id      : str   (UUID)
    field_path         : str
    original_value     : Any   (deep-copied snapshot)
    corrected_value    : Any
    reason             : str
    doc_type           : str
    component          : str
    scope              : str   (must be "active_draft")
    correction_type    : str
    timestamp          : str   (ISO8601 UTC with Z)
    source             : str
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uuid

from correction_apply import get_path_value
from correction_classify import classify_correction


# ---------------------------------------------------------------------------
# Constants


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

_ALLOWED_SCOPES = frozenset({"active_draft", "current_session"})

_ALLOWED_SOURCES = frozenset({"user", "ai_suggestion", "unknown"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_enum(value: str, allowed: frozenset[str], label: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    v = (value or "").strip().lower()
    if not v:
        warnings.append(f"{label} not provided; defaulting to 'unknown'")
        return "unknown", warnings
    if v not in allowed:
        warnings.append(
            f"Invalid {label} '{value}'; must be one of {sorted(allowed)}. Defaulting to 'unknown'."
        )
        return "unknown", warnings
    return v, warnings


def _resolve_doc_type(payload: dict[str, Any], provided: str | None) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if provided:
        return provided, warnings
    raw = payload.get("doc_type") or payload.get("correspondence_type") or payload.get("type")
    if raw:
        return str(raw).strip().lower(), warnings
    warnings.append("doc_type not found in payload; defaulting to 'unknown'")
    return "unknown", warnings


def _resolve_component(payload: dict[str, Any], provided: str | None) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if provided:
        return provided, warnings
    raw = payload.get("component")
    if isinstance(raw, dict):
        svc = raw.get("service") or raw.get("component")
        if svc:
            return str(svc).strip().lower(), warnings
    raw = payload.get("service") or payload.get("branch")
    if raw:
        return str(raw).strip().lower(), warnings
    warnings.append("component not found in payload; defaulting to 'unknown'")
    return "unknown", warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def capture_correction(
    payload: dict[str, Any],
    field_path: str,
    corrected_value: Any,
    *,
    reason: str = "",
    doc_type: str | None = None,
    component: str | None = None,
    correction_type: str = "unknown",
    scope: str = "active_draft",
    source: str = "user",
    validator_conflict: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """
    Capture a correction record from payload metadata and caller input.
    Returns (correction_record, warnings).
    """
    warnings: list[str] = []

    if not isinstance(payload, dict):
        warnings.append("payload must be a dict")
        return {}, warnings

    if not field_path or not isinstance(field_path, str):
        warnings.append("field_path is required and must be a non-empty string")
        return {}, warnings

    # Snapshot original (may be None if path missing)
    original_value = get_path_value(payload, field_path)
    if original_value is None:
        warnings.append(f"field_path '{field_path}' did not resolve in payload; original_value will be None")
    else:
        original_value = copy.deepcopy(original_value)

    corrected_value = copy.deepcopy(corrected_value)

    resolved_doc_type, w1 = _resolve_doc_type(payload, doc_type)
    warnings.extend(w1)

    resolved_component, w2 = _resolve_component(payload, component)
    warnings.extend(w2)

    resolved_type, w3 = _validate_enum(correction_type, _ALLOWED_CORRECTION_TYPES, "correction_type")
    warnings.extend(w3)

    # Phase B: classify if no explicit correction_type was provided
    classification_confidence = "user_override"
    classification_reasons: list[str] = []
    if resolved_type == "unknown":
        resolved_type, classification_confidence, classification_reasons = classify_correction(
            field_path, reason=reason, scope=scope, correction_type="unknown",
            validator_conflict=validator_conflict,
        )

    resolved_scope, w4 = _validate_enum(scope, _ALLOWED_SCOPES, "scope")
    warnings.extend(w4)

    resolved_source, w5 = _validate_enum(source, _ALLOWED_SOURCES, "source")
    warnings.extend(w5)

    record = {
        "correction_id": f"corr_{uuid.uuid4().hex}",
        "field_path": str(field_path).strip(),
        "original_value": original_value,
        "corrected_value": corrected_value,
        "reason": str(reason or "").strip(),
        "doc_type": resolved_doc_type,
        "component": resolved_component,
        "scope": resolved_scope,
        "correction_type": resolved_type,
        "classification_confidence": classification_confidence,
        "timestamp": _now_utc_iso(),
        "source": resolved_source,
    }

    if classification_reasons:
        record["classification_reasons"] = classification_reasons

    return record, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli_capture() -> int:
    if len(sys.argv) < 4:
        print(
            "Usage: python src/correction_capture.py <payload.json> <field_path> <corrected_value> [reason]",
            file=sys.stderr,
        )
        return 1

    payload_path = Path(sys.argv[1])
    field_path = sys.argv[2]
    corrected_value = sys.argv[3]
    reason = sys.argv[4] if len(sys.argv) >= 5 else ""

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    record, warnings = capture_correction(
        payload,
        field_path=field_path,
        corrected_value=corrected_value,
        reason=reason,
    )

    if not record:
        for w in warnings:
            print(f"WARNING: {w}")
        return 1

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    print(json.dumps(record, indent=2))
    print("CAPTURE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(_cli_capture())
