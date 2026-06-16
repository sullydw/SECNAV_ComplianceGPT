@echo off
REM SECNAV Compliant Letter Builder — Simple Streamlit Launcher
REM Phase L.26 — One-click launch script for Windows
REM Phase L.26H — Auto-installs streamlit and pyperclip if missing

setlocal enabledelayedexpansion

echo ==============================================
echo  SECNAV Compliant Letter Builder
echo  Streamlit Local Launcher
echo ==============================================

REM Determine repo root (directory containing this batch file)
cd /d "%~dp0"

REM Try known project Python path first
set PYTHON_EXE=C:\Users\drryl\pinokio\bin\miniconda\python.exe
if not exist "%PYTHON_EXE%" (
    echo [INFO] Known Python not found at %PYTHON_EXE%
    echo [INFO] Falling back to python...
    set PYTHON_EXE=python
)

REM --- Dependency auto-install helper ------------------------
REM Check and install a package using the selected Python.
REM Args: %1 = package name, %2 = import module name (often same as package)

REM Check streamlit
"%PYTHON_EXE%" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo.
    echo [INSTALL] streamlit is missing. Installing...
    "%PYTHON_EXE%" -m pip install streamlit
    if errorlevel 1 (
        echo [ERROR] Failed to install streamlit.
        echo.
        echo Please run the following command manually:
        echo     "%PYTHON_EXE%" -m pip install streamlit
        echo.
        pause
        exit /b 1
    )
    echo [OK] streamlit installed.
) else (
    echo [OK] streamlit already installed.
)

REM Check pyperclip
"%PYTHON_EXE%" -c "import pyperclip" 2>nul
if errorlevel 1 (
    echo [INSTALL] pyperclip is missing. Installing...
    "%PYTHON_EXE%" -m pip install pyperclip
    if errorlevel 1 (
        echo [ERROR] Failed to install pyperclip.
        echo.
        echo Please run the following command manually:
        echo     "%PYTHON_EXE%" -m pip install pyperclip
        echo.
        pause
        exit /b 1
    )
    echo [OK] pyperclip installed.
) else (
    echo [OK] pyperclip already installed.
)

REM Re-verify both packages are importable
"%PYTHON_EXE%" -c "import streamlit; import pyperclip" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] One or more dependencies failed to import after installation.
    echo.
    echo Please run the following command manually:
    echo     "%PYTHON_EXE%" -m pip install streamlit pyperclip
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies verified. Starting app...
echo.
echo Your browser should open automatically at:
echo     http://localhost:8501
echo.
echo ==============================================

REM Start Streamlit
"%PYTHON_EXE%" -m streamlit run app_streamlit_llm_guided_intake.py

echo.
echo App stopped. Press any key to close this window.
pause
