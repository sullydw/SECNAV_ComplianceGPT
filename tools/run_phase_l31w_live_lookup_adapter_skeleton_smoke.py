#!/usr/bin/env python3
"""Phase L.31W smoke: live lookup adapter skeleton is no-op and changes nothing."""

from __future__ import annotations

import sys
from pathlib import Path

THIS = Path(__file__).resolve()
REPO_ROOT = THIS.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import hermes_chat_builder as hcb  # noqa: E402
import official_command_lookup_adapter as ocla  # noqa: E402

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


# ---------------------------------------------------------------------------
# S1 — Adapter module imports and returns None
# ---------------------------------------------------------------------------
def scenario_1_adapter_imports_and_returns_none() -> None:
    result = ocla.official_command_lookup("Some Command", "from", {})
    check("S1 adapter returns None", result is None, str(result))
    result2 = ocla.official_command_lookup("II MEF", "to", {"rejected": []})
    check("S1 adapter returns None for known alias too", result2 is None, str(result2))
    result3 = ocla.official_command_lookup("", "from")
    check("S1 adapter returns None with no state", result3 is None, str(result3))


# ---------------------------------------------------------------------------
# S2 — Controlled aliases still bypass adapter
# ---------------------------------------------------------------------------
def scenario_2_controlled_aliases_bypass_adapter() -> None:
    chat = start()
    r = send(chat, "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    check("S2 From controlled alias applies", p.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point", str(p))
    check("S2 To controlled alias applies", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S2 letterhead controlled From applies", p.get("letterhead_activity") == "MARINE CORPS AIR STATION CHERRY POINT", str(p))
    check("S2 no pending source candidate", len(cc.get("pending", [])) == 0, str(cc))
    check("S2 adapter not required", r.get("source_backed_candidate") is None, str(r))


# ---------------------------------------------------------------------------
# S3 — Unknown command remains literal with no-op adapter
# ---------------------------------------------------------------------------
def scenario_3_unknown_command_remains_literal() -> None:
    chat = start()
    r = send(chat, "I need a standard letter from Imaginary Training Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    check("S3 From remains literal", p.get("from") == "Imaginary Training Command", str(p))
    check("S3 To still expands", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))
    check("S3 no invented letterhead", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S3 no auto source candidate", len(cc.get("pending", [])) == 0, str(cc))
    check("S3 asks for letterhead/detail", "letterhead" in str(r.get("next_step", "")).lower() or "letterhead" in str(r.get("assistant_response", "")).lower(), str(r))


# ---------------------------------------------------------------------------
# S4 — Existing L.31T injectable fake resolver still works
# ---------------------------------------------------------------------------
def fake_lookup(command_text: str, role: str, _state: dict) -> dict | None:
    if command_text.lower().strip() != "naval example command" or role != "from":
        return None
    return {
        "candidate_type": "command_expansion",
        "resolved_value": {
            "from": "Commanding Officer, Naval Example Command",
            "letterhead_top_line": "DEPARTMENT OF THE NAVY",
            "letterhead_activity": "NAVAL EXAMPLE COMMAND",
            "letterhead_address": "NORFOLK VA 23511-0000",
        },
        "source_tier": "official_live",
        "source_title": "Naval Example Command Official Homepage",
        "source_url": "https://www.example.navy.mil/",
        "source_limitation": "Deterministic L.31W smoke fixture; not live internet.",
        "confidence": 0.86,
        "requires_user_confirmation": True,
    }


def scenario_4_l31t_fake_resolver_still_works() -> None:
    # Inject the fake resolver (overrides the no-op default)
    hcb.set_source_backed_command_lookup_adapter(fake_lookup)

    chat = start()
    r = send(chat, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    p = payload(r)
    cc = cands(r)
    pending = cc.get("pending", [])
    cand = pending[0] if pending else {}
    check("S4 source-backed candidate created", len(pending) == 1, str(cc))
    check("S4 candidate not auto-applied to From", p.get("from") == "Naval Example Command", str(p))
    check("S4 letterhead not auto-applied", not p.get("letterhead_activity") and not p.get("letterhead_top_line"), str(p))
    check("S4 candidate provenance title present", cand.get("source_title") == "Naval Example Command Official Homepage", str(cand))
    check("S4 candidate source tier official_live", cand.get("source_tier") == "official_live", str(cand))
    check("S4 confirmation required", cand.get("requires_user_confirmation") is True, str(cand))

    # Confirm candidate
    r2 = send(chat, "confirm candidate")
    p2 = payload(r2)
    cc2 = cands(r2)
    check("S4 From applied after confirmation", p2.get("from") == "Commanding Officer, Naval Example Command", str(p2))
    check("S4 letterhead applied after confirmation", p2.get("letterhead_activity") == "NAVAL EXAMPLE COMMAND", str(p2))
    check("S4 candidate moved to confirmed", len(cc2.get("confirmed", [])) == 1 and len(cc2.get("pending", [])) == 0, str(cc2))

    # Reject candidate (fresh chat)
    chat2 = start()
    r1 = send(chat2, "I need a standard letter from Naval Example Command to II MEF about reviewing correspondence procedures.")
    r3 = send(chat2, "reject candidate")
    p3 = payload(r3) or payload(r1)
    cc3 = cands(r3)
    check("S4 rejected candidate recorded", len(cc3.get("rejected", [])) == 1 and len(cc3.get("pending", [])) == 0, str(cc3))
    check("S4 From remains literal after rejection", p3.get("from") == "Naval Example Command", str(p3))
    check("S4 letterhead not applied after rejection", not p3.get("letterhead_activity") and not p3.get("letterhead_top_line"), str(p3))

    # Restore no-op adapter for subsequent scenarios
    hcb.set_source_backed_command_lookup_adapter(ocla.official_command_lookup)


# ---------------------------------------------------------------------------
# S5 — No render behavior regression
# ---------------------------------------------------------------------------
def scenario_5_render_still_succeeds() -> None:
    chat = start()
    send(chat, "I need a standard letter from MCAS Cherry Point to II MEF about reviewing correspondence procedures.")
    r = send(chat, "Use 1 July 2026. A. B. SAMPLE will sign it. The body should say we are implementing local correspondence review procedures.")
    check("S5 reaches draft_preview", r.get("phase") == "draft_preview", str(r))
    check("S5 validation_ready true", r.get("validation_ready") is True, str(r))
    approve = send(chat, "looks good")
    check("S5 approval succeeds", approve.get("approved_ready") is True or approve.get("phase") == "approved_ready", str(approve))
    render = send(chat, "make the PDF")
    check("S5 render succeeds", render.get("success") is True and render.get("phase") == "rendered", str(render))
    pdf_text = read_pdf_text(str(render.get("pdf_path")))
    if pdf_text:
        check("S5 PDF contains controlled From", "Commanding Officer, Marine Corps Air Station Cherry Point" in pdf_text, pdf_text[:500])
        check("S5 PDF contains controlled To", "Commanding General, II Marine Expeditionary Force" in pdf_text, pdf_text[:500])
        check("S5 PDF contains signature", "A. B. SAMPLE" in pdf_text, pdf_text[:500])
    else:
        print("WARN: PDF text extraction unavailable; render success and payload checks used.")
        p = render.get("payload") or {}
        check("S5 payload contains controlled From", p.get("from") == "Commanding Officer, Marine Corps Air Station Cherry Point", str(p))
        check("S5 payload contains controlled To", p.get("to") == "Commanding General, II Marine Expeditionary Force", str(p))


# ---------------------------------------------------------------------------
def main() -> int:
    scenario_1_adapter_imports_and_returns_none()
    scenario_2_controlled_aliases_bypass_adapter()
    scenario_3_unknown_command_remains_literal()
    scenario_4_l31t_fake_resolver_still_works()
    scenario_5_render_still_succeeds()
    print(f"\nL.31W live lookup adapter skeleton smoke: {PASS}/{TOTAL} PASS")
    if FAILURES:
        print("\nFAILURES:")
        for failure in FAILURES:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
