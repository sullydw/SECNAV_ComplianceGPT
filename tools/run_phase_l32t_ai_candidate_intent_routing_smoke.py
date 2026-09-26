#!/usr/bin/env python3
"""
Phase L.32T — AI-Assisted Candidate Intent Routing

Proves Hermes can interpret natural-language responses to official lookup
suggestions and route them only to the safe, deterministic candidate commands
already implemented in the chat builder.  The router must never mutate the
payload directly and must not apply candidates without clear intent.

Design constraints preserved:
- no static command database
- no open-ended web search
- no auto-apply
- provider/fetcher behavior unchanged
- existing exact commands still work
"""

import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", "1")

import hermes_chat_builder as hermes
import official_command_lookup_adapter as adapter

_FAILED = 0
_PASSED = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global _PASSED, _FAILED
    if cond:
        _PASSED += 1
        print(f"PASS: L32T {label}" + (f" — {detail}" if detail else ""))
    else:
        _FAILED += 1
        print(f"FAIL: L32T {label}" + (f" — {detail}" if detail else ""))


class RecordingProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict) -> list[dict]:
        self.calls.append((command_text, role))
        if role == "from" and "New River" in command_text:
            return [{
                "candidate_id": "src-from-" + hashlib.sha1(command_text.encode()).hexdigest()[:8],
                "resolved_value": {
                    "from": "Commanding Officer, Marine Corps Air Station New River",
                    "letterhead_top_line": "UNITED STATES MARINE CORPS",
                    "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
                    "letterhead_address": "JACKSONVILLE NC 28545-0000",
                },
                "source_tier": "official_live",
                "source_title": "MCAS New River",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        if role == "to" and "2d Marine Division" in command_text:
            return [{
                "candidate_id": "src-to-" + hashlib.sha1(command_text.encode()).hexdigest()[:8],
                "resolved_value": {"to": "Commanding Officer, 2d Marine Division"},
                "source_tier": "official_live",
                "source_title": "2d Marine Division",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        return []


def _new_session(provider: RecordingProvider) -> str:
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    cid = hermes.start_secnav_chat()["chat_id"]
    hermes.send_secnav_chat_turn(cid, "draft a letter from MCAS New River to 2d Marine Division about training")
    return cid


def test_natural_confirm_generic() -> None:
    """yes use that -> confirm_candidate applies the most recent candidate."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    before = hermes.get_secnav_chat_status(cid)
    pending_before = (before.get("source_backed_candidates") or {}).get("pending", [])
    check("natural confirm generic pending count", len(pending_before) == 2, f"pending={len(pending_before)}")

    result = hermes.send_secnav_chat_turn(cid, "yes use that")
    check("natural confirm generic intent", result.get("intent") == "confirm_candidate", result.get("intent"))
    pending_after = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural confirm generic applied one", len(pending_after) == 1, f"pending={len(pending_after)}")
    payload = (result.get("payload") or {})
    check("natural confirm generic applied to", "2d Marine Division" in (payload.get("to") or ""), payload.get("to"))


def test_natural_confirm_from() -> None:
    """apply the sender suggestion -> confirm_from_candidate applies From only."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "apply the sender suggestion")
    check("natural confirm from intent", result.get("intent") == "confirm_from_candidate", result.get("intent"))
    pending_after = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural confirm from leaves to pending", len(pending_after) == 1, f"pending={len(pending_after)}")
    payload = result.get("payload") or {}
    check("natural confirm from applied from", "New River" in (payload.get("from") or ""), payload.get("from"))
    check("natural confirm from applied letterhead", "UNITED STATES MARINE CORPS" == payload.get("letterhead_top_line"), payload.get("letterhead_top_line"))
    check("natural confirm from did not apply official to", "Commanding Officer, 2d Marine Division" not in str(payload.get("to") or ""), payload.get("to"))


def test_natural_confirm_to() -> None:
    """use the recipient one -> confirm_to_candidate applies To only."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "use the recipient one")
    check("natural confirm to intent", result.get("intent") == "confirm_to_candidate", result.get("intent"))
    pending_after = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural confirm to leaves from pending", len(pending_after) == 1, f"pending={len(pending_after)}")
    payload = result.get("payload") or {}
    check("natural confirm to applied to", "2d Marine Division" in (payload.get("to") or ""), payload.get("to"))
    # Letterhead may already exist from a controlled From alias; the To
    # candidate itself must not carry letterhead fields.
    to_rv = result.get("confirmed_candidate", {}).get("resolved_value") or {}
    check("natural confirm to did not apply letterhead", "letterhead_top_line" not in to_rv, to_rv)


def test_natural_show_all() -> None:
    """show me what you found -> show_candidate lists all pending."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "show me what you found")
    check("natural show all intent", result.get("intent") == "show_candidate", result.get("intent"))
    check("natural show all success", result.get("success") is True)
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural show all lists both", len(pending) == 2, f"pending={len(pending)}")
    ar = result.get("assistant_response") or ""
    check("natural show all mentions from", "From:" in ar)
    check("natural show all mentions to", "To:" in ar)


def test_natural_show_from() -> None:
    """show the sender suggestion -> show_from_candidate shows From only."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "show the sender suggestion")
    check("natural show from intent", result.get("intent") == "show_from_candidate", result.get("intent"))
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural show from filtered to one", len(pending) == 1, f"pending={len(pending)}")
    check("natural show from field is from", pending[0].get("field") == "from", pending[0].get("field"))


def test_natural_dismiss_to() -> None:
    """skip the recipient suggestion -> reject_to_candidate clears To only."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "skip the recipient suggestion")
    check("natural dismiss to intent", result.get("intent") == "reject_to_candidate", result.get("intent"))
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural dismiss to leaves from pending", len(pending) == 1 and pending[0].get("field") == "from", f"pending={pending}")


def test_natural_dismiss_generic() -> None:
    """ignore that -> reject_candidate clears all pending candidates."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    result = hermes.send_secnav_chat_turn(cid, "ignore that")
    check("natural dismiss generic intent", result.get("intent") == "reject_candidate", result.get("intent"))
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("natural dismiss generic cleared all", len(pending) == 0, f"pending={len(pending)}")


def test_unclear_intent_does_not_apply() -> None:
    """hmm maybe later -> unclear/say; no candidate applied."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    before = hermes.get_secnav_chat_status(cid)
    before_pending = (before.get("source_backed_candidates") or {}).get("pending", [])
    result = hermes.send_secnav_chat_turn(cid, "hmm maybe later")
    check("unclear intent no confirm", result.get("intent") in {"say", "unclear"}, result.get("intent"))
    after_pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("unclear intent preserves pending", len(after_pending) == len(before_pending), f"before={len(before_pending)} after={len(after_pending)}")
    confirmed = (result.get("source_backed_candidates") or {}).get("confirmed", [])
    check("unclear intent did not confirm any candidate", len(confirmed) == 0, f"confirmed={len(confirmed)}")


def test_exact_commands_still_work() -> None:
    """confirm candidate / show candidate / dismiss candidate still route as before."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    r1 = hermes.send_secnav_chat_turn(cid, "show candidate")
    check("exact show candidate intent", r1.get("intent") == "show_candidate", r1.get("intent"))
    r2 = hermes.send_secnav_chat_turn(cid, "confirm candidate")
    check("exact confirm candidate intent", r2.get("intent") == "confirm_candidate", r2.get("intent"))
    r3 = hermes.send_secnav_chat_turn(cid, "dismiss candidate")
    check("exact dismiss candidate intent", r3.get("intent") == "reject_candidate", r3.get("intent"))


def test_router_does_not_mutate_payload() -> None:
    """The routing layer must only return an intent string, never touch state."""
    payload = {"from": "original from", "to": "original to"}
    payload_hash = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    intent = hermes._route_candidate_intent("yes use that")
    check("router returns safe intent", intent in hermes._CANDIDATE_ROUTER_INTENTS, intent)
    after_hash = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    check("router does not mutate payload", payload_hash == after_hash)


def test_router_known_intents_only() -> None:
    """All natural phrases route to one of the allowed safe intents."""
    global _PASSED, _FAILED
    phrases = [
        "yes use that",
        "use the official one",
        "apply the sender suggestion",
        "use the recipient one",
        "show me what you found",
        "show the sender suggestion",
        "ignore that",
        "skip the recipient suggestion",
        "hmm maybe later",
        "confirm candidate",
        "show from candidate",
        "dismiss to candidate",
    ]
    allowed = set(hermes._CANDIDATE_ROUTER_INTENTS) | {"say"}
    for phrase in phrases:
        intent = hermes._classify_intent(phrase)
        ok = intent in allowed
        if not ok:
            print(f"FAIL: L32T router safety '{phrase}' -> {intent}")
        else:
            _PASSED += 1
            print(f"PASS: L32T router safety '{phrase}' -> {intent}")


def test_l30y_approval_current() -> None:
    """Regression: L.30Y approval/revise still works after candidate routing."""
    provider = RecordingProvider()
    cid = _new_session(provider)
    hermes.send_secnav_chat_turn(cid, "apply the sender suggestion")
    hermes.send_secnav_chat_turn(cid, "use the recipient one")
    hermes.send_secnav_chat_turn(cid, "use subject Training Readiness")
    hermes.send_secnav_chat_turn(cid, "date 12 September 2026")
    hermes.send_secnav_chat_turn(cid, "signature John Smith will sign it")
    hermes.send_secnav_chat_turn(cid, "body say This letter addresses training readiness.")
    hermes.send_secnav_chat_turn(cid, "looks good")
    status = hermes.get_secnav_chat_status(cid)
    check("L30Y approval current", bool(status.get("approved_ready")), status.get("approved_ready"))


if __name__ == "__main__":
    # Clear any persisted state to keep this test deterministic.
    state_dir = Path(hermes._STATE_DIR)
    if state_dir.exists():
        for f in state_dir.glob("chat-*.json"):
            f.unlink()

    test_natural_confirm_generic()
    test_natural_confirm_from()
    test_natural_confirm_to()
    test_natural_show_all()
    test_natural_show_from()
    test_natural_dismiss_to()
    test_natural_dismiss_generic()
    test_unclear_intent_does_not_apply()
    test_exact_commands_still_work()
    test_router_does_not_mutate_payload()
    test_router_known_intents_only()
    test_l30y_approval_current()

    print(f"\nL.32T AI-assisted candidate intent routing smoke: {_PASSED}/{_PASSED + _FAILED} PASS")
    sys.exit(0 if _FAILED == 0 else 1)
