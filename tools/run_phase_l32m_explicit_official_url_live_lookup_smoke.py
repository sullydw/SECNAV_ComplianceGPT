#!/usr/bin/env python3
"""
Phase L.32M — Explicit Official URL Live Lookup Smoke

Proves that the live official lookup path works with one explicit allowed
official URL and a real/injected fetcher, while keeping all safety rules:

- live lookup is disabled by default
- network/fetch behavior requires explicit opt-in (gate + enable_network)
- only one explicit official URL is used (no open-ended web search)
- no static command database
- no auto-apply; results are candidate-only until confirmation
- fail-closed when the parser cannot confidently extract a candidate
- To-line candidates strip letterhead
- From candidates include letterhead only when all three fields are present

The smoke is designed to pass even when real network is unavailable:
- default-disabled behavior is always verified
- real-network fetch checks are skipped gracefully when the network is down
- deterministic injected-transport checks prove parser/adapter behavior
"""

from __future__ import annotations

import os
import socket
import sys
import urllib.error
import urllib.request
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
SKIP = 0

# One explicit allowed official URL only.  No search engine, no crawl.
ALLOWED_URL = "https://www.marines.mil/"
USER_AGENT = "SECNAV-ComplianceGPT-L32M-smoke/1.0"


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


def skip(name: str, reason: str) -> None:
    global SKIP
    SKIP += 1
    print(f"SKIP: {name} — {reason}")


def enable() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


# ── Deterministic fake fetcher (injected transport for parser behavior) ────

class FakeFetcher:
    """Return a fixed page_text for any URL.  No real network."""

    def __init__(self, page_text: str) -> None:
        self.page_text = page_text
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        return self.page_text


# ── Real network fetcher using only the one explicit allowed URL ────────────

class UrllibFetcher:
    """Bounded urllib fetcher for the single explicit official URL."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout_seconds: float) -> str:
        self.calls.append((url, timeout_seconds))
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
        # Bound response size defensively.
        max_chars = provider_module.MAX_OFFICIAL_FETCH_RESPONSE_CHARS
        return raw.decode("utf-8", errors="replace")[:max_chars]


def can_reach_network() -> bool:
    """Return True only if the explicit URL can be fetched quickly."""
    fetcher = UrllibFetcher()
    try:
        text = fetcher(ALLOWED_URL, 5.0)
        return bool(text.strip())
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, TimeoutError, OSError):
        return False
    except Exception:
        return False


# ── Synthetic official pages for deterministic parser checks ───────────────

FROM_PAGE = f"""<html>
<head><title>2d Marine Division</title></head>
<body>
<h1>2d Marine Division</h1>
<p>Commanding Officer: 2d Marine Division</p>
<p>Letterhead Top Line: DEPARTMENT OF THE NAVY</p>
<p>Letterhead Activity: HEADQUARTERS 2D MARINE DIVISION</p>
<p>Letterhead Address: CAMP LEJEUNE NC 28542-0000</p>
<p>Official unit information page.</p>
</body>
</html>"""

TO_PAGE = f"""<html>
<head><title>2d Marine Division</title></head>
<body>
<h1>2d Marine Division</h1>
<p>To: Commanding Officer, 2d Marine Division</p>
<p>Letterhead Top Line: BOGUS TOP</p>
<p>Letterhead Activity: BOGUS ACTIVITY</p>
<p>Letterhead Address: BOGUS ADDRESS</p>
<p>Unit Identity: BOGUS UNIT</p>
</body>
</html>"""

NO_CANDIDATE_PAGE = f"""<html>
<head><title>Marines.mil</title></head>
<body>
<h1>United States Marine Corps</h1>
<p>Welcome to the official Marine Corps website.</p>
</body>
</html>"""


# ── Adapter/provider wiring helpers ────────────────────────────────────────

def register_live(fetcher: Any, page_text: str | None = None) -> Any:
    """Build and register a live provider with the explicit allowed URL."""
    parser = provider_module.parse_official_source_page
    provider = adapter.build_and_register_live_official_command_provider(
        enable_network=True,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=parser,
        timeout_seconds=5.0,
    )
    return provider


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    return pending[-1] if pending else None


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


# ── Test cases ─────────────────────────────────────────────────────────────


def test_default_disabled_no_candidate() -> None:
    """Live lookup disabled by default: adapter returns None without fetching."""
    disable()
    fetcher = FakeFetcher(FROM_PAGE)
    register_live(fetcher)
    cand = adapter.official_command_lookup("2d Marine Division", "from", {})
    check("L32M default disabled returns None", cand is None)
    check("L32M default disabled does not fetch", fetcher.calls == [])


def test_gate_enabled_network_disabled() -> None:
    """Gate set but enable_network=False: no candidate, no fetch."""
    enable()
    fetcher = FakeFetcher(FROM_PAGE)
    provider = adapter.build_and_register_live_official_command_provider(
        enable_network=False,
        candidate_urls=[ALLOWED_URL],
        fetcher=fetcher,
        parser=provider_module.parse_official_source_page,
        timeout_seconds=5.0,
    )
    check("L32M provider built with network disabled", provider is not None)
    cand = adapter.official_command_lookup("2d Marine Division", "from", {})
    check("L32M enable_network=False returns None", cand is None)
    check("L32M enable_network=False does not fetch", fetcher.calls == [])


def test_from_candidate_with_complete_letterhead() -> None:
    """From candidate includes letterhead only when all three fields are present."""
    enable()
    fetcher = FakeFetcher(FROM_PAGE)
    register_live(fetcher)
    cand = adapter.official_command_lookup("2d Marine Division", "from", {})
    check("L32M From candidate produced", isinstance(cand, dict), f"cand={cand!r}")
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32M From value present", rv.get("from") == "Commanding Officer, 2d Marine Division")
        check("L32M letterhead_top_line present", rv.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
        check("L32M letterhead_activity present", rv.get("letterhead_activity") == "HEADQUARTERS 2D MARINE DIVISION")
        check("L32M letterhead_address present", rv.get("letterhead_address") == "CAMP LEJEUNE NC 28542-0000")
        check("L32M source_tier official_live", cand.get("source_tier") == "official_live")
        check(
            "L32M source_url is explicit allowed URL",
            provider_module.normalize_source_url(cand.get("source_url")) == provider_module.normalize_source_url(ALLOWED_URL),
            f"source_url={cand.get('source_url')!r}",
        )
        check("L32M requires confirmation", cand.get("requires_user_confirmation") is True)
        check("L32M fetcher called once", len(fetcher.calls) == 1)
        check(
            "L32M fetcher used explicit URL",
            provider_module.normalize_source_url(fetcher.calls[0][0]) == provider_module.normalize_source_url(ALLOWED_URL),
            f"calls={fetcher.calls!r}",
        )


def test_to_candidate_strips_letterhead() -> None:
    """To candidate strips letterhead and unit_identity fields."""
    enable()
    fetcher = FakeFetcher(TO_PAGE)
    register_live(fetcher)
    cand = adapter.official_command_lookup("2d Marine Division", "to", {})
    check("L32M To candidate produced", isinstance(cand, dict), f"cand={cand!r}")
    if isinstance(cand, dict):
        rv = cand.get("resolved_value") or {}
        check("L32M To value present", rv.get("to") == "Commanding Officer, 2d Marine Division")
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
            check(f"L32M To strips {key}", key not in rv, f"rv={rv!r}")
        check("L32M To requires confirmation", cand.get("requires_user_confirmation") is True)


def test_fail_closed_unparseable_page() -> None:
    """If parser cannot extract a candidate, fail closed and report it."""
    enable()
    fetcher = FakeFetcher(NO_CANDIDATE_PAGE)
    register_live(fetcher)
    cand = adapter.official_command_lookup("2d Marine Division", "from", {})
    check("L32M unparseable page returns no candidate", cand is None,
          "parser failed closed instead of inventing a candidate")


def test_real_network_fetch_fail_closed() -> None:
    """Attempt a real fetch of the one explicit official URL.

    If network is unavailable, skip live fetch checks with a clear message.
    If the fetch succeeds, the parser must fail closed because the homepage
    does not contain explicit From/To/letterhead labels.
    """
    enable()
    if not can_reach_network():
        skip(
            "L32M real network fetch of explicit official URL",
            "network unavailable; live fetch checks skipped",
        )
        return

    fetcher = UrllibFetcher()
    register_live(fetcher)
    cand = adapter.official_command_lookup("2d Marine Division", "from", {})
    check("L32M real fetch used explicit URL", fetcher.calls and fetcher.calls[0][0] == ALLOWED_URL)
    check(
        "L32M real homepage fails closed (no candidate)",
        cand is None,
        f"cand={cand!r}",
    )


def test_e2e_chat_builder_confirmation() -> None:
    """End-to-end through chat builder: candidate pending, confirm applies From+letterhead."""
    enable()
    fetcher = FakeFetcher(FROM_PAGE)
    register_live(fetcher)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from 2d Marine Division to Commanding General, II Marine Expeditionary Force about training readiness.",
    )
    cand = latest_pending(result)
    check("L32M E2E From candidate appears as pending", isinstance(cand, dict) and cand.get("field") == "from")

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload = confirmed.get("payload") or {}
    check("L32M E2E confirm applies From", payload.get("from") == "Commanding Officer, 2d Marine Division")
    check("L32M E2E confirm applies letterhead_top_line", payload.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY")
    check("L32M E2E confirm applies letterhead_activity", payload.get("letterhead_activity") == "HEADQUARTERS 2D MARINE DIVISION")
    check("L32M E2E confirm applies letterhead_address", payload.get("letterhead_address") == "CAMP LEJEUNE NC 28542-0000")


def test_no_static_db_no_search() -> None:
    """No static command database and no open-ended web search."""
    src = Path(provider_module.__file__).read_text(encoding="utf-8")
    check("L32M no static command database variable", "OFFICIAL_COMMAND_DATABASE" not in src)
    check("L32M no hardcoded command list", "COMMANDING_OFFICER" not in src.upper() or "fixture" in src.lower())
    # The live retriever uses an explicit URL list, not a search engine.
    check("L32M no search engine APIs", "google.com" not in src and "bing.com" not in src and "duckduckgo" not in src)


def main() -> int:
    tests = [
        test_default_disabled_no_candidate,
        test_gate_enabled_network_disabled,
        test_from_candidate_with_complete_letterhead,
        test_to_candidate_strips_letterhead,
        test_fail_closed_unparseable_page,
        test_real_network_fetch_fail_closed,
        test_e2e_chat_builder_confirmation,
        test_no_static_db_no_search,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))

    print(f"\nL.32M explicit official URL live lookup smoke: {PASS} PASS, {FAIL} FAIL, {SKIP} SKIP")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        disable()
        adapter.set_official_command_search_provider(None)
