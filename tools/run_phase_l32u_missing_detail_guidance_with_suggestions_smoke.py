#!/usr/bin/env python3
"""
Phase L.32U — Natural Missing-Detail Guidance With Official Suggestions

Proves that when a natural first-turn draft creates quiet official lookup
suggestions, the assistant response also clearly states the remaining
required details, and that confirming From/To candidates updates that
guidance appropriately without auto-apply or mutation of provider behavior.

Constraints preserved:
- no static command database
- no open-ended web search
- no auto-apply
- provider/fetcher behavior unchanged
- approval/render safety gates unchanged
"""

import hashlib
import json
import os
import sys
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
        print(f"PASS: L32U {label}" + (f" — {detail}" if detail else ""))
    else:
        _FAILED += 1
        print(f"FAIL: L32U {label}" + (f" — {detail}" if detail else ""))


class CompleteProvider:
    def __call__(self, command_text: str, role: str, state: dict):
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


class IncompleteFromProvider:
    def __call__(self, command_text: str, role: str, state: dict):
        if role == "from" and "Fleet Marine Force Atlantic" in command_text:
            return [{
                "candidate_id": "src-from-inc",
                "resolved_value": {"from": "Commander, Fleet Marine Force Atlantic"},
                "source_tier": "official_live",
                "source_title": "Fleet Marine Force Atlantic",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        if role == "to" and "2d Marine Division" in command_text:
            return [{
                "candidate_id": "src-to-1",
                "resolved_value": {"to": "Commanding Officer, 2d Marine Division"},
                "source_tier": "official_live",
                "source_title": "2d Marine Division",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        return []


def _new_session(provider) -> str:
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    cid = hermes.start_secnav_chat()["chat_id"]
    return cid


def test_guidance_with_dual_suggestions() -> None:
    """Natural first turn creates suggestions AND lists missing details."""
    cid = _new_session(CompleteProvider())
    result = hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division")
    ar = result.get("assistant_response") or ""
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    check("dual suggestions created", len(pending) == 2, f"pending={len(pending)}")
    check("guidance mentions missing subject", "subject line" in ar or "subject" in ar.lower(), ar)
    check("quiet suggestion note present", "source-backed" in ar.lower(), ar)
    check("guidance does not block suggestion", ar.count("source-backed") >= 1)


def test_guidance_after_complete_from_confirm() -> None:
    """Confirming complete From removes letterhead from missing guidance."""
    cid = _new_session(CompleteProvider())
    hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division")
    result = hermes.send_secnav_chat_turn(cid, "apply the sender suggestion")
    ar = result.get("assistant_response") or ""
    check("complete from confirm applied", result.get("intent") == "confirm_from_candidate")
    # Letterhead fields should now be present in payload.
    payload = result.get("payload") or {}
    check("complete from letterhead applied", "UNITED STATES MARINE CORPS" == payload.get("letterhead_top_line"))
    # Guidance should not ask for letterhead details.
    check("guidance no longer asks letterhead", "letterhead" not in ar.lower() or "command letterhead details" not in ar.lower(), ar)
    # Should still ask for other missing details.
    check("guidance still asks subject/body/date/signer", any(k in ar.lower() for k in ["subject", "body", "date", "sign"]), ar)


def test_guidance_after_incomplete_from_confirm() -> None:
    """Confirming incomplete From keeps letterhead in missing guidance."""
    cid = _new_session(IncompleteFromProvider())
    hermes.send_secnav_chat_turn(cid, "I need a letter from Fleet Marine Force Atlantic to 2d Marine Division")
    result = hermes.send_secnav_chat_turn(cid, "apply the sender suggestion")
    ar = result.get("assistant_response") or ""
    payload = result.get("payload") or {}
    check("incomplete from confirm applied", result.get("intent") == "confirm_from_candidate")
    rv = (result.get("confirmed_candidate") or {}).get("resolved_value") or {}
    check("incomplete from candidate has no letterhead", "letterhead_top_line" not in rv, rv)
    # Because letterhead is not auto-applied either (non-controlled alias),
    # payload should not have letterhead and guidance should mention it.
    check("payload lacks letterhead after incomplete from", payload.get("letterhead_top_line") is None, payload.get("letterhead_top_line"))
    check("guidance asks letterhead details after incomplete from", "letterhead" in ar.lower() or "command letterhead details" in ar.lower(), ar)


def test_guidance_after_to_confirm() -> None:
    """Confirming To does not provide From letterhead guidance."""
    cid = _new_session(CompleteProvider())
    hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division")
    result = hermes.send_secnav_chat_turn(cid, "use the recipient one")
    ar = result.get("assistant_response") or ""
    payload = result.get("payload") or {}
    check("to confirm applied", result.get("intent") == "confirm_to_candidate")
    rv = (result.get("confirmed_candidate") or {}).get("resolved_value") or {}
    check("to candidate has no letterhead", "letterhead_top_line" not in rv, rv)
    # Since From remains pending and is a controlled alias, payload may have its
    # auto-applied letterhead. We only require that the assistant does not
    # falsely claim letterhead is resolved because of the To candidate.
    check("to confirm did not falsely resolve letterhead", "letterhead" not in ar.lower() or "from" in ar.lower(), ar)
    # Guidance still lists remaining missing details.
    check("guidance still lists missing details", any(k in ar.lower() for k in ["subject", "body", "date", "sign"]), ar)


def test_disabled_lookup_guidance() -> None:
    """With lookup disabled, natural draft still gives normal missing-detail guidance."""
    prev = os.environ.get("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP")
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "0"
    # Need fresh import to pick up disabled state.
    import importlib
    importlib.reload(adapter)
    importlib.reload(hermes)
    cid = hermes.start_secnav_chat()["chat_id"]
    result = hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division")
    pending = (result.get("source_backed_candidates") or {}).get("pending", [])
    ar = result.get("assistant_response") or ""
    check("disabled lookup no pending", len(pending) == 0, f"pending={len(pending)}")
    check("disabled lookup no source-backed note", "source-backed" not in ar.lower(), ar)
    check("disabled lookup still gives guidance", any(k in ar.lower() for k in ["subject", "still need"]), ar)
    if prev is None:
        os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    else:
        os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = prev
    # Re-enable for remaining tests
    adapter.set_official_command_search_provider(CompleteProvider())
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)


def test_l30y_approval_current() -> None:
    """Regression: L.30Y approval/revise still works."""
    cid = _new_session(CompleteProvider())
    hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division")
    hermes.send_secnav_chat_turn(cid, "apply the sender suggestion")
    hermes.send_secnav_chat_turn(cid, "use the recipient one")
    hermes.send_secnav_chat_turn(cid, "subject Training Readiness")
    hermes.send_secnav_chat_turn(cid, "date 12 September 2026")
    hermes.send_secnav_chat_turn(cid, "signature John Smith will sign it")
    hermes.send_secnav_chat_turn(cid, "body say This letter addresses training readiness.")
    hermes.send_secnav_chat_turn(cid, "looks good")
    status = hermes.get_secnav_chat_status(cid)
    check("L30Y approval current", bool(status.get("approved_ready")), status.get("approved_ready"))


if __name__ == "__main__":
    state_dir = Path(hermes._STATE_DIR)
    if state_dir.exists():
        for f in state_dir.glob("chat-*.json"):
            f.unlink()

    test_guidance_with_dual_suggestions()
    test_guidance_after_complete_from_confirm()
    test_guidance_after_incomplete_from_confirm()
    test_guidance_after_to_confirm()
    test_disabled_lookup_guidance()
    test_l30y_approval_current()

    print(f"\nL.32U missing-detail guidance with suggestions smoke: {_PASSED}/{_PASSED + _FAILED} PASS")
    sys.exit(0 if _FAILED == 0 else 1)
