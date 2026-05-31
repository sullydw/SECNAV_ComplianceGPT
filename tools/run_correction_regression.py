#!/usr/bin/env python3
"""
Correction Memory Regression Runner — Phase 1 Active Draft

Exercises:
  1. Capture correction for subj.
  2. Apply correction to subj and verify changed.
  3. Verify original payload unchanged.
  4. Undo correction and verify original restored.
  5. Apply correction to nested field point_of_contact.email.
  6. Apply correction to list field body[0].
  7. Apply multiple corrections in order.
  8. Try invalid list path body[99] and verify warning, no crash.
  9. Capture correction for missing dict path local_notes.review_status and verify original_value is None and warning returned.
 10. Run run_cci_audit() before/after on at least one corrected payload and verify schema_version CCI_AUDIT_V1.

Exit 0 if all expectations met.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on path (repo root is one up from tools/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from correction_apply import apply_correction, apply_corrections, undo_correction, get_path_value
from correction_capture import capture_correction


def _load_json(rel_path: str) -> Any:
    path = _ROOT / rel_path
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_eq(label: str, actual: Any, expected: Any) -> list[str]:
    if actual != expected:
        return [f"FAIL {label}: expected {expected!r}, got {actual!r}"]
    return [f"PASS {label}"]


def main() -> int:
    failures: list[str] = []
    results: list[str] = []

    payload = _load_json("examples/audit_correction_apply.json")
    original_subj = payload["subj"]
    original_poc_email = payload["point_of_contact"]["email"]
    original_body0 = payload["body"][0]

    # ------------------------------------------------------------------
    # 1. Capture correction for subj
    # ------------------------------------------------------------------
    record, cap_warnings = capture_correction(
        payload,
        field_path="subj",
        corrected_value="POLICY UPDATE",
        reason="Remove terminal punctuation from subject line.",
        correction_type="possible_secnav_manual_rule",
    )
    results.append("[1] capture_correction(subj)")
    failures.extend(_assert_eq("record field_path", record.get("field_path"), "subj"))
    failures.extend(_assert_eq("record original_value", record.get("original_value"), original_subj))
    failures.extend(_assert_eq("record corrected_value", record.get("corrected_value"), "POLICY UPDATE"))
    failures.extend(_assert_eq("record scope", record.get("scope"), "active_draft"))
    failures.extend(_assert_eq("record doc_type", record.get("doc_type"), "standard_letter"))
    failures.extend(_assert_eq("record component", record.get("component"), "marine_corps"))
    failures.extend(_assert_eq("record correction_type", record.get("correction_type"), "possible_secnav_manual_rule"))
    failures.extend(_assert_eq("record source", record.get("source"), "user"))
    failures.extend(_assert_eq("capture warnings", cap_warnings, []))

    # ------------------------------------------------------------------
    # 2. Apply correction to subj and verify changed
    # ------------------------------------------------------------------
    new_payload, apply_warnings = apply_correction(payload, record)
    results.append("[2] apply_correction(subj)")
    failures.extend(_assert_eq("applied subj", new_payload.get("subj"), "POLICY UPDATE"))
    failures.extend(_assert_eq("apply_warnings", apply_warnings, []))

    # ------------------------------------------------------------------
    # 3. Verify original payload unchanged
    # ------------------------------------------------------------------
    results.append("[3] verify original unchanged")
    failures.extend(_assert_eq("original subj", payload["subj"], original_subj))

    # ------------------------------------------------------------------
    # 4. Undo correction and verify original restored
    # ------------------------------------------------------------------
    undone_payload, undo_warnings = undo_correction(new_payload, record)
    results.append("[4] undo_correction(subj)")
    failures.extend(_assert_eq("undone subj", undone_payload.get("subj"), original_subj))
    failures.extend(_assert_eq("undo_warnings", undo_warnings, []))

    # ------------------------------------------------------------------
    # 5. Apply correction to nested field point_of_contact.email
    # ------------------------------------------------------------------
    poc_record, _ = capture_correction(
        payload,
        field_path="point_of_contact.email",
        corrected_value="jane.doe@example.mil",
        reason="Update POC e-mail.",
    )
    poc_payload, poc_warnings = apply_correction(payload, poc_record)
    results.append("[5] apply_correction(point_of_contact.email)")
    failures.extend(
        _assert_eq(
            "poc email applied",
            poc_payload["point_of_contact"]["email"],
            "jane.doe@example.mil",
        )
    )
    failures.extend(_assert_eq("poc_warnings", poc_warnings, []))
    # Verify original payload unchanged
    failures.extend(_assert_eq("original poc email", payload["point_of_contact"]["email"], original_poc_email))

    # ------------------------------------------------------------------
    # 6. Apply correction to list field body[0]
    # ------------------------------------------------------------------
    body_record, _ = capture_correction(
        payload,
        field_path="body[0]",
        corrected_value="1. This is the corrected first paragraph.",
        reason="Reword opening paragraph.",
    )
    body_payload, body_warnings = apply_correction(payload, body_record)
    results.append("[6] apply_correction(body[0])")
    failures.extend(
        _assert_eq(
            "body[0] applied",
            body_payload["body"][0],
            "1. This is the corrected first paragraph.",
        )
    )
    failures.extend(_assert_eq("body_warnings", body_warnings, []))
    # Verify original payload unchanged
    failures.extend(_assert_eq("original body[0]", payload["body"][0], original_body0))
    # Verify body[1] unchanged
    failures.extend(_assert_eq("original body[1]", payload["body"][1], "2. This is the second paragraph of the body."))

    # ------------------------------------------------------------------
    # 7. Apply multiple corrections in order
    # ------------------------------------------------------------------
    multi1, _ = capture_correction(payload, "subj", "MULTI SUBJ", reason="First correction")
    multi2, _ = capture_correction(payload, "from", "Corrections Officer, Example", reason="Second correction")
    multi_payload, multi_warnings = apply_corrections(payload, [multi1, multi2])
    results.append("[7] apply_corrections(2)")
    failures.extend(_assert_eq("multi subj", multi_payload.get("subj"), "MULTI SUBJ"))
    failures.extend(_assert_eq("multi from", multi_payload.get("from"), "Corrections Officer, Example"))

    # ------------------------------------------------------------------
    # 8. Try invalid list path body[99] and verify warning, no crash
    # ------------------------------------------------------------------
    bad_record, _ = capture_correction(payload, "body[99]", "OOB", reason="Out of bounds")
    bad_payload, bad_warnings = apply_correction(payload, bad_record)
    results.append("[8] invalid list index body[99]")
    failures.extend(_assert_eq("bad body[99] unchanged", bad_payload["body"], payload["body"]))
    has_oob = any("out of range" in w.lower() for w in bad_warnings)
    failures.extend(_assert_eq("bad warning contains 'out of range'", has_oob, True))

    # ------------------------------------------------------------------
    # 9. Capture correction for missing dict path local_notes.review_status
    # ------------------------------------------------------------------
    missing_record, missing_warnings = capture_correction(
        payload,
        field_path="local_notes.review_status",
        corrected_value="approved",
        reason="Mark as reviewed.",
    )
    results.append("[9] missing dict path local_notes.review_status")
    failures.extend(_assert_eq("missing original_value", missing_record.get("original_value"), None))
    failures.extend(_assert_eq("missing corrected_value", missing_record.get("corrected_value"), "approved"))
    has_missing_warn = any("did not resolve" in w.lower() for w in missing_warnings)
    failures.extend(_assert_eq("missing warning present", has_missing_warn, True))

    # ------------------------------------------------------------------
    # 10. Run correction on missing dict path creates nested dict
    # ------------------------------------------------------------------
    miss_payload, miss_warnings = apply_correction(payload, missing_record)
    results.append("[10] missing dict path creation")
    failures.extend(
        _assert_eq(
            "created local_notes.review_status",
            miss_payload.get("local_notes", {}).get("review_status"),
            "approved",
        )
    )
    failures.extend(_assert_eq("miss_warnings", miss_warnings, []))
    # original payload unchanged
    failures.extend(_assert_eq("original still no local_notes", payload.get("local_notes"), None))

    # ------------------------------------------------------------------
    # 11. Run run_cci_audit() before/after and verify schema_version
    # ------------------------------------------------------------------
    results.append("[11] run_cci_audit before/after")
    try:
        from validator_runner import run_cci_audit
    except ImportError:
        failures.extend(_assert_eq("import validator_runner", False, True))
        run_cci_audit = None  # type: ignore

    if run_cci_audit:
        audit1 = run_cci_audit(payload)
        failures.extend(_assert_eq("audit1 schema_version", audit1.get("schema_version"), "CCI_AUDIT_V1"))
        audit2 = run_cci_audit(new_payload)
        failures.extend(_assert_eq("audit2 schema_version", audit2.get("schema_version"), "CCI_AUDIT_V1"))

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print("=" * 72)
    print("CORRECTION MEMORY REGRESSION RUNNER")
    print("=" * 72)
    for r in results:
        print(r)
    print()
    for f in failures:
        print(f)
    print()
    error_count = sum(1 for f in failures if f.startswith("FAIL"))
    print(f"RESULT: {'PASS' if error_count == 0 else 'FAIL'} ({error_count} failures)")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
