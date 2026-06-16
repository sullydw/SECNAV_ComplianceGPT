# SECNAV Compliant Letter Builder — Ollama Streamlit Launcher
# Phase L.26D — One-click launch with Ollama provider

Write-Host "=============================================="
Write-Host " SECNAV Compliant Letter Builder"
Write-Host " Ollama Streamlit Launcher"
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
Write-Host "[OK] Streamlit found."

# Check Ollama reachability
Write-Host "[CHECK] Verifying Ollama is running at localhost:11434..."
$ollamaReachable = $false
try {
    $null = & $PYTHON_EXE -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5).close(); print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ollamaReachable = $true
    }
} catch {
    $ollamaReachable = $false
}

if (-not $ollamaReachable) {
    Write-Host ""
    Write-Host "[ERROR] Ollama does not appear to be running."
    Write-Host ""
    Write-Host "Start Ollama first:"
    Write-Host "    ollama serve"
    Write-Host ""
    Write-Host "Or pull a model if needed:"
    Write-Host "    ollama pull llama3.2"
    Write-Host ""
    Write-Host "Then run this launcher again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Ollama is reachable."

# Set Ollama environment variables
$env:SECNAV_LLM_PROVIDER = "ollama"
$env:SECNAV_OLLAMA_MODEL = "llama3.2"

Write-Host ""
Write-Host "Provider mode: Ollama"
Write-Host "Model: llama3.2"
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
