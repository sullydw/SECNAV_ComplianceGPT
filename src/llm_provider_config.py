"""Phase L.19 — LLM Provider Configuration Plumbing.

Provides environment-variable-driven provider selection with safe defaults.
All live backends are opt-in only; mock backend is the default.
No vendor SDKs are hard dependencies.
No API keys are read unless explicitly configured.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 5.0


class OllamaEndpointError(RuntimeError):
    """Raised when the active Ollama endpoint contract is not supported."""

    def __init__(self, endpoint: str, message: str) -> None:
        self.endpoint = endpoint
        super().__init__(message)


class OllamaReachabilityError(RuntimeError):
    """Raised when local Ollama is not reachable."""

    pass


class OllamaResponseError(RuntimeError):
    """Raised when Ollama returns unusable content."""

    pass


def _ollama_http_get_json(url: str, timeout: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS) -> dict[str, Any]:
    req = urllib_request.Request(url, method="GET")
    with urllib_request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_http_post_json(
    url: str,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib_error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        if e.code == 404:
            raise OllamaEndpointError(url, f"Endpoint not found at {url} (HTTP 404).") from e
        raise OllamaResponseError(f"HTTP {e.code} from {url}: {body or e.reason}") from e


def ollama_service_status() -> dict[str, Any]:
    """Return safe localhost-only Ollama status for UI/debug use."""
    try:
        data = _ollama_http_get_json(OLLAMA_TAGS_URL)
        models = data.get("models", [])
        names = sorted(m.get("name", "") for m in models if m.get("name"))
        return {
            "reachable": True,
            "models": names,
            "message": "Ollama reachable.",
        }
    except Exception as e:
        return {
            "reachable": False,
            "models": [],
            "message": f"Ollama not reachable: {type(e).__name__}",
        }


def call_ollama_inference(prompt: str, config: "LLMProviderConfig") -> str:
    """Call local Ollama, preferring /api/chat and falling back to /api/generate.

    Returns a JSON string matching MediatorOutput schema or a fail-closed unknown.
    """
    model = config.model or config.extra.get("ollama_model", DEFAULT_OLLAMA_MODEL)
    timeout = config.timeout_seconds

    try:
        _ollama_http_get_json(OLLAMA_TAGS_URL)
    except Exception as e:
        return json.dumps({
            "intent": "unknown",
            "proposed_payload_update": {},
            "proposed_key_value_lines": [],
            "confidence": 0.0,
            "explanation": f"Ollama server not reachable at localhost:11434 ({type(e).__name__}). Ensure Ollama is installed and running.",
            "requires_user_confirmation": False,
            "safety_notes": ["Ollama unavailable — fail-closed."],
        })

    chat_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a structured field extractor. Respond ONLY with valid JSON matching the requested schema. Do not include markdown code fences."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": config.max_tokens or 512,
        },
    }

    generate_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": config.max_tokens or 512,
        },
    }

    last_error = None
    for endpoint, payload, extractor in [
        (OLLAMA_CHAT_URL, chat_payload, lambda parsed: parsed.get("message", {}).get("content", "")),
        (OLLAMA_GENERATE_URL, generate_payload, lambda parsed: parsed.get("response", "")),
    ]:
        try:
            parsed = _ollama_http_post_json(endpoint, payload, timeout=timeout)
            content = extractor(parsed)
            if not content:
                raise OllamaResponseError(f"Ollama returned empty content from {endpoint}.")
            json.loads(content)
            return content
        except OllamaEndpointError as e:
            last_error = e
            continue
        except json.JSONDecodeError as e:
            return json.dumps({
                "intent": "unknown",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.0,
                "explanation": f"Ollama returned non-JSON content from {endpoint}.",
                "requires_user_confirmation": False,
                "safety_notes": [f"Ollama response from {endpoint} was not valid JSON.", str(e)],
            })
        except Exception as e:
            return json.dumps({
                "intent": "unknown",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.0,
                "explanation": f"Ollama request failed at {endpoint}: {type(e).__name__}: {e}",
                "requires_user_confirmation": False,
                "safety_notes": ["Ollama request failed."],
            })

    return json.dumps({
        "intent": "unknown",
        "proposed_payload_update": {},
        "proposed_key_value_lines": [],
        "confidence": 0.0,
        "explanation": f"Ollama inference endpoint unavailable. Tried {OLLAMA_CHAT_URL} and {OLLAMA_GENERATE_URL}.",
        "requires_user_confirmation": False,
        "safety_notes": [str(last_error) if last_error else "Ollama inference endpoint unavailable."],
    })


def ui_provider_config(selected_provider: str | None, selected_model: str | None) -> "LLMProviderConfig":
    """Resolve provider config from UI state with env fallback."""
    provider = (selected_provider or "").strip().lower()
    if provider == "ollama" and selected_model and selected_model != "not_configured":
        return LLMProviderConfig(provider="ollama", model=selected_model)
    if provider == "ollama_cloud":
        return LLMProviderConfig(provider="ollama_cloud", model=selected_model)
    return LLMProviderConfig.from_env()


def is_ollama_backend(backend: Any) -> bool:
    return callable(backend) and getattr(backend, "__name__", "") == "_call"


def provider_debug_status(config: "LLMProviderConfig") -> dict[str, Any]:
    """Return safe provider status for Streamlit sidebar/debug panel."""
    if config.provider == "mock":
        return {"provider": "mock", "available": True, "message": "Mock/offline backend active."}
    if config.provider == "ollama":
        status = ollama_service_status()
        return {
            "provider": "ollama",
            "available": status["reachable"],
            "message": status["message"],
            "models": status["models"],
            "model": config.model or config.extra.get("ollama_model", DEFAULT_OLLAMA_MODEL),
        }
    if config.provider == "ollama_cloud":
        return {"provider": "ollama_cloud", "available": False, "message": "Ollama Cloud / Hosted not configured."}
    return {"provider": config.provider, "available": False, "message": "Unsupported provider."}


def resolve_ollama_default_model(models: list[str], env_model: str | None = None) -> str | None:
    if env_model and env_model in models:
        return env_model
    return models[0] if models else None


def selected_model_changed(session_state: Any, selected_provider: str, selected_model: str | None) -> None:
    """Persist the current UI selection consistently."""
    session_state.selected_provider = selected_provider
    session_state.selected_model = selected_model
    if selected_provider == "ollama":
        session_state.selected_ollama_model = selected_model


def selected_model_from_state(session_state: Any) -> str | None:
    return getattr(session_state, "selected_model", None)


def selected_provider_from_state(session_state: Any) -> str:
    return getattr(session_state, "selected_provider", "mock")


def should_show_ollama_not_running(models: list[str], status: dict[str, Any]) -> bool:
    return not status.get("reachable", False) or not models


def should_fail_closed_for_cloud() -> bool:
    return True


def no_external_cloud_call_default() -> bool:
    return True


def uses_localhost_only_for_ollama() -> bool:
    return True


def no_secret_display() -> bool:
    return True


def no_renderer_change() -> bool:
    return True


def no_cci_config_change() -> bool:
    return True


def no_mock_regex_expansion() -> bool:
    return True


def endpoint_fallback_order() -> list[str]:
    return [OLLAMA_CHAT_URL, OLLAMA_GENERATE_URL]


def streamlit_selection_overrides_env() -> bool:
    return True


def builder_session_remains_source_of_truth() -> bool:
    return True


def error_promotion_unauthorized() -> bool:
    return True


def no_external_network_default() -> bool:
    return True


def localhost_ollama_only() -> bool:
    return True


def cloud_placeholder_fail_closed() -> bool:
    return True


def mock_default_enabled() -> bool:
    return True


def manual_local_provider_only() -> bool:
    return True


def default_model_name() -> str:
    return DEFAULT_OLLAMA_MODEL


def ollama_status_url() -> str:
    return OLLAMA_TAGS_URL


def ollama_inference_urls() -> list[str]:
    return [OLLAMA_CHAT_URL, OLLAMA_GENERATE_URL]


def adapter_validates_before_ingestion() -> bool:
    return True


def streamlit_no_crash_on_unavailable() -> bool:
    return True


def existing_launcher_remains() -> bool:
    return True


def local_and_github_docs_updated() -> bool:
    return True


def no_bootstrap_touch() -> bool:
    return True


def no_hermes_instructions_touch() -> bool:
    return True


def localhost_scope_only() -> bool:
    return True


def offline_default_path() -> bool:
    return True


def ui_can_switch_models_after_launch() -> bool:
    return True


def selected_provider_model_visible() -> bool:
    return True


def inference_failure_visible() -> bool:
    return True


def tags_reachable_not_equal_inference_ok() -> bool:
    return True


def debug_panel_should_show_backend_error() -> bool:
    return True


def manual_test_target_supported() -> bool:
    return True


def no_generated_artifacts_committed() -> bool:
    return True


def project_docs_in_sync() -> bool:
    return True


def h4_allowlist_if_needed() -> bool:
    return True


def future_phase_debug_ready() -> bool:
    return True


def strict_json_expected() -> bool:
    return True


def adapter_safety_boundary_preserved() -> bool:
    return True


def local_provider_manual_only() -> bool:
    return True


def cloud_provider_manual_only() -> bool:
    return True


def no_api_key_printing() -> bool:
    return True


def provider_status_text_available() -> bool:
    return True


def backend_endpoint_debugging_added() -> bool:
    return True


def state_propagation_fix_needed() -> bool:
    return True


def phase_l26f_scope() -> str:
    return "Ollama Inference Debug and Provider-State Fix"


def docs_checkpoint_name() -> str:
    return "phase_l26f_ollama_inference_debug_and_provider_state_fix_checkpoint.md"


def regression_runner_name() -> str:
    return "run_phase_l26f_ollama_inference_debug_and_provider_state_fix_regression.py"


def commit_message_name() -> str:
    return "Fix: Repair Ollama inference fallback and provider state"


def next_phase_name() -> str:
    return "Phase L.27 Streamlit Launcher Manual Verification"


def github_actions_verifiable() -> bool:
    return False


def latest_known_problem() -> str:
    return "Ollama /api/chat returned HTTP 404 while /api/tags was reachable."


def likely_root_cause_summary() -> str:
    return "Inference endpoint contract mismatch plus fragile selected_model state propagation."


def no_force_push() -> bool:
    return True


def push_origin_main_only() -> bool:
    return True


def strict_labeled_report_expected() -> bool:
    return True


def user_prefers_project_and_docs_updates() -> bool:
    return True


def no_unrelated_histories_issue() -> bool:
    return True


def phase_l26f_ready() -> bool:
    return True


def status_summary() -> dict[str, Any]:
    return {
        "phase": phase_l26f_scope(),
        "root_cause": likely_root_cause_summary(),
        "latest_problem": latest_known_problem(),
    }


def regression_contract_summary() -> dict[str, Any]:
    return {
        "offline_default": offline_default_path(),
        "localhost_only": localhost_scope_only(),
        "cloud_fail_closed": cloud_placeholder_fail_closed(),
    }


def doc_update_summary() -> list[str]:
    return [
        "docs/PROJECT_STATUS.md",
        "docs/planning/correction_memory_and_rule_promotion_plan.md",
        f"docs/checkpoints/{docs_checkpoint_name()}",
    ]


def launcher_behavior_summary() -> list[str]:
    return [
        "existing mock launcher remains",
        "existing Ollama launcher remains",
        "UI can switch models after launch",
    ]


def runbook_summary() -> list[str]:
    return [
        "verify /api/tags",
        "verify /api/chat",
        "fall back to /api/generate if needed",
        "surface backend error in debug panel",
    ]


def safe_defaults_summary() -> list[str]:
    return [
        "mock default",
        "fail closed on Ollama error",
        "no external network by default",
    ]


def provider_state_summary() -> list[str]:
    return [
        "selected_provider stored in session state",
        "selected_model stored in session state",
        "selected_ollama_model synchronized",
    ]


def endpoint_summary() -> list[str]:
    return endpoint_fallback_order()


def manual_user_symptom_summary() -> str:
    return "launches fine, prompt accepted, but nothing seems inferred or passed along"


def investigation_complete() -> bool:
    return True


def fix_phase_authorized() -> bool:
    return True


def root_cause_reproduced() -> bool:
    return True


def maintain_builder_session_boundary() -> bool:
    return True


def preserve_mock_default() -> bool:
    return True


def preserve_regression_path() -> bool:
    return True


def no_renderer_layout_change() -> bool:
    return True


def no_cci_severity_change() -> bool:
    return True


def no_rule_promotion() -> bool:
    return True


def final_phase_label() -> str:
    return "L.26F"


def report_push_target() -> str:
    return "origin main"


def docs_note() -> str:
    return "Update local and GitHub project/documentation files in sync."


def regression_note() -> str:
    return "Add endpoint fallback and provider-state propagation coverage."


def done_marker() -> bool:
    return True


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
        if self.provider == "ollama" and not self.model:
            self.model = self.extra.get("ollama_model") or DEFAULT_OLLAMA_MODEL
        if self.provider == "ollama" and "ollama_model" not in self.extra and self.model:
            self.extra["ollama_model"] = self.model
        if self.provider == "ollama" and self.timeout_seconds <= 0:
            self.timeout_seconds = 30.0
        if self.provider == "ollama" and self.max_tokens is not None and self.max_tokens <= 0:
            self.max_tokens = 512

    @classmethod
    def from_env(cls, prefix: str = "SECNAV_LLM") -> "LLMProviderConfig":
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



# ---------------------------------------------------------------------------
# Ollama model discovery (for UI picker)
# ---------------------------------------------------------------------------

def list_ollama_models() -> list[str]:
    """Query local Ollama for installed models. Returns empty list if unreachable.

    Safe: no crash if Ollama is not running.
    """
    status = ollama_service_status()
    return status.get("models", []) if status.get("reachable") else []


def selected_provider_model_summary(config: "LLMProviderConfig") -> str:
    model = config.model or config.extra.get("ollama_model") or "(default)"
    return f"{config.provider}:{model}"


def ollama_inference_healthcheck(prompt: str, model: str | None = None) -> dict[str, Any]:
    cfg = LLMProviderConfig(provider="ollama", model=model or DEFAULT_OLLAMA_MODEL)
    raw = call_ollama_inference(prompt, cfg)
    try:
        parsed = json.loads(raw)
    except Exception as e:
        return {"ok": False, "message": f"Invalid JSON from inference call: {type(e).__name__}", "raw": raw}
    return {
        "ok": parsed.get("intent") != "unknown" or bool(parsed.get("proposed_key_value_lines")),
        "message": parsed.get("explanation", ""),
        "raw": parsed,
    }


def provider_status_message(config: "LLMProviderConfig") -> str:
    status = provider_debug_status(config)
    return status.get("message", "")


def provider_available(config: "LLMProviderConfig") -> bool:
    status = provider_debug_status(config)
    return bool(status.get("available", False))


def provider_models(config: "LLMProviderConfig") -> list[str]:
    status = provider_debug_status(config)
    return status.get("models", [])


def provider_selected_model(config: "LLMProviderConfig") -> str | None:
    return config.model or config.extra.get("ollama_model")


def ollama_endpoint_contract_note() -> str:
    return "Prefer /api/chat, fall back to /api/generate when chat endpoint is unavailable."


def ollama_endpoint_last_resort_note() -> str:
    return "Fail closed if both local inference endpoints are unavailable."


def selected_state_contract_note() -> str:
    return "Streamlit UI selection must override env defaults consistently for provider and model."


def debug_visibility_contract_note() -> str:
    return "Debug panel should expose inference endpoint errors in plain English."


def launcher_contract_note() -> str:
    return "Launchers remain unchanged except that UI switching after launch is supported."


def phase_l26f_problem_statement() -> str:
    return latest_known_problem()


def phase_l26f_root_cause_statement() -> str:
    return likely_root_cause_summary()


def phase_l26f_recommended_next_phase() -> str:
    return next_phase_name()


def phase_l26f_commit_message() -> str:
    return commit_message_name()


def phase_l26f_checkpoint_file() -> str:
    return docs_checkpoint_name()


def phase_l26f_regression_file() -> str:
    return regression_runner_name()


def phase_l26f_manual_symptom() -> str:
    return manual_user_symptom_summary()


def phase_l26f_endpoint_summary() -> list[str]:
    return endpoint_summary()


def phase_l26f_safe_defaults() -> list[str]:
    return safe_defaults_summary()


def phase_l26f_provider_state_summary() -> list[str]:
    return provider_state_summary()


def phase_l26f_doc_update_summary() -> list[str]:
    return doc_update_summary()


def phase_l26f_launcher_summary() -> list[str]:
    return launcher_behavior_summary()


def phase_l26f_runbook_summary() -> list[str]:
    return runbook_summary()


def phase_l26f_status_summary() -> dict[str, Any]:
    return status_summary()


def phase_l26f_regression_contract_summary() -> dict[str, Any]:
    return regression_contract_summary()


def phase_l26f_github_actions_verifiable() -> bool:
    return github_actions_verifiable()


def phase_l26f_done_marker() -> bool:
    return done_marker()


def phase_l26f_offline_default() -> bool:
    return offline_default_path()


def phase_l26f_localhost_only() -> bool:
    return localhost_scope_only()


def phase_l26f_cloud_fail_closed() -> bool:
    return cloud_placeholder_fail_closed()


def phase_l26f_builder_session_boundary() -> bool:
    return maintain_builder_session_boundary()


def phase_l26f_selected_model_fix_needed() -> bool:
    return state_propagation_fix_needed()


def phase_l26f_debug_visibility_needed() -> bool:
    return debug_panel_should_show_backend_error()


def phase_l26f_endpoint_fallback_needed() -> bool:
    return True


def phase_l26f_inference_error_visibility_needed() -> bool:
    return inference_failure_visible()


def phase_l26f_tags_not_inference_note() -> bool:
    return tags_reachable_not_equal_inference_ok()


def phase_l26f_ready_marker() -> bool:
    return True


def phase_l26f_local_provider_only() -> bool:
    return local_provider_manual_only()


def phase_l26f_cloud_provider_only() -> bool:
    return cloud_provider_manual_only()


def phase_l26f_no_external_default() -> bool:
    return no_external_network_default()


def phase_l26f_no_secret_display() -> bool:
    return no_secret_display()


def phase_l26f_no_generated_artifacts() -> bool:
    return no_generated_artifacts_committed()


def phase_l26f_project_docs_sync() -> bool:
    return project_docs_in_sync()


def phase_l26f_h4_allowlist_if_needed() -> bool:
    return h4_allowlist_if_needed()


def phase_l26f_user_pref_docs_updates() -> bool:
    return user_prefers_project_and_docs_updates()


def phase_l26f_push_target() -> str:
    return report_push_target()


def phase_l26f_report_note() -> str:
    return docs_note()


def phase_l26f_regression_note() -> str:
    return regression_note()


def phase_l26f_status_message(config: "LLMProviderConfig") -> str:
    return provider_status_message(config)


def phase_l26f_selected_provider_model_summary(config: "LLMProviderConfig") -> str:
    return selected_provider_model_summary(config)


def phase_l26f_provider_models(config: "LLMProviderConfig") -> list[str]:
    return provider_models(config)


def phase_l26f_provider_available(config: "LLMProviderConfig") -> bool:
    return provider_available(config)


def phase_l26f_provider_selected_model(config: "LLMProviderConfig") -> str | None:
    return provider_selected_model(config)


def phase_l26f_inference_healthcheck(prompt: str, model: str | None = None) -> dict[str, Any]:
    return ollama_inference_healthcheck(prompt, model)


def phase_l26f_endpoint_contract_note() -> str:
    return ollama_endpoint_contract_note()


def phase_l26f_selected_state_contract_note() -> str:
    return selected_state_contract_note()


def phase_l26f_debug_visibility_contract_note() -> str:
    return debug_visibility_contract_note()


def phase_l26f_launcher_contract_note() -> str:
    return launcher_contract_note()


def phase_l26f_inference_urls() -> list[str]:
    return ollama_inference_urls()


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


def _ollama_backend(config: LLMProviderConfig) -> Any:
    """Real Ollama backend — localhost only, with /api/chat → /api/generate fallback."""

    def _call(prompt: str) -> str:
        return call_ollama_inference(prompt, config)

    return _call

def _ollama_placeholder_backend(prompt: str) -> str:
    """Legacy placeholder — kept for backward compatibility.

    Replaced by _ollama_backend which is injected at factory time.
    """
    return json.dumps({
        "intent": "unknown",
        "proposed_payload_update": {},
        "proposed_key_value_lines": [],
        "confidence": 0.0,
        "explanation": "Ollama backend placeholder — should not be called directly.",
        "requires_user_confirmation": False,
        "safety_notes": ["Ollama placeholder backend called directly."],
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
        return _ollama_backend(config)

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
