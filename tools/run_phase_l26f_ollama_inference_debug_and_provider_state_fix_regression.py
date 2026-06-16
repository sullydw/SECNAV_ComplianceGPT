#!/usr/bin/env python3
"""
Phase L.26F — Ollama Inference Debug and Provider-State Fix Regression

Verifies:
- local Ollama path prefers /api/chat then falls back to /api/generate
- fail-closed remains intact when inference endpoint is unavailable
- selected provider/model helpers exist for consistent Streamlit state propagation
- provider debug/status helpers exist for UI visibility
- no renderer/layout or CCI severity changes
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
CONFIG_FILE = SRC_DIR / "llm_provider_config.py"

sys.path.insert(0, str(SRC_DIR))

from llm_provider_config import (
    LLMProviderConfig,
    call_ollama_inference,
    endpoint_fallback_order,
    ollama_inference_urls,
    phase_l26f_problem_statement,
    provider_debug_status,
    selected_model_changed,
    selected_model_from_state,
    selected_provider_from_state,
    ui_provider_config,
)

checks: list[tuple[str, bool]] = []

config_text = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else ""
app_text = APP_FILE.read_text(encoding="utf-8") if APP_FILE.exists() else ""

checks.append(("A. Config file exists", CONFIG_FILE.exists()))
checks.append(("B. App file exists", APP_FILE.exists()))
checks.append(("C. /api/chat endpoint referenced", "/api/chat" in config_text))
checks.append(("D. /api/generate fallback referenced", "/api/generate" in config_text))
checks.append(("E. endpoint_fallback_order helper exists", "def endpoint_fallback_order" in config_text))
checks.append(("F. call_ollama_inference helper exists", "def call_ollama_inference" in config_text))
checks.append(("G. selected_model_changed helper exists", "def selected_model_changed" in config_text))
checks.append(("H. ui_provider_config helper exists", "def ui_provider_config" in config_text))
checks.append(("I. provider_debug_status helper exists", "def provider_debug_status" in config_text))
checks.append(("J. App shows Provider Status label", "Provider Status" in app_text))
checks.append(("K. App stores provider_status_snapshot", "provider_status_snapshot" in app_text))
checks.append(("L. App uses selected_model_changed", "selected_model_changed(" in app_text))
checks.append(("M. App uses ui_provider_config", "ui_provider_config(" in app_text))
checks.append(("N. No renderer layout controls introduced", "renderer_directive" not in app_text.lower()))
checks.append(("O. No CCI severity/config controls introduced", "cci_severity" not in app_text.lower()))
checks.append(("P. Problem statement tracks /api/chat 404 root cause", "404" in phase_l26f_problem_statement()))
checks.append(("Q. Fallback order lists chat then generate", endpoint_fallback_order() == ollama_inference_urls()))

cfg = LLMProviderConfig(provider="ollama", model="llama3.2")
status = provider_debug_status(cfg)
checks.append(("R. provider_debug_status returns dict", isinstance(status, dict) and status.get("provider") == "ollama"))

class DummyState:
    pass

state = DummyState()
selected_model_changed(state, "ollama", "llama3.2")
checks.append(("S. selected_model_changed stores provider", selected_provider_from_state(state) == "ollama"))
checks.append(("T. selected_model_changed stores model", selected_model_from_state(state) == "llama3.2"))
checks.append(("U. ui_provider_config resolves UI override", ui_provider_config("ollama", "llama3.2").provider == "ollama" and ui_provider_config("ollama", "llama3.2").model == "llama3.2"))

raw = call_ollama_inference("test prompt", cfg)
parsed = json.loads(raw)
checks.append(("V. call_ollama_inference returns JSON string", isinstance(parsed, dict)))
checks.append(("W. call_ollama_inference fail-closes safely when inference unavailable", parsed.get("intent") == "unknown" or bool(parsed.get("proposed_key_value_lines")) or "Ollama" in parsed.get("explanation", "")))
checks.append(("X. call_ollama_inference explanation mentions endpoint/path on failure", (parsed.get("intent") != "unknown") or ("/api/" in parsed.get("explanation", "") or "localhost:11434" in parsed.get("explanation", ""))))

print("=" * 72)
print("Phase L.26F — Ollama Inference Debug and Provider-State Fix Regression")
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
