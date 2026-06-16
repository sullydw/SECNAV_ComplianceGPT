#!/usr/bin/env python3
"""
Phase L.26C — Ollama Provider Manual Path Regression

Verifies the Ollama provider path is wired correctly:
- mock remains default
- Ollama fails closed when server not running
- no crash when Ollama unavailable
- no live/network call in default mode
- adapter still validates output
- Streamlit safety boundaries preserved
"""

import os
import sys
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from llm_provider_config import (
    LLMProviderConfig,
    build_llm_backend_from_config,
    _ollama_backend,
)
from llm_builder_mediator import LLMBuilderMediatorAdapter, MediatorInput

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. Mock provider is default
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    for k in list(os.environ):
        if k.startswith("SECNAV_LLM_") or k == "SECNAV_OLLAMA_MODEL":
            del os.environ[k]
    config = LLMProviderConfig.from_env()
    checks.append(("A. Mock is default when no env vars set", config.provider == "mock"))
except Exception as e:
    checks.append(("A. Mock is default when no env vars set", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 2. Ollama provider selected when env var set
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    os.environ["SECNAV_OLLAMA_MODEL"] = "llama3.2"
    config = LLMProviderConfig.from_env()
    checks.append(("B. Ollama provider selected when env var set", config.provider == "ollama"))
except Exception as e:
    checks.append(("B. Ollama provider selected when env var set", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 3. Ollama backend fails closed when server not running
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    os.environ["SECNAV_OLLAMA_MODEL"] = "llama3.2"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    result = backend("test prompt")
    parsed = json.loads(result)
    is_fail_closed = (
        parsed.get("intent") == "unknown"
        and "Ollama" in parsed.get("explanation", "")
    )
    checks.append(("C. Ollama fails closed when server not running", is_fail_closed))
except Exception as e:
    checks.append(("C. Ollama fails closed when server not running", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 4. No crash when Ollama unavailable
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    os.environ["SECNAV_OLLAMA_MODEL"] = "llama3.2"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    # Call twice to ensure idempotent
    r1 = backend("prompt 1")
    r2 = backend("prompt 2")
    p1 = json.loads(r1)
    p2 = json.loads(r2)
    no_crash = (
        p1.get("intent") == "unknown"
        and p2.get("intent") == "unknown"
    )
    checks.append(("D. No crash when Ollama unavailable (idempotent)", no_crash))
except Exception as e:
    checks.append(("D. No crash when Ollama unavailable (idempotent)", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 5. No live/network call in default (mock) mode
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    for k in list(os.environ):
        if k.startswith("SECNAV_LLM_") or k == "SECNAV_OLLAMA_MODEL":
            del os.environ[k]
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    label = getattr(backend, "__class__", None).__name__ if backend else ""
    is_mock = label == "FakeBackend"
    checks.append(("E. Default mode uses FakeBackend (no network)", is_mock))
except Exception as e:
    checks.append(("E. Default mode uses FakeBackend (no network)", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 6. Adapter still validates Ollama output
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    os.environ["SECNAV_OLLAMA_MODEL"] = "llama3.2"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    adapter = LLMBuilderMediatorAdapter(backend=backend)
    inp = MediatorInput(
        session_id="test",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="test",
    )
    out = adapter.mediate(inp)
    # Even with Ollama unavailable, adapter should return safe output
    has_intent = "intent" in out
    safe = out.get("intent") == "unknown"
    checks.append(("F. Adapter validates Ollama output (safe fallback)", has_intent and safe))
except Exception as e:
    checks.append(("F. Adapter validates Ollama output (safe fallback)", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 7. Streamlit app still uses ingest_user_message
# ------------------------------------------------------------------
app_file = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
if app_file.exists():
    app_text = app_file.read_text(encoding="utf-8")
    has_ingest = "ingest_user_message" in app_text
    no_direct_mutate = "payload[" not in app_text.replace("payload_snapshot", "").replace("build_payload()", "")
    checks.append(("G. Streamlit uses ingest_user_message", has_ingest))
    checks.append(("H. No direct payload mutation in Streamlit", no_direct_mutate))
else:
    checks.append(("G. Streamlit uses ingest_user_message", False))
    checks.append(("H. No direct payload mutation in Streamlit", False))

# ------------------------------------------------------------------
# 8. Ollama backend factory is callable
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    config = LLMProviderConfig.from_env()
    backend = _ollama_backend(config)
    is_callable = callable(backend)
    checks.append(("I. _ollama_backend returns callable", is_callable))
except Exception as e:
    checks.append(("I. _ollama_backend returns callable", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 9. Ollama model name read from env
# ------------------------------------------------------------------
env_before = dict(os.environ)
try:
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    os.environ["SECNAV_OLLAMA_MODEL"] = "custom-model-7b"
    config = LLMProviderConfig.from_env()
    model_correct = config.extra.get("ollama_model") == "custom-model-7b"
    checks.append(("J. Ollama model read from SECNAV_OLLAMA_MODEL", model_correct))
except Exception as e:
    checks.append(("J. Ollama model read from SECNAV_OLLAMA_MODEL", False))
    print(f"  Error: {e}")
finally:
    os.environ.clear()
    os.environ.update(env_before)

# ------------------------------------------------------------------
# 10. L.24 regression still passes
# ------------------------------------------------------------------
l24_runner = REPO_ROOT / "tools" / "run_phase_l24_streamlit_usability_regression.py"
if l24_runner.exists():
    try:
        result = subprocess.run(
            [sys.executable, str(l24_runner)],
            capture_output=True,
            text=True,
            timeout=30
        )
        l24_passed = "ALL CHECKS PASS" in result.stdout
        checks.append(("K. L.24 regression still passes", l24_passed))
        if not l24_passed:
            print(f"  L.24 output: {result.stdout}")
    except Exception as e:
        checks.append(("K. L.24 regression still passes", False))
        print(f"  L.24 error: {e}")
else:
    checks.append(("K. L.24 regression still passes", False))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.26C — Ollama Provider Manual Path Regression")
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
