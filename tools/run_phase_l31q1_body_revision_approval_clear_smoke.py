#!/usr/bin/env python3
"""Phase L.31Q-1 smoke: natural body revision mutates payload and clears approval.

This targets the L.31Q failure where natural body-change text did not mutate the
payload before approval and did not clear approval after approval.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from hermes_chat_builder import send_secnav_chat_turn, start_secnav_chat  # noqa: E402


COMPLETE_REQUEST = (
    "I need a standard letter from MCAS New River to II MEF about reviewing correspondence procedures. "
    "Use 1 July 2026. A. B. SAMPLE will sign it. "
    "The body should say we are implementing local correspondence review procedures."
)
REVISION = "Change the body to say the command is updating local correspondence routing and review procedures."
UPDATED_PHRASE = "updating local correspondence routing and review procedures"


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    return condition


def _body(result: dict) -> str:
    payload = result.get("payload") or {}
    if isinstance(payload, dict):
        body = payload.get("body") or payload.get("body_paragraphs") or ""
        if isinstance(body, list):
            return "\n".join(str(item) for item in body)
        return str(body or "")
    return ""


def _make_complete_chat() -> tuple[str, dict]:
    chat = start_secnav_chat()
    chat_id = chat["chat_id"]
    first = send_secnav_chat_turn(chat_id, COMPLETE_REQUEST)
    return chat_id, first


def main() -> int:
    checks: list[bool] = []

    chat_id, first = _make_complete_chat()
    checks.append(_check("complete first turn reaches draft_preview", first.get("phase") == "draft_preview", str(first.get("phase"))))
    checks.append(_check("complete first turn validation_ready=True", bool(first.get("validation_ready"))))

    revised = send_secnav_chat_turn(chat_id, REVISION)
    revised_body = _body(revised)
    checks.append(_check("revise before approval reports payload_changed", bool(revised.get("payload_changed")), str(revised.get("payload_changed"))))
    checks.append(_check("revise before approval keeps approved_ready false", not bool(revised.get("approved_ready")), str(revised.get("approved_ready"))))
    checks.append(_check("updated body visible before approval", UPDATED_PHRASE in revised_body.lower(), revised_body))

    approved = send_secnav_chat_turn(chat_id, "looks good")
    checks.append(_check("approval after revised body succeeds", bool(approved.get("approved_ready") or approved.get("approved_for_finalize")), str(approved.get("phase"))))

    chat_id2, first2 = _make_complete_chat()
    approved2 = send_secnav_chat_turn(chat_id2, "looks good")
    checks.append(_check("baseline approval succeeds", bool(approved2.get("approved_ready") or approved2.get("approved_for_finalize")), str(approved2.get("phase"))))

    revised2 = send_secnav_chat_turn(chat_id2, REVISION)
    revised2_body = _body(revised2)
    checks.append(_check("revise after approval reports payload_changed", bool(revised2.get("payload_changed")), str(revised2.get("payload_changed"))))
    checks.append(_check("revise after approval reports approval_cleared", bool(revised2.get("approval_cleared")), str(revised2.get("approval_cleared"))))
    checks.append(_check("revise after approval approved_ready=False", not bool(revised2.get("approved_ready")), str(revised2.get("approved_ready"))))
    checks.append(_check("updated body visible after approval", UPDATED_PHRASE in revised2_body.lower(), revised2_body))

    blocked = send_secnav_chat_turn(chat_id2, "make the PDF")
    checks.append(_check("render blocked after approval-clearing revision", not bool(blocked.get("success")) and not blocked.get("pdf_path"), str(blocked.get("phase"))))

    reapproved = send_secnav_chat_turn(chat_id2, "looks good")
    checks.append(_check("re-approval succeeds", bool(reapproved.get("approved_ready") or reapproved.get("approved_for_finalize")), str(reapproved.get("phase"))))

    rendered = send_secnav_chat_turn(chat_id2, "make the PDF")
    checks.append(_check("render succeeds after re-approval", bool(rendered.get("success") and rendered.get("pdf_path")), str(rendered.get("pdf_path"))))

    passed = sum(1 for item in checks if item)
    total = len(checks)
    print(f"\nL.31Q-1 body revision smoke: {passed}/{total} PASS")
    if passed != total:
        print("\nFirst:", first)
        print("\nRevised:", revised)
        print("\nApproved2:", approved2)
        print("\nRevised2:", revised2)
        print("\nBlocked:", blocked)
        print("\nRendered:", rendered)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
