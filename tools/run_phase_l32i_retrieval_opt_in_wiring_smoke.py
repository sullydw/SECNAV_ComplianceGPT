#!/usr/bin/env python3
"""Phase L.32I smoke: official provider retrieval opt-in wiring.

Deterministic smoke.  Exercises the explicit opt-in wiring helper that builds
and registers a live provider skeleton.  No real internet, no filesystem
lookup, no search engine, and no static command database.
"""

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import official_command_lookup_adapter as adapter  # noqa: E402
import official_command_provider as provider_module  # noqa: E402

PASS = 0
FAIL = 0
ALLOWED_URL = "https://www.example.navy.mil/naval-example-command"
DISALLOWED_URL = "https://en.wikipedia.org/wiki/Naval_Example_Command"


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


class FakeFetcher:
    def __init__(self, text: str = "official page text", exc: Exception | None = None) -> None:
        self.text = text
        self.exc = exc
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        if self.exc is not None:
            raise self.exc
        return self.text


class FakeParser:
    def __init__(self, results: list[dict[str, Any]] | None = None) -> None:
        self.results = results or [valid_result()]
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(self, command_text: str, role: str, url: str, page_text: str) -> list[dict[str, Any]]:
        self.calls.append((command_text, role, url, page_text))
        return [dict(item) for item in self.results]


def valid_result(*, with_letterhead: bool = True) -> dict[str, Any]:
    resolved: dict[str, Any] = {"from": "Commanding Officer, Naval Example Command"}
    if with_letterhead:
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
        "source_url": ALLOWED_URL,
        "confidence": 0.92,
    }


def valid_to_result() -> dict[str, Any]:
    return {
        "resolved_value": {
            "to": "Commanding Officer, Naval Example Command",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
            "letterhead_activity": "NAVAL EXAMPLE COMMAND",
            "letterhead_address": "NORFOLK VA 23511-0000",
        },
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official .mil Page",
        "source_url": ALLOWED_URL,
        "confidence": 0.92,
    }


def from_fixture() -> dict[str, Any]:
    return {
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
        "source_url": ALLOWED_URL,
        "confidence": 0.92,
    }


def enable_gate() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable_gate() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


# S1 — helper returns live provider instance

def test_s1_helper_returns_provider() -> None:
    provider = adapter.build_and_register_live_official_command_provider()
    check("S1 helper returns provider", provider is not None)
    check("S1 provider is callable", callable(provider))
    check("S1 provider is live retriever", isinstance(provider, provider_module.OfficialCommandLiveRetriever))


# S2 — helper registers provider with adapter

def test_s2_helper_registers_provider() -> None:
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    enable_gate()
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S2 registered provider returns candidate", isinstance(cand, dict))
    check("S2 fetcher called through adapter", len(fetcher.calls) == 1)


# S3 — helper does not enable live gate

def test_s3_helper_does_not_enable_gate() -> None:
    disable_gate()
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=FakeFetcher("page"),
        parser=FakeParser([valid_result()]),
    )
    check("S3 gate remains unset", not adapter.official_lookup_enabled({}))


# S4 — gate unset blocks provider/fetcher

def test_s4_gate_unset_blocks() -> None:
    disable_gate()
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S4 gate unset returns None", cand is None)
    check("S4 fetcher not called", fetcher.calls == [])
    check("S4 parser not called", parser.calls == [])


# S5 — gate enabled + enable_network=False returns None/no fetch

def test_s5_gate_enabled_network_disabled() -> None:
    enable_gate()
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    adapter.build_and_register_live_official_command_provider(
        enable_network=False,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S5 network disabled returns None", cand is None)
    check("S5 fetcher not called", fetcher.calls == [])
    check("S5 parser not called", parser.calls == [])


# S6 — gate enabled + enable_network=True + fake fetcher/parser returns candidate

def test_s6_gate_enabled_network_enabled() -> None:
    enable_gate()
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S6 candidate returned", isinstance(cand, dict))
    check("S6 fetcher called once", len(fetcher.calls) == 1)
    check("S6 parser called once", len(parser.calls) == 1)


# S7 — candidate remains confirmation-required

def test_s7_candidate_confirmation_required() -> None:
    enable_gate()
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=FakeFetcher("page"),
        parser=FakeParser([valid_result()]),
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S7 candidate confirmation required", cand is not None and cand.get("requires_user_confirmation") is True)


# S8 — candidate source metadata present

def test_s8_candidate_source_metadata() -> None:
    enable_gate()
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=FakeFetcher("page"),
        parser=FakeParser([valid_result()]),
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S8 source_tier official_live", cand is not None and cand.get("source_tier") == "official_live")
    check("S8 source_url present", cand is not None and cand.get("source_url") == ALLOWED_URL)
    check("S8 source_title present", cand is not None and bool(cand.get("source_title")))


# S9 — To candidate strips letterhead through adapter filter

def test_s9_to_candidate_strips_letterhead() -> None:
    enable_gate()
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=FakeFetcher("page"),
        parser=FakeParser([valid_to_result()]),
    )
    cand = adapter.official_command_lookup("Naval Example Command", "to", {})
    check("S9 To candidate returned", isinstance(cand, dict))
    rv = (cand or {}).get("resolved_value") or {}
    check("S9 To field present", bool(rv.get("to")))
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
        check(f"S9 no {key} in To candidate", key not in rv)


# S10 — disallowed candidate URL prevents fetch

def test_s10_disallowed_url_no_fetch() -> None:
    enable_gate()
    fetcher = FakeFetcher("page")
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[DISALLOWED_URL],
        fetcher=fetcher,
        parser=FakeParser([valid_result()]),
    )
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S10 disallowed URL returns None", cand is None)
    check("S10 disallowed URL no fetch", fetcher.calls == [])


# S11 — clearing provider still works

def test_s11_clearing_provider() -> None:
    enable_gate()
    adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=FakeFetcher("page"),
        parser=FakeParser([valid_result()]),
    )
    adapter.register_official_command_provider(None)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S11 cleared provider returns None", cand is None)


# S12 — old fixture registration still works

def test_s12_fixture_registration() -> None:
    enable_gate()
    provider = adapter.register_fixture_official_command_provider([from_fixture()])
    check("S12 fixture provider returned", provider is not None)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S12 fixture candidate returned", isinstance(cand, dict))


# S13 — no automatic runtime registration on import

def test_s13_no_automatic_registration() -> None:
    disable_gate()
    adapter.register_official_command_provider(None)
    # Importing the modules must not have registered a live provider.
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S13 no auto-registered provider", cand is None)
    src = inspect.getsource(adapter)
    check("S13 no import-time build call", "build_and_register_live_official_command_provider(" not in src.replace("def build_and_register_live_official_command_provider(", ""))


# S14 — no static DB/no real network proof

def test_s14_no_static_db_no_network() -> None:
    src = inspect.getsource(adapter)
    for token in ("import requests", "urllib.request", "http.client", "import socket", "socket."):
        check(f"S14 adapter no {token}", token not in src)
    check("S14 adapter no command database", "COMMAND_DATABASE" not in src and "STATIC_COMMAND" not in src)
    helper_src = inspect.getsource(adapter.build_and_register_live_official_command_provider)
    check("S14 helper does not set gate env", "os.environ" not in helper_src and "os.getenv" not in helper_src and "os.putenv" not in helper_src)


def main() -> int:
    tests = [
        test_s1_helper_returns_provider,
        test_s2_helper_registers_provider,
        test_s3_helper_does_not_enable_gate,
        test_s4_gate_unset_blocks,
        test_s5_gate_enabled_network_disabled,
        test_s6_gate_enabled_network_enabled,
        test_s7_candidate_confirmation_required,
        test_s8_candidate_source_metadata,
        test_s9_to_candidate_strips_letterhead,
        test_s10_disallowed_url_no_fetch,
        test_s11_clearing_provider,
        test_s12_fixture_registration,
        test_s13_no_automatic_registration,
        test_s14_no_static_db_no_network,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    adapter.register_official_command_provider(None)
    disable_gate()
    print(f"\nL.32I retrieval opt-in wiring smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
