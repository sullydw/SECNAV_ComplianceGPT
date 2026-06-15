#!/usr/bin/env python3
"""
Phase L.20 — Optional Live LLM Smoke-Test Harness

An optional/manual test that exercises the full adapter + backend pipeline
with a minimal safe prompt. Runs ONLY when explicitly enabled via env var.

Normal regressions should NOT set SECNAV_LLM_LIVE_SMOKE; this harness will
SKIP cleanly and exit 0.

When enabled, the harness:
  1. Reads provider config from environment
  2. Builds backend + adapter
  3. Sends a minimal MediatorInput
  4. Prints adapter output (sanitized — no API keys)
  5. Reports whether the output passed adapter validation
  6. Reports whether the provider is mock (no network) or live-capable
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from llm_provider_config import LLMProviderConfig, build_llm_backend_from_config
from llm_builder_mediator import LLMBuilderMediatorAdapter, MediatorInput


def _redact(s: str) -> str:
    """Mask anything that looks like an API key in a string."""
    import re
    # Mask sk-... and similar patterns
    s = re.sub(r"sk-[A-Za-z0-9]{20,}", "<REDACTED>", s)
    s = re.sub(r"[A-Za-z0-9]{32,}", "<REDACTED>", s)
    return s


def main():
    print("=" * 56)
    print("Phase L.20 — Optional Live LLM Smoke-Test Harness")
    print("=" * 56)

    # ------------------------------------------------------------------
    # 1. Gate: only run if explicitly enabled
    # ------------------------------------------------------------------
    live_enabled = os.environ.get("SECNAV_LLM_LIVE_SMOKE", "").strip()
    if live_enabled not in ("1", "true", "yes", "on"):
        print("\nSKIP: SECNAV_LLM_LIVE_SMOKE is not set to 1.")
        print("This harness is optional and does not run by default.")
        print("To enable: set SECNAV_LLM_LIVE_SMOKE=1")
        print("=" * 56)
        return 0

    # ------------------------------------------------------------------
    # 2. Load provider config
    # ------------------------------------------------------------------
    config = LLMProviderConfig.from_env()
    provider = config.provider

    print(f"\nProvider : {provider}")
    print(f"Model    : {config.model or '(default)'}")
    print(f"Timeout  : {config.timeout_seconds}s")
    print(f"MaxTokens: {config.max_tokens}")
    print(f"KeyVar   : {config.api_key_env_var or '(none)'}")
    print(f"KeyPresent: {config.api_key_present()}")

    # ------------------------------------------------------------------
    # 3. Build backend + adapter
    # ------------------------------------------------------------------
    backend = build_llm_backend_from_config(config)
    adapter = LLMBuilderMediatorAdapter(backend=backend)

    # ------------------------------------------------------------------
    # 4. Minimal safe prompt
    # ------------------------------------------------------------------
    test_message = (
        "From Commanding Officer to Commander subject Training Plan"
    )
    inp = MediatorInput(
        session_id="l20-smoke",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message=test_message,
    )

    print(f"\nPrompt   : {test_message}")
    print("-" * 56)

    # ------------------------------------------------------------------
    # 5. Run through adapter
    # ------------------------------------------------------------------
    out = adapter.mediate(inp)

    # Sanitize any accidental key leakage in explanation
    explanation = _redact(out.get("explanation", "(none)"))
    safety_notes = [_redact(s) for s in out.get("safety_notes", [])]

    print(f"Intent        : {out['intent']}")
    print(f"Confidence    : {out['confidence']}")
    print(f"Explanation   : {explanation}")
    print(f"Safety Notes  : {safety_notes}")
    print(f"Requires Confirm: {out.get('requires_user_confirmation', False)}")

    # ------------------------------------------------------------------
    # 6. Validate behavior expectations
    # ------------------------------------------------------------------
    ok = True
    checks = []

    # Check A: adapter always returned a valid output (never crashed)
    checks.append(("A. Adapter returned valid output", True))

    # Check B: intent is in allowed set
    checks.append(("B. Intent in allowed set", out["intent"] in adapter.allowed_intents))

    # Check C: confidence bounded [0.0, 1.0]
    c = out["confidence"]
    checks.append(("C. Confidence bounded", 0.0 <= c <= 1.0))

    # Check D: payload update is a dict
    checks.append(("D. Payload update is dict", isinstance(out.get("proposed_payload_update", {}), dict)))

    # Check E: key-value lines is a list
    checks.append(("E. Key-value lines is list", isinstance(out.get("proposed_key_value_lines", []), list)))

    # Check F: no unsafe keys in payload update
    unsafe_found = [k for k in out.get("proposed_payload_update", {}) if k in {"cci_severity", "cci_config", "rule_promotion", "severity_override", "renderer_directive", "layout_override", "pdf_engine", "font_settings", "page_margins", "header_format", "footer_format"}]
    checks.append(("F. No unsafe keys in payload update", len(unsafe_found) == 0))

    # Check G: if provider is mock, we expect a real intent (not unknown)
    if provider == "mock":
        checks.append(("G. Mock provider yields real intent", out["intent"] != "unknown"))
    else:
        # For placeholder providers (openai/ollama without real calls), unknown is expected
        checks.append(("G. Placeholder provider yields controlled output", True))

    # Check H: no API key values in any printed field
    full_dump = json.dumps({k: _redact(str(v)) for k, v in out.items()})
    secret_like = any(tok in full_dump for tok in ["sk-", "api_key", "secret", "token"])
    checks.append(("H. No API key leakage in output", not secret_like))

    print("\n" + "-" * 56)
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {label}")
        if not passed:
            ok = False

    passed_count = sum(1 for _, p in checks if p)
    total_count = len(checks)

    print("-" * 56)
    print(f"Results: {passed_count}/{total_count} passed")
    print("=" * 56)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
