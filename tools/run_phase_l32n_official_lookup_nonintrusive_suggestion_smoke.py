#!/usr/bin/env python3
"""
Phase L.32N — Official Lookup Non-Intrusive Suggestion Mode

Proves that clean high-confidence official lookup results are presented as
quiet pending suggestions rather than forced confirmation prompts, while still
remaining candidate-only and never auto-applying.

Rules:
- clean high-confidence official result: candidate-only, no auto-apply, no
  forced prompt; appears as quiet suggestion in assistant_response
- conflicting or low-confidence result: fails closed or asks for clarification
- From candidate: suggests From + complete letterhead only if complete;
  incomplete letterhead suggests From only
- To candidate: suggests To only, strips letterhead/unit identity
- user can still explicitly accept/apply pending candidate later
- preserves no open-ended web search, no static DB, no auto-apply, L.30Y
  approval/revise behavior, and L.32M explicit URL behavior
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
import official_command_provider as provider_module  # noqa: E402

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


# ── Fixture provider helpers (deterministic, no network) ───────────────────

class FakeProvider:
    """Deterministic provider returning a fixed list of raw results."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((command_text, role))
        return [dict(item) for item in self.results]


def from_complete(command: str = "2d Marine Division") -> dict[str, Any]:
    return {
        "resolved_value": {
            "from": f"Commanding Officer, {command}",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
            "letterhead_activity": f"HEADQUARTERS {command.upper()}",
            "letterhead_address": "CAMP LEJEUNE NC 28542-0000",
        },
        "source_tier": "official_live",
        "source_title": f"{command} Official .mil Page",
        "source_url": "https://www.example.navy.mil/example-command",
        "source_limitation": "Official-source candidate; user confirmation required.",
        "confidence": 0.92,
    }


def from_incomplete(command: str = "2d Marine Division") -> dict[str, Any]:
    return {
        "resolved_value": {
            "from": f"Commanding Officer, {command}",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
        },
        "source_tier": "official_live",
        "source_title": f"{command} Official .mil Page",
        "source_url": "https://www.example.navy.mil/example-command",
        "source_limitation": "Official source did not provide complete letterhead address; letterhead not proposed.",
        "confidence": 0.92,
    }


def to_with_bogus_letterhead(command: str = "2d Marine Division") -> dict[str, Any]:
    return {
        "resolved_value": {
            "to": f"Commanding Officer, {command}",
            "letterhead_top_line": "BOGUS TOP",
            "letterhead_activity": "BOGUS ACTIVITY",
            "letterhead_address": "BOGUS ADDRESS",
            "unit_identity": "BOGUS UNIT",
        },
        "source_tier": "official_live",
        "source_title": f"{command} Official .mil Page",
        "source_url": "https://www.example.navy.mil/example-command",
        "source_limitation": "To-line candidates do not set letterhead; confirmation mutates only the To field.",
        "confidence": 0.92,
    }


def low_confidence(command: str = "2d Marine Division") -> dict[str, Any]:
    return {
        "resolved_value": {"from": f"Commanding Officer, {command}"},
        "source_tier": "official_live",
        "source_title": f"{command} Official .mil Page",
        "source_url": "https://www.example.navy.mil/example-command",
        "confidence": 0.80,
    }


def conflicting_results(command: str = "2d Marine Division") -> list[dict[str, Any]]:
    return [
        {
            "resolved_value": {"from": f"Commanding Officer, {command}"},
            "source_tier": "official_live",
            "source_title": "Official Page A",
            "source_url": "https://www.example.navy.mil/A",
            "confidence": 0.92,
        },
        {
            "resolved_value": {"from": f"Commander, {command}"},
            "source_tier": "official_live",
            "source_title": "Official Page B",
            "source_url": "https://www.example.navy.mil/B",
            "confidence": 0.92,
        },
    ]


def install_provider(results: list[dict[str, Any]]) -> FakeProvider:
    enable()
    provider = FakeProvider(results)
    adapter.set_official_command_search_provider(provider)
    return provider


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    return pending[-1] if pending else None


# ── Test cases ─────────────────────────────────────────────────────────────


def test_quiet_suggestion_no_auto_apply() -> None:
    """Clean From candidate appears as quiet suggestion, not auto-applied."""
    install_provider([from_complete()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)
    ar = result.get("assistant_response", "")

    check("L32N From candidate is pending", isinstance(cand, dict) and cand.get("field") == "from")
    check("L32N From value not auto-applied", payload.get("from") != "Commanding Officer, 2d Marine Division")
    check("L32N Letterhead not auto-applied", payload.get("letterhead_activity") is None)
    check("L32N assistant_response is non-empty", bool(ar))
    check("L32N suggestion appears quietly", "source-backed suggestion" in ar or "confirm candidate" in ar)
    check("L32N response also prompts next step", "What date" in ar or "Keep providing" in ar or "Tell me" in ar or "body" in ar.lower())
    check("L32N no forced confirmation prompt", "Confirm before I apply" not in ar)


def test_explicit_confirm_still_works() -> None:
    """User can still explicitly confirm/apply the suggested candidate later."""
    install_provider([from_complete()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}

    check("L32N Confirm applies From", payload.get("from") == "Commanding Officer, 2d Marine Division")
    check("L32N Confirm applies complete letterhead_top_line", payload.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("L32N Confirm applies complete letterhead_activity", payload.get("letterhead_activity") == "HEADQUARTERS 2D MARINE DIVISION")
    check("L32N Confirm applies complete letterhead_address", payload.get("letterhead_address") == "CAMP LEJEUNE NC 28542-0000")


def test_from_incomplete_letterhead_suggests_from_only() -> None:
    """Incomplete From letterhead: candidate suggests From only, no letterhead."""
    install_provider([from_incomplete()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    cand = latest_pending(result)
    payload = result.get("payload") or {}

    check("L32N Incomplete From candidate pending", isinstance(cand, dict))
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32N Incomplete From suggests From only", rv.get("from") == "Commanding Officer, 2d Marine Division")
        check("L32N Incomplete From does not suggest letterhead_activity", "letterhead_activity" not in rv)
        check("L32N Incomplete From does not suggest letterhead_address", "letterhead_address" not in rv)
    check("L32N Incomplete From not auto-applied", payload.get("letterhead_activity") is None)


def test_to_suggests_to_only_strips_letterhead() -> None:
    """To candidate suggests To only; strips letterhead and unit_identity."""
    install_provider([from_complete(), to_with_bogus_letterhead()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Commanding Officer, Marine Corps Air Station New River to 2d Marine Division about training.",
    )
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    to_cand = next((c for c in pending if c.get("field") == "to"), None)

    check("L32N To candidate is pending", isinstance(to_cand, dict))
    if isinstance(to_cand, dict):
        rv = to_cand.get("resolved_value") or {}
        check("L32N To suggests To only", rv.get("to") == "Commanding Officer, 2d Marine Division")
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
            check(f"L32N To strips {key}", key not in rv, f"rv={rv!r}")


def test_low_confidence_fails_closed() -> None:
    """Low-confidence official result does not become a quiet suggestion."""
    install_provider([low_confidence()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    cand = latest_pending(result)
    check("L32N Low confidence returns no pending candidate", cand is None, f"cand={cand!r}")


def test_conflict_fails_closed_or_asks_clarification() -> None:
    """Conflicting official results do not quietly suggest as resolved."""
    install_provider(conflicting_results())
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to II MEF about training.",
    )
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    check("L32N Conflicting results not quietly suggested", all(c.get("field") != "from" for c in pending), f"pending={pending!r}")


def test_l30y_approval_revise_preserved() -> None:
    """L.30Y approval/revise behavior remains intact with non-intrusive suggestions."""
    install_provider([from_complete()])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

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
    check("L32N L30Y approval current", approved.get("approved_ready") is True)

    revised = hermes.send_secnav_chat_turn(
        chat_id,
        "change the body to say: This letter directs a review of training readiness and immediate updates.",
    )
    check("L32N L30Y revise clears approval", revised.get("approval_cleared") is True)
    check("L32N L30Y revise payload_changed", revised.get("payload_changed") is True)

    after = hermes.send_secnav_chat_turn(chat_id, "status")
    check("L32N L30Y approved_ready false after revise", after.get("approved_ready") is False)


def test_no_static_db_no_search_no_auto_apply() -> None:
    """No static command database, no web search, no auto-apply."""
    src = Path(adapter.__file__).read_text(encoding="utf-8")
    check("L32N no search engine APIs in adapter", "google.com" not in src and "bing.com" not in src and "duckduckgo" not in src)
    check("L32N no static command database in adapter", "OFFICIAL_COMMAND_DATABASE" not in src)


def main() -> int:
    tests = [
        test_quiet_suggestion_no_auto_apply,
        test_explicit_confirm_still_works,
        test_from_incomplete_letterhead_suggests_from_only,
        test_to_suggests_to_only_strips_letterhead,
        test_low_confidence_fails_closed,
        test_conflict_fails_closed_or_asks_clarification,
        test_l30y_approval_revise_preserved,
        test_no_static_db_no_search_no_auto_apply,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32N official lookup non-intrusive suggestion smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
