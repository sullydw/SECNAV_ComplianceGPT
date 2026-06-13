#!/usr/bin/env python3
"""
Phase L.7 — Conversational Builder Interactive CLI Prototype

Small key-value CLI wrapper around BuilderSession.

Non-goals:
- no NL parsing
- no renderer/layout changes
- no CCI config/severity changes
- no Phase F/G command-layer integration
- no committed PDFs or logs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from conversational_builder import BuilderSession

SAMPLE_INPUTS = [
    "ssic: 5216",
    "date: 15 May 2026",
    "from: Commander, Naval Air Station Patuxent River",
    "to: Chief of Naval Operations",
    "subj: TRAINING PLAN.",
    "body: This is a sanitized body paragraph for the Phase L.7 CLI prototype.",
    "signature: J. Q. Sample",
    "window_envelope: false",
]


def pdf_dependency_status() -> dict[str, str]:
    """Return PDF dependency status without rendering or writing output."""
    try:
        import reportlab  # noqa: F401
    except ImportError:
        return {"status": "skipped", "reason": "reportlab unavailable"}

    try:
        import fitz  # noqa: F401
    except ImportError:
        return {"status": "skipped", "reason": "fitz/PyMuPDF unavailable"}

    return {
        "status": "available_not_run",
        "reason": "PDF dependencies available, but L.7 CLI does not render or write PDFs",
    }


def _format_question(question: dict[str, Any] | None) -> str:
    if not question:
        return "All required fields are complete."
    bucket = str(question.get("bucket", "question")).upper()
    field_path = question.get("field_path", "unknown")
    prompt_text = question.get("prompt_text", "Provide a value for this field.")
    return f"[{bucket}] {field_path}\n  {prompt_text}"


def _print_validation_summary(summary: dict[str, Any]) -> None:
    print("Validation Summary")
    print("-" * 18)
    print(
        f"Findings: {summary.get('total_findings', 0)} "
        f"(Errors: {summary.get('errors', 0)}, "
        f"Warnings: {summary.get('warnings', 0)}, "
        f"Advisories: {summary.get('advisories', 0)})"
    )
    print(f"Known warning-pilot findings: {summary.get('known_pilot_findings', 0)}")
    print(f"Pending decisions: {summary.get('pending_decisions', 0)}")
    print(f"Finalize allowed: {'yes' if summary.get('finalize_allowed') else 'no'}")
    for reason in summary.get("block_reason", []):
        print(f"  Block: {reason}")
    print()
    for item in summary.get("findings", []):
        print(f"[{str(item.get('severity', 'advisory')).upper()}] {item.get('rule_code', 'unknown')}")
        print(f"  {item.get('message', 'Review this finding.')}")
        actions = item.get("actions") or []
        if actions:
            print(f"  Actions: {', '.join(actions)}")
        decision = item.get("user_decision")
        if decision:
            print(f"  Decision: {decision}")
        print()


def run_scripted_sample(*, accept_warnings: bool = False, revise: bool = False) -> dict[str, Any]:
    """Run a sanitized scripted builder session for regression tests and demos."""
    builder = BuilderSession(session_id="phase_l7_scripted_sample")
    start_result = builder.start(
        initial_payload={
            "doc_type": "standard_letter",
            "component": {"service": "NAVY"},
        }
    )

    transcript: list[dict[str, Any]] = [
        {
            "event": "start",
            "session_id": start_result.get("session_id"),
            "current_step": start_result.get("current_step"),
            "next_question": start_result.get("next_question"),
        }
    ]

    for line in SAMPLE_INPUTS:
        result = builder.ingest_user_message(line)
        transcript.append(
            {
                "event": "ingest",
                "input": line,
                "current_step": result.get("current_step"),
                "next_question": result.get("next_question"),
                "applied_answers": result.get("applied_answers"),
            }
        )

    audit = builder.run_validation()
    validation_summary = builder.validation_summary()
    transcript.append(
        {
            "event": "validation",
            "total_findings": validation_summary.get("total_findings", 0),
            "pending_decisions": validation_summary.get("pending_decisions", 0),
            "finalize_allowed": validation_summary.get("finalize_allowed", False),
        }
    )

    if revise:
        return {
            "mode": "scripted",
            "session_id": "phase_l7_scripted_sample",
            "finalized": False,
            "action": "revise",
            "payload": builder.build_payload(),
            "audit_schema": audit.get("schema_version"),
            "validation_summary": validation_summary,
            "warning_summary": validation_summary.get("findings", []),
            "pdf": pdf_dependency_status(),
            "transcript": transcript,
        }

    finalize_result = builder.finalize(accept_warnings=accept_warnings)
    payload = finalize_result.get("payload", {})

    return {
        "mode": "scripted",
        "session_id": finalize_result.get("session_id"),
        "finalized": bool(finalize_result.get("finalize_allowed")),
        "action": "accept_warnings" if accept_warnings else "finalize_without_accept_flag",
        "payload": payload,
        "audit_schema": finalize_result.get("audit", {}).get("schema_version"),
        "validation_summary": finalize_result.get("validation_summary", {}),
        "warning_summary": finalize_result.get("warning_summary", []),
        "pdf": pdf_dependency_status(),
        "payload_json_valid": bool(json.dumps(payload, sort_keys=True)),
        "transcript": transcript,
    }


def run_interactive() -> int:
    """Run a small interactive key-value builder loop."""
    print("SECNAV Conversational Builder — Phase L.7 CLI Prototype")
    print("=" * 64)
    print("Use key-value input, for example: from: Commanding Officer")
    print("Commands: /status, /warnings, /accept-warnings, /revise, /finalize, /quit")
    print("PDF generation is not performed by this prototype.")
    print()

    builder = BuilderSession()
    result = builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    print(f"Session: {result.get('session_id')}")
    print(_format_question(result.get("next_question")))
    print()

    accept_warnings = False

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not text:
            continue

        lower = text.lower()
        if lower in {"/quit", "/exit", "/q"}:
            return 0

        if lower == "/status":
            print(json.dumps(builder.build_payload(), indent=2, sort_keys=True))
            continue

        if lower == "/warnings":
            _print_validation_summary(builder.validation_summary())
            continue

        if lower == "/accept-warnings":
            accept_warnings = True
            print("Warnings will be accepted for this finalize attempt.")
            continue

        if lower == "/revise":
            accept_warnings = False
            print("Revision path selected. Continue entering corrected key-value fields.")
            continue

        if lower == "/finalize":
            final_result = builder.finalize(accept_warnings=accept_warnings)
            print(f"Finalize allowed: {'yes' if final_result.get('finalize_allowed') else 'no'}")
            for reason in final_result.get("block_reason", []):
                print(f"  Block: {reason}")
            print()
            _print_validation_summary(final_result.get("validation_summary", {}))
            print("Normalized Payload JSON")
            print("-" * 23)
            print(json.dumps(final_result.get("payload", {}), indent=2, sort_keys=True))
            pdf_status = pdf_dependency_status()
            if pdf_status["status"] == "skipped":
                print(f"\nPDF generation skipped: {pdf_status['reason']}")
            else:
                print(f"\nPDF generation not run: {pdf_status['reason']}")
            continue

        result = builder.ingest_user_message(text)
        print(f"Step: {result.get('current_step')}")
        print(_format_question(result.get("next_question")))
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase L.7 conversational builder CLI prototype")
    parser.add_argument("--scripted-sample", action="store_true", help="Run sanitized scripted sample and print JSON")
    parser.add_argument("--accept-warnings", action="store_true", help="Accept warnings during scripted finalize")
    parser.add_argument("--revise", action="store_true", help="Run scripted revise path without finalizing")
    args = parser.parse_args(argv)

    if args.scripted_sample:
        result = run_scripted_sample(accept_warnings=args.accept_warnings, revise=args.revise)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if (result.get("finalized") or args.revise) else 1

    return run_interactive()


if __name__ == "__main__":
    raise SystemExit(main())
