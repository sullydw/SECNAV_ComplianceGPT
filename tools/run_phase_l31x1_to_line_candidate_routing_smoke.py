#!/usr/bin/env python3
"""Phase L.31X-1 smoke: To-line official lookup candidate routing.

This smoke is deterministic.  It uses an injected fake official-source provider
and does not depend on the live internet.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Iterable

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


class FakeProvider:
    def __init__(self, mode: str = "official") -> None:
        self.mode = mode
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]:
        self.calls.append((role, command_text))
        if self.mode == "official":
            return [
                {
                    "resolved_value": {
                        role: "Commanding Officer, Naval Example Command" if role == "to" else "Commanding Officer, Naval Example Command",
                        "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                        "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                        "letterhead_address": "NORFOLK VA 23511-0000",
                    },
                    "source_tier": "official_live",
                    "source_title": "Naval Example Command Official Contact Page",
                    "source_url": "https://www.example.navy.mil/Contact/",
                    "source_limitation": "Deterministic fake official page for smoke testing.",
                    "confidence": 0.91,
                }
            ]
        if self.mode == "low":
            return [
                {
                    "resolved_value": {role: "Commanding Officer, Naval Example Command"},
                    "source_tier": "official_live",
                    "source_title": "Low Confidence Official Page",
                    "source_url": "https://www.example.navy.mil/Contact/",
                    "confidence": 0.60,
                }
            ]
        if self.mode == "unofficial":
            return [
                {
                    "resolved_value": {role: "Commanding Officer, Naval Example Command"},
                    "source_tier": "secondary_credible",
                    "source_title": "Unofficial Directory",
                    "source_url": "https://example.com/naval-example-command",
                    "confidence": 0.95,
                }
            ]
        if self.mode == "conflict":
            return [
                {
                    "resolved_value": {role: "Commanding Officer, Naval Example Command"},
                    "source_tier": "official_live",
                    "source_title": "Official Page A",
                    "source_url": "https://www.example.navy.mil/A/",
                    "confidence": 0.91,
                },
                {
                    "resolved_value": {role: "Commander, Naval Example Command"},
                    "source_tier": "official_live",
                    "source_title": "Official Page B",
                    "source_url": "https://www.example.navy.mil/B/",
                    "confidence": 0.90,
                },
            ]
        return []


def setup_provider(mode: str = "official") -> FakeProvider:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    provider = FakeProvider(mode)
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)
    adapter.install_hermes_to_line_candidate_patch(hermes)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    return provider


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def request_with_unresolved_to(chat_id: str) -> dict[str, Any]:
    return hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from MCAS Cherry Point to Naval Example Command about reviewing correspondence procedures.",
    )


def pending_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(((result.get("source_backed_candidates") or {}).get("pending") or []))


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = pending_candidates(result)
    return pending[-1] if pending else None


def test_s1_unresolved_to_creates_candidate() -> str:
    provider = setup_provider("official")
    chat_id = new_chat()
    result = request_with_unresolved_to(chat_id)
    cand = latest_pending(result)
    payload = result.get("payload") or {}
    resolved = (cand or {}).get("resolved_value") or {}

    check("S1 send succeeds", bool(result.get("success")))
    check("S1 From expands through controlled alias", payload.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S1 controlled From letterhead applies", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")
    check("S1 To remains literal before confirmation", payload.get("to") == "Naval Example Command")
    check("S1 pending To candidate exists", isinstance(cand, dict) and cand.get("field") == "to")
    check("S1 candidate is official_live", cand is not None and cand.get("source_tier") == "official_live")
    check("S1 candidate requires confirmation", cand is not None and cand.get("requires_user_confirmation") is True)
    check("S1 candidate resolved_value includes To", resolved.get("to") == "Commanding Officer, Naval Example Command")
    check("S1 To candidate has no letterhead_top_line", "letterhead_top_line" not in resolved)
    check("S1 To candidate has no letterhead_activity", "letterhead_activity" not in resolved)
    check("S1 To candidate has no letterhead_address", "letterhead_address" not in resolved)
    check("S1 fake provider called only for To", provider.calls == [("to", "Naval Example Command")], str(provider.calls))
    return chat_id


def test_s2_confirm_to_candidate(chat_id: str) -> None:
    result = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = result.get("payload") or {}
    confirmed = ((result.get("source_backed_candidates") or {}).get("confirmed") or [])[-1]
    check("S2 confirm succeeds", bool(result.get("success")))
    check("S2 confirmed candidate is To", confirmed.get("field") == "to")
    check("S2 To mutates to official value", payload.get("to") == "Commanding Officer, Naval Example Command")
    check("S2 From remains controlled value", payload.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S2 From letterhead remains controlled", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")
    check("S2 no To letterhead overwrites From", payload.get("letterhead_address") == "CHERRY POINT NC 28533-0000")


def test_s3_reject_preserves_literal() -> None:
    setup_provider("official")
    chat_id = new_chat()
    first = request_with_unresolved_to(chat_id)
    check("S3 initial pending exists", latest_pending(first) is not None)
    rejected = hermes.send_secnav_chat_turn(chat_id, "reject candidate")
    payload = rejected.get("payload") or first.get("payload") or {}
    check("S3 reject succeeds", bool(rejected.get("success")))
    check("S3 To remains literal after rejection", payload.get("to") in {None, "Naval Example Command"})
    check("S3 From remains controlled after rejection", (payload.get("from") or (first.get("payload") or {}).get("from")) == "Commanding Officer, Marine Corps Air Station Cherry Point")
    again = request_with_unresolved_to(chat_id)
    check("S3 repeat does not re-suggest immediately", latest_pending(again) is None)


def test_s4_controlled_to_bypasses_lookup() -> None:
    provider = setup_provider("official")
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    check("S4 controlled To send succeeds", bool(result.get("success")))
    check("S4 To expands through controlled alias", payload.get("to") == "Commanding General, II Marine Expeditionary Force")
    check("S4 provider not called", provider.calls == [], str(provider.calls))
    check("S4 no pending candidate", latest_pending(result) is None)


def test_s5_bad_to_results_do_not_guess() -> None:
    for mode in ("low", "unofficial", "conflict"):
        setup_provider(mode)
        chat_id = new_chat()
        result = request_with_unresolved_to(chat_id)
        payload = result.get("payload") or {}
        check(f"S5 {mode} To remains literal", payload.get("to") == "Naval Example Command")
        check(f"S5 {mode} creates no pending candidate", latest_pending(result) is None)
        check(f"S5 {mode} invents no To letterhead", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")


def test_s6_confirmed_to_candidate_renders() -> None:
    setup_provider("official")
    chat_id = new_chat()
    request_with_unresolved_to(chat_id)
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    check("S6 confirm succeeds", bool(confirmed.get("success")))
    details = hermes.send_secnav_chat_turn(
        chat_id,
        "date: 13 Aug 2026\nsignature: J. A. DOE\nbody: This letter directs a review of correspondence procedures.",
    )
    check("S6 details accepted", bool(details.get("success")))
    check("S6 reaches draft preview or ready", details.get("phase") in {"draft_preview", "approved_ready"})
    check("S6 validation ready", bool(details.get("validation_ready")))
    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("S6 approval succeeds", bool(approved.get("success")))
    rendered = hermes.send_secnav_chat_turn(chat_id, "make the PDF")
    check("S6 render succeeds", bool(rendered.get("success")))
    check("S6 render phase", rendered.get("phase") == "rendered")
    check("S6 pdf path present", bool(rendered.get("pdf_path")))


def main() -> int:
    chat = test_s1_unresolved_to_creates_candidate()
    test_s2_confirm_to_candidate(chat)
    test_s3_reject_preserves_literal()
    test_s4_controlled_to_bypasses_lookup()
    test_s5_bad_to_results_do_not_guess()
    test_s6_confirmed_to_candidate_renders()

    adapter.set_official_command_search_provider(None)
    adapter.reset_official_command_lookup_cache()
    print(f"\nL.31X-1 To-line candidate routing smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
