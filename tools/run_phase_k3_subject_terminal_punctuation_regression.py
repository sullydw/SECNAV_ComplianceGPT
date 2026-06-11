#!/usr/bin/env python3
"""
Phase K.3 CCI-CH7-SUBJ-002 Subject Terminal Punctuation Regression Runner

Dedicated deterministic regression runner for CCI-CH7-SUBJ-002.

Uses the existing validator entry point (validate_cci_subject) with inline
sanitized/synthetic payloads. No external fixture files required.

Safety:
- No config changes.
- No severity changes.
- No allowlist changes.
- No validator changes.
- No catalog changes.
- Sanitized/synthetic payloads only.

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cci_subject_validate import validate_cci_subject


def _has_rule(findings: list[str], rule_id: str) -> bool:
    return any(rule_id in f for f in findings)


def _count_rule(findings: list[str], rule_id: str) -> int:
    return sum(1 for f in findings if rule_id in f)


# -------------------------------------------------------------------------
# Positive payloads (must trigger CCI-CH7-SUBJ-002)
# -------------------------------------------------------------------------

PAYLOAD_PERIOD_END = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE.",
}

PAYLOAD_QUESTION_END = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE?",
}

PAYLOAD_EXCLAMATION_END = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE!",
}

# -------------------------------------------------------------------------
# Negative payloads (must NOT trigger CCI-CH7-SUBJ-002)
# -------------------------------------------------------------------------

PAYLOAD_NO_TERMINAL = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE",
}

PAYLOAD_INTERNAL_PUNCT = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "ABC/123 SYSTEM STATUS REPORT",
}

PAYLOAD_COMMA_END = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE,",
}

PAYLOAD_SEMICOLON_END = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POLICY UPDATE;",
}

PAYLOAD_UPPERCASE_NO_PUNCT = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "STATUS REPORT FOR DEPLOYMENT",
}

PAYLOAD_MIXED_CASE_NO_PUNCT = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "Status Report for Deployment",
}

# -------------------------------------------------------------------------
# Cross-rule payloads
# -------------------------------------------------------------------------

PAYLOAD_BLANK_SUBJECT = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "",
}

PAYLOAD_TERMINAL_PLUS_ACRONYM = {
    "doc_type": "standard_letter",
    "component": "navy",
    "subj": "REQUEST FOR POC UPDATE.",
}


# -------------------------------------------------------------------------

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print("=" * 72)
    print("PHASE K.3 SUBJ-002 TERMINAL PUNCTUATION REGRESSION RUNNER")
    print(f"REPO ROOT: {root}")
    print("=" * 72)
    print()

    results: list[tuple[str, bool]] = []

    # --- Positive cases (3 checks) -----------------------------------------

    # 1. Period at end triggers SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_PERIOD_END)
    ok = _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 01: Period at end triggers SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 01")

    # 2. Question mark at end triggers SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_QUESTION_END)
    ok = _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 02: Question mark at end triggers SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 02")

    # 3. Exclamation at end triggers SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_EXCLAMATION_END)
    ok = _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 03: Exclamation at end triggers SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 03")

    # --- Negative cases (6 checks) -------------------------------------------

    # 4. No terminal punctuation does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_NO_TERMINAL)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 04: No terminal punctuation has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 04")

    # 5. Internal punctuation does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_INTERNAL_PUNCT)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 05: Internal punctuation has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 05")

    # 6. Comma at end does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_COMMA_END)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 06: Comma at end has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 06")

    # 7. Semicolon at end does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_SEMICOLON_END)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 07: Semicolon at end has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 07")

    # 8. Uppercase without terminal punctuation does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_UPPERCASE_NO_PUNCT)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 08: Uppercase no punct has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 08")

    # 9. Mixed case without terminal punctuation does not trigger SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_MIXED_CASE_NO_PUNCT)
    ok = not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 09: Mixed case no punct has no SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 09")

    # --- Cross-rule cases (2 checks) ---------------------------------------

    # 10. Blank subject: SUBJ-001 handles it, no SUBJ-002
    errors, warnings = validate_cci_subject(PAYLOAD_BLANK_SUBJECT)
    ok = _has_rule(errors, "CCI-CH7-SUBJ-001") and not _has_rule(errors, "CCI-CH7-SUBJ-002")
    results.append(("Check 10: Blank subject triggers SUBJ-001 not SUBJ-002", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # 11. Terminal punctuation + prohibited acronym: SUBJ-002 error + SUBJ-007 warning
    errors, warnings = validate_cci_subject(PAYLOAD_TERMINAL_PLUS_ACRONYM)
    ok = (
        _has_rule(errors, "CCI-CH7-SUBJ-002")
        and any("CCI-CH7-SUBJ-007" in w for w in warnings)
    )
    results.append(("Check 11: Terminal punct + acronym preserves SUBJ-002 and SUBJ-007", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 11")

    # Summary
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("PHASE K.3 REGRESSION RESULT: PASS")
        return 0
    else:
        print("PHASE K.3 REGRESSION RESULT: FAIL")
        for name, ok in results:
            if not ok:
                print(f"  FAILED: {name}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
