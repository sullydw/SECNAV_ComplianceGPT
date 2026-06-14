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
import os
import subprocess
import sys
import tempfile
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
    "signature.name: J. Q. Sample",
    "signature.role: Commanding Officer",
    "window_envelope: false",
]

# Structured signature capture (L.9+):
#   Use dotted keys for name, role, and title:
#     signature.name: J. Q. Sample
#     signature.role: Commanding Officer
#     signature.title: Commanding Officer
#   Plain signature: <value> still works and maps to signature.name for
#   backward compatibility, but the preferred form is signature.name.


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


def _render_finalized_payload(payload: dict[str, Any], output_path: str) -> dict[str, Any]:
    """
    Write payload JSON to a temp file and invoke src/pdf_v6_render.py.
    Returns a structured result dict.
    """
    # Check renderer dependencies
    try:
        import reportlab  # noqa: F401
    except ImportError:
        return {
            "status": "skipped",
            "output_path": output_path,
            "reason": "reportlab unavailable (install with pip install reportlab)",
            "stdout": "",
            "stderr": "",
        }

    renderer = str(_REPO_ROOT / "src" / "pdf_v6_render.py")
    tmp_json = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=str(_REPO_ROOT)
        ) as tf:
            json.dump(payload, tf, indent=2)
            tmp_json = tf.name

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        result = subprocess.run(
            [sys.executable, renderer, tmp_json, output_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return {
                "status": "success",
                "output_path": output_path,
                "reason": f"PDF rendered ({os.path.getsize(output_path)} bytes)",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        else:
            return {
                "status": "failed",
                "output_path": output_path,
                "reason": f"Renderer exited with code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr[:500],
            }
    except Exception as exc:
        return {
            "status": "failed",
            "output_path": output_path,
            "reason": str(exc),
            "stdout": "",
            "stderr": "",
        }
    finally:
        if tmp_json:
            try:
                os.unlink(tmp_json)
            except OSError:
                pass


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
    print("Commands: /status, /warnings, /accept-warnings, /revise, /finalize, /render, /quit")
    print("PDF generation is now available via /render <output.pdf>.")
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
            print("Warnings will be accepted for this finalize/render attempt.")
            continue

        if lower == "/revise":
            accept_warnings = False
            print("Revision path selected. Continue entering corrected key-value fields.")
            continue

        if lower.startswith("/render"):
            parts = text.split(maxsplit=1)
            output_pdf = parts[1].strip() if len(parts) > 1 else str(_REPO_ROOT / "output" / "builder_render.pdf")
            v_summary = builder.validation_summary()
            if not v_summary.get("finalize_allowed"):
                print(f"Render blocked: finalize not allowed.")
                for reason in v_summary.get("block_reason", []):
                    print(f"  {reason}")
                continue
            final_result = builder.finalize(accept_warnings=accept_warnings)
            if not final_result.get("finalize_allowed"):
                print("Render blocked: finalize returned not allowed after attempt.")
                for reason in final_result.get("block_reason", []):
                    print(f"  {reason}")
                continue
            payload = final_result.get("payload", {})
            render_result = _render_finalized_payload(payload, output_pdf)
            print(f"Render status: {render_result['status']}")
            if render_result["status"] == "success":
                print(f"PDF written: {render_result['output_path']} ({render_result['reason']})")
            elif render_result["status"] == "skipped":
                print(f"PDF generation skipped: {render_result['reason']}")
            else:
                print(f"PDF generation failed: {render_result['reason']}")
                if render_result.get("stderr"):
                    print(f"  stderr: {render_result['stderr'][:200]}")
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
    parser.add_argument("--render", metavar="PDF_PATH", default=None, help="Render PDF from scripted sample output (requires --scripted-sample)")
    args = parser.parse_args(argv)

    if args.scripted_sample:
        result = run_scripted_sample(accept_warnings=args.accept_warnings, revise=args.revise)
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.render:
            if not result.get("finalized"):
                print("\nRender skipped: scripted sample did not finalize.")
                return 1
            payload = result.get("payload", {})
            render_res = _render_finalized_payload(payload, args.render)
            print(f"\nRender status: {render_res['status']}")
            if render_res["status"] == "success":
                print(f"PDF written: {render_res['output_path']} ({render_res['reason']})")
            elif render_res["status"] == "skipped":
                print(f"PDF generation skipped: {render_res['reason']}")
            else:
                print(f"PDF generation failed: {render_res['reason']}")
                if render_res.get("stderr"):
                    print(f"  stderr: {render_res['stderr'][:200]}")
        return 0 if (result.get("finalized") or args.revise) else 1

    return run_interactive()


if __name__ == "__main__":
    raise SystemExit(main())
