#!/usr/bin/env python3
"""
Context Schema Regression Runner

Runs the context resolver against example fixtures and validates expected
schema fields, inference behavior, and warning presence.

Exit 0 only when all expectations are met.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

sys.path.insert(0, str(REPO_ROOT / "src"))

from context_resolver import resolve_context


_FIXTURES = {
    "full": {
        "path": REPO_ROOT / "examples" / "audit_context_full.json",
        "expected_doc_type": "standard_letter",
        "expected_service": "marine_corps",
        "expected_warning_count": 0,
        "expected_classification": "unclassified",
    },
    "minimal": {
        "path": REPO_ROOT / "examples" / "audit_context_minimal.json",
        "expected_doc_type": "unknown",
        "expected_service": "unknown",
        "expected_warning_count_min": 2,
        "expected_minimal_routing": True,
    },
    "inferred": {
        "path": REPO_ROOT / "examples" / "audit_context_inferred.json",
        "expected_doc_type": "unknown",
        "expected_service": "joint",
        "expected_warning_count_min": 4,
        "expected_reply_expected": True,
        "expected_action_required": True,
        "expected_deadline_required": True,
        "expected_poc_required": True,
        "expected_contains_pii": True,
        "expected_classified_or_sensitive": True,
        "expected_cui_fouo": True,
        "expected_email_transmission": True,
        "expected_fax_transmission": True,
        "expected_routing_counts": {"action_addressee_count": 3, "copy_to_count": 3, "via_count": 2},
    },
}


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def _pass(msg: str) -> None:
    print(f"PASS — {msg}")


def run_fixture(name: str, spec: dict) -> bool:
    path = spec["path"]
    print("=" * 72)
    print(f"RUNNING: context resolver on {path.name}")
    print("-" * 72)

    payload = json.loads(path.read_text(encoding="utf-8"))
    context, warnings = resolve_context(payload)

    ok = True

    # schema_version
    if context.get("schema_version") != "CCI_CONTEXT_V1":
        _fail(f"Expected schema_version CCI_CONTEXT_V1, got {context.get('schema_version')}")
        ok = False
    else:
        _pass("schema_version == CCI_CONTEXT_V1")

    # document.doc_type
    expected_dt = spec.get("expected_doc_type")
    actual_dt = context["document"]["doc_type"]
    if expected_dt is not None and actual_dt != expected_dt:
        _fail(f"Expected doc_type={expected_dt}, got {actual_dt}")
        ok = False
    else:
        _pass(f"doc_type == {actual_dt}")

    # component.service
    expected_svc = spec.get("expected_service")
    actual_svc = context["component"]["service"]
    if expected_svc is not None and actual_svc != expected_svc:
        _fail(f"Expected service={expected_svc}, got {actual_svc}")
        ok = False
    else:
        _pass(f"component.service == {actual_svc}")

    # warnings count
    expected_wc = spec.get("expected_warning_count")
    if expected_wc is not None and len(warnings) != expected_wc:
        _fail(f"Expected {expected_wc} warnings, got {len(warnings)}")
        ok = False
    else:
        _pass(f"warnings count == {len(warnings)}")

    expected_wc_min = spec.get("expected_warning_count_min")
    if expected_wc_min is not None and len(warnings) < expected_wc_min:
        _fail(f"Expected at least {expected_wc_min} warnings, got {len(warnings)}")
        ok = False
    elif expected_wc_min is not None:
        _pass(f"warnings count >= {expected_wc_min}")

    # routing counts
    if spec.get("expected_minimal_routing"):
        rc = context["routing"]
        if rc.get("action_addressee_count", 0) == 0 and rc.get("copy_to_count", 0) == 0:
            _fail("Minimal routing counts appear empty unexpectedly")
            ok = False
        else:
            _pass("minimal routing counts present")

    rc_expected = spec.get("expected_routing_counts")
    if rc_expected:
        rc = context["routing"]
        for key, val in rc_expected.items():
            actual = rc.get(key)
            if actual != val:
                _fail(f"Expected routing.{key}={val}, got {actual}")
                ok = False
            else:
                _pass(f"routing.{key} == {actual}")

    # response flags
    for key in ("reply_expected", "action_required", "deadline_required", "point_of_contact_required"):
        expected = spec.get(f"expected_{key}")
        if expected is not None:
            actual = context["response"].get(key)
            if actual != expected:
                _fail(f"Expected response.{key}={expected}, got {actual}")
                ok = False
            else:
                _pass(f"response.{key} == {actual}")

    # privacy_security flags
    for key in ("contains_pii", "classified_or_sensitive", "cui_fouo", "email_transmission", "fax_transmission"):
        expected = spec.get(f"expected_{key}")
        if expected is not None:
            actual = context["privacy_security"].get(key)
            if actual != expected:
                _fail(f"Expected privacy_security.{key}={expected}, got {actual}")
                ok = False
            else:
                _pass(f"privacy_security.{key} == {actual}")

    # classification_context
    expected_cls = spec.get("expected_classification")
    if expected_cls is not None:
        actual_cls = context["document"]["classification_context"]
        if actual_cls != expected_cls:
            _fail(f"Expected classification_context={expected_cls}, got {actual_cls}")
            ok = False
        else:
            _pass(f"classification_context == {actual_cls}")

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    status = "PASS" if ok else "FAIL"
    print(f"RESULT: {status} — {path.name}")
    return ok


def main() -> int:
    print("CONTEXT SCHEMA REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {PYTHON}")
    print()

    all_ok = True
    for name, spec in _FIXTURES.items():
        if not run_fixture(name, spec):
            all_ok = False
        print()

    print("=" * 72)
    if all_ok:
        print("CONTEXT SCHEMA REGRESSION RESULT: PASS")
        return 0
    else:
        print("CONTEXT SCHEMA REGRESSION RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
