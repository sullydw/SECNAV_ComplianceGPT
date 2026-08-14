#!/usr/bin/env python3
"""Phase L.32C smoke: official provider adapter registration.

This smoke is deterministic.  It uses the registration helpers and
FixtureOfficialCommandProvider; no internet access is performed.
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

import official_command_lookup_adapter as adapter  # noqa: E402
import official_command_provider as provider_mod  # noqa: E402

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


# ── Counting wrapper for call tracking ─────────────────────────────────────


class CountingProvider:
    """Wraps a real provider and counts calls."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> Any:
        self.calls.append((role, command_text))
        return self._inner(command_text, role, state)


# ── Fixtures ───────────────────────────────────────────────────────────────

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


def cleanup() -> None:
    adapter.set_official_command_search_provider(None)
    adapter.reset_official_command_lookup_cache()
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)


# ── S1: register provider delegates to adapter ────────────────────────────


def test_s1_register_delegates() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    base = provider_mod.build_fixture_provider([FROM_FIXTURE])
    counting = CountingProvider(base)
    adapter.register_official_command_provider(counting)

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S1 adapter returns candidate", isinstance(result, dict))
    check("S1 resolved from", (result or {}).get("resolved_value", {}).get("from") == "Commanding Officer, Naval Example Command")
    check("S1 provider called", len(counting.calls) >= 1)
    cleanup()


# ── S2: registration does not enable live lookup ──────────────────────────


def test_s2_registration_no_gate() -> None:
    cleanup()
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    base = provider_mod.build_fixture_provider([FROM_FIXTURE])
    counting = CountingProvider(base)
    adapter.register_official_command_provider(counting)

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S2 adapter returns None when gate unset", result is None)
    check("S2 provider not called", counting.calls == [])
    cleanup()


# ── S3: clearing provider works ───────────────────────────────────────────


def test_s3_clearing_provider() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    base = provider_mod.build_fixture_provider([FROM_FIXTURE])
    counting = CountingProvider(base)
    adapter.register_official_command_provider(counting)

    result1 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S3 before clear returns candidate", isinstance(result1, dict))
    calls_before = len(counting.calls)

    adapter.register_official_command_provider(None)
    adapter.reset_official_command_lookup_cache()
    result2 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S3 after clear returns None", result2 is None)
    check("S3 no new calls after clear", len(counting.calls) == calls_before)
    cleanup()


# ── S4: fixture registration helper works ──────────────────────────────────


def test_s4_fixture_registration_helper() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    prov = adapter.register_fixture_official_command_provider([FROM_FIXTURE])

    check("S4 returned instance is FixtureOfficialCommandProvider", isinstance(prov, provider_mod.FixtureOfficialCommandProvider))
    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S4 adapter returns result from fixture", isinstance(result, dict))
    check("S4 resolved from", (result or {}).get("resolved_value", {}).get("from") == "Commanding Officer, Naval Example Command")
    cleanup()


# ── S5: fixture registration helper does not enable gate ───────────────────


def test_s5_fixture_registration_no_gate() -> None:
    cleanup()
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    prov = adapter.register_fixture_official_command_provider([FROM_FIXTURE])

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S5 adapter returns None when gate unset", result is None)

    # Direct provider call still works
    direct = list(prov("Naval Example Command", "from", {}))
    check("S5 direct provider call returns fixture", len(direct) == 1)
    check("S5 direct result has from", direct[0]["resolved_value"]["from"] == "Commanding Officer, Naval Example Command")
    cleanup()


# ── S6: role distinction through registration ─────────────────────────────


def test_s6_role_distinction_registration() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.register_fixture_official_command_provider([FROM_FIXTURE, TO_FIXTURE])

    from_result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S6 from returns candidate", isinstance(from_result, dict))
    check("S6 from has from field", "from" in (from_result or {}).get("resolved_value", {}))

    to_result = adapter.official_command_lookup("Naval Example Command", "to", {})
    check("S6 to returns candidate", isinstance(to_result, dict))
    to_resolved = (to_result or {}).get("resolved_value") or {}
    check("S6 to has to field", "to" in to_resolved)
    check("S6 to has no letterhead_top_line", "letterhead_top_line" not in to_resolved)
    cleanup()


# ── S7: invalid role through adapter returns None ─────────────────────────


def test_s7_invalid_role() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.register_fixture_official_command_provider([FROM_FIXTURE])

    result = adapter.official_command_lookup("Naval Example Command", "via", {})
    check("S7 invalid role returns None", result is None)
    cleanup()


# ── S8: missing provenance still rejected through registered provider ──────


def test_s8_missing_provenance_registered() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.register_fixture_official_command_provider([FROM_FIXTURE_NO_URL])

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S8 missing source_url returns None", result is None)
    cleanup()


# ── S9: multiple registered results preserve conflict behavior ────────────


def test_s9_conflict_through_registration() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.register_fixture_official_command_provider([FROM_FIXTURE, FROM_FIXTURE_ALT])

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S9 conflicting results return None", result is None)
    cleanup()


# ── S10: reset behavior is explicit ───────────────────────────────────────


def test_s10_reset_behavior() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    base = provider_mod.build_fixture_provider([FROM_FIXTURE])
    counting = CountingProvider(base)
    adapter.register_official_command_provider(counting)

    # Confirm provider works before reset
    result1 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S10 before reset returns candidate", isinstance(result1, dict))

    # reset_official_command_lookup_cache clears the cache but does NOT clear
    # the registered provider — that is the existing accepted behavior.
    adapter.reset_official_command_lookup_cache()
    result2 = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S10 after reset still returns candidate (provider persists)", isinstance(result2, dict))
    check("S10 provider called again after reset", len(counting.calls) >= 2)
    cleanup()


# ── S11: old setter still works ───────────────────────────────────────────


def test_s11_old_setter() -> None:
    cleanup()
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    base = provider_mod.build_fixture_provider([FROM_FIXTURE])
    adapter.set_official_command_search_provider(base)

    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S11 old setter returns candidate", isinstance(result, dict))
    check("S11 resolved from", (result or {}).get("resolved_value", {}).get("from") == "Commanding Officer, Naval Example Command")
    cleanup()


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    test_s1_register_delegates()
    test_s2_registration_no_gate()
    test_s3_clearing_provider()
    test_s4_fixture_registration_helper()
    test_s5_fixture_registration_no_gate()
    test_s6_role_distinction_registration()
    test_s7_invalid_role()
    test_s8_missing_provenance_registered()
    test_s9_conflict_through_registration()
    test_s10_reset_behavior()
    test_s11_old_setter()

    cleanup()
    print(f"\nL.32C official provider adapter registration smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
