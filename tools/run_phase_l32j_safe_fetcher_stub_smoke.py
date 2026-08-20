#!/usr/bin/env python3
"""Phase L.32J smoke: official provider safe fetcher stub.

Deterministic smoke. Uses injected fake transports only. No real internet,
no filesystem lookup, no environment gate mutation by the fetcher, and no
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
import official_command_provider as provider  # noqa: E402

PASS = 0
FAIL = 0
ALLOWED_URL = "https://www.example.navy.mil/naval-example-command"
DISALLOWED_URL = "https://en.wikipedia.org/wiki/Naval_Example_Command"
STATIC_URL = "static://commands/naval-example-command"
LOCALDB_URL = "localdb://naval-example-command"
PAGE_TEXT = """Title: Naval Example Command
From: Commanding Officer, Naval Example Command
Letterhead Top Line: DEPARTMENT OF THE NAVY
Letterhead Activity: NAVAL EXAMPLE COMMAND
Letterhead Address: NORFOLK VA 23511-0000
"""


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


class FakeTransport:
    def __init__(self, text: str = PAGE_TEXT, exc: Exception | None = None) -> None:
        self.text = text
        self.exc = exc
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        if self.exc is not None:
            raise self.exc
        return self.text


class FakeParser:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(self, command_text: str, role: str, url: str, page_text: str) -> list[dict[str, Any]]:
        self.calls.append((command_text, role, url, page_text))
        return provider.parse_official_source_page(command_text, role, url, page_text)


def enable_adapter() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable_adapter() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


def test_s1_default_fetcher_returns_empty() -> None:
    fetcher = provider.build_safe_official_command_fetcher()
    check("S1 default returns empty", fetcher(ALLOWED_URL, 3.0) == "")


def test_s2_network_false_blocks_transport() -> None:
    transport = FakeTransport()
    fetcher = provider.build_safe_official_command_fetcher(allow_network=False, transport=transport)
    check("S2 allow_network False returns empty", fetcher(ALLOWED_URL, 3.0) == "")
    check("S2 transport not called", transport.calls == [])


def test_s3_network_true_calls_transport() -> None:
    transport = FakeTransport("page")
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    check("S3 allowed URL returns text", fetcher(ALLOWED_URL, 3.0) == "page")
    check("S3 transport called once", len(transport.calls) == 1)
    check("S3 normalized URL supplied", transport.calls[0][0] == ALLOWED_URL)


def test_s4_disallowed_url_blocks_transport() -> None:
    transport = FakeTransport()
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    check("S4 disallowed URL returns empty", fetcher(DISALLOWED_URL, 3.0) == "")
    check("S4 transport not called", transport.calls == [])


def test_s5_pseudo_urls_block_transport() -> None:
    transport = FakeTransport()
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    check("S5 static URL empty", fetcher(STATIC_URL, 3.0) == "")
    check("S5 localdb URL empty", fetcher(LOCALDB_URL, 3.0) == "")
    check("S5 transport not called", transport.calls == [])


def test_s6_timeout_clamp() -> None:
    low = provider.build_safe_official_command_fetcher(timeout_seconds=-1)
    high = provider.build_safe_official_command_fetcher(timeout_seconds=999)
    bad = provider.build_safe_official_command_fetcher(timeout_seconds="bad")
    check("S6 negative uses default", low.timeout_seconds == provider.DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)
    check("S6 invalid uses default", bad.timeout_seconds == provider.DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)
    check("S6 huge clamps max", high.timeout_seconds == provider.MAX_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)


def test_s7_runtime_error_fail_closed() -> None:
    transport = FakeTransport(exc=RuntimeError("boom"))
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    check("S7 RuntimeError returns empty", fetcher(ALLOWED_URL, 3.0) == "")
    check("S7 transport called once", len(transport.calls) == 1)


def test_s8_timeout_fail_closed() -> None:
    custom = FakeTransport(exc=provider.OfficialCommandRetrievalTimeout("timeout"))
    fetcher1 = provider.build_safe_official_command_fetcher(allow_network=True, transport=custom)
    check("S8 custom timeout returns empty", fetcher1(ALLOWED_URL, 3.0) == "")

    builtin = FakeTransport(exc=TimeoutError("timeout"))
    fetcher2 = provider.build_safe_official_command_fetcher(allow_network=True, transport=builtin)
    check("S8 builtin timeout returns empty", fetcher2(ALLOWED_URL, 3.0) == "")


def test_s9_live_provider_compatibility() -> None:
    transport = FakeTransport(PAGE_TEXT)
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    parser = FakeParser()
    live = provider.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
    )
    results = list(live("Naval Example Command", "from", {}))
    check("S9 live provider returns result", len(results) == 1)
    check("S9 transport called once", len(transport.calls) == 1)
    check("S9 parser called once", len(parser.calls) == 1)
    check("S9 result source tier", results and results[0].get("source_tier") == "official_live")


def test_s10_adapter_gate_blocks_provider_fetcher() -> None:
    disable_adapter()
    transport = FakeTransport(PAGE_TEXT)
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=transport)
    live = provider.build_live_provider(enable_network=True, candidate_urls=[ALLOWED_URL], fetcher=fetcher)
    adapter.register_official_command_provider(live)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S10 adapter returns None with gate unset", cand is None)
    check("S10 transport not called", transport.calls == [])


def test_s11_no_auto_registration() -> None:
    enable_adapter()
    adapter.register_official_command_provider(None)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S11 no automatic provider registration", cand is None)


def test_s12_no_network_static_db_proof() -> None:
    src = inspect.getsource(provider)
    for token in ("import requests", "urllib.request", "http.client", "import socket", "socket."):
        check(f"S12 no {token}", token not in src)
    check("S12 no command database variable", "COMMAND_DATABASE" not in src and "STATIC_COMMAND" not in src)
    fetcher_src = inspect.getsource(provider.SafeOfficialCommandFetcher)
    for token in ("os.environ", "os.getenv", "putenv", "register_official", "register_fixture"):
        check(f"S12 fetcher no {token}", token not in fetcher_src)


def main() -> int:
    tests = [
        test_s1_default_fetcher_returns_empty,
        test_s2_network_false_blocks_transport,
        test_s3_network_true_calls_transport,
        test_s4_disallowed_url_blocks_transport,
        test_s5_pseudo_urls_block_transport,
        test_s6_timeout_clamp,
        test_s7_runtime_error_fail_closed,
        test_s8_timeout_fail_closed,
        test_s9_live_provider_compatibility,
        test_s10_adapter_gate_blocks_provider_fetcher,
        test_s11_no_auto_registration,
        test_s12_no_network_static_db_proof,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    adapter.register_official_command_provider(None)
    disable_adapter()
    print(f"\nL.32J safe fetcher stub smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
