#!/usr/bin/env python3
"""
C8 Structural Validator

Checks obvious C8 address-format contradictions in a v6 payload.

Public API:
    validate_c8(payload) -> tuple[list[str], list[str]]
        Returns (errors, warnings).  Warnings alone do not constitute failure.

CLI:
    python src/c8_validate.py <payload.json>

    Prints any WARNING lines first, then FAIL + errors (if any, exit 1), or PASS
    (exit 0) when there are no errors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def validate_c8(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the C8 structural checks."""

    errors: list[str] = []
    warnings: list[str] = []

    dist_mode = payload.get("distribution_mode")
    to_field = payload.get("to")
    dist_field = payload.get("distribution")
    via_field = payload.get("via")

    # --- Rule 1: distribution_only -----------------------------------------
    if dist_mode == "distribution_only":
        if to_field is not None:
            errors.append(
                "C8-003: To line must be omitted in distribution_only mode"
            )

        if not isinstance(dist_field, list) or len(dist_field) == 0:
            errors.append(
                "C8-003: distribution list must exist and not be empty in "
                "distribution_only mode"
            )

    # --- Rule 2: to_plus_distribution --------------------------------------
    elif dist_mode == "to_plus_distribution":
        if to_field is None:
            errors.append(
                "C8-004: To line must exist in to_plus_distribution mode"
            )
        elif isinstance(to_field, list):
            errors.append(
                "C8-004: To must be a string (group title), not a list, in "
                "to_plus_distribution mode"
            )

        if not isinstance(dist_field, list) or len(dist_field) == 0:
            errors.append(
                "C8-004: distribution list must exist and not be empty in "
                "to_plus_distribution mode"
            )

    # --- Rule 3: no distribution_mode, To-line-only case -------------------
    elif dist_mode is None:
        # To is required for any standard letter, but only check if present
        # (some payloads may still be under construction)
        if to_field is not None:
            # Warn if To is a list with more than 4 entries
            # (C8-002 says ≤4 action addressees → To line; >4 → Distribution)
            if isinstance(to_field, list) and len(to_field) > 4:
                warnings.append(
                    "C8-002: To list has more than 4 entries; consider "
                    "distribution_only mode for >4 action addressees"
                )

            # Fail if Via exists in To-line-only mode
            # (Via is a separate addressing element not allowed with To-line-only)
            if via_field is not None:
                errors.append(
                    "C8-002: Via must not exist in To-line-only format"
                )

            # Fail if Distribution exists without distribution_mode
            if dist_field is not None:
                errors.append(
                    "C8: Distribution exists without distribution_mode; set "
                    "distribution_mode to indicate addressing intent"
                )
        else:
            # No To and no distribution_mode — may be a partial payload but
            # this is structurally questionable
            warnings.append(
                "C8: No To line and no distribution_mode specified"
            )

    # --- Rule 4: unsupported distribution_mode -----------------------------
    else:
        errors.append(
            f"C8: Unsupported distribution_mode: {dist_mode!r}"
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("USAGE: python src/c8_validate.py <payload.json>", file=sys.stderr)
        return 2

    input_path = Path(argv[1])
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        return 2

    try:
        with input_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Failed to read payload: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_c8(payload)

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
