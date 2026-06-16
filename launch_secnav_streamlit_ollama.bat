@echo off
REM SECNAV Compliant Letter Builder — Ollama Streamlit Launcher
REM Phase L.26D — One-click launch with Ollama provider

setlocal enabledelayedexpansion

echo ==============================================
echo  SECNAV Compliant Letter Builder
echo  Ollama Streamlit Launcher
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
echo [OK] Streamlit found.

REM Check Ollama reachability
echo [CHECK] Verifying Ollama is running at localhost:11434...
"%PYTHON_EXE%" -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5).close(); print('OK')" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Ollama does not appear to be running.
    echo.
    echo Start Ollama first:
    echo     ollama serve
    echo.
    echo Or pull a model if needed:
    echo     ollama pull llama3.2
    echo.
    echo Then run this launcher again.
    echo.
    pause
    exit /b 1
)
echo [OK] Ollama is reachable.

REM Set Ollama environment variables
set SECNAV_LLM_PROVIDER=ollama
set SECNAV_OLLAMA_MODEL=llama3.2

echo.
echo Provider mode: Ollama
echo Model: llama3.2
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
