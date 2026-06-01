#!/usr/bin/env python3
"""
Correction Store — Phase A Session Correction Persistence

Public API:
    save_session_correction(session_id: str, correction_record: dict) -> list[str]
        Append or replace a correction record in the session JSONL store.

    load_session_corrections(
        session_id: str,
        doc_type: str | None = None,
        component: str | None = None,
        field_path: str | None = None,
        exclude_rejected: bool = True,
    ) -> list[dict]
        Read and filter corrections from the session store.

    update_session_correction_status(
        session_id: str,
        correction_id: str,
        promotion_status: str,
    ) -> bool
        Update promotion_status on an existing record.

    delete_session_correction(session_id: str, correction_id: str) -> bool
        Remove a specific correction from the session store.

    delete_session_file(session_id: str) -> bool
        Remove the entire session file.

    set_session_correction_rejected(
        session_id: str,
        correction_id: str,
        rejected: bool = True,
    ) -> bool
        Set or clear user_rejected on an existing record.

Design choices:
    - All JSONL I/O is isolated in this module.
    - Atomic writes: write to .tmp then rename.
    - Missing session files return empty list (no crash).
    - Session directory is created on first save.
    - No automatic cleanup in Phase A (retention is advisory).
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SESSION_DIR = _REPO_ROOT / "corrections" / "session"

_SAFE_SESSION_ID = re.compile(r"^[a-zA-Z0-9_-]+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session_path(session_id: str) -> Path:
    if not _SAFE_SESSION_ID.match(session_id):
        raise ValueError(f"Invalid session_id: {session_id!r}")
    return _SESSION_DIR / f"{session_id}.jsonl"


def _ensure_session_dir() -> None:
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _tighten_permissions(path: Path) -> list[str]:
    warnings: list[str] = []
    try:
        if os.name == "nt":
            # Windows: no simple octal mode equivalent via stdlib
            pass
        else:
            os.chmod(path, 0o600)
    except Exception as exc:
        warnings.append(f"Could not tighten permissions on {path}: {exc}")
    return warnings


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read a JSONL file. Returns (records, warnings)."""
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not path.exists():
        return records, warnings
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)
            else:
                warnings.append(f"Line {i} in {path.name} is not a dict; skipped")
        except json.JSONDecodeError as exc:
            warnings.append(f"Line {i} in {path.name} JSON parse error: {exc}")
    return records, warnings


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> list[str]:
    """Atomically write records to JSONL. Returns warnings."""
    warnings: list[str] = []
    tmp = path.with_suffix(".tmp")
    try:
        lines = [json.dumps(r, ensure_ascii=False) + "\n" for r in records]
        tmp.write_text("".join(lines), encoding="utf-8")
        os.replace(str(tmp), str(path))
        warnings.extend(_tighten_permissions(path))
    except Exception as exc:
        warnings.append(f"Failed writing session file {path.name}: {exc}")
    return warnings


def _validate_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a correction_record has required fields."""
    warnings: list[str] = []
    for key in ("correction_id", "field_path", "doc_type", "component", "timestamp"):
        if not record.get(key):
            warnings.append(f"Record missing required field: {key}")
    return (len(warnings) == 0), warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_session_correction(session_id: str, correction_record: dict[str, Any]) -> list[str]:
    """
    Append or replace a correction record in the session JSONL store.
    If a record with the same correction_id exists, replace it.
    Otherwise, append.
    """
    warnings: list[str] = []
    valid, validate_warnings = _validate_record(correction_record)
    if not valid:
        warnings.extend(validate_warnings)
        return warnings

    _ensure_session_dir()
    path = _session_path(session_id)
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    cid = correction_record.get("correction_id")
    replaced = False
    for i, r in enumerate(records):
        if r.get("correction_id") == cid:
            records[i] = copy.deepcopy(correction_record)
            replaced = True
            break
    if not replaced:
        records.append(copy.deepcopy(correction_record))

    write_warnings = _write_jsonl(path, records)
    warnings.extend(write_warnings)
    return warnings


def load_session_corrections(
    session_id: str,
    doc_type: str | None = None,
    component: str | None = None,
    field_path: str | None = None,
    exclude_rejected: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Load corrections from session store with optional filters.
    Returns (matching_records, warnings).
    """
    warnings: list[str] = []
    path = _session_path(session_id)
    records, read_warnings = _read_jsonl(path)
    warnings.extend(read_warnings)

    filtered: list[dict[str, Any]] = []
    for r in records:
        if exclude_rejected and r.get("user_rejected"):
            continue
        if doc_type is not None and r.get("doc_type") != doc_type:
            continue
        if component is not None and r.get("component") != component:
            continue
        if field_path is not None and r.get("field_path") != field_path:
            continue
        filtered.append(r)
    return filtered, warnings


def update_session_correction_status(
    session_id: str,
    correction_id: str,
    promotion_status: str,
) -> bool:
    """Update promotion_status on an existing record. Returns True if found and updated."""
    path = _session_path(session_id)
    records, _ = _read_jsonl(path)
    for r in records:
        if r.get("correction_id") == correction_id:
            r["promotion_status"] = promotion_status
            _write_jsonl(path, records)
            return True
    return False


def set_session_correction_rejected(
    session_id: str,
    correction_id: str,
    rejected: bool = True,
) -> bool:
    """Set or clear user_rejected flag. Returns True if found and updated."""
    path = _session_path(session_id)
    records, _ = _read_jsonl(path)
    for r in records:
        if r.get("correction_id") == correction_id:
            r["user_rejected"] = bool(rejected)
            _write_jsonl(path, records)
            return True
    return False


def delete_session_correction(session_id: str, correction_id: str) -> bool:
    """Remove a specific correction from the session store. Returns True if removed."""
    path = _session_path(session_id)
    records, _ = _read_jsonl(path)
    new_records = [r for r in records if r.get("correction_id") != correction_id]
    if len(new_records) == len(records):
        return False
    _write_jsonl(path, new_records)
    return True


def delete_session_file(session_id: str) -> bool:
    """Remove the entire session file. Returns True if file existed and was removed."""
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
        return True
    return False
