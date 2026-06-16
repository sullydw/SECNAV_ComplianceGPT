# Phase L.26H Streamlit Launcher Dependency Auto-Install Hotfix

**Status:** Implementation checkpoint
**Date:** 2026-06-16
**Runner:** `tools/run_phase_l26h_streamlit_dependency_autoinstall_regression.py`
**Result:** ALL CHECKS PASS

---

## Root Cause

The Streamlit app crashed at runtime with:

```
ModuleNotFoundError: No module named 'pyperclip'
```

The crash occurred because the example-prompt copy buttons in the Streamlit UI unconditionally imported `pyperclip` inside a button callback on the render path. The user had not installed `pyperclip` manually.

## Changes Made

### 1. App fix (`app_streamlit_llm_guided_intake.py`)

- Removed unconditional `import pyperclip` from the render-path button callback.
- Added guarded top-level import: `try: import pyperclip except ImportError: ...`
- Added `_copy_to_clipboard(text: str) -> tuple[bool, str]` helper.
- If `pyperclip` is missing, the helper returns `(False, "Clipboard not available — copy the text manually.")` and the UI shows a friendly toast instead of crashing.
- No renderer/layout changes; no CCI config/severity changes.

### 2. Launcher dependency auto-install

All four launchers now automatically check and install `streamlit` and `pyperclip` before starting the app:

| Launcher | Auto-install packages |
|----------|----------------------|
| `launch_secnav_streamlit.bat` | streamlit, pyperclip |
| `launch_secnav_streamlit.ps1` | streamlit, pyperclip |
| `launch_secnav_streamlit_ollama.bat` | streamlit, pyperclip |
| `launch_secnav_streamlit_ollama.ps1` | streamlit, pyperclip |

Behavior per launcher:
- Detects the same Python it will use to launch the app (preferred: `C:\Users\drryl\pinokio\bin\miniconda\python.exe`, falls back to `python`).
- Runs `<python> -c "import <package>"` to test importability.
- If missing, runs `<python> -m pip install <package>`.
- Re-checks import after install.
- If install fails, prints the manual command and exits cleanly with code 1.
- Does **not** auto-install Ollama (only checks reachability).
- Does **not** install vendor LLM SDKs (openai, anthropic, etc.).
- Does **not** display or request API keys.

## File Sizes

- `app_streamlit_llm_guided_intake.py`: 23694 bytes
- `launch_secnav_streamlit.bat`: 2724 bytes
- `launch_secnav_streamlit.ps1`: 3363 bytes
- `launch_secnav_streamlit_ollama.bat`: 3260 bytes
- `launch_secnav_streamlit_ollama.ps1`: 4358 bytes
- `tools/run_phase_l26h_streamlit_dependency_autoinstall_regression.py`: 10183 bytes

## Regression Checks (22 total)

- [PASS] A. App file exists
- [PASS] B. No unconditional top-level import pyperclip
- [PASS] C. Guarded pyperclip import present
- [PASS] D. _copy_to_clipboard helper exists
- [PASS] E. Helper returns (bool, str)
- [PASS] F. Friendly manual-copy fallback message
- [PASS] G. No inline pyperclip import in render path
- [PASS] H. No renderer/layout controls introduced
- [PASS] I. No CCI severity/config controls introduced
- [PASS] J. All four launchers exist
- [PASS] K. All launchers check streamlit
- [PASS] L. All launchers check pyperclip
- [PASS] M. All launchers use same Python for pip install
- [PASS] N. Launchers re-check after install
- [PASS] O. Clean exit on install failure with manual command
- [PASS] P. Launchers do NOT auto-install Ollama
- [PASS] Q. No vendor LLM SDK auto-install
- [PASS] R. No API key display in launchers
- [PASS] S. No unexpected live provider env vars in base launchers
- [PASS] T. Ollama launchers set env vars but do not install Ollama
- [PASS] U. App-level no API key display
- [PASS] V. App parses without pyperclip

## Verdict

- Clipboard support is now optional; app no longer crashes when `pyperclip` is missing.
- All four launchers auto-install only `streamlit` and `pyperclip`.
- No Ollama auto-install; no vendor SDK auto-install; no API key exposure.
- No renderer/layout, config/severity, or command-layer changes.
- Recommended next phase: **Phase L.27 Streamlit Launcher Manual Verification**.

**Explicit prohibitions upheld:**
- No rule promotion
- No error promotion
- No CCI config/severity/catalog/validator/renderer/prompt/command changes
- No force-push
