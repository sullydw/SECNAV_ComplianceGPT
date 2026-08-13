#!/usr/bin/env python3
"""Phase L.31X smoke: official-source lookup candidates stay candidate-only."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

THIS = Path(__file__).resolve()
REPO_ROOT = THIS.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import hermes_chat_builder as hcb  # noqa: E402
import official_command_lookup_adapter as adapter  # noqa: E402

TOTAL = 0
PASS = 0
FAILURES: list[str] = []
CALLS: list[tuple[str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global TOTAL, PASS
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"PASS: {name}")
    else:
        msg = f"FAIL: {name}" + (f" -- {detail}" if detail else "")
        FAILURES.append(msg)
        print(msg)


def payload(result: dict[str, Any]) -> dict[str, Any]:
    return result.get("payload") or {}


def cands(result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return result.get("source_backed_candidates") or {"pending": [], "confirmed": [], "rejected": []}


def start() -> str:
    r = hcb.start_secnav_chat()
    check("chat starts", r.get("success", False), str(r))
    return r["chat_id"]


def send(chat_id: str, text: str) -> dict[str, Any]:
    return hcb.send_secnav_chat_turn(chat_id, text)


def official_provider(command_text: str, role: str, _state: dict[str, Any]):
    CALLS.append((role, command_text))
    if command_text.lower().strip() != "naval example command":
        return []
    resolved = {role: "Commanding Officer, Naval Example Command" if role == "from" else "Commander, Naval Example Command"}
    if role == "from":
        resolved.update(
            {
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            }
        )
    else:
        resolved.update(
            {
                "letterhead_top_line": "SHOULD NOT APPLY",
                "letterhead_activity": "SHOULD NOT APPLY",
                "letterhead_address": "SHOULD NOT APPLY",
            }
        )
    return [
        {
            "candidate_type": "command_expansion",
            "resolved_value": resolved,
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official Homepage",
            "source_url": "https://www.example.navy.mil/",
            "source_limitation": "Deterministic L.31X smoke fixture; not live internet.",
            "confidence": 0.91,
        }
    ]


def low_confidence_provider(command_text: str, role: str, _state: dict[str, Any]):
    CALLS.append((role, command_text))
    return [
        {
            "resolved_value": {role: "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Low Confidence Official Page",
            "source_url": "https://www.example.navy.mil/low",
            "confidence": 0.60,
        }
    ]


def unofficial_provider(command_text: str, role: str, _state: dict[str, Any]):
    CALLS.append((role, command_text))
    return [
        {
            "resolved_value": {role: "Commanding Officer, Naval Example Command"},
            "source_tier": "secondary_credible",
            "source_title": "Unofficial Directory",
            "source_url": "https://example.com/naval-example-command",
            "confidence": 0.95,
        }
    ]


def conflicting_provider(command_text: str, role: str, _state: dict[str, Any]):
    CALLS.append((role, command_text))
    return [
        {
            "resolved_value": {role: "Commanding Officer, Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Official Page A",
            "source_url": "https://www.example.navy.mil/a",
            "confidence": 0.91,
        },
        {
            "resolved_value": {role: "Commander, Different Naval Example Command"},
            "source_tier": "official_live",
            "source_title": "Official Page B",
            "source_url": "https://www.example.navy.mil/b",
            "confidence": 0.90,
        },
    ]


def enable(provider) -> None:
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "1"
    adapter.set_official_command_search_provider(provider)
    hcb.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    CALLS.clear()


def disable() -> None:
    os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    adapter.set_official_command_search_provider(None)
    hcb.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    CALLS.clear()


def read_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def scenario_1_disabled_noop() -> None:
    disable()
    result = adapter.official_command_lookup("Naval Example Command", "from", {})
    check("S1 disabled lookup returns None", result is None, str(result))
    check("S1 disabled lookup makes no provider calls", CALLS == [], str(CALLS))


def scenario_2_controlled_alias_bypasses_lookup() -> None:
    enable(official_provider)
    chat = start()
    r = send(chat, "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    check("S2 From controlled alias applies", p.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point", str(p))
    check("S2 To controlled alias applies", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S2 controlled From letterhead applies", p.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT", str(p))
    check("S2 no pending candidate", len(cands(r).get("pending", [])) == 0, str(cands(r)))
    check("S2 lookup provider not called", CALLS == [], str(CALLS))


def scenario_3_from_candidate_not_applied() -> tuple[str, dict[str, Any]]:
    enable(official_provider)
    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    pending = cands(r).get("pending", [])
    cand = pending[0] if pending else {}
    check("S3 official From candidate exists", len(pending) == 1, str(cands(r)))
    check("S3 From not auto-applied", p.get("from") == "Naval Example Command", str(p))
    check("S3 letterhead not auto-applied", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S3 source tier official_live", cand.get("source_tier") == "official_live", str(cand))
    check("S3 source title present", bool(cand.get("source_title")), str(cand))
    check("S3 source URL present", bool(cand.get("source_url")), str(cand))
    check("S3 confidence gate passed", float(cand.get("confidence", 0)) >= 0.85, str(cand))
    check("S3 confirmation required", cand.get("requires_user_confirmation") is True, str(cand))
    return chat, r


def scenario_4_confirm_from_candidate() -> None:
    chat, _ = scenario_3_from_candidate_not_applied()
    r = send(chat, "confirm candidate")
    p = payload(r)
    cc = cands(r)
    check("S4 From applied", p.get("from") == "Commanding Officer, Naval Example Command", str(p))
    check("S4 top line applied", p.get("letterhead_top_line") == "DEPARTMENT OF THE NAVY", str(p))
    check("S4 activity applied", p.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND", str(p))
    check("S4 address applied", p.get("letterhead_address") == "NORFOLK VA 23511-0000", str(p))
    check("S4 candidate confirmed", len(cc.get("confirmed", [])) == 1 and len(cc.get("pending", [])) == 0, str(cc))
    check("S4 no approval/render shortcut", not r.get("approved_ready", False), str(r))


def scenario_5_to_candidate_adapter_strips_letterhead() -> None:
    enable(official_provider)
    result = adapter.official_command_lookup("Naval Example Command", "to", {"enable_official_command_lookup": True})
    rv = (result or {}).get("resolved_value") or {}
    check("S5 To candidate returned", isinstance(result, dict), str(result))
    check("S5 To value present", rv.get("to") == "Commander, Naval Example Command", str(rv))
    check("S5 To candidate has no top line", "letterhead_top_line" not in rv, str(rv))
    check("S5 To candidate has no activity", "letterhead_activity" not in rv, str(rv))
    check("S5 To candidate has no address", "letterhead_address" not in rv, str(rv))


def scenario_6_low_confidence_no_candidate() -> None:
    enable(low_confidence_provider)
    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    check("S6 no pending low confidence candidate", len(cands(r).get("pending", [])) == 0, str(cands(r)))
    check("S6 From remains literal", p.get("from") == "Naval Example Command", str(p))
    check("S6 no letterhead invented", not p.get("letterhead_activity"), str(p))


def scenario_7_unofficial_no_candidate() -> None:
    enable(unofficial_provider)
    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    check("S7 unofficial source no pending candidate", len(cands(r).get("pending", [])) == 0, str(cands(r)))
    check("S7 command remains literal", p.get("from") == "Naval Example Command", str(p))


def scenario_8_conflict_no_candidate() -> None:
    enable(conflicting_provider)
    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    check("S8 conflicting official results no candidate", len(cands(r).get("pending", [])) == 0, str(cands(r)))
    check("S8 command remains literal", p.get("from") == "Naval Example Command", str(p))


def scenario_9_reject_no_resuggest() -> None:
    enable(official_provider)
    chat = start()
    send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    r2 = send(chat, "reject candidate")
    r3 = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    check("S9 rejected candidate recorded", len(cands(r2).get("rejected", [])) == 1, str(cands(r2)))
    check("S9 no immediate re-suggestion", len(cands(r3).get("pending", [])) == 0, str(cands(r3)))


def scenario_10_confirmed_path_renders() -> None:
    enable(official_provider)
    chat = start()
    send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    send(chat, "confirm candidate")
    r = send(chat, "Use 1 July 2026. A. B. SAMPLE will sign it. The body should say we are implementing local correspondence review procedures.")
    check("S10 reaches draft_preview", r.get("phase") == "draft_preview", str(r))
    check("S10 validation_ready", r.get("validation_ready") is True, str(r))
    approve = send(chat, "looks good")
    check("S10 approval succeeds", approve.get("approved_ready") is True or approve.get("phase") == "approved_ready", str(approve))
    render = send(chat, "make the PDF")
    check("S10 render succeeds", render.get("success") is True and render.get("phase") == "rendered", str(render))
    text = read_pdf_text(str(render.get("pdf_path")))
    if text:
        check("S10 PDF source-backed letterhead", "NAVAL EXAMPLE COMMAND" in text, text[:500])
        check("S10 PDF source-backed From", "Commanding Officer, Naval Example Command" in text, text[:500])
        check("S10 PDF controlled To", "Commanding General, II Marine Expeditionary Force" in text, text[:500])
        check("S10 PDF signature", "A. B. SAMPLE" in text, text[:500])
    else:
        p = render.get("payload") or {}
        check("S10 payload source-backed From", p.get("from") == "Commanding Officer, Naval Example Command", str(p))
        check("S10 payload source-backed letterhead", p.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND", str(p))


def main() -> int:
    scenario_1_disabled_noop()
    scenario_2_controlled_alias_bypasses_lookup()
    scenario_3_from_candidate_not_applied()
    scenario_4_confirm_from_candidate()
    scenario_5_to_candidate_adapter_strips_letterhead()
    scenario_6_low_confidence_no_candidate()
    scenario_7_unofficial_no_candidate()
    scenario_8_conflict_no_candidate()
    scenario_9_reject_no_resuggest()
    scenario_10_confirmed_path_renders()
    disable()
    print(f"\nL.31X official source lookup candidate smoke: {PASS}/{TOTAL} PASS")
    if FAILURES:
        print("\nFAILURES:")
        for failure in FAILURES:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
