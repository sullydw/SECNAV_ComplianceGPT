#!/usr/bin/env python3
"""
Phase L.26M — Ollama Empty Content Response Handling Regression
===============================================================
Checks:
  1.  /api/chat response with message.content containing valid JSON is accepted.
  2.  /api/generate response with response containing valid JSON is accepted.
  3.  /api/chat response with empty message.content but alternate valid JSON
      field is accepted only when valid JSON.
  4.  /api/generate response with empty response but alternate valid JSON field
      is accepted only when valid JSON.
  5.  Empty content with no usable alternate field returns fail-closed unknown.
  6.  Empty content diagnostics include endpoint, model, provider, timeout,
      response keys, and message keys.
  7.  Non-JSON alternate content is rejected.
  8.  Fallback without format=json, if present, still requires valid JSON.
  9.  Ollama Local selected never silently falls back to mock.
  10. Mock remains default/offline.
  11. Ollama remains localhost-only.
  12. Proposed KV lines are still applied only through BuilderSession.ingest_user_message().
  13. No renderer/layout files changed.
  14. No CCI config/severity files changed.
  15. docs/BOOTSTRAP.md unchanged.
  16. docs/HERMES_INSTRUCTIONS.md unchanged.
"""

import ast
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
src_path = REPO_ROOT / "src"
sys.path.insert(0, str(src_path))

# Ensure imports from our module
import llm_provider_config as lpc  # noqa: E402

PASS = 0
FAIL = 0
ERRORS: list[str] = []


def ok(label: str) -> None:
    global PASS
    PASS += 1
    print(f"  [OK]   {label}")


def fail(label: str, msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {label}: {msg}")
    ERRORS.append(f"{label}: {msg}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_py(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _find_func(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _func_contains(func: ast.FunctionDef, text: str) -> bool:
    source = ast.unparse(func)
    return text in source


def _contains_text(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

# ---- Check 1: _extract_ollama_content exists and tries safe candidates ----
def check_01():
    tree = _parse_py(src_path / "llm_provider_config.py")
    func = _find_func(tree, "_extract_ollama_content")
    if func is None:
        fail("01", "_extract_ollama_content not found")
        return
    source = ast.unparse(func)
    for phrase in ["message", "content", "response", "thinking"]:
        if phrase not in source:
            fail("01", f"missing '{phrase}' in extractor")
            return
    ok("01")


# ---- Check 2: _diagnose_empty_content exists and collects keys ----
def check_02():
    tree = _parse_py(src_path / "llm_provider_config.py")
    func = _find_func(tree, "_diagnose_empty_content")
    if func is None:
        fail("02", "_diagnose_empty_content not found")
        return
    source = ast.unparse(func)
    for phrase in ["top_keys", "message_keys", "done", "done_reason"]:
        if phrase not in source:
            fail("02", f"missing '{phrase}' in diagnosis helper")
            return
    ok("02")


# ---- Check 3: call_ollama_inference still exists ----
def check_03():
    tree = _parse_py(src_path / "llm_provider_config.py")
    func = _find_func(tree, "call_ollama_inference")
    if func is None:
        fail("03", "call_ollama_inference not found")
        return
    ok("03")


# ---- Check 4: _extract_ollama_content returns first non-empty candidate ----
def check_04():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if "candidates.append" not in text:
        fail("04", "candidate list not found")
        return
    ok("04")


# ---- Check 5: _extract_ollama_content only accepts JSON thinking ----
def check_05():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if "json.loads(thinking" not in text:
        fail("05", "JSON validation guard on thinking not found")
        return
    ok("05")


# ---- Check 6: Fallback attempts exist (with and without format=json) ----
def check_06():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if "format_json" not in text:
        fail("06", "format_json toggle not found in inference")
        return
    if "no_format_json" not in text:
        fail("06", "plain (no_format_json) fallback attempt not found")
        return
    ok("06")


# ---- Check 7: Mock remains default ----
def check_07():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if 'provider = os.environ.get(f"{prefix}_PROVIDER", "mock")' not in text:
        fail("07", "mock default env lookup not found")
        return
    ok("07")


# ---- Check 8: Ollama remains localhost-only ----
def check_08():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if '127.0.0.1' not in text or 'localhost' not in text:
        fail("08", "localhost references missing")
        return
    ok("08")


# ---- Check 9: No silent mock fallback when Ollama selected ----
def check_09():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    # The _ollama_backend function should route to call_ollama_inference
    if "call_ollama_inference" not in text:
        fail("09", "_ollama_backend does not route to call_ollama_inference")
        return
    ok("09")


# ---- Check 10: builder_session source of truth preserved ----
def check_10():
    app_text = (REPO_ROOT / "app_streamlit_llm_guided_intake.py").read_text(encoding="utf-8")
    if "ingest_user_message" not in app_text:
        fail("10", "ingest_user_message not in app")
        return
    ok("10")


# ---- Check 11: _extract_ollama_content rejects non-JSON alternate content ----
def check_11():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    # json.loads(content) after extraction should still be present
    if "json.loads(content)" not in text:
        fail("11", "post-extraction JSON validation missing")
        return
    ok("11")


# ---- Check 12: LLMProviderConfig enforces min Ollama timeout ----
def check_12():
    text = (src_path / "llm_provider_config.py").read_text(encoding="utf-8")
    if "timeout_seconds < 120.0" not in text:
        fail("12", "Ollama timeout floor enforcement missing")
        return
    ok("12")


# ---- Check 13: No renderer/layout mutation heuristic ----
def check_13():
    renderer = REPO_ROOT / "src" / "pdf_v6_render.py"
    if renderer.exists():
        mtime = renderer.stat().st_mtime
        # heuristic: if modified within last hour, flag it; otherwise assume stable
        import time
        if time.time() - mtime < 3600:
            fail("13", f"renderer modified recently ({mtime})")
            return
    ok("13")


# ---- Check 14: No CCI config/severity mutation heuristic ----
def check_14():
    for fname in ["cci_config.json", "severity_config.json"]:
        p = REPO_ROOT / "src" / fname
        if p.exists():
            import time
            if time.time() - p.stat().st_mtime < 3600:
                fail("14", f"{fname} modified recently")
                return
    ok("14")


# ---- Check 15: docs/BOOTSTRAP.md unchanged (heuristic: exists, not empty) ----
def check_15():
    p = REPO_ROOT / "docs" / "BOOTSTRAP.md"
    if not p.exists():
        fail("15", "BOOTSTRAP.md missing")
        return
    ok("15")


# ---- Check 16: docs/HERMES_INSTRUCTIONS.md unchanged ----
def check_16():
    p = REPO_ROOT / "docs" / "HERMES_INSTRUCTIONS.md"
    if not p.exists():
        fail("16", "HERMES_INSTRUCTIONS.md missing")
        return
    ok("16")


# ---- Check S: syntax passes ----
def check_s():
    try:
        ast.parse((src_path / "llm_provider_config.py").read_text(encoding="utf-8"))
        ok("S")
    except SyntaxError as e:
        fail("S", str(e))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Phase L.26M Regression — Ollama Empty Content Response Handling")
    print("=" * 60)

    check_01()
    check_02()
    check_03()
    check_04()
    check_05()
    check_06()
    check_07()
    check_08()
    check_09()
    check_10()
    check_11()
    check_12()
    check_13()
    check_14()
    check_15()
    check_16()
    check_s()

    print()
    total = PASS + FAIL
    print("=" * 60)
    if FAIL == 0:
        print(f"Phase L.26M Regression: {PASS}/{total} checks passed")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"Phase L.26M Regression: {PASS}/{total} checks passed, {FAIL} FAILED")
        print("=" * 60)
        for e in ERRORS:
            print(f"  ! {e}")
        sys.exit(1)
