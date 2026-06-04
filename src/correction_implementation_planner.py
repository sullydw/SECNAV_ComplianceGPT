#!/usr/bin/env python3
"""
Approved-Rule Implementation Planner — Phase H Stage 1

Public API:
    list_approved_records_for_implementation(
        approved_path: Path | None = None,
        status: str | None = None,
        rule_category: str | None = None,
        field_path: str | None = None,
    ) -> tuple[list[dict], list[str]]
        Return approved records eligible for implementation planning.

    claim_record_for_implementation(
        rule_id: str,
        implementer_id: str,
        approved_path: Path | None = None,
    ) -> dict
        Claim an approved record for implementation planning.
        Sets status to implementation_planned and records implementer metadata.

    plan_implementation(
        rule_id: str,
        implementer_id: str,
        implementation_target: str,
        source_verification_summary: str,
        implementation_plan_summary: str = "",
        approved_path: Path | None = None,
    ) -> dict
        Core planner action: assign target, record verification, set status.

    reject_for_implementation(
        rule_id: str,
        implementer_id: str,
        rationale: str,
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as rejected_for_implementation.

    defer_implementation(
        rule_id: str,
        implementer_id: str,
        rationale: str,
        deferred_until: str | None = None,
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as deferred.

    mark_superseded(
        rule_id: str,
        implementer_id: str,
        superseded_by_rule_id: str | None = None,
        rationale: str = "",
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as superseded.

    validate_eligibility(record: dict) -> tuple[bool, list[str]]
        Check whether a single approved record is eligible for planning.

    mark_implemented(
        rule_id: str,
        implementer_id: str,
        implementation_commit: str = "",
        approved_path: Path | None = None,
    ) -> dict
        Public wrapper: mark an implementation_planned record as implemented.
        Validates existence, status, and implementer match.
        Records implementation_commit hash in metadata when provided.

    reject_for_implementation(
        rule_id: str,
        implementer_id: str,
        rationale: str,
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as rejected_for_implementation.

    defer_implementation(
        rule_id: str,
        implementer_id: str,
        rationale: str,
        deferred_until: str | None = None,
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as deferred.

    mark_superseded(
        rule_id: str,
        implementer_id: str,
        superseded_by_rule_id: str | None = None,
        rationale: str = "",
        approved_path: Path | None = None,
    ) -> dict
        Mark an approved record as superseded.

    validate_eligibility(record: dict) -> tuple[bool, list[str]]
        Check whether a single approved record is eligible for planning.

    validate_status_transition(current: str, new: str) -> tuple[bool, str]
        Validate a status transition. Includes implementation_planned -> implemented
        and the public mark_implemented() wrapper.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure sibling imports work
_SRC_DIR = Path(__file__).resolve().parent
import sys
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_APPROVED_PATH = _REPO_ROOT / "corrections" / "approved_rule_promotions.json"

_ALLOWED_IMPLEMENTATION_STATUSES = {
    "pending_implementation",
    "implementation_planned",
    "implemented",
    "rejected_for_implementation",
    "deferred",
    "superseded",
}

_ALLOWED_IMPLEMENTATION_TARGETS = {
    "validator_update",
    "rule_catalog",
    "prompt_contract",
    "documentation_only",
    "none_needed",
}

_MAX_TEXT_LEN = 2000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_approved_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read approved rule records from local JSON store."""
    warnings: list[str] = []
    if not path.exists():
        return [], []
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return [], []
        data = json.loads(text)
        if isinstance(data, list):
            return data, warnings
        if isinstance(data, dict):
            return [data], warnings
        warnings.append(f"Unexpected JSON type in {path.name}: {type(data).__name__}")
        return [], warnings
    except json.JSONDecodeError as exc:
        warnings.append(f"JSON parse error in {path.name}: {exc}")
        return [], warnings
    except Exception as exc:
        warnings.append(f"Failed reading {path.name}: {exc}")
        return [], warnings


def _write_approved_records(path: Path, records: list[dict[str, Any]]) -> list[str]:
    """Write approved rule records to local JSON store (atomic replace)."""
    warnings: list[str] = []
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception as exc:
        warnings.append(f"Failed writing {path.name}: {exc}")
    return warnings


def _find_record(records: list[dict[str, Any]], rule_id: str) -> dict[str, Any] | None:
    for r in records:
        if r.get("rule_id") == rule_id:
            return r
    return None


def _append_implementation_metadata(
    record: dict[str, Any],
    action: str,
    implementer_id: str,
    previous_status: str,
    new_status: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append an implementation metadata entry to the record."""
    entry: dict[str, Any] = {
        "action": action,
        "implementer_id": str(implementer_id)[:200],
        "timestamp": _now_utc_iso(),
        "previous_status": previous_status,
        "new_status": new_status,
    }
    if extra:
        entry.update(extra)
    if "implementation_metadata" not in record or record["implementation_metadata"] is None:
        record["implementation_metadata"] = []
    if not isinstance(record["implementation_metadata"], list):
        record["implementation_metadata"] = [record["implementation_metadata"]]
    record["implementation_metadata"].append(entry)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_status_transition(current: str, new: str) -> tuple[bool, str]:
    """
    Validate a status transition.

    Valid transitions:
        pending_implementation -> implementation_planned
        pending_implementation -> rejected_for_implementation
        pending_implementation -> deferred
        implementation_planned -> implemented       (defined for completeness;
                                                        Stage 1 does not expose mark_implemented)
        implementation_planned -> rejected_for_implementation
        implementation_planned -> deferred
        implementation_planned -> superseded
        deferred -> implementation_planned
        deferred -> rejected_for_implementation
        deferred -> superseded
        any -> superseded
    """
    allowed = {
        "pending_implementation": {
            "implementation_planned",
            "rejected_for_implementation",
            "deferred",
            "superseded",
        },
        "implementation_planned": {
            "implemented",
            "rejected_for_implementation",
            "deferred",
            "superseded",
        },
        "deferred": {
            "implementation_planned",
            "rejected_for_implementation",
            "superseded",
        },
        "rejected_for_implementation": {"superseded"},
        "implemented": {"superseded"},
        "superseded": set(),
    }
    if new not in allowed.get(current, set()):
        return False, f"Invalid transition: {current} -> {new}"
    return True, ""


def validate_eligibility(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check whether an approved record is eligible for implementation planning.

    Eligibility requirements:
        - implementation_status is pending_implementation
        - review_decision is approved (if present)
        - rule_category is possible_secnav_manual_rule or bug_validator_gap
        - secnav_citation present for manual_rule
        - validator_evidence present for validator_gap
        - not already implemented, rejected, or superseded
    """
    reasons: list[str] = []
    status = record.get("implementation_status", "")
    if status != "pending_implementation":
        reasons.append(f"implementation_status={status} is not pending_implementation")

    review_decision = record.get("review_metadata", {}).get("review_action", "")
    if review_decision and review_decision != "promote":
        reasons.append(f"review_action={review_decision} is not promote (approved)")

    rule_category = record.get("rule_category", "")
    if rule_category not in ("manual_rule", "validator_gap"):
        ctype = record.get("correction_type", "")
        if ctype not in ("possible_secnav_manual_rule", "bug_validator_gap"):
            reasons.append(f"rule_category={rule_category} not eligible for global implementation")

    if rule_category == "manual_rule" or record.get("correction_type") == "possible_secnav_manual_rule":
        secnav = record.get("secnav_citation")
        if not secnav or not isinstance(secnav, dict):
            reasons.append("secnav_citation required for manual_rule")
        elif not any(secnav.get(k) for k in ("chapter", "paragraph", "figure", "quote")):
            reasons.append("secnav_citation missing required fields (chapter/paragraph/figure/quote)")

    if rule_category == "validator_gap" or record.get("correction_type") == "bug_validator_gap":
        evidence = record.get("validator_evidence")
        if not evidence or not isinstance(evidence, dict):
            reasons.append("validator_evidence required for validator_gap")
        elif not evidence.get("validator_name"):
            reasons.append("validator_evidence.validator_name required")

    if status in ("implemented", "rejected_for_implementation", "superseded"):
        reasons.append(f"status={status} already terminal; cannot plan implementation")

    return len(reasons) == 0, reasons


def list_approved_records_for_implementation(
    approved_path: Path | None = None,
    status: str | None = None,
    rule_category: str | None = None,
    field_path: str | None = None,
    exclude_terminal: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Return approved records eligible for implementation planning.

    Parameters:
        status: filter by implementation_status.
        rule_category: filter by rule_category.
        field_path: filter by field_path.
        exclude_terminal: if True, exclude implemented, rejected_for_implementation, superseded.
    """
    warnings: list[str] = []
    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    eligible: list[dict[str, Any]] = []
    for r in records:
        if exclude_terminal:
            if r.get("implementation_status") in ("implemented", "rejected_for_implementation", "superseded"):
                continue
        if status is not None and r.get("implementation_status") != status:
            continue
        if rule_category is not None and r.get("rule_category") != rule_category:
            continue
        if field_path is not None and r.get("field_path") != field_path:
            continue
        eligible.append(copy.deepcopy(r))

    return eligible, warnings


def claim_record_for_implementation(
    rule_id: str,
    implementer_id: str,
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Claim an approved record for implementation planning.
    Sets status to implementation_planned and records claim metadata.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    # Check that another implementer has not already claimed
    existing_meta = record.get("implementation_metadata", [])
    if isinstance(existing_meta, list) and any(
        m.get("action") == "claimed" and m.get("new_status") == "implementation_planned"
        for m in existing_meta
    ):
        warnings.append("Record already claimed for implementation planning")
        return result

    current_status = record.get("implementation_status", "")
    valid, msg = validate_status_transition(current_status, "implementation_planned")
    if not valid:
        warnings.append(msg)
        return result

    # Validate eligibility before claiming
    # For deferred records, skip the "not pending_implementation" check since
    # deferred -> implementation_planned is an explicit valid transition
    eligible, eligibility_reasons = validate_eligibility(record)
    if not eligible:
        if current_status == "deferred":
            # Filter out the non-pending status complaint; keep evidence/terminal checks
            filtered = [r for r in eligibility_reasons
                        if "not pending_implementation" not in r]
            if filtered:
                warnings.extend(filtered)
                return result
        else:
            warnings.extend(eligibility_reasons)
            return result

    record["implementation_status"] = "implementation_planned"
    record["implementer"] = str(implementer_id)[:200]
    record["planned_at"] = _now_utc_iso()

    _append_implementation_metadata(
        record,
        action="claimed",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="implementation_planned",
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def plan_implementation(
    rule_id: str,
    implementer_id: str,
    implementation_target: str,
    source_verification_summary: str,
    implementation_plan_summary: str = "",
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Core planner action: assign target, record source verification, update metadata.

    The record must already be claimed (status=implementation_planned) by the same
    implementer, or this call will fail.

    Required fields on the record after success:
        - source_verification_summary
        - implementation_target
        - implementer
        - planned_at
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    if implementation_target not in _ALLOWED_IMPLEMENTATION_TARGETS:
        warnings.append(
            f"implementation_target must be one of {_ALLOWED_IMPLEMENTATION_TARGETS}; "
            f"got {implementation_target}"
        )
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    if current_status != "implementation_planned":
        warnings.append(f"Record status is {current_status}; must be implementation_planned")
        return result

    # Verify same implementer
    record_implementer = record.get("implementer", "")
    if record_implementer and record_implementer != implementer_id:
        warnings.append(
            f"Record claimed by {record_implementer}; cannot plan by {implementer_id}"
        )
        return result

    # Update record
    record["implementation_target"] = implementation_target
    record["source_verification_summary"] = str(source_verification_summary)[:_MAX_TEXT_LEN]
    if implementation_plan_summary:
        record["implementation_plan_summary"] = str(implementation_plan_summary)[:_MAX_TEXT_LEN]

    # Ensure required fields
    if "planned_at" not in record or not record["planned_at"]:
        record["planned_at"] = _now_utc_iso()
    if "implementer" not in record or not record["implementer"]:
        record["implementer"] = str(implementer_id)[:200]

    _append_implementation_metadata(
        record,
        action="plan_implementation",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="implementation_planned",
        extra={
            "implementation_target": implementation_target,
            "source_verification_summary": record["source_verification_summary"],
        },
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def reject_for_implementation(
    rule_id: str,
    implementer_id: str,
    rationale: str,
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Mark an approved record as rejected_for_implementation.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    if not rationale or not str(rationale).strip():
        warnings.append("rationale is required for rejection")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    valid, msg = validate_status_transition(current_status, "rejected_for_implementation")
    if not valid:
        warnings.append(msg)
        return result

    record["implementation_status"] = "rejected_for_implementation"

    _append_implementation_metadata(
        record,
        action="reject",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="rejected_for_implementation",
        extra={"rationale": str(rationale)[:_MAX_TEXT_LEN]},
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def defer_implementation(
    rule_id: str,
    implementer_id: str,
    rationale: str,
    deferred_until: str | None = None,
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Mark an approved record as deferred.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    if not rationale or not str(rationale).strip():
        warnings.append("rationale is required for deferral")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    valid, msg = validate_status_transition(current_status, "deferred")
    if not valid:
        warnings.append(msg)
        return result

    record["implementation_status"] = "deferred"
    extra: dict[str, Any] = {"rationale": str(rationale)[:_MAX_TEXT_LEN]}
    if deferred_until:
        extra["deferred_until"] = str(deferred_until)[:50]

    _append_implementation_metadata(
        record,
        action="defer",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="deferred",
        extra=extra,
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def mark_superseded(
    rule_id: str,
    implementer_id: str,
    superseded_by_rule_id: str | None = None,
    rationale: str = "",
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Mark an approved record as superseded.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    valid, msg = validate_status_transition(current_status, "superseded")
    if not valid:
        warnings.append(msg)
        return result

    record["implementation_status"] = "superseded"
    extra: dict[str, Any] = {}
    if superseded_by_rule_id:
        extra["superseded_by_rule_id"] = str(superseded_by_rule_id)[:200]
        record["superseded_by_rule_id"] = str(superseded_by_rule_id)[:200]
    if rationale:
        extra["rationale"] = str(rationale)[:_MAX_TEXT_LEN]

    _append_implementation_metadata(
        record,
        action="supersede",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="superseded",
        extra=extra,
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def mark_implemented(
    rule_id: str,
    implementer_id: str,
    implementation_commit: str = "",
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    Public wrapper: mark an implementation_planned record as implemented.

    Validates:
      - record exists
      - status is implementation_planned
      - caller matches the claiming implementer
    Records implementation_commit in metadata when provided.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    if current_status != "implementation_planned":
        warnings.append(f"Record status is {current_status}; must be implementation_planned")
        return result

    record_implementer = record.get("implementer", "")
    if record_implementer and record_implementer != implementer_id:
        warnings.append(
            f"Record claimed by {record_implementer}; cannot mark implemented by {implementer_id}"
        )
        return result

    # Transition status
    record["implementation_status"] = "implemented"

    extra: dict[str, Any] = {}
    if implementation_commit:
        extra["implementation_commit"] = str(implementation_commit)[:200]
        record["implementation_commit"] = str(implementation_commit)[:200]

    _append_implementation_metadata(
        record,
        action="mark_implemented",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="implemented",
        extra=extra,
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


def _mark_implemented_internal(
    rule_id: str,
    implementer_id: str,
    approved_path: Path | None = None,
) -> dict[str, Any]:
    """
    INTERNAL ONLY — Stage 1 does not expose this publicly.
    Used for synthetic fixture testing only.
    """
    warnings: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "rule_id": rule_id,
        "warnings": warnings,
        "record": None,
    }

    if not implementer_id:
        warnings.append("implementer_id is required")
        return result

    path = approved_path or _DEFAULT_APPROVED_PATH
    records, read_warnings = _read_approved_records(path)
    warnings.extend(read_warnings)

    record = _find_record(records, rule_id)
    if record is None:
        warnings.append(f"Rule {rule_id} not found")
        return result

    current_status = record.get("implementation_status", "")
    valid, msg = validate_status_transition(current_status, "implemented")
    if not valid:
        warnings.append(msg)
        return result

    record["implementation_status"] = "implemented"

    _append_implementation_metadata(
        record,
        action="mark_implemented",
        implementer_id=implementer_id,
        previous_status=current_status,
        new_status="implemented",
    )

    write_warnings = _write_approved_records(path, records)
    warnings.extend(write_warnings)

    result["success"] = True
    result["record"] = copy.deepcopy(record)
    return result


# ---------------------------------------------------------------------------
# CLI (minimal)
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    print("correction_implementation_planner.py is a library module. Import it, do not run directly.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
