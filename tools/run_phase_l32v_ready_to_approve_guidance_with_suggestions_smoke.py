#!/usr/bin/env python3
"""
Phase L.32V — Ready-to-Approve Guidance With Pending Suggestions

Proves that when a draft has all required details but still has pending
official lookup suggestions, the assistant clearly explains the draft is
ready for review while mentioning the suggestion as optional. Approval and
render safety behavior is preserved.

Constraints preserved:
- no static command database
- no open-ended web search
- no auto-apply
- provider/fetcher behavior unchanged
- approval/render safety gates unchanged
"""

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", "1")

import hermes_chat_builder as hermes
import official_command_lookup_adapter as adapter

_FAILED = 0
_PASSED = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global _PASSED, _FAILED
    if cond:
        _PASSED += 1
        print(f"PASS: L32V {label}" + (f" — {detail}" if detail else ""))
    else:
        _FAILED += 1
        print(f"FAIL: L32V {label}" + (f" — {detail}" if detail else ""))


class Provider:
    def __call__(self, command_text: str, role: str, state: dict):
        if role == "from" and "New River" in command_text:
            return [{
                "candidate_id": "src-from-" + hashlib.sha1(command_text.encode()).hexdigest()[:8],
                "resolved_value": {
                    "from": "Commanding Officer, Marine Corps Air Station New River",
                    "letterhead_top_line": "UNITED STATES MARINE CORPS",
                    "letterhead_activity": "MARINE CORPS AIR STATION NEW RIVER",
                    "letterhead_address": "JACKSONVILLE NC 28545-0000",
                },
                "source_tier": "official_live",
                "source_title": "MCAS New River",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        if role == "to" and "2d Marine Division" in command_text:
            return [{
                "candidate_id": "src-to-" + hashlib.sha1(command_text.encode()).hexdigest()[:8],
                "resolved_value": {"to": "Commanding Officer, 2d Marine Division"},
                "source_tier": "official_live",
                "source_title": "2d Marine Division",
                "source_url": "https://www.marines.mil/",
                "source_limitation": "Official live lookup result.",
                "confidence": 0.92,
            }]
        return []


def _new_session(provider) -> str:
    adapter.set_official_command_search_provider(provider)
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)
    cid = hermes.start_secnav_chat()["chat_id"]
    return cid


def _complete_draft(cid: str) -> None:
    hermes.send_secnav_chat_turn(cid, "I need a letter from MCAS New River to 2d Marine Division about training")
    hermes.send_secnav_chat_turn(cid, "date 12 September 2026")
    hermes.send_secnav_chat_turn(cid, "signature John Smith will sign it")
    hermes.send_secnav_chat_turn(cid, "body say This letter addresses training readiness.")


def test_complete_no_pending_guidance() -> None:
    """Complete draft without pending suggestions gives ready-for-review guidance."""
    prev = os.environ.get("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP")
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "0"
    import importlib
    importlib.reload(adapter)
    importlib.reload(hermes)
    cid = hermes.start_secnav_chat()["chat_id"]
    _complete_draft(cid)
    status = hermes.get_secnav_chat_status(cid)
    ar = status.get("assistant_response") or ""
    check("no pending phase is draft_preview", status.get("phase") == "draft_preview", status.get("phase"))
    check("no pending ready message", "ready for review" in ar.lower() or "looks good" in ar.lower(), ar)
    check("no pending reminder approval", "approve" in ar.lower(), ar)
    check("no pending no source note", "source-backed" not in ar.lower(), ar)
    if prev is None:
        os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    else:
        os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = prev
    adapter.set_official_command_search_provider(Provider())
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)


def test_complete_with_pending_guidance() -> None:
    """Complete draft with pending suggestion notes suggestion is optional."""
    cid = _new_session(Provider())
    _complete_draft(cid)
    status = hermes.get_secnav_chat_status(cid)
    ar = status.get("assistant_response") or ""
    pending = (status.get("source_backed_candidates") or {}).get("pending", [])
    check("with pending candidates exist", len(pending) > 0, f"pending={len(pending)}")
    check("with pending phase is draft_preview", status.get("phase") == "draft_preview", status.get("phase"))
    check("with pending ready for review", "otherwise ready for review" in ar.lower() or "ready for review" in ar.lower(), ar)
    check("with pending mentions suggestion", "source-backed" in ar.lower(), ar)
    check("with pending approval option", "looks good" in ar.lower(), ar)
    check("with pending confirm option", "confirm candidate" in ar.lower(), ar)
    check("with pending dismiss option", "dismiss candidate" in ar.lower(), ar)


def test_approve_with_pending_preserved() -> None:
    """Approval proceeds and preserves pending suggestion."""
    cid = _new_session(Provider())
    _complete_draft(cid)
    r = hermes.send_secnav_chat_turn(cid, "looks good")
    pending = (r.get("source_backed_candidates") or {}).get("pending", [])
    check("approve with pending success", r.get("success") is True)
    check("approve with pending phase approved_ready", r.get("phase") == "approved_ready", r.get("phase"))
    check("approve with pending approved_ready true", r.get("approved_ready") is True)
    check("approve with pending preserved", len(pending) > 0, f"pending={len(pending)}")
    ar = r.get("assistant_response") or ""
    check("approve with pending mentions make PDF", "pdf" in ar.lower() and ("make" in ar.lower() or "generate" in ar.lower()), ar)


def test_render_safety_after_approve() -> None:
    """Render works after approval, blocked without approval."""
    cid = _new_session(Provider())
    _complete_draft(cid)
    # Render before approve should be blocked.
    r1 = hermes.send_secnav_chat_turn(cid, "make the PDF")
    check("render before approve blocked", r1.get("phase") != "rendered" and r1.get("pdf_path") is None, f"phase={r1.get('phase')}")
    check("render before approve mentions approval", "approve" in (r1.get("assistant_response") or "").lower(), r1.get("assistant_response"))
    # Approve then render.
    hermes.send_secnav_chat_turn(cid, "looks good")
    r2 = hermes.send_secnav_chat_turn(cid, "make the PDF")
    check("render after approve success", r2.get("phase") == "rendered", r2.get("phase"))
    check("render after approve pdf produced", bool(r2.get("pdf_path")), r2.get("pdf_path"))


def test_render_blocked_after_revise() -> None:
    """Revision clears approval; render is blocked until re-approval."""
    cid = _new_session(Provider())
    _complete_draft(cid)
    hermes.send_secnav_chat_turn(cid, "looks good")
    r = hermes.send_secnav_chat_turn(cid, "change the body to say This letter directs a review of correspondence procedures and immediate updates.")
    check("revise clears approval", r.get("approval_cleared") is True, r.get("approval_cleared"))
    check("revise phase draft_preview", r.get("phase") == "draft_preview", r.get("phase"))
    r2 = hermes.send_secnav_chat_turn(cid, "make the PDF")
    check("render blocked after revise", r2.get("phase") != "rendered" and r2.get("pdf_path") is None, f"phase={r2.get('phase')}")


def test_disabled_lookup_complete() -> None:
    """With lookup disabled, complete draft still gives approval guidance."""
    prev = os.environ.get("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP")
    os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = "0"
    import importlib
    importlib.reload(adapter)
    importlib.reload(hermes)
    cid = hermes.start_secnav_chat()["chat_id"]
    _complete_draft(cid)
    status = hermes.get_secnav_chat_status(cid)
    ar = status.get("assistant_response") or ""
    check("disabled phase is draft_preview", status.get("phase") == "draft_preview")
    check("disabled ready for review", "ready for review" in ar.lower() or "looks good" in ar.lower(), ar)
    check("disabled no pending", len((status.get("source_backed_candidates") or {}).get("pending", [])) == 0)
    if prev is None:
        os.environ.pop("SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP", None)
    else:
        os.environ["SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"] = prev
    adapter.set_official_command_search_provider(Provider())
    hermes.set_source_backed_command_lookup_adapter(adapter.official_command_lookup)


def test_l30y_approval_current() -> None:
    """Regression: L.30Y approval/revise still works."""
    cid = _new_session(Provider())
    _complete_draft(cid)
    hermes.send_secnav_chat_turn(cid, "looks good")
    status = hermes.get_secnav_chat_status(cid)
    check("L30Y approval current", bool(status.get("approved_ready")), status.get("approved_ready"))


if __name__ == "__main__":
    state_dir = Path(hermes._STATE_DIR)
    if state_dir.exists():
        for f in state_dir.glob("chat-*.json"):
            f.unlink()

    test_complete_no_pending_guidance()
    test_complete_with_pending_guidance()
    test_approve_with_pending_preserved()
    test_render_safety_after_approve()
    test_render_blocked_after_revise()
    test_disabled_lookup_complete()
    test_l30y_approval_current()

    print(f"\nL.32V ready-to-approve guidance with suggestions smoke: {_PASSED}/{_PASSED + _FAILED} PASS")
    sys.exit(0 if _FAILED == 0 else 1)
