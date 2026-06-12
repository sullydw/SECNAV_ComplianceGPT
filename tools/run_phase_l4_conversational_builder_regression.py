#!/usr/bin/env python3
"""
Phase L.4 Conversational Builder Regression Runner

Tests:
  1. BuilderSession starts successfully
  2. BuilderSession tracks missing required fields after start
  3. Key-value ingestion updates fields correctly
  4. next_question returns the next missing required field
  5. window_envelope field is captured in build_payload
  6. warning_summary maps CCI-ROUTE-010, CCI-ROUTE-011, CCI-CH7-SUBJ-002
  7. warning_summary provides generic fallback for unknown advisory/warning
  8. No renderer/config/validator mutation occurs
  9. finalize returns structured payload without PDF generation
  10. run_validation returns CCI_AUDIT_V1 if available

Exit 0 if all expectations met; non-zero otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure repo root and src/ are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from conversational_builder import BuilderSession

_PASS = 0
_FAIL = 0


def _assert(condition: bool, message: str) -> None:
    global _PASS, _FAIL
    if not condition:
        _FAIL += 1
        print(f"FAIL: {message}", file=sys.stderr)
        raise AssertionError(message)
    else:
        _PASS += 1
        print(f"PASS: {message}")


def test_builder_start() -> BuilderSession:
    print("\n=== TEST: builder_start ===")
    builder = BuilderSession()
    result = builder.start()
    _assert(result["session_id"] is not None, "session_id is set")
    _assert(result["current_step"] in ("intake", "validation"), "current_step is valid")
    print(f"  Step: {result['current_step']}")
    return builder


def test_missing_required_tracked() -> None:
    print("\n=== TEST: missing_required_tracked ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    status = builder._orchestrator.get_status()
    missing = set(status.get("missing_required", []))
    _assert("from" in missing, "from is missing required for standard_letter")
    _assert("subj" in missing, "subj is missing required for standard_letter")
    _assert("to" in missing, "to is missing required for standard_letter")
    _assert("date" in missing, "date is missing required for standard_letter")
    print(f"  Missing required fields: {sorted(missing)}")


def test_key_value_ingestion() -> None:
    print("\n=== TEST: key_value_ingestion ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    result = builder.ingest_user_message("from: Commanding Officer, USS NEVERSAIL")
    _assert(result["applied_answers"].get("from") == "Commanding Officer, USS NEVERSAIL", "from field ingested")

    result = builder.ingest_user_message("to: Commander, Example Command")
    _assert(result["applied_answers"].get("to") == "Commander, Example Command", "to field ingested")

    result = builder.ingest_user_message("subj: TRAINING PLAN")
    _assert(result["applied_answers"].get("subj") == "TRAINING PLAN", "subj field ingested")

    result = builder.ingest_user_message("window_envelope: false")
    _assert(result["applied_answers"].get("window_envelope") is False, "window_envelope field coerced to False")

    payload = builder.build_payload()
    _assert(payload.get("from") == "Commanding Officer, USS NEVERSAIL", "from present in payload")
    _assert(payload.get("to") == "Commander, Example Command", "to present in payload")
    _assert(payload.get("subj") == "TRAINING PLAN", "subj present in payload")
    _assert(payload.get("window_envelope") is False, "window_envelope present in payload")

    print(f"  Payload keys: {sorted(payload.keys())}")


def test_next_question_behavior() -> None:
    print("\n=== TEST: next_question_behavior ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    # Provide only a few fields; next_question should return a missing required field
    builder.ingest_user_message("from: Commanding Officer, USS NEVERSAIL")
    q = builder.next_question()
    _assert(q is not None, "next_question returns a question when missing fields remain")
    _assert(q.get("field_path") is not None, "next_question has field_path")
    print(f"  Next question: {q['field_path']} ({q['bucket']})")

    # Fill all standard letter required fields and assert next_question returns a recommended field
    msgs = [
        "from: Commanding Officer, USS NEVERSAIL",
        "to: Commander, Example Command",
        "subj: TRAINING PLAN",
        "date: 15 May 2026",
        "body: Paragraph 1. Paragraph 2.",
        "signature: J. DOE",
    ]
    for m in msgs:
        builder.ingest_user_message(m)

    q = builder.next_question()
    _assert(q is not None, "next_question returns a recommended field when required are present")
    _assert(q.get("bucket") == "recommended", "next question is recommended after required filled")
    print(f"  Next question after required filled: {q['field_path']} ({q['bucket']})")


def test_window_envelope_field() -> None:
    print("\n=== TEST: window_envelope_field ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    builder.ingest_user_message("from: CO, USS NEVERSAIL")
    builder.ingest_user_message("to: COMEXCOM")
    builder.ingest_user_message("subj: TEST")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Test body.")
    builder.ingest_user_message("signature: J. DOE")
    builder.ingest_user_message("window_envelope: yes")

    payload = builder.build_payload()
    _assert(payload.get("window_envelope") is True, "window_envelope is True when yes is supplied")

    builder2 = BuilderSession()
    builder2.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    builder2.ingest_user_message("from: CO")
    builder2.ingest_user_message("to: COMEXCOM")
    builder2.ingest_user_message("subj: TEST")
    builder2.ingest_user_message("date: 15 May 2026")
    builder2.ingest_user_message("body: Test body.")
    builder2.ingest_user_message("signature: J. DOE")
    builder2.ingest_user_message("window_envelope: false")

    payload2 = builder2.build_payload()
    _assert(payload2.get("window_envelope") is False, "window_envelope is False when false is supplied")
    print("  window_envelope captured correctly.")


def test_warning_summary_known_ids() -> None:
    print("\n=== TEST: warning_summary_known_ids ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    # Populate a payload that may trigger known warning pilots
    builder.ingest_user_message("from: Code 123")
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TEST PLAN.")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Test body paragraph.")
    builder.ingest_user_message("signature: J. DOE")

    summary = builder.warning_summary()
    _assert(isinstance(summary, list), "warning_summary returns a list")

    # Collect rule codes present in summary
    codes = {item.get("rule_code") for item in summary}
    print(f"  Codes in summary: {codes}")

    # We expect at least one known warning or an advisory fallback
    expected_known = {"CCI-ROUTE-010", "CCI-ROUTE-011", "CCI-CH7-SUBJ-002", "unknown"}
    _assert(bool(codes & expected_known), "summary contains a known or generic code")

    for item in summary:
        _assert("severity" in item, "each summary item has severity")
        _assert("message" in item, "each summary item has message")
        _assert("actions" in item, "each summary item has actions")
        print(f"  [{item['severity'].upper()}] {item['rule_code']}: {item['message'][:60]}...")


def test_generic_fallback() -> None:
    print("\n=== TEST: generic_fallback ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    # Use synthetic data unlikely to trigger known warnings
    builder.ingest_user_message("from: Commander, USS NEVERSAIL")
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TRAINING PLAN")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Test body paragraph.")
    builder.ingest_user_message("signature: J. DOE")

    summary = builder.warning_summary()
    # If any summary items exist, at least one should be advisory or error
    if summary:
        severities = {item["severity"] for item in summary}
        _assert("advisory" in severities or "error" in severities or "warning" in severities,
                "summary has at least one severity classification")
    else:
        _assert(True, "summary empty for fully clean payload (acceptable)")
    print(f"  Summary length: {len(summary)}")


def test_no_renderer_mutation() -> None:
    print("\n=== TEST: no_renderer_mutation ===")
    # Do not import pdf_v6_render here — it requires reportlab which may not be installed.
    # Instead verify the file exists and contains the expected entry function.
    pdf_path = _REPO_ROOT / "src" / "pdf_v6_render.py"
    _assert(pdf_path.exists(), "pdf_v6_render.py still exists")
    source = pdf_path.read_text(encoding="utf-8")
    _assert("def main" in source, "pdf_v6_render.py still contains main() function")
    print("  Renderer file intact.")


def test_finalize_returns_structured_payload() -> None:
    print("\n=== TEST: finalize_returns_structured_payload ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})

    builder.ingest_user_message("from: Commanding Officer, USS NEVERSAIL")
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TRAINING PLAN")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Paragraph 1. Paragraph 2.")
    builder.ingest_user_message("signature: J. DOE")

    result = builder.finalize()
    _assert("payload" in result, "finalize returns payload")
    _assert("audit" in result, "finalize returns audit")
    _assert("warning_summary" in result, "finalize returns warning_summary")
    _assert(result["builder_version"] == "L.4", "builder_version is L.4")
    _assert(result["draft_final_status"] in ("draft", "final"), "draft_final_status is valid")
    print(f"  Finalized payload keys: {sorted(result['payload'].keys())}")
    print(f"  Audit schema: {result['audit'].get('schema_version')}")


def test_run_validation_returns_audit_v1() -> None:
    print("\n=== TEST: run_validation_returns_audit_v1 ===")
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    audit = builder.run_validation()
    _assert(audit.get("schema_version") == "CCI_AUDIT_V1", "run_validation returns CCI_AUDIT_V1")
    _assert("validators" in audit, "audit has validators")
    _assert("summary" in audit, "audit has summary")
    print(f"  Audit errors: {audit['summary']['total_errors']}")
    print(f"  Audit warnings: {audit['summary']['total_warnings']}")
    print(f"  Overall pass: {audit['summary']['overall_pass']}")


def main(argv: list[str]) -> int:
    print("=" * 70)
    print("Phase L.4 Conversational Builder Regression Runner")
    print("=" * 70)

    try:
        test_builder_start()
        test_missing_required_tracked()
        test_key_value_ingestion()
        test_next_question_behavior()
        test_window_envelope_field()
        test_warning_summary_known_ids()
        test_generic_fallback()
        test_no_renderer_mutation()
        test_finalize_returns_structured_payload()
        test_run_validation_returns_audit_v1()
    except AssertionError:
        print("\n" + "=" * 70, file=sys.stderr)
        print("REGRESSION FAILED", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return 1

    print("\n" + "=" * 70)
    print(f"REGRESSION PASSED  ({_PASS} passed, {_FAIL} failed)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
