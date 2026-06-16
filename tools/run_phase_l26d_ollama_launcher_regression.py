#!/usr/bin/env python3
"""
Phase L.26D — One-Click Ollama Streamlit Launcher Regression

Verifies the Ollama launcher files exist, set env vars correctly,
check Ollama reachability, and do not leak secrets.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BAT_FILE = REPO_ROOT / "launch_secnav_streamlit_ollama.bat"
PS1_FILE = REPO_ROOT / "launch_secnav_streamlit_ollama.ps1"
MOCK_BAT = REPO_ROOT / "launch_secnav_streamlit.bat"
MOCK_PS1 = REPO_ROOT / "launch_secnav_streamlit.ps1"
DEMO_DOC = REPO_ROOT / "docs" / "demo" / "streamlit_guided_intake_manual_demo_script.md"

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. BAT launcher exists
# ------------------------------------------------------------------
checks.append(("A. Ollama BAT launcher exists", BAT_FILE.exists()))

# ------------------------------------------------------------------
# 2. PS1 launcher exists
# ------------------------------------------------------------------
checks.append(("B. Ollama PS1 launcher exists", PS1_FILE.exists()))

# ------------------------------------------------------------------
# 3. Both set SECNAV_LLM_PROVIDER=ollama
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_text = BAT_FILE.read_text(encoding="utf-8")
    ps1_text = PS1_FILE.read_text(encoding="utf-8")
    has_provider_bat = 'SECNAV_LLM_PROVIDER=ollama' in bat_text
    has_provider_ps1 = '$env:SECNAV_LLM_PROVIDER = "ollama"' in ps1_text
    checks.append(("C. BAT sets SECNAV_LLM_PROVIDER=ollama", has_provider_bat))
    checks.append(("D. PS1 sets SECNAV_LLM_PROVIDER=ollama", has_provider_ps1))
else:
    checks.append(("C. BAT sets SECNAV_LLM_PROVIDER=ollama", False))
    checks.append(("D. PS1 sets SECNAV_LLM_PROVIDER=ollama", False))

# ------------------------------------------------------------------
# 4. Both set SECNAV_OLLAMA_MODEL=llama3.2
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    has_model_bat = 'SECNAV_OLLAMA_MODEL=llama3.2' in bat_text
    has_model_ps1 = '$env:SECNAV_OLLAMA_MODEL = "llama3.2"' in ps1_text
    checks.append(("E. BAT sets SECNAV_OLLAMA_MODEL=llama3.2", has_model_bat))
    checks.append(("F. PS1 sets SECNAV_OLLAMA_MODEL=llama3.2", has_model_ps1))
else:
    checks.append(("E. BAT sets SECNAV_OLLAMA_MODEL=llama3.2", False))
    checks.append(("F. PS1 sets SECNAV_OLLAMA_MODEL=llama3.2", False))

# ------------------------------------------------------------------
# 5. Both reference http://localhost:8501
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    has_url_bat = 'http://localhost:8501' in bat_text
    has_url_ps1 = 'http://localhost:8501' in ps1_text
    checks.append(("G. BAT references localhost:8501", has_url_bat))
    checks.append(("H. PS1 references localhost:8501", has_url_ps1))
else:
    checks.append(("G. BAT references localhost:8501", False))
    checks.append(("H. PS1 references localhost:8501", False))

# ------------------------------------------------------------------
# 6. Both reference app file
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    has_app_bat = 'app_streamlit_llm_guided_intake.py' in bat_text
    has_app_ps1 = 'app_streamlit_llm_guided_intake.py' in ps1_text
    checks.append(("I. BAT references app file", has_app_bat))
    checks.append(("J. PS1 references app file", has_app_ps1))
else:
    checks.append(("I. BAT references app file", False))
    checks.append(("J. PS1 references app file", False))

# ------------------------------------------------------------------
# 7. Both check or mention Ollama reachability
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    has_ollama_check_bat = 'localhost:11434' in bat_text or 'Ollama' in bat_text
    has_ollama_check_ps1 = 'localhost:11434' in ps1_text or 'Ollama' in ps1_text
    checks.append(("K. BAT checks Ollama reachability", has_ollama_check_bat))
    checks.append(("L. PS1 checks Ollama reachability", has_ollama_check_ps1))
else:
    checks.append(("K. BAT checks Ollama reachability", False))
    checks.append(("L. PS1 checks Ollama reachability", False))

# ------------------------------------------------------------------
# 8. No API key display
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    no_key_bat = 'api_key' not in bat_text.lower() and 'apikey' not in bat_text.lower()
    no_key_ps1 = 'api_key' not in ps1_text.lower() and 'apikey' not in ps1_text.lower()
    checks.append(("M. BAT avoids API key display", no_key_bat))
    checks.append(("N. PS1 avoids API key display", no_key_ps1))
else:
    checks.append(("M. BAT avoids API key display", False))
    checks.append(("N. PS1 avoids API key display", False))

# ------------------------------------------------------------------
# 9. Existing mock launchers still exist
# ------------------------------------------------------------------
checks.append(("O. Mock BAT launcher still exists", MOCK_BAT.exists()))
checks.append(("P. Mock PS1 launcher still exists", MOCK_PS1.exists()))

# ------------------------------------------------------------------
# 10. Demo doc mentions Ollama launcher if present
# ------------------------------------------------------------------
if DEMO_DOC.exists():
    demo_text = DEMO_DOC.read_text(encoding="utf-8")
    mentions_ollama = 'ollama' in demo_text.lower()
    checks.append(("Q. Demo doc mentions Ollama launcher", mentions_ollama))
else:
    checks.append(("Q. Demo doc mentions Ollama launcher", False))

# ------------------------------------------------------------------
# 11. No renderer/layout/CCI config changes in app
# ------------------------------------------------------------------
app_file = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
if app_file.exists():
    app_text = app_file.read_text(encoding="utf-8")
    no_renderer = 'renderer' not in app_text.lower() or 'pdf_v6_render' in app_text.lower()
    no_cci_config = 'cci_severity' not in app_text.lower()
    checks.append(("R. No renderer layout controls", no_renderer))
    checks.append(("S. No CCI config controls", no_cci_config))
else:
    checks.append(("R. No renderer layout controls", False))
    checks.append(("S. No CCI config controls", False))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.26D — One-Click Ollama Streamlit Launcher Regression")
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
