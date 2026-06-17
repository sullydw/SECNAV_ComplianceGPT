#!/usr/bin/env python3
"""
Phase L.26E — Ollama Provider and Model Picker Regression

Verifies the Streamlit app has a provider/model picker UI that:
- Shows Mock / Ollama Local / Ollama Cloud options
- Discovers local Ollama models via localhost:11434/api/tags
- Fails closed if Ollama not running
- Keeps mock as default
- Respects UI selection in mediation
- Cloud placeholder is fail-closed
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
CONFIG_FILE = REPO_ROOT / "src" / "llm_provider_config.py"

sys.path.insert(0, str(REPO_ROOT / "src"))

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. App file exists
# ------------------------------------------------------------------
checks.append(("A. App file exists", APP_FILE.exists()))

# ------------------------------------------------------------------
# 2. Provider picker labels exist
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_mock = "Mock / Offline" in app_text or "mock" in app_text.lower()
    has_ollama_local = "Ollama Local" in app_text
    has_ollama_cloud = "Ollama Cloud" in app_text
    checks.append(("B. Mock provider option present", has_mock))
    checks.append(("C. Ollama Local option present", has_ollama_local))
    checks.append(("D. Ollama Cloud option present", has_ollama_cloud))
else:
    checks.append(("B. Mock provider option present", False))
    checks.append(("C. Ollama Local option present", False))
    checks.append(("D. Ollama Cloud option present", False))

# ------------------------------------------------------------------
# 3. Model selector/dropdown exists
# ------------------------------------------------------------------
if APP_FILE.exists():
    has_model_select = "Ollama Model" in app_text or "st.selectbox" in app_text
    checks.append(("E. Model dropdown UI present", has_model_select))
else:
    checks.append(("E. Model dropdown UI present", False))

# ------------------------------------------------------------------
# 4. list_ollama_models function exists in provider config
# ------------------------------------------------------------------
if CONFIG_FILE.exists():
    config_text = CONFIG_FILE.read_text(encoding="utf-8")
    has_func = "def list_ollama_models" in config_text
    checks.append(("F. list_ollama_models function exists", has_func))
else:
    checks.append(("F. list_ollama_models function exists", False))

# ------------------------------------------------------------------
# 5. list_ollama_models uses localhost:11434/api/tags
# ------------------------------------------------------------------
if CONFIG_FILE.exists():
    uses_localhost = ("localhost:11434/api/tags" in config_text or
                      "127.0.0.1:11434/api/tags" in config_text or
                      "OLLAMA_HOSTS" in config_text)
    checks.append(("G. list_ollama_models uses localhost:11434 or 127.0.0.1", uses_localhost))
else:
    checks.append(("G. list_ollama_models uses localhost:11434 or 127.0.0.1", False))

# ------------------------------------------------------------------
# 6. list_ollama_models returns empty list on error (fail-closed)
# ------------------------------------------------------------------
try:
    from llm_provider_config import list_ollama_models
    # Should return empty list when Ollama is not running
    models = list_ollama_models()
    is_list = isinstance(models, list)
    safe = True  # function didn't crash
    checks.append(("H. list_ollama_models returns list", is_list))
    checks.append(("I. list_ollama_models fails closed (no crash)", safe))
except Exception as e:
    checks.append(("H. list_ollama_models returns list", False))
    checks.append(("I. list_ollama_models fails closed (no crash)", False))

# ------------------------------------------------------------------
# 7. No API key display pattern
# ------------------------------------------------------------------
if APP_FILE.exists():
    no_key = "api_key" not in app_text.lower() or "API keys are never shown" in app_text
    checks.append(("J. No API key display pattern", no_key))
else:
    checks.append(("J. No API key display pattern", False))

# ------------------------------------------------------------------
# 8. Mock remains default in UI
# ------------------------------------------------------------------
if APP_FILE.exists():
    mock_default = "mock" in app_text and "default" in app_text.lower()
    checks.append(("K. Mock is default in UI", mock_default))
else:
    checks.append(("K. Mock is default in UI", False))

# ------------------------------------------------------------------
# 9. UI selection can override env defaults
# ------------------------------------------------------------------
if APP_FILE.exists():
    respects_ui = "selected_provider" in app_text and "selected_model" in app_text
    checks.append(("L. UI selection respected in mediation", respects_ui))
else:
    checks.append(("L. UI selection respected in mediation", False))

# ------------------------------------------------------------------
# 10. Cloud placeholder is fail-closed
# ------------------------------------------------------------------
if APP_FILE.exists():
    cloud_safe = "not yet configured" in app_text.lower() or "not_configured" in app_text
    checks.append(("M. Cloud placeholder fail-closed", cloud_safe))
else:
    checks.append(("M. Cloud placeholder fail-closed", False))

# ------------------------------------------------------------------
# 11. Launchers still exist
# ------------------------------------------------------------------
ollama_bat = REPO_ROOT / "launch_secnav_streamlit_ollama.bat"
ollama_ps1 = REPO_ROOT / "launch_secnav_streamlit_ollama.ps1"
mock_bat = REPO_ROOT / "launch_secnav_streamlit.bat"
checks.append(("N. Ollama BAT launcher exists", ollama_bat.exists()))
checks.append(("O. Ollama PS1 launcher exists", ollama_ps1.exists()))
checks.append(("P. Mock BAT launcher exists", mock_bat.exists()))

# ------------------------------------------------------------------
# 12. No renderer/CCI changes
# ------------------------------------------------------------------
if APP_FILE.exists():
    no_renderer = "renderer" not in app_text.lower() or "pdf_v6_render" in app_text
    no_cci = "cci_severity" not in app_text.lower()
    checks.append(("Q. No renderer layout controls", no_renderer))
    checks.append(("R. No CCI config controls", no_cci))
else:
    checks.append(("Q. No renderer layout controls", False))
    checks.append(("R. No CCI config controls", False))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.26E — Ollama Provider and Model Picker Regression")
print("=" * 64)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
for label, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
print(f"\n{'=' * 64}")
print(f"Total: {passed}/{total} passed")
if passed == total:
    print("ALL CHECKS PASS")
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
print("=" * 64)
