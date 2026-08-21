#!/usr/bin/env python3
"""Phase L.32K smoke: official provider safe fetcher contract hardening.

Deterministic smoke. Uses injected fake transports only. No real internet,
no filesystem lookup, no env.
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
import official_command_provider as provider  # noqa: E402

PASSED = 0
FAILED = 0


def check(name, cond):
    global PASSED, FAILED
    if cond:
        print(f"PASS: {name}")
        PASSED += 1
    else:
        print(f"FAIL: {name}")
        FAILED += 1


def enable_adapter():
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable_adapter():
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()
    adapter.register_official_command_provider(None)


class _TransportRecorder:
    def __init__(self, return_value):
        self.return_value = return_value
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        return self.return_value


# S1: non-callable transport ignored / fails closed
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport="not-callable")
check("S1 non-callable transport ignored", fetcher("https://www.example.navy.mil/x", 5.0) == "")

# S2: transport returning None becomes empty
rec = _TransportRecorder(None)
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
check("S2 None response becomes empty", fetcher("https://www.example.navy.mil/x", 5.0) == "")
check("S2 transport called once", len(rec.calls) == 1)

# S3: non-string transport values convert safely to string / fail closed deterministically
for raw in (b"bytes body", 12345):
    rec = _TransportRecorder(raw)
    fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
    result = fetcher("https://www.example.navy.mil/x", 5.0)
    check(f"S3 {type(raw).__name__} response converted", isinstance(result, str) and result != "")

# S4: whitespace-only becomes empty
rec = _TransportRecorder("   \n\t  ")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
check("S4 whitespace-only becomes empty", fetcher("https://www.example.navy.mil/x", 5.0) == "")

# S5: oversized response is bounded
huge = "x" * (provider.MAX_OFFICIAL_FETCH_RESPONSE_CHARS + 1000)
rec = _TransportRecorder(huge)
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
result = fetcher("https://www.example.navy.mil/x", 5.0)
check("S5 oversized result length bounded", len(result) <= provider.MAX_OFFICIAL_FETCH_RESPONSE_CHARS)
check("S5 oversized result prefix preserved", result.startswith("x"))

# S6: timeout passed to transport is clamped
rec = _TransportRecorder("ok")
provider.build_safe_official_command_fetcher(
    allow_network=True, transport=rec, timeout_seconds=60.0
)("https://www.example.navy.mil/x", 9999.0)
_, passed_timeout = rec.calls[-1]
check("S6 call timeout clamped", passed_timeout == provider.clamp_official_lookup_timeout(9999.0))

# S7: invalid __call__ timeout clamps / falls back safely
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec, timeout_seconds=2.0)
for bad in (-1.0, "bad", 0.0):
    rec.calls.clear()
    fetcher("https://www.example.navy.mil/x", bad)
    _, passed_timeout = rec.calls[-1]
    check(f"S7 {repr(bad)} call timeout uses default", passed_timeout == provider.clamp_official_lookup_timeout(bad))

# S8: invalid URL argument returns empty, transport not called
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
for bad_url in ("", "   ", "not-a-url"):
    rec.calls.clear()
    check(f"S8 {repr(bad_url)} URL returns empty", fetcher(bad_url, 5.0) == "")
check("S8 transport not called for invalid URLs", len(rec.calls) == 0)

# S9: URL passed to transport is normalized
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
fetcher("https://www.example.navy.mil/path/", 5.0)
passed_url, _ = rec.calls[-1]
check("S9 URL normalized", passed_url == "https://www.example.navy.mil/path")

# S10: disallowed/pseudo URL returns empty before transport
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
for bad_url in ("https://example.com/x", "static://commands/x", "localdb://x"):
    rec.calls.clear()
    check(f"S10 {bad_url.split('://')[0]} URL empty", fetcher(bad_url, 5.0) == "")
check("S10 transport never called for blocked", len(rec.calls) == 0)

# S11: default fetcher returns empty
fetcher = provider.build_safe_official_command_fetcher()
check("S11 default fetcher returns empty", fetcher("https://www.example.navy.mil/x", 5.0) == "")

# S12: allow_network=False still blocks transport
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=False, transport=rec)
check("S12 allow_network False returns empty", fetcher("https://www.example.navy.mil/x", 5.0) == "")
check("S12 transport not called", len(rec.calls) == 0)

# S13: live provider compatibility still works
enable_adapter()
ALLOWED_URL = "https://www.example.navy.mil/naval-example-command"
PAGE_HTML = "<html><title>T</title><body>From: Commanding Officer, Naval Example Command</body></html>"
rec = _TransportRecorder(PAGE_HTML)
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)

_complete_result = {
    "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
    "source_tier": "official_live",
    "source_title": "Naval Example Command",
    "source_url": ALLOWED_URL,
    "source_limitation": "Official-source candidate parsed from supplied page text; user confirmation required.",
    "confidence": 0.92,
}

def _fake_parser(command_text, role, url, page_text):
    return [_complete_result]

live = provider.build_live_provider(
    enable_network=True,
    candidate_urls=[ALLOWED_URL],
    fetcher=fetcher,
    parser=_fake_parser,
)
adapter.register_official_command_provider(live)
result = adapter.official_command_lookup("Naval Example Command", "from", {})
check("S13 live provider returns result", isinstance(result, dict) and len(result) >= 1)
check("S13 transport called once", len(rec.calls) == 1)
check("S13 result source tier", result.get("source_tier") == "official_live")

# S14: adapter gate still blocks provider/fetcher when unset
disable_adapter()
rec = _TransportRecorder("ok")
fetcher = provider.build_safe_official_command_fetcher(allow_network=True, transport=rec)
live = provider.build_live_provider(enable_network=True, fetcher=fetcher)
adapter.register_official_command_provider(live)
result = adapter.official_command_lookup("Naval Example Command", "from", {})
check("S14 adapter returns None with gate unset", result is None)
check("S14 transport not called", len(rec.calls) == 0)

# S15: no env/static DB/direct network/registration proof
source = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_command_provider.py"), "r", encoding="utf-8").read()
fetcher_source = source[source.find("class SafeOfficialCommandFetcher") : source.find("def build_safe_official_command_fetcher")]
for token in ["import requests", "urllib.request", "http.client", "import socket", "socket."]:
    check(f"S15 fetcher class no {token}", token not in fetcher_source)
for token in ["os.environ", "os.getenv", "putenv"]:
    check(f"S15 fetcher class no {token}", token not in fetcher_source)
for token in ["register_official", "register_fixture"]:
    check(f"S15 fetcher class no {token}", token not in fetcher_source)
check("S15 no command database variable", "OFFICIAL_COMMAND_DATABASE" not in fetcher_source)
check("S15 constant exists", "MAX_OFFICIAL_FETCH_RESPONSE_CHARS" in source)

print(f"\nL.32K safe fetcher contract hardening smoke: {PASSED}/{PASSED + FAILED} PASS")
sys.exit(0 if FAILED == 0 else 1)
