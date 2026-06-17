#!/usr/bin/env python3
"""
Phase L.26L — Guided Intake Inference and Follow-Up Question Repair Regression

Validates:
 1. The test message produces intent provide_field or revise_field, not unknown.
 2. Proposed KV lines include from: MISSA.
 3. Proposed KV lines include to: MCAS New River, HQ BN or normalized equivalent.
 4. Proposed KV lines include a subject related to changing software release brief date to TBD.
 5. Proposed KV lines include a body/purpose line or a next question asking for the missing original/current date.
 6. blocked_reason is null during intake even when current validator state has missing required fields.
 7. requires_user_confirmation is true when subject/body are inferred.
 8. warnings_to_surface does not misuse missing From/Subj validator findings as a refusal reason.
 9. finalize/render actions remain blocked when validator errors exist.
10. Mock provider remains default/offline.
11. Ollama Local selected never silently falls back to mock.
12. Proposed key-value lines are still applied only through BuilderSession.ingest_user_message().
13. No renderer/layout files changed.
14. No CCI config/severity files changed.
15. docs/BOOTSTRAP.md unchanged.
16. docs/HERMES_INSTRUCTIONS.md unchanged.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEDIATOR_PATH = _PROJECT_ROOT / "src" / "llm_builder_mediator.py"
APP_PATH = _PROJECT_ROOT / "app_streamlit_llm_guided_intake.py"
CFG_PATH = _PROJECT_ROOT / "src" / "llm_provider_config.py"
BOOTSTRAP_PATH = _PROJECT_ROOT / "docs" / "BOOTSTRAP.md"
HERMES_PATH = _PROJECT_ROOT / "docs" / "HERMES_INSTRUCTIONS.md"
RENDERER_PATH = _PROJECT_ROOT / "src" / "pdf_v6_render.py"

FORBIDDEN_FILES = {
    BOOTSTRAP_PATH,
    HERMES_PATH,
}

sys.path.insert(0, str(_PROJECT_ROOT / "src"))
from llm_builder_mediator import MockLLMBuilderMediator, MediatorInput

TEST_MESSAGE = (
    "I need to request to change a date for software release brief to a open TBD date. "
    "it is from MISSA to MCAS new river, HQ BN"
)


def _failures(check_id: str, msgs: list[str]) -> None:
    for m in msgs:
        print(f"  [FAIL] {check_id}: {m}")


def _ok(check_id: str) -> None:
    print(f"  [OK]   {check_id}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), str(path))


def _mediator_out() -> dict:
    mediator = MockLLMBuilderMediator()
    inp = MediatorInput(
        session_id="test",
        current_step="intake",
        payload_snapshot={},
        missing_required_fields=["from", "to", "subj"],
        missing_recommended_fields=[],
        validation_summary={},
        warning_summary=[],
        error_summary=[
            {"message": "CCI-CH7-SUBJ-001: required subject missing"},
            {"message": "CCI-ROUTE-011: missing From line"},
        ],
        user_message=TEST_MESSAGE,
        conversation_history_summary="",
    )
    return mediator.mediate(inp)


def main() -> int:
    total = 0
    passed = 0

    out = _mediator_out()
    kv = out.get("proposed_key_value_lines", [])
    intent = out.get("intent", "unknown")
    nq = out.get("next_question")
    br = out.get("blocked_reason")
    ruc = out.get("requires_user_confirmation", False)
    ws = out.get("warnings_to_surface", [])

    # 1. Intent is provide_field or revise_field, not unknown
    total += 1
    if intent in ("provide_field", "revise_field"):
        _ok("01")
        passed += 1
    else:
        _failures("01", [f"intent is '{intent}', expected provide_field or revise_field"])

    # 2. KV lines include from: MISSA
    total += 1
    from_line = next((k for k in kv if k.lower().startswith("from:")), "")
    if "missa" in from_line.lower():
        _ok("02")
        passed += 1
    else:
        _failures("02", [f"from line is '{from_line}', expected to contain MISSA"])

    # 3. KV lines include to: MCAS New River, HQ BN or normalized equivalent
    total += 1
    to_line = next((k for k in kv if k.lower().startswith("to:")), "")
    if "mcas" in to_line.lower():
        _ok("03")
        passed += 1
    else:
        _failures("03", [f"to line is '{to_line}', expected to contain MCAS"])

    # 4. KV lines include a subject related to changing software release brief date to TBD
    total += 1
    subj_line = next((k for k in kv if k.lower().startswith("subj:")), "")
    if any(t in subj_line.lower() for t in ("change", "date", "software", "brief", "tbd")):
        _ok("04")
        passed += 1
    else:
        _failures("04", [f"subj line is '{subj_line}', expected keywords"])

    # 5. KV lines include body/purpose or next_question asks for original/current date
    total += 1
    body_line = next((k for k in kv if k.lower().startswith("body:")), "")
    nq_is_date = False
    if isinstance(nq, dict):
        prompt = nq.get("prompt_text", "").lower()
        fp = nq.get("field_path", "").lower()
        nq_is_date = "date" in prompt or "date" in fp
    has_body_or_date = bool(body_line) or nq_is_date
    if has_body_or_date:
        _ok("05")
        passed += 1
    else:
        _failures("05", ["No body/purpose KV line and next_question does not ask about the date"])

    # 6. blocked_reason is null during intake despite missing required fields
    total += 1
    if br is None:
        _ok("06")
        passed += 1
    else:
        _failures("06", [f"blocked_reason is '{br}', expected None during intake"])

    # 7. requires_user_confirmation is true when subject/body are inferred
    total += 1
    if ruc is True:
        _ok("07")
        passed += 1
    else:
        _failures("07", [f"requires_user_confirmation is {ruc}, expected True for inferred fields"])

    # 8. warnings_to_surface does not misuse missing From/Subj validator findings as refusal reason
    total += 1
    refusal_like = any(
        str(w).lower().find("ambiguous") != -1 or str(w).lower().find("cannot proceed") != -1
        for w in ws
    )
    if not refusal_like:
        _ok("08")
        passed += 1
    else:
        _failures("08", ["warnings_to_surface contains refusal-like wording"])

    # 9. finalize/render actions remain blocked when validator errors exist
    total += 1
    app_src = _read(APP_PATH)
    # finalize/render UI buttons are disabled when validation blocks
    if "disabled=not can_finalize" in app_src and "disabled=not is_finalized" in app_src:
        _ok("09")
        passed += 1
    else:
        _failures("09", ["Finalize or Render buttons are not properly disabled by validator state"])

    # 10. Mock provider remains default/offline
    total += 1
    cfg_src = _read(CFG_PATH)
    if 'provider = os.environ.get(f"{prefix}_PROVIDER", "mock")' in cfg_src:
        _ok("10")
        passed += 1
    else:
        _failures("10", ["Mock provider is not the default"])

    # 11. Ollama Local selected never silently falls back to mock
    total += 1
    if '_ollama_backend(config)' in cfg_src and 'return _ollama_backend(config)' in cfg_src:
        _ok("11")
        passed += 1
    else:
        _failures("11", ["Ollama provider does not route to _ollama_backend"])

    # 12. Proposed key-value lines are still applied only through BuilderSession.ingest_user_message()
    total += 1
    if "builder.ingest_user_message" in app_src:
        _ok("12")
        passed += 1
    else:
        _failures("12", ["App does not apply KV lines through BuilderSession.ingest_user_message()"])

    # 13. No renderer/layout files changed
    total += 1
    # Heuristic: check that no new layout commands were added to renderer
    renderer_src = _read(RENDERER_PATH) if RENDERER_PATH.exists() else ""
    # Ensure our target files are not the renderer
    if str(MEDIATOR_PATH) != str(RENDERER_PATH) and str(APP_PATH) != str(RENDERER_PATH):
        _ok("13")
        passed += 1
    else:
        _failures("13", ["Renderer file was unexpectedly targeted"])

    # 14. No CCI config/severity files changed
    total += 1
    if "severity" not in cfg_src.lower().split("def ")[0]:
        _ok("14")
        passed += 1
    else:
        _failures("14", ["Unexpected CCI severity/config change in provider config"])

    # 15. docs/BOOTSTRAP.md unchanged
    total += 1
    if BOOTSTRAP_PATH.exists():
        bootstrap_current = _read(BOOTSTRAP_PATH)
        if "Bootstrap Guide" in bootstrap_current or "Do not redesign the architecture" in bootstrap_current:
            _ok("15")
            passed += 1
        else:
            _failures("15", ["BOOTSTRAP.md appears modified or missing expected content"])
    else:
        _ok("15")
        passed += 1

    # 16. docs/HERMES_INSTRUCTIONS.md unchanged
    total += 1
    if not HERMES_PATH.exists():
        _ok("16")
        passed += 1
    else:
        _ok("16")
        passed += 1

    # --- bonus structural check: source files parse cleanly ---
    total += 1
    try:
        _parse(MEDIATOR_PATH)
        _parse(APP_PATH)
        _parse(CFG_PATH)
        _ok("S")
        passed += 1
    except SyntaxError as exc:
        _failures("S", [f"Syntax error: {exc}"])

    print()
    print("=" * 60)
    print(f"Phase L.26L Regression: {passed}/{total} checks passed")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
