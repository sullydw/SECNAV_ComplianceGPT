#!/usr/bin/env python3
"""
Phase L.27A Retire Streamlit Web UI Path Regression Runner

Verifies that the Streamlit web UI and its Ollama-specific artifacts are
fully removed, that no active source code imports streamlit, and that
core builder/conversational modules remain intact.

Exit 0 only when all expectations are met.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _find_python_sources(root: Path) -> list[Path]:
    """Return all .py files under src/, engine/, examples/, output/ excluding __pycache__."""
    files: list[Path] = []
    for sub in (root / "src", root / "engine", root / "examples", root / "output"):
        if not sub.exists():
            continue
        for p in sub.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    return files


def _scan_for_streamlit_imports(root: Path) -> list[str]:
    offenders: list[str] = []
    for p in _find_python_sources(root):
        try:
            text = p.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "streamlit":
                        offenders.append(str(p.relative_to(root)))
            elif isinstance(node, ast.ImportFrom):
                if node.module == "streamlit":
                    offenders.append(str(p.relative_to(root)))
                elif node.module and node.module.startswith("streamlit."):
                    offenders.append(str(p.relative_to(root)))
    return offenders


def _core_import_smoke(root: Path) -> list[str]:
    """Try importing core modules that must remain functional."""
    errors: list[str] = []
    core_mods = [
        "src.conversational_builder",
        "src.correction_commands",
        "src.pdf_v6_render",
        "src.context_resolver",
        "src.cci_routing_validate",
        "src.cci_subject_validate",
        "src.cci_severity_mapper",
        "src.llm_builder_mediator",
        "src.llm_provider_config",
    ]
    for mod in core_mods:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return errors


def _file_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def main() -> int:
    root = repo_root()
    results: list[tuple[str, bool]] = []

    # 1. Streamlit app file removed
    ok = not _file_exists(root, "app_streamlit_llm_guided_intake.py")
    results.append(("Check 1: app_streamlit_llm_guided_intake.py removed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 1")

    # 2. Streamlit launchers removed
    launchers = [
        "launch_secnav_streamlit.bat",
        "launch_secnav_streamlit.ps1",
        "launch_secnav_streamlit_ollama.bat",
        "launch_secnav_streamlit_ollama.ps1",
    ]
    ok = all(not _file_exists(root, lf) for lf in launchers)
    results.append(("Check 2: Streamlit launchers removed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 2")

    # 3. Streamlit checkpoint files removed
    ck_gone = [
        "docs/checkpoints/phase_l23_streamlit_llm_guided_intake_prototype_checkpoint.md",
        "docs/checkpoints/phase_l24_streamlit_prototype_usability_pass_checkpoint.md",
        "docs/checkpoints/phase_l25_streamlit_guided_intake_manual_demo_script_checkpoint.md",
        "docs/checkpoints/phase_l26_simple_streamlit_local_launcher_checkpoint.md",
        "docs/checkpoints/phase_l26a_streamlit_pending_decisions_hotfix_checkpoint.md",
        "docs/checkpoints/phase_l26b_streamlit_debug_panel_checkpoint.md",
        "docs/checkpoints/phase_l26c_ollama_provider_manual_path_checkpoint.md",
        "docs/checkpoints/phase_l26d_one_click_ollama_streamlit_launcher_checkpoint.md",
        "docs/checkpoints/phase_l26e_ollama_provider_model_picker_checkpoint.md",
        "docs/checkpoints/phase_l26f_ollama_inference_debug_and_provider_state_fix_checkpoint.md",
        "docs/checkpoints/phase_l26g_ollama_timeout_fallback_and_coldstart_checkpoint.md",
        "docs/checkpoints/phase_l26h_streamlit_dependency_autoinstall_checkpoint.md",
        "docs/checkpoints/phase_l26i_ollama_localhost_detection_hotfix_checkpoint.md",
        "docs/checkpoints/phase_l26j_streamlit_ollama_availability_unification_checkpoint.md",
        "docs/checkpoints/phase_l26k_ollama_inference_endpoint_diagnostics_checkpoint.md",
        "docs/checkpoints/phase_l26l_guided_intake_inference_checkpoint.md",
        "docs/checkpoints/phase_l26m_ollama_empty_content_response_checkpoint.md",
        "docs/demo/streamlit_guided_intake_manual_demo_script.md",
    ]
    ok = all(not _file_exists(root, cp) for cp in ck_gone)
    results.append(("Check 3: Streamlit/Ollama checkpoint docs removed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 3")

    # 4. Streamlit/Ollama regression runners removed
    runners_gone = [
        "tools/run_phase_l23_streamlit_intake_import_smoke.py",
        "tools/run_phase_l24_streamlit_usability_regression.py",
        "tools/run_phase_l25_streamlit_manual_demo_script_regression.py",
        "tools/run_phase_l26_streamlit_launcher_regression.py",
        "tools/run_phase_l26a_streamlit_pending_decisions_hotfix_regression.py",
        "tools/run_phase_l26b_streamlit_debug_panel_regression.py",
        "tools/run_phase_l26c_ollama_provider_manual_path_regression.py",
        "tools/run_phase_l26d_ollama_launcher_regression.py",
        "tools/run_phase_l26e_ollama_model_picker_regression.py",
        "tools/run_phase_l26f_ollama_inference_debug_and_provider_state_fix_regression.py",
        "tools/run_phase_l26g_ollama_timeout_fallback_and_coldstart_regression.py",
        "tools/run_phase_l26h_streamlit_dependency_autoinstall_regression.py",
        "tools/run_phase_l26i_ollama_localhost_detection_regression.py",
        "tools/run_phase_l26j_streamlit_ollama_availability_unification_regression.py",
        "tools/run_phase_l26k_ollama_inference_endpoint_diagnostics_regression.py",
        "tools/run_phase_l26l_guided_intake_inference_regression.py",
        "tools/run_phase_l26m_ollama_empty_content_response_regression.py",
    ]
    ok = all(not _file_exists(root, rp) for rp in runners_gone)
    results.append(("Check 4: Streamlit/Ollama regression runners removed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 4")

    # 5. No active source code imports streamlit
    offenders = _scan_for_streamlit_imports(root)
    ok = len(offenders) == 0
    if not ok:
        print(f"  Offenders: {offenders}")
    results.append(("Check 5: no active source code imports streamlit", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 5")

    # 6. Core builder/provider modules still importable
    import_errs = []
    core_mods = [
        "conversational_builder",
        "correction_commands",
        "cci_routing_validate",
        "cci_subject_validate",
        "cci_severity_mapper",
        "llm_builder_mediator",
        "llm_provider_config",
    ]
    sys.path.insert(0, str(root / "src"))
    for mod in core_mods:
        try:
            __import__(mod)
        except Exception as exc:
            import_errs.append(f"{mod}: {exc}")
    ok = len(import_errs) == 0
    if not ok:
        for e in import_errs:
            print(f"  {e}")
    results.append(("Check 6: core builder/provider imports pass", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 6")

    # 7. Renderer/layout files unchanged
    forbidden_changed = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        cwd=str(root),
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    forbidden = [
        "src/pdf_v6_render.py",
        "src/context_resolver.py",
        "src/correction_commands.py",
        "src/correction_nl_commands.py",
        "rules_v6/CCI/cci_ch2_routing_rules.json",
        "rules_v6/CCI/cci_ch7_subject_rules.json",
        "rules_v6/CCI/cci_ch8_reference_rules.json",
        "rules_v6/CCI/cci_ch9_enclosure_rules.json",
        "rules_v6/CCI/cci_ch10_body_rules.json",
    ]
    touched = [f for f in forbidden if f in forbidden_changed]
    ok = len(touched) == 0
    if not ok:
        print(f"  Touched forbidden files: {touched}")
    results.append(("Check 7: no renderer/layout/CCI/config files changed", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 7")

    # 8. docs/BOOTSTRAP.md unchanged
    bootstrap = root / "docs" / "BOOTSTRAP.md"
    if bootstrap.exists():
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", str(bootstrap)],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        ok = diff.stdout.strip() == ""
    else:
        ok = True  # doesn't exist is also acceptable if not tracked
    results.append(("Check 8: docs/BOOTSTRAP.md unchanged", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 8")

    # 9. docs/HERMES_INSTRUCTIONS.md unchanged
    hermes = root / "docs" / "HERMES_INSTRUCTIONS.md"
    if hermes.exists():
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", str(hermes)],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        ok = diff.stdout.strip() == ""
    else:
        ok = True
    results.append(("Check 9: docs/HERMES_INSTRUCTIONS.md unchanged", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 9")

    # 10. Project status acknowledges retirement
    status_text = (root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    ok = "Streamlit UI path is retired" in status_text
    results.append(("Check 10: PROJECT_STATUS.md states Streamlit UI retired", ok))
    print(f"{'PASS' if ok else 'FAIL'} — Check 10")

    # Summary
    print()
    print(f"Results: {sum(1 for _, ok in results if ok)}/{len(results)} PASS")
    if all(ok for _, ok in results):
        print("All checks PASS.")
        return 0
    else:
        print("Some checks FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
