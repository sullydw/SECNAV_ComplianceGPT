#!/usr/bin/env python3
"""Phase L.31O-2 smoke: nonblocking SSIC assisted resolution.

This verifies that a user can omit SSIC, Hermes infers 5216 for a
correspondence-procedure subject, preview/render do not block for SSIC, and the
final PDF contains the inferred SSIC before the date and From line.
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
        # Last-resort fallback keeps the smoke informative if PyMuPDF is missing.
        return pdf_path.read_bytes().decode("latin-1", errors="ignore")


def _contains_5216(*values: object) -> bool:
    return any("5216" in str(value or "") for value in values)


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    return condition


def main() -> int:
    checks: list[bool] = []
    request = """I need a standard letter from Commanding Officer, Marine Corps Air Station New River to Commanding General, II Marine Expeditionary Force. Use the date 1 July 2026, signer A. B. SAMPLE, subject REVIEW OF CORRESPONDENCE PROCEDURES, and make the body about implementing local correspondence review procedures.

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

    checks.append(_check("first turn reached draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("validation_ready=True", bool(first.get("validation_ready") or status.get("validation_ready"))))
    checks.append(_check("NEXT ACTION does not ask for SSIC", "ssic" not in str(first.get("next_step", "")).lower()))
    checks.append(_check("SSIC 5216 present before approval", _contains_5216(preview_text, first_text, status_text, ssic_value), f"ssic={ssic_value!r}"))

    approved = send_secnav_chat_turn(chat_id, "looks good")
    checks.append(_check("approval succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize")), str(approved.get("phase"))))
    checks.append(_check("post-approval guidance mentions PDF/render", any(token in str(approved).lower() for token in ["make the pdf", "render", "pdf"])))

    rendered = send_secnav_chat_turn(chat_id, "make the PDF")
    pdf_path = rendered.get("pdf_path") or ""
    checks.append(_check("render succeeds", bool(rendered.get("success") and pdf_path), str(pdf_path)))

    text = _pdf_text(str(pdf_path)) if pdf_path else ""
    idx_5216 = text.find("5216")
    idx_date = text.find("1 Jul 26")
    idx_from = text.find("From:")
    idx_body = text.find("This letter addresses")
    checks.append(_check("PDF contains 5216", idx_5216 >= 0))
    checks.append(_check("5216 appears before date and From", idx_5216 >= 0 and idx_date > idx_5216 and idx_from > idx_5216, f"5216={idx_5216}, date={idx_date}, from={idx_from}"))
    checks.append(_check("body text remains present", idx_body >= 0))

    passed = sum(1 for item in checks if item)
    total = len(checks)
    print(f"\nL.31O-2 smoke: {passed}/{total} PASS")
    if passed != total:
        print("\nFirst result:", first)
        print("\nStatus:", status)
        print("\nRendered:", rendered)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
