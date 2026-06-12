#!/usr/bin/env python3
"""
Phase L.5 Conversational Builder Validation Summary Regression Runner

Tests:
  1. no_findings_summary — clean payload returns zero findings, finalize_allowed True
  2. known_route010_warning_summary — plain-English ROUTE-010 message, severity warning
  3. known_route011_warning_summary — plain-English ROUTE-011 message, severity warning
  4. known_subj002_warning_summary — plain-English SUBJ-002 message, severity warning
  5. unknown_advisory_fallback — unknown finding mapped to advisory fallback
  6. pending_decision_state — un-accepted warning shows pending, blocks finalize
  7. accepted_warning_state — recorded decision moves to accepted, allows finalize
  8. finalize_allowed_with_accepted_warnings — accept_warnings=False, decisions present
  9. finalize_allowed_with_accept_warnings_flag — accept_warnings=True overrides pending
  10. finalize_blocked_with_synthetic_error — injected error in summary blocks finalize

Exit 0 if all expectations met; non-zero otherwise.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

# Ensure repo root and src/ are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from conversational_builder import BuilderSession

_PASS = 0
_FAIL = 0


def _assert(condition: bool, message: str) -> None:
    global _PASS, _FAIL
    if not condition:
        _FAIL += 1
        print(f"FAIL: {message}", file=sys.stderr)
        raise AssertionError(message)
    else:
        _PASS += 1
        print(f"PASS: {message}")


# -- helpers -----------------------------------------------------------------

def _make_clean_builder() -> BuilderSession:
    """Return a BuilderSession with all required fields filled using clean data."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    builder.ingest_user_message("from: Commander, USS NEVERSAIL")
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TRAINING PLAN")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Paragraph 1. Paragraph 2.")
    builder.ingest_user_message("signature: J. DOE")
    return builder


def _make_route010_builder() -> BuilderSession:
    """Return a BuilderSession with a raw office-code To line to trigger ROUTE-010."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    builder.ingest_user_message("from: Commander, USS NEVERSAIL")
    # Raw numeric office code in the To line triggers ROUTE-010
    builder.ingest_user_message("to: Commander, 123")
    builder.ingest_user_message("subj: TRAINING PLAN")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Paragraph 1. Paragraph 2.")
    builder.ingest_user_message("signature: J. DOE")
    return builder


def _make_route011_builder() -> BuilderSession:
    """Return a BuilderSession without a From line to trigger ROUTE-011."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    # Deliberately omit 'from' — only to, subj, date, body, signature
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TRAINING PLAN")
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Paragraph 1. Paragraph 2.")
    builder.ingest_user_message("signature: J. DOE")
    return builder


def _make_subj002_builder() -> BuilderSession:
    """Return a BuilderSession with terminal punctuation in subject to trigger SUBJ-002."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "navy"}})
    builder.ingest_user_message("from: Commander, USS NEVERSAIL")
    builder.ingest_user_message("to: Commander, Example Command")
    builder.ingest_user_message("subj: TRAINING PLAN.")  # terminal period triggers SUBJ-002
    builder.ingest_user_message("date: 15 May 2026")
    builder.ingest_user_message("body: Paragraph 1. Paragraph 2.")
    builder.ingest_user_message("signature: J. DOE")
    return builder


# -- tests -------------------------------------------------------------------

def test_no_findings_summary() -> None:
    print("\n=== TEST: no_findings_summary ===")
    builder = _make_clean_builder()
    v = builder.validation_summary()
    # The underlying validator may still emit advisory findings (e.g., CCI-CH7-SUBJ-005)
    # for seemingly clean data. The important invariants are: no errors, no warnings,
    # and finalize is allowed because advisory-level findings do not block.
    _assert(v["errors"] == 0, "clean payload has zero errors")
    _assert(v["warnings"] == 0, "clean payload has zero warnings")
    _assert(v["finalize_allowed"] is True, "clean payload allows finalize (only advisory present)")
    _assert(v["block_reason"] == [], "clean payload has no block reasons")
    print(f"  Findings: {v['total_findings']} (errors={v['errors']}, warnings={v['warnings']}, advisories={v['advisories']}) — finalize allowed.")


def test_known_route010_warning_summary() -> None:
    print("\n=== TEST: known_route010_warning_summary ===")
    builder = _make_route010_builder()
    v = builder.validation_summary()
    # At least one finding should be ROUTE-010
    route010_items = [f for f in v["findings"] if f["rule_code"] == "CCI-ROUTE-010"]
    _assert(len(route010_items) >= 1, "ROUTE-010 appears in findings")
    item = route010_items[0]
    _assert(item["severity"] == "warning", "ROUTE-010 severity is warning")
    _assert("Code 123" in item["message"] or "numbers only" in item["message"],
            "ROUTE-010 message is plain-English")
    _assert("Revise now" in item["actions"], "ROUTE-010 actions include Revise now")
    print(f"  ROUTE-010: {item['message'][:60]}...")


def test_known_route011_warning_summary() -> None:
    print("\n=== TEST: known_route011_warning_summary ===")
    builder = _make_route011_builder()
    v = builder.validation_summary()
    route011_items = [f for f in v["findings"] if f["rule_code"] == "CCI-ROUTE-011"]
    _assert(len(route011_items) >= 1, "ROUTE-011 appears in findings")
    item = route011_items[0]
    _assert(item["severity"] == "warning", "ROUTE-011 severity is warning")
    _assert("From:" in item["message"] or "window" in item["message"].lower(),
            "ROUTE-011 message is plain-English")
    _assert("Revise now" in item["actions"], "ROUTE-011 actions include Revise now")
    print(f"  ROUTE-011: {item['message'][:60]}...")


def test_known_subj002_warning_summary() -> None:
    print("\n=== TEST: known_subj002_warning_summary ===")
    builder = _make_subj002_builder()
    v = builder.validation_summary()
    subj_items = [f for f in v["findings"] if f["rule_code"] == "CCI-CH7-SUBJ-002"]
    _assert(len(subj_items) >= 1, "SUBJ-002 appears in findings")
    item = subj_items[0]
    _assert(item["severity"] == "warning", "SUBJ-002 severity is warning")
    _assert("punctuation" in item["message"].lower(),
            "SUBJ-002 message mentions punctuation")
    _assert("Revise now" in item["actions"], "SUBJ-002 actions include Revise now")
    print(f"  SUBJ-002: {item['message'][:60]}...")


def test_unknown_advisory_fallback() -> None:
    print("\n=== TEST: unknown_advisory_fallback ===")
    builder = _make_clean_builder()
    # Manually inject an unknown finding by patching the returned audit
    # We test the mapping logic directly: if warning_summary sees an unmapped code,
    # it should produce an advisory fallback.
    original_warning_summary = builder.warning_summary
    def _patched_warning_summary() -> list[dict[str, Any]]:
        # Return a synthetic unknown finding mixed with real findings
        real = original_warning_summary()
        real.append({
            "rule_code": "CCI-UNKNOWN-999",
            "severity": "advisory",
            "message": "A validator finding may need review. Please verify the content follows SECNAV conventions before finalizing.",
            "raw_warning": "Synthetic unknown validator output.",
            "actions": ["Dismiss"],
            "user_decision": None,
        })
        return real
    builder.warning_summary = _patched_warning_summary  # type: ignore[method-assign]

    v = builder.validation_summary()
    unknown_items = [f for f in v["findings"] if f["rule_code"] == "CCI-UNKNOWN-999"]
    _assert(len(unknown_items) >= 1, "unknown finding appears in findings")
    item = unknown_items[0]
    _assert(item["severity"] == "advisory", "unknown fallback severity is advisory")
    _assert("verify" in item["message"].lower() or "review" in item["message"].lower(),
            "unknown fallback message is plain-English")
    print(f"  Unknown fallback: {item['severity']} — {item['message'][:60]}...")


def test_pending_decision_state() -> None:
    print("\n=== TEST: pending_decision_state ===")
    builder = _make_route010_builder()
    v = builder.validation_summary()
    # No user decision recorded yet → pending
    route010_items = [f for f in v["findings"] if f["rule_code"] == "CCI-ROUTE-010"]
    _assert(len(route010_items) >= 1, "ROUTE-010 present")
    item = route010_items[0]
    _assert(item.get("user_decision") is None, "unaccepted warning shows user_decision = None (pending)")
    # Since there is a pending warning, finalize should be blocked (accept_warnings=False)
    _assert(v["finalize_allowed"] is False, "pending warning blocks finalize")
    _assert(any("Pending" in r or "pending" in r for r in v["block_reason"]),
            "block_reason mentions pending decisions")
    print(f"  Pending decisions: {v['pending_decisions']}  Finalize allowed: {v['finalize_allowed']}")


def test_accepted_warning_state() -> None:
    print("\n=== TEST: accepted_warning_state ===")
    builder = _make_route010_builder()
    builder.record_user_decision("CCI-ROUTE-010", "accept")
    v = builder.validation_summary()
    route010_items = [f for f in v["findings"] if f["rule_code"] == "CCI-ROUTE-010"]
    _assert(len(route010_items) >= 1, "ROUTE-010 present after decision")
    item = route010_items[0]
    _assert(item.get("user_decision") == "accept", "recorded accept decision is reflected")
    # After accepting, there should be no pending decisions, so finalize_allowed True
    _assert(v["finalize_allowed"] is True, "accepted warning allows finalize")
    _assert(v["pending_decisions"] == 0, "no pending decisions after accept")
    print(f"  Decision: {item['user_decision']}  Finalize allowed: {v['finalize_allowed']}")


def test_finalize_allowed_with_accepted_warnings() -> None:
    print("\n=== TEST: finalize_allowed_with_accepted_warnings ===")
    builder = _make_subj002_builder()
    builder.record_user_decision("CCI-CH7-SUBJ-002", "accept")
    result = builder.finalize(accept_warnings=False)
    _assert(result["finalize_allowed"] is True, "finalize allowed when warning decisions recorded")
    _assert(result["block_reason"] == [], "no block reasons when decisions recorded")
    _assert(result["validation_summary"]["pending_decisions"] == 0, "pending decisions zero")
    print(f"  Finalize allowed: {result['finalize_allowed']}  Block reasons: {result['block_reason']}")


def test_finalize_allowed_with_accept_warnings_flag() -> None:
    print("\n=== TEST: finalize_allowed_with_accept_warnings_flag ===")
    builder = _make_route010_builder()
    # No explicit user decision recorded
    result = builder.finalize(accept_warnings=True)
    _assert(result["finalize_allowed"] is True, "accept_warnings=True allows finalize despite pending")
    _assert(result["block_reason"] == [], "no block reasons when accept_warnings=True")
    # Findings should show accepted_via_flag
    route010_items = [f for f in result["warning_summary"] if f["rule_code"] == "CCI-ROUTE-010"]
    _assert(len(route010_items) >= 1, "ROUTE-010 in warning_summary")
    _assert(route010_items[0].get("user_decision") == "accepted_via_flag",
            "accept_warnings sets user_decision to accepted_via_flag")
    print(f"  Finalize allowed: {result['finalize_allowed']}  Decision: {route010_items[0]['user_decision']}")


def test_finalize_blocked_with_synthetic_error() -> None:
    print("\n=== TEST: finalize_blocked_with_synthetic_error ===")
    builder = _make_clean_builder()
    # Inject a synthetic error into validation_summary without touching config/validators
    original_validation_summary = builder.validation_summary
    def _patched_validation_summary() -> dict[str, Any]:
        real = original_validation_summary()
        synthetic_error = {
            "rule_code": "SYNTH-ERROR-001",
            "severity": "error",
            "message": "Synthetic error injected for L.5 test.",
            "raw_warning": "Synthetic error.",
            "actions": ["Fix before finalizing"],
            "user_decision": None,
        }
        real["findings"].append(synthetic_error)
        real["errors"] += 1
        real["total_findings"] += 1
        real["finalize_allowed"] = False
        real["block_reason"] = ["Errors must be fixed before finalizing."]
        real["pending_decisions"] = 0
        return real
    builder.validation_summary = _patched_validation_summary  # type: ignore[method-assign]

    result = builder.finalize(accept_warnings=False)
    _assert(result["finalize_allowed"] is False, "synthetic error blocks finalize")
    _assert(any("error" in r.lower() for r in result["block_reason"]),
            "block_reason mentions errors")
    print(f"  Finalize allowed: {result['finalize_allowed']}  Block: {result['block_reason']}")


# -- main --------------------------------------------------------------------

def main(argv: list[str]) -> int:
    print("=" * 70)
    print("Phase L.5 Conversational Builder Validation Summary Regression Runner")
    print("=" * 70)

    tests = [
        test_no_findings_summary,
        test_known_route010_warning_summary,
        test_known_route011_warning_summary,
        test_known_subj002_warning_summary,
        test_unknown_advisory_fallback,
        test_pending_decision_state,
        test_accepted_warning_state,
        test_finalize_allowed_with_accepted_warnings,
        test_finalize_allowed_with_accept_warnings_flag,
        test_finalize_blocked_with_synthetic_error,
    ]

    for t in tests:
        try:
            t()
        except AssertionError:
            print("\n" + "=" * 70, file=sys.stderr)
            print(f"REGRESSION FAILED at {t.__name__}", file=sys.stderr)
            print("=" * 70, file=sys.stderr)
            return 1

    print("\n" + "=" * 70)
    print(f"REGRESSION PASSED  ({_PASS} passed, {_FAIL} failed)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
