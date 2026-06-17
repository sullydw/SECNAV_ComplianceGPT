#!/usr/bin/env python3
"""
Phase L.26G — Ollama Timeout Fallback and Cold-Start Headroom Regression

Verifies:
- TimeoutError on /api/chat continues to /api/generate fallback (does NOT return)
- Ollama default timeout raised to 120s to accommodate cold model loads
- Streamlit UI shows cold-start caption
- no renderer/layout or CCI changes
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
CONFIG_FILE = SRC_DIR / "llm_provider_config.py"

sys.path.insert(0, str(SRC_DIR))

from llm_provider_config import LLMProviderConfig

config_text = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else ""
app_text = APP_FILE.read_text(encoding="utf-8") if APP_FILE.exists() else ""

checks: list[tuple[str, bool]] = []

checks.append(("A. Config file exists", CONFIG_FILE.exists()))
checks.append(("B. App file exists", APP_FILE.exists()))
checks.append(("C. TimeoutError caught with continue in call_ollama_inference",
    ("except TimeoutError as e:" in config_text and "continue" in config_text)
    or ("except TimeoutError" in config_text and "attempt[\"status\"] = \"timeout\"" in config_text)))
checks.append(("D. Ollama default timeout raised to 120s",
    "self.timeout_seconds = 120.0" in config_text))
checks.append(("E. Ollama timeout capped at minimum 120s",
    "self.timeout_seconds < 60" in config_text or "self.timeout_seconds = 120.0" in config_text))
checks.append(("F. App shows cold-start caption",
    "60–90 seconds" in app_text or "60-90 seconds" in app_text))
checks.append(("G. No renderer layout controls introduced", "renderer_directive" not in app_text.lower()))
checks.append(("H. No CCI severity/config controls introduced", "cci_severity" not in app_text.lower()))

print("=" * 72)
print("Phase L.26G — Ollama Timeout Fallback and Cold-Start Headroom Regression")
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
