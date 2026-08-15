#!/usr/bin/env python3
"""Phase L.32D smoke: official provider source filter and ranking skeleton.

This smoke is deterministic and fixture-only.  It exercises the source
filter/ranking helpers in ``official_command_provider`` and asserts that no
live/network/static-database behavior was introduced.  No internet access is
performed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

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


def _from_result(
    *,
    value: str = "Commanding Officer, Naval Example Command",
    tier: str = "official_live",
    url: str = "https://www.example.navy.mil/naval-example-command",
    title: str = "Naval Example Command Official .mil Page",
    confidence: float = 0.92,
    limitation: str = "",
    extra_rv: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rv: dict[str, Any] = {"from": value}
    if extra_rv:
        rv.update(extra_rv)
    result: dict[str, Any] = {
        "resolved_value": rv,
        "source_tier": tier,
        "source_title": title,
        "source_url": url,
        "confidence": confidence,
    }
    if limitation:
        result["source_limitation"] = limitation
    return result


def _to_result(
    *,
    value: str = "Commanding Officer, Naval Example Command",
    tier: str = "official_live",
    url: str = "https://www.example.navy.mil/naval-example-command",
    title: str = "Naval Example Command Official .mil Page",
    confidence: float = 0.92,
    limitation: str = "",
    extra_rv: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rv: dict[str, Any] = {"to": value}
    if extra_rv:
        rv.update(extra_rv)
    result: dict[str, Any] = {
        "resolved_value": rv,
        "source_tier": tier,
        "source_title": title,
        "source_url": url,
        "confidence": confidence,
    }
    if limitation:
        result["source_limitation"] = limitation
    return result


# ── S1: official .mil URLs allowed ─────────────────────────────────────────


def test_s1_official_urls_allowed() -> None:
    allowed = [
        "https://www.example.navy.mil/naval-example-command",
        "https://www.marines.mil/unit-page",
        "https://www.defense.gov/About/",
        "https://www.dod.mil/example",
    ]
    for url in allowed:
        check(f"S1 allowed {url}", provider_mod.is_allowed_official_source(url))
        cls = provider_mod.classify_source_url(url)
        check(f"S1 classified official {url}", cls["is_official"] is True and cls["reason"] == "")


# ── S2: disallowed URLs rejected as official ────────────────────────────────


def test_s2_disallowed_urls_rejected() -> None:
    disallowed = [
        "https://en.wikipedia.org/wiki/Naval_Example_Command",
        "https://www.facebook.com/navalexample",
        "https://x.com/navalexample",
        "https://twitter.com/navalexample",
        "https://www.instagram.com/navalexample",
        "https://www.linkedin.com/company/navalexample",
        "https://example.com/naval-example-command",
        "static://commands/naval-example-command",
        "localdb://naval-example-command",
        "",
        "   ",
    ]
    for url in disallowed:
        check(f"S2 disallowed {url!r}", provider_mod.is_allowed_official_source(url) is False)
        cls = provider_mod.classify_source_url(url)
        check(f"S2 classified non-official {url!r}", cls["is_official"] is False)


# ── S3: provenance completeness required ────────────────────────────────────


def test_s3_provenance_completeness() -> None:
    missing_url = _from_result()
    missing_url.pop("source_url")
    missing_title = _from_result()
    missing_title.pop("source_title")

    filtered = provider_mod.filter_provider_results([missing_url, missing_title], "from")
    check("S3 missing source_url removed", all(r.get("source_url") for r in filtered))
    check("S3 missing source_title removed", all(r.get("source_title") for r in filtered))
    check("S3 both incomplete results removed", len(filtered) == 0)


# ── S4: role-specific resolved value required ───────────────────────────────


def test_s4_role_specific_resolved_value() -> None:
    # A "from" result passed to role "to" has no "to" key -> removed
    from_result = _from_result()
    filtered_to = provider_mod.filter_provider_results([from_result], "to")
    check("S4 from-result removed for role to", len(filtered_to) == 0)

    # A "to" result passed to role "from" has no "from" key -> removed
    to_result = _to_result()
    filtered_from = provider_mod.filter_provider_results([to_result], "from")
    check("S4 to-result removed for role from", len(filtered_from) == 0)


# ── S5: confidence gate enforced for official_live ──────────────────────────


def test_s5_confidence_gate() -> None:
    low = _from_result(confidence=0.84)
    ok = _from_result(confidence=0.85)
    filtered = provider_mod.filter_provider_results([low, ok], "from")
    check("S5 confidence 0.84 removed", all(r["confidence"] >= 0.85 for r in filtered))
    check("S5 confidence 0.85 retained", len(filtered) == 1 and filtered[0]["confidence"] == 0.85)


# ── S6: To stripping works ──────────────────────────────────────────────────


def test_s6_to_stripping() -> None:
    bogus = _to_result(
        extra_rv={
            "letterhead_top_line": "BOGUS LETTERHEAD",
            "letterhead_activity": "BOGUS ACTIVITY",
            "letterhead_address": "BOGUS ADDRESS",
            "unit_identity": "BOGUS UNIT",
        }
    )
    filtered = provider_mod.filter_provider_results([bogus], "to")
    check("S6 To result retained", len(filtered) == 1)
    rv = filtered[0]["resolved_value"]
    check("S6 resolved_value contains to only", set(rv.keys()) == {"to"})
    check("S6 no letterhead_top_line", "letterhead_top_line" not in rv)
    check("S6 no letterhead_activity", "letterhead_activity" not in rv)
    check("S6 no letterhead_address", "letterhead_address" not in rv)
    check("S6 no unit_identity", "unit_identity" not in rv)


# ── S7: official_archived requires caution limitation ───────────────────────


def test_s7_archived_caution() -> None:
    with_caution = _from_result(
        tier="official_archived",
        confidence=0.80,
        limitation="Archived official source; verify current validity before applying.",
    )
    without_caution = _from_result(tier="official_archived", confidence=0.80)
    filtered = provider_mod.filter_provider_results([with_caution, without_caution], "from")
    check("S7 archived with caution retained", len(filtered) == 1)
    check("S7 archived without caution removed", filtered[0]["source_limitation"] == with_caution["source_limitation"])


# ── S8: secondary_credible not treated as official apply-ready ──────────────


def test_s8_secondary_not_apply_ready() -> None:
    secondary = _from_result(
        tier="secondary_credible",
        url="https://example.com/naval-example-command",
        confidence=0.99,
    )
    filtered = provider_mod.filter_provider_results([secondary], "from")
    check("S8 secondary_credible removed", len(filtered) == 0)


# ── S9: user_provided pass-through but not official ─────────────────────────


def test_s9_user_provided_passthrough() -> None:
    user = _from_result(tier="user_provided", url="https://example.com/user-supplied", confidence=0.5)
    filtered = provider_mod.filter_provider_results([user], "from")
    check("S9 user_provided retained", len(filtered) == 1)
    check("S9 user_provided tier preserved", filtered[0]["source_tier"] == "user_provided")
    check("S9 user_provided not official_live", filtered[0]["source_tier"] != "official_live")


# ── S10: ranking is deterministic ──────────────────────────────────────────


def test_s10_ranking_deterministic() -> None:
    results = [
        _from_result(value="A", tier="secondary_credible", url="https://example.com/a", confidence=0.99),
        _from_result(value="B", tier="official_live", url="https://www.example.navy.mil/b", confidence=0.90),
        _from_result(value="C", tier="official_live", url="https://www.example.navy.mil/c", confidence=0.95),
        _from_result(value="D", tier="official_archived", url="https://www.example.navy.mil/d", confidence=0.99, limitation="Archived; verify validity."),
        _from_result(value="E", tier="user_provided", url="https://example.com/e", confidence=0.99),
        _from_result(value="F", tier="unresolved", url="", confidence=0.0),
    ]
    first = provider_mod.rank_provider_results(results, "from", "Naval Example Command")
    second = provider_mod.rank_provider_results(results, "from", "Naval Example Command")
    check("S10 repeated calls identical", first == second)

    tiers = [r["source_tier"] for r in first]
    check("S10 official_live first", tiers[0] == "official_live")
    check("S10 highest confidence live first", first[0]["resolved_value"]["from"] == "C")
    check("S10 official_archived before user_provided", tiers.index("official_archived") < tiers.index("user_provided"))
    check("S10 user_provided before secondary_credible", tiers.index("user_provided") < tiers.index("secondary_credible"))
    check("S10 unresolved last", tiers[-1] == "unresolved")


# ── S11: conflict values preserved for adapter-level handling ───────────────


def test_s11_conflict_preserved() -> None:
    r1 = _from_result(value="Commanding Officer, Naval Example Command", url="https://www.example.navy.mil/a", confidence=0.95)
    r2 = _from_result(value="Commander, Naval Example Command", url="https://www.example.navy.mil/b", confidence=0.95)
    ranked = provider_mod.rank_provider_results([r1, r2], "from", "Naval Example Command")
    check("S11 two results preserved", len(ranked) == 2)
    values = {r["resolved_value"]["from"] for r in ranked}
    check("S11 distinct From values preserved", len(values) == 2)


# ── S12: no live/network/static DB proof ────────────────────────────────────


def test_s12_no_live_behavior() -> None:
    source = Path(provider_mod.__file__).read_text() if provider_mod.__file__ else ""
    check("S12 no requests import", "import requests" not in source and "from requests" not in source)
    check("S12 no urllib.request", "urllib.request" not in source and "urlopen" not in source)
    check("S12 no http.client", "http.client" not in source)
    check("S12 no socket import", "import socket" not in source)
    check("S12 no broad command database", "COMMAND_DATABASE" not in source and "COMMANDS" not in source)
    check("S12 no fixture defaults with commands", "build_fixture_provider()" in source or "fixtures or []" in source)

    # Helpers work only on supplied result dicts: empty input -> empty output
    check("S12 filter empty -> empty", provider_mod.filter_provider_results([], "from") == [])
    check("S12 rank empty -> empty", provider_mod.rank_provider_results([], "from") == [])


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    test_s1_official_urls_allowed()
    test_s2_disallowed_urls_rejected()
    test_s3_provenance_completeness()
    test_s4_role_specific_resolved_value()
    test_s5_confidence_gate()
    test_s6_to_stripping()
    test_s7_archived_caution()
    test_s8_secondary_not_apply_ready()
    test_s9_user_provided_passthrough()
    test_s10_ranking_deterministic()
    test_s11_conflict_preserved()
    test_s12_no_live_behavior()

    print(f"\nL.32D official provider source filter smoke: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
