#!/usr/bin/env python3
"""
Phase L.15 — Mock LLM Builder Mediator

A deterministic, rule-based mediator prototype that follows the L.14 contract.
Translates natural-language user input into proposed structured updates
without using a real LLM.

Invariant:
  The mediator NEVER mutates BuilderSession directly.
  All proposed updates must be applied via builder.ingest_user_message().

Non-goals:
- no real LLM API calls
- no network calls
- no renderer/layout changes
- no CCI config/severity changes
- no rule promotion
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# L.14 contract data structures (plain dicts for portability)
# ---------------------------------------------------------------------------

def MediatorInput(
    session_id: str,
    current_step: str,
    payload_snapshot: dict[str, Any],
    missing_required_fields: list[str],
    missing_recommended_fields: list[str],
    validation_summary: dict[str, Any],
    warning_summary: list[dict],
    error_summary: list[dict],
    user_message: str,
    conversation_history_summary: str = "",
    available_commands: list[str] | None = None,
    safety_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Construct a MediatorInput dict conforming to the L.14 contract."""
    return {
        "session_id": session_id,
        "current_step": current_step,
        "payload_snapshot": payload_snapshot,
        "missing_required_fields": missing_required_fields,
        "missing_recommended_fields": missing_recommended_fields,
        "validation_summary": validation_summary,
        "warning_summary": warning_summary,
        "error_summary": error_summary,
        "user_message": user_message,
        "conversation_history_summary": conversation_history_summary,
        "available_commands": available_commands or [],
        "safety_flags": safety_flags or {
            "block_invented_official_data": True,
            "require_confirmation_for_inferred": True,
            "require_confirmation_before_finalize": True,
            "require_confirmation_before_render": True,
        },
    }


def MediatorOutput(
    intent: str,
    proposed_payload_update: dict[str, Any] | None = None,
    proposed_key_value_lines: list[str] | None = None,
    next_question: dict[str, Any] | None = None,
    explanation: str = "",
    requires_user_confirmation: bool = False,
    warnings_to_surface: list[dict] | None = None,
    blocked_reason: str | None = None,
    confidence: float = 1.0,
    safety_notes: list[str] | None = None,
) -> dict[str, Any]:
    """Construct a MediatorOutput dict conforming to the L.14 contract."""
    return {
        "intent": intent,
        "proposed_payload_update": proposed_payload_update or {},
        "proposed_key_value_lines": proposed_key_value_lines or [],
        "next_question": next_question,
        "explanation": explanation,
        "requires_user_confirmation": requires_user_confirmation,
        "warnings_to_surface": warnings_to_surface or [],
        "blocked_reason": blocked_reason,
        "confidence": confidence,
        "safety_notes": safety_notes or [],
    }


# ---------------------------------------------------------------------------
# Mock LLM Builder Mediator — deterministic, rule-based
# ---------------------------------------------------------------------------

class MockLLMBuilderMediator:
    """
    Deterministic mediator that maps natural-language-ish messages to
    structured intents and payload updates.
    """

    # Known field extractors: regex pattern -> (field_path, value_group)
    _FIELD_PATTERNS: list[tuple[re.Pattern, str]] = [
        # From
        (re.compile(r"from\s+(.+?)(?:\.|$)", re.IGNORECASE), "from"),
        (re.compile(r"sender\s+is\s+(.+?)(?:\.|$)", re.IGNORECASE), "from"),
        (re.compile(r"the\s+letter\s+is\s+from\s+(.+?)(?:\.|$)", re.IGNORECASE), "from"),
        # To
        (re.compile(r"to\s+(.+?)(?:\.|$)", re.IGNORECASE), "to"),
        (re.compile(r"recipient\s+is\s+(.+?)(?:\.|$)", re.IGNORECASE), "to"),
        (re.compile(r"send\s+(?:it|this)\s+to\s+(.+?)(?:\.|$)", re.IGNORECASE), "to"),
        # Subject
        (re.compile(r"subject\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "subj"),
        (re.compile(r"subj\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "subj"),
        (re.compile(r"regarding\s+(.+?)(?:\.|$)", re.IGNORECASE), "subj"),
        (re.compile(r"about\s+(.+?)(?:\.|$)", re.IGNORECASE), "subj"),
        # Body
        (re.compile(r"body\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "body"),
        (re.compile(r"(?:the\s+)?body\s+(?:of\s+)?(?:the\s+)?letter\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "body"),
        (re.compile(r"(?:this\s+)?letter\s+(?:provides|states|says)\s+(.+?)(?:\.|$)", re.IGNORECASE), "body"),
        # SSIC
        (re.compile(r"ssic\s+(?:is\s+)?(\d{4})", re.IGNORECASE), "ssic"),
        (re.compile(r"ssic\s+(?:is\s+)?(\d{4}[A-Z]?)", re.IGNORECASE), "ssic"),
        # Document type
        (re.compile(r"(?:doc_type|document\s+type)\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "doc_type"),
        # Distribution
        (re.compile(r"distribution\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "distribution"),
        # Copy-to
        (re.compile(r"copy[\s-]to\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "copy_to"),
        # Via
        (re.compile(r"via\s+(?:is\s+)?(.+?)(?:\.|$)", re.IGNORECASE), "via"),
        # Window envelope
        (re.compile(r"window\s+envelope\s+(?:is\s+)?(true|yes|1|false|no|0)", re.IGNORECASE), "window_envelope"),
    ]

    # Signature patterns
    _SIGNATURE_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"signed\s+by\s+(.+)$", re.IGNORECASE), "signature.name"),
        (re.compile(r"signature\s+(?:name\s+)?(?:is\s+)?(.+)$", re.IGNORECASE), "signature.name"),
        (re.compile(r"(?:the\s+)?signatory\s+(?:is\s+)?(.+)$", re.IGNORECASE), "signature.name"),
    ]

    # Official data that must never be invented
    _OFFICIAL_DATA_FIELDS: set[str] = {"ssic", "command", "ref", "encl", "routing"}

    def __init__(self) -> None:
        self._conversation_history: list[dict[str, Any]] = []

    # -- public API -----------------------------------------------------------

    def mediate(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a MediatorInput and return a MediatorOutput.
        """
        user_message: str = input_data.get("user_message", "")
        payload: dict[str, Any] = input_data.get("payload_snapshot", {})
        missing_required: list[str] = input_data.get("missing_required_fields", [])
        warnings: list[dict] = input_data.get("warning_summary", [])
        errors: list[dict] = input_data.get("error_summary", [])
        safety_flags: dict[str, bool] = input_data.get("safety_flags", {})

        normalized = user_message.strip().lower()

        # Guard: empty message
        if not normalized:
            return MediatorOutput(
                intent="unknown",
                explanation="No user message provided.",
                confidence=0.0,
            )

        # -- intent detection --------------------------------------------------

        intent, confidence = self._detect_intent(normalized)

        # -- command intents (no payload updates) ------------------------------

        if intent in {"accept_warnings", "finalize", "render_pdf"}:
            requires_confirmation = (
                (intent == "finalize" and safety_flags.get("require_confirmation_before_finalize", True))
                or (intent == "render_pdf" and safety_flags.get("require_confirmation_before_render", True))
                or (intent == "accept_warnings" and bool(warnings))
            )

            explanation = f"Detected intent: {intent}."
            if errors:
                return MediatorOutput(
                    intent=intent,
                    explanation=f"{explanation} Cannot proceed: validation errors exist.",
                    blocked_reason="Validation errors block finalize/render.",
                    warnings_to_surface=errors,
                    requires_user_confirmation=True,
                    confidence=confidence,
                )
            if warnings and intent != "accept_warnings":
                return MediatorOutput(
                    intent=intent,
                    explanation=f"{explanation} Warnings are pending. Please accept warnings first.",
                    blocked_reason="Pending warnings must be accepted before finalize/render.",
                    warnings_to_surface=warnings,
                    requires_user_confirmation=True,
                    confidence=confidence,
                )

            return MediatorOutput(
                intent=intent,
                explanation=explanation,
                requires_user_confirmation=requires_confirmation,
                warnings_to_surface=warnings if warnings else [],
                confidence=confidence,
            )

        # -- provide_field / revise_field ---------------------------------------

        updates: dict[str, Any] = {}
        kv_lines: list[str] = []
        safety_notes: list[str] = []
        requires_confirmation = False

        # Extract signature first (structured dotted keys)
        sig_updates, sig_lines, sig_notes = self._extract_signature(normalized)
        updates.update(sig_updates)
        kv_lines.extend(sig_lines)
        safety_notes.extend(sig_notes)

        # Extract other fields
        for pattern, field_path in self._FIELD_PATTERNS:
            match = pattern.search(user_message)
            if match:
                value = match.group(1).strip()
                # Normalize window_envelope boolean
                if field_path == "window_envelope":
                    value = value.lower() in ("true", "yes", "1")
                updates[field_path] = value
                kv_lines.append(f"{field_path}: {value}")

                # Official data guard: if field is official and wasn't explicitly
                # matched by a user-provided pattern, flag it.
                if field_path in self._OFFICIAL_DATA_FIELDS and safety_flags.get("require_confirmation_for_inferred", True):
                    requires_confirmation = True
                    safety_notes.append(f"Inferred official field '{field_path}': {value}")

        # -- missing required fields → ask question ------------------------------

        next_question = None
        if missing_required and not updates:
            # No field updates this turn → ask for next required field
            # Always ask questions if there are missing required fields, regardless of intent
            field_path = missing_required[0]
            next_question = {
                "field_path": field_path,
                "prompt_text": self._generate_question_text(field_path),
                "bucket": "required",
            }
            return MediatorOutput(
                intent=intent,
                next_question=next_question,
                explanation=f"Asking for missing required field: {field_path}",
                confidence=confidence,
            )

        # -- assemble output ---------------------------------------------------

        explanation = f"Detected intent: {intent}."
        if updates:
            explanation += f" Proposed updates for {', '.join(updates.keys())}."
        if safety_notes:
            explanation += f" Safety notes: {'; '.join(safety_notes)}."

        return MediatorOutput(
            intent=intent,
            proposed_payload_update=updates,
            proposed_key_value_lines=kv_lines,
            next_question=next_question,
            explanation=explanation,
            requires_user_confirmation=requires_confirmation,
            warnings_to_surface=warnings if warnings else [],
            confidence=confidence,
            safety_notes=safety_notes,
        )

    # -- internal helpers ----------------------------------------------------

    def _detect_intent(self, message: str) -> tuple[str, float]:
        """Return (intent, confidence) based on keyword heuristics."""
        if re.search(r"\b(start|begin|create|new)\b.*\bletter\b", message):
            return "start_letter", 1.0
        if re.search(r"\baccept\b.*\bwarning(s)?\b", message):
            return "accept_warnings", 1.0
        if re.search(r"\bfinalize\b", message):
            return "finalize", 1.0
        if re.search(r"\b(render|generate|create).*\bpdf\b", message):
            return "render_pdf", 1.0
        if re.search(r"\b(explain|what|why)\b.*\bwarning(s)?\b", message):
            return "request_warning_explanation", 1.0
        if re.search(r"\b(change|revise|update|fix|correct)\b", message):
            return "revise_field", 0.9
        # Default: treat as providing a field if any known pattern matches
        if any(p[0].search(message) for p in self._FIELD_PATTERNS):
            return "provide_field", 0.85
        if any(p[0].search(message) for p in self._SIGNATURE_PATTERNS):
            return "provide_field", 0.85
        return "unknown", 0.5

    def _extract_signature(self, message: str) -> tuple[dict[str, Any], list[str], list[str]]:
        """Extract signature fields from message. Returns (updates, kv_lines, safety_notes)."""
        updates: dict[str, Any] = {}
        kv_lines: list[str] = []
        safety_notes: list[str] = []

        # Extract name
        name_match = None
        for pattern, field_path in self._SIGNATURE_PATTERNS:
            match = pattern.search(message)
            if match:
                name_match = match
                break

        if name_match:
            name = name_match.group(1).strip()
            updates["signature.name"] = name
            kv_lines.append(f"signature.name: {name}")

        # Extract role/title from surrounding text (simple heuristics)
        # Look for "... is a Commanding Officer" or "..., Commanding Officer, ..."
        role_patterns = [
            re.compile(r"(?:is\s+a|as\s+|,\s+)(commanding officer|director|chief|supervisor|manager|officer)[\.,;]?", re.IGNORECASE),
            re.compile(r"(?:commanding officer|director|chief|supervisor|manager|officer)\s+of\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
        ]
        for pattern in role_patterns:
            match = pattern.search(message)
            if match:
                role = match.group(1).strip()
                updates["signature.role"] = role
                kv_lines.append(f"signature.role: {role}")
                # If we also have a name, infer title = role
                if "signature.name" in updates and "signature.title" not in updates:
                    updates["signature.title"] = role
                    kv_lines.append(f"signature.title: {role}")
                break

        return updates, kv_lines, safety_notes

    def _generate_question_text(self, field_path: str) -> str:
        """Generate a natural-language question for a missing required field."""
        # Map field paths to friendly questions
        questions = {
            "from": "Who is the sender of this letter?",
            "to": "Who is the recipient of this letter?",
            "subj": "What is the subject of this letter?",
            "body": "What is the body or main content of this letter?",
            "signature.name": "Who is signing this letter? (Provide the name)",
            "signature.role": "What is the signatory's role? (e.g., Commanding Officer)",
            "ssic": "What is the SSIC (Standard Subject Identification Code)?",
            "doc_type": "What type of document is this? (e.g., standard letter)",
            "copy_to": "Who should receive copies of this letter?",
            "distribution": "How should this letter be distributed?",
            "via": "Via whom should this letter be routed?",
            "window_envelope": "Should this letter use a window envelope? (true/false)",
        }
        return questions.get(field_path, f"Please provide the {field_path}.")


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_mock_mediator() -> MockLLMBuilderMediator:
    """Create a fresh MockLLMBuilderMediator instance."""
    return MockLLMBuilderMediator()


# ---------------------------------------------------------------------------
# Module-level sanity check (not a full test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mediator = create_mock_mediator()

    # Example: provide from
    inp = MediatorInput(
        session_id="demo_001",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj"],
        missing_recommended_fields=["via", "copy_to"],
        validation_summary={},
        warning_summary=[],
        error_summary=[],
        user_message="From Commanding Officer, Example Command",
    )
    out = mediator.mediate(inp)
    print("Intent:", out["intent"])
    print("Updates:", out["proposed_payload_update"])
    print("KV lines:", out["proposed_key_value_lines"])
    print("Explanation:", out["explanation"])
    print("Confidence:", out["confidence"])
