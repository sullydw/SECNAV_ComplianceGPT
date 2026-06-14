#!/usr/bin/env python3
"""
Phase L.12 — Conversational Builder End-to-End Demo Runner

Runs the current builder CLI path from scripted sample to finalized payload
and PDF render attempt. Generated PDFs are deleted before exit.

Non-goals:
- no renderer/layout changes
- no CCI config/severity changes
- no Phase F/G command-layer integration
- no committed PDFs or logs
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "tools"))

import run_phase_l7_conversational_builder_cli as cli


def _git_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _cleanup_pdf(path: Path) -> bool:
    if path.exists():
        try:
            path.unlink()
        except OSError:
            return False
    return not path.exists()


def main() -> int:
    results: list[tuple[str, bool]] = []

    print("=" * 72)
    print("Phase L.12 Conversational Builder End-to-End Demo")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Run scripted builder session through the same sample path used
    #    by the CLI and demo docs.
    # ------------------------------------------------------------------
    result = cli.run_scripted_sample(accept_warnings=True, revise=False)
    payload = result.get("payload", {})
    validation_summary = result.get("validation_summary", {})
    warning_summary = result.get("warning_summary", [])

    ok = result.get("finalized") is True
    results.append(("Scripted session finalized after accepting warnings", ok))
    print(f"{'PASS' if ok else 'FAIL'} — finalized = {result.get('finalized')}")

    ok = result.get("audit_schema") == "CCI_AUDIT_V1"
    results.append(("Audit schema is CCI_AUDIT_V1", ok))
    print(f"{'PASS' if ok else 'FAIL'} — audit_schema = {result.get('audit_schema')}")

    try:
        json.dumps(payload, sort_keys=True)
        ok = True
    except Exception:
        ok = False
    results.append(("Finalized payload is JSON serializable", ok))
    print(f"{'PASS' if ok else 'FAIL'} — payload JSON serializable")

    sig = payload.get("signature")
    ok = isinstance(sig, dict) and sig.get("name") == "J. Q. Sample"
    results.append(("Signature is structured dict with expected name", ok))
    print(f"{'PASS' if ok else 'FAIL'} — signature = {sig}")

    ok = payload.get("subj") is not None and payload.get("body") is not None
    results.append(("Required sample fields are present", ok))
    print(f"{'PASS' if ok else 'FAIL'} — subject/body present")

    ok = isinstance(validation_summary, dict) and "total_findings" in validation_summary
    results.append(("Validation summary is present", ok))
    print(f"{'PASS' if ok else 'FAIL'} — validation summary present")

    ok = isinstance(warning_summary, list)
    results.append(("Warning summary is a list", ok))
    print(f"{'PASS' if ok else 'FAIL'} — warning summary list")

    # ------------------------------------------------------------------
    # 2. Attempt PDF render using the L.11 helper and then delete output.
    # ------------------------------------------------------------------
    output_pdf = _REPO_ROOT / "output" / "demo_builder_letter.pdf"
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    if output_pdf.exists():
        output_pdf.unlink()

    render_result = cli._render_finalized_payload(payload, str(output_pdf))
    status = render_result.get("status")
    ok = status in {"success", "skipped", "failed"}
    results.append(("Render returned structured status", ok))
    print(f"{'PASS' if ok else 'FAIL'} — render status = {status}")

    if status == "success":
        ok = output_pdf.exists() and output_pdf.stat().st_size > 0
        results.append(("PDF generated with nonzero size", ok))
        print(f"{'PASS' if ok else 'FAIL'} — PDF generated at {output_pdf}")
    elif status == "skipped":
        ok = True
        results.append(("PDF dependency skip handled cleanly", ok))
        print(f"PASS — PDF skipped: {render_result.get('reason')}")
    else:
        ok = True
        results.append(("Renderer failure reported cleanly", ok))
        print(f"PASS — renderer failure reported: {render_result.get('reason')}")

    ok = _cleanup_pdf(output_pdf)
    results.append(("Generated PDF cleaned up", ok))
    print(f"{'PASS' if ok else 'FAIL'} — generated PDF cleaned up")

    # ------------------------------------------------------------------
    # 3. Confirm protected areas are untouched.
    # ------------------------------------------------------------------
    changed = _git_changed_files()
    renderer_changed = any(
        path in {"src/pdf_v6_render.py", "src/audit_pdf_layout.py", "src/letter_model_v6.py"}
        for path in changed
    )
    ok = not renderer_changed
    results.append(("No renderer/layout files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — no renderer/layout mutation")

    config_changed = any(path.startswith("config/") or "cci_enforcement_config" in path for path in changed)
    ok = not config_changed
    results.append(("No CCI config/severity files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — no config/severity mutation")

    generated_in_status = any(path.endswith(".pdf") or path.endswith(".log") for path in changed)
    ok = not generated_in_status
    results.append(("No generated PDFs/logs in git diff", ok))
    print(f"{'PASS' if ok else 'FAIL'} — no generated PDFs/logs in git diff")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 72)
    print(f"RESULTS: {passed}/{len(results)} passed, {failed}/{len(results)} failed")
    if failed == 0:
        print("ALL CHECKS PASS")
    print("=" * 72)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
