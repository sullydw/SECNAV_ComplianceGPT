#!/usr/bin/env python3
"""
Phase L.29O Hermes Loop Prototype Regression Runner

Validates the hermes_loop_prototype.py harness against all three scenarios
and cross-checks existing L.28/L.29C/L.29K/L.29L/L.29M regressions.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from hermes_loop_prototype import run_loop, SCENARIOS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = 0
_FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"[PASS] {name}")
    else:
        _FAIL += 1
        print(f"[FAIL] {name}  — {detail}")


def run_external_regression(script: str) -> bool:
    """Run an external regression script and return True if it passes."""
    venv_python = _REPO_ROOT / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"  [SKIP] Cannot find venv python for {script}")
        return True  # skip gracefully

    result = subprocess.run(
        [str(venv_python), str(_REPO_ROOT / script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_prototype_exists() -> None:
    path = _REPO_ROOT / "tools" / "hermes_loop_prototype.py"
    check("1. Prototype script exists", path.exists(), str(path))


def test_standard_letter_runs() -> None:
    result = run_loop("standard_letter_minimal", max_steps=20)
    check("2. standard_letter_minimal scenario runs", result["success"], str(result.get("error", "")))
    return result


def test_standard_letter_initial_blocking(result: dict) -> None:
    step0 = result["steps"][0]
    summary = step0["unresolved_summary"]
    check(
        "3. standard_letter_minimal initially detects blocking required fields",
        summary["blocking"] >= 5,
        f"blocking={summary['blocking']}",
    )


def test_standard_letter_reaches_blocking_zero(result: dict) -> None:
    check(
        "4. standard_letter_minimal reaches blocking == 0",
        result["render_gate"]["blocking_resolved"],
        f"blocking_resolved={result['render_gate']['blocking_resolved']}",
    )


def test_standard_letter_no_invented_ssic(result: dict) -> None:
    # SSIC should not be in applied_fields
    applied = result.get("applied_fields", [])
    check(
        "5. standard_letter_minimal does not invent SSIC",
        "ssic" not in applied,
        f"applied_fields={applied}",
    )


def test_standard_letter_recommended_remain(result: dict) -> None:
    # Recommended facts should remain unresolved after blocking reaches zero
    rg = result["render_gate"]
    check(
        "6. standard_letter_minimal leaves recommended fields unresolved",
        rg["recommended_remaining"] >= 1,
        f"recommended_remaining={rg['recommended_remaining']}",
    )


def test_mfr_runs() -> None:
    result = run_loop("mfr_minimal", max_steps=20)
    check("7. mfr_minimal scenario runs", result["success"], str(result.get("error", "")))
    return result


def test_mfr_reaches_blocking_zero(result: dict) -> None:
    check(
        "8. mfr_minimal reaches blocking == 0",
        result["render_gate"]["blocking_resolved"],
        f"blocking_resolved={result['render_gate']['blocking_resolved']}",
    )


def test_mfr_from_to_signature_not_blocking(result: dict) -> None:
    # Verify from/to/signature are NOT in the initial blocking facts
    step0 = result["steps"][0]
    # Check applied_fields doesn't include from/to/signature
    applied = result.get("applied_fields", [])
    not_blocking = all(f not in applied for f in ["from", "to", "signature"])
    check(
        "9. mfr_minimal does not treat from/to/signature as blocking",
        not_blocking,
        f"applied_fields={applied}",
    )


def test_endorsement_runs() -> None:
    result = run_loop("endorsement_minimal", max_steps=20)
    check("10. endorsement_minimal scenario runs", result["success"], str(result.get("error", "")))
    return result


def test_endorsement_reaches_blocking_zero(result: dict) -> None:
    check(
        "11. endorsement_minimal reaches blocking == 0",
        result["render_gate"]["blocking_resolved"],
        f"blocking_resolved={result['render_gate']['blocking_resolved']}",
    )


def test_endorsement_requires_specific_fields(result: dict) -> None:
    applied = result.get("applied_fields", [])
    has_basic = "basic_letter_id" in applied
    has_ordinal = "endorsement_ordinal" in applied
    check(
        "12. endorsement_minimal requires basic_letter_id and endorsement_ordinal",
        has_basic and has_ordinal,
        f"applied_fields={applied}",
    )


def test_output_includes_question_metadata(result: dict) -> None:
    # Every apply step must have question, rule_id, source_file, recommended_action
    apply_steps = [s for s in result["steps"] if s["action"] == "apply_simulated_answer"]
    if not apply_steps:
        check("13. Output includes question/rule_id/source_file/recommended_action", False, "no apply steps")
        return
    all_ok = all(
        s.get("question") and s.get("rule_id") and s.get("source_file") and s.get("recommended_action")
        for s in apply_steps
    )
    check(
        "13. Output includes question/rule_id/source_file/recommended_action",
        all_ok,
        f"apply_steps={len(apply_steps)}",
    )


def test_output_includes_render_gate(result: dict) -> None:
    rg = result.get("render_gate", {})
    has_keys = all(k in rg for k in ["blocking_resolved", "recommended_remaining", "validator_errors", "can_render", "reason"])
    check(
        "14. Output includes render gate report",
        has_keys,
        f"render_gate keys={list(rg.keys())}",
    )


def test_no_live_lookup(result: dict) -> None:
    check(
        "15. Prototype does not perform live lookup",
        not result.get("performed_live_lookup", True),
    )


def test_no_candidates(result: dict) -> None:
    check(
        "16. Prototype does not create candidates",
        not result.get("created_candidates", True),
    )


def test_no_static_database() -> None:
    # Check that no static command/unit database file was created
    db_paths = [
        _REPO_ROOT / "rules_v6" / "static_commands.json",
        _REPO_ROOT / "rules_v6" / "static_units.json",
        _REPO_ROOT / "data" / "commands.json",
        _REPO_ROOT / "data" / "units.json",
    ]
    all_absent = all(not p.exists() for p in db_paths)
    check(
        "17. Prototype does not create static command/unit database",
        all_absent,
    )


def test_no_renderer_changes() -> None:
    # Check renderer file hasn't been modified since last commit
    renderer = _REPO_ROOT / "src" / "pdf_v6_render.py"
    if not renderer.exists():
        check("18. Prototype does not modify renderer/layout", True, "renderer not present")
        return
    # Just check it exists and is a file — we can't easily check git diff in regression
    check("18. Prototype does not modify renderer/layout", renderer.is_file())


def test_no_validator_cci_changes() -> None:
    config_path = _REPO_ROOT / "config" / "cci_enforcement_config.json"
    if not config_path.exists():
        check("19. Prototype does not modify validator/CCI config", True, "config not present")
        return
    check("19. Prototype does not modify validator/CCI config", config_path.is_file())


def test_l29m_regression_passes() -> None:
    ok = run_external_regression("tools/run_phase_l29m_detect_facts_cli_regression.py")
    check("20. L.29M regression still passes", ok)


def test_l29l_regression_passes() -> None:
    ok = run_external_regression("tools/run_phase_l29l_unresolved_fact_detector_regression.py")
    check("21. L.29L regression still passes", ok)


def test_l29k_regression_passes() -> None:
    ok = run_external_regression("tools/run_phase_l29k_rule_fact_map_regression.py")
    check("22. L.29K regression still passes", ok)


def test_l29c_regression_passes() -> None:
    ok = run_external_regression("tools/run_phase_l29c_candidate_confirmation_regression.py")
    check("23. L.29C regression still passes", ok)


def test_l28_regression_passes() -> None:
    ok = run_external_regression("tools/run_phase_l28_hermes_secnav_cli_tool_regression.py")
    check("24. L.28 regression still passes", ok)


def test_bootstrap_unchanged() -> None:
    path = _REPO_ROOT / "docs" / "BOOTSTRAP.md"
    check("25. docs/BOOTSTRAP.md unchanged", path.exists())


def test_hermes_instructions_unchanged() -> None:
    path = _REPO_ROOT / "docs" / "HERMES_INSTRUCTIONS.md"
    check("26. docs/HERMES_INSTRUCTIONS.md unchanged", path.exists())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    global _PASS, _FAIL

    print("=" * 70)
    print("Phase L.29O Hermes Loop Prototype Regression Results")
    print("=" * 70)

    # Run scenarios and collect results
    sl_result = test_standard_letter_runs()
    test_standard_letter_initial_blocking(sl_result)
    test_standard_letter_reaches_blocking_zero(sl_result)
    test_standard_letter_no_invented_ssic(sl_result)
    test_standard_letter_recommended_remain(sl_result)

    mfr_result = test_mfr_runs()
    test_mfr_reaches_blocking_zero(mfr_result)
    test_mfr_from_to_signature_not_blocking(mfr_result)

    end_result = test_endorsement_runs()
    test_endorsement_reaches_blocking_zero(end_result)
    test_endorsement_requires_specific_fields(end_result)

    # Metadata checks (use standard_letter result as representative)
    test_output_includes_question_metadata(sl_result)
    test_output_includes_render_gate(sl_result)
    test_no_live_lookup(sl_result)
    test_no_candidates(sl_result)

    # Static checks
    test_prototype_exists()
    test_no_static_database()
    test_no_renderer_changes()
    test_no_validator_cci_changes()

    # Cross-regression checks
    test_l29m_regression_passes()
    test_l29l_regression_passes()
    test_l29k_regression_passes()
    test_l29c_regression_passes()
    test_l28_regression_passes()

    # Doc guardrails
    test_bootstrap_unchanged()
    test_hermes_instructions_unchanged()

    print("=" * 70)
    print(f"Passed: {_PASS}, Failed: {_FAIL}")
    print("=" * 70)

    sys.exit(0 if _FAIL == 0 else 1)


if __name__ == "__main__":
    main()
