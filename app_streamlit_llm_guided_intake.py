#!/usr/bin/env python3
"""
Phase L.23 — Streamlit LLM-Guided Intake Prototype

User-facing web UI that wraps the BuilderSession + Adapter + Provider layers.
All payload mutations route through BuilderSession.ingest_user_message().
No direct payload mutation from LLM/provider output.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# ------------------------------------------------------------------
# Guarded Streamlit import
# ------------------------------------------------------------------
try:
    import streamlit as st  # type: ignore[import-untyped]
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# ------------------------------------------------------------------
# Project paths
# ------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent
_SRC_DIR = _REPO_ROOT / "src"
_OUTPUT_DIR = _REPO_ROOT / "output"
_OUTPUT_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(_SRC_DIR))

# ------------------------------------------------------------------
# Backend imports
# ------------------------------------------------------------------
from llm_builder_mediator import (
    MockLLMBuilderMediator,
    LLMBuilderMediatorAdapter,
    MediatorInput,
)
from conversational_builder import BuilderSession
from llm_provider_config import (
    LLMProviderConfig,
    build_llm_backend_from_config,
)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
_UNSAFE_KEYS = {
    "cci_severity", "cci_config", "rule_promotion", "severity_override",
    "renderer_directive", "layout_override", "command_injection",
}
_ALLOWED_INTENTS = {
    "provide_field", "accept_warnings", "finalize", "render_pdf",
    "reject_warning", "ask_for_missing", "unknown",
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _load_session() -> BuilderSession:
    """Load or create a BuilderSession in Streamlit state."""
    if STREAMLIT_AVAILABLE:
        if "builder" not in st.session_state:
            st.session_state.builder = BuilderSession(session_id="streamlit_ui")
            st.session_state.builder.start(
                initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}}
            )
        return st.session_state.builder
    # Fallback: non-Streamlit call (use a local instance)
    builder = BuilderSession(session_id="streamlit_ui")
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    return builder


def _provider_status_label(config: LLMProviderConfig) -> str:
    if config.provider == "mock":
        return "mock (default — no network)"
    if config.provider == "openai":
        return "openai (manual — requires API key)"
    if config.provider == "ollama":
        return "ollama (manual — requires local server)"
    return f"{config.provider} (unsupported — unavailable)"


def _provider_available(config: LLMProviderConfig) -> bool:
    backend = build_llm_backend_from_config(config)
    label = getattr(backend, "__class__", None).__name__ if backend else ""
    return label == "FakeBackend"


def _redact_api_keys(text: str) -> str:
    """Remove API key-like values from strings."""
    import re
    return re.sub(r"sk-[A-Za-z0-9]{20,}", "[REDACTED]", text)


def _run_mediation(builder: BuilderSession, user_message: str):
    """Run full mediation cycle: build input → adapter → ingest → return result."""
    config = LLMProviderConfig.from_env()
    backend = build_llm_backend_from_config(config)
    adapter = LLMBuilderMediatorAdapter(backend=backend)

    payload = builder.build_payload()
    missing_req = []
    missing_rec = []
    try:
        val = builder.validation_summary()
        missing_req = val.get("missing_required_fields", [])
        missing_rec = val.get("missing_recommended_fields", [])
    except Exception:
        pass

    inp = MediatorInput(
        session_id=builder.build_payload().get("session_id", "streamlit_ui"),
        current_step="intake",
        payload_snapshot=payload,
        missing_required_fields=missing_req,
        missing_recommended_fields=missing_rec,
        validation_summary=val if "val" in dir() else {},
        warning_summary=builder.warning_summary(),
        error_summary=[],
        user_message=user_message,
        conversation_history_summary="",
    )

    out = adapter.mediate(inp)

    kv_lines = out.get("proposed_key_value_lines", [])
    if kv_lines:
        builder.ingest_user_message("\n".join(kv_lines))

    return out


def _render_page():
    """Render the Streamlit page (called only when Streamlit is available)."""
    st.set_page_config(page_title="SECNAV Letter Builder", layout="wide")
    st.title("SECNAV Compliant Letter Builder")
    st.caption("Phase L.23 — LLM-Guided Conversational Intake")

    # -- left column ---------------------------------------------------
    col_chat, col_draft = st.columns([1, 1])

    with col_chat:
        st.header("Conversation")

        # Provider status
        config = LLMProviderConfig.from_env()
        provider_label = _provider_status_label(config)
        available = _provider_available(config)

        badge_color = "green" if available else "orange"
        st.markdown(
            f"**Provider:** `{provider_label}` | **Available:** `:{'green' if available else 'orange'}-circle:`"
        )

        builder = _load_session()

        # Chat history
        if "chat_log" not in st.session_state:
            st.session_state.chat_log = []

        for entry in st.session_state.chat_log:
            with st.chat_message("user"):
                st.write(entry["user"])
            with st.chat_message("assistant"):
                st.write(entry["assistant"])

        # Input
        user_msg = st.chat_input("Type a field update or command...")
        if user_msg:
            out = _run_mediation(builder, user_msg)
            intent = out.get("intent", "unknown")
            explanation = out.get("explanation", "")
            assistant_msg = f"**Intent:** `{intent}`"
            if explanation:
                assistant_msg += f"\n\n{explanation}"
            st.session_state.chat_log.append({
                "user": user_msg,
                "assistant": assistant_msg,
            })
            st.rerun()

        # Actions
        st.divider()

        val = builder.validation_summary()
        can_finalize = val.get("finalize_allowed", False)
        warnings_pending = len(val.get("pending_decisions", [])) > 0

        col_actions = st.columns(3)
        with col_actions[0]:
            if st.button("Accept Warnings", disabled=not warnings_pending):
                _run_mediation(builder, "accept warnings")
                st.success("Warnings accepted.")
                st.rerun()
        with col_actions[1]:
            if st.button("Finalize", disabled=not can_finalize):
                result = builder.finalize(accept_warnings=True)
                if result.get("finalized"):
                    st.success("Finalized successfully!")
                else:
                    st.error(f"Blocked: {result.get('block_reason', 'unknown')}")
                st.rerun()
        with col_actions[2]:
            payload = builder.build_payload()
            is_finalized = payload.get("finalized", False)
            if st.button("Render PDF", disabled=not is_finalized):
                try:
                    pdf_path = _OUTPUT_DIR / "streamlit_render.pdf"
                    # Use existing renderer path: write payload JSON to temp file,
                    # then invoke src/pdf_v6_render.py (same as L.7 CLI)
                    import json as _json
                    import subprocess as _sp
                    tmp_json = _OUTPUT_DIR / "streamlit_payload.json"
                    with open(tmp_json, "w", encoding="utf-8") as fh:
                        _json.dump(payload, fh, indent=2, default=str)
                    renderer = str(_REPO_ROOT / "src" / "pdf_v6_render.py")
                    _sp.run(
                        [sys.executable, renderer, str(tmp_json), str(pdf_path)],
                        check=True,
                        capture_output=True,
                    )
                    if pdf_path.exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download PDF",
                                data=f,
                                file_name="letter.pdf",
                                mime="application/pdf",
                            )
                        st.info(f"PDF rendered ({pdf_path.stat().st_size} bytes)")
                    else:
                        st.warning("Render completed but PDF not found.")
                except Exception as exc:
                    st.warning(f"Render not available in this environment: {exc}")

    # -- right column --------------------------------------------------
    with col_draft:
        st.header("Draft Summary")
        payload = builder.build_payload()

        st.subheader("Current Fields")
        fields = {
            "Document Type": payload.get("doc_type"),
            "From": payload.get("from"),
            "To": payload.get("to"),
            "Subject": payload.get("subj"),
            "SSIC": payload.get("ssic"),
            "Body": payload.get("body"),
            "Signature": payload.get("signature"),
            "Window Envelope": payload.get("window_envelope"),
        }
        for label, value in fields.items():
            st.write(f"**{label}:** `{value or '(none)'}`")

        st.divider()

        st.subheader("Missing Fields")
        missing = val.get("missing_required_fields", []) if "val" in dir() else []
        rec = val.get("missing_recommended_fields", []) if "val" in dir() else []
        if missing:
            st.error("Required: " + ", ".join(missing))
        else:
            st.success("All required fields present")
        if rec:
            st.info("Recommended: " + ", ".join(rec))

        st.divider()

        st.subheader("Validation")
        totals = val.get("totals", {}) if "val" in dir() else {}
        st.write(f"**Findings:** {totals.get('total_findings', 0)}  |  "
                 f"**Errors:** {totals.get('errors', 0)}  |  "
                 f"**Warnings:** {totals.get('warnings', 0)}  |  "
                 f"**Advisories:** {totals.get('advisories', 0)}")
        st.write(f"**Finalize allowed:** {can_finalize if 'can_finalize' in dir() else False}")
        if warnings_pending:
            st.warning("Warnings are pending — accept them before finalizing.")
        elif not can_finalize:
            st.error("Cannot finalize — please address errors or missing fields.")
        else:
            st.success("Ready to finalize!")

        st.divider()

        st.subheader("Provider Status")
        st.write(f"**Provider:** `{provider_label}`")
        st.write(f"**Available:** `{'Yes' if available else 'No'}`")
        st.write(f"**Model:** `{config.model or '(default)'}`")
        st.write(f"**Timeout:** `{config.timeout_seconds}s`")
        st.write(f"**Max Tokens:** `{config.max_tokens}`")
        st.write("No API keys are displayed in the UI.")

        st.divider()

        st.subheader("Raw Payload Preview")
        import json
        preview = json.dumps(payload, indent=2, default=str)
        st.code(preview[:2000] + ("\n... (truncated)" if len(preview) > 2000 else ""), language="json")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
def main() -> None:
    if not STREAMLIT_AVAILABLE:
        print("ERROR: Streamlit is not installed.")
        print("Install it with: pip install streamlit")
        print("Then run: streamlit run app_streamlit_llm_guided_intake.py")
        sys.exit(1)
    _render_page()


if __name__ == "__main__":
    main()
