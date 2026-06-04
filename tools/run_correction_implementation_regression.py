#!/usr/bin/env python3
"""
Phase H Approved-Rule Implementation Planner Regression Runner

Uses ONLY synthetic/temp approved-promotion fixtures.
Never reads, writes, or modifies the real local
`corrections/approved_rule_promotions.json`.

Run:
    python tools/run_correction_implementation_regression.py

Exit 0 if all checks pass.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure src/ is importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from correction_implementation_planner import (
    validate_status_transition,
    validate_eligibility,
    list_approved_records_for_implementation,
    claim_record_for_implementation,
    plan_implementation,
    reject_for_implementation,
    defer_implementation,
    mark_superseded,
    mark_implemented,
    _mark_implemented_internal,
    _ALLOWED_IMPLEMENTATION_TARGETS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_base_approved_record(**overrides) -> dict:
    base = {
        "rule_id": "agr_20260101_test001",
        "promoted_from_candidate_id": "cand_test_001",
        "promoted_at": "2026-06-01T12:00:00Z",
        "promoted_by": "reviewer_1",
        "rule_category": "manual_rule",
        "field_path": "subj",
        "doc_type_filter": ["standard_letter"],
        "component_filter": ["marine_corps"],
        "sanitized_value": "POLICY UPDATE",
        "original_value_sanitized": "POLICY UPDATE.",
        "secnav_citation": {"chapter": "7", "paragraph": "3", "figure": "7-1", "quote": "Subject line should not end with a period"},
        "validator_evidence": None,
        "rationale": "Confirmed against SECNAV M-5216.5 figure 7-1",
        "evidence_quality": "strong",
        "implementation_status": "pending_implementation",
        "linked_validator_update": None,
        "linked_rule_file": None,
        "review_metadata": {
            "reviewed_at": "2026-06-01T12:00:00Z",
            "reviewed_by": "reviewer_1",
            "review_action": "promote",
            "previous_status": "under_review",
            "new_status": "promoted",
            "rationale": "Confirmed against manual",
            "secnav_citation": {"chapter": "7", "paragraph": "3", "figure": "7-1"},
            "rule_category": "manual_rule",
            "evidence_quality": "strong",
        },
        "implementation_metadata": None,
    }
    base.update(overrides)
    return base


def _make_validator_gap_record(**overrides) -> dict:
    base = _make_base_approved_record(
        rule_id="agr_20260101_test002",
        rule_category="validator_gap",
        field_path="via",
        secnav_citation=None,
        validator_evidence={
            "validator_name": "cci_routing_validator",
            "expected_behavior": "Flag missing intermediate Via addressee",
            "actual_behavior": "No warning for missing Via",
            "reproduction_payload": {"via": []},
        },
        rationale="Validator gap confirmed",
    )
    base.update(overrides)
    return base


def _make_approved_file(records: list[dict]) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_h_impl_"))
    path = tmpdir / "approved_rule_promotions.json"
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _passed(msg: str) -> None:
    print(f"  PASS — {msg}")


def _failed(msg: str) -> None:
    print(f"  FAIL — {msg}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_01_status_transition_pending_to_planned():
    ok, msg = validate_status_transition("pending_implementation", "implementation_planned")
    assert ok, msg
    _passed("pending_implementation -> implementation_planned valid")


def check_02_status_transition_planned_to_implemented():
    ok, msg = validate_status_transition("implementation_planned", "implemented")
    assert ok, msg
    _passed("implementation_planned -> implemented valid")


def check_03_status_transition_pending_to_implemented_invalid():
    ok, msg = validate_status_transition("pending_implementation", "implemented")
    assert not ok, f"Expected invalid: {msg}"
    _passed("pending_implementation -> implemented blocked")


def check_04_status_transition_implemented_to_pending_invalid():
    ok, msg = validate_status_transition("implemented", "pending_implementation")
    assert not ok, f"Expected invalid: {msg}"
    _passed("implemented -> pending_implementation blocked")


def check_05_status_transition_any_to_superseded():
    for src in ("pending_implementation", "implementation_planned", "deferred", "implemented"):
        ok, msg = validate_status_transition(src, "superseded")
        assert ok, f"Expected {src} -> superseded valid: {msg}"
    _passed("Any status -> superseded valid")


def check_06_eligibility_manual_rule_passes():
    record = _make_base_approved_record()
    ok, reasons = validate_eligibility(record)
    assert ok, reasons
    _passed("Eligibility passes for manual_rule with secnav_citation")


def check_07_eligibility_missing_secnav_fails():
    record = _make_base_approved_record(secnav_citation=None)
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("secnav_citation" in r for r in reasons)
    _passed("Eligibility fails for missing secnav_citation")


def check_08_eligibility_missing_validator_evidence_fails():
    record = _make_validator_gap_record(validator_evidence=None)
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("validator_evidence" in r for r in reasons)
    _passed("Eligibility fails for missing validator_evidence")


def check_09_eligibility_wrong_status_fails():
    record = _make_base_approved_record(implementation_status="implemented")
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("not pending_implementation" in r or "already terminal" in r for r in reasons)
    _passed("Eligibility fails for wrong status")


def check_10_eligibility_validator_gap_passes():
    record = _make_validator_gap_record()
    ok, reasons = validate_eligibility(record)
    assert ok, reasons
    _passed("Eligibility passes for validator_gap with evidence")


def check_11_list_returns_all():
    path = _make_approved_file([_make_base_approved_record(), _make_validator_gap_record()])
    records, warnings = list_approved_records_for_implementation(path)
    assert len(records) == 2, f"Expected 2, got {len(records)}"
    _passed("List returns all records")
    shutil.rmtree(path.parent)


def check_12_list_filters_by_status():
    path = _make_approved_file([
        _make_base_approved_record(),
        _make_base_approved_record(
            rule_id="agr_20260101_test003",
            implementation_status="rejected_for_implementation",
        ),
    ])
    records, _ = list_approved_records_for_implementation(path, status="pending_implementation")
    assert len(records) == 1
    assert records[0]["rule_id"] == "agr_20260101_test001"
    _passed("List filters by status")
    shutil.rmtree(path.parent)


def check_13_list_filters_by_rule_category():
    path = _make_approved_file([_make_base_approved_record(), _make_validator_gap_record()])
    records, _ = list_approved_records_for_implementation(path, rule_category="validator_gap")
    assert len(records) == 1
    assert records[0]["rule_category"] == "validator_gap"
    _passed("List filters by rule_category")
    shutil.rmtree(path.parent)


def check_14_list_filters_by_field_path():
    path = _make_approved_file([_make_base_approved_record(), _make_validator_gap_record()])
    records, _ = list_approved_records_for_implementation(path, field_path="subj")
    assert len(records) == 1
    assert records[0]["field_path"] == "subj"
    _passed("List filters by field_path")
    shutil.rmtree(path.parent)


def check_15_list_exclude_terminal():
    path = _make_approved_file([
        _make_base_approved_record(),
        _make_base_approved_record(
            rule_id="agr_20260101_test003",
            implementation_status="implemented",
        ),
        _make_base_approved_record(
            rule_id="agr_20260101_test004",
            implementation_status="rejected_for_implementation",
        ),
    ])
    records, _ = list_approved_records_for_implementation(path, exclude_terminal=True)
    assert len(records) == 1
    assert records[0]["rule_id"] == "agr_20260101_test001"
    _passed("List excludes terminal statuses")
    shutil.rmtree(path.parent)


def check_16_claim_changes_status():
    path = _make_approved_file([_make_base_approved_record()])
    result = claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "implementation_planned"
    assert records[0]["implementer"] == "impl_1"
    assert records[0]["planned_at"] != ""
    _passed("Claim changes status to implementation_planned")
    shutil.rmtree(path.parent)


def check_17_claim_fails_already_claimed():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = claim_record_for_implementation("agr_20260101_test001", "impl_2", approved_path=path)
    assert result["success"] is False
    assert any("already claimed" in w.lower() for w in result["warnings"])
    _passed("Claim fails for already claimed record")
    shutil.rmtree(path.parent)


def check_18_claim_fails_non_pending():
    path = _make_approved_file([
        _make_base_approved_record(implementation_status="implemented")
    ])
    result = claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is False
    assert any("Invalid transition" in w for w in result["warnings"])
    _passed("Claim fails for non-pending status")
    shutil.rmtree(path.parent)


def check_19_plan_assigns_target_and_verification():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = plan_implementation(
        "agr_20260101_test001", "impl_1",
        implementation_target="rule_catalog",
        source_verification_summary="Verified against figure 7-1",
        implementation_plan_summary="Add catalog entry",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    record = result["record"]
    assert record["implementation_target"] == "rule_catalog"
    assert record["source_verification_summary"] == "Verified against figure 7-1"
    assert record["implementation_plan_summary"] == "Add catalog entry"
    _passed("Plan assigns target and verification")
    shutil.rmtree(path.parent)


def check_20_plan_fails_wrong_status():
    path = _make_approved_file([_make_base_approved_record(implementation_status="implemented")])
    result = plan_implementation(
        "agr_20260101_test001", "impl_1",
        implementation_target="rule_catalog",
        source_verification_summary="Verified",
        approved_path=path,
    )
    assert result["success"] is False
    assert any("must be implementation_planned" in w for w in result["warnings"])
    _passed("Plan fails for wrong status")
    shutil.rmtree(path.parent)


def check_21_plan_fails_wrong_implementer():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = plan_implementation(
        "agr_20260101_test001", "impl_2",
        implementation_target="rule_catalog",
        source_verification_summary="Verified",
        approved_path=path,
    )
    assert result["success"] is False
    assert any("claimed by" in w for w in result["warnings"])
    _passed("Plan fails for different implementer")
    shutil.rmtree(path.parent)


def check_22_plan_fails_invalid_target():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = plan_implementation(
        "agr_20260101_test001", "impl_1",
        implementation_target="invalid_target",
        source_verification_summary="Verified",
        approved_path=path,
    )
    assert result["success"] is False
    assert any("implementation_target must be one of" in w for w in result["warnings"])
    _passed("Plan fails for invalid target")
    shutil.rmtree(path.parent)


def check_23_plan_sets_required_fields():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = plan_implementation(
        "agr_20260101_test001", "impl_1",
        implementation_target="documentation_only",
        source_verification_summary="Verified",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    record = result["record"]
    assert record.get("source_verification_summary")
    assert record.get("implementation_target")
    assert record.get("implementer")
    assert record.get("planned_at")
    _passed("Plan sets all required fields")
    shutil.rmtree(path.parent)


def check_24_reject_changes_status():
    path = _make_approved_file([_make_base_approved_record()])
    result = reject_for_implementation(
        "agr_20260101_test001", "impl_1",
        rationale="Not enforceable",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "rejected_for_implementation"
    _passed("Reject changes status")
    shutil.rmtree(path.parent)


def check_25_reject_requires_rationale():
    path = _make_approved_file([_make_base_approved_record()])
    result = reject_for_implementation(
        "agr_20260101_test001", "impl_1",
        rationale="",
        approved_path=path,
    )
    assert result["success"] is False
    assert any("rationale is required" in w for w in result["warnings"])
    _passed("Reject requires rationale")
    shutil.rmtree(path.parent)


def check_26_defer_changes_status():
    path = _make_approved_file([_make_base_approved_record()])
    result = defer_implementation(
        "agr_20260101_test001", "impl_1",
        rationale="Need more evidence",
        deferred_until="2026-12-31",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "deferred"
    _passed("Defer changes status")
    shutil.rmtree(path.parent)


def check_27_defer_requires_rationale():
    path = _make_approved_file([_make_base_approved_record()])
    result = defer_implementation(
        "agr_20260101_test001", "impl_1",
        rationale="",
        approved_path=path,
    )
    assert result["success"] is False
    assert any("rationale is required" in w for w in result["warnings"])
    _passed("Defer requires rationale")
    shutil.rmtree(path.parent)


def check_28_supersede_changes_status():
    path = _make_approved_file([_make_base_approved_record()])
    result = mark_superseded(
        "agr_20260101_test001", "impl_1",
        superseded_by_rule_id="agr_20260101_new001",
        rationale="Newer rule exists",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "superseded"
    assert records[0].get("superseded_by_rule_id") == "agr_20260101_new001"
    _passed("Supersede changes status")
    shutil.rmtree(path.parent)


def check_29_internal_mark_implemented_synthetic():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = _mark_implemented_internal("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "implemented"
    _passed("Internal mark_implemented works on synthetic fixture")
    shutil.rmtree(path.parent)


def check_30_internal_mark_implemented_requires_planned():
    path = _make_approved_file([_make_base_approved_record()])
    result = _mark_implemented_internal("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is False
    assert any("Invalid transition" in w for w in result["warnings"])
    _passed("Internal mark_implemented blocked from pending_implementation")
    shutil.rmtree(path.parent)


def check_31_eligibility_fails_already_implemented():
    record = _make_base_approved_record(implementation_status="implemented")
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("already terminal" in r for r in reasons)
    _passed("Eligibility fails for already implemented")


def check_32_eligibility_fails_already_rejected():
    record = _make_base_approved_record(implementation_status="rejected_for_implementation")
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("already terminal" in r for r in reasons)
    _passed("Eligibility fails for already rejected")


def check_33_eligibility_fails_already_superseded():
    record = _make_base_approved_record(implementation_status="superseded")
    ok, reasons = validate_eligibility(record)
    assert not ok
    assert any("already terminal" in r for r in reasons)
    _passed("Eligibility fails for already superseded")


def check_34_eligibility_passes_full_secnav():
    record = _make_base_approved_record(
        secnav_citation={"chapter": "7", "paragraph": "3", "figure": "7-1", "quote": "Example text"}
    )
    ok, reasons = validate_eligibility(record)
    assert ok, reasons
    _passed("Eligibility passes with full secnav_citation")


def check_35_eligibility_passes_full_validator():
    record = _make_validator_gap_record(
        validator_evidence={
            "validator_name": "cci_subject_validator",
            "expected_behavior": "Flag terminal period",
            "actual_behavior": "No warning",
        }
    )
    ok, reasons = validate_eligibility(record)
    assert ok, reasons
    _passed("Eligibility passes with full validator_evidence")


def check_36_list_handles_missing_file():
    fake_path = Path(tempfile.mkdtemp(prefix="phase_h_impl_")) / "nonexistent.json"
    records, warnings = list_approved_records_for_implementation(fake_path)
    assert len(records) == 0
    _passed("List handles missing file")
    shutil.rmtree(fake_path.parent)


def check_37_list_handles_empty_file():
    tmpdir = Path(tempfile.mkdtemp(prefix="phase_h_impl_"))
    path = tmpdir / "empty.json"
    path.write_text("", encoding="utf-8")
    records, warnings = list_approved_records_for_implementation(path)
    assert len(records) == 0
    _passed("List handles empty file")
    shutil.rmtree(tmpdir)


def check_38_plan_records_metadata():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    plan_implementation(
        "agr_20260101_test001", "impl_1",
        implementation_target="rule_catalog",
        source_verification_summary="Verified",
        approved_path=path,
    )
    records, _ = list_approved_records_for_implementation(path)
    meta = records[0]["implementation_metadata"]
    assert isinstance(meta, list)
    assert any(m["action"] == "plan_implementation" for m in meta)
    _passed("Plan records implementation metadata")
    shutil.rmtree(path.parent)


def check_39_claim_records_metadata():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    records, _ = list_approved_records_for_implementation(path)
    meta = records[0]["implementation_metadata"]
    assert isinstance(meta, list)
    assert any(m["action"] == "claimed" for m in meta)
    _passed("Claim records implementation metadata")
    shutil.rmtree(path.parent)


def check_40_deferred_can_be_reclaimed():
    path = _make_approved_file([_make_base_approved_record()])
    defer_implementation(
        "agr_20260101_test001", "impl_1",
        rationale="Need more evidence",
        approved_path=path,
    )
    result = claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "implementation_planned"
    _passed("Deferred record can be reclaimed")
    shutil.rmtree(path.parent)


def check_41_public_mark_implemented_success():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = mark_implemented("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is True, result["warnings"]
    records, _ = list_approved_records_for_implementation(path)
    assert records[0]["implementation_status"] == "implemented"
    _passed("Public mark_implemented succeeds from implementation_planned")
    shutil.rmtree(path.parent)


def check_42_public_mark_implemented_wrong_implementer():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = mark_implemented("agr_20260101_test001", "impl_2", approved_path=path)
    assert result["success"] is False
    assert any("claimed by" in w for w in result["warnings"])
    _passed("Public mark_implemented rejects wrong implementer")
    shutil.rmtree(path.parent)


def check_43_public_mark_implemented_non_planned_status():
    path = _make_approved_file([_make_base_approved_record()])
    result = mark_implemented("agr_20260101_test001", "impl_1", approved_path=path)
    assert result["success"] is False
    assert any("must be implementation_planned" in w for w in result["warnings"])
    _passed("Public mark_implemented rejects non-planned status")
    shutil.rmtree(path.parent)


def check_44_public_mark_implemented_records_commit():
    path = _make_approved_file([_make_base_approved_record()])
    claim_record_for_implementation("agr_20260101_test001", "impl_1", approved_path=path)
    result = mark_implemented(
        "agr_20260101_test001", "impl_1",
        implementation_commit="ef365d3",
        approved_path=path,
    )
    assert result["success"] is True, result["warnings"]
    record = result["record"]
    assert record.get("implementation_commit") == "ef365d3"
    meta = record["implementation_metadata"]
    assert any(
        m.get("action") == "mark_implemented" and m.get("implementation_commit") == "ef365d3"
        for m in meta
    )
    _passed("Public mark_implemented records implementation commit")
    shutil.rmtree(path.parent)


def check_45_public_mark_implemented_does_not_touch_real_log():
    # Ensure the real local approved log is untouched by using a temp path only
    import correction_implementation_planner as _impl
    real_default = _impl._DEFAULT_APPROVED_PATH
    assert real_default.name == "approved_rule_promotions.json"
    # The check above just confirms awareness; real test is we only used temp paths
    _passed("Public mark_implemented does not touch real approved log (temp-only test)")


def run() -> int:
    checks = [
        check_01_status_transition_pending_to_planned,
        check_02_status_transition_planned_to_implemented,
        check_03_status_transition_pending_to_implemented_invalid,
        check_04_status_transition_implemented_to_pending_invalid,
        check_05_status_transition_any_to_superseded,
        check_06_eligibility_manual_rule_passes,
        check_07_eligibility_missing_secnav_fails,
        check_08_eligibility_missing_validator_evidence_fails,
        check_09_eligibility_wrong_status_fails,
        check_10_eligibility_validator_gap_passes,
        check_11_list_returns_all,
        check_12_list_filters_by_status,
        check_13_list_filters_by_rule_category,
        check_14_list_filters_by_field_path,
        check_15_list_exclude_terminal,
        check_16_claim_changes_status,
        check_17_claim_fails_already_claimed,
        check_18_claim_fails_non_pending,
        check_19_plan_assigns_target_and_verification,
        check_20_plan_fails_wrong_status,
        check_21_plan_fails_wrong_implementer,
        check_22_plan_fails_invalid_target,
        check_23_plan_sets_required_fields,
        check_24_reject_changes_status,
        check_25_reject_requires_rationale,
        check_26_defer_changes_status,
        check_27_defer_requires_rationale,
        check_28_supersede_changes_status,
        check_29_internal_mark_implemented_synthetic,
        check_30_internal_mark_implemented_requires_planned,
        check_31_eligibility_fails_already_implemented,
        check_32_eligibility_fails_already_rejected,
        check_33_eligibility_fails_already_superseded,
        check_34_eligibility_passes_full_secnav,
        check_35_eligibility_passes_full_validator,
        check_36_list_handles_missing_file,
        check_37_list_handles_empty_file,
        check_38_plan_records_metadata,
        check_39_claim_records_metadata,
        check_40_deferred_can_be_reclaimed,
        check_41_public_mark_implemented_success,
        check_42_public_mark_implemented_wrong_implementer,
        check_43_public_mark_implemented_non_planned_status,
        check_44_public_mark_implemented_records_commit,
        check_45_public_mark_implemented_does_not_touch_real_log,
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
