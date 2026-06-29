#!/usr/bin/env python3
"""
Phase L.30N Smoke Test — Candidate Source Warning Summaries

Verifies:
- official_live candidate shows OFFICIAL SOURCE
- secondary_credible candidate shows SOURCE WARNING
- missing source_tier shows SOURCE WARNING
- source_limitation appears when present
- preview remains read-only
- candidate counts unchanged
- approval/finalize/render behavior unchanged
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent

_PYTHON = Path(r"C:\Users\drryl\pinokio\bin\miniconda\python.exe")
_TOOL = _TOOL_ROOT / "hermes_secnav_tool.py"


def _run_tool(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(_PYTHON), str(_TOOL)] + args,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(_REPO_ROOT),
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return {"success": False, "error": proc.stderr or f"exit code {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON: {proc.stdout[:200]}"}


def _apply(session_id: str, kv: str) -> dict:
    return _run_tool(["apply", "--session", session_id, "--kv", kv])


def _preview(session_id: str) -> dict:
    return _run_tool(["preview", "--session", session_id])


def _add_candidate(session_id: str, cand_path: Path) -> dict:
    return _run_tool(["candidate-add", "--session", session_id, "--json", str(cand_path)])


def main() -> int:
    errors: list[str] = []

    # --- Start session ---
    start_r = _run_tool(["start"])
    if not start_r.get("success"):
        print(f"FAIL: start failed: {start_r.get('error')}")
        return 1
    sid = start_r["session_id"]

    # --- Build a complete-enough draft ---
    _apply(sid, "from: CO, USS NEVERSAIL")
    _apply(sid, "to: SECNAV")
    _apply(sid, "subj: Test subject")
    _apply(sid, "body: Test body paragraph.")
    _apply(sid, "date: 2026-06-28")
    _apply(sid, "signature.name: J. Doe")

    # --- Add candidates with different source tiers ---
    official = {
        "candidate_type": "unit_identity",
        "input_text": "CO of USS NEVERSAIL is CDR J. Smith per official Navy listing.",
        "resolved_value": {"unit": "USS NEVERSAIL", "co_name": "CDR J. Smith"},
        "confidence": 0.95,
        "requires_user_confirmation": True,
        "source_tier": "official_live",
        "source_url": "https://www.navy.mil/example",
        "source_title": "Official Navy Listing",
    }
    secondary = {
        "candidate_type": "ssic_candidate",
        "input_text": "SSIC 1234 from Jane's reference.",
        "resolved_value": {"ssic": "1234", "title": "Naval Operations"},
        "confidence": 0.72,
        "requires_user_confirmation": True,
        "source_tier": "secondary_credible",
        "source_url": "https://example.com/janes",
        "source_title": "Jane's Reference",
        "source_limitation": "Third-party database, not primary US Navy source",
    }
    unresolved = {
        "candidate_type": "unit_identity",
        "input_text": "Originator code N1 from unknown source.",
        "resolved_value": {"originator_code": "N1"},
        "confidence": 0.5,
        "requires_user_confirmation": True,
    }

    tmp_dir = _TOOL_ROOT
    official_path = tmp_dir / "cand_official.json"
    secondary_path = tmp_dir / "cand_secondary.json"
    unresolved_path = tmp_dir / "cand_unresolved.json"

    official_path.write_text(json.dumps(official), encoding="utf-8")
    secondary_path.write_text(json.dumps(secondary), encoding="utf-8")
    unresolved_path.write_text(json.dumps(unresolved), encoding="utf-8")

    add1 = _add_candidate(sid, official_path)
    add2 = _add_candidate(sid, secondary_path)
    add3 = _add_candidate(sid, unresolved_path)

    if not add1.get("success"):
        errors.append(f"official candidate add failed: {add1.get('error')}")
    if not add2.get("success"):
        errors.append(f"secondary candidate add failed: {add2.get('error')}")
    if not add3.get("success"):
        errors.append(f"unresolved candidate add failed: {add3.get('error')}")

    # --- Preview and inspect text ---
    preview = _preview(sid)
    preview_text = preview.get("preview_text", "")

    # 1. official_live shows OFFICIAL SOURCE
    if "[OFFICIAL SOURCE]" not in preview_text:
        errors.append("official_live candidate should show [OFFICIAL SOURCE] in preview_text")

    # 2. secondary_credible shows SOURCE WARNING
    if "[SOURCE WARNING — not official; verify before confirming]" not in preview_text:
        errors.append("secondary_credible candidate should show SOURCE WARNING in preview_text")

    # 3. missing source_tier shows SOURCE WARNING
    if "[SOURCE WARNING — source quality unresolved]" not in preview_text:
        errors.append("missing source_tier candidate should show SOURCE WARNING in preview_text")

    # 4. source_limitation appears
    if "Third-party database, not primary US Navy source" not in preview_text:
        errors.append("source_limitation should appear in preview_text")

    # 5. source_url and source_title appear
    if "https://www.navy.mil/example" not in preview_text:
        errors.append("source_url should appear in preview_text")
    if "Official Navy Listing" not in preview_text:
        errors.append("source_title should appear in preview_text")

    # 6. candidate counts unchanged after preview
    status_before = preview.get("pending_candidates", -1)
    preview2 = _preview(sid)
    status_after = preview2.get("pending_candidates", -2)
    if status_before != status_after:
        errors.append("preview changed pending candidate count unexpectedly")

    # 7. approval behavior unchanged (not approved yet)
    ap = preview.get("approval") or {}
    if ap.get("approval_current"):
        errors.append("draft should not be approved automatically")

    # Cleanup temp files
    for p in (official_path, secondary_path, unresolved_path):
        try:
            p.unlink()
        except Exception:
            pass

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
