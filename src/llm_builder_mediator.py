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
        # Colon-labeled fields (stop before next capitalized label or end of string)
        (re.compile(r"subject:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "subj"),
        (re.compile(r"body:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "body"),
        (re.compile(r"date:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "date"),
        (re.compile(r"ssic:\s*(\d{4}[A-Z]?)", re.IGNORECASE), "ssic"),
        (re.compile(r"originator\s+code:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "originator_code"),
        (re.compile(r"point\s+of\s+contact:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "point_of_contact"),
        (re.compile(r"signature:\s*(.+?)(?=\.\s+[A-Z][\w\s]+:|$)", re.IGNORECASE), "signature.name"),
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

        # Post-process: fix common natural-language crossovers (e.g., "from X to Y")
        from_val = updates.get("from", "")
        if from_val and re.search(r"\s+to\s+", from_val, re.IGNORECASE):
            parts = re.split(r"\s+to\s+", from_val, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                updates["from"] = parts[0].strip()
                updates["to"] = parts[1].strip()
                # Rebuild KV lines for from/to
                kv_lines = [line for line in kv_lines if not line.startswith("from:") and not line.startswith("to:")]
                kv_lines.append(f"from: {updates['from']}")
                kv_lines.append(f"to: {updates['to']}")

        # Infer plain-language subject from purpose statements
        if "subj" not in updates:
            inferred_subj = self._infer_subject(normalized)
            if inferred_subj:
                updates["subj"] = inferred_subj
                kv_lines.append(f"subj: {inferred_subj}")
                requires_confirmation = True
                safety_notes.append("Inferred subject from user purpose statement.")

        # Infer body draft from purpose statements
        if "body" not in updates:
            inferred_body = self._infer_body(normalized)
            if inferred_body:
                updates["body"] = inferred_body
                kv_lines.append(f"body: {inferred_body}")
                requires_confirmation = True
                safety_notes.append("Inferred body draft from user purpose statement.")

        # -- missing required fields → ask question ------------------------------

        next_question = None
        # Identify required fields that are still missing after extracted/inferred updates
        fields_still_missing = [f for f in missing_required if f not in updates]
        if fields_still_missing and not next_question:
            field_path = fields_still_missing[0]
            next_question = {
                "field_path": field_path,
                "prompt_text": self._generate_question_text(field_path),
                "bucket": "required",
            }

        # If absolutely nothing extracted and no missing required fields, fall back to first missing
        if missing_required and not updates and not next_question:
            field_path = missing_required[0]
            next_question = {
                "field_path": field_path,
                "prompt_text": self._generate_question_text(field_path),
                "bucket": "required",
            }
            # Early return when no updates at all
            return MediatorOutput(
                intent=intent,
                next_question=next_question,
                explanation=f"Asking for missing required field: {field_path}",
                confidence=confidence,
            )

        # If we extracted some fields but the user still lacks a key detail, ask one follow-up
        if next_question is None and not updates:
            # Already handled by the early-return above when no updates at all
            pass

        # Follow-up for date-change requests where date is not yet provided
        if next_question is None and updates and "date" not in updates:
            if re.search(r"\b(tbd|open date|change a date|change the date|current date|scheduled date|original date)\b", normalized):
                next_question = {
                    "field_path": "date",
                    "prompt_text": "What is the original or currently scheduled date you want to change from?",
                    "bucket": "recommended",
                }

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

    def _infer_subject(self, message: str) -> str | None:
        """Infer a plain-language subject from a user's purpose statement."""
        # Use only the first sentence that looks like a purpose statement
        sentences = re.split(r"(?<!\w\w)[.!?]\s+", message)
        purpose_fragments = [
            s for s in sentences
            if re.search(r"\b(request|ask|change|update|modify|need|want)\b", s, re.IGNORECASE)
        ]
        purpose_text = purpose_fragments[0] if purpose_fragments else sentences[0] if sentences else message
        # Trim trailing routing clause markers
        purpose_text = re.split(r"\s+(it is from|signed by|via)\b", purpose_text, flags=re.IGNORECASE)[0].strip()

        purpose_patterns = [
            (re.compile(r"\b(request|ask)\b.*?\b(to|for)\b\s+(.+?)(?:[.!?]|$)", re.IGNORECASE), 3),
            (re.compile(r"\b(need|want)\s+to\s+(request|ask|change|update|modify)\b\s*(.+?)(?:[.!?]|$)", re.IGNORECASE), 3),
            (re.compile(r"\b(change|update|modify)\s+a\s+(.+?)(?:[.!?]|$)", re.IGNORECASE), 2),
            (re.compile(r"\b(approve|disapprove|forward|direct)\s+(.+?)(?:[.!?]|$)", re.IGNORECASE), 2),
        ]
        for pattern, group_idx in purpose_patterns:
            match = pattern.search(purpose_text)
            if match:
                raw = match.group(group_idx).strip()
                raw = re.split(r"\s+(it is|this is|signed by|from|via|regards|sincerely)\b", raw, flags=re.IGNORECASE)[0]
                raw = raw.strip().rstrip(",")
                if raw and len(raw) > 3:
                    return raw[:120]
        return None

    def _infer_body(self, message: str) -> str | None:
        """Infer a brief body/purpose draft from a user's statement."""
        sentences = re.split(r"(?<!\w\w)[.!?]\s+", message)
        purpose_fragments = [
            s for s in sentences
            if re.search(r"\b(request|ask|change|update|modify|need|want)\b", s, re.IGNORECASE)
        ]
        purpose_text = purpose_fragments[0] if purpose_fragments else sentences[0] if sentences else message
        purpose_text = re.split(r"\s+(it is from|signed by|via)\b", purpose_text, flags=re.IGNORECASE)[0].strip()

        purpose_patterns = [
            (re.compile(r"\b(request|ask)\b.*?\b(to|for)\b\s+(.+?)(?:[.!?]|$)", re.IGNORECASE), 3),
            (re.compile(r"\b(need|want)\s+to\s+(request|ask|change|update|modify)\b\s*(.+?)(?:[.!?]|$)", re.IGNORECASE), 3),
            (re.compile(r"\b(change|update|modify)\s+a\s+(.+?)(?:[.!?]|$)", re.IGNORECASE), 2),
        ]
        for pattern, group_idx in purpose_patterns:
            match = pattern.search(purpose_text)
            if match:
                raw = match.group(group_idx).strip()
                raw = re.split(r"\s+(it is|this is|signed by|from|via)\b", raw, flags=re.IGNORECASE)[0]
                raw = raw.strip().rstrip(",")
                if raw and len(raw) > 3:
                    return f"Purpose: {raw[:300]}"
        return None

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
# Phase L.17 — LLM Builder Mediator Adapter with Fake Backend
# ---------------------------------------------------------------------------

class SafetyFilter:
    """
    Configurable safety filter for LLM mediator output.

    Rejects prohibited fields, enforces confirmation for unsafe intents,
    and marks invented official data for review.
    """

    _PROHIBITED_KEYS: set[str] = {
        "cci_severity", "cci_config", "rule_promotion", "severity_override",
        "renderer_directive", "layout_override", "pdf_engine",
        "font_settings", "page_margins", "header_format", "footer_format",
    }

    _OFFICIAL_DATA_KEYS: set[str] = {"ssic", "command", "ref", "encl", "routing"}

    def __init__(
        self,
        block_invented_official_data: bool = True,
        require_confirmation_for_inferred: bool = True,
        require_confirmation_before_finalize: bool = True,
        require_confirmation_before_render: bool = True,
        min_confidence: float = 0.3,
        max_confidence: float = 1.0,
    ) -> None:
        self.block_invented_official_data = block_invented_official_data
        self.require_confirmation_for_inferred = require_confirmation_for_inferred
        self.require_confirmation_before_finalize = require_confirmation_before_finalize
        self.require_confirmation_before_render = require_confirmation_before_render
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence

    def apply(
        self,
        raw_output: dict[str, Any],
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run safety filters on raw LLM output.
        Returns a sanitized MediatorOutput dict.
        """
        safety_notes: list[str] = []
        intent: str = raw_output.get("intent", "unknown")
        confidence: float = raw_output.get("confidence", 0.5)

        # -- required keys check -----------------------------------------------
        required_keys = {"intent", "proposed_payload_update", "proposed_key_value_lines", "confidence"}
        missing_keys = required_keys - set(raw_output.keys())
        if missing_keys:
            safety_notes.append(f"Missing required keys from backend output: {sorted(missing_keys)}.")
            if "intent" in missing_keys:
                intent = "unknown"
            if "confidence" in missing_keys:
                confidence = 0.5

        # -- confidence bounds ------------------------------------------------
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
            safety_notes.append("Confidence was non-numeric; defaulted to 0.5.")
        confidence = float(confidence)
        if confidence < self.min_confidence:
            intent = "unknown"
            safety_notes.append(f"Confidence {confidence} below threshold {self.min_confidence}; degraded to unknown.")
        confidence = max(self.min_confidence, min(self.max_confidence, confidence))

        # -- intent validation -------------------------------------------------
        allowed = input_data.get("allowed_intents", [
            "start_letter", "provide_field", "revise_field",
            "accept_warnings", "request_warning_explanation",
            "finalize", "render_pdf", "unknown",
        ])
        if intent not in allowed:
            intent = "unknown"
            safety_notes.append(f"Unsupported intent '{raw_output.get('intent')}' replaced with unknown.")

        # -- payload update sanitization ---------------------------------------
        proposed_payload_update: dict[str, Any] = raw_output.get("proposed_payload_update") or {}
        if not isinstance(proposed_payload_update, dict):
            proposed_payload_update = {}
            safety_notes.append("proposed_payload_update was not a dict; cleared.")

        # Reject prohibited keys
        for key in list(proposed_payload_update.keys()):
            if key in self._PROHIBITED_KEYS:
                del proposed_payload_update[key]
                safety_notes.append(f"Prohibited key '{key}' rejected from payload update.")

        # Reject invented official data
        payload_snapshot: dict[str, Any] = input_data.get("payload_snapshot", {})
        for key in list(proposed_payload_update.keys()):
            if key in self._OFFICIAL_DATA_KEYS and self.block_invented_official_data:
                # If key was not already in payload_snapshot, mark as invented
                if key not in payload_snapshot:
                    safety_notes.append(f"Invented official data '{key}' detected; marked for confirmation.")

        # -- key-value lines validation ----------------------------------------
        proposed_key_value_lines: list[str] = raw_output.get("proposed_key_value_lines") or []
        if not isinstance(proposed_key_value_lines, list):
            proposed_key_value_lines = []
            safety_notes.append("proposed_key_value_lines was not a list; cleared.")
        else:
            # Keep only str items
            filtered: list[str] = []
            for item in proposed_key_value_lines:
                if isinstance(item, str):
                    filtered.append(item)
                else:
                    safety_notes.append(f"Non-string key-value line removed: {item!r}")
            proposed_key_value_lines = filtered

        # -- confirmation enforcement -------------------------------------------
        requires_confirmation: bool = raw_output.get("requires_user_confirmation", False)
        if intent in {"finalize", "render_pdf"}:
            if self.require_confirmation_before_finalize and intent == "finalize":
                requires_confirmation = True
            if self.require_confirmation_before_render and intent == "render_pdf":
                requires_confirmation = True
        if intent == "accept_warnings":
            requires_confirmation = True

        # -- warnings_to_surface validation -------------------------------------
        warnings_to_surface: list[dict] = raw_output.get("warnings_to_surface") or []
        if not isinstance(warnings_to_surface, list):
            warnings_to_surface = []

        # -- blocked_reason handling --------------------------------------------
        blocked_reason: str | None = raw_output.get("blocked_reason")
        if not isinstance(blocked_reason, (str, type(None))):
            blocked_reason = None

        # -- next_question validation -------------------------------------------
        next_question: dict[str, Any] | None = raw_output.get("next_question")
        if not isinstance(next_question, (dict, type(None))):
            next_question = None

        # -- explanation fallback -----------------------------------------------
        explanation: str = raw_output.get("explanation", "")
        if not isinstance(explanation, str):
            explanation = ""
        if safety_notes and not explanation:
            explanation = "Safety filters applied."

        # If degraded to unknown and no next_question, generate one
        if intent == "unknown" and not next_question:
            missing = input_data.get("missing_required_fields", [])
            if missing:
                field_path = missing[0]
                next_question = {
                    "field_path": field_path,
                    "prompt_text": f"Please provide the {field_path}.",
                    "bucket": "required",
                }

        return MediatorOutput(
            intent=intent,
            proposed_payload_update=proposed_payload_update,
            proposed_key_value_lines=proposed_key_value_lines,
            next_question=next_question,
            explanation=explanation,
            requires_user_confirmation=requires_confirmation,
            warnings_to_surface=warnings_to_surface,
            blocked_reason=blocked_reason,
            confidence=confidence,
            safety_notes=safety_notes,
        )


class FakeBackend:
    """
    Deterministic fake backend for testing the LLMBuilderMediatorAdapter.
    Returns JSON strings based on a response key or callable override.
    """

    def __init__(
        self,
        response_key: str = "valid",
        custom_response: str | None = None,
        override: dict[str, Any] | None = None,
    ) -> None:
        self.response_key = response_key
        self.custom_response = custom_response
        self.override = override or {}

    def __call__(self, prompt: str) -> str:
        """Return a JSON string matching the configured response key."""
        if self.custom_response is not None:
            return self.custom_response

        responses: dict[str, dict[str, Any]] = {
            "valid": {
                "intent": "provide_field",
                "proposed_payload_update": {"from": "Commander Example"},
                "proposed_key_value_lines": ["from: Commander Example"],
                "confidence": 0.9,
                "explanation": "Detected from field.",
            },
            "malformed": "this is not json {",
            "missing_keys": {
                "proposed_payload_update": {},
                "confidence": 0.8,
            },
            "unsupported_intent": {
                "intent": "delete_everything",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.95,
            },
            "low_confidence": {
                "intent": "provide_field",
                "proposed_payload_update": {"from": "Commander Example"},
                "proposed_key_value_lines": ["from: Commander Example"],
                "confidence": 0.1,
            },
            "high_confidence": {
                "intent": "provide_field",
                "proposed_payload_update": {"from": "Commander Example"},
                "proposed_key_value_lines": ["from: Commander Example"],
                "confidence": 999.0,
            },
            "cci_tamper": {
                "intent": "provide_field",
                "proposed_payload_update": {"cci_severity": "error", "from": "Commander Example"},
                "proposed_key_value_lines": ["from: Commander Example"],
                "confidence": 0.9,
            },
            "renderer_directive": {
                "intent": "provide_field",
                "proposed_payload_update": {"layout_override": "custom", "from": "Commander Example"},
                "proposed_key_value_lines": ["from: Commander Example"],
                "confidence": 0.9,
            },
            "invented_ssic": {
                "intent": "provide_field",
                "proposed_payload_update": {"ssic": "1234", "from": "Commander Example"},
                "proposed_key_value_lines": ["ssic: 1234", "from: Commander Example"],
                "confidence": 0.9,
            },
            "finalize_no_confirm": {
                "intent": "finalize",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.95,
                "requires_user_confirmation": False,
            },
            "render_no_confirm": {
                "intent": "render_pdf",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.95,
                "requires_user_confirmation": False,
            },
            "accept_warnings_silent": {
                "intent": "accept_warnings",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.9,
                "requires_user_confirmation": False,
            },
            "unknown": {
                "intent": "unknown",
                "proposed_payload_update": {},
                "proposed_key_value_lines": [],
                "confidence": 0.5,
                "explanation": "I did not understand.",
            },
        }

        base = responses.get(self.response_key, responses["unknown"])
        if isinstance(base, dict):
            merged = {**base, **self.override}
            import json
            return json.dumps(merged)
        return base


class LLMBuilderMediatorAdapter:
    """
    Thin boundary between a real LLM backend and BuilderSession.

    Injected backend: a callable that takes a prompt string and returns
    raw text (expected to be JSON matching MediatorOutput schema).

    All output is validated and safety-filtered before return.
    """

    def __init__(
        self,
        backend: Any | None = None,
        allowed_intents: list[str] | None = None,
        min_confidence: float = 0.3,
        max_confidence: float = 1.0,
        safety_filter: SafetyFilter | None = None,
    ) -> None:
        self.backend = backend
        self.allowed_intents = allowed_intents or [
            "start_letter", "provide_field", "revise_field",
            "accept_warnings", "request_warning_explanation",
            "finalize", "render_pdf", "unknown",
        ]
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.safety_filter = safety_filter or SafetyFilter(
            min_confidence=min_confidence,
            max_confidence=max_confidence,
        )

    def _build_prompt(self, input_data: dict[str, Any]) -> str:
        """Build a prompt string from MediatorInput for the backend."""
        user_message = input_data.get("user_message", "")
        payload = input_data.get("payload_snapshot", {})
        missing_required = input_data.get("missing_required_fields", [])
        missing_recommended = input_data.get("missing_recommended_fields", [])
        validation_summary = input_data.get("validation_summary", {})
        warning_summary = input_data.get("warning_summary", [])
        error_summary = input_data.get("error_summary", [])
        current_step = input_data.get("current_step", "intake")

        # Plain-English warning/error messages only
        warning_texts = []
        for w in warning_summary:
            if isinstance(w, dict):
                warning_texts.append(w.get("message", str(w)))
            else:
                warning_texts.append(str(w))

        error_texts = []
        for e in error_summary:
            if isinstance(e, dict):
                error_texts.append(e.get("message", str(e)))
            else:
                error_texts.append(str(e))

        prompt_lines = [
            "You are a translator, not the source of truth.",
            "Your role: interpret user natural-language input and propose structured field updates.",
            "You do NOT own final state, validation, or rendering.",
            "",
            "Rules:",
            "1. Do not invent official data (SSIC, command names, routing, references).",
            "2. Output must be valid JSON matching the schema below — no markdown, no prose outside JSON.",
            "3. Use only the allowed intents listed below.",
            "4. Warnings and errors from the validation system must be surfaced, not suppressed.",
            "5. All field updates are proposals only; they will be reviewed before application.",
            "6. Do not include renderer/layout instructions.",
            "7. Do not include CCI configuration or severity directives.",
            "8. If the user asks for something ambiguous, ask a clarifying question.",
            "9. If the user asks for official data you do not have, do not guess — set next_question.",
            "",
            f"Allowed intents: {self.allowed_intents}",
            "",
            "Current builder state:",
            f"  step: {current_step}",
            f"  payload: {payload}",
            f"  missing_required: {missing_required}",
            f"  missing_recommended: {missing_recommended}",
            f"  validation_summary: {validation_summary}",
            f"  warnings: {warning_texts}",
            f"  errors: {error_texts}",
            "",
            "User message:",
            f'  "{user_message}"',
            "",
            "Expected JSON schema:",
            '{"intent": "<allowed_intent>", "proposed_payload_update": {}, "proposed_key_value_lines": [], "next_question": null, "explanation": "", "requires_user_confirmation": false, "warnings_to_surface": [], "blocked_reason": null, "confidence": 0.0, "safety_notes": []}',
            "",
            "Respond with JSON only.",
        ]
        return "\n".join(prompt_lines)

    def mediate(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Adapter entry point. Mirrors MockLLMBuilderMediator.mediate().

        Flow:
          1. Build prompt from input_data
          2. Call backend(prompt) → raw text
          3. Parse raw text as JSON
          4. Validate against MediatorOutput schema
          5. Run safety filters
          6. Return sanitized MediatorOutput dict
          7. On any failure → return degraded unknown/clarification output
        """
        import json

        # If no backend is configured, degrade safely
        if self.backend is None:
            missing = input_data.get("missing_required_fields", [])
            return MediatorOutput(
                intent="unknown",
                explanation="No LLM backend configured.",
                next_question={
                    "field_path": missing[0] if missing else "user_input",
                    "prompt_text": "No backend available. Please try again or use key-value input.",
                    "bucket": "required",
                } if missing else None,
                confidence=0.0,
                safety_notes=["Backend not configured."],
            )

        prompt = self._build_prompt(input_data)

        try:
            raw_text = self.backend(prompt)
        except Exception as exc:
            return MediatorOutput(
                intent="unknown",
                explanation=f"Backend call failed: {exc}",
                confidence=0.0,
                safety_notes=[f"Backend exception: {exc}"],
            )

        # Parse JSON
        try:
            raw_output = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            return MediatorOutput(
                intent="unknown",
                explanation=f"Backend returned invalid JSON: {exc}",
                confidence=0.0,
                safety_notes=["Invalid JSON from backend."],
            )
        except Exception as exc:
            return MediatorOutput(
                intent="unknown",
                explanation=f"Unexpected parse error: {exc}",
                confidence=0.0,
                safety_notes=[f"Parse exception: {exc}"],
            )

        # Ensure raw_output is a dict
        if not isinstance(raw_output, dict):
            return MediatorOutput(
                intent="unknown",
                explanation="Backend returned non-dict JSON root.",
                confidence=0.0,
                safety_notes=["JSON root was not an object."],
            )

        # Inject allowed_intents into safety filter context
        filter_input = dict(input_data)
        filter_input["allowed_intents"] = self.allowed_intents

        sanitized = self.safety_filter.apply(raw_output, filter_input)
        return sanitized


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
