#!/usr/bin/env python3
"""
Phase L.32L — Official Lookup Fixture Confirmation End-to-End Smoke

Proves that source-backed fixture candidates work end-to-end through the
Hermes chat builder after the L.30Y approval/revise cleanup:

- fixture official From candidate appears only as pending candidate
- no auto-apply before confirmation
- confirming From applies From and complete letterhead
- fixture official To candidate strips letterhead
- confirming To mutates only To
- approval/render workflow still passes after confirmation
- L.30Y approval/revise behavior remains intact

Deterministic.  Uses injected fixture providers only; no network access.
"""

from __future__ import annotations

import os
import sys
import uuid
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


# ── Fixture definitions ────────────────────────────────────────────────────

FROM_FIXTURE: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "from",
    "resolved_value": {
        "from": "Commanding Officer, Naval Example Command",
        "letterhead_top_line": "DEPARTMENT OF THE NAVY",
        "letterhead_activity": "NAVAL EXAMPLE COMMAND",
        "letterhead_address": "NORFOLK VA 23511-0000",
    },
    "source_tier": "official_live",
    "source_title": "Naval Example Command Official .mil Page",
    "source_url": "https://www.example.navy.mil/naval-example-command",
    "source_limitation": "Official-source candidate; user confirmation required before applying.",
    "confidence": 0.92,
}

TO_FIXTURE: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "to",
    "resolved_value": {
        "to": "Commanding Officer, Naval Example Command",
        "letterhead_top_line": "BOGUS TOP",
        "letterhead_activity": "BOGUS ACTIVITY",
        "letterhead_address": "BOGUS ADDRESS",
        "unit_identity": "BOGUS UNIT",
    },
    "source_tier": "official_live",
    "source_title": "Naval Example Command Official .mil Page",
    "source_url": "https://www.example.navy.mil/naval-example-command",
    "source_limitation": "To-line candidates do not set letterhead; confirmation mutates only the To field.",
    "confidence": 0.92,
}


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    return pending[-1] if pending else None


def latest_confirmed(result: dict[str, Any]) -> dict[str, Any] | None:
    confirmed = list(((result.get("source_backed_candidates") or {}).get("confirmed") or []))
    return confirmed[-1] if confirmed else None


def is_candidate_displayed(result: dict[str, Any], *, field: str = "from") -> bool:
    c = latest_pending(result)
    return isinstance(c, dict) and c.get("field") == field


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


# ── Test cases ─────────────────────────────────────────────────────────────


def test_from_fixture_pending_only() -> None:
    """Fixture official From candidate appears only as pending candidate; no auto-apply."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )

    payload = result.get("payload") or {}
    cand = latest_pending(result)

    check(
        "L32L From candidate appears as pending",
        isinstance(cand, dict) and cand.get("field") == "from",
        f"pending={cand!r}",
    )
    check(
        "L32L From candidate is official_live",
        isinstance(cand, dict) and cand.get("source_tier") == "official_live",
    )
    check(
        "L32L From value is not auto-applied before confirmation",
        payload.get("from") != "Commanding Officer, Naval Example Command",
        f"from={payload.get('from')!r}",
    )
    check(
        "L32L Letterhead is not auto-applied before confirmation",
        payload.get("letterhead_activity") is None,
        f"letterhead_activity={payload.get('letterhead_activity')!r}",
    )


def test_from_confirmation_applies_from_and_letterhead() -> None:
    """Confirming From applies From and complete letterhead."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")

    payload = confirmed.get("payload") or {}
    check(
        "L32L Confirm From applies From",
        payload.get("from") == "Commanding Officer, Naval Example Command",
        f"from={payload.get('from')!r}",
    )
    check(
        "L32L Confirm From applies letterhead_top_line",
        payload.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY",
    )
    check(
        "L32L Confirm From applies letterhead_activity",
        payload.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND",
    )
    check(
        "L32L Confirm From applies letterhead_address",
        payload.get("letterhead_address") == "NORFOLK VA 23511-0000",
    )

    moved = latest_confirmed(confirmed)
    check(
        "L32L From candidate moved to confirmed",
        isinstance(moved, dict) and moved.get("field") == "from",
    )


def test_to_fixture_strips_letterhead() -> None:
    """Fixture official To candidate strips letterhead."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE, TO_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Naval Example Command about training.",
    )

    # First candidate is From (controlled alias); To fixture should also appear pending.
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    to_cand = next((c for c in pending if c.get("field") == "to"), None)

    check(
        "L32L To candidate appears as pending",
        isinstance(to_cand, dict),
        f"pending={pending!r}",
    )
    if isinstance(to_cand, dict):
        resolved = to_cand.get("resolved_value") or {}
        check(
            "L32L To candidate resolved includes to",
            resolved.get("to") == "Commanding Officer, Naval Example Command",
        )
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
            check(f"L32L To candidate strips {key}", key not in resolved, f"resolved={resolved!r}")


def test_to_confirmation_mutates_only_to() -> None:
    """Confirming To mutates only To, not letterhead."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE, TO_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Naval Example Command about training.",
    )

    # Confirm the pending To candidate (expected to be the To fixture).
    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}

    check(
        "L32L Confirm To applies To",
        payload.get("to") == "Commanding Officer, Naval Example Command",
        f"to={payload.get('to')!r}",
    )
    check(
        "L32L Confirm To does not apply bogus letterhead_top_line",
        payload.get("letterhead_top_line") != "BOGUS TOP",
    )
    check(
        "L32L Confirm To does not apply bogus letterhead_activity",
        payload.get("letterhead_activity") != "BOGUS ACTIVITY",
    )
    check(
        "L32L Confirm To does not apply bogus letterhead_address",
        payload.get("letterhead_address") != "BOGUS ADDRESS",
    )
    check(
        "L32L Confirm To does not apply bogus unit_identity",
        payload.get("unit_identity") != "BOGUS UNIT",
    )


def test_approval_render_after_confirmation() -> None:
    """Approval/render workflow still passes after confirmation."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to Commanding General, II Marine Expeditionary Force about reviewing correspondence procedures.",
    )
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")

    details = hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of correspondence procedures.",
    )
    check(
        "L32L Draft reaches preview/ready after filling details",
        bool(details.get("success")) and details.get("phase") in {"draft_preview", "approved_ready"},
        f"phase={details.get('phase')!r}",
    )

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L32L Approval succeeds", bool(approved.get("success")))

    rendered = hermes.send_secnav_chat_turn(chat_id, "make the PDF")
    check(
        "L32L Render succeeds",
        bool(rendered.get("success")) and rendered.get("phase") == "rendered",
        f"phase={rendered.get('phase')!r}",
    )
    check(
        "L32L PDF path present",
        bool(rendered.get("pdf_path")),
        f"pdf_path={rendered.get('pdf_path')!r}",
    )

    pdf_path = Path(rendered.get("pdf_path") or "")
    if pdf_path:
        check("L32L PDF file exists", pdf_path.exists() and pdf_path.stat().st_size > 0)


def test_l30y_revise_clears_approval_after_confirmation() -> None:
    """L.30Y approval/revise behavior remains intact after official lookup confirmation."""
    enable()
    adapter.register_fixture_official_command_provider([FROM_FIXTURE])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to Commanding General, II Marine Expeditionary Force about reviewing correspondence procedures.",
    )
    hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE, Commanding Officer\nbody: This letter directs a review of correspondence procedures.",
    )

    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("L30Y Approval current after approve", approved.get("approved_ready") is True or (approved.get("payload") or {}).get("approved_ready") is True)

    revised = hermes.send_secnav_chat_turn(chat_id, "change the body to say: This letter directs a review of correspondence procedures and immediate updates.")
    check(
        "L30Y Revise after approval clears approval when body changes",
        revised.get("approval_cleared") is True,
        f"approval_cleared={revised.get('approval_cleared')!r}",
    )
    check(
        "L30Y Revise payload_changed is True",
        revised.get("payload_changed") is True,
        f"payload_changed={revised.get('payload_changed')!r}",
    )

    # Approval should not remain current after a body change.
    after = hermes.send_secnav_chat_turn(chat_id, "status")
    check(
        "L30Y Approved_ready false after revise clears approval",
        after.get("approved_ready") is False,
        f"approved_ready={after.get('approved_ready')!r}",
    )


def main() -> int:
    tests = [
        test_from_fixture_pending_only,
        test_from_confirmation_applies_from_and_letterhead,
        test_to_fixture_strips_letterhead,
        test_to_confirmation_mutates_only_to,
        test_approval_render_after_confirmation,
        test_l30y_revise_clears_approval_after_confirmation,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32L official lookup fixture confirmation smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
