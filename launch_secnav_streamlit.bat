@echo off
REM SECNAV Compliant Letter Builder — Simple Streamlit Launcher
REM Phase L.26 — One-click launch script for Windows

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

REM Check if Streamlit is installed
echo [CHECK] Verifying Streamlit is installed...
"%PYTHON_EXE%" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Streamlit is not installed.
    echo.
    echo Install it with:
    echo     %PYTHON_EXE% -m pip install streamlit
    echo.
    echo After installing, run this launcher again.
    echo.
    pause
    exit /b 1
)

echo [OK] Streamlit found. Starting app...
echo.
echo Your browser should open automatically at:
echo     http://localhost:8501
if not exist "http://localhost:8501" (
    REM Browser auto-open is best-effort; show URL regardless
    echo If your browser does not open, visit the URL manually.
)
echo.
echo ==============================================

REM Start Streamlit
"%PYTHON_EXE%" -m streamlit run app_streamlit_llm_guided_intake.py

echo.
echo App stopped. Press any key to close this window.
pause
