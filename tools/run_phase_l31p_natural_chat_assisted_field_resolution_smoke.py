#!/usr/bin/env python3
"""Phase L.31P smoke: natural chat assisted field resolution.

This verifies that shorthand user intake is expanded into useful SECNAV fields,
SSIC is inferred without asking the user, remaining required details are asked
in plain English, and the completed draft can still be approved and rendered.
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

    chat = start_secnav_chat()
    chat_id = chat["chat_id"]

    first_request = "I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures."
    first = send_secnav_chat_turn(chat_id, first_request)
    first_status = get_secnav_chat_status(chat_id)
    first_payload = first.get("payload") or {}
    first_text = str(first) + "\n" + str(first_status)
    first_next = str(first.get("next_step") or first_status.get("next_step") or "")
    first_assistant = str(first.get("assistant_response") or first_status.get("assistant_response") or "")
    first_combined = f"{first_next}\n{first_assistant}\n{first_text}"

    checks.append(_check("first turn did not route as revise", first.get("intent") == "say", str(first.get("intent"))))
    checks.append(_check("From expanded from MCAS shorthand", _contains("Commanding Officer, Marine Corps Air Station New River", first_payload, first_text)))
    checks.append(_check("To expanded from II MEF shorthand", _contains("Commanding General, II Marine Expeditionary Force", first_payload, first_text)))
    checks.append(_check("Subject inferred from about phrase", _contains("REVIEW OF CORRESPONDENCE PROCEDURES", first_payload, first_text)))
    checks.append(_check("Letterhead inferred for MCAS New River", _contains("MARINE CORPS AIR STATION NEW RIVER", first_payload, first_text) and _contains("JACKSONVILLE NC 28545-0000", first_payload, first_text)))
    checks.append(_check("SSIC 5216 inferred", _contains("5216", first_payload, first_text)))
    checks.append(_check("Does not ask for SSIC", "ssic" not in first_next.lower() and "ssic" not in first_assistant.lower()))
    checks.append(_check("Does not ask for originator code", "originator" not in first_next.lower() and "originator" not in first_assistant.lower()))
    checks.append(_check("Asks for date in plain English", "date" in first_combined.lower()))
    checks.append(_check("Asks for signer in plain English", "sign" in first_combined.lower()))
    checks.append(_check("Asks for body in plain English", "body" in first_combined.lower()))

    followup = "Use 1 July 2026. A. B. SAMPLE will sign it. The body should say we are implementing local correspondence review procedures."
    second = send_secnav_chat_turn(chat_id, followup)
    second_status = get_secnav_chat_status(chat_id)
    second_payload = second.get("payload") or {}
    second_text = str(second) + "\n" + str(second_status)

    checks.append(_check("second turn reached draft_preview", second.get("phase") == "draft_preview", str(second.get("phase"))))
    checks.append(_check("validation_ready=True after follow-up", bool(second.get("validation_ready") or second_status.get("validation_ready"))))
    checks.append(_check("approved_ready=False before approval", not bool(second.get("approved_ready") or second_status.get("approved_ready"))))
    checks.append(_check("Date captured", _contains("1 July 2026", second_payload, second_text) or _contains("1 Jul 26", second_text)))
    checks.append(_check("Signer captured", _contains("A. B. SAMPLE", second_payload, second_text)))
    checks.append(_check("Body captured", _contains("implementing local correspondence review procedures", second_payload, second_text)))
    checks.append(_check("SSIC remains present", _contains("5216", second_payload, second_text)))
    checks.append(_check("Preview/next action says review or approve", any(token in str(second).lower() for token in ["review", "approve", "looks good"])))

    approved = send_secnav_chat_turn(chat_id, "looks good")
    checks.append(_check("approval succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize")), str(approved.get("phase"))))
    checks.append(_check("post-approval mentions PDF/render", any(token in str(approved).lower() for token in ["make the pdf", "render", "pdf"])))

    rendered = send_secnav_chat_turn(chat_id, "make the PDF")
    pdf_path = rendered.get("pdf_path") or ""
    checks.append(_check("render succeeds", bool(rendered.get("success") and pdf_path), str(pdf_path)))

    text = _pdf_text(str(pdf_path)) if pdf_path else ""
    checks.append(_check("PDF contains letterhead", "UNITED STATES MARINE CORPS" in text and "MARINE CORPS AIR STATION NEW RIVER" in text))
    checks.append(_check("PDF contains inferred SSIC", "5216" in text))
    checks.append(_check("PDF contains date", "1 Jul 26" in text))
    checks.append(_check("PDF contains From", "Commanding Officer, Marine Corps Air Station New River" in text))
    checks.append(_check("PDF contains To", "Commanding General, II Marine Expeditionary Force" in text))
    checks.append(_check("PDF contains subject", "REVIEW OF CORRESPONDENCE PROCEDURES" in text))
    checks.append(_check("PDF contains body", "implementing local correspondence review procedures" in text))
    checks.append(_check("PDF contains signature", "A. B. SAMPLE" in text))

    passed = sum(1 for item in checks if item)
    total = len(checks)
    print(f"\nL.31P smoke: {passed}/{total} PASS")
    if passed != total:
        print("\nFirst result:", first)
        print("\nFirst status:", first_status)
        print("\nSecond result:", second)
        print("\nSecond status:", second_status)
        print("\nApproved:", approved)
        print("\nRendered:", rendered)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
