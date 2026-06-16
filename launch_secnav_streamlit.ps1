# SECNAV Compliant Letter Builder — Simple Streamlit Launcher
# Phase L.26 — One-click launch script for Windows PowerShell

Write-Host "=============================================="
Write-Host " SECNAV Compliant Letter Builder"
Write-Host " Streamlit Local Launcher"
Write-Host "=============================================="

# Determine repo root (directory containing this script)
$REPO_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $REPO_ROOT

# Try known project Python path first
$PYTHON_EXE = "C:\Users\drryl\pinokio\bin\miniconda\python.exe"
if (-not (Test-Path $PYTHON_EXE)) {
    Write-Host "[INFO] Known Python not found at $PYTHON_EXE"
    Write-Host "[INFO] Falling back to python..."
    $PYTHON_EXE = "python"
}

# Check if Streamlit is installed
Write-Host "[CHECK] Verifying Streamlit is installed..."
$hasStreamlit = $false
try {
    $null = & $PYTHON_EXE -c "import streamlit" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $hasStreamlit = $true
    }
} catch {
    $hasStreamlit = $false
}

if (-not $hasStreamlit) {
    Write-Host ""
    Write-Host "[ERROR] Streamlit is not installed."
    Write-Host ""
    Write-Host "Install it with:"
    Write-Host "    $PYTHON_EXE -m pip install streamlit"
    Write-Host ""
    Write-Host "After installing, run this launcher again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Streamlit found. Starting app..."
Write-Host ""
Write-Host "Your browser should open automatically at:"
Write-Host "    http://localhost:8501"
Write-Host ""
Write-Host "=============================================="

# Start Streamlit
& $PYTHON_EXE -m streamlit run "$REPO_ROOT\app_streamlit_llm_guided_intake.py"

Write-Host ""
Write-Host "App stopped. Press Enter to close this window."
Read-Host
