#!/usr/bin/env python3
"""
Phase L.32O — Official Candidate Suggestion Commands

Proves simple chat commands for managing quiet official lookup suggestions:
- show candidate: displays pending candidate details without applying
- confirm candidate: applies pending candidate and clears it
- dismiss candidate: clears pending candidate without applying
- no-pending behavior for all three commands

Preserves L.32N quiet suggestion behavior, no auto-apply, To/From letterhead
rules, and L.30Y approval/revise behavior.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import hermes_chat_builder as hermes  # noqa: E402
import official_command_lookup_adapter as adapter  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


def enable() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


class FakeProvider:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(item) for item in self.results]


def from_candidate() -> dict[str, Any]:
    return {
        "resolved_value": {
            "from": "Commanding Officer, 2d Marine Division",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
            "letterhead_activity": "HEADQUARTERS 2D MARINE DIVISION",
            "letterhead_address": "CAMP LEJEUNE NC 28542-0000",
        },
        "source_tier": "official_live",
        "source_title": "2d Marine Division Official .mil Page",
        "source_url": "https://www.marines.mil/",
        "source_limitation": "Official-source candidate; user confirmation required before applying.",
        "confidence": 0.92,
    }


def to_candidate() -> dict[str, Any]:
    return {
        "resolved_value": {
            "to": "Commanding Officer, 2d Marine Division",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
            "letterhead_activity": "HEADQUARTERS 2D MARINE DIVISION",
        },
        "source_tier": "official_live",
        "source_title": "2d Marine Division Official .mil Page",
        "source_url": "https://www.marines.mil/",
        "source_limitation": "To-line candidates do not set letterhead; confirmation mutates only the To field.",
        "confidence": 0.92,
    }


def install_provider(results: list[dict[str, Any]]) -> FakeProvider:
    enable()
    provider = FakeProvider(results)
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)
    return provider


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def pending(result: dict[str, Any]) -> dict[str, Any] | None:
    cands = result.get("source_backed_candidates") or {}
    p = cands.get("pending") or []
    return p[-1] if p else None


# ── Test cases ─────────────────────────────────────────────────────────────


def test_show_candidate_displays_no_apply() -> None:
    """show candidate displays field, resolved value, source title/tier/limitation without applying."""
    install_provider([from_candidate()])
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    shown = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    payload = shown.get("payload") or {}
    cand = shown.get("pending_candidate") or pending(shown)

    check("L32O show candidate intent", shown.get("intent") == "show_candidate")
    check("L32O show candidate success", shown.get("success") is True)
    check("L32O show candidate does not apply From", payload.get("from") != "Commanding Officer, 2d Marine Division")
    check("L32O show candidate does not apply letterhead", payload.get("letterhead_activity") is None)
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32O show candidate field", cand.get("field") == "from")
        check("L32O show candidate resolved from", rv.get("from") == "Commanding Officer, 2d Marine Division")
        check("L32O show candidate source title", "2d Marine Division" in (cand.get("source_title") or ""))
        check("L32O show candidate source tier", cand.get("source_tier") == "official_live")
        check("L32O show candidate limitation present", bool(cand.get("source_limitation")))
    else:
        check("L32O show candidate returned candidate", False, "no pending_candidate returned")


def test_confirm_candidate_applies_and_clears() -> None:
    """confirm candidate applies pending candidate and clears pending list."""
    install_provider([from_candidate()])
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}
    cands = confirmed.get("source_backed_candidates") or {}

    check("L32O confirm candidate intent", confirmed.get("intent") == "confirm_candidate")
    check("L32O confirm applies From", payload.get("from") == "Commanding Officer, 2d Marine Division")
    check("L32O confirm applies letterhead_top_line", payload.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("L32O confirm applies letterhead_activity", payload.get("letterhead_activity") == "HEADQUARTERS 2D MARINE DIVISION")
    check("L32O confirm applies letterhead_address", payload.get("letterhead_address") == "CAMP LEJEUNE NC 28542-0000")
    check("L32O confirm clears pending", len(cands.get("pending") or []) == 0)
    check("L32O confirm adds to confirmed", len(cands.get("confirmed") or []) == 1)


def test_dismiss_candidate_clears_no_apply() -> None:
    """dismiss candidate clears pending without applying and suppresses re-suggestion."""
    install_provider([from_candidate()])
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    dismissed = hermes.send_secnav_chat_turn(chat_id, "dismiss candidate")
    payload = dismissed.get("payload") or {}
    cands_after = dismissed.get("source_backed_candidates") or {}

    check("L32O dismiss candidate intent", dismissed.get("intent") == "reject_candidate")
    check("L32O dismiss candidate success", dismissed.get("success") is True)
    check("L32O dismiss does not apply From", payload.get("from") != "Commanding Officer, 2d Marine Division")
    check("L32O dismiss clears pending", len(cands_after.get("pending") or []) == 0)
    check("L32O dismiss adds to rejected", len(cands_after.get("rejected") or []) == 1)

    followup = hermes.send_secnav_chat_turn(
        chat_id,
        "I still want the letter from 2d Marine Division to II MEF about training.",
    )
    cands_followup = followup.get("source_backed_candidates") or {}
    check("L32O dismissed candidate not immediately re-suggested", len(cands_followup.get("pending") or []) == 0)


def test_no_pending_show_confirm_dismiss() -> None:
    """With no pending candidate, show/confirm/dismiss respond truthfully."""
    install_provider([from_candidate()])
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter. I'll provide the from line myself.",
    )
    # No candidate should be pending (no recognizable official command text).
    show = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    confirm = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    dismiss = hermes.send_secnav_chat_turn(chat_id, "dismiss candidate")

    check("L32O no-pending show intent", show.get("intent") == "show_candidate")
    check("L32O no-pending show success False", show.get("success") is False)
    check("L32O no-pending show message", "no pending" in (show.get("message") or "").lower())
    check("L32O no-pending confirm intent", confirm.get("intent") == "confirm_candidate")
    check("L32O no-pending confirm success False", confirm.get("success") is False)
    check("L32O no-pending confirm message", "no pending" in (confirm.get("message") or "").lower())
    check("L32O no-pending dismiss intent", dismiss.get("intent") == "reject_candidate")
    check("L32O no-pending dismiss success False", dismiss.get("success") is False)
    check("L32O no-pending dismiss message", "no pending" in (dismiss.get("message") or "").lower())


def test_confirm_to_candidate_mutates_only_to() -> None:
    """confirm candidate on a To candidate mutates only the To field."""

    class RoleAwareProvider:
        def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> list[dict[str, Any]]:
            if role == "to":
                return [to_candidate()]
            return []

    install_provider([])
    adapter.set_official_command_search_provider(RoleAwareProvider())
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Commanding Officer, 3d Marine Division to 2d Marine Division about training.",
    )
    # The patched To-line candidate creation should create a To candidate.
    hermes.send_secnav_chat_turn(chat_id, "show candidate")
    before = hermes.send_secnav_chat_turn(chat_id, "status")
    before_payload = before.get("payload") or {}
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}
    cands = confirmed.get("source_backed_candidates") or {}

    check("L32O confirm To applies To", payload.get("to") == "Commanding Officer, 2d Marine Division")
    check("L32O confirm To did not auto-apply letterhead before confirm", before_payload.get("letterhead_activity") is None)
    check("L32O confirm To does not apply letterhead_top_line", payload.get("letterhead_top_line") is None)
    check("L32O confirm To does not apply letterhead_activity", payload.get("letterhead_activity") is None)
    check("L32O confirm To does not apply letterhead_address", payload.get("letterhead_address") is None)
    check("L32O confirm To does not apply unit_identity", payload.get("unit_identity") is None)
    check("L32O confirm To clears pending", len(cands.get("pending") or []) == 0)


def test_l30y_approval_revise_preserved() -> None:
    """L.30Y approval/revise behavior remains intact with suggestion commands."""
    install_provider([from_candidate()])
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to Commanding General, II Marine Expeditionary Force about training readiness.",
    )
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of training readiness.",
    )

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L32O L30Y approval current", approved.get("approved_ready") is True)

    revised = hermes.send_secnav_chat_turn(
        chat_id,
        "change the body to say: This letter directs a review of training readiness and immediate updates.",
    )
    check("L32O L30Y revise clears approval", revised.get("approval_cleared") is True)
    check("L32O L30Y revise payload_changed", revised.get("payload_changed") is True)

    after = hermes.send_secnav_chat_turn(chat_id, "status")
    check("L32O L30Y approved_ready false after revise", after.get("approved_ready") is False)


def main() -> int:
    tests = [
        test_show_candidate_displays_no_apply,
        test_confirm_candidate_applies_and_clears,
        test_dismiss_candidate_clears_no_apply,
        test_no_pending_show_confirm_dismiss,
        test_confirm_to_candidate_mutates_only_to,
        test_l30y_approval_revise_preserved,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32O official candidate suggestion commands smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
