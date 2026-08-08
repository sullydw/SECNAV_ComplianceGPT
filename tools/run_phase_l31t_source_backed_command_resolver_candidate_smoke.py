#!/usr/bin/env python3
"""Phase L.31T smoke: source-backed command resolver candidates are candidate-only."""

from __future__ import annotations

import sys
from pathlib import Path

THIS = Path(__file__).resolve()
REPO_ROOT = THIS.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import hermes_chat_builder as hcb  # noqa: E402

TOTAL = 0
PASS = 0
FAILURES: list[str] = []


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


def payload(result: dict) -> dict:
    return result.get("payload") or {}


def cands(result: dict) -> dict:
    return result.get("source_backed_candidates") or {"pending": [], "confirmed": [], "rejected": []}


def start() -> str:
    r = hcb.start_secnav_chat()
    check("chat starts", r.get("success", False), str(r))
    return r["chat_id"]


def send(chat_id: str, text: str) -> dict:
    return hcb.send_secnav_chat_turn(chat_id, text)


def fake_lookup(command_text: str, role: str, _state: dict) -> dict | None:
    if command_text.lower().strip() != "naval example command" or role != "from":
        return None
    return {
        "candidate_type": "command_expansion",
        "resolved_value": {
            "from": "Commanding Officer, Naval Example Command",
            "letterhead_top_line": "UNITED STATES NAVY",
            "letterhead_activity": "NAVAL EXAMPLE COMMAND",
            "letterhead_address": "NORFOLK VA 23511-0000",
        },
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official Homepage",
        "source_url": "https://www.example.navy.mil/",
        "source_limitation": "Deterministic L.31T smoke fixture; not live internet.",
        "confidence": 0.86,
        "requires_user_confirmation": True,
    }


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


def scenario_1_controlled_alias_bypasses_candidate() -> None:
    chat = start()
    r = send(chat, "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    check("S1 From controlled alias applies", p.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point", str(p))
    check("S1 To controlled alias applies", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S1 letterhead controlled From applies", p.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT", str(p))
    check("S1 no pending source candidate", len(cc.get("pending", [])) == 0, str(cc))
    check("S1 SSIC inferred", str(p.get("ssic")) == "5216", str(p))


def scenario_2_unknown_unresolved_literal() -> None:
    chat = start()
    r = send(chat, "I need a standard letter from Imaginary Training Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    check("S2 From remains literal", p.get("from") == "Imaginary Training Command", str(p))
    check("S2 To still expands", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S2 no invented letterhead", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S2 no auto source candidate", len(cc.get("pending", [])) == 0, str(cc))
    check("S2 asks for letterhead/detail", "letterhead" in str(r.get("next_step", "")).lower() or "letterhead" in str(r.get("assistant_response", "")).lower(), str(r))


def scenario_3_candidate_not_applied() -> tuple[str, dict]:
    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    pending = cc.get("pending", [])
    cand = pending[0] if pending else {}
    check("S3 source-backed candidate created", len(pending) == 1, str(cc))
    check("S3 candidate not auto-applied to From", p.get("from") == "Naval Example Command", str(p))
    check("S3 letterhead not auto-applied", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S3 candidate provenance title present", cand.get("source_title") == "Naval Example Command Official Homepage", str(cand))
    check("S3 candidate provenance URL present", cand.get("source_url") == "https://www.example.navy.mil/", str(cand))
    check("S3 candidate source tier official_live", cand.get("source_tier") == "official_live", str(cand))
    check("S3 candidate confidence present", float(cand.get("confidence", 0)) >= 0.86, str(cand))
    check("S3 confirmation required", cand.get("requires_user_confirmation") is True, str(cand))
    check("S3 not render-ready solely from candidate", not r.get("validation_ready", False), str(r))
    return chat, r


def scenario_4_confirm_candidate() -> None:
    chat, _ = scenario_3_candidate_not_applied()
    r = send(chat, "confirm candidate")
    p = payload(r)
    cc = cands(r)
    check("S4 From applied after confirmation", p.get("from") == "Commanding Officer, Naval Example Command", str(p))
    check("S4 letterhead applied after confirmation", p.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND", str(p))
    check("S4 To remains controlled alias", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S4 SSIC remains inferred", str(p.get("ssic")) == "5216", str(p))
    check("S4 candidate moved to confirmed", len(cc.get("confirmed", [])) == 1 and len(cc.get("pending", [])) == 0, str(cc))
    check("S4 asks only remaining basics", all(word in str(r.get("next_step", "")).lower() for word in ["date", "sign", "body"]), str(r))


def scenario_5_reject_candidate() -> None:
    chat = start()
    r1 = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    r2 = send(chat, "reject candidate")
    p = payload(r2) or payload(r1)
    cc = cands(r2)
    check("S5 rejected candidate recorded", len(cc.get("rejected", [])) == 1 and len(cc.get("pending", [])) == 0, str(cc))
    check("S5 From remains literal", p.get("from") == "Naval Example Command", str(p))
    check("S5 letterhead not applied", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S5 asks user for full command or letterhead", "letterhead" in str(r2.get("assistant_response", "")).lower() or "full command" in str(r2.get("assistant_response", "")).lower(), str(r2))
    r3 = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    check("S5 rejected candidate not immediately re-suggested", len(cands(r3).get("pending", [])) == 0, str(cands(r3)))


def scenario_6_complete_confirmed_path_renders() -> None:
    chat = start()
    send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    send(chat, "confirm candidate")
    r = send(chat, "Use 1 July 2026. A. B. SAMPLE will sign it. The body should say we are implementing local correspondence review procedures.")
    check("S6 reaches draft_preview", r.get("phase") == "draft_preview", str(r))
    check("S6 validation_ready true", r.get("validation_ready") is True, str(r))
    approve = send(chat, "looks good")
    check("S6 approval succeeds", approve.get("approved_ready") is True or approve.get("phase") == "approved_ready", str(approve))
    render = send(chat, "make the PDF")
    check("S6 render succeeds", render.get("success") is True and render.get("phase") == "rendered", str(render))
    pdf_text = read_pdf_text(str(render.get("pdf_path")))
    if pdf_text:
        check("S6 PDF contains source-backed letterhead", "NAVAL EXAMPLE COMMAND" in pdf_text, pdf_text[:500])
        check("S6 PDF contains source-backed From", "Commanding Officer, Naval Example Command" in pdf_text, pdf_text[:500])
        check("S6 PDF contains controlled To", "Commanding General, II Marine Expeditionary Force" in pdf_text, pdf_text[:500])
        check("S6 PDF contains signature", "A. B. SAMPLE" in pdf_text, pdf_text[:500])
    else:
        print("WARN: PDF text extraction unavailable; render success and payload checks used.")
        p = render.get("payload") or {}
        check("S6 payload contains source-backed From", p.get("from") == "Commanding Officer, Naval Example Command", str(p))
        check("S6 payload contains source-backed letterhead", p.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND", str(p))


def main() -> int:
    hcb.set_source_backed_command_lookup_adapter(fake_lookup)
    scenario_1_controlled_alias_bypasses_candidate()
    scenario_2_unknown_unresolved_literal()
    scenario_3_candidate_not_applied()
    scenario_4_confirm_candidate()
    scenario_5_reject_candidate()
    scenario_6_complete_confirmed_path_renders()
    print(f"\nL.31T source-backed candidate smoke: {PASS}/{TOTAL} PASS")
    if FAILURES:
        print("\nFAILURES:")
        for failure in FAILURES:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
