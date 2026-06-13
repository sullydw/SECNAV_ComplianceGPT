#!/usr/bin/env python3
"""
Phase L.7 Conversational Builder CLI Regression Runner

Covers scripted CLI/session behavior without manual input or PDF dependencies.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "tools" / "run_phase_l7_conversational_builder_cli.py"

_PASS = 0
_FAIL = 0


def _assert(condition: bool, message: str) -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"PASS: {message}")
    else:
        _FAIL += 1
        print(f"FAIL: {message}", file=sys.stderr)
        raise AssertionError(message)


def _load_cli_module() -> Any:
    spec = importlib.util.spec_from_file_location("phase_l7_cli", _CLI_PATH)
    _assert(spec is not None and spec.loader is not None, "CLI module spec loads")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_cli_file_exists() -> Any:
    print("\n=== TEST: cli_file_exists ===")
    _assert(_CLI_PATH.exists(), "L.7 CLI script exists")
    module = _load_cli_module()
    _assert(hasattr(module, "run_interactive"), "CLI exposes run_interactive()")
    _assert(hasattr(module, "run_scripted_sample"), "CLI exposes run_scripted_sample()")
    _assert(hasattr(module, "pdf_dependency_status"), "CLI exposes pdf_dependency_status()")
    return module


def test_scripted_accept_path(module: Any) -> None:
    print("\n=== TEST: scripted_accept_path ===")
    result = module.run_scripted_sample(accept_warnings=True)
    _assert(result.get("mode") == "scripted", "scripted mode returned")
    _assert(result.get("finalized") is True, "accept-warnings path finalizes")
    _assert(result.get("payload_json_valid") is True, "payload JSON is valid")
    _assert(isinstance(result.get("payload"), dict), "payload is a dict")
    _assert(result.get("payload", {}).get("doc_type") == "standard_letter", "payload doc_type preserved")
    _assert(result.get("audit_schema") == "CCI_AUDIT_V1", "audit schema is CCI_AUDIT_V1")
    _assert(isinstance(result.get("validation_summary"), dict), "validation summary is structured")
    _assert(isinstance(result.get("warning_summary"), list), "warning summary is a list")
    _assert(result.get("pdf", {}).get("status") in {"skipped", "available_not_run"}, "PDF status is non-failing")


def test_scripted_revise_path(module: Any) -> None:
    print("\n=== TEST: scripted_revise_path ===")
    result = module.run_scripted_sample(revise=True)
    _assert(result.get("mode") == "scripted", "scripted revise mode returned")
    _assert(result.get("finalized") is False, "revise path does not finalize")
    _assert(result.get("action") == "revise", "revise action recorded")
    _assert(isinstance(result.get("payload"), dict), "revise path returns current payload")
    _assert(isinstance(result.get("transcript"), list), "revise path returns transcript")


def test_subprocess_scripted_json() -> None:
    print("\n=== TEST: subprocess_scripted_json ===")
    proc = subprocess.run(
        [sys.executable, str(_CLI_PATH), "--scripted-sample", "--accept-warnings"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    _assert(proc.returncode == 0, "scripted CLI exits zero with accept-warnings")
    parsed = json.loads(proc.stdout)
    _assert(parsed.get("finalized") is True, "subprocess output finalized true")
    _assert(parsed.get("payload", {}).get("builder_version") == "L.5", "builder version preserved in payload")
    _assert(parsed.get("pdf", {}).get("status") in {"skipped", "available_not_run"}, "subprocess PDF status is non-failing")


def test_pdf_dependency_status(module: Any) -> None:
    print("\n=== TEST: pdf_dependency_status ===")
    status = module.pdf_dependency_status()
    _assert(status.get("status") in {"skipped", "available_not_run"}, "PDF dependency status does not fail")
    _assert(bool(status.get("reason")), "PDF dependency status has reason")


def test_no_renderer_or_config_mutation() -> None:
    print("\n=== TEST: no_renderer_or_config_mutation ===")
    protected_paths = [
        "src/pdf_v6_render.py",
        "src/audit_pdf_layout.py",
        "config/cci_enforcement_config.json",
    ]
    proc = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *protected_paths],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    _assert(proc.returncode == 0, "renderer/layout/config files unchanged relative to HEAD")


def main(argv: list[str] | None = None) -> int:
    print("=" * 70)
    print("Phase L.7 Conversational Builder CLI Regression Runner")
    print("=" * 70)

    try:
        module = test_cli_file_exists()
        test_scripted_accept_path(module)
        test_scripted_revise_path(module)
        test_subprocess_scripted_json()
        test_pdf_dependency_status(module)
        test_no_renderer_or_config_mutation()
    except AssertionError:
        print("\n" + "=" * 70, file=sys.stderr)
        print("REGRESSION FAILED", file=sys.stderr)
        print(f"PASSED: {_PASS}  FAILED: {_FAIL}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print("\n" + "=" * 70, file=sys.stderr)
        print(f"REGRESSION FAILED — invalid JSON output: {exc}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return 1

    print("\n" + "=" * 70)
    print(f"REGRESSION PASSED  ({_PASS} passed, {_FAIL} failed)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
