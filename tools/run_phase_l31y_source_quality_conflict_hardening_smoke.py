#!/usr/bin/env python3
"""Phase L.31Y smoke: source quality and conflict handling hardening.

This smoke is deterministic.  It uses injected fake providers and does not
depend on the live internet.
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


# ── Fake providers ────────────────────────────────────────────────────────


class FakeProvider:
    """Returns a single result dict per call."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]:
        self.calls.append((role, command_text))
        return self.results


def setup_provider(results: list[dict[str, Any]]) -> FakeProvider:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    provider = FakeProvider(results)
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)
    adapter.install_hermes_to_line_candidate_patch(hermes)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    return provider


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def pending_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(((result.get("source_backed_candidates") or {}).get("pending") or []))


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = pending_candidates(result)
    return pending[-1] if pending else None


# ── S1: Missing provenance does not propose ───────────────────────────────


def test_s1_missing_provenance() -> None:
    """Fake provider returns official-looking result missing source_url."""
    setup_provider([
        {
            "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Naval Example Command Page",
            # source_url intentionally missing
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S1 no pending candidate", cand is None)
    check("S1 From remains literal", payload.get("from") == "Naval Example Command")
    check("S1 no letterhead invented", not payload.get("letterhead_top_line"))
    check("S1 no letterhead activity", not payload.get("letterhead_activity"))
    check("S1 no letterhead address", not payload.get("letterhead_address"))


# ── S2: Conflicting official From results do not propose ──────────────────


def test_s2_conflicting_official_from() -> None:
    """Two official_live results with different From values."""
    setup_provider([
        {
            "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Official Page A",
            "source_url": "https://www.example.navy.mil/A/",
            "confidence": 0.91,
        },
        {
            "resolved_value": {"from": "Commander, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Official Page B",
            "source_url": "https://www.example.navy.mil/B/",
            "confidence": 0.90,
        },
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S2 no apply-ready pending candidate", cand is None)
    check("S2 From remains literal", payload.get("from") == "Naval Example Command")
    check("S2 no letterhead invented", not payload.get("letterhead_top_line"))


# ── S3: Incomplete official From letterhead proposes From only ────────────


def test_s3_incomplete_from_letterhead() -> None:
    """Official result has From but no complete letterhead fields."""
    setup_provider([
        {
            "resolved_value": {
                "from": "Commanding Officer, Naval Example Command",
                # no letterhead fields
            },
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S3 pending From candidate exists", isinstance(cand, dict) and cand.get("field") == "from")
    check("S3 resolved_value includes from", (cand or {}).get("resolved_value", {}).get("from") == "Commanding Officer, Naval Example Command")
    check("S3 no letterhead in resolved_value", "letterhead_top_line" not in (cand or {}).get("resolved_value", {}))
    check("S3 source_limitation mentions incomplete letterhead", "letterhead" in str(cand.get("source_limitation", "")).lower() if cand else False)
    check("S3 From remains literal before confirmation", payload.get("from") == "Naval Example Command")

    # Confirm candidate
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S3 confirm succeeds", bool(confirmed.get("success")))
    check("S3 From mutates to official value", payload2.get("from") == "Commanding Officer, Naval Example Command")
    check("S3 no letterhead applied after confirm", not payload2.get("letterhead_top_line"))
    check("S3 no letterhead activity after confirm", not payload2.get("letterhead_activity"))


# ── S4: Complete official From letterhead still works ─────────────────────


def test_s4_complete_from_letterhead() -> None:
    """Official result has complete From + all three letterhead fields."""
    setup_provider([
        {
            "resolved_value": {
                "from": "Commanding Officer, Naval Example Command",
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            },
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S4 pending candidate exists", isinstance(cand, dict))
    check("S4 From remains literal before confirmation", payload.get("from") == "Naval Example Command")
    check("S4 no letterhead before confirmation", not payload.get("letterhead_top_line"))

    # Confirm
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S4 confirm succeeds", bool(confirmed.get("success")))
    check("S4 From mutates", payload2.get("from") == "Commanding Officer, Naval Example Command")
    check("S4 letterhead applies", payload2.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("S4 letterhead activity applies", payload2.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND")
    check("S4 letterhead address applies", payload2.get("letterhead_address") == "NORFOLK VA 23511-0000")

    # Render path
    details = hermes.send_secnav_chat_turn(
        chat_id,
        "date: 13 Aug 2026\nsignature: J. A. DOE\nbody: This letter directs a review of correspondence procedures.",
    )
    check("S4 details accepted", bool(details.get("success")))
    check("S4 reaches draft preview or ready", details.get("phase") in {"draft_preview", "approved_ready"})
    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("S4 approval succeeds", bool(approved.get("success")))
    rendered = hermes.send_secnav_chat_turn(chat_id, "make the PDF")
    check("S4 render succeeds", bool(rendered.get("success")))
    check("S4 render phase", rendered.get("phase") == "rendered")


# ── S5: To candidate limitation wording and stripping ─────────────────────


def test_s5_to_candidate_stripping() -> None:
    """Official To result includes bogus letterhead fields — they must be stripped."""
    setup_provider([
        {
            "resolved_value": {
                "to": "Commanding Officer, Naval Example Command",
                "letterhead_top_line": "BOGUS LETTERHEAD",
                "letterhead_activity": "BOGUS ACTIVITY",
                "letterhead_address": "BOGUS ADDRESS",
                "unit_identity": "BOGUS UNIT",
            },
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from MCAS Cherry Point to Naval Example Command about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S5 pending To candidate exists", isinstance(cand, dict) and cand.get("field") == "to")
    resolved = (cand or {}).get("resolved_value") or {}
    check("S5 resolved_value includes to", resolved.get("to") == "Commanding Officer, Naval Example Command")
    check("S5 no letterhead_top_line in resolved", "letterhead_top_line" not in resolved)
    check("S5 no letterhead_activity in resolved", "letterhead_activity" not in resolved)
    check("S5 no letterhead_address in resolved", "letterhead_address" not in resolved)
    check("S5 no unit_identity in resolved", "unit_identity" not in resolved)
    check("S5 source_limitation mentions To", "To" in str(cand.get("source_limitation", "")) if cand else False)

    # Confirm mutates only To
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S5 confirm succeeds", bool(confirmed.get("success")))
    check("S5 To mutates", payload2.get("to") == "Commanding Officer, Naval Example Command")
    check("S5 From remains controlled", payload2.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S5 no To letterhead overwrites From", payload2.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")


# ── S6: user_provided candidate requires confirmation ─────────────────────


def test_s6_user_provided_requires_confirmation() -> None:
    """Inject user_provided source result through test state/provider."""
    setup_provider([
        {
            "resolved_value": {"from": "Commanding Officer, User Provided Command"},
            "source_tier": "user_provided",
            "source_title": "User-provided command reference",
            "source_url": "https://example.com/user-ref",
            "source_limitation": "User-provided source; verify before applying.",
            "confidence": 0.95,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from User Provided Command to II MEF about reviewing correspondence procedures.",
    )
    cand = latest_pending(result)

    check("S6 pending candidate exists", isinstance(cand, dict))
    check("S6 requires_user_confirmation is True", cand is not None and cand.get("requires_user_confirmation") is True)
    check("S6 source_tier is user_provided", cand is not None and cand.get("source_tier") == "user_provided")
    check("S6 not treated as official_live", cand is not None and cand.get("source_tier") != "official_live")
    check("S6 no automatic mutation before confirmation", (result.get("payload") or {}).get("from") == "User Provided Command")


# ── S7: user_provided From does not auto-apply official letterhead ────────


def test_s7_user_provided_from_no_auto_letterhead() -> None:
    """Fake user_provided result includes From and letterhead fields."""
    setup_provider([
        {
            "resolved_value": {
                "from": "Commanding Officer, User Provided Command",
                "letterhead_top_line": "USER LETTERHEAD",
                "letterhead_activity": "USER ACTIVITY",
                "letterhead_address": "USER ADDRESS",
            },
            "source_tier": "user_provided",
            "source_title": "User-provided command reference",
            "source_url": "https://example.com/user-ref",
            "confidence": 0.95,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from User Provided Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S7 no mutation before confirmation", payload.get("from") == "User Provided Command")
    check("S7 source_tier remains user_provided", cand is not None and cand.get("source_tier") == "user_provided")
    check("S7 does not claim official_live", cand is not None and cand.get("source_tier") != "official_live")

    # Confirm — user_provided From should NOT auto-apply letterhead
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S7 confirm succeeds", bool(confirmed.get("success")))
    check("S7 From mutates", payload2.get("from") == "Commanding Officer, User Provided Command")
    # user_provided letterhead must not be auto-applied
    check("S7 no letterhead auto-applied", not payload2.get("letterhead_top_line"))


# ── S8: Rejection memory still blocks immediate re-suggestion ─────────────


def test_s8_rejection_memory() -> None:
    """Create candidate, reject it, repeat same input — no re-suggestion."""
    setup_provider([
        {
            "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    first = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    check("S8 initial pending exists", latest_pending(first) is not None)

    rejected = hermes.send_secnav_chat_turn(chat_id, "reject candidate")
    check("S8 reject succeeds", bool(rejected.get("success")))
    payload = rejected.get("payload") or first.get("payload") or {}
    check("S8 From remains literal after rejection", payload.get("from") in {None, "Naval Example Command"})

    again = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    check("S8 repeat does not re-suggest immediately", latest_pending(again) is None)
    check("S8 literal field preserved", (again.get("payload") or {}).get("from") == "Naval Example Command")


# ── S9: Candidate prompt includes field and limitation ────────────────────


def test_s9_candidate_prompt() -> None:
    """Create a pending To candidate and verify assistant_response wording."""
    setup_provider([
        {
            "resolved_value": {"to": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "source_limitation": "To-line candidates do not set letterhead; confirmation mutates only the To field.",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from MCAS Cherry Point to Naval Example Command about reviewing correspondence procedures.",
    )
    resp = result.get("assistant_response") or ""

    check("S9 response includes To candidate", "To" in resp)
    check("S9 response includes source_title", "Naval Example Command Official Page" in resp)
    check("S9 response includes resolved value", "Commanding Officer, Naval Example Command" in resp)
    check("S9 response includes source_limitation", "To-line" in resp or "letterhead" in resp.lower())
    check("S9 response includes confirmation language", "confirm" in resp.lower() or "Confirm" in resp)


# ── S10: Existing accepted paths still pass ───────────────────────────────


def test_s10_existing_paths() -> None:
    """Run through controlled aliases, official From complete, official To, and bad results."""

    # S10a: controlled aliases bypass lookup
    setup_provider([
        {
            "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    check("S10a From expands through controlled alias", payload.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S10a controlled letterhead applies", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")
    check("S10a no pending candidate for controlled alias", latest_pending(result) is None)

    # S10b: official From complete candidate confirm/render
    setup_provider([
        {
            "resolved_value": {
                "from": "Commanding Officer, Naval Example Command",
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            },
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id2 = new_chat()
    result2 = hermes.send_secnav_chat_turn(
        chat_id2,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    check("S10b pending candidate exists", latest_pending(result2) is not None)
    confirmed = hermes.send_secnav_chat_turn(chat_id2, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S10b confirm succeeds", bool(confirmed.get("success")))
    check("S10b From mutates", payload2.get("from") == "Commanding Officer, Naval Example Command")
    check("S10b letterhead applies", payload2.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")

    # S10c: official To candidate confirm/render
    setup_provider([
        {
            "resolved_value": {"to": "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Page",
            "source_url": "https://www.example.navy.mil/Contact/",
            "confidence": 0.91,
        }
    ])
    chat_id3 = new_chat()
    result3 = hermes.send_secnav_chat_turn(
        chat_id3,
        "I need a standard letter from MCAS Cherry Point to Naval Example Command about reviewing correspondence procedures.",
    )
    check("S10c pending To candidate exists", isinstance(latest_pending(result3), dict) and (latest_pending(result3) or {}).get("field") == "to")
    confirmed3 = hermes.send_secnav_chat_turn(chat_id3, "confirm candidate")
    payload3 = confirmed3.get("payload") or {}
    check("S10c To mutates", payload3.get("to") == "Commanding Officer, Naval Example Command")

    # S10d: low-confidence/unofficial/conflicting results do not guess
    for mode, results in [
        ("low", [{"resolved_value": {"from": "Commanding Officer, Naval Example Command"}, "source_tier": "official_live", "source_title": "Low Confidence Page", "source_url": "https://www.example.navy.mil/", "confidence": 0.60}]),
        ("unofficial", [{"resolved_value": {"from": "Commanding Officer, Naval Example Command"}, "source_tier": "secondary_credible", "source_title": "Unofficial Directory", "source_url": "https://example.com/", "confidence": 0.95}]),
        ("conflict", [
            {"resolved_value": {"from": "Commanding Officer, Naval Example Command"}, "source_tier": "official_live", "source_title": "Official Page A", "source_url": "https://www.example.navy.mil/A/", "confidence": 0.91},
            {"resolved_value": {"from": "Commander, Naval Example Command"}, "source_tier": "official_live", "source_title": "Official Page B", "source_url": "https://www.example.navy.mil/B/", "confidence": 0.90},
        ]),
    ]:
        setup_provider(results)
        chat_id = new_chat()
        result = hermes.send_secnav_chat_turn(
            chat_id,
            "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
        )
        payload = result.get("payload") or {}
        check(f"S10d {mode} From remains literal", payload.get("from") == "Naval Example Command")
        check(f"S10d {mode} creates no pending candidate", latest_pending(result) is None)


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    test_s1_missing_provenance()
    test_s2_conflicting_official_from()
    test_s3_incomplete_from_letterhead()
    test_s4_complete_from_letterhead()
    test_s5_to_candidate_stripping()
    test_s6_user_provided_requires_confirmation()
    test_s7_user_provided_from_no_auto_letterhead()
    test_s8_rejection_memory()
    test_s9_candidate_prompt()
    test_s10_existing_paths()

    adapter.set_official_command_search_provider(None)
    adapter.reset_official_command_lookup_cache()
    print(f"\nL.31Y source quality hardening smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
