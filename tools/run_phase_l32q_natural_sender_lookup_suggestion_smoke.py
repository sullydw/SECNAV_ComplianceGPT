#!/usr/bin/env python3
"""
Phase L.32Q — Natural Sender Lookup Suggestion Workflow

Proves that a natural first-turn draft with a sender phrase like
"from MCAS New River" quietly surfaces an official lookup From/letterhead
suggestion without interrupting the draft flow.

Rules:
- natural first-turn draft extracts literal From value
- if official lookup is enabled and a clean source-backed From candidate
  exists, it is stored as a quiet pending suggestion
- draft flow continues normally
- complete From candidate may suggest From + complete letterhead, but does not
  auto-apply; applies only after confirm candidate
- incomplete From candidate suggests From only and does not invent letterhead
- disabled lookup: natural draft still works, no provider call
- dismissed candidate: same sender text does not immediately recreate it
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


class RoleAwareProvider:
    """Return official From candidates for natural sender phrases."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((command_text, role))
        if role == "from" and "New River" in command_text:
            return [{
                "resolved_value": {
                    "from": "Commanding Officer, Marine Corps Air Station New River",
                    "letterhead_top_line": "UNITED STATES MARINE CORPS",
                    "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
                    "letterhead_address": "JACKSONVILLE NC 28545-0000",
                },
                "source_tier": "official_live",
                "source_title": "Marine Corps Air Station New River Official .mil Page",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official-source candidate; user confirmation required before applying.",
                "confidence": 0.92,
            }]
        if role == "from" and "Cherry Point" in command_text:
            return [{
                "resolved_value": {
                    "from": "Commanding Officer, Marine Corps Air Station Cherry Point",
                    "letterhead_top_line": "UNITED STATES MARINE CORPS",
                },
                "source_tier": "official_live",
                "source_title": "Marine Corps Air Station Cherry Point Official .mil Page",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official source did not provide complete letterhead address; letterhead not proposed.",
                "confidence": 0.92,
            }]
        return []


def install_provider(provider: RoleAwareProvider) -> None:
    enable()
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def pending(result: dict[str, Any]) -> dict[str, Any] | None:
    cands = result.get("source_backed_candidates") or {}
    p = cands.get("pending") or []
    return p[-1] if p else None


# ── Test cases ─────────────────────────────────────────────────────────────


def test_natural_first_turn_from_suggestion_complete() -> None:
    """Natural sender phrase with complete letterhead stores a quiet From suggestion."""
    provider = RoleAwareProvider()
    install_provider(provider)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    payload = result.get("payload") or {}
    cand = pending(result)
    ar = result.get("assistant_response", "")

    check("L32Q natural draft extracted literal From", payload.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32Q From candidate is pending", isinstance(cand, dict) and cand.get("field") == "from")
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32Q From candidate resolved from", rv.get("from") == "Commanding Officer, Marine Corps Air Station New River")
        check("L32Q From candidate includes letterhead_top_line", rv.get("letterhead_top_line") == "UNITED STATES MARINE CORPS")
        check("L32Q From candidate includes letterhead_activity", rv.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER")
        check("L32Q From candidate includes letterhead_address", rv.get("letterhead_address") == "JACKSONVILLE NC 28545-0000")
    check("L32Q From suggestion appears quietly", "source-backed suggestion" in ar or "confirm candidate" in ar)
    # The controlled alias for MCAS New River already applies its own letterhead
    # to the draft; the source-backed candidate remains pending (candidate-only).
    check("L32Q From candidate not auto-confirmed", cand.get("status") == "pending")
    check("L32Q provider called for From", any(c[1] == "from" and "New River" in c[0] for c in provider.calls))


def test_confirm_complete_from_applies_letterhead() -> None:
    """Confirming a complete From candidate applies From and full letterhead."""
    provider = RoleAwareProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}
    cands = confirmed.get("source_backed_candidates") or {}

    check("L32Q confirm From applies From", payload.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32Q confirm From applies letterhead_top_line", payload.get("letterhead_top_line") == "UNITED STATES MARINE CORPS")
    check("L32Q confirm From applies letterhead_activity", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER")
    check("L32Q confirm From applies letterhead_address", payload.get("letterhead_address") == "JACKSONVILLE NC 28545-0000")
    check("L32Q confirm From clears pending", len(cands.get("pending") or []) == 0)


def test_incomplete_from_suggests_from_only() -> None:
    """Incomplete letterhead From candidate suggests From only and does not invent letterhead."""
    provider = RoleAwareProvider()
    install_provider(provider)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS Cherry Point to 2d Marine Division about training.",
    )
    payload = result.get("payload") or {}
    cand = pending(result)

    check("L32Q incomplete From candidate is pending", isinstance(cand, dict) and cand.get("field") == "from")
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32Q incomplete From candidate suggests From only", rv.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
        check("L32Q incomplete From candidate does not suggest letterhead_activity", "letterhead_activity" not in rv)
        check("L32Q incomplete From candidate does not suggest letterhead_address", "letterhead_address" not in rv)
    # The controlled alias for MCAS Cherry Point already applies its own
    # letterhead to the draft; the candidate itself does not invent it.
    check("L32Q incomplete From candidate not confirmed", cand.get("status") == "pending")


def test_disabled_lookup_no_provider_call() -> None:
    """With official lookup disabled, natural draft works and no provider is called."""
    provider = RoleAwareProvider()
    disable()
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    payload = result.get("payload") or {}
    cands = result.get("source_backed_candidates") or {}

    check("L32Q disabled lookup still extracts From", payload.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32Q disabled lookup no pending candidates", len(cands.get("pending") or []) == 0)
    check("L32Q disabled lookup provider not called", provider.calls == [], f"calls={provider.calls!r}")


def test_dismiss_prevents_re_suggestion() -> None:
    """Dismissed From candidate is not immediately re-suggested on similar input."""
    provider = RoleAwareProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    hermes.send_secnav_chat_turn(chat_id, "dismiss candidate")
    followup = hermes.send_secnav_chat_turn(
        chat_id,
        "I still want the letter from MCAS New River to 2d Marine Division about training readiness.",
    )
    cands = followup.get("source_backed_candidates") or {}

    check("L32Q dismissed From not re-suggested", len(cands.get("pending") or []) == 0)


def test_l30y_preserved() -> None:
    """L.30Y approval/revise behavior remains intact after natural From suggestion."""
    provider = RoleAwareProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training readiness.",
    )
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of training readiness.",
    )

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L32Q L30Y approval current", approved.get("approved_ready") is True)

    revised = hermes.send_secnav_chat_turn(
        chat_id,
        "change the body to say: This letter directs a review of training readiness and immediate updates.",
    )
    check("L32Q L30Y revise clears approval", revised.get("approval_cleared") is True)
    check("L32Q L30Y revise payload_changed", revised.get("payload_changed") is True)

    after = hermes.send_secnav_chat_turn(chat_id, "status")
    check("L32Q L30Y approved_ready false after revise", after.get("approved_ready") is False)


def main() -> int:
    tests = [
        test_natural_first_turn_from_suggestion_complete,
        test_confirm_complete_from_applies_letterhead,
        test_incomplete_from_suggests_from_only,
        test_disabled_lookup_no_provider_call,
        test_dismiss_prevents_re_suggestion,
        test_l30y_preserved,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32Q natural sender lookup suggestion smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
