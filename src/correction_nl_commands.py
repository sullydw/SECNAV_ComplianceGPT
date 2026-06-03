#!/usr/bin/env python3
"""
Phase G Natural-Language Command Mediation

Deterministic-only natural-language mediator that converts plain user input
into canonical structured Phase F slash-command objects.

Scope:
  - Intent detection via regex/phrase dictionaries (no AI/LLM).
  - Field-path inference with clarification for ambiguity.
  - Confirmation gating for persistent/review actions.
  - Review-decision evidence collected through structured follow-up prompts.
  - Output is the canonical structured command schema; execution is delegated
    to Phase F CommandDispatcher.

Safety:
  - No direct persistence writes.
  - No renderer, validator, or rule-catalog imports.
  - No AI-assisted proposals in this first implementation.
  - Persistent actions require confirmation.
  - Low-confidence or ambiguous input triggers clarification.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is importable when running standalone
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

# Phase F dispatcher — used for actual execution after confirmation
from correction_commands import CommandDispatcher

# ---------------------------------------------------------------------------
# Constants — aligned with Phase G plan Sections 11.1–11.3
# ---------------------------------------------------------------------------

_INTENTS = frozenset({
    "correction",
    "undo",
    "remember_session",
    "session_list",
    "session_accept",
    "session_reject",
    "profile_promotion",
    "pending_candidate_log",
    "review_list",
    "review_claim",
    "review_decision",
    "approved_list",
    "status",
    "unsupported",
})

_CONFIDENCE_LEVELS = frozenset({"high", "medium", "low", "unsupported"})

_SAFETY_CLASSES = frozenset({
    "read_only",
    "active_draft",
    "session_persistent",
    "profile_persistent",
    "pending_candidate_persistent",
    "review_status_change",
    "approved_record_creation",
    "unsupported",
})

# Mapping from intent to safety class
_INTENT_SAFETY: dict[str, str] = {
    "correction": "active_draft",
    "undo": "active_draft",
    "remember_session": "session_persistent",
    "session_list": "read_only",
    "session_accept": "session_persistent",
    "session_reject": "session_persistent",
    "profile_promotion": "profile_persistent",
    "pending_candidate_log": "pending_candidate_persistent",
    "review_list": "read_only",
    "review_claim": "review_status_change",
    "review_decision": "approved_record_creation",
    "approved_list": "read_only",
    "status": "read_only",
    "unsupported": "unsupported",
}

# Persistent actions require confirmation
_PERSISTENT_SAFETY = frozenset({
    "session_persistent",
    "profile_persistent",
    "pending_candidate_persistent",
    "review_status_change",
    "approved_record_creation",
})

# Confirmation vocabulary (case-insensitive)
_CONFIRMATION_YES = frozenset({"yes", "y", "confirm"})

# ---------------------------------------------------------------------------
# Field-path phrase mapping (Section 6)
# ---------------------------------------------------------------------------

_FIELD_PHRASES: dict[str, tuple[str, ...]] = {
    "subj": (
        "subject", "subject line", "subj line", "subj",
    ),
    "from": (
        "from line", "sender line", "from",
    ),
    "to": (
        "to line", "recipient line", "to",
    ),
    "via": (
        "via line", "via",
    ),
    "ref": (
        "reference", "references", "ref",
    ),
    "encl": (
        "enclosure", "enclosures", "encl",
    ),
    "body": (
        "body paragraph", "body", "paragraph",
    ),
    "point_of_contact": (
        "point of contact", "poc", "contact",
    ),
    "ssic": (
        "ssic", "standard subject identification code",
    ),
    "originator_code": (
        "originator code", "originator",
    ),
    "signature": (
        "signature block", "signature",
    ),
}

# Repeated fields that need an index to be unambiguous
_INDEXED_FIELDS = frozenset({"via", "ref", "encl", "body"})

# ---------------------------------------------------------------------------
# Intent phrase dictionaries — deterministic keyword matching (Option A/C)
# ---------------------------------------------------------------------------

_INTENT_PHRASES: dict[str, tuple[str, ...]] = {
    "correction": (
        "change", "fix", "set", "update", "correct", "correction", "make", "edit",
        "switch", "replace", "adjust",
    ),
    "undo": (
        "undo", "revert", "back out", "roll back", "reverse",
    ),
    "remember_session": (
        "remember", "save", "store", "persist", "keep",
        "remember for this session", "save for this session",
        "remember that for this session", "save that for this session",
    ),
    "session_list": (
        "show session", "list session", "session corrections",
        "what was reused", "what corrections",
        "show me what was reused", "show me session corrections",
        "show session corrections", "list session corrections",
    ),
    "session_accept": (
        "accept", "approve correction", "confirm correction", "yes to correction",
        "accept that", "accept this", "accept correction", "accept the correction",
        "accept that correction", "accept this correction",
        "accept session correction", "accept the session correction",
    ),
    "session_reject": (
        "reject", "discard", "ignore correction", "no to correction",
        "reject that", "reject this", "reject correction", "reject the correction",
        "reject that correction", "reject this correction",
        "reject session correction", "reject the session correction",
    ),
    "profile_promotion": (
        "promote", "command preference", "local preference", "profile",
        "make this my command standard", "make this a command preference",
        "promote to profile", "promote this",
    ),
    "pending_candidate_log": (
        "log candidate", "log this", "flag as rule", "flag this",
        "possible manual rule", "possible secnav rule", "global rule candidate",
        "this should be a secnav rule", "global rule",
        "log this as a rule", "flag this as a rule",
    ),
    "review_list": (
        "review pending", "pending candidates", "candidates for review",
        "show pending", "list pending",
        "show pending candidates", "list pending candidates",
    ),
    "review_claim": (
        "claim", "take candidate", "review this candidate",
        "claim that", "claim this", "claim candidate",
    ),
    "review_decision": (
        "decide", "approve candidate", "reject candidate", "defer candidate",
        "supersede candidate", "approve", "reject", "defer", "supersede",
        "approve this candidate", "reject this candidate",
        "defer this candidate", "supersede this candidate",
        "approve that candidate", "reject that candidate",
        "defer that candidate", "supersede that candidate",
    ),
    "approved_list": (
        "approved rules", "show approved", "list approved",
        "approved rule", "approved promotion",
        "show approved rules", "list approved rules",
    ),
    "status": (
        "status", "what corrections", "active corrections", "current state",
        "active", "current corrections", "what is the status",
        "what is active", "show active corrections",
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _has_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(p.lower() in lowered for p in phrases)


def _extract_quoted_value(text: str) -> str | None:
    """Extract a double-quoted or single-quoted substring."""
    m = re.search(r'["\'](.+?)["\']', text)
    if m:
        return m.group(1)
    return None


def _extract_field_path(text: str) -> str | None:
    """Map natural-language field phrase to canonical field path."""
    lowered = text.lower()
    for field, phrases in _FIELD_PHRASES.items():
        for phrase in phrases:
            if phrase in lowered:
                # For indexed fields, require explicit index if phrase is generic
                if field in _INDEXED_FIELDS:
                    # Try to find an explicit number after the phrase
                    # e.g., "change the 2nd body paragraph" or "body paragraph 2"
                    idx_match = re.search(
                        rf"{re.escape(phrase)}\s*(\d+)|(\d+)(?:st|nd|rd|th)?\s*{re.escape(phrase)}",
                        lowered,
                    )
                    if idx_match:
                        num = idx_match.group(1) or idx_match.group(2)
                        return f"{field}[{int(num) - 1}]"  # 0-based index
                    # If no index found, return the base field so caller knows to clarify
                    return field  # ambiguous — needs index
                return field
    return None


def _extract_corrected_value(text: str, field_phrase_used: str | None) -> str | None:
    """Heuristic: extract value after field phrase, or from quotes."""
    quoted = _extract_quoted_value(text)
    if quoted:
        return quoted

    # Try to capture everything after "to" or "as" following the field phrase
    if field_phrase_used:
        pattern = rf"(?:change|fix|set|update|correct|make|edit|switch|replace|adjust)\s+(?:the\s+)?{re.escape(field_phrase_used)}\s+(?:to|as|into|with|be)\s+(.+)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Strip trailing punctuation that isn't part of the value
            val = re.sub(r"[.!?]$", "", val).strip()
            return val

    # Fallback: grab quoted or everything after last "to"
    parts = text.split(" to ")
    if len(parts) >= 2:
        return parts[-1].strip().strip("\"'").strip()

    return None


def _is_confirmed(text: str) -> bool:
    return text.strip().lower() in _CONFIRMATION_YES


def _is_rejection_response(text: str) -> bool:
    return text.strip().lower() in {"no", "n", "cancel", "abort"}


def _build_structured_command(
    raw_input: str,
    intent: str,
    command_name: str | None = None,
    arguments: dict[str, Any] | None = None,
    target: dict[str, Any] | None = None,
    confidence: str = "low",
    requires_confirmation: bool = False,
    requires_clarification: bool = False,
    clarification_prompt: str | None = None,
    blocked_reason: str | None = None,
    safety_notes: list[str] | None = None,
    slash_command: str | None = None,
) -> dict[str, Any]:
    """Build the canonical structured command object per Phase G Section 5."""
    safety_class = _INTENT_SAFETY.get(intent, "unsupported")
    persistent = safety_class in _PERSISTENT_SAFETY
    return {
        "raw_input": raw_input,
        "intent": intent,
        "command_name": command_name,
        "slash_command": slash_command,
        "arguments": arguments or {},
        "target": target or {"correction_id": None, "candidate_id": None, "source": "active_draft"},
        "confidence": confidence,
        "requires_confirmation": requires_confirmation or persistent,
        "requires_clarification": requires_clarification,
        "clarification_prompt": clarification_prompt,
        "safety_class": safety_class,
        "persistent_action": persistent,
        "blocked_reason": blocked_reason,
        "safety_notes": safety_notes or [],
    }


def _build_slash_command(cmd_name: str, args: dict[str, Any]) -> str | None:
    """Render a slash-command string from a command name + arguments."""
    if not cmd_name:
        return None

    # Correction: /correct <field> <value>
    if cmd_name == "correct":
        fp = args.get("field_path")
        val = args.get("corrected_value")
        if fp and val is not None:
            # Quote value if it contains spaces
            if " " in str(val):
                return f'/correct {fp} "{val}"'
            return f"/correct {fp} {val}"
        return None

    # Undo
    if cmd_name == "undo":
        return "/undo"

    # Remember session
    if cmd_name == "remember" and args.get("scope") == "session":
        return "/remember session"

    # Session corrections
    if cmd_name == "session" and args.get("scope") == "corrections":
        return "/session corrections"

    # Accept / reject
    if cmd_name in ("accept", "reject"):
        cid = args.get("correction_id")
        if cid:
            return f"/{cmd_name} {cid}"
        return None

    # Promote profile
    if cmd_name == "promote" and args.get("scope") == "profile":
        return "/promote profile"

    # Log candidate
    if cmd_name == "log" and args.get("scope") == "candidate":
        return "/log candidate"

    # Review pending
    if cmd_name == "review" and args.get("scope") == "pending":
        return "/review pending"

    # Claim
    if cmd_name == "claim":
        cid = args.get("candidate_id")
        if cid:
            return f"/claim {cid}"
        return None

    # Decide
    if cmd_name == "decide":
        cid = args.get("candidate_id")
        decision = args.get("decision")
        if cid and decision:
            parts = [f"/decide {cid} {decision}"]
            if args.get("rationale"):
                parts.append(f"--rationale {args['rationale']}")
            if args.get("evidence"):
                parts.append(f"--evidence {args['evidence']}")
            return " ".join(parts)
        return None

    # Approved rules
    if cmd_name == "approved" and args.get("scope") == "rules":
        return "/approved rules"

    # Status
    if cmd_name == "status":
        return "/status"

    return None


# ---------------------------------------------------------------------------
# Mediator class
# ---------------------------------------------------------------------------

class NLCommandMediator:
    """
    Deterministic natural-language command mediator.

    Usage:
        mediator = NLCommandMediator(dispatcher)
        result = mediator.mediate("Change the subject to POLICY UPDATE")
        # result is a structured command dict; execute via dispatcher if confirmed.
    """

    def __init__(self, dispatcher: CommandDispatcher):
        self._dispatcher = dispatcher
        self._pending_confirmation: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def mediate(
        self,
        user_input: str,
        confirmed: bool = False,
        correction_id: str | None = None,
        candidate_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Convert natural-language input into a structured Phase F command.

        Parameters:
            user_input: raw natural-language text.
            confirmed: if True, skip confirmation prompt for persistent actions.
            correction_id: explicit correction ID when available.
            candidate_id: explicit candidate ID when available.
            evidence: structured evidence dict for review decisions.

        Returns:
            Canonical structured command dict.
        """
        raw = user_input.strip()
        if not raw:
            return _build_structured_command(
                raw, "unsupported", confidence="unsupported",
                blocked_reason="Empty input.",
            )

        # If there is a pending confirmation and user replies with yes/no, handle it
        pending = self._pending_confirmation
        if pending is not None:
            if _is_confirmed(raw):
                self._pending_confirmation = None
                # Return the pending command with confirmed semantics
                pending["requires_confirmation"] = False
                pending["user_confirmed"] = True
                return pending
            if _is_rejection_response(raw):
                self._pending_confirmation = None
                return _build_structured_command(
                    raw, "unsupported", confidence="unsupported",
                    blocked_reason="User cancelled pending confirmation.",
                )

        # Detect intent
        intent, confidence, reason = self._detect_intent(raw)

        if intent == "unsupported":
            return _build_structured_command(
                raw, "unsupported", confidence="unsupported",
                blocked_reason=reason or "Unsupported intent.",
            )

        # Route to handler
        handler = getattr(self, f"_handle_{intent}", None)
        if handler is None:
            return _build_structured_command(
                raw, "unsupported", confidence="unsupported",
                blocked_reason=f"No handler for intent '{intent}'.",
            )

        return handler(raw, confidence, confirmed, correction_id, candidate_id, evidence)

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(self, text: str) -> tuple[str, str, str | None]:
        """Return (intent, confidence, reason)."""
        lowered = text.lower()

        scores: dict[str, int] = {}
        for intent, phrases in _INTENT_PHRASES.items():
            for phrase in phrases:
                if phrase in lowered:
                    scores[intent] = scores.get(intent, 0) + 1

        if not scores:
            return ("unsupported", "unsupported", "No recognized intent phrases.")

        # Pick highest score
        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]

        # Tie-break: if multiple intents tie, prefer more specific intents over generic correction.
        tied = [k for k, v in scores.items() if v == best_score]
        if len(tied) > 1:
            preference_order = [
                "undo", "remember_session", "session_list",
                "session_accept", "session_reject",
                "profile_promotion", "pending_candidate_log",
                "review_list", "review_claim", "review_decision",
                "approved_list", "status", "correction",
            ]
            for preferred in preference_order:
                if preferred in tied:
                    best_intent = preferred
                    break

        # Candidate context override: if the text mentions "candidate" and the winner
        # is a session accept/reject, prefer review_decision when it is also tied.
        if "candidate" in lowered and best_intent in ("session_accept", "session_reject") and "review_decision" in scores:
            best_intent = "review_decision"

        # Confidence heuristics
        if best_score >= 2:
            confidence = "high"
        elif best_score == 1:
            # Single match is medium unless the phrase is very specific
            specific_phrases = {
                "undo", "revert", "review pending", "approved rules",
                "status", "log candidate", "promote profile",
                "session corrections", "remember session",
            }
            if any(p in lowered for p in specific_phrases):
                confidence = "high"
            else:
                confidence = "medium"
        else:
            confidence = "low"

        return (best_intent, confidence, None)

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------

    def _handle_correction(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        field_path = _extract_field_path(raw)

        if field_path is None:
            return _build_structured_command(
                raw, "correction", command_name="correct",
                confidence="low", requires_clarification=True,
                clarification_prompt="Which field do you want to correct? (e.g., subject, From line, body paragraph 2)",
            )

        # If field is indexed but no index extracted, clarify
        if field_path in _INDEXED_FIELDS:
            return _build_structured_command(
                raw, "correction", command_name="correct",
                confidence="low", requires_clarification=True,
                clarification_prompt=f"Which {field_path} do you want to change? Use a number, such as {field_path} 1 or {field_path} 2.",
            )

        corrected_value = _extract_corrected_value(raw, field_path)
        if corrected_value is None:
            return _build_structured_command(
                raw, "correction", command_name="correct",
                arguments={"field_path": field_path},
                confidence="low", requires_clarification=True,
                clarification_prompt=f"What should the new value for '{field_path}' be?",
            )

        args = {"field_path": field_path, "corrected_value": corrected_value}
        slash = _build_slash_command("correct", args)
        return _build_structured_command(
            raw, "correction", command_name="correct",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    def _handle_undo(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        slash = _build_slash_command("undo", {})
        return _build_structured_command(
            raw, "undo", command_name="undo",
            arguments={}, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    def _handle_remember_session(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        args = {"scope": "session"}
        slash = _build_slash_command("remember", args)
        cmd = _build_structured_command(
            raw, "remember_session", command_name="remember",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
            target={"correction_id": correction_id, "candidate_id": None, "source": "current_session"},
        )
        if not confirmed:
            self._pending_confirmation = cmd
            cmd["clarification_prompt"] = (
                "I interpreted your request as:\n\n/remember session\n\n"
                "This will persist the most recent correction to the session store. Confirm? yes/no"
            )
        return cmd

    def _handle_session_list(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        args = {"scope": "corrections"}
        slash = _build_slash_command("session", args)
        return _build_structured_command(
            raw, "session_list", command_name="session",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    def _handle_session_accept(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not correction_id:
            return _build_structured_command(
                raw, "session_accept", command_name="accept",
                confidence="low", requires_clarification=True,
                clarification_prompt="Which session correction do you want to accept? Provide the correction ID.",
            )
        args = {"correction_id": correction_id}
        slash = _build_slash_command("accept", args)
        return _build_structured_command(
            raw, "session_accept", command_name="accept",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
        )

    def _handle_session_reject(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not correction_id:
            return _build_structured_command(
                raw, "session_reject", command_name="reject",
                confidence="low", requires_clarification=True,
                clarification_prompt="Which session correction do you want to reject? Provide the correction ID.",
            )
        args = {"correction_id": correction_id}
        slash = _build_slash_command("reject", args)
        return _build_structured_command(
            raw, "session_reject", command_name="reject",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
        )

    def _handle_profile_promotion(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        # Must target the most recent correction or a current-session correction
        last = self._dispatcher._get_last_correction()
        if last is None and not correction_id:
            return _build_structured_command(
                raw, "profile_promotion", command_name="promote",
                confidence="low", requires_clarification=True,
                clarification_prompt="No recent correction found. Apply a correction first, then ask to promote it.",
            )
        args = {"scope": "profile"}
        slash = _build_slash_command("promote", args)
        target = {
            "correction_id": correction_id or last.get("correction_id") if last else None,
            "candidate_id": None,
            "source": "active_draft" if last else "current_session",
        }
        cmd = _build_structured_command(
            raw, "profile_promotion", command_name="promote",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
            target=target,
            safety_notes=["Phase C two-step confirmation required after dispatch."],
        )
        if not confirmed:
            self._pending_confirmation = cmd
            cmd["clarification_prompt"] = (
                "I interpreted your request as:\n\n/promote profile\n\n"
                "This will start the Phase C local profile promotion workflow for the most recent correction. "
                "It will not write to your profile until the Phase C two-step confirmation completes.\n\n"
                "Confirm? yes/no"
            )
        return cmd

    def _handle_pending_candidate_log(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        last = self._dispatcher._get_last_correction()
        if last is None and not correction_id:
            return _build_structured_command(
                raw, "pending_candidate_log", command_name="log",
                confidence="low", requires_clarification=True,
                clarification_prompt="No recent correction found. Apply a correction first, then ask to log it.",
            )
        args = {"scope": "candidate"}
        slash = _build_slash_command("log", args)
        target = {
            "correction_id": correction_id or (last.get("correction_id") if last else None),
            "candidate_id": None,
            "source": "active_draft" if last else "current_session",
        }
        cmd = _build_structured_command(
            raw, "pending_candidate_log", command_name="log",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
            target=target,
            safety_notes=["Phase D sanitization and explicit approval required after dispatch."],
        )
        if not confirmed:
            self._pending_confirmation = cmd
            cmd["clarification_prompt"] = (
                "I interpreted your request as:\n\n/log candidate\n\n"
                "This will log the most recent correction as a pending global rule candidate. "
                "It will not enforce a global rule. Confirm? yes/no"
            )
        return cmd

    def _handle_review_list(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        args = {"scope": "pending"}
        slash = _build_slash_command("review", args)
        return _build_structured_command(
            raw, "review_list", command_name="review",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    def _handle_review_claim(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not candidate_id:
            return _build_structured_command(
                raw, "review_claim", command_name="claim",
                confidence="low", requires_clarification=True,
                clarification_prompt="Which candidate do you want to claim? Provide the candidate ID.",
            )
        args = {"candidate_id": candidate_id}
        slash = _build_slash_command("claim", args)
        return _build_structured_command(
            raw, "review_claim", command_name="claim",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
        )

    def _handle_review_decision(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not candidate_id:
            return _build_structured_command(
                raw, "review_decision", command_name="decide",
                confidence="low", requires_clarification=True,
                clarification_prompt="Which candidate do you want to decide on? Provide the candidate ID.",
            )

        # Determine decision from text
        decision = self._infer_decision(raw)
        if not decision:
            return _build_structured_command(
                raw, "review_decision", command_name="decide",
                arguments={"candidate_id": candidate_id},
                confidence="low", requires_clarification=True,
                clarification_prompt="What decision do you want to make? (approve, reject, defer, supersede)",
            )

        # For approve, require structured evidence through follow-up prompts
        if decision == "approve":
            # Validate evidence is present
            if not evidence:
                return _build_structured_command(
                    raw, "review_decision", command_name="decide",
                    arguments={"candidate_id": candidate_id, "decision": decision},
                    confidence="medium", requires_clarification=True,
                    clarification_prompt=(
                        "Review evidence is required before approving.\n"
                        "For a manual rule, provide secnav_citation (chapter/paragraph/figure/quote).\n"
                        "For a validator gap, provide validator_evidence (validator_name, expected_behavior, actual_behavior)."
                    ),
                )

            # Validate evidence has required fields
            if "secnav_citation" in evidence and not evidence["secnav_citation"]:
                return _build_structured_command(
                    raw, "review_decision", command_name="decide",
                    arguments={"candidate_id": candidate_id, "decision": decision},
                    confidence="medium", requires_clarification=True,
                    clarification_prompt="Manual-rule approval requires a secnav_citation. Provide chapter, paragraph, figure, or quote.",
                )
            if "validator_evidence" in evidence and not evidence["validator_evidence"]:
                return _build_structured_command(
                    raw, "review_decision", command_name="decide",
                    arguments={"candidate_id": candidate_id, "decision": decision},
                    confidence="medium", requires_clarification=True,
                    clarification_prompt="Validator-gap approval requires validator_evidence. Provide validator_name, expected_behavior, and actual_behavior.",
                )

        args = {
            "candidate_id": candidate_id,
            "decision": decision,
            "rationale": evidence.get("rationale", "") if evidence else "",
            "evidence": evidence.get("secnav_citation", evidence.get("validator_evidence", "")) if evidence else "",
        }
        slash = _build_slash_command("decide", args)
        return _build_structured_command(
            raw, "review_decision", command_name="decide",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=True,
            safety_notes=["Phase E evidence validation required after dispatch. Approved records remain pending_implementation."],
        )

    def _handle_approved_list(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        args = {"scope": "rules"}
        slash = _build_slash_command("approved", args)
        return _build_structured_command(
            raw, "approved_list", command_name="approved",
            arguments=args, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    def _handle_status(
        self,
        raw: str,
        confidence: str,
        confirmed: bool,
        correction_id: str | None,
        candidate_id: str | None,
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any]:
        slash = _build_slash_command("status", {})
        return _build_structured_command(
            raw, "status", command_name="status",
            arguments={}, slash_command=slash,
            confidence=confidence, requires_confirmation=False,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _infer_decision(self, text: str) -> str | None:
        lowered = text.lower()
        if "approve" in lowered:
            return "approve"
        if "reject" in lowered:
            return "reject"
        if "defer" in lowered:
            return "defer"
        if "supersede" in lowered:
            return "supersede"
        return None

    # ------------------------------------------------------------------
    # Execution bridge (convenience)
    # ------------------------------------------------------------------

    def execute_if_ready(self, cmd: dict[str, Any]) -> dict[str, Any]:
        """
        If the structured command is unambiguous and confirmed, dispatch via
        the Phase F CommandDispatcher and return its result.
        """
        if cmd.get("requires_clarification"):
            return {
                "success": False,
                "message": cmd.get("clarification_prompt") or "Clarification required.",
                "data": {"command": cmd},
            }

        if cmd.get("requires_confirmation") and not cmd.get("user_confirmed"):
            return {
                "success": False,
                "message": cmd.get("clarification_prompt") or "Confirmation required.",
                "data": {"command": cmd, "requires_confirmation": True},
            }

        slash = cmd.get("slash_command")
        if not slash:
            return {
                "success": False,
                "message": "No slash command could be built from the structured command.",
                "data": {"command": cmd},
            }

        # Dispatch through Phase F
        return self._dispatcher.dispatch(slash, confirmed=True)


# ---------------------------------------------------------------------------
# Standalone CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Minimal CLI for testing the NL mediator."""
    if argv is None:
        argv = sys.argv[1:]

    payload = {
        "subj": "TEST SUBJECT.",
        "from": "Commanding Officer, USS EXAMPLE",
        "body": ["Paragraph one.", "Paragraph two."],
    }

    from intake_orchestrator import IntakeOrchestrator
    orch = IntakeOrchestrator(payload=payload, session_id="demo_session")
    dispatcher = CommandDispatcher(orch)
    mediator = NLCommandMediator(dispatcher)

    if not argv:
        print("Usage: python -m correction_nl_commands <natural-language request>")
        print('Example: python -m correction_nl_commands "Change the subject to POLICY UPDATE"')
        return 1

    user_input = " ".join(argv)
    result = mediator.mediate(user_input)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
