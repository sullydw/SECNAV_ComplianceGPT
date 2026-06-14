#!/usr/bin/env python3
"""
Phase L.19 — LLM Provider Configuration Plumbing Regression Runner

Validates provider config loading, backend factory, safe defaults,
and adapter integration without any live API/network calls.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from llm_provider_config import (
    LLMProviderConfig,
    build_llm_backend_from_config,
    build_adapter_from_env,
)
from llm_builder_mediator import MediatorInput


def _check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"[PASS] {label}")
        return True
    else:
        print(f"[FAIL] {label}: {detail}")
        return False


def main():
    passed = 0
    failed = 0
    total = 0

    # ------------------------------------------------------------------
    # 1. default config returns mock provider
    # ------------------------------------------------------------------
    total += 1
    # Clear any env vars that might interfere
    for key in list(os.environ.keys()):
        if key.startswith("SECNAV_LLM") or key == "SECNAV_OPENAI_API_KEY" or key == "SECNAV_OLLAMA_MODEL":
            del os.environ[key]
    config = LLMProviderConfig.from_env()
    ok = config.provider == "mock"
    if _check("1. Default config returns mock provider", ok, f"provider={config.provider}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 2. missing env vars safe
    # ------------------------------------------------------------------
    total += 1
    ok = (
        config.model is None
        and config.timeout_seconds == 30.0
        and config.max_tokens == 512
        and config.api_key_env_var is None
    )
    if _check("2. Missing env vars safe", ok, f"config={config.to_dict()}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 3. provider env var normalized
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_PROVIDER"] = "OpenAI"
    config = LLMProviderConfig.from_env()
    ok = config.provider == "openai"
    if _check("3. Provider env var normalized", ok, f"provider={config.provider}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_PROVIDER"]

    # ------------------------------------------------------------------
    # 4. unsupported provider handled safely
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_PROVIDER"] = "some_unknown_provider"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    result = backend("test prompt")
    parsed = json.loads(result)
    ok = (
        parsed.get("intent") == "unknown"
        and "unavailable" in parsed.get("explanation", "").lower()
    )
    if _check("4. Unsupported provider handled safely", ok, f"explanation={parsed.get('explanation')}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_PROVIDER"]

    # ------------------------------------------------------------------
    # 5. OpenAI provider selected without API key fails closed
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_PROVIDER"] = "openai"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    result = backend("test prompt")
    parsed = json.loads(result)
    ok = (
        parsed.get("intent") == "unknown"
        and "unavailable" in parsed.get("explanation", "").lower()
    )
    if _check("5. OpenAI without API key fails closed", ok, f"explanation={parsed.get('explanation')}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_PROVIDER"]

    # ------------------------------------------------------------------
    # 6. Ollama provider selected without local model fails closed
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_PROVIDER"] = "ollama"
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    result = backend("test prompt")
    parsed = json.loads(result)
    ok = (
        parsed.get("intent") == "unknown"
        and "unavailable" in parsed.get("explanation", "").lower()
    )
    if _check("6. Ollama without local server fails closed", ok, f"explanation={parsed.get('explanation')}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_PROVIDER"]

    # ------------------------------------------------------------------
    # 7. timeout/max_tokens parsing valid values
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_TIMEOUT_SECONDS"] = "45"
    os.environ["SECNAV_LLM_MAX_TOKENS"] = "1024"
    config = LLMProviderConfig.from_env()
    ok = config.timeout_seconds == 45.0 and config.max_tokens == 1024
    if _check("7. Timeout/max_tokens valid values", ok, f"timeout={config.timeout_seconds}, max_tokens={config.max_tokens}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_TIMEOUT_SECONDS"]
    del os.environ["SECNAV_LLM_MAX_TOKENS"]

    # ------------------------------------------------------------------
    # 8. invalid timeout handled safely
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_TIMEOUT_SECONDS"] = "not_a_number"
    config = LLMProviderConfig.from_env()
    ok = config.timeout_seconds == 30.0
    if _check("8. Invalid timeout safe", ok, f"timeout={config.timeout_seconds}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_TIMEOUT_SECONDS"]

    # ------------------------------------------------------------------
    # 9. invalid max_tokens handled safely
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_MAX_TOKENS"] = "99999"
    config = LLMProviderConfig.from_env()
    ok = config.max_tokens == 512
    if _check("9. Invalid max_tokens safe", ok, f"max_tokens={config.max_tokens}"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_MAX_TOKENS"]

    # ------------------------------------------------------------------
    # 10. no API key values printed
    # ------------------------------------------------------------------
    total += 1
    os.environ["SECNAV_LLM_API_KEY_ENV_VAR"] = "SECNAV_OPENAI_API_KEY"
    os.environ["SECNAV_OPENAI_API_KEY"] = "sk-secret123456"
    config = LLMProviderConfig.from_env()
    d = config.to_dict()
    ok = "secret123456" not in json.dumps(d)
    if _check("10. No API key values in to_dict", ok, f"dict may contain secret"):
        passed += 1
    else:
        failed += 1
    del os.environ["SECNAV_LLM_API_KEY_ENV_VAR"]
    del os.environ["SECNAV_OPENAI_API_KEY"]

    # ------------------------------------------------------------------
    # 11. fake backend still works through adapter
    # ------------------------------------------------------------------
    total += 1
    adapter = build_adapter_from_env()
    inp = MediatorInput(
        session_id="r11", current_step="intake", payload_snapshot={},
        missing_required_fields=[], missing_recommended_fields=[],
        validation_summary={}, warning_summary=[], error_summary=[],
        user_message="From Commander Example",
    )
    out = adapter.mediate(inp)
    ok = (
        out["intent"] == "provide_field"
        and out["confidence"] == 0.9
    )
    if _check("11. Fake backend works through adapter", ok, f"intent={out['intent']}, confidence={out['confidence']}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 12. no network/API dependency in imports
    # ------------------------------------------------------------------
    total += 1
    import inspect
    src_file = inspect.getsourcefile(build_llm_backend_from_config)
    with open(src_file or "src/llm_provider_config.py", "r", encoding="utf-8") as f:
        src_text = f.read().lower()
    forbidden = ["openai", "anthropic", "requests", "httpx", "urllib", "aiohttp"]
    found = []
    for name in forbidden:
        # Only flag actual import statements, not comments/docstrings
        if f"import {name}" in src_text or f"from {name}" in src_text:
            found.append(name)
    ok = not found
    if _check("12. No real LLM/API dependency in config module", ok, f"found imports: {found}"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 13. no renderer/layout changes
    # ------------------------------------------------------------------
    total += 1
    ok = "render" not in src_text or "renderer" not in src_text
    if _check("13. No renderer references in config module", ok, "renderer found in source"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # 14. no CCI config/severity changes
    # ------------------------------------------------------------------
    total += 1
    ok = "cci_severity" not in src_text and "severity_override" not in src_text
    if _check("14. No CCI severity references in config module", ok, "severity found in source"):
        passed += 1
    else:
        failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 52)
    print("L.19 LLM Provider Configuration Plumbing Results")
    print("=" * 52)
    print(f"Total : {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 52)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
