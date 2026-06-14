"""Phase L.19 — LLM Provider Configuration Plumbing.

Provides environment-variable-driven provider selection with safe defaults.
All live backends are opt-in only; mock backend is the default.
No vendor SDKs are hard dependencies.
No API keys are read unless explicitly configured.
"""

from __future__ import annotations

import os
import json
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class LLMProviderConfig:
    """Immutable-ish provider configuration loaded from environment."""

    def __init__(
        self,
        provider: str = "mock",
        model: str | None = None,
        timeout_seconds: float = 30.0,
        max_tokens: int | None = 512,
        api_key_env_var: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider.lower().strip()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.api_key_env_var = api_key_env_var
        self.extra = extra or {}

    @classmethod
    def from_env(cls, prefix: str = "SECNAV_LLM") -> LLMProviderConfig:
        """Build configuration from environment variables.

        Reads (all optional, mock backend if absent):
          {PREFIX}_PROVIDER          → provider name (default: mock)
          {PREFIX}_MODEL             → model name
          {PREFIX}_TIMEOUT_SECONDS   → timeout (default: 30.0)
          {PREFIX}_MAX_TOKENS        → max tokens (default: 512)
          {PREFIX}_API_KEY_ENV_VAR   → env var that holds the API key name
                                        (e.g. SECNAV_OPENAI_API_KEY)
          SECNAV_OPENAI_API_KEY      → not read directly; referenced by api_key_env_var
          SECNAV_OLLAMA_MODEL        → Ollama model override
        """
        provider = os.environ.get(f"{prefix}_PROVIDER", "mock").strip().lower()
        model = os.environ.get(f"{prefix}_MODEL", None)
        if model:
            model = model.strip()

        timeout_raw = os.environ.get(f"{prefix}_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(timeout_raw)
            if timeout <= 0 or timeout > 300:
                timeout = 30.0
        except ValueError:
            timeout = 30.0

        max_tokens_raw = os.environ.get(f"{prefix}_MAX_TOKENS", "512")
        try:
            max_tokens = int(max_tokens_raw)
            if max_tokens <= 0 or max_tokens > 4096:
                max_tokens = 512
        except ValueError:
            max_tokens = 512

        api_key_env_var = os.environ.get(f"{prefix}_API_KEY_ENV_VAR", None)
        if api_key_env_var:
            api_key_env_var = api_key_env_var.strip()

        extra: dict[str, Any] = {}
        ollama_model = os.environ.get("SECNAV_OLLAMA_MODEL", None)
        if ollama_model:
            extra["ollama_model"] = ollama_model.strip()

        return cls(
            provider=provider,
            model=model,
            timeout_seconds=timeout,
            max_tokens=max_tokens,
            api_key_env_var=api_key_env_var,
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict. API key value is never included."""
        return {
            "provider": self.provider,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_tokens": self.max_tokens,
            "api_key_env_var": self.api_key_env_var,
            "extra": {k: v for k, v in self.extra.items() if "key" not in k.lower()},
        }

    def api_key_present(self) -> bool:
        """Return True if the configured API key env var exists and is non-empty."""
        if not self.api_key_env_var:
            return False
        val = os.environ.get(self.api_key_env_var, "")
        return bool(val.strip())


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------

def _unavailable_backend(prompt: str) -> str:
    """Safe fallback backend that always returns unavailable JSON."""
    return json.dumps({
        "intent": "unknown",
        "proposed_payload_update": {},
        "proposed_key_value_lines": [],
        "confidence": 0.0,
        "explanation": "LLM backend unavailable (provider not configured or missing credentials).",
        "requires_user_confirmation": False,
        "safety_notes": ["Backend unavailable."],
    })


def _openai_placeholder_backend(prompt: str) -> str:
    """Placeholder OpenAI backend — returns unavailable without making calls.

    If real integration is desired, this callable should be replaced with a
    wrapper that imports openai only when needed and validates the key.
    """
    return json.dumps({
        "intent": "unknown",
        "proposed_payload_update": {},
        "proposed_key_value_lines": [],
        "confidence": 0.0,
        "explanation": "OpenAI backend not yet wired. Set SECNAV_LLM_PROVIDER=openai and provide a valid API key via the configured env var.",
        "requires_user_confirmation": False,
        "safety_notes": ["OpenAI backend is a placeholder; no network call made."],
    })


def _ollama_placeholder_backend(prompt: str) -> str:
    """Placeholder Ollama backend — returns unavailable without making calls.

    If real integration is desired, this callable should be replaced with a
    wrapper that imports requests/httpx only when needed and targets the
    local Ollama endpoint.
    """
    return json.dumps({
        "intent": "unknown",
        "proposed_payload_update": {},
        "proposed_key_value_lines": [],
        "confidence": 0.0,
        "explanation": "Ollama backend unavailable. Set SECNAV_LLM_PROVIDER=ollama and ensure a local Ollama server is running.",
        "requires_user_confirmation": False,
        "safety_notes": ["Ollama backend is a placeholder; no network call made."],
    })


def build_llm_backend_from_config(config: LLMProviderConfig | None = None) -> Any:
    """Build a backend callable from configuration.

    Returns:
        A callable with signature Callable[[str], str] suitable for injection
        into LLMBuilderMediatorAdapter.

    Safe defaults:
      - config is None → mock backend
      - provider is "mock" → mock backend (deterministic)
      - provider unsupported → unavailable backend (no network)
      - provider "openai" without key → unavailable backend (no network)
      - provider "ollama" → unavailable backend (no network)
    """
    if config is None:
        config = LLMProviderConfig.from_env()

    provider = config.provider

    if provider == "mock":
        # Deterministic mock backend from llm_builder_mediator
        from llm_builder_mediator import FakeBackend
        return FakeBackend("valid")

    if provider == "openai":
        if not config.api_key_present():
            return _unavailable_backend
        return _openai_placeholder_backend

    if provider == "ollama":
        return _ollama_placeholder_backend

    # Unsupported provider → safe unavailable backend
    return _unavailable_backend


# ---------------------------------------------------------------------------
# Convenience: build adapter from environment
# ---------------------------------------------------------------------------

def build_adapter_from_env() -> Any:
    """One-shot factory: reads env, builds backend, returns adapter.

    Import guard: this imports llm_builder_mediator.LLMBuilderMediatorAdapter.
    """
    from llm_builder_mediator import LLMBuilderMediatorAdapter
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    return LLMBuilderMediatorAdapter(backend=backend)
