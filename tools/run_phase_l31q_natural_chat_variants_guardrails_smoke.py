#!/usr/bin/env python3
"""Phase L.31Q smoke: natural chat variants and guardrails.

This smoke runs separate fresh chats across realistic user phrasings to prove
that the accepted natural-chat/PDF path is stable without changing renderer,
validator, or rule files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from hermes_chat_builder import (  # noqa: E402
    get_secnav_chat_status,
    send_secnav_chat_turn,
    start_secnav_chat,
)


CANON_FROM = "Commanding Officer, Marine Corps Air Station New River"
CANON_TO = "Commanding General, II Marine Expeditionary Force"
CANON_SUBJ = "REVIEW OF CORRESPONDENCE PROCEDURES"
CANON_LH = "MARINE CORPS AIR STATION NEW RIVER"
CANON_ADDR = "JACKSONVILLE NC 28545-0000"
COMPLETE = (
    "I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures. "
    "Use 1 July 2026. A. B. SAMPLE will sign it. "
    "The body should say we are implementing local correspondence review procedures."
)
COMPLETE_WITH_ORIG = (
    "I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures. "
    "Use originator code S-1. Use 1 July 2026. A. B. SAMPLE will sign it. "
    "The body should say we are implementing local correspondence review procedures."
)
REVISE_BODY = "Change the body to say the command is updating local correspondence routing and review procedures."


def _pdf_text(path: str) -> str:
    pdf_path = Path(path)
    try:
        import fitz  # type: ignore

        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception:
        return pdf_path.read_bytes().decode("latin-1", errors="ignore")


def _blob(*values: object) -> str:
    return "\n".join(str(v or "") for v in values)


def _contains(value: str, *haystacks: object) -> bool:
    return value in _blob(*haystacks)


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload") or {}
    return payload if isinstance(payload, dict) else {}


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    return condition


def _start_and_send(text: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    chat = start_secnav_chat()
    chat_id = chat["chat_id"]
    first = send_secnav_chat_turn(chat_id, text)
    status = get_secnav_chat_status(chat_id)
    return chat_id, first, status


def _approve_and_render(chat_id: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    approved = send_secnav_chat_turn(chat_id, "looks good")
    rendered = send_secnav_chat_turn(chat_id, "make the PDF")
    pdf_path = rendered.get("pdf_path") or ""
    text = _pdf_text(str(pdf_path)) if pdf_path else ""
    return approved, rendered, text


def _check_common_inferred(checks: list[bool], label: str, first: dict[str, Any], status: dict[str, Any]) -> None:
    payload = _payload(first)
    blob = _blob(first, status, payload)
    next_text = _blob(first.get("next_step"), first.get("assistant_response"), status.get("next_step"), status.get("assistant_response")).lower()
    checks.append(_check(f"{label}: From expanded", CANON_FROM in blob))
    checks.append(_check(f"{label}: To expanded", CANON_TO in blob))
    checks.append(_check(f"{label}: subject inferred", CANON_SUBJ in blob or "CORRESPONDENCE REVIEW PROCEDURES" in blob))
    checks.append(_check(f"{label}: letterhead inferred", CANON_LH in blob and CANON_ADDR in blob))
    checks.append(_check(f"{label}: SSIC 5216 inferred", "5216" in blob))
    checks.append(_check(f"{label}: does not ask for SSIC", "ssic" not in next_text))
    checks.append(_check(f"{label}: does not ask for originator code", "originator" not in next_text))


def main() -> int:
    checks: list[bool] = []

    print("\nScenario 1 — Existing accepted shorthand")
    _, first, status = _start_and_send("I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures.")
    _check_common_inferred(checks, "S1", first, status)

    print("\nScenario 2 — Alternate shorthand")
    _, first, status = _start_and_send("Prepare a standard letter from New River air station to Second MEF about correspondence review procedures.")
    _check_common_inferred(checks, "S2", first, status)

    print("\nScenario 3 — Title shorthand")
    _, first, status = _start_and_send("Draft a letter from Commanding Officer MCAS New River to CG II MEF about reviewing correspondence procedures.")
    blob = _blob(first, status, _payload(first))
    _check_common_inferred(checks, "S3", first, status)
    checks.append(_check("S3: no duplicate Commanding Officer title", "Commanding Officer, Commanding Officer" not in blob))
    checks.append(_check("S3: no duplicate Commanding General title", "Commanding General, Commanding General" not in blob))

    print("\nScenario 4 — Complete first-turn request")
    chat_id, first, status = _start_and_send(COMPLETE)
    payload = _payload(first)
    blob = _blob(first, status, payload)
    checks.append(_check("S4: reaches draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("S4: validation_ready=True", bool(first.get("validation_ready") or status.get("validation_ready"))))
    checks.append(_check("S4: approved_ready=False before approval", not bool(first.get("approved_ready") or status.get("approved_ready"))))
    checks.append(_check("S4: SSIC 5216 present", "5216" in blob))
    approved, rendered, pdf_text = _approve_and_render(chat_id)
    checks.append(_check("S4: approval succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize")), str(approved.get("phase"))))
    checks.append(_check("S4: render succeeds", bool(rendered.get("success") and rendered.get("pdf_path")), str(rendered.get("pdf_path"))))
    checks.append(_check("S4: PDF has core content", all(x in pdf_text for x in [CANON_LH, "5216", "1 Jul 26", CANON_FROM, CANON_TO, CANON_SUBJ, "A. B. SAMPLE"])))

    print("\nScenario 5 — Originator code first-turn request")
    chat_id, first, status = _start_and_send(COMPLETE_WITH_ORIG)
    blob = _blob(first, status, _payload(first))
    checks.append(_check("S5: reaches draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("S5: SSIC 5216 present", "5216" in blob))
    checks.append(_check("S5: originator_code S-1 present", "S-1" in blob))
    _, rendered, pdf_text = _approve_and_render(chat_id)
    idx_5216 = pdf_text.find("5216")
    idx_orig = pdf_text.find("S-1")
    idx_date = pdf_text.find("1 Jul 26")
    idx_from = pdf_text.find("From:")
    checks.append(_check("S5: render succeeds", bool(rendered.get("success") and rendered.get("pdf_path"))))
    checks.append(_check("S5: PDF order 5216 < S-1 < date < From", idx_5216 >= 0 and idx_orig > idx_5216 and idx_date > idx_orig and idx_from > idx_date, f"5216={idx_5216}, S-1={idx_orig}, date={idx_date}, from={idx_from}"))

    print("\nScenario 6 — No optional originator code")
    chat_id, first, status = _start_and_send(COMPLETE)
    next_text = _blob(first.get("next_step"), first.get("assistant_response"), status.get("next_step"), status.get("assistant_response")).lower()
    checks.append(_check("S6: reaches draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("S6: validation_ready=True", bool(first.get("validation_ready") or status.get("validation_ready"))))
    checks.append(_check("S6: does not ask for originator code", "originator" not in next_text))
    _, rendered, pdf_text = _approve_and_render(chat_id)
    idx_5216 = pdf_text.find("5216")
    idx_date = pdf_text.find("1 Jul 26")
    idx_from = pdf_text.find("From:")
    checks.append(_check("S6: render succeeds", bool(rendered.get("success") and rendered.get("pdf_path"))))
    checks.append(_check("S6: PDF order 5216 < date < From", idx_5216 >= 0 and idx_date > idx_5216 and idx_from > idx_date, f"5216={idx_5216}, date={idx_date}, from={idx_from}"))
    checks.append(_check("S6: PDF does not contain S-1", "S-1" not in pdf_text))

    print("\nScenario 7 — Revise before approval")
    chat_id, first, _ = _start_and_send(COMPLETE)
    revised = send_secnav_chat_turn(chat_id, REVISE_BODY)
    rev_blob = _blob(revised, _payload(revised))
    checks.append(_check("S7: payload changes", bool(revised.get("payload_changed"))))
    checks.append(_check("S7: still not approved", not bool(revised.get("approved_ready"))))
    checks.append(_check("S7: draft_preview remains available", revised.get("phase") == "draft_preview", str(revised.get("phase"))))
    checks.append(_check("S7: updated body visible before approval", "updating local correspondence routing" in rev_blob.lower()))
    _, rendered, pdf_text = _approve_and_render(chat_id)
    checks.append(_check("S7: render succeeds after approval", bool(rendered.get("success") and rendered.get("pdf_path"))))
    checks.append(_check("S7: updated body appears in PDF", "updating local correspondence routing" in pdf_text.lower()))

    print("\nScenario 8 — Revise after approval clears approval")
    chat_id, first, _ = _start_and_send(COMPLETE)
    approved = send_secnav_chat_turn(chat_id, "looks good")
    checks.append(_check("S8: initial approval succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize"))))
    revised = send_secnav_chat_turn(chat_id, REVISE_BODY)
    checks.append(_check("S8: payload_changed=True", bool(revised.get("payload_changed"))))
    checks.append(_check("S8: approval_cleared=True", bool(revised.get("approval_cleared"))))
    checks.append(_check("S8: approved_ready=False after revision", not bool(revised.get("approved_ready"))))
    blocked = send_secnav_chat_turn(chat_id, "make the PDF")
    checks.append(_check("S8: render blocked until re-approved", not bool(blocked.get("success")) and not blocked.get("pdf_path"), str(blocked.get("phase"))))
    reapproved, rendered, pdf_text = _approve_and_render(chat_id)
    checks.append(_check("S8: re-approval succeeds", bool(reapproved.get("approved_ready") or reapproved.get("approved_for_finalize"))))
    checks.append(_check("S8: render succeeds after re-approval", bool(rendered.get("success") and rendered.get("pdf_path"))))
    checks.append(_check("S8: updated body appears in final PDF", "updating local correspondence routing" in pdf_text.lower()))

    passed = sum(1 for item in checks if item)
    total = len(checks)
    print(f"\nL.31Q smoke: {passed}/{total} PASS")
    if passed != total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())