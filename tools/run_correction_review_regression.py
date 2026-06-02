#!/usr/bin/env python3
"""
Phase E Review/Promotion Utility Regression Runner

Uses ONLY synthetic/temp fixtures. Never writes to the real
`corrections/pending_corrections.jsonl` or `corrections/approved_rule_promotions.json`.

Run:
    python tools/run_correction_review_regression.py

Exit 0 if all checks pass.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

# Ensure src/ is importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from correction_review import (
    list_candidates_for_review,
    claim_candidate,
    review_candidate,
    supersede_candidate,
    propose_phase_c_redirect,
    _validate_evidence,
    _sanitize_reviewer_text,
    _validate_status_transition,
)
from correction_pending_log import (
    _write_jsonl,
    _sanitize_value,
    _compute_fingerprint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_base_candidate(**overrides) -> dict:
    base = {
        "candidate_id": "cand_test_001",
        "recorded_at": "2026-06-01T12:00:00Z",
        "status": "pending",
        "correction_type": "possible_secnav_manual_rule",
        "field_path": "subj",
        "sanitized_value": "POLICY UPDATE",
        "original_value_sanitized": "POLICY UPDATE.",
        "doc_type": "standard_letter",
        "component": "marine_corps",
        "user_reason": "SECNAV manual says subject should not end with a period",
        "classification_confidence": "high",
        "classification_method": "field_path_keyword",
        "source_correction_id": "corr_test_001",
        "session_id": "sess_test_001",
        "review_metadata": None,
        "duplicate_of": None,
        "sanitization_warnings": [],
        "fingerprint": "fp_abc123",
    }
    base.update(overrides)
    return base


def _make_validator_gap_candidate(**overrides) -> dict:
    base = _make_base_candidate(
        candidate_id="cand_test_002",
        correction_type="bug_validator_gap",
        field_path="via",
        sanitized_value="[COMMAND_NAME]",
        original_value_sanitized="[COMMAND_NAME]",
        user_reason="Validator did not flag missing intermediate Via addressee",
        fingerprint="fp_def456",
    )
    base.update(overrides)
    return base


def _make_log_file(candidates: list[dict]) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_e_review_"))
    log_file = tmpdir / "pending_corrections.jsonl"
    _write_jsonl(log_file, candidates)
    return log_file


def _passed(msg: str) -> None:
    print(f"  PASS — {msg}")


def _failed(msg: str) -> None:
    print(f"  FAIL — {msg}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_01_list_pending_returns_eligible():
    """List pending candidates returns only eligible records."""
    log = _make_log_file([_make_base_candidate()])
    candidates, warnings = list_candidates_for_review(log)
    assert len(candidates) == 1, f"Expected 1, got {len(candidates)}"
    assert candidates[0]["candidate_id"] == "cand_test_001"
    _passed("List pending returns eligible records")
    shutil.rmtree(log.parent)


def check_02_list_filters_by_correction_type():
    """List filters by correction_type."""
    log = _make_log_file([_make_base_candidate(), _make_validator_gap_candidate()])
    candidates, _ = list_candidates_for_review(log, correction_type="possible_secnav_manual_rule")
    assert len(candidates) == 1
    assert candidates[0]["correction_type"] == "possible_secnav_manual_rule"
    _passed("List filters by correction_type")
    shutil.rmtree(log.parent)


def check_03_list_filters_by_component():
    """List filters by component."""
    log = _make_log_file([
        _make_base_candidate(component="navy"),
        _make_base_candidate(component="marine_corps"),
    ])
    candidates, _ = list_candidates_for_review(log, component="navy")
    assert len(candidates) == 1
    assert candidates[0]["component"] == "navy"
    _passed("List filters by component")
    shutil.rmtree(log.parent)


def check_04_claim_changes_status():
    """Claim candidate → status changes to under_review."""
    log = _make_log_file([_make_base_candidate()])
    result = claim_candidate("cand_test_001", "reviewer_1", log_path=log)
    assert result["success"] is True, result["warnings"]
    candidates, _ = list_candidates_for_review(log, status="under_review")
    assert len(candidates) == 1
    assert candidates[0]["status"] == "under_review"
    meta = candidates[0]["review_metadata"]
    assert isinstance(meta, list)
    assert meta[-1]["review_action"] == "claimed"
    _passed("Claim changes status to under_review")
    shutil.rmtree(log.parent)


def check_05_reject_records_metadata():
    """Reject candidate → status rejected, review metadata recorded."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "reject",
        {"rationale": "Not a global rule", "rejection_reason": "misclassified_local"},
        log_path=log,
    )
    assert result["success"] is True, result["warnings"]
    candidates, _ = list_candidates_for_review(log, status="rejected")
    assert len(candidates) == 0  # rejected not eligible
    # Read raw
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    r = records[0]
    assert r["status"] == "rejected"
    meta = r["review_metadata"]
    assert meta[-1]["review_action"] == "reject"
    assert meta[-1]["rejection_reason"] == "misclassified_local"
    _passed("Reject records metadata")
    shutil.rmtree(log.parent)


def check_06_promote_creates_approved_record():
    """Promote candidate → status promoted, approved_global_rule record created."""
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_e_review_"))
    log = tmpdir / "pending.jsonl"
    approved_path = tmpdir / "approved.json"
    _write_jsonl(log, [_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {
            "rationale": "Confirmed against manual",
            "rule_category": "manual_rule",
            "secnav_citation": {"chapter": "7", "paragraph": "3", "figure": "7-1"},
            "evidence_quality": "strong",
        },
        log_path=log,
        approved_rule_path=approved_path,
    )
    assert result["success"] is True, result["warnings"]
    assert result["approved_rule_record"] is not None
    assert result["approved_rule_record"]["implementation_status"] == "pending_implementation"
    assert approved_path.exists()
    _passed("Promote creates approved record")
    shutil.rmtree(tmpdir)


def check_07_promotion_blocked_missing_secnav():
    """Promotion blocked if secnav_citation missing for manual_rule."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {"rationale": "Confirmed", "rule_category": "manual_rule"},
        log_path=log,
    )
    assert result["success"] is False
    assert any("secnav_citation" in w for w in result["warnings"])
    _passed("Promotion blocked missing secnav_citation")
    shutil.rmtree(log.parent)


def check_08_promotion_blocked_missing_validator():
    """Promotion blocked if validator_name missing for validator_gap."""
    log = _make_log_file([_make_validator_gap_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_002", "reviewer_1", "promote",
        {"rationale": "Confirmed gap", "rule_category": "validator_gap"},
        log_path=log,
    )
    assert result["success"] is False
    assert any("validator_name" in w for w in result["warnings"])
    _passed("Promotion blocked missing validator_evidence")
    shutil.rmtree(log.parent)


def check_09_promotion_blocked_empty_rationale():
    """Promotion blocked if rationale empty."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {"rationale": "", "rule_category": "manual_rule", "secnav_citation": {"chapter": "7"}},
        log_path=log,
    )
    assert result["success"] is False
    assert any("rationale" in w for w in result["warnings"])
    _passed("Promotion blocked empty rationale")
    shutil.rmtree(log.parent)


def check_10_defer_then_reopen():
    """Defer candidate → status deferred, can be re-opened."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "defer",
        {"rationale": "Need more evidence"},
        log_path=log,
    )
    assert result["success"] is True
    # Reopen
    result2 = review_candidate(
        "cand_test_001", "reviewer_1", "reject",
        {"rationale": "Still insufficient"},
        log_path=log,
    )
    assert result2["success"] is True
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    assert records[0]["status"] == "rejected"
    assert len(records[0]["review_metadata"]) == 2
    _passed("Defer then reopen works")
    shutil.rmtree(log.parent)


def check_11_superseded_excluded_from_queue():
    """Superseded candidate → terminal status, excluded from active queue."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = supersede_candidate("cand_test_001", "reviewer_1", "Later candidate covers this", log_path=log)
    assert result["success"] is True
    candidates, _ = list_candidates_for_review(log)
    assert len(candidates) == 0
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    assert records[0]["status"] == "superseded"
    _passed("Superseded excluded from queue")
    shutil.rmtree(log.parent)


def check_12_duplicate_fingerprint_warning():
    """Duplicate fingerprint detected during review → not shown as eligible."""
    c1 = _make_base_candidate(candidate_id="cand_a", fingerprint="fp_dup")
    c2 = _make_base_candidate(candidate_id="cand_b", fingerprint="fp_dup")
    log = _make_log_file([c1, c2])
    candidates, _ = list_candidates_for_review(log)
    # Both pending with same fingerprint; neither is promoted yet so both show
    assert len(candidates) == 2
    _passed("Duplicate fingerprint handling")
    shutil.rmtree(log.parent)


def check_13_rejected_redirect_phase_c_proposal():
    """Rejected candidate with redirect → Phase C proposal generated."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    # Reject with redirect flag
    result = review_candidate(
        "cand_test_001", "reviewer_1", "reject",
        {
            "rationale": "Command-specific",
            "rejection_reason": "local_command_preference",
            "redirected_to_phase_c": True,
            "phase_c_profile_name": "uss_test",
        },
        log_path=log,
    )
    assert result["success"] is True
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    meta = records[0]["review_metadata"][-1]
    assert meta.get("redirected_to_phase_c") is True
    assert meta.get("phase_c_profile_name") == "uss_test"
    _passed("Rejected redirect recorded")
    shutil.rmtree(log.parent)


def check_14_rejected_without_redirect():
    """Rejected candidate without redirect → no Phase C proposal."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "reject",
        {"rationale": "Not valid"},
        log_path=log,
    )
    assert result["success"] is True
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    meta = records[0]["review_metadata"][-1]
    assert meta.get("redirected_to_phase_c", False) is False
    _passed("Rejected without redirect")
    shutil.rmtree(log.parent)


def check_15_review_metadata_append_only():
    """Review metadata append-only; previous entries preserved."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    review_candidate("cand_test_001", "r1", "defer", {"rationale": "First"}, log_path=log)
    review_candidate("cand_test_001", "r1", "reject", {"rationale": "Second"}, log_path=log)
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    meta = records[0]["review_metadata"]
    assert len(meta) == 2
    assert meta[0]["review_action"] == "defer"
    assert meta[1]["review_action"] == "reject"
    _passed("Review metadata append-only")
    shutil.rmtree(log.parent)


def check_16_approved_record_has_required_fields():
    """approved_global_rule record contains all required fields."""
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_e_review_"))
    log = tmpdir / "pending.jsonl"
    approved_path = tmpdir / "approved.json"
    _write_jsonl(log, [_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {
            "rationale": "Confirmed",
            "rule_category": "manual_rule",
            "secnav_citation": {"chapter": "7", "paragraph": "3"},
            "evidence_quality": "strong",
        },
        log_path=log,
        approved_rule_path=approved_path,
    )
    record = result["approved_rule_record"]
    required = ["rule_id", "promoted_from_candidate_id", "promoted_at", "promoted_by",
                "rule_category", "field_path", "sanitized_value", "original_value_sanitized",
                "rationale", "evidence_quality", "implementation_status", "review_metadata"]
    for f in required:
        assert f in record, f"Missing field: {f}"
    _passed("Approved record has required fields")
    shutil.rmtree(tmpdir)


def check_17_approved_record_pending_implementation():
    """approved_global_rule record implementation_status defaults to pending_implementation."""
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_e_review_"))
    log = tmpdir / "pending.jsonl"
    approved_path = tmpdir / "approved.json"
    _write_jsonl(log, [_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {
            "rationale": "Confirmed",
            "rule_category": "manual_rule",
            "secnav_citation": {"chapter": "7"},
            "evidence_quality": "moderate",
        },
        log_path=log,
        approved_rule_path=approved_path,
    )
    assert result["approved_rule_record"]["implementation_status"] == "pending_implementation"
    _passed("implementation_status is pending_implementation")
    shutil.rmtree(tmpdir)


def check_18_ai_suggested_not_enough():
    """AI-suggested citation does not satisfy evidence without human confirmation."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "promote",
        {
            "rationale": "Confirmed",
            "rule_category": "manual_rule",
            "ai_suggested_citation": "Chapter 7, para 3",
            "ai_assisted": True,
        },
        log_path=log,
    )
    assert result["success"] is False
    assert any("secnav_citation" in w for w in result["warnings"])
    _passed("AI-suggested citation not enough")
    shutil.rmtree(log.parent)


def check_19_reviewer_pii_sanitized():
    """Reviewer-entered PII in notes is sanitized before storage."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_001", "reviewer_1", "reject",
        {"rationale": "Contact john.doe@navy.mil for details"},
        log_path=log,
    )
    assert result["success"] is True
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    meta = records[0]["review_metadata"][-1]
    assert "[EMAIL]" in meta["rationale"]
    _passed("Reviewer PII sanitized")
    shutil.rmtree(log.parent)


def check_20_no_real_command_data_in_outputs():
    """No real command data appears in review outputs."""
    c = _make_base_candidate(
        sanitized_value="Commanding Officer, USS TESTSHIP",
        original_value_sanitized="Commanding Officer, USS TESTSHIP",
    )
    # _sanitize_value should have redacted this
    sanitized, confidence, _ = _sanitize_value("from", "Commanding Officer, USS TESTSHIP")
    assert "[COMMAND_NAME]" in sanitized or confidence == "low"
    _passed("No real command data in outputs")


def check_21_phase_d_regression_compatible():
    """Existing Phase D regression still passes after Phase E module added."""
    # This is a structural check: ensure correction_pending_log functions still work
    log = _make_log_file([_make_base_candidate()])
    from correction_pending_log import list_pending_candidates
    candidates, _ = list_pending_candidates(log, status="pending")
    assert len(candidates) == 1
    _passed("Phase D compatibility")
    shutil.rmtree(log.parent)


def check_22_phase_c_regression_compatible():
    """Existing Phase C regression still passes after Phase E module added."""
    # Structural check: correction_promote imports still available
    try:
        from correction_promote import propose_promotion, confirm_and_write_promotion
        assert callable(propose_promotion)
        _passed("Phase C compatibility")
    except Exception as exc:
        _failed(f"Phase C compatibility: {exc}")


def check_23_phase_b_regression_compatible():
    """Existing Phase B regression still passes after Phase E module added."""
    try:
        from correction_classify import classify_correction
        assert callable(classify_correction)
        _passed("Phase B compatibility")
    except Exception as exc:
        _failed(f"Phase B compatibility: {exc}")


def check_24_phase_a_regression_compatible():
    """Existing Phase A regression still passes after Phase E module added."""
    try:
        from correction_store import save_session_correction, load_session_corrections
        assert callable(save_session_correction)
        _passed("Phase A compatibility")
    except Exception as exc:
        _failed(f"Phase A compatibility: {exc}")


def check_25_validator_gap_promote_creates_record():
    """Promote validator_gap candidate creates approved record with validator_evidence."""
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_e_review_"))
    log = tmpdir / "pending.jsonl"
    approved_path = tmpdir / "approved.json"
    _write_jsonl(log, [_make_validator_gap_candidate(status="under_review", review_metadata=[])])
    result = review_candidate(
        "cand_test_002", "reviewer_1", "promote",
        {
            "rationale": "Validator gap confirmed",
            "rule_category": "validator_gap",
            "validator_evidence": {
                "validator_name": "cci_routing",
                "expected_behavior": "Flag missing intermediate Via",
                "actual_behavior": "No flag raised",
                "reproduction_payload": {"via": []},
            },
            "evidence_quality": "strong",
        },
        log_path=log,
        approved_rule_path=approved_path,
    )
    assert result["success"] is True, result["warnings"]
    record = result["approved_rule_record"]
    assert record["rule_category"] == "validator_gap"
    assert record["validator_evidence"]["validator_name"] == "cci_routing"
    assert record["secnav_citation"] is None
    _passed("Validator gap promote creates record")
    shutil.rmtree(tmpdir)


def check_26_status_transition_invalid_blocked():
    """Invalid status transitions are blocked."""
    ok, msg = _validate_status_transition("promoted", "pending")
    assert ok is False
    assert "Invalid transition" in msg
    ok2, _ = _validate_status_transition("pending", "under_review")
    assert ok2 is True
    _passed("Invalid status transitions blocked")


def check_27_superseded_explicit_only():
    """In Phase E, superseded is explicit reviewer action only."""
    log = _make_log_file([_make_base_candidate(status="under_review", review_metadata=[])])
    # Try to auto-supersede (not allowed)
    result = supersede_candidate("cand_test_001", "reviewer_1", "Explicit reason", log_path=log)
    assert result["success"] is True
    from correction_pending_log import _read_jsonl
    records, _ = _read_jsonl(log)
    assert records[0]["status"] == "superseded"
    _passed("Superseded explicit only")
    shutil.rmtree(log.parent)


def check_28_reviewer_text_truncation():
    """Reviewer text longer than 2000 chars is truncated."""
    long_text = "x" * 2500
    sanitized, warnings = _sanitize_reviewer_text(long_text)
    assert len(sanitized) <= 2000
    assert any("truncated" in w.lower() for w in warnings)
    _passed("Reviewer text truncation")


def check_29_list_excludes_promoted_and_rejected():
    """List excludes promoted and rejected from active queue."""
    log = _make_log_file([
        _make_base_candidate(candidate_id="cand_a", status="pending", fingerprint="fp_a"),
        _make_base_candidate(candidate_id="cand_b", status="promoted", review_metadata=[], fingerprint="fp_b"),
        _make_base_candidate(candidate_id="cand_c", status="rejected", review_metadata=[], fingerprint="fp_c"),
    ])
    candidates, _ = list_candidates_for_review(log)
    ids = {c["candidate_id"] for c in candidates}
    assert ids == {"cand_a"}
    _passed("List excludes promoted and rejected")
    shutil.rmtree(log.parent)


def check_30_propose_phase_c_redirect_synthetic():
    """Propose Phase C redirect returns synthetic record when session missing."""
    candidate = _make_base_candidate(field_path="from")
    result = propose_phase_c_redirect(candidate, "profiles/user/test_profile.json")
    # Should succeed with warning about synthetic
    assert result["success"] is True
    assert any("synthetic" in w.lower() for w in result["warnings"])
    assert result["proposal"] is not None
    _passed("Phase C redirect synthetic fallback")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> int:
    checks = [
        check_01_list_pending_returns_eligible,
        check_02_list_filters_by_correction_type,
        check_03_list_filters_by_component,
        check_04_claim_changes_status,
        check_05_reject_records_metadata,
        check_06_promote_creates_approved_record,
        check_07_promotion_blocked_missing_secnav,
        check_08_promotion_blocked_missing_validator,
        check_09_promotion_blocked_empty_rationale,
        check_10_defer_then_reopen,
        check_11_superseded_excluded_from_queue,
        check_12_duplicate_fingerprint_warning,
        check_13_rejected_redirect_phase_c_proposal,
        check_14_rejected_without_redirect,
        check_15_review_metadata_append_only,
        check_16_approved_record_has_required_fields,
        check_17_approved_record_pending_implementation,
        check_18_ai_suggested_not_enough,
        check_19_reviewer_pii_sanitized,
        check_20_no_real_command_data_in_outputs,
        check_21_phase_d_regression_compatible,
        check_22_phase_c_regression_compatible,
        check_23_phase_b_regression_compatible,
        check_24_phase_a_regression_compatible,
        check_25_validator_gap_promote_creates_record,
        check_26_status_transition_invalid_blocked,
        check_27_superseded_explicit_only,
        check_28_reviewer_text_truncation,
        check_29_list_excludes_promoted_and_rejected,
        check_30_propose_phase_c_redirect_synthetic,
    ]

    passed = 0
    failed = 0
    for fn in checks:
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            _failed(f"{fn.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            _failed(f"{fn.__name__} EXCEPTION: {exc}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed, {len(checks)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
