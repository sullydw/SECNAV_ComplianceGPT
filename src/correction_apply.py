#!/usr/bin/env python3
"""
Correction Apply — Active-draft correction application for SECNAV correspondence payloads.

Public API:
    get_path_value(payload: dict, field_path: str) -> Any
        Resolve a dot/bracket path against a nested dict and return the value.

    apply_correction(payload: dict, correction: dict) -> tuple[dict, list[str]]
        Deep-copy payload, apply correction["corrected_value"] at correction["field_path"],
        return (new_payload, warnings).

    undo_correction(payload: dict, correction: dict) -> tuple[dict, list[str]]
        Deep-copy payload, restore correction["original_value"] at correction["field_path"],
        return (new_payload, warnings).

    apply_corrections(payload: dict, corrections: list[dict]) -> tuple[dict, list[str]]
        Apply each correction in order.  Return (final_payload, aggregated_warnings).

Design choices:
    - Never mutates the caller's payload or correction record.
    - Missing dict paths are created automatically.
    - Missing list indices are rejected with a warning.
    - Invalid paths are rejected with a warning.
    - All functions deep-copy before any mutation.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_PAT_SEGMENT = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\[(\d+)\])?$")


def _parse_path(field_path: str) -> list[tuple[str, int | None]]:
    """
    Parse a dot/bracket path into segments.

    Examples:
        "subj"                    -> [("subj", None)]
        "body[0]"                 -> [("body", 0)]
        "signature.name"          -> [("signature", None), ("name", None)]
        "point_of_contact.email"  -> [("point_of_contact", None), ("email", None)]
        "body[0].text"            -> [("body", 0), ("text", None)]

    Raises ValueError if a segment is malformed.
    """
    parts = field_path.split(".")
    segments: list[tuple[str, int | None]] = []
    for part in parts:
        # split bracket notation if present, e.g. "body[0]" -> "body", "0"
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]$", part)
        if m:
            segments.append((m.group(1), int(m.group(2))))
        elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", part):
            segments.append((part, None))
        else:
            raise ValueError(f"Invalid path segment: '{part}' in path '{field_path}'")
    return segments


# ---------------------------------------------------------------------------
# Value retrieval
# ---------------------------------------------------------------------------

def get_path_value(payload: dict[str, Any], field_path: str) -> Any:
    """
    Resolve field_path against payload and return the value.
    Returns None if the path does not exist.
    """
    try:
        segments = _parse_path(field_path)
    except ValueError:
        return None

    node: Any = payload
    for key, idx in segments:
        if isinstance(node, dict) and key in node:
            node = node[key]
            if idx is not None:
                if isinstance(node, list) and 0 <= idx < len(node):
                    node = node[idx]
                else:
                    return None
        else:
            return None
    return node


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------

def _set_path(payload: dict[str, Any], field_path: str, value: Any) -> tuple[dict[str, Any], list[str]]:
    """
    Deep-copy payload, then set value at field_path.
    Returns (new_payload, warnings).
    """
    warnings: list[str] = []
    new_payload = copy.deepcopy(payload)

    try:
        segments = _parse_path(field_path)
    except ValueError as exc:
        warnings.append(f"Invalid field_path '{field_path}': {exc}")
        return new_payload, warnings

    if not segments:
        warnings.append(f"Empty field_path '{field_path}'")
        return new_payload, warnings

    node: Any = new_payload
    for i, (key, idx) in enumerate(segments):
        is_last = i == len(segments) - 1

        if is_last:
            if idx is not None:
                if isinstance(node, dict) and key in node:
                    target_list = node[key]
                    if isinstance(target_list, list) and 0 <= idx < len(target_list):
                        target_list[idx] = value
                    else:
                        warnings.append(
                            f"List index [{idx}] out of range for field '{key}' in path '{field_path}'"
                        )
                else:
                    warnings.append(
                        f"Cannot set list index on missing dict key '{key}' in path '{field_path}'"
                    )
            else:
                if isinstance(node, dict):
                    node[key] = value
                else:
                    warnings.append(
                        f"Cannot set dict key '{key}' on non-dict node in path '{field_path}'"
                    )
        else:
            if isinstance(node, dict):
                if key not in node:
                    node[key] = {}
                node = node[key]
                if idx is not None:
                    if isinstance(node, list):
                        if 0 <= idx < len(node):
                            node = node[idx]
                        else:
                            warnings.append(
                                f"List index [{idx}] out of range for field '{key}' in path '{field_path}'"
                            )
                            return new_payload, warnings
                    else:
                        warnings.append(
                            f"Expected list for field '{key}' but got {type(node).__name__} in path '{field_path}'"
                        )
                        return new_payload, warnings
            else:
                warnings.append(
                    f"Cannot traverse non-dict node at key '{key}' in path '{field_path}'"
                )
                return new_payload, warnings

    return new_payload, warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_correction(payload: dict[str, Any], correction: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Apply a single correction to a deep-copied payload.
    correction must contain 'field_path' and 'corrected_value'.
    Returns (new_payload, warnings).
    """
    warnings: list[str] = []

    if not isinstance(correction, dict):
        warnings.append("correction must be a dict")
        return copy.deepcopy(payload), warnings

    field_path = correction.get("field_path")
    if not field_path or not isinstance(field_path, str):
        warnings.append("correction missing or invalid 'field_path'")
        return copy.deepcopy(payload), warnings

    corrected_value = correction.get("corrected_value")
    # corrected_value may be any type including None, so we only check KeyError
    if "corrected_value" not in correction:
        warnings.append("correction missing 'corrected_value'")
        return copy.deepcopy(payload), warnings

    return _set_path(payload, field_path, corrected_value)


def undo_correction(payload: dict[str, Any], correction: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Undo a correction by restoring original_value at field_path.
    correction must contain 'field_path' and 'original_value'.
    Returns (new_payload, warnings).
    """
    warnings: list[str] = []

    if not isinstance(correction, dict):
        warnings.append("correction must be a dict")
        return copy.deepcopy(payload), warnings

    field_path = correction.get("field_path")
    if not field_path or not isinstance(field_path, str):
        warnings.append("correction missing or invalid 'field_path'")
        return copy.deepcopy(payload), warnings

    if "original_value" not in correction:
        warnings.append("correction missing 'original_value'")
        return copy.deepcopy(payload), warnings

    original_value = correction["original_value"]
    return _set_path(payload, field_path, original_value)


def apply_corrections(
    payload: dict[str, Any],
    corrections: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """
    Apply a list of corrections in order to a deep-copied payload.
    Returns (final_payload, aggregated_warnings).
    """
    current = copy.deepcopy(payload)
    all_warnings: list[str] = []

    for i, correction in enumerate(corrections):
        current, warns = apply_correction(current, correction)
        for w in warns:
            all_warnings.append(f"[correction {i}] {w}")

    return current, all_warnings


# ---------------------------------------------------------------------------
# CLI helpers (optional)
# ---------------------------------------------------------------------------

def _cli_apply() -> int:
    if len(sys.argv) < 3:
        print("Usage: python src/correction_apply.py <payload.json> <correction.json>", file=sys.stderr)
        return 1

    payload_path = Path(sys.argv[1])
    correction_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        correction = json.loads(correction_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    new_payload, warnings = apply_correction(payload, correction)
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    print(json.dumps(new_payload, indent=2))
    print("APPLY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(_cli_apply())
