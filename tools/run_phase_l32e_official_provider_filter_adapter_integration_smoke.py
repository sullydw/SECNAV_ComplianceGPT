#!/usr/bin/env python3
"""Phase L.32E smoke: official provider filter adapter integration.

Deterministic smoke.  Uses injected providers/fixtures only.  No live internet,
no filesystem lookup, and no static command database.
"""

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import hermes_chat_builder as hermes  # noqa: E402
import official_command_lookup_adapter as adapter  # noqa: E402
import official_command_provider as provider_module  # noqa: E402

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


class CountingProvider:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str]] = []

    def __call__(self, command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]:
        self.calls.append((role, command_text))
        return self.results


def enable() -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.reset_official_command_lookup_cache()


def disable() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.reset_official_command_lookup_cache()


def install(results: list[dict[str, Any]], *, enabled: bool = True) -> CountingProvider:
    enable() if enabled else disable()
    p = CountingProvider(results)
    adapter.register_official_command_provider(p)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)
    return p


def official_from(value: str = "Commanding Officer, Naval Example Command", *, confidence: float = 0.92, url: str = "https://www.example.navy.mil/naval-example-command", title: str = "Naval Example Command Official .mil Page", tier: str = "official_live", limitation: str | None = None, letterhead: bool = True) -> dict[str, Any]:
    resolved: dict[str, Any] = {"from": value}
    if letterhead:
        resolved.update(
            {
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            }
        )
    out: dict[str, Any] = {
        "resolved_value": resolved,
        "source_tier": tier,
        "source_title": title,
        "source_url": url,
        "confidence": confidence,
    }
    if limitation is not None:
        out["source_limitation"] = limitation
    return out


def official_to_with_bogus_letterhead() -> dict[str, Any]:
    return {
        "resolved_value": {
            "to": "Commanding Officer, Naval Example Command",
            "letterhead_top_line": "BOGUS",
            "letterhead_activity": "BOGUS ACTIVITY",
            "letterhead_address": "BOGUS ADDRESS",
            "unit_identity": "BOGUS UNIT",
        },
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official .mil Page",
        "source_url": "https://www.example.navy.mil/naval-example-command",
        "confidence": 0.92,
    }


def lookup(text: str = "Naval Example Command", role: str = "from") -> dict[str, Any] | None:
    return adapter.official_command_lookup(text, role, {})


def new_chat() -> str:
    result = hermes.start_secnav_chat()
    assert result.get("success"), result
    return str(result["chat_id"])


def latest_pending(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = list(((result.get("source_backed_candidates") or {}).get("pending") or []))
    return pending[-1] if pending else None


# S1 — adapter filters missing provenance

def test_s1_missing_provenance() -> None:
    item = official_from()
    item.pop("source_url")
    install([item])
    check("S1 missing source_url rejected", lookup() is None)


# S2 — adapter rejects disallowed official URL

def test_s2_disallowed_url() -> None:
    install([official_from(url="https://en.wikipedia.org/wiki/Naval_Example_Command")])
    check("S2 wikipedia official_live rejected", lookup() is None)


# S3 — adapter enforces confidence gate

def test_s3_confidence_gate() -> None:
    install([official_from(confidence=0.84)])
    check("S3 confidence 0.84 rejected", lookup() is None)
    install([official_from(confidence=0.85)])
    cand = lookup()
    check("S3 confidence 0.85 retained", isinstance(cand, dict))
    check("S3 retained candidate confidence", cand is not None and cand.get("confidence") == 0.85)


# S4 — adapter enforces role-specific resolved value

def test_s4_role_specific_resolved_value() -> None:
    to_only = {
        "resolved_value": {"to": "Commanding Officer, Naval Example Command"},
        "source_tier": "official_live",
        "source_title": "Official Page",
        "source_url": "https://www.example.navy.mil/naval-example-command",
        "confidence": 0.92,
    }
    install([to_only])
    check("S4 to-only result rejected for From", lookup(role="from") is None)

    from_only = official_from()
    install([from_only])
    check("S4 from-only result rejected for To", lookup(role="to") is None)


# S5 — adapter strips To letterhead through integrated filter

def test_s5_to_stripping() -> None:
    install([official_to_with_bogus_letterhead()])
    cand = lookup(role="to")
    resolved = (cand or {}).get("resolved_value") or {}
    check("S5 To candidate exists", isinstance(cand, dict))
    check("S5 To retained", resolved.get("to") == "Commanding Officer, Naval Example Command")
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
        check(f"S5 stripped {key}", key not in resolved)


# S6 — adapter preserves conflict no-guess behavior after filter

def test_s6_conflict_no_guess() -> None:
    install([official_from("Commanding Officer, Naval Example Command"), official_from("Commander, Naval Example Command", url="https://www.example.navy.mil/naval-example-alt")])
    check("S6 conflicting official results return None", lookup() is None)


# S7 — deterministic ranking for non-conflicting results

def test_s7_deterministic_ranking() -> None:
    low = official_from(confidence=0.86, url="https://www.example.navy.mil/b")
    high = official_from(confidence=0.93, url="https://www.example.navy.mil/a")
    install([low, high])
    first = lookup()
    adapter.reset_official_command_lookup_cache()
    second = lookup()
    check("S7 candidate returned", isinstance(first, dict) and isinstance(second, dict))
    check("S7 highest confidence selected", first is not None and first.get("source_url") == "https://www.example.navy.mil/a")
    check("S7 repeated calls same source", first is not None and second is not None and first.get("source_url") == second.get("source_url"))


# S8 — official_archived requires caution

def test_s8_archived_caution() -> None:
    no_caution = official_from(tier="official_archived", confidence=0.92, limitation="Official archived source candidate.")
    no_caution.pop("source_limitation")
    install([no_caution])
    check("S8 archived without caution rejected", lookup() is None)

    caution = official_from(
        tier="official_archived",
        confidence=0.92,
        limitation="Official archived source candidate; verify current validity before applying.",
    )
    install([caution])
    cand = lookup()
    check("S8 archived with caution retained", isinstance(cand, dict))
    check("S8 archived tier retained", cand is not None and cand.get("source_tier") == "official_archived")
    check("S8 caution limitation retained", cand is not None and "valid" in str(cand.get("source_limitation", "")).lower())


# S9 — secondary_credible and unresolved do not become apply-ready

def test_s9_secondary_unresolved_rejected() -> None:
    secondary = official_from(tier="secondary_credible", confidence=0.99, url="https://news.example.com/naval-example")
    install([secondary])
    check("S9 secondary_credible rejected", lookup() is None)

    unresolved = official_from(tier="unresolved", confidence=0.99)
    install([unresolved])
    check("S9 unresolved rejected", lookup() is None)


# S10 — user_provided remains user_provided

def test_s10_user_provided() -> None:
    user = {
        "resolved_value": {"from": "Commanding Officer, User Provided Command"},
        "source_tier": "user_provided",
        "source_title": "User-provided command reference",
        "source_url": "https://example.com/user-ref",
        "source_limitation": "User-provided source; confirm before applying.",
        "confidence": 0.95,
    }
    install([user])
    cand = adapter.official_command_lookup("User Provided Command", "from", {})
    check("S10 user_provided candidate returned", isinstance(cand, dict))
    check("S10 tier preserved", cand is not None and cand.get("source_tier") == "user_provided")
    check("S10 confirmation required", cand is not None and cand.get("requires_user_confirmation") is True)
    check("S10 not official_live", cand is not None and cand.get("source_tier") != "official_live")


# S11 — live gate still prevents provider/filter use

def test_s11_live_gate_blocks_provider() -> None:
    p = install([official_from()], enabled=False)
    check("S11 adapter returns None when gate unset", lookup() is None)
    check("S11 provider not called", p.calls == [])


# S12 — Hermes E2E still works through integrated filter

def test_s12_hermes_e2e() -> None:
    enable()
    fixture = {
        "input_text": "Naval Example Command",
        "role": "from",
        **official_from(),
    }
    adapter.register_fixture_official_command_provider([fixture])
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    if hasattr(adapter, "install_hermes_to_line_candidate_patch"):
        adapter.install_hermes_to_line_candidate_patch(hermes)

    chat_id = new_chat()
    result = hermes.send_secnav_chat_turn(
        chat_id,
        "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.",
    )
    payload = result.get("payload") or {}
    cand = latest_pending(result)
    check("S12 pending From candidate exists", isinstance(cand, dict) and cand.get("field") == "from")
    check("S12 provenance complete", cand is not None and all(cand.get(k) for k in ("source_title", "source_url", "source_tier", "confidence")))
    check("S12 no mutation before confirmation", payload.get("from") == "Naval Example Command")

    confirmed = hermes.send_secnav_chat_turn(chat_id, "confirm candidate")
    payload2 = confirmed.get("payload") or {}
    check("S12 confirmation succeeds", bool(confirmed.get("success")))
    check("S12 From applied", payload2.get("from") == "Commanding Officer, Naval Example Command")
    check("S12 letterhead applied", payload2.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND")

    details = hermes.send_secnav_chat_turn(
        chat_id,
        "date: 15 Aug 2026\nsignature: J. A. DOE\nbody: This letter directs a review of correspondence procedures.",
    )
    check("S12 draft preview reached", bool(details.get("success")) and details.get("phase") in {"draft_preview", "approved_ready"})
    approved = hermes.send_secnav_chat_turn(chat_id, "looks good")
    check("S12 approval succeeds", bool(approved.get("success")))
    rendered = hermes.send_secnav_chat_turn(chat_id, "make the PDF")
    check("S12 render succeeds", bool(rendered.get("success")) and rendered.get("phase") == "rendered")
    check("S12 pdf path present", bool(rendered.get("pdf_path") or rendered.get("output_path")))


# S13 — no static DB/no network proof

def test_s13_no_static_db_no_network() -> None:
    adapter_src = inspect.getsource(adapter)
    provider_src = inspect.getsource(provider_module)
    combined = adapter_src + "\n" + provider_src
    forbidden = ["import requests", "urllib.request", "http.client", "import socket", "socket."]
    for token in forbidden:
        check(f"S13 no {token}", token not in combined)
    check("S13 no command database variable", "COMMAND_DATABASE" not in combined and "STATIC_COMMAND" not in combined)
    empty = provider_module.build_fixture_provider([])
    check("S13 empty fixture provider returns empty", list(empty("Naval Example Command", "from", {})) == [])


def main() -> int:
    tests = [
        test_s1_missing_provenance,
        test_s2_disallowed_url,
        test_s3_confidence_gate,
        test_s4_role_specific_resolved_value,
        test_s5_to_stripping,
        test_s6_conflict_no_guess,
        test_s7_deterministic_ranking,
        test_s8_archived_caution,
        test_s9_secondary_unresolved_rejected,
        test_s10_user_provided,
        test_s11_live_gate_blocks_provider,
        test_s12_hermes_e2e,
        test_s13_no_static_db_no_network,
    ]
    for test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            check(test.__name__, False, repr(exc))
    print(f"\nL.32E smoke result: {PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
