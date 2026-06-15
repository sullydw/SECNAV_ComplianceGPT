#!/usr/bin/env python3
"""
Phase L.25 — Streamlit Manual Demo Script Regression

Verifies the manual demo script document and that the underlying
Streamlit app still meets safety/label requirements.
"""

import ast
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_FILE = REPO_ROOT / "docs" / "demo" / "streamlit_guided_intake_manual_demo_script.md"
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. Demo script document exists
# ------------------------------------------------------------------
checks.append(("A. Demo script document exists", SCRIPT_FILE.exists()))

# ------------------------------------------------------------------
# 2. Launch command present
# ------------------------------------------------------------------
if SCRIPT_FILE.exists():
    text = SCRIPT_FILE.read_text(encoding="utf-8")
    checks.append(("B. Launch command present", "streamlit run app_streamlit_llm_guided_intake.py" in text))
else:
    checks.append(("B. Launch command present", False))

# ------------------------------------------------------------------
# 3. localhost URL present
# ------------------------------------------------------------------
if SCRIPT_FILE.exists():
    checks.append(("C. localhost URL present", "http://localhost:8501" in text))
else:
    checks.append(("C. localhost URL present", False))

# ------------------------------------------------------------------
# 4. All demo scenario fields present
# ------------------------------------------------------------------
scenario_fields = [
    "standard_letter",
    "Commanding Officer, Example Command",
    "Commander, Example Group",
    "Training Plan",
    "5216",
    "This letter provides the proposed training plan",
    "J. Q. Sample",
    "window envelope",
]
if SCRIPT_FILE.exists():
    found = [f for f in scenario_fields if f in text]
    checks.append(("D. Demo scenario fields present", len(found) == len(scenario_fields)))
    if len(found) != len(scenario_fields):
        print(f"  Missing fields: {[f for f in scenario_fields if f not in text]}")
else:
    checks.append(("D. Demo scenario fields present", False))

# ------------------------------------------------------------------
# 5. Step-by-step messages present
# ------------------------------------------------------------------
step_messages = [
    "I need to write a standard letter.",
    "It is from Commanding Officer, Example Command.",
    "Send it to Commander, Example Group.",
    "The subject is Training Plan.",
    "Use SSIC 5216.",
    "The body should say",
    "Signed by J. Q. Sample",
    "No window envelope.",
]
if SCRIPT_FILE.exists():
    found_steps = [s for s in step_messages if s in text]
    checks.append(("E. Step-by-step messages present", len(found_steps) == len(step_messages)))
    if len(found_steps) != len(step_messages):
        print(f"  Missing steps: {[s for s in step_messages if s not in text]}")
else:
    checks.append(("E. Step-by-step messages present", False))

# ------------------------------------------------------------------
# 6. Expected UI observation sections present
# ------------------------------------------------------------------
observation_sections = [
    "Expected observation",
    "Draft Summary",
    "Missing Fields",
    "Validation Panel",
]
if SCRIPT_FILE.exists():
    found_obs = [o for o in observation_sections if o in text]
    checks.append(("F. UI observation sections present", len(found_obs) == len(observation_sections)))
else:
    checks.append(("F. UI observation sections present", False))

# ------------------------------------------------------------------
# 7. Warning/finalize/render/reset/provider sections present
# ------------------------------------------------------------------
behavior_sections = [
    "Warning",
    "Finalize",
    "Render PDF",
    "Reset",
    "Provider",
    "Troubleshooting",
]
if SCRIPT_FILE.exists():
    found_beh = [b for b in behavior_sections if b in text]
    checks.append(("G. Warning/finalize/render/reset/provider sections", len(found_beh) == len(behavior_sections)))
else:
    checks.append(("G. Warning/finalize/render/reset/provider sections", False))

# ------------------------------------------------------------------
# 8. No API key value pattern
# ------------------------------------------------------------------
if SCRIPT_FILE.exists():
    api_leak = "sk-" in text and "[REDACTED]" not in text.split("sk-")[1][:50]
    checks.append(("H. No API key value pattern", not api_leak))
else:
    checks.append(("H. No API key value pattern", False))

# ------------------------------------------------------------------
# 9. No generated PDF/log committed advice
# ------------------------------------------------------------------
if SCRIPT_FILE.exists():
    checks.append(("I. No generated PDF committed advice", "not committed" in text.lower() or "not commit" in text.lower()))
else:
    checks.append(("I. No generated PDF committed advice", False))

# ------------------------------------------------------------------
# 10. Streamlit app still has required UI labels
# ------------------------------------------------------------------
if APP_FILE.exists():
    app_text = APP_FILE.read_text(encoding="utf-8")
    required_labels = [
        "SECNAV Letter Builder",
        "How to use",
        "Conversation",
        "Draft Summary",
        "Missing Fields",
        "Validation",
        "Provider Status",
        "Accept Warnings",
        "Finalize",
        "Render PDF",
    ]
    found_labels = [l for l in required_labels if l in app_text]
    checks.append(("J. App has required UI labels", len(found_labels) == len(required_labels)))
    if len(found_labels) != len(required_labels):
        print(f"  Missing labels: {[l for l in required_labels if l not in app_text]}")
else:
    checks.append(("J. App has required UI labels", False))

# ------------------------------------------------------------------
# 11. App syntax still clean
# ------------------------------------------------------------------
if APP_FILE.exists():
    try:
        ast.parse(app_text)
        checks.append(("K. App syntax parses cleanly", True))
    except SyntaxError as exc:
        checks.append(("K. App syntax parses cleanly", False))
        print(f"  Syntax error: {exc}")
else:
    checks.append(("K. App syntax parses cleanly", False))

# ------------------------------------------------------------------
# 12. App safety terms still present
# ------------------------------------------------------------------
safety_terms = [
    "ingest_user_message",
    "LLMBuilderMediatorAdapter",
    "LLMProviderConfig",
    "validation_summary",
    "finalize_allowed",
    "warning_summary",
]
if APP_FILE.exists():
    found_safety = [t for t in safety_terms if t in app_text]
    checks.append(("L. App safety terms present", len(found_safety) == len(safety_terms)))
else:
    checks.append(("L. App safety terms present", False))

# ------------------------------------------------------------------
# 13. No direct payload mutation in app
# ------------------------------------------------------------------
if APP_FILE.exists():
    unsafe = [p for p in ["payload.update(", "payload[", "build_payload()["] if p in app_text]
    checks.append(("M. No direct payload mutation", len(unsafe) == 0))
else:
    checks.append(("M. No direct payload mutation", False))

# ------------------------------------------------------------------
# 14. Cleanup generated files
# ------------------------------------------------------------------
output_dir = REPO_ROOT / "output"
for ext in ("*.pdf", "*.log", "*.json"):
    for f in output_dir.glob(ext):
        f.unlink()
checks.append(("N. Generated files cleaned up", len(list(output_dir.glob("*.pdf"))) == 0))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.25 — Streamlit Manual Demo Script Regression")
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
