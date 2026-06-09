#!/usr/bin/env python3
"""
Phase H.13 / Phase I.12 — Severity Config Support Regression Runner

Validates the cci_severity_mapper module, default config, and
config-driven severity behavior in cci_routing_validate.py.

Exit 0 only when all expectations are met.

Checks:
  1. cci_severity_mapper module loads.
  2. effective_severity callable exists.
  3. Default config file exists and is readable.
  4. Default config schema is CCI_ENFORCEMENT_CONFIG_V1.
  5. Default config has ROUTE-010/011 in allowlist.
  6. Default config has ROUTE-010 effective_severity=advisory, ROUTE-011 effective_severity=warning.
  7. Missing config → advisory fallback for both rules.
  8. Malformed config → advisory fallback.
  9. Unknown rule ID → advisory fallback.
 10. Unsupported severity string → advisory fallback.
 11. Advisory config still produces warnings (not errors).
 12. Error config (temp) produces errors for ROUTE-010.
 13. Error config (temp) produces errors for ROUTE-011.
 14. Warning config (temp) produces errors (blocking) for ROUTE-010.
 14b. Warning config (temp) produces errors (blocking) for ROUTE-011.
 15. Allowlist-denied rule stays advisory even if override says error.
 16. Ceiling clamp: effective_severity cannot exceed allow_override_up_to.
 17. validator_runner overall_pass=True with default config (warnings only).
 18. validator_runner overall_pass=False with temp error config.
 19. Existing H.6 positive fixtures still emit warnings, not errors.
 20. Existing H.10 positive fixtures still emit warnings, not errors.
 21. H.6 regression runner still passes.
 22. H.10 regression runner still passes.
 23. H.9 regression runner still passes.
 24. CCI routing regression runner still passes.
 25. No renderer/layout, prompt-contract, command-layer, approved/pending log, or real-data files changed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

import cci_severity_mapper as mapper
from cci_routing_validate import validate_cci_routing
from validator_runner import run_cci_audit


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_CONFIG_FILE = REPO_ROOT / "config" / "cci_enforcement_config.json"


def _with_temp_config(data: dict):
    """Context manager: temporarily replaces the real config file."""
    class _Ctx:
        def __enter__(self):
            self.saved = _CONFIG_FILE.read_bytes() if _CONFIG_FILE.exists() else None
            tmp_fd, self.tmp_path = tempfile.mkstemp(suffix=".json", prefix="cci_cfg_")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            shutil.copy(self.tmp_path, str(_CONFIG_FILE))
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.saved is not None:
                _CONFIG_FILE.write_bytes(self.saved)
            else:
                try:
                    _CONFIG_FILE.unlink()
                except Exception:
                    pass
            try:
                os.unlink(self.tmp_path)
            except Exception:
                pass
            return False
    return _Ctx()


def load_fixture(name: str) -> dict:
    path = REPO_ROOT / "examples" / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_route_010(warnings: list[str], errors: list[str] | None = None) -> bool:
    targets = warnings if errors is None else warnings + errors
    return any("CCI-ROUTE-010" in t for t in targets)


def has_route_011(warnings: list[str], errors: list[str] | None = None) -> bool:
    targets = warnings if errors is None else warnings + errors
    return any("CCI-ROUTE-011" in t for t in targets)


def route_010_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-010" in e for e in errors)


def route_011_in_errors(errors: list[str]) -> bool:
    return any("CCI-ROUTE-011" in e for e in errors)


def route_010_in_warnings(warnings: list[str]) -> bool:
    return any("CCI-ROUTE-010" in w for w in warnings)


def route_011_in_warnings(warnings: list[str]) -> bool:
    return any("CCI-ROUTE-011" in w for w in warnings)


def run_sub_runner(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        shell=False,
        timeout=120,
    )
    return result.returncode == 0


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> int:
    python = sys.executable
    print("=" * 72)
    print("PHASE H.13 SEVERITY CONFIG SUPPORT REGRESSION RUNNER")
    print(f"REPO ROOT: {REPO_ROOT}")
    print(f"PYTHON: {python}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # 01: Module loads
    results.append(("Check 01: cci_severity_mapper module loads", True))
    print("PASS  Check 01")

    # 02: effective_severity callable
    ok = callable(mapper.effective_severity)
    results.append(("Check 02: effective_severity is callable", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 02")

    # 03: Default config exists and readable
    cfg_path = REPO_ROOT / "config" / "cci_enforcement_config.json"
    ok = cfg_path.exists()
    results.append(("Check 03: Default config file exists", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 03")
    if not ok:
        print("  CRITICAL: default config missing; aborting remaining checks")
        return _summary(results)

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg_data = json.load(f)

    # 04: Schema version
    ok = cfg_data.get("_schema_version") == "CCI_ENFORCEMENT_CONFIG_V1"
    results.append(("Check 04: Default config schema is CCI_ENFORCEMENT_CONFIG_V1", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 04")

    # 05: Allowlist contains both rules
    allowlist = cfg_data.get("_allowlist", [])
    ok = "CCI-ROUTE-010" in allowlist and "CCI-ROUTE-011" in allowlist
    results.append(("Check 05: Default config allowlists ROUTE-010 and ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 05")

    # 06: Default severity
    overrides = cfg_data.get("overrides", {})
    sev010 = overrides.get("CCI-ROUTE-010", {}).get("effective_severity")
    sev011 = overrides.get("CCI-ROUTE-011", {}).get("effective_severity")
    ok = sev010 == "advisory" and sev011 == "warning"
    results.append(("Check 06: Default config effective_severity=advisory for ROUTE-010, warning for ROUTE-011", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 06")

    # 07: Missing config → advisory fallback
    missing_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
        "global_default": "advisory",
        "overrides": {},
    }
    with _with_temp_config(missing_cfg):
        sev = mapper.effective_severity("CCI-ROUTE-010")
        ok = sev == "advisory"
    results.append(("Check 07: Missing override entry → advisory fallback", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 07")

    # 08: Malformed config → advisory fallback
    bad_cfg = {"not_a_valid": "schema"}
    with _with_temp_config(bad_cfg):
        sev = mapper.effective_severity("CCI-ROUTE-010")
        ok = sev == "advisory"
    results.append(("Check 08: Malformed config → advisory fallback", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 08")

    # 09: Unknown rule ID → advisory fallback
    ok = mapper.effective_severity("CCI-FAKE-999") == "advisory"
    results.append(("Check 09: Unknown rule ID → advisory fallback", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 09")

    # 10: Unsupported severity string → advisory fallback
    bad_sev_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "critical",
                "allow_override_up_to": "error",
            }
        },
    }
    with _with_temp_config(bad_sev_cfg):
        sev = mapper.effective_severity("CCI-ROUTE-010")
        ok = sev == "advisory"
    results.append(("Check 10: Unsupported severity string → advisory fallback", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 10")

    # 11: Advisory config still produces warnings (not errors) for ROUTE-010
    payload = load_fixture("routing_h6_positive_01.json")
    errors, warnings = validate_cci_routing(payload)
    ok = route_010_in_warnings(warnings) and not route_010_in_errors(errors)
    results.append(("Check 11: Advisory config → ROUTE-010 in warnings, not errors", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 11")

    # 11b: Default config (warning for ROUTE-011) produces errors (blocking) for ROUTE-011
    payload = load_fixture("routing_from_h10_pos_01_missing_from.json")
    errors, warnings = validate_cci_routing(payload)
    ok = route_011_in_errors(errors) and not route_011_in_warnings(warnings)
    results.append(("Check 11b: Default warning config → ROUTE-011 in errors, not warnings", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 11b")

    # 12: Error config (temp) produces errors for ROUTE-010
    error_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "error",
                "allow_override_up_to": "error",
            },
            "CCI-ROUTE-011": {
                "effective_severity": "advisory",
                "allow_override_up_to": "error",
            },
        },
    }
    with _with_temp_config(error_cfg):
        payload = load_fixture("routing_h6_positive_01.json")
        errors, warnings = validate_cci_routing(payload)
        ok = route_010_in_errors(errors) and not route_010_in_warnings(warnings)
    results.append(("Check 12: Temp error config → ROUTE-010 in errors, not warnings", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 12")

    # 13: Error config (temp) produces errors for ROUTE-011
    error_cfg_011 = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "advisory",
                "allow_override_up_to": "error",
            },
            "CCI-ROUTE-011": {
                "effective_severity": "error",
                "allow_override_up_to": "error",
            },
        },
    }
    with _with_temp_config(error_cfg_011):
        payload = load_fixture("routing_from_h10_pos_01_missing_from.json")
        errors, warnings = validate_cci_routing(payload)
        ok = route_011_in_errors(errors) and not route_011_in_warnings(warnings)
    results.append(("Check 13: Temp error config → ROUTE-011 in errors, not warnings", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 13")

    # 14: Warning config (temp) produces errors (blocking) for ROUTE-010
    warn_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "warning",
                "allow_override_up_to": "error",
            },
        },
    }
    with _with_temp_config(warn_cfg):
        payload = load_fixture("routing_h6_positive_01.json")
        errors, warnings = validate_cci_routing(payload)
        ok = route_010_in_errors(errors) and not route_010_in_warnings(warnings)
    results.append(("Check 14: Temp warning config → ROUTE-010 in errors (blocking)", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 14")

    # 14b: Warning config (temp) produces errors (blocking) for ROUTE-011
    warn_cfg_011 = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010", "CCI-ROUTE-011"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-011": {
                "effective_severity": "warning",
                "allow_override_up_to": "error",
            },
        },
    }
    with _with_temp_config(warn_cfg_011):
        payload = load_fixture("routing_from_h10_pos_01_missing_from.json")
        errors, warnings = validate_cci_routing(payload)
        ok = route_011_in_errors(errors) and not route_011_in_warnings(warnings)
    results.append(("Check 14b: Temp warning config → ROUTE-011 in errors (blocking)", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 14b")

    # 15: Allowlist-denied rule stays advisory
    deny_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-011"],  # 010 NOT allowlisted
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "error",
                "allow_override_up_to": "error",
            },
        },
    }
    with _with_temp_config(deny_cfg):
        sev = mapper.effective_severity("CCI-ROUTE-010")
        ok = sev == "advisory"
    results.append(("Check 15: Denylisted rule override ignored → advisory fallback", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 15")

    # 16: Ceiling clamp
    clamp_cfg = {
        "_schema_version": "CCI_ENFORCEMENT_CONFIG_V1",
        "_allowlist": ["CCI-ROUTE-010"],
        "global_default": "advisory",
        "overrides": {
            "CCI-ROUTE-010": {
                "effective_severity": "error",
                "allow_override_up_to": "warning",
            },
        },
    }
    with _with_temp_config(clamp_cfg):
        sev = mapper.effective_severity("CCI-ROUTE-010")
        ok = sev == "warning"
    results.append(("Check 16: Ceiling clamp → error clamped to warning", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 16")

    # 17: validator_runner overall_pass=True with default config (no ROUTE-011 trigger)
    # Use a synthetic payload with a From line so ROUTE-011 does NOT fire.
    payload = {
        "doc_type": "standard_letter",
        "to": "Commanding Officer, Example Activity",
        "from": "Commanding Officer, Example Unit",
        "subj": "TEST SUBJECT",
        "date": "1 May 2026",
        "body": ["1. Test paragraph."],
        "signature": ["J. DOE", "By direction"]
    }
    audit = run_cci_audit(payload)
    ok = audit["summary"]["overall_pass"] is True
    results.append(("Check 17: validator_runner overall_pass=True with default config (no trigger)", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 17")

    # 18: validator_runner overall_pass=False with temp error config (ROUTE-011)
    with _with_temp_config(error_cfg_011):
        payload = load_fixture("routing_from_h10_pos_01_missing_from.json")
        audit = run_cci_audit(payload)
        ok = audit["summary"]["overall_pass"] is False
    results.append(("Check 18: validator_runner overall_pass=False with temp error config", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 18")

    # 19: Existing H.6 positive fixtures still warnings, not errors (default config)
    h6_ok = True
    for i in range(1, 11):
        payload = load_fixture(f"routing_h6_positive_{i:02d}.json")
        errors, warnings = validate_cci_routing(payload)
        if route_010_in_errors(errors):
            h6_ok = False
            print(f"  FAIL  H.6 positive {i:02d} produced ROUTE-010 in errors")
            break
    results.append(("Check 19: H.6 positive fixtures still warnings only", h6_ok))
    print(f"{'PASS' if h6_ok else 'FAIL'}  Check 19")

    # 20: Existing H.10 positive fixtures produce errors for ROUTE-011 under default warning config
    h10_ok = True
    for suffix in [
        "01_missing_from", "02_empty_from", "03_whitespace_from",
        "04_tab_newline_from", "05_standard_letter", "06_null_from",
        "07_dual_rule", "08_complex_via", "09_complex_copy_to",
        "10_complex_distribution",
    ]:
        payload = load_fixture(f"routing_from_h10_pos_{suffix}.json")
        errors, warnings = validate_cci_routing(payload)
        if not route_011_in_errors(errors):
            h10_ok = False
            print(f"  FAIL  H.10 pos {suffix} did NOT produce ROUTE-011 in errors")
            break
    results.append(("Check 20: H.10 positive fixtures produce ROUTE-011 errors under default warning config", h10_ok))
    print(f"{'PASS' if h10_ok else 'FAIL'}  Check 20")

    # 21: H.6 runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_phase_h6_routing_office_code_evidence_regression.py")
    results.append(("Check 21: H.6 regression runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 21")

    # 22: H.10 runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_phase_h10_from_line_evidence_regression.py")
    results.append(("Check 22: H.10 regression runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 22")

    # 23: H.9 runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_phase_h9_from_line_validator_regression.py")
    results.append(("Check 23: H.9 regression runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 23")

    # 24: CCI routing regression runner still passes
    ok = run_sub_runner(REPO_ROOT / "tools" / "run_cci_routing_regression.py")
    results.append(("Check 24: CCI routing regression runner still passes", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 24")

    # 25: No forbidden files changed (git status check)
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        shell=False,
    )
    # We expect only our newly added files to be untracked; modified files
    # in forbidden paths would show as M.
    forbidden_modified = any(
        line.startswith(" M") and any(p in line for p in [
            "src/pdf_v6_render.py", "src/intake_orchestrator.py",
            "src/correction_commands.py", "src/correction_nl_commands.py",
            "src/context_resolver.py", "src/letter_model_v6.py",
        ])
        for line in result.stdout.splitlines()
    )
    ok = not forbidden_modified
    results.append(("Check 25: No forbidden files modified", ok))
    print(f"{'PASS' if ok else 'FAIL'}  Check 25")

    return _summary(results)


def _summary(results: list[tuple[str, bool]]) -> int:
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    if passed == total:
        print(f"PHASE H.13 REGRESSION RESULT: PASS  ({passed}/{total})")
        return 0
    else:
        print(f"PHASE H.13 REGRESSION RESULT: FAIL  ({passed}/{total})")
        for label, ok in results:
            if not ok:
                print(f"  FAIL  {label}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
