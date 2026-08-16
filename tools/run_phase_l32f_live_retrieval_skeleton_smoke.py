#!/usr/bin/env python3
"""Phase L.32F smoke: official provider live retrieval skeleton.

Deterministic smoke.  Uses injected candidate URLs, injected fake fetchers, and
injected fake parsers only.  No real internet, no filesystem lookup, and no
static command database.
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
STATIC_URL = "static://commands/naval-example-command"
LOCALDB_URL = "localdb://naval-example-command"


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
    def __init__(self, results: list[dict[str, Any]] | None = None, exc: Exception | None = None) -> None:
        self.results = results or [valid_result()]
        self.exc = exc
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(self, command_text: str, role: str, url: str, page_text: str) -> list[dict[str, Any]]:
        self.calls.append((command_text, role, url, page_text))
        if self.exc is not None:
            raise self.exc
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


def enable_adapter() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable_adapter() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


# S1 — default live retriever returns empty and performs no network

def test_s1_default_empty_no_network() -> None:
    state: dict[str, Any] = {"sentinel": "unchanged"}
    provider = provider_module.build_live_provider()
    results = list(provider("Naval Example Command", "from", state))
    check("S1 default provider returns empty", results == [])
    check("S1 state unchanged", state == {"sentinel": "unchanged"})


# S2 — network disabled prevents injected fetcher call

def test_s2_network_disabled_blocks_fetcher() -> None:
    fetcher = FakeFetcher()
    parser = FakeParser()
    provider = provider_module.build_live_provider(
        enable_network=False,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    results = list(provider("Naval Example Command", "from", {}))
    check("S2 network disabled returns empty", results == [])
    check("S2 fetcher not called", fetcher.calls == [])
    check("S2 parser not called", parser.calls == [])


# S3 — enable_network=True allows injected fake fetcher only

def test_s3_enabled_fake_fetcher_parser() -> None:
    fetcher = FakeFetcher("deterministic official page")
    parser = FakeParser([valid_result()])
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    results = list(provider("Naval Example Command", "from", {}))
    check("S3 fetcher called once", len(fetcher.calls) == 1)
    check("S3 parser called once", len(parser.calls) == 1)
    check("S3 result returned", len(results) == 1)
    result = results[0] if results else {}
    for key in ("source_url", "source_title", "source_tier", "confidence", "resolved_value"):
        check(f"S3 result has {key}", bool(result.get(key)))


# S4 — disallowed URL precheck prevents fetch

def test_s4_disallowed_url_no_fetch() -> None:
    fetcher = FakeFetcher()
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[DISALLOWED_URL],
        fetcher=fetcher,
        parser=FakeParser(),
    )
    results = list(provider("Naval Example Command", "from", {}))
    check("S4 disallowed URL returns empty", results == [])
    check("S4 disallowed URL no fetch", fetcher.calls == [])


# S5 — pseudo URLs prevent fetch

def test_s5_pseudo_urls_no_fetch() -> None:
    fetcher = FakeFetcher()
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[STATIC_URL, LOCALDB_URL],
        fetcher=fetcher,
        parser=FakeParser(),
    )
    results = list(provider("Naval Example Command", "from", {}))
    check("S5 pseudo URLs return empty", results == [])
    check("S5 pseudo URLs no fetch", fetcher.calls == [])


# S6 — timeout clamp works

def test_s6_timeout_clamp() -> None:
    neg = provider_module.build_live_provider(timeout_seconds=-1)
    huge = provider_module.build_live_provider(timeout_seconds=999)
    invalid = provider_module.build_live_provider(timeout_seconds="not-a-number")
    check("S6 negative timeout uses default", neg.timeout_seconds == provider_module.DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)
    check("S6 invalid timeout uses default", invalid.timeout_seconds == provider_module.DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)
    check("S6 huge timeout clamps max", huge.timeout_seconds == provider_module.MAX_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)


# S7 — fetcher exception fails closed

def test_s7_fetcher_exception_fail_closed() -> None:
    fetcher = FakeFetcher(exc=RuntimeError("boom"))
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=FakeParser(),
    )
    check("S7 fetcher exception returns empty", list(provider("Naval Example Command", "from", {})) == [])
    check("S7 fetcher called once", len(fetcher.calls) == 1)


# S8 — timeout exception fails closed

def test_s8_timeout_exception_fail_closed() -> None:
    fetcher1 = FakeFetcher(exc=provider_module.OfficialCommandRetrievalTimeout("timeout"))
    provider1 = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher1,
        parser=FakeParser(),
    )
    check("S8 custom timeout returns empty", list(provider1("Naval Example Command", "from", {})) == [])

    fetcher2 = FakeFetcher(exc=TimeoutError("timeout"))
    provider2 = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher2,
        parser=FakeParser(),
    )
    check("S8 builtin timeout returns empty", list(provider2("Naval Example Command", "from", {})) == [])


# S9 — parser exception fails closed

def test_s9_parser_exception_fail_closed() -> None:
    fetcher = FakeFetcher("page")
    parser = FakeParser(exc=RuntimeError("parse boom"))
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    check("S9 parser exception returns empty", list(provider("Naval Example Command", "from", {})) == [])
    check("S9 fetcher called", len(fetcher.calls) == 1)
    check("S9 parser called", len(parser.calls) == 1)


# S10 — empty page text returns empty

def test_s10_empty_page_returns_empty() -> None:
    fetcher = FakeFetcher("")
    parser = FakeParser()
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    check("S10 empty page returns empty", list(provider("Naval Example Command", "from", {})) == [])
    check("S10 parser not called", parser.calls == [])


# S11 — parser does not invent letterhead

def test_s11_parser_no_invented_letterhead() -> None:
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result(with_letterhead=False)])
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    results = list(provider("Naval Example Command", "from", {}))
    rv = (results[0] if results else {}).get("resolved_value") or {}
    check("S11 From result returned", rv.get("from") == "Commanding Officer, Naval Example Command")
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
        check(f"S11 no invented {key}", key not in rv)


# S12 — live provider compatible with adapter registration

def test_s12_adapter_registration_compatibility() -> None:
    enable_adapter()
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    adapter.register_official_command_provider(provider)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S12 adapter returns candidate", isinstance(cand, dict))
    check("S12 official_live tier", cand is not None and cand.get("source_tier") == "official_live")
    check("S12 confirmation required", cand is not None and cand.get("requires_user_confirmation") is True)
    check("S12 fetcher called through adapter", len(fetcher.calls) == 1)


# S13 — live provider still blocked by adapter gate

def test_s13_adapter_gate_blocks_provider() -> None:
    disable_adapter()
    fetcher = FakeFetcher("page")
    parser = FakeParser([valid_result()])
    provider = provider_module.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    adapter.register_official_command_provider(provider)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S13 adapter returns None with gate unset", cand is None)
    check("S13 fetcher not called", fetcher.calls == [])
    check("S13 parser not called", parser.calls == [])


# S14 — no static DB/no real network proof

def test_s14_no_static_db_no_real_network() -> None:
    src = inspect.getsource(provider_module)
    for token in ("import requests", "urllib.request", "http.client", "import socket", "socket."):
        check(f"S14 no {token}", token not in src)
    check("S14 no command database variable", "COMMAND_DATABASE" not in src and "STATIC_COMMAND" not in src)
    check("S14 default discovery empty", provider_module.discover_candidate_urls("Naval Example Command", "from", {}) == [])
    check("S14 empty provider returns empty", list(provider_module.build_live_provider()("Naval Example Command", "from", {})) == [])


def main() -> int:
    tests = [
        test_s1_default_empty_no_network,
        test_s2_network_disabled_blocks_fetcher,
        test_s3_enabled_fake_fetcher_parser,
        test_s4_disallowed_url_no_fetch,
        test_s5_pseudo_urls_no_fetch,
        test_s6_timeout_clamp,
        test_s7_fetcher_exception_fail_closed,
        test_s8_timeout_exception_fail_closed,
        test_s9_parser_exception_fail_closed,
        test_s10_empty_page_returns_empty,
        test_s11_parser_no_invented_letterhead,
        test_s12_adapter_registration_compatibility,
        test_s13_adapter_gate_blocks_provider,
        test_s14_no_static_db_no_real_network,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    adapter.register_official_command_provider(None)
    disable_adapter()
    print(f"\nL.32F live retrieval skeleton smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
