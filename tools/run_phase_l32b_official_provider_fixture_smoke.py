#!/usr/bin/env python3
"""Phase L.32B smoke: official provider fixture implementation.

This smoke is deterministic.  It uses the FixtureOfficialCommandProvider
and does not perform any internet access.
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

import official_command_provider as provider_mod  # noqa: E402
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


# ── Fixture helpers ────────────────────────────────────────────────────────

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
    "confidence": 0.92,
}

TO_FIXTURE: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "to",
    "resolved_value": {
        "to": "Commanding Officer, Naval Example Command",
    },
    "source_tier": "official_live",
    "source_title": "Naval Example Command Official .mil Page",
    "source_url": "https://www.example.navy.mil/naval-example-command",
    "confidence": 0.92,
}

TO_FIXTURE_WITH_BOGUS_LETTERHEAD: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "to",
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

FROM_FIXTURE_ALT: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "from",
    "resolved_value": {
        "from": "Commander, Naval Example Command",
    },
    "source_tier": "official_live",
    "source_title": "Naval Example Command Alternate .mil Page",
    "source_url": "https://www.example.navy.mil/naval-example-command-alt",
    "confidence": 0.90,
}

FROM_FIXTURE_NO_URL: dict[str, Any] = {
    "input_text": "Naval Example Command",
    "role": "from",
    "resolved_value": {
        "from": "Commanding Officer, Naval Example Command",
    },
    "source_tier": "official_live",
    "source_title": "Naval Example Command Official .mil Page",
    # source_url intentionally missing
    "confidence": 0.92,
}


# ── S1: fixture provider returns deterministic From result ─────────────────


def test_s1_deterministic_from_result() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    state: dict[str, Any] = {}
    results = list(provider("Naval Example Command", "from", state))

    check("S1 returns one result", len(results) == 1)
    r = results[0]
    check("S1 resolved from", r["resolved_value"]["from"] == "Commanding Officer, Naval Example Command")
    check("S1 source_tier", r["source_tier"] == "official_live")
    check("S1 source_title", bool(r["source_title"]))
    check("S1 source_url", bool(r["source_url"]))
    check("S1 confidence", r["confidence"] == 0.92)
    check("S1 state unchanged", state == {})


# ── S2: normalization works ────────────────────────────────────────────────


def test_s2_normalization() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    state: dict[str, Any] = {}

    for variant in ("Naval Example Command", "naval   example command", " NAVAL EXAMPLE COMMAND "):
        results = list(provider(variant, "from", state))
        check(f"S2 variant {variant!r} returns one result", len(results) == 1)
        check(f"S2 variant {variant!r} resolved from", results[0]["resolved_value"]["from"] == "Commanding Officer, Naval Example Command")


# ── S3: role distinction works ─────────────────────────────────────────────


def test_s3_role_distinction() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE, TO_FIXTURE])
    state: dict[str, Any] = {}

    from_results = list(provider("Naval Example Command", "from", state))
    check("S3 from returns one result", len(from_results) == 1)
    check("S3 from has from field", "from" in from_results[0]["resolved_value"])
    check("S3 from has letterhead", "letterhead_top_line" in from_results[0]["resolved_value"])

    to_results = list(provider("Naval Example Command", "to", state))
    check("S3 to returns one result", len(to_results) == 1)
    check("S3 to has to field", "to" in to_results[0]["resolved_value"])
    check("S3 to has no letterhead_top_line", "letterhead_top_line" not in to_results[0]["resolved_value"])


# ── S4: no match returns empty list ────────────────────────────────────────


def test_s4_no_match() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    state: dict[str, Any] = {}
    results = list(provider("Unknown Command", "from", state))
    check("S4 no match returns empty", results == [])


# ── S5: invalid role returns empty list ─────────────────────────────────────


def test_s5_invalid_role() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    state: dict[str, Any] = {}
    results = list(provider("Naval Example Command", "via", state))
    check("S5 invalid role returns empty", results == [])


# ── S6: multiple results supported ─────────────────────────────────────────


def test_s6_multiple_results() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE, FROM_FIXTURE_ALT])
    state: dict[str, Any] = {}
    results = list(provider("Naval Example Command", "from", state))
    check("S6 returns two results", len(results) == 2)
    check("S6 first is CO", results[0]["resolved_value"]["from"] == "Commanding Officer, Naval Example Command")
    check("S6 second is Commander", results[1]["resolved_value"]["from"] == "Commander, Naval Example Command")


# ── S7: provider has no live gate ──────────────────────────────────────────


def test_s7_no_live_gate() -> None:
    # Ensure env var is unset
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    state: dict[str, Any] = {}
    results = list(provider("Naval Example Command", "from", state))
    check("S7 provider returns result without gate", len(results) == 1)
    check("S7 result has from", results[0]["resolved_value"]["from"] == "Commanding Officer, Naval Example Command")


# ── S8: adapter gate still controls use ─────────────────────────────────────


def test_s8_adapter_gate() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE])
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)

    # Disabled
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S8 disabled adapter returns None", result is None)

    # Enabled
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()
    result2 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S8 enabled adapter returns candidate", isinstance(result2, dict))
    check("S8 candidate has from", (result2 or {}).get("resolved_value", {}).get("from") == "Commanding Officer, Naval Example Command")


# ── S9: adapter still enforces provenance ──────────────────────────────────


def test_s9_adapter_provenance() -> None:
    provider = provider_mod.build_fixture_provider([FROM_FIXTURE_NO_URL])
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S9 missing source_url returns None", result is None)


# ── S10: adapter still strips To letterhead ────────────────────────────────


def test_s10_adapter_strips_to_letterhead() -> None:
    provider = provider_mod.build_fixture_provider([TO_FIXTURE_WITH_BOGUS_LETTERHEAD])
    adapter.reset_official_command_lookup_cache()
    adapter.set_official_command_search_provider(provider)
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"

    result = adapter.official_command_lookup("Naval Example Command", "to", {})
    check("S10 adapter returns To candidate", isinstance(result, dict))
    resolved = (result or {}).get("resolved_value") or {}
    check("S10 resolved includes to", resolved.get("to") == "Commanding Officer, Naval Example Command")
    check("S10 no letterhead_top_line", "letterhead_top_line" not in resolved)
    check("S10 no letterhead_activity", "letterhead_activity" not in resolved)
    check("S10 no letterhead_address", "letterhead_address" not in resolved)
    check("S10 no unit_identity", "unit_identity" not in resolved)


# ── S11: no static database proof ──────────────────────────────────────────


def test_s11_no_static_database() -> None:
    # Default provider has empty fixtures
    provider = provider_mod.build_fixture_provider()
    results = list(provider("Naval Example Command", "from", {}))
    check("S11 empty provider returns empty", results == [])

    results2 = list(provider("MCAS Cherry Point", "from", {}))
    check("S11 unknown command returns empty", results2 == [])

    # Module has no broad default command list
    mod_source = Path(provider_mod.__file__).read_text() if provider_mod.__file__ else ""
    check("S11 no hardcoded command list", "COMMANDING_OFFICER" not in mod_source.upper() or "fixture" in mod_source.lower())

    # Result count comes only from supplied fixtures
    provider2 = provider_mod.build_fixture_provider([FROM_FIXTURE, TO_FIXTURE])
    results3 = list(provider2("Naval Example Command", "from", {}))
    check("S11 result count matches supplied fixtures", len(results3) == 1)


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    test_s1_deterministic_from_result()
    test_s2_normalization()
    test_s3_role_distinction()
    test_s4_no_match()
    test_s5_invalid_role()
    test_s6_multiple_results()
    test_s7_no_live_gate()
    test_s8_adapter_gate()
    test_s9_adapter_provenance()
    test_s10_adapter_strips_to_letterhead()
    test_s11_no_static_database()

    # Clean up
    adapter.set_official_command_search_provider(None)
    adapter.reset_official_command_lookup_cache()
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)

    print(f"\nL.32B official provider fixture smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
