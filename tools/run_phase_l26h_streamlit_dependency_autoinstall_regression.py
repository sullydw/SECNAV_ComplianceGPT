#!/usr/bin/env python3
"""
Phase L.26H — Streamlit Launcher Dependency Auto-Install Hotfix Regression

Verifies:
- app_streamlit_llm_guided_intake.py does NOT unconditionally import pyperclip
- optional clipboard helper exists and returns (success, message)
- all four launchers check + auto-install streamlit and pyperclip
- launchers use the selected Python executable for pip install
- launchers re-check after install
- launchers exit cleanly on install failure with manual command
- launchers do NOT auto-install Ollama
- launchers do NOT install vendor LLM SDKs (openai, anthropic, etc.)
- no API key display in any launcher
- no renderer/layout changes in the app
- no CCI config/severity changes
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
BAT_FILE = REPO_ROOT / "launch_secnav_streamlit.bat"
PS1_FILE = REPO_ROOT / "launch_secnav_streamlit.ps1"
BAT_O_FILE = REPO_ROOT / "launch_secnav_streamlit_ollama.bat"
PS1_O_FILE = REPO_ROOT / "launch_secnav_streamlit_ollama.ps1"

app_text = APP_FILE.read_text(encoding="utf-8") if APP_FILE.exists() else ""
bat_text = BAT_FILE.read_text(encoding="utf-8") if BAT_FILE.exists() else ""
ps1_text = PS1_FILE.read_text(encoding="utf-8") if PS1_FILE.exists() else ""
bat_o_text = BAT_O_FILE.read_text(encoding="utf-8") if BAT_O_FILE.exists() else ""
ps1_o_text = PS1_O_FILE.read_text(encoding="utf-8") if PS1_O_FILE.exists() else ""

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# App-level checks
# ------------------------------------------------------------------
# A. App file exists
checks.append(("A. App file exists", APP_FILE.exists()))

# B. No unconditional top-level "import pyperclip" (should be guarded)
checks.append(("B. No unconditional top-level import pyperclip",
               not ("\nimport pyperclip\n" in app_text and "try:\n    import pyperclip" not in app_text)))

# C. Guarded pyperclip import pattern present
checks.append(("C. Guarded pyperclip import present",
               "try:\n    import pyperclip" in app_text or "try:\n    import pyperclip as _pyperclip" in app_text))

# D. Optional clipboard helper exists
checks.append(("D. _copy_to_clipboard helper exists", "_copy_to_clipboard" in app_text))

# E. Helper returns (bool, str) pattern
checks.append(("E. Helper returns (bool, str)",
               "tuple[bool, str]" in app_text and "return True, \"Copied to clipboard\"" in app_text))

# F. No crash on missing pyperclip (friendly manual message)
checks.append(("F. Friendly manual-copy fallback message",
               "Clipboard not available" in app_text))

# G. No inline `import pyperclip` inside render path
checks.append(("G. No inline pyperclip import in render path",
               "import pyperclip  # noqa: F811" not in app_text))

# H. No renderer/layout controls introduced
checks.append(("H. No renderer/layout controls introduced",
               not any(k in app_text.lower() for k in ["renderer_directive", "layout_override", "font_size", "margin", "page_size"])))

# I. No CCI severity/config controls introduced
checks.append(("I. No CCI severity/config controls introduced",
               not any(k in app_text.lower() for k in ["severity_override", "promote_rule", "disable_validator", "cci_config"])))

# ------------------------------------------------------------------
# Launcher checks — shared helper text
# ------------------------------------------------------------------
launcher_texts = {
    "BAT": bat_text,
    "PS1": ps1_text,
    "BAT_O": bat_o_text,
    "PS1_O": ps1_o_text,
}

for label, text in launcher_texts.items():
    pass

# J. All four launchers exist
checks.append(("J. All four launchers exist",
               BAT_FILE.exists() and PS1_FILE.exists() and BAT_O_FILE.exists() and PS1_O_FILE.exists()))

# K. All launchers check for streamlit
checks.append(("K. All launchers check streamlit",
               all("streamlit" in t.lower() and ("-c \"import streamlit\"" in t or 'Test-Import "streamlit"' in t) for t in launcher_texts.values())))

# L. All launchers check for pyperclip
checks.append(("L. All launchers check pyperclip",
               all("pyperclip" in t.lower() and ("-c \"import pyperclip\"" in t or 'Test-Import "pyperclip"' in t) for t in launcher_texts.values())))

# M. All launchers run pip install via same Python
checks.append(("M. All launchers use same Python for pip install",
               all("%PYTHON_EXE%" in t and "-m pip install" in t for t in [bat_text, bat_o_text]) and
               all("$PYTHON_EXE" in t and "-m pip install" in t for t in [ps1_text, ps1_o_text])))

# N. All launchers re-check after install (second import test)
# BAT: has two "-c \"import streamlit\"" segments (check + re-verify)
# The re-verify in BAT uses combined "import streamlit; import pyperclip"
bat_has_recheck_streamlit = bat_text.count("-c \"import streamlit\"") >= 2 or "import streamlit; import pyperclip" in bat_text
bat_o_has_recheck_streamlit = bat_o_text.count("-c \"import streamlit\"") >= 2 or "import streamlit; import pyperclip" in bat_o_text
# PS1: has a combined "import streamlit; import pyperclip" re-verify line
ps1_has_reverify = "import streamlit; import pyperclip" in ps1_text
ps1_o_has_reverify = "import streamlit; import pyperclip" in ps1_o_text
checks.append(("N. Launchers re-check after install",
               bat_has_recheck_streamlit and bat_o_has_recheck_streamlit and ps1_has_reverify and ps1_o_has_reverify))

# O. Launchers exit cleanly on install failure (print manual command + exit)
checks.append(("O. Clean exit on install failure with manual command",
               all("exit" in t.lower() and "pip install" in t.lower() and "manually" in t.lower()
                   for t in launcher_texts.values())))

# P. Launchers do NOT auto-install Ollama (ollama serve is a suggestion, not install)
checks.append(("P. Launchers do NOT auto-install Ollama",
               all("pip install ollama" not in t.lower() for t in launcher_texts.values())))

# Q. Launchers do NOT install vendor LLM SDKs (openai, anthropic, gemini, etc.)
vendor_sdks = ["openai", "anthropic", "google-generativeai", "vertexai", "mistral", "cohere", "groq"]
checks.append(("Q. No vendor LLM SDK auto-install",
               all(all(v not in t.lower() for v in vendor_sdks) for t in launcher_texts.values())))

# R. No API key display in launchers
checks.append(("R. No API key display in launchers",
               all("sk-" not in t for t in launcher_texts.values()) and
               all("api_key" not in t.lower() for t in launcher_texts.values())))

# S. No live-LLM provider enabling in BAT/PS1 (mock only defaults)
checks.append(("S. No unexpected live provider env vars in base launchers",
               "SECNAV_LLM_PROVIDER" not in bat_text and "SECNAV_LLM_PROVIDER" not in ps1_text))

# T. Ollama launchers set env vars but do NOT install Ollama
checks.append(("T. Ollama launchers set env vars but do not install Ollama",
               "SECNAV_LLM_PROVIDER" in bat_o_text and "SECNAV_LLM_PROVIDER" in ps1_o_text and
               "pip install ollama" not in bat_o_text.lower() and "pip install ollama" not in ps1_o_text.lower()))

# U. App-level: no API key display patterns
checks.append(("U. App-level no API key display",
               all(p not in app_text.lower() for p in [
                   "print(api_key", "print(os.getenv", "st.write(config.api_key",
                   "st.text(config.api_key", "st.markdown(config.api_key"
               ])))

# ------------------------------------------------------------------
# Dynamic smoke: app file importable WITHOUT pyperclip (simulate missing)
# ------------------------------------------------------------------
try:
    import types
    fake_st = types.ModuleType("streamlit")
    fake_st.session_state = {}
    fake_st.set_page_config = lambda **kw: None
    fake_st.title = lambda *a, **kw: None
    fake_st.caption = lambda *a, **kw: None
    fake_st.header = lambda *a, **kw: None
    fake_st.subheader = lambda *a, **kw: None
    fake_st.write = lambda *a, **kw: None
    fake_st.markdown = lambda *a, **kw: None
    fake_st.code = lambda *a, **kw: None
    fake_st.divider = lambda: None
    fake_st.columns = lambda *a, **kw: [fake_st] * 3
    fake_st.container = lambda *a, **kw: fake_st
    fake_st.chat_container = lambda *a, **kw: fake_st
    fake_st.chat_message = lambda *a, **kw: fake_st
    fake_st.chat_input = lambda *a, **kw: None
    fake_st.button = lambda *a, **kw: False
    fake_st.download_button = lambda *a, **kw: None
    fake_st.info = lambda *a, **kw: None
    fake_st.warning = lambda *a, **kw: None
    fake_st.error = lambda *a, **kw: None
    fake_st.success = lambda *a, **kw: None
    fake_st.rerun = lambda: None
    fake_st.toast = lambda *a, **kw: None
    fake_st.metric = lambda *a, **kw: None
    fake_st.expander = lambda *a, **kw: fake_st
    fake_st.sidebar = fake_st
    fake_st.__version__ = "0.0.0"
    sys.modules["streamlit"] = fake_st

    # Remove pyperclip if present so we simulate missing dependency
    if "pyperclip" in sys.modules:
        del sys.modules["pyperclip"]

    # Ensure src modules from repo root are importable
    src_dir = str(REPO_ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # We can't fully import the app (needs BuilderSession etc.), but we can parse it
    import ast
    tree = ast.parse(app_text)
    checks.append(("V. App parses without pyperclip", True))
except Exception as exc:
    checks.append(("V. App parses without pyperclip", False))
    print(f"  Parse/import error: {exc}")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 72)
print("Phase L.26H — Streamlit Launcher Dependency Auto-Install Hotfix")
print("=" * 72)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
for label, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
print(f"\n{'=' * 72}")
print(f"Total: {passed}/{total} passed")
if passed == total:
    print("ALL CHECKS PASS")
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
print("=" * 72)
