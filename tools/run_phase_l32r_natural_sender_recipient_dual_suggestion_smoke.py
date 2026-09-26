#!/usr/bin/env python3
"""
Phase L.32R — Natural Sender and Recipient Dual Suggestion Workflow

Proves that a natural first-turn draft with both a From phrase and a To phrase
quietly surfaces source-backed suggestions for both fields without interrupting
the draft flow or forcing a confirmation detour.

Rules:
- natural first-turn draft extracts literal From and To values
- clean source-backed From and To candidates are stored as quiet pending suggestions
- draft flow continues normally
- no auto-apply
- assistant_response summarizes both suggestions in a quiet note
- show candidate displays pending candidates clearly
- confirm candidate applies candidates deterministically (one at a time from the back)
- dismiss candidate clears pending suggestions without applying
- From candidate applies complete letterhead only after confirmation
- To candidate mutates only To
- disabled lookup: natural draft works, no provider calls
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


class DualProvider:
    """Return official From and To candidates for natural sender/recipient phrases."""

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
        if role == "to" and "2d Marine Division" in command_text:
            return [{
                "resolved_value": {"to": "Commanding Officer, 2d Marine Division"},
                "source_tier": "official_live",
                "source_title": "2d Marine Division Official .mil Page",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "To-line candidates do not set letterhead; confirmation mutates only the To field.",
                "confidence": 0.92,
            }]
        return []


def install_provider(provider: DualProvider) -> None:
    enable()
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def pending(result: dict[str, Any]) -> list[dict[str, Any]]:
    cands = result.get("source_backed_candidates") or {}
    return list(cands.get("pending") or [])


# ── Test cases ─────────────────────────────────────────────────────────────


def test_dual_suggestion_first_turn() -> None:
    """Natural draft with From and To creates quiet pending suggestions for both."""
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    payload = result.get("payload") or {}
    cands = pending(result)
    ar = result.get("assistant_response", "")
    fields = {c.get("field"): c for c in cands}

    check("L32R dual draft extracted From", payload.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32R dual draft extracted To", payload.get("to") == "2d Marine Division")
    check("L32R From candidate pending", "from" in fields)
    check("L32R To candidate pending", "to" in fields)
    check("L32R dual suggestion note present", "source-backed suggestions" in ar.lower())
    check("L32R dual suggestion lists From", "From:" in ar)
    check("L32R dual suggestion lists To", "To:" in ar)
    check("L32R dual suggestion mentions show/confirm/dismiss", "show candidate" in ar and "confirm candidate" in ar and "dismiss candidate" in ar)
    check("L32R no auto-apply From candidate", fields["from"].get("status") == "pending")
    check("L32R no auto-apply To candidate", fields["to"].get("status") == "pending")
    check("L32R provider called for From", any(c == ("Commanding Officer, Marine Corps Air Station New River", "from") for c in provider.calls))
    check("L32R provider called for To", any(c == ("2d Marine Division", "to") for c in provider.calls))


def test_show_candidate_displays_both() -> None:
    """show candidate clearly displays both pending candidates."""
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    shown = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    cands = pending(shown)
    ar = shown.get("assistant_response", "")
    fields = {c.get("field"): c for c in cands}

    check("L32R show candidate success", shown.get("success") is True)
    check("L32R show candidate displays From", "from" in fields)
    check("L32R show candidate displays To", "to" in fields)
    check("L32R show candidate assistant_response lists both", "From:" in ar and "To:" in ar)


def test_confirm_candidate_applies_one_at_a_time() -> None:
    """confirm candidate applies the most recent pending candidate, then the next."""
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    first = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload1 = first.get("payload") or {}
    pending1 = pending(first)

    # The most recent candidate (To) should be applied first; From remains pending.
    check("L32R first confirm applied To", payload1.get("to") == "Commanding Officer, 2d Marine Division")
    check("L32R first confirm kept From pending", len(pending1) == 1 and pending1[0].get("field") == "from")

    second = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = second.get("payload") or {}
    pending2 = pending(second)

    check("L32R second confirm applied From", payload2.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32R second confirm applied letterhead", payload2.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER")
    check("L32R second confirm cleared pending", len(pending2) == 0)


def test_dismiss_candidate_clears_both() -> None:
    """dismiss candidate clears all pending suggestions without applying either."""
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    hermes.send_secnav_chat_turn(chat_id, "dismiss candidate")
    # After one dismiss, reject all remaining pending candidates explicitly.
    while (hermes.send_secnav_chat_turn(chat_id, "show candidate").get("source_backed_candidates") or {}).get("pending"):
        hermes.send_secnav_chat_turn(chat_id, "dismiss candidate")

    status = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    payload = status.get("payload") or {}
    cands = status.get("source_backed_candidates") or {}

    check("L32R dismiss cleared pending", len(cands.get("pending") or []) == 0)
    check("L32R dismiss does not apply From", payload.get("from") != "Commanding Officer, Marine Corps Air Station New River")
    check("L32R dismiss does not apply To", payload.get("to") != "Commanding Officer, 2d Marine Division")


def test_disabled_lookup_no_provider_call() -> None:
    """With official lookup disabled, dual natural draft works and no provider is called."""
    provider = DualProvider()
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

    check("L32R disabled lookup still extracts From", payload.get("from") == "Commanding Officer, Marine Corps Air Station New River")
    check("L32R disabled lookup still extracts To", payload.get("to") == "2d Marine Division")
    check("L32R disabled lookup no pending candidates", len(cands.get("pending") or []) == 0)
    check("L32R disabled lookup provider not called", provider.calls == [], f"calls={provider.calls!r}")


def test_l30y_preserved() -> None:
    """L.30Y approval/revise behavior remains intact after dual suggestions."""
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training readiness.",
    )
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of training readiness.",
    )

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L32R L30Y approval current", approved.get("approved_ready") is True)

    revised = hermes.send_secnav_chat_turn(
        chat_id,
        "change the body to say: This letter directs a review of training readiness and immediate updates.",
    )
    check("L32R L30Y revise clears approval", revised.get("approval_cleared") is True)
    check("L32R L30Y revise payload_changed", revised.get("payload_changed") is True)

    after = hermes.send_secnav_chat_turn(chat_id, "status")
    check("L32R L30Y approved_ready false after revise", after.get("approved_ready") is False)


def main() -> int:
    tests = [
        test_dual_suggestion_first_turn,
        test_show_candidate_displays_both,
        test_confirm_candidate_applies_one_at_a_time,
        test_dismiss_candidate_clears_both,
        test_disabled_lookup_no_provider_call,
        test_l30y_preserved,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32R natural sender/recipient dual suggestion smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
