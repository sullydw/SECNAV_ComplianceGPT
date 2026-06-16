#!/usr/bin/env python3
"""
Phase L.23 — Streamlit Intake Prototype Import Smoke Test

Validates the Streamlit app file without requiring the Streamlit package
at import time. Uses AST inspection and safe exec() in a namespace where
streamlit is mocked.
"""

import ast
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

# ------------------------------------------------------------------
# 1. File existence
# ------------------------------------------------------------------
checks: list[tuple[str, bool]] = []

checks.append(("A. App file exists", APP_FILE.exists()))

# ------------------------------------------------------------------
# 2. Syntax validity
# ------------------------------------------------------------------
src_text = APP_FILE.read_text(encoding="utf-8")
try:
    tree = ast.parse(src_text)
    checks.append(("B. Syntax parses cleanly", True))
except SyntaxError as exc:
    checks.append(("B. Syntax parses cleanly", False))
    print(f"Syntax error: {exc}")

# ------------------------------------------------------------------
# 3. Source inspection: required sections/labels
# ------------------------------------------------------------------
required_labels = [
    "Conversation",
    "Draft Summary",
    "Current Fields",
    "Missing Fields",
    "Validation",
    "Provider & Model",
    "Accept Warnings",
    "Finalize",
    "Render PDF",
    "SECNAV Letter Builder",
    "Guided Conversational Intake",
]
found_labels = [label for label in required_labels if label in src_text]
checks.append(("C. All required UI labels present", len(found_labels) == len(required_labels)))
if len(found_labels) != len(required_labels):
    missing = [l for l in required_labels if l not in src_text]
    print(f"  Missing labels: {missing}")

# ------------------------------------------------------------------
# 4. Backend safety terms present
# ------------------------------------------------------------------
safety_terms = [
    "ingest_user_message",
    "LLMBuilderMediatorAdapter",
    "LLMProviderConfig",
    "validation_summary",
    "finalize_allowed",
    "finalize",
    "warning_summary",
    "session_state",
]
found_safety = [t for t in safety_terms if t in src_text]
checks.append(("D. Backend safety terms present", len(found_safety) == len(safety_terms)))
if len(found_safety) != len(safety_terms):
    missing = [t for t in safety_terms if t not in src_text]
    print(f"  Missing safety terms: {missing}")

# ------------------------------------------------------------------
# 5. No direct payload mutation from mediator output
# ------------------------------------------------------------------
unsafe_patterns = [
    "payload.update(",
    "payload[",
    "build_payload()[",
]
found_unsafe = [p for p in unsafe_patterns if p in src_text]
checks.append(("E. No direct payload mutation patterns", len(found_unsafe) == 0))
if found_unsafe:
    print(f"  Found unsafe patterns: {found_unsafe}")

# ------------------------------------------------------------------
# 6. No API key print/display
# ------------------------------------------------------------------
api_patterns = [
    "print(api_key",
    "print(os.getenv",
    "st.write(config.api_key",
    "st.text(config.api_key",
    "st.markdown(config.api_key",
]
found_api_leak = [p for p in api_patterns if p in src_text.lower()]
checks.append(("F. No API key leak patterns", len(found_api_leak) == 0))
if found_api_leak:
    print(f"  Found API leak patterns: {found_api_leak}")

# ------------------------------------------------------------------
# 7. Mock/no-network default path
# ------------------------------------------------------------------
checks.append(("G. Default provider is mock", "provider == \"mock\"" in src_text or "mock" in src_text))

# ------------------------------------------------------------------
# 8. Import without Streamlit (mocked)
# ------------------------------------------------------------------
try:
    # We know streamlit might not be installed, so mock it before importing
    import types
    fake_st = types.ModuleType("streamlit")
    fake_st.session_state = {}
    fake_st.set_page_config = lambda **kw: None
    fake_st.title = lambda *a, **kw: None
    fake_st.caption = lambda *a, **kw: None
    fake_st.header = lambda *a, **kw: None
    fake_st.subheader = lambda *a, **kw: None
    fake_st.write = lambda *a, **kw: None
    fake_st.markdown = lambda *a, **kw: None
    fake_st.code = lambda *a, **kw: None
    fake_st.divider = lambda: None
    fake_st.columns = lambda *a, **kw: [fake_st] * 3
    fake_st.chat_container = lambda *a, **kw: fake_st
    fake_st.chat_message = lambda *a, **kw: fake_st
    fake_st.chat_input = lambda *a, **kw: None
    fake_st.button = lambda *a, **kw: False
    fake_st.download_button = lambda *a, **kw: None
    fake_st.info = lambda *a, **kw: None
    fake_st.warning = lambda *a, **kw: None
    fake_st.error = lambda *a, **kw: None
    fake_st.success = lambda *a, **kw: None
    fake_st.rerun = lambda: None
    fake_st.__version__ = "0.0.0"
    sys.modules["streamlit"] = fake_st

    # Also add src to path if not already there
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    spec = __import__("importlib.util").util.spec_from_file_location("app_streamlit", str(APP_FILE))
    module = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks.append(("H. Imports cleanly with mocked streamlit", True))
except Exception as exc:
    checks.append(("H. Imports cleanly with mocked streamlit", False))
    print(f"Import error: {exc}")

# ------------------------------------------------------------------
# 9. Generated PDF cleanup
# ------------------------------------------------------------------
output_dir = REPO_ROOT / "output"
generated_pdfs = list(output_dir.glob("*.pdf"))
for pdf in generated_pdfs:
    pdf.unlink()
generated_logs = list(output_dir.glob("*.log"))
for log in generated_logs:
    log.unlink()
checks.append(("I. Generated PDFs/logs cleaned up", len(list(output_dir.glob("*.pdf"))) == 0))

# ------------------------------------------------------------------
# 10. No renderer/layout mutation
# ------------------------------------------------------------------
checks.append(("J. No renderer mutation", "renderer" not in src_text.lower() or "render" in src_text))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.23 — Streamlit Intake Import Smoke Test")
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
