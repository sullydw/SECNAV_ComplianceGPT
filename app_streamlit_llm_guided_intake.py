#!/usr/bin/env python3
"""
Phase L.24 — Streamlit LLM-Guided Intake Prototype (Usability Pass)

User-facing web UI that wraps the BuilderSession + Adapter + Provider layers.
All payload mutations route through BuilderSession.ingest_user_message().
No direct payload mutation from LLM/provider output.

Usability additions (Phase L.24):
- Instructions banner and example prompts
- Reset / New Letter control
- Transcript / history panel
- Provider status explanation
- Raw payload in collapsible section
- Improved validation display (errors, warnings, advisories separated)
"""

from __future__ import annotations

import json
import os
import sys
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
_EXAMPLE_PROMPTS = [
    "I need to write a standard letter.",
    "It is from Commanding Officer, Example Command.",
    "Send it to Commander, Example Group.",
    "The subject is Training Plan.",
    "Use SSIC 5216.",
    "The body should say this letter provides the proposed training plan.",
    "Signed by J. Q. Sample, Commanding Officer.",
    "No window envelope.",
]


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
            st.session_state.chat_log = []
        return st.session_state.builder
    # Fallback: non-Streamlit call (use a local instance)
    builder = BuilderSession(session_id="streamlit_ui")
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    return builder


def _reset_session() -> None:
    """Reset session state to start a new letter."""
    if "builder" in st.session_state:
        del st.session_state.builder
    if "chat_log" in st.session_state:
        del st.session_state.chat_log
    # _load_session will recreate on next access


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


# ------------------------------------------------------------------
# Page render
# ------------------------------------------------------------------
def _render_page():
    """Render the Streamlit page (called only when Streamlit is available)."""
    st.set_page_config(page_title="SECNAV Letter Builder", layout="wide")
    st.title("📄 SECNAV Compliant Letter Builder")
    st.caption("Phase L.24 — Guided Conversational Intake")

    # -- Instructions ----------------------------------------------
    with st.expander("ℹ️ How to use", expanded=True):
        st.write(
            "**Welcome.** This guided builder helps you create a Navy or Marine Corps "
            "standard letter. Just describe what you need in plain language, and the "
            "system will collect the required fields for you."
        )
        st.write(
            "**Steps:**"
            "\n1. Describe your letter in the chat box below (sender, recipient, subject, body, etc.)."
            "\n2. Watch the draft summary on the right as fields are captured."
            "\n3. Address any missing fields and review validation findings."
            "\n4. Accept warnings if comfortable, then click **Finalize**."
            "\n5. Once finalized, click **Render PDF** to download your letter."
        )
        st.write(
            "**Provider:** The default provider is a safe, offline mock backend. "
            "If you want to use a live LLM, set environment variables manually — "
            "but this is never required."
        )

        st.subheader("Example prompts you can paste")
        for i, prompt in enumerate(_EXAMPLE_PROMPTS, start=1):
            cols = st.columns([10, 1])
            cols[0].code(prompt, language="text")
            if cols[1].button("📋", key=f"copy_prompt_{i}"):
                import pyperclip  # noqa: F811
                pyperclip.copy(prompt)
                st.toast("Copied to clipboard")

    # -- Sidebar: provider + reset -------------------------------
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 New Letter", use_container_width=True):
            _reset_session()
            st.success("Session reset — start a new letter anytime.")
            st.rerun()

        st.divider()

        config = LLMProviderConfig.from_env()
        provider_label = _provider_status_label(config)
        available = _provider_available(config)

        st.subheader("Provider Status")
        st.markdown(f"**Type:** `{provider_label}`")
        st.markdown(f"**Available:** `{'Yes ✅' if available else 'No ⚠️'}`")
        st.markdown(f"**Model:** `{config.model or '(default)'}`")
        st.markdown(f"**Timeout:** `{config.timeout_seconds}s`")
        st.markdown(f"**Max Tokens:** `{config.max_tokens}`")
        st.caption("API keys are never shown in this UI.")

    # -- Main columns ---------------------------------------------
    builder = _load_session()

    col_chat, col_draft = st.columns([1, 1])

    with col_chat:
        st.header("💬 Conversation")

        # Transcript / history
        if "chat_log" not in st.session_state:
            st.session_state.chat_log = []

        if st.session_state.chat_log:
            with st.container(border=True):
                st.markdown("#### Conversation History")
                for entry in st.session_state.chat_log:
                    st.markdown(f"**User:** {entry['user']}")
                    st.markdown(f"→ *{entry['assistant']}*")
                    st.markdown("---")
        else:
            st.info("Start typing below to build your letter.")

        user_msg = st.chat_input("Type a field update or command...")
        if user_msg:
            out = _run_mediation(builder, user_msg)
            intent = out.get("intent", "unknown")
            explanation = out.get("explanation", "")
            assistant_msg = f"Detected intent: `{intent}`"
            if explanation:
                assistant_msg += f" — {explanation}"
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
            if st.button(
                "⚠️ Accept Warnings",
                disabled=not warnings_pending,
                help="Acknowledge warnings so you can proceed to finalize." if warnings_pending else "No warnings to accept.",
                use_container_width=True,
            ):
                _run_mediation(builder, "accept warnings")
                st.success("Warnings accepted.")
                st.rerun()
        with col_actions[1]:
            if st.button(
                "✅ Finalize",
                disabled=not can_finalize,
                help="Lock the draft. Only enabled when all required fields and validations are satisfied." if can_finalize else "Complete required fields and resolve errors before finalizing.",
                use_container_width=True,
            ):
                result = builder.finalize(accept_warnings=True)
                if result.get("finalized"):
                    st.success("Finalized successfully!")
                else:
                    st.error(f"Blocked: {result.get('block_reason', 'unknown')}")
                st.rerun()
        with col_actions[2]:
            payload = builder.build_payload()
            is_finalized = payload.get("finalized", False)
            if st.button(
                "🖨️ Render PDF",
                disabled=not is_finalized,
                help="Generate a PDF after finalizing." if is_finalized else "Finalize the draft before rendering.",
                use_container_width=True,
            ):
                try:
                    pdf_path = _OUTPUT_DIR / "streamlit_render.pdf"
                    tmp_json = _OUTPUT_DIR / "streamlit_payload.json"
                    with open(tmp_json, "w", encoding="utf-8") as fh:
                        json.dump(payload, fh, indent=2, default=str)
                    renderer = str(_REPO_ROOT / "src" / "pdf_v6_render.py")
                    import subprocess as _sp
                    _sp.run(
                        [sys.executable, renderer, str(tmp_json), str(pdf_path)],
                        check=True,
                        capture_output=True,
                    )
                    if pdf_path.exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=f,
                                file_name="letter.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        st.info(f"PDF rendered ({pdf_path.stat().st_size} bytes)")
                    else:
                        st.warning("Render completed but PDF not found.")
                except Exception as exc:
                    st.warning(f"Render not available in this environment: {exc}")

    with col_draft:
        st.header("📋 Draft Summary")
        payload = builder.build_payload()

        # Field cards
        st.markdown("### Current Fields")
        fields = [
            ("Document Type", payload.get("doc_type")),
            ("From", payload.get("from")),
            ("To", payload.get("to")),
            ("Subject", payload.get("subj")),
            ("SSIC", payload.get("ssic")),
            ("Body", 
             (payload.get("body")[0][:60] + "..." 
              if isinstance(payload.get("body"), list) and payload.get("body") 
              else payload.get("body") or "(none)")),
            ("Signature Name", payload.get("signature", {}).get("name", "(none)")),
            ("Signature Role", payload.get("signature", {}).get("role", "(none)")),
            ("Window Envelope", payload.get("window_envelope", "(not set)")),
        ]
        for label, value in fields:
            st.write(f"**{label}:** `{value}`")

        # Missing fields
        st.divider()
        st.markdown("### Missing Fields")
        missing = val.get("missing_required_fields", []) if "val" in dir() else []
        rec = val.get("missing_recommended_fields", []) if "val" in dir() else []
        if missing:
            st.error("❌ Required: " + ", ".join(missing))
        else:
            st.success("✅ All required fields present")
        if rec:
            st.info("ℹ️ Recommended: " + ", ".join(rec))

        # Validation breakdown
        st.divider()
        st.markdown("### Validation")
        totals = val.get("totals", {}) if "val" in dir() else {}
        err_count = totals.get("errors", 0)
        warn_count = totals.get("warnings", 0)
        adv_count = totals.get("advisories", 0)

        v_col1, v_col2, v_col3 = st.columns(3)
        v_col1.metric(label="Errors", value=err_count, delta=None, delta_color="inverse")
        v_col2.metric(label="Warnings", value=warn_count, delta=None, delta_color="off")
        v_col3.metric(label="Advisories", value=adv_count, delta=None, delta_color="normal")

        st.write(f"**Finalize allowed:** {'Yes ✅' if can_finalize else 'No ⛔'}")

        if warnings_pending:
            st.warning("⚠️ Warnings are pending — accept them before finalizing.")
        elif not can_finalize:
            st.error("⛔ Cannot finalize — please address errors or missing fields.")
        else:
            st.success("✅ Ready to finalize!")

        # Raw payload in collapsible section
        st.divider()
        with st.expander("🔍 Raw Payload Preview", expanded=False):
            preview = json.dumps(payload, indent=2, default=str)
            st.code(preview[:2500] + ("\n... (truncated)" if len(preview) > 2500 else ""), language="json")


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
