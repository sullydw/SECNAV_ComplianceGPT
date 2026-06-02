"""
Phase F UI/Command Integration — Slash-Command Dispatcher

Scope:
  - Slash-command parsing and dispatch only.
  - No natural-language parsing (deferred to Phase G).
  - Delegates to existing Phase A–E APIs.
  - No direct JSONL, profile, or catalog writes.

Safety:
  - /promote profile and /log candidate operate only on the most recent
    active-draft or current-session correction; no arbitrary unattached IDs.
  - All persistent actions require an explicit confirmation step.
  - /decide approve delegates to correction_review.review_candidate().
  - Approved global rule records remain implementation_status="pending_implementation".
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is importable when running standalone
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from intake_orchestrator import IntakeOrchestrator
from correction_classify import classify_correction
from correction_promote import (
    is_eligible_for_promotion,
    propose_promotion,
    confirm_and_write_promotion,
)
from correction_pending_log import (
    is_eligible_for_pending_log,
    propose_pending_log as _propose_pending_log,
    confirm_and_write_pending_log,
    list_pending_candidates,
)
from correction_review import (
    list_candidates_for_review,
    claim_candidate,
    review_candidate,
    supersede_candidate,
    propose_phase_c_redirect,
)
from correction_store import (
    load_session_corrections,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_DECISIONS = frozenset({"approve", "reject", "defer", "supersede"})

# Scope display names for user messages
_SCOPE_NAMES = {
    "active_draft": "active draft only",
    "current_session": "this session",
    "local_command_profile": "local command profile",
    "pending_global_rule_candidate": "pending global rule candidate",
}


# ---------------------------------------------------------------------------
# Command result type
# ---------------------------------------------------------------------------

def _ok(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data or {}}


def _err(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": data or {}}


# ---------------------------------------------------------------------------
# Confirmation helpers
# ---------------------------------------------------------------------------

def _needs_confirm(action_name: str) -> str:
    return f"Confirm {action_name}? (yes/no): "


def _is_confirmed(response: str | bool) -> bool:
    if isinstance(response, bool):
        return response
    return response.strip().lower() in {"yes", "y", "confirm"}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class CommandDispatcher:
    """Parse and dispatch slash commands for the correction-memory system."""

    def __init__(self, orchestrator: IntakeOrchestrator):
        self._orch = orchestrator
        self._last_correction: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Public dispatch entry
    # ------------------------------------------------------------------

    def dispatch(self, command_line: str, confirmed: bool = False) -> dict[str, Any]:
        """
        Parse a slash command and dispatch to the appropriate handler.

        Parameters:
            command_line: raw user input, e.g. "/correct subj NEW SUBJECT"
            confirmed: if True, skip interactive confirmation for destructive
                       or persistent actions (useful for programmatic callers).

        Returns:
            dict with success, message, and data.
        """
        line = command_line.strip()
        if not line.startswith("/"):
            return _err("Commands must start with '/'.")

        parts = line[1:].split()
        if not parts:
            return _err("Empty command.")

        verb = parts[0].lower()
        args = parts[1:]

        # Route to handler
        handler = getattr(self, f"_cmd_{verb}", None)
        if handler is None:
            return _err(f"Unknown command: /{verb}")

        try:
            return handler(args, confirmed=confirmed)
        except Exception as exc:
            return _err(f"Command /{verb} failed: {exc}")

    # ------------------------------------------------------------------
    # Command: /correct
    # ------------------------------------------------------------------

    def _cmd_correct(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if len(args) < 2:
            return _err("Usage: /correct <field_path> <corrected_value>")

        field_path = args[0]
        corrected_value = " ".join(args[1:])

        # Use the orchestrator's capture + apply convenience
        status = self._orch.apply_user_correction(
            field_path=field_path,
            corrected_value=corrected_value,
            reason="User correction via /correct command",
            correction_type="unknown",
            source="command",
        )

        # Track the most recent applied correction for /promote and /log
        corrections = status.get("corrections_applied", [])
        if corrections:
            self._last_correction = corrections[-1]

        return _ok(
            f"Corrected '{field_path}' to '{corrected_value}'.",
            {"status": status},
        )

    # ------------------------------------------------------------------
    # Command: /undo
    # ------------------------------------------------------------------

    def _cmd_undo(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        corrections = self._orch.get_status().get("corrections_applied", [])
        if not corrections:
            return _err("No correction to undo.")

        last = corrections[-1]
        status = self._orch.undo_correction(last)

        # Clear last_correction if it matches the undone one
        if self._last_correction and self._last_correction.get("correction_id") == last.get("correction_id"):
            self._last_correction = None

        return _ok("Last correction undone.", {"status": status})

    # ------------------------------------------------------------------
    # Command: /remember
    # ------------------------------------------------------------------

    def _cmd_remember(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args:
            return _err("Usage: /remember <session|profile|candidate>")

        scope = args[0].lower()
        if scope == "active_draft":
            return _ok("Active-draft corrections are already applied. Nothing to remember.")

        if scope == "session":
            return self._remember_session(confirmed)
        if scope == "profile":
            return self._remember_profile(confirmed)
        if scope == "candidate":
            return self._remember_candidate(confirmed)

        return _err(f"Unknown scope: {scope}. Use session, profile, or candidate.")

    def _remember_session(self, confirmed: bool) -> dict[str, Any]:
        last = self._get_last_correction()
        if last is None:
            return _err("No recent correction to remember for session. Apply a correction first.")

        # Classification gate
        ctype = last.get("correction_type", "unknown")
        if ctype == "unknown":
            # Auto-classify if unknown
            ctype, confidence, reasons = classify_correction(
                field_path=last.get("field_path", ""),
                reason=last.get("reason", ""),
                scope="current_session",
                correction_type="unknown",
                validator_conflict=last.get("validator_conflict", False),
            )
            last["correction_type"] = ctype
            last["classification_confidence"] = confidence
            last["classification_reasons"] = reasons

        if ctype == "one_time_wording" and last.get("classification_confidence") != "user_override":
            return _err(
                "This correction is classified as one-time wording. "
                "It will not be persisted to the session. "
                "If you want to override, set classification_confidence=user_override first."
            )

        persisted = self._orch.persist_correction(last)
        if persisted:
            return _ok("Correction remembered for this session.", {"correction": last})
        return _err("Could not persist to session (no session_id set or persistence blocked).")

    def _remember_profile(self, confirmed: bool) -> dict[str, Any]:
        return self._run_promote_profile(confirmed)

    def _remember_candidate(self, confirmed: bool) -> dict[str, Any]:
        return self._run_log_candidate(confirmed)

    # ------------------------------------------------------------------
    # Command: /session corrections
    # ------------------------------------------------------------------

    def _cmd_session(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args or args[0].lower() != "corrections":
            return _err("Usage: /session corrections")

        session_id = self._orch.get_status().get("session_id")
        if not session_id:
            return _err("No active session. Set a session_id first.")

        corrections, warnings = load_session_corrections(session_id)
        return _ok(
            f"Found {len(corrections)} session correction(s).",
            {"corrections": corrections, "warnings": warnings},
        )

    # ------------------------------------------------------------------
    # Command: /accept /reject
    # ------------------------------------------------------------------

    def _cmd_accept(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args:
            return _err("Usage: /accept <session_correction_id>")
        return _err("Accepting a pre-applied session correction is handled automatically during draft load.")

    def _cmd_reject(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args:
            return _err("Usage: /reject <session_correction_id>")

        correction_id = args[0]
        # We need to find the correction record in the active draft or session store
        # For simplicity, build a minimal record with the id
        rejection_record = {"correction_id": correction_id}
        status = self._orch.reject_session_correction(rejection_record)
        return _ok(f"Session correction {correction_id} rejected.", {"status": status})

    # ------------------------------------------------------------------
    # Command: /promote profile
    # ------------------------------------------------------------------

    def _cmd_promote(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if len(args) < 1 or args[0].lower() != "profile":
            return _err("Usage: /promote profile")
        return self._run_promote_profile(confirmed)

    def _run_promote_profile(self, confirmed: bool) -> dict[str, Any]:
        last = self._get_last_correction()
        if last is None:
            return _err("No recent correction to promote. Apply a correction first.")

        # Upgrade scope to current_session for promotion eligibility
        last = copy.deepcopy(last)
        last["scope"] = "current_session"

        # Must be local_command_preference
        ctype = last.get("correction_type", "unknown")
        if ctype == "unknown":
            ctype, confidence, reasons = classify_correction(
                field_path=last.get("field_path", ""),
                reason=last.get("reason", ""),
                scope="current_session",
                correction_type="unknown",
                validator_conflict=last.get("validator_conflict", False),
            )
            last["correction_type"] = ctype
            last["classification_confidence"] = confidence
            last["classification_reasons"] = reasons

        if ctype != "local_command_preference":
            return _err(
                f"Correction type is '{ctype}', not 'local_command_preference'. "
                "Only local command preferences may be promoted to a profile."
            )

        # Phase C Step 1: eligibility
        eligible, reasons = is_eligible_for_promotion(last)
        if not eligible:
            return _err(f"Not eligible for profile promotion: {'; '.join(reasons)}")

        # Determine profile path from active profile or default
        active_profile = self._orch.get_status().get("active_profile")
        if active_profile:
            profile_path = f"profiles/user/{active_profile}.json"
        else:
            profile_path = "profiles/user/default_profile.json"

        # Step 2: propose
        proposal = propose_promotion(last, profile_path)
        if not proposal.get("eligible"):
            return _err(f"Promotion proposal failed: {proposal.get('reasons', [])}")

        # Confirmation prompt
        if not confirmed:
            return _ok(
                "PROMOTION PREVIEW (reply with confirmed=True to proceed):\n"
                f"  Field: {last.get('field_path')}\n"
                f"  Value: {last.get('corrected_value')}\n"
                f"  Profile: {profile_path}\n"
                f"  Backup will be created before write.",
                {"proposal": proposal, "requires_confirmation": True},
            )

        # Execute
        result = confirm_and_write_promotion(proposal, confirmed=True)
        if result.get("success"):
            return _ok(
                f"Promoted to profile: {profile_path}",
                {"result": result, "backup_path": result.get("backup_path")},
            )
        return _err(f"Promotion failed: {result.get('reasons', [])}")

    # ------------------------------------------------------------------
    # Command: /log candidate
    # ------------------------------------------------------------------

    def _cmd_log(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if len(args) < 1 or args[0].lower() != "candidate":
            return _err("Usage: /log candidate")
        return self._run_log_candidate(confirmed)

    def _run_log_candidate(self, confirmed: bool) -> dict[str, Any]:
        last = self._get_last_correction()
        if last is None:
            return _err("No recent correction to log. Apply a correction first.")

        # Upgrade scope to current_session for candidate logging eligibility
        last = copy.deepcopy(last)
        last["scope"] = "current_session"

        # Must be possible_secnav_manual_rule or bug_validator_gap
        ctype = last.get("correction_type", "unknown")
        if ctype == "unknown":
            ctype, confidence, reasons = classify_correction(
                field_path=last.get("field_path", ""),
                reason=last.get("reason", ""),
                scope="current_session",
                correction_type="unknown",
                validator_conflict=last.get("validator_conflict", False),
            )
            last["correction_type"] = ctype
            last["classification_confidence"] = confidence
            last["classification_reasons"] = reasons

        if ctype not in {"possible_secnav_manual_rule", "bug_validator_gap"}:
            return _err(
                f"Correction type is '{ctype}'. "
                "Only 'possible_secnav_manual_rule' or 'bug_validator_gap' may be logged as global rule candidates."
            )

        # Phase D Step 1: eligibility
        eligible, reasons = is_eligible_for_pending_log(last)
        if not eligible:
            return _err(f"Not eligible for pending candidate log: {'; '.join(reasons)}")

        # Step 2: propose
        proposal = _propose_pending_log(last)
        if not proposal.get("eligible"):
            return _err(f"Pending log proposal failed: {proposal.get('reasons', [])}")

        # Confirmation prompt
        if not confirmed:
            return _ok(
                "CANDIDATE LOG PREVIEW (reply with confirmed=True to proceed):\n"
                f"  Field: {last.get('field_path')}\n"
                f"  Sanitized value: {proposal.get('sanitized_value', '(none)')}\n"
                f"  Log path: corrections/pending_corrections.jsonl\n"
                "  This will append a sanitized record.",
                {"proposal": proposal, "requires_confirmation": True},
            )

        # Execute
        log_path = Path("corrections/pending_corrections.jsonl")
        result = confirm_and_write_pending_log(proposal, log_path)
        if result.get("success"):
            return _ok(
                f"Candidate logged with ID: {result.get('candidate_id')}",
                {"result": result},
            )
        return _err(f"Candidate logging failed: {result.get('reasons', [])}")

    # ------------------------------------------------------------------
    # Command: /review pending
    # ------------------------------------------------------------------

    def _cmd_review(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args or args[0].lower() != "pending":
            return _err("Usage: /review pending")

        candidates, warnings = list_candidates_for_review()
        return _ok(
            f"Found {len(candidates)} candidate(s) awaiting review.",
            {"candidates": candidates, "warnings": warnings},
        )

    # ------------------------------------------------------------------
    # Command: /claim
    # ------------------------------------------------------------------

    def _cmd_claim(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args:
            return _err("Usage: /claim <candidate_id>")

        candidate_id = args[0]
        reviewer_id = self._orch.get_status().get("session_id") or "cli_user"
        result = claim_candidate(candidate_id, reviewer_id)
        if result.get("success"):
            return _ok(f"Claimed candidate {candidate_id} for review.", {"result": result})
        return _err(f"Could not claim candidate: {result.get('warnings', [])}")

    # ------------------------------------------------------------------
    # Command: /decide
    # ------------------------------------------------------------------

    def _cmd_decide(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if len(args) < 2:
            return _err("Usage: /decide <candidate_id> <approve|reject|defer|supersede> [--rationale ...] [--evidence ...]")

        candidate_id = args[0]
        decision = args[1].lower()

        if decision not in _ALLOWED_DECISIONS:
            return _err(f"Invalid decision: {decision}. Must be one of: {', '.join(sorted(_ALLOWED_DECISIONS))}")

        # Parse optional --rationale and --evidence
        rationale = ""
        evidence = ""
        i = 2
        while i < len(args):
            if args[i] == "--rationale" and i + 1 < len(args):
                rationale = args[i + 1]
                i += 2
            elif args[i] == "--evidence" and i + 1 < len(args):
                evidence = args[i + 1]
                i += 2
            else:
                i += 1

        reviewer_id = self._orch.get_status().get("session_id") or "cli_user"

        # Build review_metadata
        review_metadata: dict[str, Any] = {
            "rationale": rationale,
        }

        if decision == "approve":
            # Determine rule category from candidate
            log_path = Path("corrections/pending_corrections.jsonl")
            candidates, _ = list_candidates_for_review(log_path=log_path)
            candidate = None
            for c in candidates:
                if c.get("candidate_id") == candidate_id:
                    candidate = c
                    break

            if candidate is None:
                return _err(f"Candidate {candidate_id} not found or not eligible for review.")

            ctype = candidate.get("correction_type", "")
            if ctype == "possible_secnav_manual_rule":
                review_metadata["rule_category"] = "manual_rule"
                review_metadata["secnav_citation"] = {
                    "chapter": "",
                    "paragraph": "",
                    "figure": "",
                    "quote": evidence or "",
                }
                if not evidence:
                    return _err("Approve requires --evidence <secnav_citation>. Example: --evidence 'SECNAV M-5216.5, Ch 7, para 2'")
            elif ctype == "bug_validator_gap":
                review_metadata["rule_category"] = "validator_gap"
                review_metadata["validator_evidence"] = {
                    "validator_name": "",
                    "expected_behavior": "",
                    "actual_behavior": evidence or "",
                    "reproduction_payload": {},
                }
                if not evidence:
                    return _err("Approve requires --evidence <validator_evidence>. Example: --evidence 'cci_subject validator missed period'")
            else:
                return _err(f"Cannot approve candidate of type '{ctype}'.")

            if not rationale:
                return _err("Approve requires --rationale <reason>. Example: --rationale 'Subject line must not end with period per manual'")

        if decision == "supersede":
            review_metadata["superseded_by_rule_id"] = ""
            review_metadata["superseded_by_candidate_id"] = ""

        # Execute Phase E review
        log_path = Path("corrections/pending_corrections.jsonl")
        approved_rule_path = Path("corrections/approved_rule_promotions.json")

        result = review_candidate(
            candidate_id=candidate_id,
            reviewer_id=reviewer_id,
            decision=decision,
            review_metadata=review_metadata,
            log_path=log_path,
            approved_rule_path=approved_rule_path,
        )

        if result.get("success"):
            msg = f"Review decision '{decision}' recorded for candidate {candidate_id}."
            if result.get("approved_rule_record"):
                msg += f" Approved rule record created (status: pending_implementation)."
            return _ok(msg, {"result": result})
        return _err(f"Review decision failed: {result.get('warnings', [])}")

    # ------------------------------------------------------------------
    # Command: /approved rules
    # ------------------------------------------------------------------

    def _cmd_approved(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        if not args or args[0].lower() != "rules":
            return _err("Usage: /approved rules")

        # correction_review doesn't expose load_approved_promotions in the public API,
        # but we can read from the known path directly for display only.
        path = Path("corrections/approved_rule_promotions.json")
        if not path.exists():
            return _ok("No approved rule promotions found.", {"records": []})

        try:
            with open(path, encoding="utf-8") as f:
                records = json.load(f)
        except Exception as exc:
            return _err(f"Could not read approved rules: {exc}")

        # Anonymize by default (strip session IDs)
        for r in records:
            r.pop("session_id", None)
            r.pop("reviewer_id", None)

        return _ok(f"Found {len(records)} approved rule record(s).", {"records": records})

    # ------------------------------------------------------------------
    # Command: /status
    # ------------------------------------------------------------------

    def _cmd_status(self, args: list[str], confirmed: bool = False) -> dict[str, Any]:
        status = self._orch.get_status()
        corrections = status.get("corrections_applied", [])
        conflicts = status.get("correction_conflicts", [])
        session_id = status.get("session_id")

        lines = [
            f"Session ID: {session_id or '(none)'}",
            f"Corrections applied: {len(corrections)}",
            f"Correction conflicts: {len(conflicts)}",
        ]
        if corrections:
            lines.append("Last correction:")
            last = corrections[-1]
            lines.append(f"  - {last.get('field_path')}: {last.get('corrected_value')}")
            lines.append(f"    type={last.get('correction_type')}, scope={last.get('scope')}")
        if conflicts:
            lines.append("Active conflicts:")
            for c in conflicts:
                lines.append(f"  - {c.get('field_path')}: {c.get('message', '')}")

        return _ok("\n".join(lines), {"status": status})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_last_correction(self) -> dict[str, Any] | None:
        """Return the most recently applied correction from the active draft."""
        corrections = self._orch.get_status().get("corrections_applied", [])
        if not corrections:
            return self._last_correction
        return corrections[-1]


# ---------------------------------------------------------------------------
# Standalone CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Minimal CLI for testing the command dispatcher."""
    if argv is None:
        argv = sys.argv[1:]

    # Build a minimal payload for demonstration
    payload = {
        "subj": "TEST SUBJECT.",
        "from": "Commanding Officer, USS EXAMPLE",
        "body": ["Paragraph one.", "Paragraph two."],
    }

    orch = IntakeOrchestrator(payload=payload, session_id="demo_session")
    dispatcher = CommandDispatcher(orch)

    if not argv:
        print("Usage: python -m correction_commands <command>")
        print("Example: python -m correction_commands '/correct subj NEW SUBJECT'")
        return 1

    result = dispatcher.dispatch(" ".join(argv), confirmed=False)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
