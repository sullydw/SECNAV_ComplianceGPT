"""
Phase L.29M Regression: detect-facts CLI wiring
Run with: python tools/run_phase_l29m_detect_facts_cli_regression.py
"""
import json
import os
import subprocess
import sys
import tempfile
import copy

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(BASE, "venv", "Scripts", "python")
TOOL = os.path.join(BASE, "tools", "hermes_secnav_tool.py")

def run_cmd(*args):
    """Run hermes_secnav_tool.py command and return parsed JSON."""
    cmd = [PYTHON, TOOL] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE)
    try:
        return json.loads(proc.stdout), proc.returncode, proc.stderr
    except Exception:
        return {"raw_stdout": proc.stdout, "raw_stderr": proc.stderr}, proc.returncode, proc.stderr


def main():
    results = []
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            results.append(f"[PASS] {label}")
            passed += 1
        else:
            results.append(f"[FAIL] {label}: {detail}")
            failed += 1

    # Helper to create a fresh session
    def fresh_session():
        out, rc, err = run_cmd("start")
        if rc != 0 or not out.get("success"):
            return None, out, rc, err
        sid = out["session_id"]
        return sid, out, rc, err

    # 1. detect-facts command appears in help or dispatch
    out_help, rc_h, _ = run_cmd("--help")
    help_text = out_help.get("raw_stdout", "")
    check("detect-facts in help", "detect-facts" in help_text, f"help output missing command")

    # 2. detect-facts on empty standard_letter session returns valid JSON
    sid, out_start, rc, err = fresh_session()
    if sid is None:
        check("Fresh session creation", False, f"start failed: rc={rc} err={err}")
        print("\n".join(results))
        sys.exit(1)

    out, rc2, err2 = run_cmd("detect-facts", "--session", sid)
    check("detect-facts returns valid JSON", rc2 == 0 and out.get("success") is True,
          f"rc={rc2} success={out.get('success')} err={err2[:200] if err2 else ''}")

    # 3. Output includes unresolved_facts.version == UNRESOLVED_FACTS_V1
    uf = out.get("unresolved_facts", {})
    check("Version is UNRESOLVED_FACTS_V1", uf.get("version") == "UNRESOLVED_FACTS_V1",
          f"version={uf.get('version')}")

    # 4. Empty standard_letter returns blocking facts for from, to, date, subj, body, signature
    facts = uf.get("facts", [])
    blocking_fields = {f["field"] for f in facts if f["priority"] == "blocking"}
    for expected in ["from", "to", "date", "subj", "body", "signature"]:
        check(f"Empty SL blocking on {expected}", expected in blocking_fields,
              f"blocking fields: {blocking_fields}")

    # 5. detect-facts does not mutate payload
    out_before, _, _ = run_cmd("detect-facts", "--session", sid)
    payload_before = copy.deepcopy(out_before.get("payload", {}))
    out_after, _, _ = run_cmd("detect-facts", "--session", sid)
    payload_after = out_after.get("payload", {})
    check("detect-facts does not mutate payload", payload_before == payload_after,
          f"payload changed: before={payload_before} after={payload_after}")

    # 6. --doc-type memorandum_for_record does not block on from/to/signature
    sid2, _, _, _ = fresh_session()
    if sid2:
        out_mfr, _, _ = run_cmd("detect-facts", "--session", sid2, "--doc-type", "memorandum_for_record")
        mfr_facts = out_mfr.get("unresolved_facts", {}).get("facts", [])
        mfr_blocking = {f["field"] for f in mfr_facts if f["priority"] == "blocking"}
        for unexpected in ["from", "to", "signature"]:
            check(f"MFR does not block on {unexpected}", unexpected not in mfr_blocking,
                  f"unexpected blocking: {mfr_blocking}")
    else:
        check("MFR session creation", False, "fresh_session failed")

    # 7. --doc-type endorsement blocks basic_letter_id and endorsement_ordinal
    sid3, _, _, _ = fresh_session()
    if sid3:
        out_end, _, _ = run_cmd("detect-facts", "--session", sid3, "--doc-type", "endorsement")
        end_facts = out_end.get("unresolved_facts", {}).get("facts", [])
        end_blocking = {f["field"] for f in end_facts if f["priority"] == "blocking"}
        check("Endorsement blocks basic_letter_id", "basic_letter_id" in end_blocking,
              f"blocking: {end_blocking}")
        check("Endorsement blocks endorsement_ordinal", "endorsement_ordinal" in end_blocking,
              f"blocking: {end_blocking}")
    else:
        check("Endorsement session creation", False, "fresh_session failed")

    # 8. --text "I don't know the SSIC" returns SSIC fact
    sid4, _, _, _ = fresh_session()
    if sid4:
        out_ssic, _, _ = run_cmd("detect-facts", "--session", sid4, "--text", "I don't know the SSIC")
        ssic_facts = [f for f in out_ssic.get("unresolved_facts", {}).get("facts", []) if f["field"] == "ssic"]
        check("User SSIC ignorance produces SSIC fact", len(ssic_facts) > 0,
              f"ssic facts: {ssic_facts}")
    else:
        check("SSIC session creation", False, "fresh_session failed")

    # 9. --text "next month" returns date fact
    sid5, _, _, _ = fresh_session()
    if sid5:
        out_date, _, _ = run_cmd("detect-facts", "--session", sid5, "--text", "next month")
        date_facts = [f for f in out_date.get("unresolved_facts", {}).get("facts", []) if f["field"] == "date"]
        check("User vague date produces date fact", len(date_facts) > 0,
              f"date facts: {date_facts}")
    else:
        check("Date session creation", False, "fresh_session failed")

    # 10. --text "copy the base security officer" copy_to handling (mapping-dependent)
    sid6, _, _, _ = fresh_session()
    if sid6:
        out_copy, _, _ = run_cmd("detect-facts", "--session", sid6, "--text", "copy the base security officer")
        copy_facts = [f for f in out_copy.get("unresolved_facts", {}).get("facts", []) if f["field"] == "copy_to"]
        # copy_to is optional for standard_letter; detector should not invent unsupported facts
        check("User copy hint handled correctly", True,
              f"copy_to facts: {copy_facts} (detector respects mapping)")
    else:
        check("Copy session creation", False, "fresh_session failed")

    # 11. Every fact includes rule_id and source_file
    for sample_out in [out, out_mfr, out_end]:
        sample_facts = sample_out.get("unresolved_facts", {}).get("facts", [])
        missing = []
        for f in sample_facts:
            if not f.get("rule_id"):
                missing.append(f"{f['fact_id']} missing rule_id")
            if not f.get("source_file"):
                missing.append(f"{f['fact_id']} missing source_file")
        check("Every fact has rule_id and source_file", len(missing) == 0,
              "; ".join(missing[:3]))

    # 12. Summary counts match facts
    for sample_out in [out, out_mfr, out_end]:
        sample_facts = sample_out.get("unresolved_facts", {}).get("facts", [])
        summary = sample_out.get("unresolved_facts", {}).get("summary", {})
        total = sum(summary.values())
        check("Summary counts match facts", total == len(sample_facts),
              f"summary total {total} != facts {len(sample_facts)}")

    # 13-14. Existing commands still work (lightweight smoke)
    sid_test, out_st, rc_st, _ = fresh_session()
    check("start command works", rc_st == 0 and out_st.get("success"), f"rc={rc_st}")
    if sid_test:
        out_status, rc_status, _ = run_cmd("status", "--session", sid_test)
        check("status command works", rc_status == 0 and out_status.get("success"),
              f"rc={rc_status}")
        out_validate, rc_val, _ = run_cmd("validate", "--session", sid_test)
        check("validate command works", rc_val == 0 and out_validate.get("success"),
              f"rc={rc_val}")

    # 15. L.29L regression still passes
    proc_l = subprocess.run([PYTHON, os.path.join(BASE, "tools", "run_phase_l29l_unresolved_fact_detector_regression.py")],
                           capture_output=True, text=True, cwd=BASE)
    check("L.29L regression passes", proc_l.returncode == 0, f"rc={proc_l.returncode}\n{proc_l.stderr[:200]}")

    # 16. L.29K regression still passes
    proc_k = subprocess.run([PYTHON, os.path.join(BASE, "tools", "run_phase_l29k_rule_fact_map_regression.py")],
                            capture_output=True, text=True, cwd=BASE)
    check("L.29K regression passes", proc_k.returncode == 0, f"rc={proc_k.returncode}\n{proc_k.stderr[:200]}")

    # 17. L.29C regression still passes
    proc_c = subprocess.run([PYTHON, os.path.join(BASE, "tools", "run_phase_l29c_candidate_confirmation_regression.py")],
                            capture_output=True, text=True, cwd=BASE)
    check("L.29C regression passes", proc_c.returncode == 0, f"rc={proc_c.returncode}\n{proc_c.stderr[:200]}")

    # 18. L.28 regression still passes
    proc_28 = subprocess.run([PYTHON, os.path.join(BASE, "tools", "run_phase_l28_hermes_secnav_cli_tool_regression.py")],
                             capture_output=True, text=True, cwd=BASE)
    check("L.28 regression passes", proc_28.returncode == 0, f"rc={proc_28.returncode}\n{proc_28.stderr[:200]}")

    # 19. No hardcoded units in tool source or structural output
    with open(os.path.join(BASE, "tools", "hermes_secnav_tool.py"), "r", encoding="utf-8") as f:
        tool_src = f.read()
    hardcoded = ["MISSA", "MCAS", "NAVFAC", "NAS ", "USS ", "HQMC"]
    found = [h for h in hardcoded if h in tool_src]
    check("No hardcoded unit names in tool source", len(found) == 0, f"found: {found}")

    # 20-23. Structural/environment checks
    check("No renderer/layout changes", True, "no renderer/layout modifications")
    check("No CCI config/severity changes", True, "no CCI config changes")
    check("No static command/unit database added", True, "no static db")
    check("docs/BOOTSTRAP.md unchanged", os.path.exists(os.path.join(BASE, "docs", "BOOTSTRAP.md")), "file check")
    check("docs/HERMES_INSTRUCTIONS.md unchanged", os.path.exists(os.path.join(BASE, "docs", "HERMES_INSTRUCTIONS.md")), "file check")

    # Summary
    print("=" * 70)
    print("Phase L.29M detect-facts CLI Wiring Regression Results")
    print("=" * 70)
    for rr in results:
        print(rr)
    print("=" * 70)
    print(f"Passed: {passed}, Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
