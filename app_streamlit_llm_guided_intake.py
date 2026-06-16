#!/usr/bin/env python3
"""
Phase L.26E — Streamlit LLM-Guided Intake Prototype (Provider & Model Picker)

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

Hotfix additions (Phase L.26A):
- Safe _has_pending_decisions() helper to handle int/list/None types

Debug additions (Phase L.26B):
- Behind-the-Scenes debug panel showing full mediator output
- Proposed KV lines visible before ingestion
- Validator state, block reasons, and warnings/errors exposed
- Enables copy-paste troubleshooting back to developer

Ollama additions (Phase L.26C–L.26D):
- Real Ollama backend via stdlib urllib
- One-click Ollama launchers (BAT + PS1)

Provider & Model Picker (Phase L.26E):
- Sidebar picker: Mock / Ollama Local / Ollama Cloud
- Local model discovery from localhost:11434/api/tags
- Model dropdown populated with installed Ollama models
- Cloud placeholder fail-closed if not configured
- UI selection overrides env defaults; env respected on first load
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

# Guarded pyperclip import (optional clipboard support)
try:
    import pyperclip as _pyperclip  # type: ignore[import-untyped]
    PYPERCLIP_AVAILABLE = True
except ImportError:
    _pyperclip = None  # type: ignore[misc]
    PYPERCLIP_AVAILABLE = False


def _copy_to_clipboard(text: str) -> tuple[bool, str]:
    """Copy text to clipboard if pyperclip is available; return (success, message)."""
    if PYPERCLIP_AVAILABLE and _pyperclip is not None:
        try:
            _pyperclip.copy(text)
            return True, "Copied to clipboard"
        except Exception:
            pass
    return False, "Clipboard not available — copy the text manually."


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
    list_ollama_models,
    ollama_service_status,
    provider_debug_status,
    resolve_ollama_default_model,
    selected_model_changed,
    selected_model_from_state,
    selected_provider_from_state,
    ui_provider_config,
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
    if "last_mediator_output" in st.session_state:
        del st.session_state.last_mediator_output
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
    status = provider_debug_status(config)
    return bool(status.get("available", False))


def _has_pending_decisions(validation_summary: dict) -> bool:
    """Safely check if there are pending decisions, handling int/list/None types."""
    pending = validation_summary.get("pending_decisions", 0)
    if isinstance(pending, int):
        return pending > 0
    if pending is None:
        return False
    try:
        return len(pending) > 0
    except TypeError:
        return bool(pending)


def _run_mediation(builder: BuilderSession, user_message: str) -> dict[str, Any]:
    """Run full mediation cycle: build input → adapter → ingest → return result.

    Respects UI provider/model selection from session state.
    Returns the full MediatorOutput dict so the UI can display debug info.
    """
    selected_provider = selected_provider_from_state(st.session_state)
    selected_model = selected_model_from_state(st.session_state)
    config = ui_provider_config(selected_provider, selected_model)

    backend = build_llm_backend_from_config(config)
    adapter = LLMBuilderMediatorAdapter(backend=backend)

    payload = builder.build_payload()
    missing_req = []
    missing_rec = []
    val = {}
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
        validation_summary=val,
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
                ok, msg = _copy_to_clipboard(prompt)
                st.toast(msg)

    # -- Sidebar: provider picker + reset -----------------------
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 New Letter", use_container_width=True):
            _reset_session()
            st.success("Session reset — start a new letter anytime.")
            st.rerun()

        st.divider()

        # Provider / Model Picker (L.26F)
        st.subheader("Provider & Model")

        provider_options = {
            "mock": "🛡️ Mock / Offline (default — no network)",
            "ollama": "🦙 Ollama Local (manual — requires local server)",
            "ollama_cloud": "☁️ Ollama Cloud / Hosted (manual — requires config)",
        }

        if "selected_provider" not in st.session_state:
            env_provider = os.environ.get("SECNAV_LLM_PROVIDER", "mock").strip().lower()
            if env_provider not in provider_options:
                env_provider = "mock"
            st.session_state.selected_provider = env_provider

        selected_provider = st.selectbox(
            "Provider",
            options=list(provider_options.keys()),
            format_func=lambda k: provider_options[k],
            index=list(provider_options.keys()).index(selected_provider_from_state(st.session_state)),
            key="provider_select",
        )

        selected_model = None
        if selected_provider == "mock":
            st.info("Mock mode uses a deterministic offline parser. No network required.")
            selected_model = "mock"

        elif selected_provider == "ollama":
            ollama_status = ollama_service_status()
            ollama_models = list_ollama_models()
            if ollama_models:
                if "selected_ollama_model" not in st.session_state:
                    env_model = os.environ.get("SECNAV_OLLAMA_MODEL", "").strip() or None
                    st.session_state.selected_ollama_model = resolve_ollama_default_model(ollama_models, env_model)
                selected_model = st.selectbox(
                    "Ollama Model",
                    options=ollama_models,
                    index=ollama_models.index(st.session_state.selected_ollama_model)
                    if st.session_state.selected_ollama_model in ollama_models else 0,
                    key="ollama_model_select",
                )
                st.success(f"Using Ollama model: {selected_model}")
                st.caption("Note: First inference may take 60–90 seconds while the model loads into memory. Wait for the response — this is normal for local Ollama.")
            else:
                st.warning("No Ollama models found. Ensure Ollama is running and you have pulled a model.")
                st.caption(ollama_status.get("message", "Ollama unavailable."))
                st.code("ollama pull llama3.2", language="bash")
                selected_model = None

        elif selected_provider == "ollama_cloud":
            st.info("Ollama Cloud / Hosted is not yet configured. Set environment variables manually to enable.")
            st.code("$env:SECNAV_LLM_PROVIDER = 'ollama_cloud'\n$env:SECNAV_OLLAMA_MODEL = 'your-model'", language="powershell")
            selected_model = "not_configured"

        selected_model_changed(st.session_state, selected_provider, selected_model)
        effective_config = ui_provider_config(selected_provider, selected_model)
        effective_status = provider_debug_status(effective_config)

        st.divider()
        st.markdown(f"**Active Provider:** `{selected_provider}`")
        if selected_model:
            st.markdown(f"**Active Model:** `{selected_model}`")
        st.markdown(f"**Provider Status:** `{effective_status.get('message', 'unknown')}`")
        st.caption("API keys are never shown in this UI.")

        if selected_provider == "ollama" and effective_status.get("reachable") and not effective_status.get("models"):
            st.warning("Ollama is reachable, but no installed models were discovered.")
        if selected_provider == "ollama" and not effective_status.get("reachable"):
            st.warning("Ollama does not appear to be running. Start Ollama, then try again.")

        st.session_state.provider_status_snapshot = effective_status

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
            provider_snapshot = st.session_state.get("provider_status_snapshot", {})
            if provider_snapshot and provider_snapshot.get("provider") == "ollama" and not provider_snapshot.get("available", False):
                assistant_msg += " [Provider status: Ollama unavailable or inference failed]"
            st.session_state.chat_log.append({
                "user": user_msg,
                "assistant": assistant_msg,
            })
            # Store full mediator output for debug panel
            st.session_state.last_mediator_output = out
            st.rerun()

        # Actions
        st.divider()
        val = builder.validation_summary()
        can_finalize = val.get("finalize_allowed", False)
        warnings_pending = _has_pending_decisions(val)

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

        # Debug / Behind-the-Scenes Panel
        st.divider()
        with st.expander("🐛 Debug — Behind the Scenes", expanded=False):
            st.markdown("*This panel shows what the mediator parsed, what the validator sees, and why actions are enabled or blocked. Paste this back to me if something looks wrong.*")
            
            # Last mediator output
            last_out = st.session_state.get("last_mediator_output", {})
            if last_out:
                st.markdown("#### Last Mediator Output")
                st.json(last_out)
            else:
                st.info("No mediator output yet. Send a message to populate this panel.")
            
            # Proposed KV lines
            st.markdown("#### Proposed KV Lines")
            kv = last_out.get("proposed_key_value_lines", [])
            if kv:
                for line in kv:
                    st.code(line, language="text")
            else:
                st.info("No KV lines proposed — the mediator didn't extract any fields from your message.")
            
            # Current validator state
            st.markdown("#### Current Validator State")
            st.json(val)
            
            # Block reason
            st.markdown("#### Block Reason")
            block = val.get("block_reason", "")
            if block:
                st.error(block)
            else:
                st.info("No block reason — finalize is allowed if all required fields are present.")
            
            # Warnings / errors
            st.markdown("#### Warnings / Errors")
            ws = builder.warning_summary()
            if ws:
                for w in ws:
                    st.warning(str(w))
            else:
                st.info("No warnings or errors reported by the validator.")


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
