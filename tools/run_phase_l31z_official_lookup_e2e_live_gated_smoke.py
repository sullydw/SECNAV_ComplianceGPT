#!/usr/bin/env python3
"""Phase L.31Z smoke: official lookup end-to-end live-gated flow.

This smoke is deterministic.  It uses injected fake providers and does not
perform live internet access.  It proves the full Hermes chat path remains
live-gated, source-backed, candidate-only, and confirmation-based.
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
    """Deterministic fake provider used by the live-gated adapter."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]:
        self.calls.append((role, command_text))
        return self.results


def install_provider(results: list[dict[str, Any]], *, enabled: bool = True) -> FakeProvider:
    if enabled:
        os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    else:
        os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    provider = FakeProvider(results)
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    return provider


def disable_lookup_with_provider(results: list[dict[str, Any]]) -> FakeProvider:
    return install_provider(results, enabled=False)


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def pending_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(((result.get("source_backed_candidates") or {}).get("pending") or []))


def rejected_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(((result.get("source_backed_candidates") or {}).get("rejected") or []))


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = pending_candidates(result)
    return pending[-1] if pending else None


def official_from_result(*, complete_letterhead: bool = True) -> dict[str, Any]:
    resolved: dict[str, Any] = {"from": "Commanding Officer, Naval Example Command"}
    if complete_letterhead:
        resolved.update(
            {
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            }
        )
    return {
        "resolved_value": resolved,
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official .mil Page",
        "source_url": "https://www.example.navy.mil/naval-example-command",
        "confidence": 0.92,
    }


def official_to_result_with_bogus_letterhead() -> dict[str, Any]:
    return {
        "resolved_value": {
            "to": "Commanding Officer, Naval Example Command",
            "letterhead_top_line": "BOGUS LETTERHEAD",
            "letterhead_activity": "BOGUS ACTIVITY",
            "letterhead_address": "BOGUS ADDRESS",
            "unit_identity": "BOGUS UNIT",
        },
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official .mil Page",
        "source_url": "https://www.example.navy.mil/naval-example-command",
        "confidence": 0.92,
    }


def request_from_unknown_to_controlled() -> str:
    return "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures."


def request_from_controlled_to_unknown() -> str:
    return "I need a standard letter from MCAS Cherry Point to Naval Example Command about reviewing correspondence procedures."


# ── S1: Default live lookup remains disabled ──────────────────────────────


def test_s1_default_disabled_no_provider_call() -> None:
    provider = disable_lookup_with_provider([official_from_result()])
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    payload = result.get("payload") or {}

    check("S1 provider not called when disabled", provider.calls == [])
    check("S1 no pending candidate", latest_pending(result) is None)
    check("S1 literal From preserved", payload.get("from") == "Naval Example Command")
    check("S1 controlled To still expands", payload.get("to") == "Commanding General, II Marine Expeditionary Force")
    check("S1 no invented letterhead", not payload.get("letterhead_top_line"))

    direct = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S1 direct adapter disabled returns None", direct is None)


# ── S2/S3: Full From candidate E2E ────────────────────────────────────────


def test_s2_s3_full_from_candidate_e2e() -> None:
    provider = install_provider([official_from_result(complete_letterhead=True)], enabled=True)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    payload = result.get("payload") or {}
    cand = latest_pending(result)
    response = str(result.get("assistant_response") or "")

    check("S2 provider called when enabled", bool(provider.calls))
    check("S2 pending From candidate exists", isinstance(cand, dict) and cand.get("field") == "from")
    check("S2 From remains literal before confirmation", payload.get("from") == "Naval Example Command")
    check("S2 no letterhead before confirmation", not payload.get("letterhead_top_line"))
    check("S2 candidate provenance type", cand is not None and cand.get("candidate_type") == "command_expansion")
    check("S2 candidate provenance input", cand is not None and cand.get("input_text") == "Naval Example Command")
    check("S2 candidate provenance tier", cand is not None and cand.get("source_tier") == "official_live")
    check("S2 candidate provenance title", bool(cand and cand.get("source_title")))
    check("S2 candidate provenance url", bool(cand and cand.get("source_url")))
    check("S2 candidate confirmation required", cand is not None and cand.get("requires_user_confirmation") is True)
    check("S2 assistant response says From candidate", "From candidate" in response)
    check("S2 assistant response has source title", cand is not None and str(cand.get("source_title")) in response)
    check("S2 assistant response has resolved value", "Commanding Officer, Naval Example Command" in response)
    check("S2 assistant response requires confirmation", "Confirm" in response or "confirmation" in response)

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S3 confirmation succeeds", bool(confirmed.get("success")))
    check("S3 From mutates after confirmation", payload2.get("from") == "Commanding Officer, Naval Example Command")
    check("S3 letterhead top applies", payload2.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("S3 letterhead activity applies", payload2.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND")
    check("S3 letterhead address applies", payload2.get("letterhead_address") == "NORFOLK VA 23511-0000")
    check("S3 controlled To remains", payload2.get("to") == "Commanding General, II Marine Expeditionary Force")
    check("S3 no premature approval", not bool(confirmed.get("approved_ready")))


# ── S4: Full To candidate E2E ─────────────────────────────────────────────


def test_s4_full_to_candidate_e2e() -> None:
    provider = install_provider([official_to_result_with_bogus_letterhead()], enabled=True)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_controlled_to_unknown())
    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check("S4 provider called for To", any(role == "to" for role, _ in provider.calls))
    check("S4 From controlled expands", payload.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S4 From controlled letterhead applies", payload.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")
    check("S4 To remains literal before confirmation", payload.get("to") == "Naval Example Command")
    check("S4 pending To candidate exists", isinstance(cand, dict) and cand.get("field") == "to")
    resolved = (cand or {}).get("resolved_value") or {}
    check("S4 To resolved value present", resolved.get("to") == "Commanding Officer, Naval Example Command")
    check("S4 To candidate strips top line", "letterhead_top_line" not in resolved)
    check("S4 To candidate strips activity", "letterhead_activity" not in resolved)
    check("S4 To candidate strips address", "letterhead_address" not in resolved)
    check("S4 To candidate strips unit_identity", "unit_identity" not in resolved)

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S4 To confirmation succeeds", bool(confirmed.get("success")))
    check("S4 To mutates after confirmation", payload2.get("to") == "Commanding Officer, Naval Example Command")
    check("S4 From unchanged after To confirmation", payload2.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point")
    check("S4 From letterhead preserved", payload2.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT")
    check("S4 bogus To letterhead not applied", payload2.get("letterhead_top_line") == "UNITED STATES MARINE CORPS")


# ── S5: Rejection path E2E ────────────────────────────────────────────────


def test_s5_rejection_e2e() -> None:
    install_provider([official_from_result()], enabled=True)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    cand = latest_pending(result)
    check("S5 pending candidate created", isinstance(cand, dict))

    rejected = hermes.send_secnav_chat_turn(chat_id, "reject candidate")
    check("S5 rejection succeeds", bool(rejected.get("success")))
    check("S5 rejected candidate recorded", len(rejected_candidates(rejected)) >= 1)

    # After rejection, the literal From should still be in the state.
    # The reject response doesn't include payload, so verify via a follow-up turn.
    repeated = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    payload2 = repeated.get("payload") or {}
    check("S5 literal From preserved after rejection", payload2.get("from") == "Naval Example Command")
    check("S5 no immediate re-suggestion", latest_pending(repeated) is None)
    check("S5 literal preserved after repeat", payload2.get("from") == "Naval Example Command")


# ── S6: Conflict path E2E ─────────────────────────────────────────────────


def test_s6_conflict_e2e() -> None:
    install_provider(
        [
            official_from_result(),
            {
                "resolved_value": {"from": "Commander, Naval Example Command"},
                "source_tier": "official_live",
                "source_title": "Conflicting Official .mil Page",
                "source_url": "https://www.example.navy.mil/naval-example-command-alt",
                "confidence": 0.91,
            },
        ],
        enabled=True,
    )
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    payload = result.get("payload") or {}
    check("S6 no apply-ready pending candidate", latest_pending(result) is None)
    check("S6 literal From preserved", payload.get("from") == "Naval Example Command")
    check("S6 no invented letterhead", not payload.get("letterhead_top_line"))
    check("S6 normal prompt continues", bool(result.get("assistant_response")))


# ── S7: Incomplete From letterhead E2E ────────────────────────────────────


def test_s7_incomplete_from_letterhead_e2e() -> None:
    install_provider([official_from_result(complete_letterhead=False)], enabled=True)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    cand = latest_pending(result)
    resolved = (cand or {}).get("resolved_value") or {}
    check("S7 pending From candidate exists", isinstance(cand, dict) and cand.get("field") == "from")
    check("S7 no letterhead in candidate", "letterhead_top_line" not in resolved and "letterhead_activity" not in resolved and "letterhead_address" not in resolved)
    check("S7 limitation explains letterhead", "letterhead" in str((cand or {}).get("source_limitation", "")).lower())

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}
    check("S7 confirmation succeeds", bool(confirmed.get("success")))
    check("S7 From mutates only", payload.get("from") == "Commanding Officer, Naval Example Command")
    check("S7 no letterhead after confirmation", not payload.get("letterhead_top_line"))
    # After confirming incomplete From, the system should still ask for letterhead.
    # Check assistant_response or next_step for letterhead mention.
    resp = str(confirmed.get("assistant_response") or confirmed.get("next_step") or "").lower()
    check("S7 still requires letterhead before render", "letterhead" in resp or not bool(confirmed.get("validation_ready")))


# ── S8: Full render E2E ───────────────────────────────────────────────────


def test_s8_full_render_e2e() -> None:
    install_provider([official_from_result(complete_letterhead=True)], enabled=True)
    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(chat_id, request_from_unknown_to_controlled())
    check("S8 pending candidate exists", latest_pending(result) is not None)

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    check("S8 candidate confirmation succeeds", bool(confirmed.get("success")))

    details = hermes.send_secnav_chat_turn(
        chat_id,
        "date: 13 Aug 2026\nsignature: J. A. DOE\nbody: This letter directs a review of correspondence procedures.",
    )
    check("S8 details accepted", bool(details.get("success")))
    check("S8 draft preview reached", details.get("phase") in {"draft_preview", "approved_ready"})
    check("S8 validation ready", bool(details.get("validation_ready")))

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("S8 approval succeeds", bool(approved.get("success")))
    check("S8 approved ready", bool(approved.get("approved_ready")))

    rendered = hermes.send_secnav_chat_turn(chat_id, "make the PDF")
    payload = rendered.get("payload") or {}
    pdf_path = Path(str(rendered.get("pdf_path") or ""))
    check("S8 render succeeds", bool(rendered.get("success")))
    check("S8 rendered phase", rendered.get("phase") == "rendered")
    check("S8 PDF path present", bool(rendered.get("pdf_path")))
    check("S8 PDF exists", pdf_path.exists() if str(pdf_path) else False)
    check("S8 payload has source-backed From", payload.get("from") == "Commanding Officer, Naval Example Command")
    check("S8 payload has source-backed letterhead", payload.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND")
    check("S8 payload has controlled To", payload.get("to") == "Commanding General, II Marine Expeditionary Force")
    check("S8 payload has body", "correspondence procedures" in str(payload.get("body") or "").lower())
    check("S8 payload has signature", "J. A. DOE" in str(payload.get("signature") or ""))


# ── S9: No static database proof ──────────────────────────────────────────


def test_s9_no_static_database_proof() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(None)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    direct = adapter.official_command_lookup("Totally Unknown Naval Command", "from", {})
    check("S9 no provider returns None", direct is None)

    provider = disable_lookup_with_provider([official_from_result()])
    direct2 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S9 disabled with provider still returns None", direct2 is None)
    check("S9 disabled direct did not call provider", provider.calls == [])


# ── Runner ────────────────────────────────────────────────────────────────


def main() -> int:
    tests = [
        test_s1_default_disabled_no_provider_call,
        test_s2_s3_full_from_candidate_e2e,
        test_s4_full_to_candidate_e2e,
        test_s5_rejection_e2e,
        test_s6_conflict_e2e,
        test_s7_incomplete_from_letterhead_e2e,
        test_s8_full_render_e2e,
        test_s9_no_static_database_proof,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    print(f"\nL.31Z official lookup E2E live-gated smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
