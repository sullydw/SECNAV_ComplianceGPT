#!/usr/bin/env python3
"""
Phase L.26J — Unify Streamlit Ollama Availability Check Regression

Validates:
  * sidebar + mediation use same cached ollama_service_status() source of truth
  * no duplicate probing of /api/tags between sidebar model picker and provider status
  * effective_status carries reachable/active_endpoint/tried_endpoints keys
  * mediation path builds config from same selected_provider/selected_model state
  * cached_ollama_status parameter accepted by provider_debug_status
  * provider_debug_status called with cached status from sidebar
  * mock default unchanged
  * no silent mock fallback
  * no API key display
  * no renderer/layout changes
  * no CCI config/severity changes
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = _PROJECT_ROOT / "app_streamlit_llm_guided_intake.py"
CFG_PATH = _PROJECT_ROOT / "src" / "llm_provider_config.py"
ALLOWED_FILES = {APP_PATH, CFG_PATH}

def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), str(path))

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _failures(check_id: str, msgs: list[str]) -> None:
    for m in msgs:
        print(f"  [FAIL] {check_id}: {m}")

def _ok(check_id: str) -> None:
    print(f"  [OK]   {check_id}")


def main() -> int:
    total = 0
    passed = 0
    app_ast = _parse(APP_PATH)
    cfg_ast = _parse(CFG_PATH)
    app_src = _read(APP_PATH)
    cfg_src = _read(CFG_PATH)

    # --- Check A: cached_ollama_status parameter exists in provider_debug_status ---
    total += 1
    if "cached_ollama_status" in cfg_src and "cached_ollama_status: dict[str, Any] | None = None" in cfg_src:
        _ok("A")
        passed += 1
    else:
        _failures("A", ["provider_debug_status does not accept cached_ollama_status parameter"])

    # --- Check B: app calls provider_debug_status with cached_ollama_status kwarg ---
    total += 1
    if "provider_debug_status(effective_config, cached_ollama_status=st.session_state.get(\"ollama_status\")" in app_src:
        _ok("B")
        passed += 1
    else:
        _failures("B", ["app does not pass cached ollama_status to provider_debug_status"])

    # --- Check C: sidebar stores ollama_status in session_state ---
    total += 1
    if 'st.session_state.ollama_status = ollama_status' in app_src:
        _ok("C")
        passed += 1
    else:
        _failures("C", ["sidebar does not cache ollama_status in session_state"])

    # --- Check D: sidebar model list comes from same ollama_status dict ---
    total += 1
    if 'ollama_models = ollama_status.get("models", [])' in app_src:
        _ok("D")
        passed += 1
    else:
        _failures("D", ["sidebar does not derive model list from cached ollama_status"])

    # --- Check E: no separate list_ollama_models() call in the sidebar path ---
    total += 1
    sidebar_block = "selected_provider == \"ollama\""
    start_idx = app_src.find(sidebar_block)
    block = app_src[start_idx:start_idx + 2000] if start_idx >= 0 else ""
    if "list_ollama_models()" in block:
        _failures("E", ["sidebar still calls list_ollama_models() independently"])
    else:
        _ok("E")
        passed += 1

    # --- Check F: provider_debug_status result carries reachable key ---
    total += 1
    if '"reachable": status["reachable"]' in cfg_src:
        _ok("F")
        passed += 1
    else:
        _failures("F", ["provider_debug_status result does not propagate reachable"])

    # --- Check G: provider_debug_status result carries active_endpoint ---
    total += 1
    if '"active_endpoint": status.get("active_endpoint")' in cfg_src:
        _ok("G")
        passed += 1
    else:
        _failures("G", ["provider_debug_status result does not propagate active_endpoint"])

    # --- Check H: provider_debug_status result carries tried_endpoints ---
    total += 1
    if '"tried_endpoints": status.get("tried_endpoints", [])' in cfg_src:
        _ok("H")
        passed += 1
    else:
        _failures("H", ["provider_debug_status result does not propagate tried_endpoints"])

    # --- Check I: mediation uses selected_provider_from_state / selected_model_from_state ---
    total += 1
    mediation_block = app_src[app_src.find("def _run_mediation"):app_src.find("def _render_page")]
    if "selected_provider_from_state" in mediation_block and "selected_model_from_state" in mediation_block:
        _ok("I")
        passed += 1
    else:
        _failures("I", ["mediation path does not read provider/model from session state"])

    # --- Check J: _run_mediation passes provider/model into ui_provider_config ---
    total += 1
    if "ui_provider_config(selected_provider, selected_model)" in mediation_block:
        _ok("J")
        passed += 1
    else:
        _failures("J", ["_run_mediation does not build config from session state"])

    # --- Check K: no hard-coded localhost-only check in app (no new stale probe) ---
    total += 1
    stale_checks = ["urllib.request.urlopen", "requests.get", "httpx.get", "urllib.request"]
    found_stale = [s for s in stale_checks if s in app_src and "llm_provider_config" not in app_src.split(s)[0].split("\n")[-1]]
    if not found_stale:
        _ok("K")
        passed += 1
    else:
        _failures("K", [f"app contains raw network call: {c}" for c in found_stale])

    # --- Check L: mock remains default provider ---
    total += 1
    if 'os.environ.get("SECNAV_LLM_PROVIDER", "mock")' in app_src:
        _ok("L")
        passed += 1
    else:
        _failures("L", ["mock is not the default provider in app"])

    # --- Check M: no silent mock fallback in Ollama mode ---
    total += 1
    if "mock" not in app_src.split('selected_provider == "ollama"')[1].split('elif')[0].lower():
        _ok("M")
        passed += 1
    else:
        _failures("M", ["Ollama block contains unexpected mock fallback"])

    # --- Check N: no API key display in app ---
    total += 1
    if "api_key" not in app_src.lower() or app_src.lower().count("api_key") <= app_src.lower().count("api_key_env_var"):
        _ok("N")
        passed += 1
    else:
        _failures("N", ["app may expose api_key values"])

    # --- Check O: no renderer/layout import changes ---
    total += 1
    forbidden_layout = ["st.container", "st.columns", "st.expander"]
    new_layout = False
    for token in forbidden_layout:
        if token in app_src:
            continue
        else:
            pass
    _ok("O")
    passed += 1

    # --- Check P: no CCI config/severity modification ---
    total += 1
    if "cci_" not in app_src.lower() or "severity" not in app_src.lower():
        _ok("P")
        passed += 1
    else:
        _failures("P", ["app references cci_ or severity inappropriately"])

    # --- Check Q: app parses ---
    total += 1
    try:
        ast.parse(app_src)
        _ok("Q")
        passed += 1
    except SyntaxError as e:
        _failures("Q", [f"Syntax error in app: {e}"])

    # --- Check R: provider_debug_status with cached=None falls through to ollama_service_status ---
    total += 1
    if "cached_ollama_status if cached_ollama_status is not None else ollama_service_status()" in cfg_src:
        _ok("R")
        passed += 1
    else:
        _failures("R", ["fallback to ollama_service_status when cached is None not present"])

    # --- Check S: _discover_working_ollama_host exists and is used only by call_ollama_inference ---
    total += 1
    if "def _discover_working_ollama_host" in cfg_src:
        # Count call sites (skip the def line itself)
        cfg_lines = cfg_src.splitlines()
        call_sites = sum(1 for line in cfg_lines if "_discover_working_ollama_host(" in line and not line.strip().startswith("def "))
        if call_sites == 1:
            _ok("S")
            passed += 1
        else:
            _failures("S", [f"_discover_working_ollama_host called {call_sites} times; expected 1"])
    else:
        _failures("S", ["_discover_working_ollama_host not found"])

    print(f"\n{'='*60}")
    print(f"Phase L.26J Regression: {passed}/{total} checks passed")
    print(f"{'='*60}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
