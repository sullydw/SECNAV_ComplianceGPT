#!/usr/bin/env python3
"""Phase L.32H smoke: official provider candidate URL discovery skeleton.

Deterministic smoke.  Exercises the candidate-URL discovery helpers only.
No real internet, no filesystem lookup, no search engine, and no static
command database.
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

ALLOWED_A = "https://www.example.navy.mil/naval-example-command"
ALLOWED_B = "https://www.example.marines.mil/other-command"
ALLOWED_DEFENSE = "https://www.defense.gov/example"
DISALLOWED = "https://en.wikipedia.org/wiki/Naval_Example_Command"
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


def discover(
    role: str = "from",
    state: dict[str, Any] | None = None,
    *,
    candidate_urls: list[str] | None = None,
) -> list[str]:
    return provider.discover_candidate_urls(
        "Naval Example Command", role, state, candidate_urls=candidate_urls
    )


# S1 — explicit constructor URLs returned when allowed

def test_s1_explicit_constructor_urls() -> None:
    result = discover(candidate_urls=[ALLOWED_A])
    check("S1 explicit constructor URL returned", result == [ALLOWED_A])


# S2 — state fixture URLs returned when constructor URLs absent

def test_s2_state_fixture_urls() -> None:
    state = {"_official_lookup_fixture_urls": [ALLOWED_A]}
    result = discover(state=state)
    check("S2 state fixture URL returned", result == [ALLOWED_A])


# S3 — state candidate URLs returned when fixture URLs absent

def test_s3_state_candidate_urls() -> None:
    state = {"_official_lookup_candidate_urls": [ALLOWED_A]}
    result = discover(state=state)
    check("S3 state candidate URL returned", result == [ALLOWED_A])


# S4 — constructor URLs take priority over state URLs

def test_s4_constructor_priority() -> None:
    state = {
        "_official_lookup_fixture_urls": [ALLOWED_B],
        "_official_lookup_candidate_urls": [ALLOWED_DEFENSE],
    }
    result = discover(state=state, candidate_urls=[ALLOWED_A])
    check("S4 constructor priority", result == [ALLOWED_A])


# S5 — order preserved

def test_s5_order_preserved() -> None:
    result = discover(candidate_urls=[ALLOWED_A, ALLOWED_B, ALLOWED_DEFENSE])
    check("S5 order preserved", result == [ALLOWED_A, ALLOWED_B, ALLOWED_DEFENSE])


# S6 — duplicates removed after normalization

def test_s6_duplicates_removed() -> None:
    result = discover(candidate_urls=[ALLOWED_A, ALLOWED_A.upper(), ALLOWED_A + "/", ALLOWED_A + "#frag"])
    check("S6 duplicates removed", result == [ALLOWED_A])


# S7 — empty/whitespace removed

def test_s7_empty_whitespace_removed() -> None:
    result = discover(candidate_urls=["", "   ", ALLOWED_A, "\t"])
    check("S7 empty/whitespace removed", result == [ALLOWED_A])


# S8 — disallowed domains removed

def test_s8_disallowed_domains_removed() -> None:
    result = discover(candidate_urls=[ALLOWED_A, DISALLOWED])
    check("S8 disallowed domains removed", result == [ALLOWED_A])


# S9 — pseudo URLs removed

def test_s9_pseudo_urls_removed() -> None:
    result = discover(candidate_urls=[ALLOWED_A, STATIC_URL, LOCALDB_URL])
    check("S9 pseudo URLs removed", result == [ALLOWED_A])


# S10 — invalid role returns []

def test_s10_invalid_role() -> None:
    result = discover(role="via", candidate_urls=[ALLOWED_A])
    check("S10 invalid role returns empty", result == [])


# S11 — no state mutation

def test_s11_no_state_mutation() -> None:
    state: dict[str, Any] = {
        "_official_lookup_fixture_urls": [ALLOWED_A],
        "_official_lookup_candidate_urls": [ALLOWED_B],
        "sentinel": "unchanged",
    }
    before = dict(state)
    discover(state=state)
    check("S11 no state mutation", state == before)


# S12 — live retriever uses discovery helper

def test_s12_live_retriever_uses_discovery() -> None:
    fetcher = _FakeFetcher("page")
    parser = _FakeParser([_valid_result()])
    live = provider.build_live_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_A],
        fetcher=fetcher,
        parser=parser,
    )
    results = list(live("Naval Example Command", "from", {}))
    check("S12 live retriever returns result", len(results) == 1)
    check("S12 fetcher called once", len(fetcher.calls) == 1)
    check("S12 fetcher URL allowed", fetcher.calls[0][0] == ALLOWED_A)


# S13 — default discovery returns []

def test_s13_default_discovery_empty() -> None:
    check("S13 default discovery empty", discover() == [])


# S14 — no network/static DB proof

def test_s14_no_network_static_db() -> None:
    src = inspect.getsource(provider)
    for token in ("import requests", "urllib.request", "http.client", "import socket", "socket."):
        check(f"S14 no {token}", token not in src)
    check("S14 no command database variable", "COMMAND_DATABASE" not in src and "STATIC_COMMAND" not in src)
    check("S14 no environment gate read", "SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP" not in src)
    check("S14 no adapter registration", "register_official_command_provider" not in src)


class _FakeFetcher:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        return self.text


class _FakeParser:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(self, command_text: str, role: str, url: str, page_text: str) -> list[dict[str, Any]]:
        self.calls.append((command_text, role, url, page_text))
        return [dict(item) for item in self.results]


def _valid_result() -> dict[str, Any]:
    return {
        "resolved_value": {"from": "Commanding Officer, Naval Example Command"},
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official .mil Page",
        "source_url": ALLOWED_A,
        "confidence": 0.92,
    }


def main() -> int:
    tests = [
        test_s1_explicit_constructor_urls,
        test_s2_state_fixture_urls,
        test_s3_state_candidate_urls,
        test_s4_constructor_priority,
        test_s5_order_preserved,
        test_s6_duplicates_removed,
        test_s7_empty_whitespace_removed,
        test_s8_disallowed_domains_removed,
        test_s9_pseudo_urls_removed,
        test_s10_invalid_role,
        test_s11_no_state_mutation,
        test_s12_live_retriever_uses_discovery,
        test_s13_default_discovery_empty,
        test_s14_no_network_static_db,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:
            check(test.__name__, False, f"unexpected exception: {exc!r}")
    print(f"\nL.32H candidate URL discovery skeleton smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
