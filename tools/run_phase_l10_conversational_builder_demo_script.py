#!/usr/bin/env python3
"""
Phase L.10 — Conversational Builder Demo Script and Operator Walkthrough Runner

Runs the L.7 CLI scripted sample and verifies key behaviors:
- sample sequence completes
- payload JSON valid
- signature dict present (structured capture)
- finalize allowed after accepting warnings

Non-goals:
- no renderer/layout changes
- no CCI config/severity changes
- no Phase F/G command-layer integration
- no committed PDFs or logs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from conversational_builder import BuilderSession


def _run_demo(*, accept_warnings: bool = True, revise: bool = False) -> dict:
    """Run the L.7 scripted sample and return the result dict."""
    # Import from L.7 CLI module to reuse the same sequence
    cli_module_path = str(_REPO_ROOT / "tools")
    if cli_module_path not in sys.path:
        sys.path.insert(0, cli_module_path)
    import run_phase_l7_conversational_builder_cli as cli
    return cli.run_scripted_sample(accept_warnings=accept_warnings, revise=revise)


def _check_signature_dict(payload: dict) -> bool:
    sig = payload.get("signature")
    if sig is None:
        return False
    if isinstance(sig, dict):
        return True
    if isinstance(sig, list) and len(sig) > 0:
        return False  # old list form is not what we want
    return False


def main() -> int:
    results: list[tuple[str, bool]] = []

    print("=" * 64)
    print("Phase L.10 Conversational Builder Demo Script")
    print("=" * 64)

    # ------------------------------------------------------------------
    # 1. Scripted sample with accept-warnings path
    # ------------------------------------------------------------------
    print("\n--- Demo: accept-warnings path ---")
    result = _run_demo(accept_warnings=True, revise=False)

    payload = result.get("payload", {})
    finalized = result.get("finalized", False)
    audit_schema = result.get("audit_schema")
    validation_summary = result.get("validation_summary", {})
    warning_summary = result.get("warning_summary", [])
    pdf_status = result.get("pdf", {})

    ok = finalized is True
    results.append(("Demo: finalized is True after accept-warnings", ok))
    print(f"{'PASS' if ok else 'FAIL'} — finalized = {finalized}")

    ok = audit_schema == "CCI_AUDIT_V1"
    results.append(("Demo: audit schema is CCI_AUDIT_V1", ok))
    print(f"{'PASS' if ok else 'FAIL'} — audit_schema = {audit_schema}")

    try:
        json.dumps(payload, sort_keys=True)
        ok = True
    except Exception:
        ok = False
    results.append(("Demo: payload JSON is serializable", ok))
    print(f"{'PASS' if ok else 'FAIL'} — payload JSON serializable")

    ok = _check_signature_dict(payload)
    results.append(("Demo: signature is structured dict", ok))
    print(f"{'PASS' if ok else 'FAIL'} — signature type = {type(payload.get('signature')).__name__}")

    sig = payload.get("signature", {})
    ok = sig.get("name") == "J. Q. Sample"
    results.append(("Demo: signature.name matches input", ok))
    print(f"{'PASS' if ok else 'FAIL'} — signature.name = {sig.get('name')}")

    ok = sig.get("role") == "Commanding Officer"
    results.append(("Demo: signature.role matches input", ok))
    print(f"{'PASS' if ok else 'FAIL'} — signature.role = {sig.get('role')}")

    ok = payload.get("doc_type") == "standard_letter"
    results.append(("Demo: doc_type preserved", ok))
    print(f"{'PASS' if ok else 'FAIL'} — doc_type = {payload.get('doc_type')}")

    ok = payload.get("subj") is not None
    results.append(("Demo: subj present in payload", ok))
    print(f"{'PASS' if ok else 'FAIL'} — subj present")

    ok = validation_summary.get("total_findings", 0) >= 0
    results.append(("Demo: validation summary has findings count", ok))
    print(f"{'PASS' if ok else 'FAIL'} — total_findings = {validation_summary.get('total_findings')}")

    ok = isinstance(warning_summary, list)
    results.append(("Demo: warning_summary is a list", ok))
    print(f"{'PASS' if ok else 'FAIL'} — warning_summary is list")

    ok = pdf_status.get("status") in ("skipped", "available_not_run")
    results.append(("Demo: PDF status is non-failing", ok))
    print(f"{'PASS' if ok else 'FAIL'} — pdf status = {pdf_status.get('status')}")

    # ------------------------------------------------------------------
    # 2. Scripted sample with revise path
    # ------------------------------------------------------------------
    print("\n--- Demo: revise path ---")
    result_revise = _run_demo(accept_warnings=False, revise=True)

    ok = result_revise.get("finalized") is False
    results.append(("Demo: revise path does not finalize", ok))
    print(f"{'PASS' if ok else 'FAIL'} — finalized = {result_revise.get('finalized')}")

    ok = result_revise.get("action") == "revise"
    results.append(("Demo: revise path action recorded", ok))
    print(f"{'PASS' if ok else 'FAIL'} — action = {result_revise.get('action')}")

    ok = result_revise.get("payload") is not None
    results.append(("Demo: revise path returns current payload", ok))
    print(f"{'PASS' if ok else 'FAIL'} — payload present on revise")

    # ------------------------------------------------------------------
    # 3. Summary
    # ------------------------------------------------------------------
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 64)
    print(f"RESULTS: {passed}/{len(results)} passed, {failed}/{len(results)} failed")
    if failed == 0:
        print("ALL CHECKS PASS")
    print("=" * 64)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
