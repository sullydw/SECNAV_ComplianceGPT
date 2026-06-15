#!/usr/bin/env python3
"""
Phase L.24 — Streamlit Prototype Usability Regression

Verifies the usability-pass additions in the Streamlit app file:
instructions, example prompts, reset control, transcript/history panel,
provider explanation, improved validation display, raw payload as optional.

Does not require streamlit to be installed at import time.
"""

import ast
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "app_streamlit_llm_guided_intake.py"
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

checks: list[tuple[str, bool]] = []

# ------------------------------------------------------------------
# 1. File exists
# ------------------------------------------------------------------
checks.append(("A. App file exists", APP_FILE.exists()))

# ------------------------------------------------------------------
# 2. Syntax parses cleanly
# ------------------------------------------------------------------
src_text = APP_FILE.read_text(encoding="utf-8")
try:
    tree = ast.parse(src_text)
    checks.append(("B. Syntax parses cleanly", True))
except SyntaxError as exc:
    checks.append(("B. Syntax parses cleanly", False))
    print(f"Syntax error: {exc}")

# ------------------------------------------------------------------
# 3. Usability labels / instructions present
# ------------------------------------------------------------------
usability_labels = [
    "How to use",
    "Welcome",
    "Steps:",
    "Describe your letter",
    "Watch the draft summary",
    "Address any missing fields",
    "Accept warnings",
    "Finalize",
    "Render PDF",
    "Provider:",
]
found_usability = [l for l in usability_labels if l in src_text]
checks.append(("C. Usability instructions present", len(found_usability) == len(usability_labels)))
if len(found_usability) != len(usability_labels):
    missing = [l for l in usability_labels if l not in src_text]
    print(f"  Missing instructions: {missing}")

# ------------------------------------------------------------------
# 4. Example prompts present
# ------------------------------------------------------------------
example_checks = [
    "I need to write a standard letter.",
    "Commanding Officer, Example Command",
    "Commander, Example Group",
    "Training Plan",
    "SSIC 5216",
]
found_examples = [e for e in example_checks if e in src_text]
checks.append(("D. Example prompts present", len(found_examples) == len(example_checks)))
if len(found_examples) != len(example_checks):
    missing = [e for e in example_checks if e not in src_text]
    print(f"  Missing examples: {missing}")

# ------------------------------------------------------------------
# 5. Reset / new-letter control present
# ------------------------------------------------------------------
checks.append(("E. Reset / New Letter control", "New Letter" in src_text and "_reset_session" in src_text))

# ------------------------------------------------------------------
# 6. Transcript / history panel present
# ------------------------------------------------------------------
checks.append(("F. Transcript / history panel", "Conversation History" in src_text))

# ------------------------------------------------------------------
# 7. Provider status explanation present
# ------------------------------------------------------------------
provider_explanations = [
    "mock (default",
    "requires API key",
    "requires local server",
    "API keys are never shown",
]
found_provider = [e for e in provider_explanations if e in src_text]
checks.append(("G. Provider explanations present", len(found_provider) == len(provider_explanations)))
if len(found_provider) != len(provider_explanations):
    missing = [e for e in provider_explanations if e not in src_text]
    print(f"  Missing provider explanations: {missing}")

# ------------------------------------------------------------------
# 8. Raw payload optional / collapsible
# ------------------------------------------------------------------
checks.append(("H. Raw payload collapsible", "expander" in src_text.lower() and "Raw Payload Preview" in src_text))

# ------------------------------------------------------------------
# 9. No direct payload mutation
# ------------------------------------------------------------------
unsafe_patterns = [
    "payload.update(",
    "payload[",
    "build_payload()[",
]
found_unsafe = [p for p in unsafe_patterns if p in src_text]
checks.append(("I. No direct payload mutation", len(found_unsafe) == 0))
if found_unsafe:
    print(f"  Unsafe patterns: {found_unsafe}")

# ------------------------------------------------------------------
# 10. No API key display
# ------------------------------------------------------------------
api_patterns = [
    "print(api_key",
    "print(os.getenv",
    "st.write(config.api_key",
    "st.text(config.api_key",
    "st.markdown(config.api_key",
]
found_api = [p for p in api_patterns if p in src_text.lower()]
checks.append(("J. No API key display", len(found_api) == 0))
if found_api:
    print(f"  API leak patterns: {found_api}")

# ------------------------------------------------------------------
# 11. No renderer/layout controls
# ------------------------------------------------------------------
renderer_controls = [
    "layout_override", "renderer_directive", "font_size", "margin", "page_size"
]
found_renderer = [r for r in renderer_controls if r in src_text.lower()]
checks.append(("K. No renderer layout controls", len(found_renderer) == 0))
if found_renderer:
    print(f"  Renderer controls found: {found_renderer}")

# ------------------------------------------------------------------
# 12. No CCI severity/config controls
# ------------------------------------------------------------------
cci_controls = ["severity_override", "promote_rule", "disable_validator", "cci_config"]
found_cci = [c for c in cci_controls if c in src_text.lower()]
checks.append(("L. No CCI severity/config controls", len(found_cci) == 0))
if found_cci:
    print(f"  CCI controls found: {found_cci}")

# ------------------------------------------------------------------
# 13. Validation display improved (errors/warnings/advisories separated)
# ------------------------------------------------------------------
checks.append(("M. Errors/Warnings/Advisories separated", "Errors" in src_text and "Warnings" in src_text and "Advisories" in src_text))

# ------------------------------------------------------------------
# 14. Button help text present
# ------------------------------------------------------------------
checks.append(("N. Button help text present", "help=" in src_text and "use_container_width" in src_text))

# ------------------------------------------------------------------
# 15. Import with mocked streamlit (guarded import)
# ------------------------------------------------------------------
try:
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
    fake_st.container = lambda *a, **kw: fake_st
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
    fake_st.toast = lambda *a, **kw: None
    fake_st.metric = lambda *a, **kw: None
    fake_st.expander = lambda *a, **kw: fake_st
    fake_st.sidebar = fake_st
    fake_st.__version__ = "0.0.0"
    sys.modules["streamlit"] = fake_st

    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    spec = __import__("importlib.util").util.spec_from_file_location("app_streamlit", str(APP_FILE))
    module = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks.append(("O. Imports cleanly with mocked streamlit", True))
except Exception as exc:
    checks.append(("O. Imports cleanly with mocked streamlit", False))
    print(f"Import error: {exc}")

# ------------------------------------------------------------------
# 16. Cleanup generated files
# ------------------------------------------------------------------
output_dir = REPO_ROOT / "output"
for ext in ("*.pdf", "*.log", "*.json"):
    for f in output_dir.glob(ext):
        f.unlink()
checks.append(("P. Generated files cleaned up", len(list(output_dir.glob("*.pdf"))) == 0))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 64)
print("Phase L.24 — Streamlit Prototype Usability Regression")
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
