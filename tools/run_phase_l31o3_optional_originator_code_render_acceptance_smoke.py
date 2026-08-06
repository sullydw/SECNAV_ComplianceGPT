#!/usr/bin/env python3
"""Phase L.31O-3 smoke: optional originator code render acceptance.

This verifies that when the user provides an optional originator/office code,
Hermes preserves it through preview/approval/render and the final PDF places it
in the sender-symbol block between SSIC and date.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from hermes_chat_builder import (  # noqa: E402
    get_secnav_chat_status,
    send_secnav_chat_turn,
    start_secnav_chat,
)


def _pdf_text(path: str) -> str:
    pdf_path = Path(path)
    try:
        import fitz  # type: ignore

        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception:
        return pdf_path.read_bytes().decode("latin-1", errors="ignore")


def _contains(value: str, *haystacks: object) -> bool:
    needle = str(value)
    return any(needle in str(item or "") for item in haystacks)


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    return condition


def main() -> int:
    checks: list[bool] = []
    request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, originator code S-1, and make the body about implementing local correspondence review procedures.

letterhead_top_line: UNITED STATES MARINE CORPS
letterhead_activity: MARINE CORPS AIR STATION NEW RIVER
letterhead_address: JACKSONVILLE NC 28545-0000"""

    chat = start_secnav_chat()
    chat_id = chat["chat_id"]
    first = send_secnav_chat_turn(chat_id, request)
    status = get_secnav_chat_status(chat_id)

    preview_text = str(first.get("preview_text") or status.get("preview_text") or "")
    first_text = str(first)
    status_text = str(status)
    payload = first.get("payload") or {}
    ssic_value = payload.get("ssic") if isinstance(payload, dict) else None
    originator_value = payload.get("originator_code") if isinstance(payload, dict) else None
    next_step_text = str(first.get("next_step", "")).lower()

    checks.append(_check("first turn reached draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("validation_ready=True", bool(first.get("validation_ready") or status.get("validation_ready"))))
    checks.append(_check("SSIC 5216 present before approval", _contains("5216", preview_text, first_text, status_text, ssic_value), f"ssic={ssic_value!r}"))
    checks.append(_check("originator code S-1 present before approval", _contains("S-1", preview_text, first_text, status_text, originator_value), f"originator_code={originator_value!r}"))
    checks.append(_check("NEXT ACTION does not ask for SSIC", "ssic" not in next_step_text))
    checks.append(_check("NEXT ACTION does not ask for originator code", "originator" not in next_step_text))

    approved = send_secnav_chat_turn(chat_id, "looks good")
    checks.append(_check("approval succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize")), str(approved.get("phase"))))

    rendered = send_secnav_chat_turn(chat_id, "make the PDF")
    pdf_path = rendered.get("pdf_path") or ""
    checks.append(_check("render succeeds", bool(rendered.get("success") and pdf_path), str(pdf_path)))

    text = _pdf_text(str(pdf_path)) if pdf_path else ""
    idx_5216 = text.find("5216")
    idx_originator = text.find("S-1")
    idx_date = text.find("1 Jul 26")
    idx_from = text.find("From:")
    idx_body = text.find("This letter addresses")
    checks.append(_check("PDF contains 5216", idx_5216 >= 0))
    checks.append(_check("PDF contains S-1", idx_originator >= 0))
    checks.append(_check(
        "sender-symbol order is 5216, S-1, date, From",
        idx_5216 >= 0 and idx_originator > idx_5216 and idx_date > idx_originator and idx_from > idx_date,
        f"5216={idx_5216}, S-1={idx_originator}, date={idx_date}, from={idx_from}",
    ))
    checks.append(_check("body text remains present", idx_body >= 0))

    passed = sum(1 for item in checks if item)
    total = len(checks)
    print(f"\nL.31O-3 smoke: {passed}/{total} PASS")
    if passed != total:
        print("\nFirst result:", first)
        print("\nStatus:", status)
        print("\nRendered:", rendered)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
