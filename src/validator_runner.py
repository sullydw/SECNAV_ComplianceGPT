#!/usr/bin/env python3
"""
CCI Validator Runner — Consolidated Audit Report

Public API:
    run_cci_audit(payload, user_answers=None) -> dict
        Returns a CCI_AUDIT_V1 audit result dictionary.

CLI:
    python src/validator_runner.py <payload.json>
    python src/validator_runner.py --json <payload.json>

    Default output is human-readable.
    Use --json for machine-readable CCI_AUDIT_V1 JSON.
    Exit 0 when overall_pass is true; exit 1 when total_errors > 0.

Scope:
    - Imports and runs all seven CCI validators in a single pass.
    - Calls resolve_context(payload, user_answers) first.
    - Does NOT render PDFs.
    - Does NOT run C7-C10 layout validators.
    - Purely additive; does not modify existing validators.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on sys.path so imports work when executed as script
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from context_resolver import resolve_context
from cci_subject_validate import validate_cci_subject
from cci_ref_encl_validate import validate_cci_ref_encl
from cci_acronym_validate import validate_cci_acronyms
from cci_date_time_validate import validate_cci_date_time
from cci_personnel_validate import validate_cci_personnel
from cci_poc_validate import validate_cci_poc
from cci_routing_validate import validate_cci_routing


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = "CCI_AUDIT_V1"

_VALIDATOR_REGISTRY: list[tuple[str, Any]] = [
    ("subject", validate_cci_subject),
    ("ref_encl", validate_cci_ref_encl),
    ("acronyms", validate_cci_acronyms),
    ("date_time", validate_cci_date_time),
    ("personnel", validate_cci_personnel),
    ("poc", validate_cci_poc),
    ("routing", validate_cci_routing),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_cci_audit(payload: dict[str, Any], user_answers: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run all CCI validators + context resolver and return a CCI_AUDIT_V1 result."""
    context, context_warnings = resolve_context(payload, user_answers)

    validators: dict[str, dict[str, Any]] = {}
    total_errors = 0
    total_warnings = 0
    validators_with_errors: list[str] = []
    validators_with_warnings: list[str] = []

    for key, fn in _VALIDATOR_REGISTRY:
        errors, warnings = fn(payload)
        error_count = len(errors)
        warning_count = len(warnings)

        validators[key] = {
            "errors": errors,
            "warnings": warnings,
            "error_count": error_count,
            "warning_count": warning_count,
            "passed": error_count == 0,
        }

        total_errors += error_count
        total_warnings += warning_count

        if errors:
            validators_with_errors.append(key)
        if warnings:
            validators_with_warnings.append(key)

    overall_pass = total_errors == 0

    result = {
        "schema_version": _SCHEMA_VERSION,
        "context": context,
        "context_warnings": context_warnings,
        "validators": validators,
        "summary": {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validators_run": len(_VALIDATOR_REGISTRY),
            "validators_with_errors": validators_with_errors,
            "validators_with_warnings": validators_with_warnings,
            "overall_pass": overall_pass,
        },
    }

    return result


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_human(result: dict[str, Any]) -> None:
    """Print a human-readable audit report to stdout."""
    context = result["context"]
    context_warnings = result["context_warnings"]
    validators = result["validators"]
    summary = result["summary"]

    print("=" * 72)
    print("CCI CONSOLIDATED AUDIT REPORT")
    print("=" * 72)
    print()

    # Context Summary
    print("Context Summary")
    print("-" * 72)
    doc = context.get("document", {})
    print(f"  Document type      : {doc.get('doc_type')}")
    print(f"  Classification     : {doc.get('classification_context')}")
    print(f"  SSIC               : {doc.get('ssic')}")
    print(f"  Originotor code    : {doc.get('originator_code')}")
    print(f"  Serial number      : {doc.get('serial_number')}")
    comp = context.get("component", {})
    print(f"  Service            : {comp.get('service')}")
    print(f"  Activity name      : {comp.get('activity_name')}")
    resp = context.get("response", {})
    print(f"  Reply expected     : {resp.get('reply_expected')}")
    print(f"  Action required    : {resp.get('action_required')}")
    print(f"  POC required       : {resp.get('point_of_contact_required')}")
    rout = context.get("routing", {})
    print(f"  Action addressees  : {rout.get('action_addressee_count')}")
    print(f"  Via count          : {rout.get('via_count')}")
    print(f"  Copy-to count      : {rout.get('copy_to_count')}")
    print()

    # Context Inferences
    if context_warnings:
        print("Context Inferences")
        print("-" * 72)
        for w in context_warnings:
            print(f"  WARNING: {w}")
        print()

    # Validator Results
    print("Validator Results")
    print("-" * 72)
    for key in ("subject", "ref_encl", "acronyms", "date_time", "personnel", "poc", "routing"):
        v = validators[key]
        status = "PASS" if v["passed"] else "FAIL"
        print(f"  [{status}] {key:12s}  errors={v['error_count']}  warnings={v['warning_count']}")
        for e in v["errors"]:
            print(f"      ERROR: {e}")
        for w in v["warnings"]:
            print(f"      WARNING: {w}")
    print()

    # Summary
    print("Summary")
    print("-" * 72)
    print(f"  Validators run      : {summary['validators_run']}")
    print(f"  Total errors        : {summary['total_errors']}")
    print(f"  Total warnings      : {summary['total_warnings']}")
    print(f"  With errors         : {summary['validators_with_errors']}")
    print(f"  With warnings       : {summary['validators_with_warnings']}")
    overall = "PASS" if summary["overall_pass"] else "FAIL"
    print(f"  Overall             : {overall}")
    print()
    print("=" * 72)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="CCI Consolidated Validator Runner — produces a single audit report for all CCI validators.",
    )
    parser.add_argument("payload", help="Path to JSON payload file")
    parser.add_argument("--json", action="store_true", help="Emit raw CCI_AUDIT_V1 JSON instead of human-readable report")
    args = parser.parse_args(argv[1:])

    path = Path(args.payload)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON parse error: {exc}", file=sys.stderr)
        return 2

    result = run_cci_audit(payload)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_human(result)

    return 0 if result["summary"]["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
