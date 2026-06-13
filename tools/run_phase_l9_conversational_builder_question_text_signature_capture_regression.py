#!/usr/bin/env python3
"""
Phase L.9 — Conversational Builder Question Text and Signature Capture Regression

Tests structured signature capture and question text improvements.

Exit codes:
    0  all checks pass
    1  one or more checks fail

Non-goals:
- no renderer/layout changes
- no CCI config/severity changes
- no validator/catalog changes
- no Phase F/G command-layer changes
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from conversational_builder import BuilderSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sig_is_dict(session: BuilderSession) -> bool:
    payload = session.build_payload()
    sig = payload.get("signature")
    return isinstance(sig, dict)


def _sig_field(session: BuilderSession, field: str, expected: str) -> bool:
    payload = session.build_payload()
    sig = payload.get("signature")
    if not isinstance(sig, dict):
        return False
    return sig.get(field) == expected


def _sig_name(session: BuilderSession) -> str | None:
    payload = session.build_payload()
    sig = payload.get("signature")
    if isinstance(sig, dict):
        return sig.get("name")
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_signature_name_ingestion() -> None:
    """signature.name: J. Q. Sample stores signature dict with name field."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample")
    _assert(_sig_is_dict(builder), "signature should be a dict after signature.name ingestion")
    _assert(_sig_field(builder, "name", "J. Q. Sample"), "signature.name should equal 'J. Q. Sample'")


def test_signature_role_ingestion() -> None:
    """signature.role: Commanding Officer stores role in signature dict."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.role: Commanding Officer")
    _assert(_sig_is_dict(builder), "signature should be a dict after signature.role ingestion")
    _assert(_sig_field(builder, "role", "Commanding Officer"), "signature.role should equal 'Commanding Officer'")


def test_signature_title_ingestion() -> None:
    """signature.title: Commanding Officer stores title in signature dict."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.title: Commanding Officer")
    _assert(_sig_is_dict(builder), "signature should be a dict after signature.title ingestion")
    _assert(_sig_field(builder, "title", "Commanding Officer"), "signature.title should equal 'Commanding Officer'")


def test_multi_field_signature_dict() -> None:
    """Multiple signature.* fields merge into a single dict."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample")
    builder.ingest_user_message("signature.role: Commanding Officer")
    builder.ingest_user_message("signature.title: CO")
    _assert(_sig_is_dict(builder), "signature should be a dict after multi-field ingestion")
    _assert(_sig_field(builder, "name", "J. Q. Sample"), "name should be preserved")
    _assert(_sig_field(builder, "role", "Commanding Officer"), "role should be preserved")
    _assert(_sig_field(builder, "title", "CO"), "title should be preserved")


def test_plain_signature_maps_to_dict_name() -> None:
    """Plain 'signature: J. Q. Sample' maps safely to structured dict.name."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature: J. Q. Sample")
    _assert(_sig_is_dict(builder), "plain signature: should produce a dict, not a list")
    _assert(_sig_field(builder, "name", "J. Q. Sample"), "plain signature should map to dict.name")


def test_finalize_payload_has_renderer_compatible_signature() -> None:
    """Finalized payload contains a renderer-compatible signature dict."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample")
    builder.ingest_user_message("signature.role: Commanding Officer")
    result = builder.finalize(accept_warnings=True)
    payload = result.get("payload", {})
    sig = payload.get("signature")
    _assert(isinstance(sig, dict), "finalized signature should be a dict")
    _assert(sig.get("name") == "J. Q. Sample", "finalized signature.name should match")
    _assert(sig.get("role") == "Commanding Officer", "finalized signature.role should match")


def test_signature_not_list_after_name_ingestion() -> None:
    """signature.name ingestion should not produce a list."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample")
    payload = builder.build_payload()
    sig = payload.get("signature")
    _assert(not isinstance(sig, list), "signature should not be a list after signature.name ingestion")


def test_builder_version_is_l9() -> None:
    """Builder version should reflect L.9."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    result = builder.finalize(accept_warnings=True)
    _assert(result.get("builder_version") == "L.9", "builder_version should be L.9")


def test_signature_name_only_dict() -> None:
    """signature.name alone produces dict with name set and other keys None/default."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample")
    payload = builder.build_payload()
    sig = payload.get("signature")
    _assert(isinstance(sig, dict), "signature should be a dict")
    _assert(sig.get("name") == "J. Q. Sample", "name should be set")
    # role/title may be None or absent — both are acceptable
    _assert("role" not in sig or sig.get("role") is None, "role should be unset when only name provided")
    _assert("title" not in sig or sig.get("title") is None, "title should be unset when only name provided")


def test_signature_dict_with_trailing_spaces() -> None:
    """signature.name values with trailing spaces are stripped."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.ingest_user_message("signature.name: J. Q. Sample   ")
    _assert(_sig_field(builder, "name", "J. Q. Sample"), "trailing spaces should be stripped from signature.name")


def test_set_signature_field_api() -> None:
    """set_signature_field(name, value) sets individual signature dict fields."""
    builder = BuilderSession()
    builder.start(initial_payload={"doc_type": "standard_letter", "component": {"service": "NAVY"}})
    builder.set_signature_field("name", "J. Q. Sample")
    builder.set_signature_field("role", "Commanding Officer")
    _assert(_sig_field(builder, "name", "J. Q. Sample"), "set_signature_field should set name")
    _assert(_sig_field(builder, "role", "Commanding Officer"), "set_signature_field should set role")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

_TESTS = [
    test_signature_name_ingestion,
    test_signature_role_ingestion,
    test_signature_title_ingestion,
    test_multi_field_signature_dict,
    test_plain_signature_maps_to_dict_name,
    test_finalize_payload_has_renderer_compatible_signature,
    test_signature_not_list_after_name_ingestion,
    test_builder_version_is_l9,
    test_signature_name_only_dict,
    test_signature_dict_with_trailing_spaces,
    test_set_signature_field_api,
]


def run_all() -> int:
    passed = 0
    failed = 0
    for test in _TESTS:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERR   {test.__name__}: {e}")
            failed += 1

    print()
    print(f"Results: {passed}/{len(_TESTS)} passed, {failed}/{len(_TESTS)} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
