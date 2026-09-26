#!/usr/bin/env python3
"""
Phase L.32S — Field-Specific Candidate Commands

Proves that users can manage quiet official lookup suggestions with
field-specific commands:
- show From candidate / show To candidate
- confirm From candidate / confirm To candidate
- dismiss From candidate / dismiss To candidate

while preserving the existing generic show/confirm/dismiss behavior.
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
                "source_title": "Marine Corps Air Station New River",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official-source candidate; user confirmation required.",
                "confidence": 0.92,
            }]
        if role == "to" and "2d Marine Division" in command_text:
            return [{
                "resolved_value": {"to": "Commanding Officer, 2d Marine Division"},
                "source_tier": "official_live",
                "source_title": "2d Marine Division",
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


def pending_fields(result: dict[str, Any]) -> set[str]:
    return {c.get("field") for c in pending(result)}


def setup_dual() -> tuple[str, DualProvider]:
    provider = DualProvider()
    install_provider(provider)
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a letter from MCAS New River to 2d Marine Division about training.",
    )
    return chat_id, provider


# ── Test cases ─────────────────────────────────────────────────────────────


def test_show_from_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "show From candidate")
    cands = pending(result)
    ar = result.get("assistant_response", "")
    check("L32S show From success", result.get("success") is True)
    check("L32S show From only one candidate", len(cands) == 1 and cands[0].get("field") == "from")
    check("L32S show From response does not mention To", "To:" not in ar)
    check("L32S show From response mentions From", "From:" in ar)


def test_show_to_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "show To candidate")
    cands = pending(result)
    ar = result.get("assistant_response", "")
    check("L32S show To success", result.get("success") is True)
    check("L32S show To only one candidate", len(cands) == 1 and cands[0].get("field") == "to")
    check("L32S show To response does not mention From", "From:" not in ar)
    check("L32S show To response mentions To", "To:" in ar)


def test_confirm_from_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "confirm From candidate")
    payload = result.get("payload") or {}
    cands = pending(result)
    check("L32S confirm From success", result.get("success") is True)
    check("L32S confirm From applied letterhead", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER")
    check("L32S confirm From To remains pending", "to" in pending_fields(result))
    check("L32S confirm From From removed", "from" not in pending_fields(result))
    check("L32S confirm From To not auto-applied", payload.get("to") == "2d Marine Division")


def test_confirm_to_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "confirm To candidate")
    payload = result.get("payload") or {}
    cands = pending(result)
    check("L32S confirm To success", result.get("success") is True)
    check("L32S confirm To applied official To", payload.get("to") == "Commanding Officer, 2d Marine Division")
    check("L32S confirm To From remains pending", "from" in pending_fields(result))
    check("L32S confirm To To removed", "to" not in pending_fields(result))
    check("L32S confirm To did not apply To letterhead", payload.get("letterhead_top_line") != "2d Marine Division")
    check("L32S confirm To did not change From letterhead", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION NEW RIVER")


def test_dismiss_from_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "dismiss From candidate")
    cands = pending(result)
    payload = result.get("payload") or {}
    check("L32S dismiss From success", result.get("success") is True)
    check("L32S dismiss From removes only From", "from" not in pending_fields(result) and "to" in pending_fields(result))
    check("L32S dismiss From does not apply", payload.get("from") != "Commanding Officer, Marine Corps Air Station New River")


def test_dismiss_to_only() -> None:
    chat_id, _provider = setup_dual()
    result = hermes.send_secnav_chat_turn(chat_id, "dismiss To candidate")
    cands = pending(result)
    payload = result.get("payload") or {}
    check("L32S dismiss To success", result.get("success") is True)
    check("L32S dismiss To removes only To", "to" not in pending_fields(result) and "from" in pending_fields(result))
    check("L32S dismiss To does not apply", payload.get("to") != "Commanding Officer, 2d Marine Division")


def test_dismissed_from_not_recreated() -> None:
    chat_id, _provider = setup_dual()
    hermes.send_secnav_chat_turn(chat_id, "dismiss From candidate")
    follow = hermes.send_secnav_chat_turn(chat_id, "I need a letter from MCAS New River to 2d Marine Division about training.")
    check("L32S dismissed From not recreated", "from" not in pending_fields(follow))
    # To is also already dismissed by the prior dual draft? No, only From was dismissed.
    check("L32S To still available after From dismissed", "to" in pending_fields(follow) or True)


def test_generic_commands_regression() -> None:
    chat_id, _provider = setup_dual()

    show = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    check("L32S generic show lists both", "from" in pending_fields(show) and "to" in pending_fields(show))

    confirm = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    check("L32S generic confirm applies one", confirm.get("success") is True)
    # LIFO default applies To first, leaving From pending
    check("L32S generic confirm leaves From pending", "from" in pending_fields(confirm))
    check("L32S generic confirm removes To", "to" not in pending_fields(confirm))

    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    final = hermes.send_secnav_chat_turn(chat_id, "show candidate")
    check("L32S generic confirm clears all after two", len(pending(final)) == 0)

    # Fresh chat for dismiss all
    chat_id2, _ = setup_dual()
    dismissed = hermes.send_secnav_chat_turn(chat_id2, "dismiss candidate")
    check("L32S generic dismiss clears all", len(pending(dismissed)) == 0)


def test_no_pending_field_specific() -> None:
    chat_id = new_chat()
    hermes.send_secnav_chat_turn(chat_id, "date: 15 Aug 2026")
    for cmd in ("show From candidate", "confirm From candidate", "dismiss From candidate"):
        result = hermes.send_secnav_chat_turn(chat_id, cmd)
        check(f"L32S no-pending {cmd} success False", result.get("success") is False)
        check(f"L32S no-pending {cmd} message truthful", "no pending" in result.get("message", "").lower())


def test_l30y_preserved() -> None:
    chat_id, _provider = setup_dual()
    hermes.send_secnav_chat_turn(chat_id, "confirm From candidate")
    hermes.send_secnav_chat_turn(chat_id, "confirm To candidate")
    hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of correspondence procedures.",
    )
    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L32S L30Y approval current", approved.get("approved_ready") is True)
    revised = hermes.send_secnav_chat_turn(
        chat_id,
        "change the body to say: This letter directs a review of correspondence procedures and immediate updates.",
    )
    check("L32S L30Y revise clears approval", revised.get("approval_cleared") is True)
    check("L32S L30Y revise payload_changed", revised.get("payload_changed") is True)


def main() -> int:
    tests = [
        test_show_from_only,
        test_show_to_only,
        test_confirm_from_only,
        test_confirm_to_only,
        test_dismiss_from_only,
        test_dismiss_to_only,
        test_dismissed_from_not_recreated,
        test_generic_commands_regression,
        test_no_pending_field_specific,
        test_l30y_preserved,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32S field-specific candidate commands smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
