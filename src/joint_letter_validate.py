#!/usr/bin/env python3
"""SECNAV M-5216.5 — Joint Letter Validator (Phase J1)

Validates joint letter payloads per Chapter 7 / Figure 7-4.

Public API:
    validate_joint_letter(payload) -> list[str]
"""

import json
import os
import sys
from typing import Any

# Import body validator from sibling module
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from body_v6_validate import validate_body


_VALID_HEADINGS = {"JOINT LETTER", "JOINT MEMORANDUM"}


def validate_joint_letter(payload: dict[str, Any]) -> list[str]:
    """Validate a joint letter payload. Returns list of error strings (empty if valid)."""
    errors: list[str] = []

    # doc_type
    doc_type = payload.get("doc_type")
    if doc_type != "DT_JOINT_LTR":
        errors.append(f"doc_type must be 'DT_JOINT_LTR', got: {doc_type!r}")

    # joint_heading
    joint_heading = payload.get("joint_heading")
    if joint_heading not in _VALID_HEADINGS:
        errors.append(
            f"joint_heading must be 'JOINT LETTER' or 'JOINT MEMORANDUM', got: {joint_heading!r}"
        )

    # commands
    commands = payload.get("commands")
    if not isinstance(commands, list):
        errors.append("commands must be a list")
        return errors  # Cannot proceed without a list

    if len(commands) < 2:
        errors.append("commands must contain at least 2 entries")
    elif len(commands) > 2:
        errors.append(
            "manual allows two or more commands, but J1 supports exactly two"
        )

    # senior_command_index
    senior_command_index = payload.get("senior_command_index")
    try:
        idx = int(senior_command_index)
    except (TypeError, ValueError):
        errors.append(f"senior_command_index must be an integer, got: {senior_command_index!r}")
        idx = -1

    if 0 <= idx < len(commands):
        pass  # valid
    else:
        errors.append(
            f"senior_command_index ({senior_command_index}) must point to a valid command index (0-{max(0, len(commands) - 1)})"
        )

    # to
    to_val = payload.get("to")
    if not to_val or not str(to_val).strip():
        errors.append("'to' must be present and non-empty")

    # subj
    subj = payload.get("subj")
    if not subj or not str(subj).strip():
        errors.append("'subj' must be present and non-empty")

    # body
    body = payload.get("body")
    if not isinstance(body, list) or len(body) == 0:
        errors.append("'body' must be a non-empty list")
    else:
        # Run existing body validator
        body_errors = validate_body(payload)
        if body_errors:
            errors.extend(body_errors)

    # Per-command validation
    for i, cmd in enumerate(commands):
        prefix = f"command[{i}]"
        if not isinstance(cmd, dict):
            errors.append(f"{prefix} must be a dict")
            continue

        command_title = cmd.get("command_title")
        if not command_title or not str(command_title).strip():
            errors.append(f"{prefix} missing 'command_title'")

        sig = cmd.get("signature")
        if not isinstance(sig, dict):
            errors.append(f"{prefix} missing 'signature' dict")
        else:
            sig_name = sig.get("name")
            if not sig_name or not str(sig_name).strip():
                errors.append(f"{prefix} signature missing 'name'")

    return errors


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python src/joint_letter_validate.py <fixture.json>")
        return 1

    path = argv[1]
    if not os.path.exists(path):
        print(f"FAIL: file not found: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    errors = validate_joint_letter(payload)
    if errors:
        print("FAIL")
        for err in errors:
            print(f"  ERROR: {err}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
