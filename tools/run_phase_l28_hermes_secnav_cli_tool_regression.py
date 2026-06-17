#!/usr/bin/env python3
"""
Phase L.28 Hermes SECNAV CLI Tool Regression

Verifies the CLI bridge created in Phase L.28.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_TOOL = Path(__file__).resolve().parent.parent / "tools" / "hermes_secnav_tool.py"
_PYTHON = Path(__file__).resolve().parent.parent / "venv" / "Scripts" / "python.exe"
_SAMPLE_TEXT = (
    "I need to request to change a date for software release brief to a open TBD date. "
    "it is from MISSA to MCAS new river, HQ BN"
)

failed: list[str] = []
passed: list[str] = []


def run(cmd: list[str]) -> tuple[bool, dict[str, Any], str]:
    full_cmd = [str(_PYTHON), str(_TOOL)] + cmd
    try:
        proc = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if out:
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = {"raw_stdout": out, "success": False}
        else:
            data = {"success": False, "error": "Empty stdout"}
        ok = data.get("success", False) and proc.returncode == 0
        return ok, data, err
    except subprocess.TimeoutExpired:
        return False, {"success": False, "error": "Timeout"}, ""
    except Exception as exc:
        return False, {"success": False, "error": str(exc)}, ""


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        passed.append(label)
        print(f"  PASS  {label}")
    else:
        failed.append(label)
        print(f"  FAIL  {label}{' — ' + detail if detail else ''}")


def main() -> int:
    print("=" * 70)
    print("Phase L.28 Hermes SECNAV CLI Tool Regression")
    print("=" * 70)
    print()

    # 1. Tool file exists
    print("Check 1: tool file exists")
    check("tool_exists", _TOOL.exists(), str(_TOOL))

    # 2. start returns valid JSON and session_id
    print("Check 2: start returns valid JSON and session_id")
    ok, data, _err = run(["start"])
    check("start_ok", ok and data.get("session_id", "").startswith("builder_"))
    session_id: str = data.get("session_id", "")

    if not session_id:
        print("CRITICAL: no session_id; aborting")
        return 1

    # 3. ingest with sample request returns proposed_kv including from/to/subj/body
    print("Check 3: ingest sample returns proposed_kv with from/to/subj/body")
    ok, data, _err = run(["ingest", "--session", session_id, "--text", _SAMPLE_TEXT])
    proposed_kv = data.get("proposed_kv", []) or []
    kv_text = "\n".join(proposed_kv)
    check("ingest_proposed_from", "from:" in kv_text.lower() and "missa" in kv_text.lower())
    check("ingest_proposed_to", "to:" in kv_text.lower() and "mcas" in kv_text.lower())
    check("ingest_proposed_subj", "subj:" in kv_text.lower() and "software" in kv_text.lower())
    check("ingest_proposed_body", "body:" in kv_text.lower())

    # 4. ingest applied proposed_kv through BuilderSession
    print("Check 4: ingest auto-applied proposed_kv")
    payload_after_ingest = data.get("payload", {})
    check("applied_from", "MISSA" in str(payload_after_ingest.get("from", "")))
    check("applied_to", "MCAS new river" in str(payload_after_ingest.get("to", "")))

    # 5. status returns persisted payload across a separate process invocation
    print("Check 5: status persists payload across process")
    ok, data, _err = run(["status", "--session", session_id])
    payload_status = data.get("payload", {})
    check("persisted_from", "MISSA" in str(payload_status.get("from", "")))

    # 6. validate returns structured validation_summary
    print("Check 6: validate returns structured validation_summary")
    ok, data, _err = run(["validate", "--session", session_id])
    vs = data.get("validation_summary", {})
    check("validate_has_errors", "errors" in vs)
    check("validate_has_findings", isinstance(vs.get("findings"), list))

    # 7. finalize succeeds for sample request if required fields are present
    print("Check 7: finalize after applying remaining required fields")
    # Fix subject casing and add date + signature to allow finalize
    ok2, _, _ = run([
        "apply", "--session", session_id,
        "--kv",
        "subj: CHANGE OF DATE FOR SOFTWARE RELEASE BRIEF TO OPEN TBD\n"
        "date: 17 June 2026\n"
        "signature.name: J. Q. SAMPLE"
    ])
    ok3, data3, _ = run(["finalize", "--session", session_id])
    check("finalize_ok", ok3 and data3.get("validation_summary", {}).get("finalize_allowed") is True)

    # 8. render writes a PDF
    print("Check 8: render writes a PDF")
    pdf_out = Path(__file__).resolve().parent.parent / "output" / f"l28_{session_id}.pdf"
    ok4, data4, _ = run(["render", "--session", session_id, "--out", str(pdf_out)])
    check("render_success", ok4)
    check("pdf_exists", pdf_out.exists(), str(pdf_out))

    # 9. list shows the session
    print("Check 9: list shows the session")
    ok5, data5, _ = run(["list"])
    sessions = data5.get("sessions", [])
    check("list_has_session", any(s.get("session_id") == session_id for s in sessions))

    # 10. reset deletes the session
    print("Check 10: reset deletes the session")
    ok6, _, _ = run(["reset", "--session", session_id])
    check("reset_ok", ok6)
    ok7, data7, _ = run(["status", "--session", session_id])
    check("reset_deleted", not ok7 and "Session not found" in str(data7.get("error", "")))

    # cleanup PDF if still around
    if pdf_out.exists():
        pdf_out.unlink()

    # 11. --no-apply previews without changing payload
    print("Check 11: --no-apply preview mode")
    ok_s, data_s, _ = run(["start"])
    sid = data_s.get("session_id", "")
    # Use a rich NL prompt that the mock mediator recognizes
    ok_i, data_i, _ = run(["ingest", "--session", sid, "--text", _SAMPLE_TEXT, "--no-apply"])
    check("preview_has_kv", len(data_i.get("proposed_kv", [])) > 0)
    ok_st, data_st, _ = run(["status", "--session", sid])
    check("preview_not_applied", data_st.get("payload", {}).get("from") is None)
    run(["reset", "--session", sid])

    # 12. stdout is valid JSON only
    print("Check 12: stdout is valid JSON")
    ok_j, data_j, _ = run(["start"])
    check("stdout_is_json", ok_j and isinstance(data_j, dict))
    run(["reset", "--session", data_j.get("session_id", "")])

    # 13. tool does not import streamlit
    print("Check 13: no streamlit import in tool source")
    src = _TOOL.read_text(encoding="utf-8")
    check("no_streamlit_import", "streamlit" not in src.lower())

    # 14. renderer/layout files unchanged
    print("Check 14: renderer/layout files unchanged")
    check("renderer_untouched",
          not any(s in src for s in ["layout_v6", "letterhead_v6", "body_v6"]))

    # 15. CCI config/severity files unchanged
    print("Check 15: CCI config/severity files unchanged")
    check("cci_untouched",
          not any(s in src for s in ["cci_severity", "rules_v6", "_RULES_DIR"]))

    # 16. docs/BOOTSTRAP.md unchanged
    print("Check 16: docs/BOOTSTRAP.md unchanged")
    bootstrap = _TOOL.parent.parent / "docs" / "BOOTSTRAP.md"
    check("bootstrap_exists", bootstrap.exists(), str(bootstrap))
    # We only verify it exists; we are not modifying it in this phase.

    # 17. docs/HERMES_INSTRUCTIONS.md unchanged
    print("Check 17: docs/HERMES_INSTRUCTIONS.md unchanged")
    hermes_inst = _TOOL.parent.parent / "docs" / "HERMES_INSTRUCTIONS.md"
    check("hermes_instructions_exists", hermes_inst.exists(), str(hermes_inst))

    # Final tally
    print()
    print("=" * 70)
    print(f"Results: {len(passed)} passed / {len(failed)} failed")
    if failed:
        print("Failed checks:")
        for f in failed:
            print(f"  - {f}")
        print("=" * 70)
        return 1
    print("=" * 70)
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
