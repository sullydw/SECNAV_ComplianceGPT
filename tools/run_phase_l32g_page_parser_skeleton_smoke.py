#!/usr/bin/env python3
"""Phase L.32G smoke: official provider page parser skeleton.

Deterministic smoke. Parses supplied page text only. Uses fake fetcher for live
retriever checks. No real internet, no filesystem lookup, and no static command
database.
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
URL = "https://www.example.navy.mil/naval-example-command"


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


class FakeFetcher:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        return self.text


def parse(text: str, role: str = "from") -> list[dict[str, Any]]:
    return provider.parse_official_source_page("Naval Example Command", role, URL, text)


def resolved(result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    rv = result.get("resolved_value")
    return rv if isinstance(rv, dict) else {}


def test_titles() -> None:
    check("S1 title tag", provider.extract_official_page_title("<title>Naval Example Command</title>") == "Naval Example Command")
    check("S2 h1 fallback", provider.extract_official_page_title("<h1>Naval Example Command</h1>") == "Naval Example Command")
    check("S3 Title line", provider.extract_official_page_title("Title: Naval Example Command") == "Naval Example Command")


def test_explicit_from() -> None:
    result = parse("Title: Naval Example Command\nFrom: Commanding Officer, Naval Example Command")
    item = result[0] if result else None
    rv = resolved(item)
    check("S4 one From result", len(result) == 1)
    check("S4 From value", rv.get("from") == "Commanding Officer, Naval Example Command")
    check("S4 official_live", item is not None and item.get("source_tier") == "official_live")
    check("S4 confidence explicit", item is not None and float(item.get("confidence", 0)) >= 0.90)
    check("S4 URL retained", item is not None and item.get("source_url") == URL)


def test_to_stripping() -> None:
    text = """Title: Naval Example Command
Command: Naval Example Command
Letterhead Top Line: SHOULD NOT APPLY
Letterhead Activity: SHOULD NOT APPLY
Letterhead Address: SHOULD NOT APPLY
"""
    result = parse(text, "to")
    rv = resolved(result[0] if result else None)
    check("S5 To result", rv.get("to") == "Naval Example Command")
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
        check(f"S5 no {key}", key not in rv)


def test_letterhead_rules() -> None:
    complete = """Title: Naval Example Command
From: Commanding Officer, Naval Example Command
Letterhead Top Line: DEPARTMENT OF THE NAVY
Letterhead Activity: NAVAL EXAMPLE COMMAND
Letterhead Address: NORFOLK VA 23511-0000
"""
    rv = resolved(parse(complete)[0])
    check("S6 letterhead top", rv.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("S6 letterhead activity", rv.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND")
    check("S6 letterhead address", rv.get("letterhead_address") == "NORFOLK VA 23511-0000")

    incomplete = """Title: Naval Example Command
From: Commanding Officer, Naval Example Command
Letterhead Top Line: DEPARTMENT OF THE NAVY
"""
    item = parse(incomplete)[0]
    rv2 = resolved(item)
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
        check(f"S7 omitted incomplete {key}", key not in rv2)
    check("S7 limitation mentions letterhead", "letterhead" in str(item.get("source_limitation", "")).lower())

    from_only = parse("From: Commanding Officer, Naval Example Command")[0]
    rv3 = resolved(from_only)
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
        check(f"S8 no invented {key}", key not in rv3)


def test_negative_and_conflict() -> None:
    check("S9 unrelated empty", parse("Welcome to a page about nothing useful.") == [])
    check("S10 invalid role empty", parse("From: Commanding Officer, Naval Example Command", "via") == [])
    conflict = parse("""Title: Naval Example Command
From: Commanding Officer, Naval Example Command
From: Commander, Naval Example Command
""")
    values = [resolved(item).get("from") for item in conflict]
    check("S11 conflicts preserved count", len(conflict) == 2)
    check("S11 first conflict value", "Commanding Officer, Naval Example Command" in values)
    check("S11 second conflict value", "Commander, Naval Example Command" in values)

    fallback = parse("<title>Naval Example Command</title>")
    if fallback:
        check("S12 fallback bounded", float(fallback[0].get("confidence", 0)) <= 0.85)
        rv = resolved(fallback[0])
        check("S12 fallback no letterhead", not any(k.startswith("letterhead_") for k in rv))
    else:
        check("S12 fallback may return empty", True)


def test_live_and_adapter_paths() -> None:
    page = """Title: Naval Example Command
From: Commanding Officer, Naval Example Command
Letterhead Top Line: DEPARTMENT OF THE NAVY
Letterhead Activity: NAVAL EXAMPLE COMMAND
Letterhead Address: NORFOLK VA 23511-0000
"""
    fetcher = FakeFetcher(page)
    live = provider.build_live_provider(enable_network=True, candidate_urls=[URL], fetcher=fetcher)
    raw = list(live("Naval Example Command", "from", {}))
    check("S13 live default parser result", len(raw) == 1)
    check("S13 fetcher once", len(fetcher.calls) == 1)
    check("S13 parser result tier", raw and raw[0].get("source_tier") == "official_live")

    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()
    adapter.register_official_command_provider(live)
    cand = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S14 adapter candidate", isinstance(cand, dict))
    check("S14 confirmation required", isinstance(cand, dict) and cand.get("requires_user_confirmation") is True)
    check("S14 source metadata", isinstance(cand, dict) and all(cand.get(k) for k in ("source_title", "source_url", "source_tier", "confidence")))


def test_no_network_static_db() -> None:
    src = inspect.getsource(provider)
    for token in ("import requests", "urllib.request", "http.client", "import socket", "socket."):
        check(f"S15 no {token}", token not in src)
    check("S15 no command database variable", "COMMAND_DATABASE" not in src and "STATIC_COMMAND" not in src)
    check("S15 empty text returns empty", provider.parse_official_source_page("x", "from", URL, "") == [])
    check("S15 parser source-text only hook present", "page_text" in inspect.signature(provider.parse_official_source_page).parameters)


def main() -> int:
    tests = [
        test_titles,
        test_explicit_from,
        test_to_stripping,
        test_letterhead_rules,
        test_negative_and_conflict,
        test_live_and_adapter_paths,
        test_no_network_static_db,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    adapter.register_official_command_provider(None)
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()
    print(f"\nL.32G page parser skeleton smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
