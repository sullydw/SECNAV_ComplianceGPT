#!/usr/bin/env python3
"""
Phase L.26 — Simple Streamlit Local Launcher Regression

Verifies both launcher files (.bat and .ps1) exist, reference the app,
display the correct URL, handle missing Streamlit, and avoid unsafe patterns.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BAT_FILE = REPO_ROOT / "launch_secnav_streamlit.bat"
PS1_FILE = REPO_ROOT / "launch_secnav_streamlit.ps1"
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
DEMO_DOC = REPO_ROOT / "docs" / "demo" / "streamlit_guided_intake_manual_demo_script.md"

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. BAT launcher exists
# ------------------------------------------------------------------
checks.append(("A. BAT launcher exists", BAT_FILE.exists()))

# ------------------------------------------------------------------
# 2. PowerShell launcher exists
# ------------------------------------------------------------------
checks.append(("B. PS1 launcher exists", PS1_FILE.exists()))

# ------------------------------------------------------------------
# 3. BAT references app file
# ------------------------------------------------------------------
if BAT_FILE.exists():
    bat_text = BAT_FILE.read_text(encoding="utf-8")
    checks.append(("C. BAT references app file", "app_streamlit_llm_guided_intake.py" in bat_text))
else:
    checks.append(("C. BAT references app file", False))

# ------------------------------------------------------------------
# 4. PS1 references app file
# ------------------------------------------------------------------
if PS1_FILE.exists():
    ps1_text = PS1_FILE.read_text(encoding="utf-8")
    checks.append(("D. PS1 references app file", "app_streamlit_llm_guided_intake.py" in ps1_text))
else:
    checks.append(("D. PS1 references app file", False))

# ------------------------------------------------------------------
# 5. Both display localhost:8501
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    url = "http://localhost:8501"
    checks.append(("E. Both display localhost URL", url in bat_text and url in ps1_text))
else:
    checks.append(("E. Both display localhost URL", False))

# ------------------------------------------------------------------
# 6. Both use safe python -m streamlit run command
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_safe = "streamlit run" in bat_text and "python" in bat_text.lower()
    ps1_safe = "streamlit run" in ps1_text and "python" in ps1_text.lower()
    checks.append(("F. Safe streamlit run command", bat_safe and ps1_safe))
else:
    checks.append(("F. Safe streamlit run command", False))

# ------------------------------------------------------------------
# 7. Both handle missing Streamlit
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_missing = "Streamlit is not installed" in bat_text or "not installed" in bat_text or "is missing" in bat_text.lower()
    ps1_missing = "Streamlit is not installed" in ps1_text or "not installed" in ps1_text or "is missing" in ps1_text.lower()
    checks.append(("G. Missing Streamlit handling", bat_missing and ps1_missing))
else:
    checks.append(("G. Missing Streamlit handling", False))

# ------------------------------------------------------------------
# 8. Both avoid API key display
# ------------------------------------------------------------------
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_no_key = "sk-" not in bat_text
    ps1_no_key = "sk-" not in ps1_text
    checks.append(("H. No API key display", bat_no_key and ps1_no_key))
else:
    checks.append(("H. No API key display", False))

# ------------------------------------------------------------------
# 9. Both avoid live-provider env vars
# ------------------------------------------------------------------
live_vars = ["OPENAI_API_KEY", "OLLAMA_HOST", "SECNAV_LLM_PROVIDER"]
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_live = not any(v in bat_text for v in live_vars)
    ps1_live = not any(v in ps1_text for v in live_vars)
    checks.append(("I. No live provider enabling", bat_live and ps1_live))
else:
    checks.append(("I. No live provider enabling", False))

# ------------------------------------------------------------------
# 10. Neither modifies renderer/layout/CCI config
# ------------------------------------------------------------------
renderer_keywords = ["pdf_v6_render", "layout_override", "severity_override", "cci_config"]
if BAT_FILE.exists() and PS1_FILE.exists():
    bat_clean = not any(k in bat_text for k in renderer_keywords)
    ps1_clean = not any(k in ps1_text for k in renderer_keywords)
    checks.append(("J. No renderer/CCI mutation", bat_clean and ps1_clean))
else:
    checks.append(("J. No renderer/CCI mutation", False))

# ------------------------------------------------------------------
# 11. Manual demo doc mentions launcher files
# ------------------------------------------------------------------
if DEMO_DOC.exists():
    demo_text = DEMO_DOC.read_text(encoding="utf-8")
    has_launcher = "launch_secnav_streamlit" in demo_text
    checks.append(("K. Demo doc mentions launcher", has_launcher))
    if not has_launcher:
        print("  Launcher not mentioned in demo doc — will patch next")
else:
    checks.append(("K. Demo doc mentions launcher", False))

# ------------------------------------------------------------------
# 12. No generated files present
# ------------------------------------------------------------------
output_dir = REPO_ROOT / "output"
has_pdfs = len(list(output_dir.glob("*.pdf"))) > 0
has_logs = len(list(output_dir.glob("*.log"))) > 0
has_json = len(list(output_dir.glob("*.json"))) > 0
checks.append(("L. No generated PDFs/logs/jsons", not (has_pdfs or has_logs or has_json)))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.26 — Simple Streamlit Local Launcher Regression")
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
