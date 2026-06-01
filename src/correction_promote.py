#!/usr/bin/env python3
"""
Correction Promotion — Phase C: Local Command Profile Promotion

Public API:
    propose_promotion(correction_record: dict, profile_path: str) -> dict
        Step 1: generate a promotion proposal with diff info.

    confirm_and_write_promotion(proposal: dict) -> dict
        Step 2: validate, backup, write to profile override_rules atomically.

    is_eligible_for_promotion(correction_record: dict) -> tuple[bool, list[str]]
        Check whether a correction record meets all eligibility criteria.

    list_promoted_corrections(profile_path: str) -> list[dict]
        Return all override_rules entries from a profile.

    disable_promoted_correction(profile_path: str, field_path: str) -> dict
        Soft-disable an override_rules entry by setting disabled=true.

    remove_promoted_correction(profile_path: str, field_path: str) -> dict
        Delete an override_rules entry with confirmation summary.

    edit_promoted_correction(profile_path: str, field_path: str,
                             new_value: Any, reason: str = "") -> dict
        Replace an existing override_rules entry; runs full approval workflow.

Design choices:
    - All file writes are atomic (temp file + os.replace).
    - Backups are timestamped; only last 10 retained.
    - Profile size warning at 100 KB (soft).
    - No auto-approve; two-step confirmation required.
    - External profile paths only; blocks example profiles.
    - No side effects on renderer or session stores.
"""

from __future__ import annotations

import copy
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Import local_profile for validation; handle both import and direct execution
import sys

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

try:
    from local_profile import validate_profile, load_profile
except Exception:
    # Allow script-level testing without full project setup
    def validate_profile(profile: dict) -> tuple[list[str], list[str]]:
        return [], []
    def load_profile(path: str, profile_dir: str = "profiles") -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROFILE_SIZE_WARN_KB = 100
_BACKUP_RETENTION = 10
_ALLOWED_PROMOTION_TYPES = {"local_command_preference"}
_ALLOWED_PROMOTION_FIELDS = {
    "from", "to", "signature", "point_of_contact",
    "ssic", "originator_code", "unit_identity", "letterhead_lines",
}
_INVALID_PLACEHOLDERS = {"tbd", "todo", "placeholder", "<tbd>", "<todo>"}
_EXAMPLE_PATH_PATTERNS = re.compile(r"example", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

def is_eligible_for_promotion(correction_record: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check whether a correction record is eligible for profile promotion.
    Returns (eligible, reasons).
    """
    reasons: list[str] = []
    eligible = True

    # 1. Classification
    ctype = correction_record.get("correction_type", "unknown")
    if ctype not in _ALLOWED_PROMOTION_TYPES:
        reasons.append(f"Ineligible classification: {ctype}")
        eligible = False

    # 2. Scope
    scope = correction_record.get("scope", "active_draft")
    if scope != "current_session":
        reasons.append(f"Ineligible scope: {scope} (must be current_session)")
        eligible = False

    # 3. Field path
    fp = correction_record.get("field_path", "")
    if fp not in _ALLOWED_PROMOTION_FIELDS:
        reasons.append(f"Ineligible field_path: {fp}")
        eligible = False

    # 4. User approval status — not rejected
    if correction_record.get("user_rejected"):
        reasons.append("Correction was rejected by user")
        eligible = False

    # 5. No validator conflict
    if correction_record.get("validator_conflict"):
        reasons.append("Correction has validator_conflict=True")
        eligible = False

    # 6. Value stability
    corrected = str(correction_record.get("corrected_value", "")).strip()
    if not corrected:
        reasons.append("Corrected value is empty")
        eligible = False
    elif corrected.lower() in _INVALID_PLACEHOLDERS:
        reasons.append(f"Corrected value is a placeholder: {corrected}")
        eligible = False

    # 7. Session recency — caller must ensure current session only
    # We do not enforce session_id matching here; that is orchestrator-level.

    if eligible:
        reasons.append("Correction is eligible for profile promotion")

    return eligible, reasons


# ---------------------------------------------------------------------------
# Proposal (Step 1)
# ---------------------------------------------------------------------------

def propose_promotion(
    correction_record: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    """
    Step 1 — Generate a promotion proposal.

    Returns a proposal dict with:
      - eligibility check
      - current profile value (if any)
      - corrected value
      - diff summary
      - required confirmation flag
    """
    proposal: dict[str, Any] = {
        "step": 1,
        "eligible": False,
        "field_path": correction_record.get("field_path", ""),
        "corrected_value": correction_record.get("corrected_value"),
        "profile_path": profile_path,
        "reasons": [],
        "can_proceed": False,
    }

    eligible, reasons = is_eligible_for_promotion(correction_record)
    proposal["eligible"] = eligible
    proposal["reasons"] = reasons

    if not eligible:
        return proposal

    # Block example profile paths
    if _EXAMPLE_PATH_PATTERNS.search(profile_path):
        proposal["eligible"] = False
        proposal["reasons"].append("Promotion to example profile is blocked")
        return proposal

    # Load existing profile to show current value
    try:
        profile = load_profile(profile_path)
    except Exception as exc:
        proposal["profile_load_error"] = str(exc)
        proposal["current_value"] = None
    else:
        proposal["profile_id"] = profile.get("profile_id")
        # Check existing override_rules for same field
        overrides = profile.get("override_rules", [])
        existing = None
        for rule in overrides:
            if rule.get("field_path") == proposal["field_path"]:
                existing = rule.get("value")
                break
        if existing is None:
            # Check defaults
            existing = profile.get("defaults", {}).get(proposal["field_path"])
        proposal["current_value"] = existing

    doc_type = correction_record.get("doc_type", "unknown")
    component = correction_record.get("component", "unknown")
    proposal["doc_type"] = doc_type
    proposal["component"] = component
    proposal["can_proceed"] = True
    return proposal


# ---------------------------------------------------------------------------
# Confirmation + Write (Step 2)
# ---------------------------------------------------------------------------

def confirm_and_write_promotion(
    proposal: dict[str, Any],
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Step 2 — Validate, backup, and write the promotion to the profile.

    Must receive `confirmed=True` from caller (two-step workflow).
    Returns result dict with success/failure, warnings, and metadata.
    """
    result: dict[str, Any] = {
        "success": False,
        "profile_path": proposal.get("profile_path"),
        "field_path": proposal.get("field_path"),
        "warnings": [],
    }

    if not proposal.get("eligible"):
        result["warnings"].append("Proposal is not eligible")
        return result

    if not proposal.get("can_proceed"):
        result["warnings"].append("Proposal cannot proceed")
        return result

    if not confirmed:
        result["warnings"].append("Promotion not confirmed by caller")
        return result

    profile_path = proposal["profile_path"]

    # Block example profiles again at write time (defense in depth)
    if _EXAMPLE_PATH_PATTERNS.search(profile_path):
        result["warnings"].append("Promotion to example profile is blocked")
        return result

    try:
        profile = load_profile(profile_path)
    except Exception as exc:
        result["warnings"].append(f"Failed to load profile: {exc}")
        return result

    # Validate before mutation
    errors, warnings = validate_profile(profile)
    if errors:
        result["warnings"].extend(f"Pre-write validation error: {e}" for e in errors)
        return result
    result["warnings"].extend(f"Pre-write validation warning: {w}" for w in warnings)

    # Field type consistency check
    existing_type = _get_existing_value_type(profile, proposal["field_path"])
    new_type = type(proposal["corrected_value"]).__name__
    if existing_type is not None and existing_type != new_type:
        result["warnings"].append(
            f"Type mismatch: existing={existing_type}, new={new_type}"
        )
        return result

    # Backup
    backup_warnings = _create_backup(profile_path)
    result["warnings"].extend(backup_warnings)

    # Mutate profile
    overrides = profile.setdefault("override_rules", [])
    # Remove existing rule for same field_path
    overrides[:] = [r for r in overrides if r.get("field_path") != proposal["field_path"]]

    doc_type = proposal.get("doc_type", "unknown")
    component = proposal.get("component", "unknown")

    new_rule: dict[str, Any] = {
        "field_path": proposal["field_path"],
        "value": copy.deepcopy(proposal["corrected_value"]),
        "doc_type_filter": [doc_type] if doc_type and doc_type != "unknown" else [],
        "component_filter": [component] if component and component != "unknown" else [],
        "source": "user_promoted_correction",
        "disabled": False,
    }
    overrides.append(new_rule)

    # Update correction_history
    history = profile.setdefault("correction_history", [])
    history.append({
        "field_path": proposal["field_path"],
        "previous_value": proposal.get("current_value"),
        "corrected_value": proposal["corrected_value"],
        "promoted_at": _utcnow(),
        "doc_type": doc_type,
        "component": component,
        "session_correction_id": proposal.get("correction_id"),
    })

    # Update promotion_metadata
    meta = profile.setdefault("promotion_metadata", {})
    meta["last_promoted_at"] = _utcnow()
    meta["promotion_count"] = meta.get("promotion_count", 0) + 1

    # Post-mutation validation
    errors2, warnings2 = validate_profile(profile)
    if errors2:
        result["warnings"].extend(f"Post-write validation error: {e}" for e in errors2)
        return result
    result["warnings"].extend(f"Post-write validation warning: {w}" for w in warnings2)

    # Profile size warning
    profile_json = json.dumps(profile, ensure_ascii=False)
    size_kb = len(profile_json.encode("utf-8")) / 1024.0
    if size_kb > _PROFILE_SIZE_WARN_KB:
        result["warnings"].append(
            f"Profile size is {size_kb:.1f} KB (exceeds {_PROFILE_SIZE_WARN_KB} KB warning threshold)"
        )

    # Atomic write
    write_warnings = _atomic_write_json(profile_path, profile)
    result["warnings"].extend(write_warnings)

    result["success"] = True
    result["size_kb"] = round(size_kb, 2)
    return result


# ---------------------------------------------------------------------------
# List / Disable / Remove / Edit
# ---------------------------------------------------------------------------

def list_promoted_corrections(profile_path: str) -> list[dict[str, Any]]:
    """Return all override_rules entries from a profile."""
    try:
        profile = load_profile(profile_path)
    except Exception:
        return []
    return copy.deepcopy(profile.get("override_rules", []))


def disable_promoted_correction(
    profile_path: str,
    field_path: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Soft-disable an override_rules entry by setting disabled=true."""
    result: dict[str, Any] = {"success": False, "field_path": field_path, "warnings": []}
    if not confirmed:
        result["warnings"].append("Disable not confirmed")
        return result
    try:
        profile = load_profile(profile_path)
    except Exception as exc:
        result["warnings"].append(f"Load failed: {exc}")
        return result

    overrides = profile.get("override_rules", [])
    found = False
    for rule in overrides:
        if rule.get("field_path") == field_path:
            rule["disabled"] = True
            found = True
            break
    if not found:
        result["warnings"].append(f"No override_rules entry found for {field_path}")
        return result

    _create_backup(profile_path)
    write_warnings = _atomic_write_json(profile_path, profile)
    result["warnings"].extend(write_warnings)
    result["success"] = True
    return result


def remove_promoted_correction(
    profile_path: str,
    field_path: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Delete an override_rules entry with confirmation summary."""
    result: dict[str, Any] = {"success": False, "field_path": field_path, "warnings": []}
    if not confirmed:
        result["warnings"].append("Remove not confirmed")
        return result
    try:
        profile = load_profile(profile_path)
    except Exception as exc:
        result["warnings"].append(f"Load failed: {exc}")
        return result

    overrides = profile.get("override_rules", [])
    new_overrides = [r for r in overrides if r.get("field_path") != field_path]
    if len(new_overrides) == len(overrides):
        result["warnings"].append(f"No override_rules entry found for {field_path}")
        return result

    profile["override_rules"] = new_overrides
    _create_backup(profile_path)
    write_warnings = _atomic_write_json(profile_path, profile)
    result["warnings"].extend(write_warnings)
    result["success"] = True
    result["removed_count"] = len(overrides) - len(new_overrides)
    return result


def edit_promoted_correction(
    profile_path: str,
    field_path: str,
    new_value: Any,
    reason: str = "",
    confirmed: bool = False,
    doc_type: str = "unknown",
    component: str = "unknown",
) -> dict[str, Any]:
    """
    Replace an existing override_rules entry. Runs full approval-like workflow
    but caller is assumed to have already presented a diff.
    """
    result: dict[str, Any] = {
        "success": False,
        "field_path": field_path,
        "warnings": [],
    }
    if not confirmed:
        result["warnings"].append("Edit not confirmed")
        return result

    # Build a synthetic correction_record for eligibility reuse
    synthetic_record: dict[str, Any] = {
        "correction_type": "local_command_preference",
        "scope": "current_session",
        "field_path": field_path,
        "corrected_value": new_value,
        "user_rejected": False,
        "validator_conflict": False,
        "doc_type": doc_type,
        "component": component,
    }
    eligible, reasons = is_eligible_for_promotion(synthetic_record)
    if not eligible:
        result["warnings"].extend(reasons)
        return result

    proposal = propose_promotion(synthetic_record, profile_path)
    if not proposal.get("eligible"):
        result["warnings"].extend(proposal.get("reasons", []))
        return result

    return confirm_and_write_promotion(proposal, confirmed=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_existing_value_type(profile: dict[str, Any], field_path: str) -> str | None:
    """Return the type name of an existing value for field_path, or None."""
    # Check override_rules first
    for rule in profile.get("override_rules", []):
        if rule.get("field_path") == field_path and not rule.get("disabled"):
            val = rule.get("value")
            if val is not None:
                return type(val).__name__
    # Check defaults
    val = profile.get("defaults", {}).get(field_path)
    if val is not None:
        return type(val).__name__
    return None


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _create_backup(profile_path: str) -> list[str]:
    """Create a timestamped backup of profile_path. Keep last _BACKUP_RETENTION."""
    warnings: list[str] = []
    path = Path(profile_path)
    if not path.exists():
        return warnings
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.name}.backup.{timestamp}"
    backup_path = path.parent / backup_name
    try:
        shutil.copy2(str(path), str(backup_path))
    except Exception as exc:
        warnings.append(f"Backup creation failed: {exc}")
        return warnings
    # Prune old backups
    pattern = f"{path.name}.backup.*"
    backups = sorted(
        path.parent.glob(pattern),
        key=lambda p: p.stat().st_mtime,
    )
    to_remove = backups[: max(0, len(backups) - _BACKUP_RETENTION)]
    for old in to_remove:
        try:
            old.unlink()
        except Exception as exc:
            warnings.append(f"Failed to remove old backup {old.name}: {exc}")
    return warnings


def _atomic_write_json(file_path: str, data: dict[str, Any]) -> list[str]:
    """Write JSON atomically via temp file + os.replace."""
    warnings: list[str] = []
    path = Path(file_path)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if hasattr(os, "replace"):
            os.replace(str(tmp), str(path))
        else:
            # Fallback for very old Python / Windows
            if path.exists():
                path.unlink()
            shutil.move(str(tmp), str(path))
    except Exception as exc:
        warnings.append(f"Atomic write failed: {exc}")
    return warnings


# ---------------------------------------------------------------------------
# CLI (minimal)
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    print("correction_promote.py is a library module. Import it, do not run directly.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
