#!/usr/bin/env python3
"""
Phase L.26B — Streamlit Debug Panel Regression

Verifies the behind-the-scenes debug panel added to the Streamlit app.
Ensures users can see mediator output, validator state, and block reasons.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
L24_RUNNER = REPO_ROOT / "tools" / "run_phase_l24_streamlit_usability_regression.py"

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. App file exists
# ------------------------------------------------------------------
checks.append(("A. App file exists", APP_FILE.exists()))

# ------------------------------------------------------------------
# 2. Debug panel label present
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_debug_label = "🐛 Debug" in app_text or "Debug" in app_text
    checks.append(("B. Debug panel label present", has_debug_label))
else:
    checks.append(("B. Debug panel label present", False))

# ------------------------------------------------------------------
# 3. Last mediator output stored in session state
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    stores_output = "last_mediator_output" in app_text
    checks.append(("C. Stores last_mediator_output", stores_output))
else:
    checks.append(("C. Stores last_mediator_output", False))

# ------------------------------------------------------------------
# 4. KV lines visible in debug panel
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_kv_section = "Proposed KV Lines" in app_text
    checks.append(("D. KV lines section in debug panel", has_kv_section))
else:
    checks.append(("D. KV lines section in debug panel", False))

# ------------------------------------------------------------------
# 5. Validator state visible in debug panel
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_val_section = "Validator State" in app_text
    checks.append(("E. Validator state in debug panel", has_val_section))
else:
    checks.append(("E. Validator state in debug panel", False))

# ------------------------------------------------------------------
# 6. Block reason visible in debug panel
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_block_section = "Block Reason" in app_text
    checks.append(("F. Block reason in debug panel", has_block_section))
else:
    checks.append(("F. Block reason in debug panel", False))

# ------------------------------------------------------------------
# 7. Warnings/errors visible in debug panel
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    has_warn_section = "Warnings / Errors" in app_text
    checks.append(("G. Warnings/errors in debug panel", has_warn_section))
else:
    checks.append(("G. Warnings/errors in debug panel", False))

# ------------------------------------------------------------------
# 8. Debug panel is collapsed by default
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    collapsed = "expanded=False" in app_text
    checks.append(("H. Debug panel collapsed by default", collapsed))
else:
    checks.append(("H. Debug panel collapsed by default", False))

# ------------------------------------------------------------------
# 9. L.24 regression still passes
# ------------------------------------------------------------------
if L24_RUNNER.exists():
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(L24_RUNNER)],
            capture_output=True,
            text=True,
            timeout=30
        )
        l24_passed = "ALL CHECKS PASS" in result.stdout
        checks.append(("I. L.24 regression still passes", l24_passed))
        if not l24_passed:
            print(f"  L.24 output: {result.stdout}")
    except Exception as e:
        checks.append(("I. L.24 regression still passes", False))
        print(f"  L.24 error: {e}")
else:
    checks.append(("I. L.24 regression still passes", False))

# ------------------------------------------------------------------
# 10. No direct payload mutation from mediator output
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    no_mutation = "builder.build_payload()[" not in app_text and "payload[" not in app_text.replace("payload_snapshot", "")
    checks.append(("J. No direct payload mutation", no_mutation))
else:
    checks.append(("J. No direct payload mutation", False))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.26B — Streamlit Debug Panel Regression")
print("=" * 64)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
for label, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
print(f"\n{'=' * 64}")
print(f"Total: {passed}/{total} passed")
if passed == total:
    print("ALL CHECKS PASS")
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
print("=" * 64)
