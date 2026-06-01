#!/usr/bin/env python3
"""
Local Command Profile — Phase 1 Foundation

Public API:
    list_profiles(profile_dir="profiles") -> list[str]
        Returns available .json profile files in profile_dir.

    load_profile(profile_name_or_path, profile_dir="profiles") -> dict
        Accepts a direct JSON file path or a profile id that resolves to
        profile_dir/<name>.json.

    validate_profile(profile: dict) -> tuple[list[str], list[str]]
        Validates profile dict against schema expectations.
        Returns (errors, warnings).

    apply_profile_defaults(payload: dict, profile: dict, user_answers: dict | None = None) -> tuple[dict, dict]
        Merges profile defaults into a copy of payload without mutating inputs.
        Merge priority:
          1. explicit non-empty payload values
          2. user_answers values
          3. profile defaults
          4. empty remains empty
        Returns (merged_payload, merge_report).

CLI:
    python src/local_profile.py <profile.json> <payload.json> [user_answers.json]

Design choices:
    - Standalone module; no imports from intake_orchestrator or renderer.
    - Does not modify input dicts.
    - JSON-only profiles for v1.
    - No auto-activation.
    - Fake example data only in committed profiles.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROFILE_SCHEMA_VERSION = "LOCAL_PROFILE_V1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_missing(value: Any) -> bool:
    """Treat None, '', [], {} as missing."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and not value:
        return True
    if isinstance(value, dict) and not value:
        return True
    return False


def _deep_get(mapping: dict[str, Any], dot_path: str) -> Any:
    """Retrieve a nested value via dot-separated path; return None if absent."""
    parts = dot_path.split(".")
    current: Any = mapping
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _deep_set(mapping: dict[str, Any], dot_path: str, value: Any) -> None:
    """Set a nested value via dot-separated path, creating intermediate dicts."""
    parts = dot_path.split(".")
    current = mapping
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _flatten_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize flat dot-notation keys into nested dictionaries."""
    result: dict[str, Any] = {}
    for key, value in answers.items():
        if "." in key and not key.startswith("."):
            _deep_set(result, key, value)
        else:
            result[key] = value
    return result


def _field_paths_present(mapping: dict[str, Any]) -> list[str]:
    """Return list of top-level and dot-path field keys that are present."""
    paths: list[str] = []
    for key, value in mapping.items():
        if not _is_missing(value):
            paths.append(key)
        if isinstance(value, dict):
            for sub in _field_paths_present(value):
                paths.append(f"{key}.{sub}")
    return paths


def _resolve_repo_root() -> Path:
    """Return repo root by walking up from this file."""
    return Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_profiles(profile_dir: str = "profiles") -> list[str]:
    """List available .json profile files in profile_dir, excluding hidden files."""
    repo_root = _resolve_repo_root()
    target = repo_root / profile_dir
    if not target.exists():
        return []
    files = sorted(
        p.name
        for p in target.iterdir()
        if p.is_file() and p.suffix == ".json" and not p.name.startswith(".")
    )
    return files


def load_profile(profile_name_or_path: str, profile_dir: str = "profiles") -> dict[str, Any]:
    """Load a profile by path or by name resolving to profile_dir/<name>.json."""
    repo_root = _resolve_repo_root()
    path_candidate = Path(profile_name_or_path)

    # Try direct path first
    if path_candidate.exists() and path_candidate.suffix == ".json":
        return json.loads(path_candidate.read_text(encoding="utf-8"))

    # Resolve as name under profile_dir
    resolved = repo_root / profile_dir / f"{profile_name_or_path}.json"
    if resolved.exists():
        return json.loads(resolved.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"Profile not found: '{profile_name_or_path}' (tried path and {resolved})"
    )


def validate_profile(profile: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate a profile dict. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(profile, dict):
        errors.append("Profile must be a dict")
        return errors, warnings

    sv = profile.get("schema_version")
    if sv != _PROFILE_SCHEMA_VERSION:
        errors.append(f"schema_version must be '{_PROFILE_SCHEMA_VERSION}', got '{sv}'")

    for required in ("profile_id", "profile_name"):
        if not profile.get(required):
            errors.append(f"Missing required field: {required}")

    if not profile.get("command_info"):
        errors.append("Missing required field: command_info")
    elif not isinstance(profile["command_info"], dict):
        errors.append("command_info must be a dict")

    defaults = profile.get("defaults")
    if defaults is None:
        errors.append("Missing required field: defaults")
    elif not isinstance(defaults, dict):
        errors.append("defaults must be a dict")
    else:
        # Warn if defaults section is empty
        if not defaults:
            warnings.append("defaults section is empty")

    override_rules = profile.get("override_rules")
    if override_rules is not None and not isinstance(override_rules, list):
        errors.append("override_rules must be a list if present")
    elif isinstance(override_rules, list):
        for i, rule in enumerate(override_rules):
            if not isinstance(rule, dict):
                errors.append(f"override_rules[{i}] must be a dict")
                continue
            # Validate new optional fields if present
            if "source" in rule and not isinstance(rule["source"], str):
                errors.append(f"override_rules[{i}].source must be a string")
            if "disabled" in rule and not isinstance(rule["disabled"], bool):
                errors.append(f"override_rules[{i}].disabled must be a boolean")
            if "doc_type_filter" in rule and not isinstance(rule["doc_type_filter"], list):
                errors.append(f"override_rules[{i}].doc_type_filter must be a list")
            if "component_filter" in rule and not isinstance(rule["component_filter"], list):
                errors.append(f"override_rules[{i}].component_filter must be a list")

    # Validate optional new top-level fields
    if "correction_history" in profile and not isinstance(profile["correction_history"], list):
        errors.append("correction_history must be a list if present")
    if "promotion_metadata" in profile and not isinstance(profile["promotion_metadata"], dict):
        errors.append("promotion_metadata must be a dict if present")

    safety_notes = profile.get("safety_notes", [])
    if isinstance(safety_notes, list) and safety_notes:
        has_fake_warning = any("fake" in str(s).lower() or "example" in str(s).lower() for s in safety_notes)
        if profile.get("profile_id", "").startswith("example") and not has_fake_warning:
            warnings.append("Example profile should include a fake/example safety note")

    # Warns if real-looking contact info in example
    if profile.get("profile_id", "").startswith("example"):
        poc = profile.get("poc_defaults", {})
        email = str(poc.get("email", "")).lower()
        if email and not ("example" in email or "fake" in email or "test" in email):
            warnings.append("Example profile POC email does not appear fake; verify it is not real")
        phone = str(poc.get("telephone", ""))
        if phone and not ("555" in phone or "example" in phone.lower()):
            warnings.append("Example profile POC telephone does not appear fake; verify it is not real")

    return errors, warnings


def _signature_for_doc_type(profile: dict[str, Any], doc_type: str | None) -> Any:
    """Return a signature block from profile if payload lacks one and doc_type matches."""
    blocks = profile.get("signature_blocks")
    if not isinstance(blocks, dict):
        return None
    if not doc_type:
        return None
    return blocks.get(doc_type)


def apply_profile_defaults(
    payload: dict[str, Any],
    profile: dict[str, Any],
    user_answers: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge profile defaults into payload copy. Does not mutate inputs.

    Merge priority:
      1. explicit non-empty payload values win
      2. user_answers values fill missing fields
      3. profile defaults fill remaining missing fields
      4. empty remains empty

    Returns (merged_payload, merge_report).
    """
    merged = copy.deepcopy(payload)
    normalized_answers = _flatten_answers(copy.deepcopy(user_answers) if user_answers else {})
    profile_defaults = copy.deepcopy(profile.get("defaults", {}))

    fields_from_payload: list[str] = []
    fields_from_user_answers: list[str] = []
    fields_from_profile: list[str] = []
    fields_still_missing: list[str] = []
    merge_warnings: list[str] = []

    # Determine all field keys worth checking (top-level payload keys)
    all_keys = set(merged.keys()) | set(normalized_answers.keys()) | set(profile_defaults.keys())

    # Special: signature_blocks derived from doc_type
    doc_type = merged.get("doc_type") or normalized_answers.get("doc_type")
    profile_sig = _signature_for_doc_type(profile, doc_type)
    if profile_sig is not None:
        all_keys.add("signature")

    def _track(field: str, source: str) -> None:
        if source == "payload":
            if field not in fields_from_payload:
                fields_from_payload.append(field)
        elif source == "user_answers":
            if field not in fields_from_user_answers:
                fields_from_user_answers.append(field)
        elif source == "profile":
            if field not in fields_from_profile:
                fields_from_profile.append(field)

    # Determine applicable override rules (Priority 3 in merge stack)
    doc_type = merged.get("doc_type") or normalized_answers.get("doc_type")
    component = merged.get("component") or normalized_answers.get("component") or profile.get("command_info", {}).get("component_service")

    applicable_overrides: dict[str, Any] = {}
    for rule in profile.get("override_rules", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("disabled"):
            continue
        # Respect doc_type_filter
        dtf = rule.get("doc_type_filter", [])
        if dtf and doc_type not in dtf:
            continue
        # Respect component_filter
        ctf = rule.get("component_filter", [])
        if ctf and component not in ctf:
            continue
        fp = rule.get("field_path", "")
        if fp:
            applicable_overrides[fp] = rule.get("value")

    fields_from_profile_override: list[str] = []

    # Merge logic per key
    for key in sorted(all_keys):
        # Priority 1: payload explicit non-empty
        if not _is_missing(merged.get(key)):
            _track(key, "payload")
            continue

        # Priority 2: user_answers
        ua_val = normalized_answers.get(key)
        if not _is_missing(ua_val):
            merged[key] = copy.deepcopy(ua_val)
            _track(key, "user_answers")
            continue

        # Priority 3: promoted profile corrections (override_rules)
        or_val = applicable_overrides.get(key)
        if not _is_missing(or_val):
            merged[key] = copy.deepcopy(or_val)
            _track(key, "profile")
            fields_from_profile_override.append(key)
            continue

        # Priority 4: profile defaults
        pd_val = profile_defaults.get(key)
        if not _is_missing(pd_val):
            merged[key] = copy.deepcopy(pd_val)
            _track(key, "profile")
            continue

        # Special: signature from profile signature_blocks
        if key == "signature" and profile_sig is not None:
            merged[key] = copy.deepcopy(profile_sig)
            _track(key, "profile")
            continue

        # Still empty
        if key in merged and not _is_missing(merged[key]):
            # Already set above
            pass
        else:
            fields_still_missing.append(key)

    # Post-merge: fill point_of_contact from poc_defaults if both are missing
    poc_ua = normalized_answers.get("point_of_contact")
    poc_payload = merged.get("point_of_contact")
    poc_profile = profile.get("poc_defaults")
    if _is_missing(poc_payload) and _is_missing(poc_ua) and not _is_missing(poc_profile):
        merged["point_of_contact"] = copy.deepcopy(poc_profile)
        _track("point_of_contact", "profile")
        if "point_of_contact" in fields_still_missing:
            fields_still_missing.remove("point_of_contact")

    # Remove duplicates from fields_still_missing that are actually present now
    fields_still_missing = [
        k for k in fields_still_missing
        if k not in fields_from_payload and k not in fields_from_user_answers and k not in fields_from_profile
    ]

    profile_id = profile.get("profile_id", "unknown")
    profile_name = profile.get("profile_name", "unknown")

    merge_report = {
        "profile_id": profile_id,
        "profile_name": profile_name,
        "fields_from_payload": fields_from_payload,
        "fields_from_user_answers": fields_from_user_answers,
        "fields_from_profile": fields_from_profile,
        "fields_from_profile_override": fields_from_profile_override,
        "fields_still_missing": fields_still_missing,
        "warnings": merge_warnings,
    }

    return merged, merge_report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Usage: python src/local_profile.py <profile.json> <payload.json> [user_answers.json]", file=sys.stderr)
        return 1

    profile_path = Path(argv[1])
    payload_path = Path(argv[2])
    user_answers: dict[str, Any] = {}

    if len(argv) >= 4:
        ua_path = Path(argv[3])
        if ua_path.exists():
            user_answers = json.loads(ua_path.read_text(encoding="utf-8"))

    if not profile_path.exists():
        print(f"ERROR: profile not found: {profile_path}", file=sys.stderr)
        return 1
    if not payload_path.exists():
        print(f"ERROR: payload not found: {payload_path}", file=sys.stderr)
        return 1

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    errors, warnings = validate_profile(profile)
    if errors:
        for e in errors:
            print(f"VALIDATION ERROR: {e}")
        return 1
    if warnings:
        for w in warnings:
            print(f"VALIDATION WARNING: {w}")

    merged, report = apply_profile_defaults(payload, profile, user_answers)

    print("=" * 72)
    print("MERGED PAYLOAD KEYS")
    print("=" * 72)
    for k in sorted(merged.keys()):
        print(f"  {k}: {type(merged[k]).__name__}")
    print()
    print("=" * 72)
    print("MERGE REPORT")
    print("=" * 72)
    print(json.dumps(report, indent=2))
    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
