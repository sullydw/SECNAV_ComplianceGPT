# SECNAV Compliant Letter Builder — Ollama Streamlit Launcher
# Phase L.26D — One-click launch with Ollama provider
# Phase L.26H — Auto-installs streamlit and pyperclip if missing
# Phase L.26I — Robust Ollama localhost detection (127.0.0.1 + localhost)

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

# --- Dependency auto-install helper --------------------------
function Test-Import {
    param([string]$module)
    try {
        $null = & $PYTHON_EXE -c "import $module" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Install-Package {
    param([string]$package)
    Write-Host "[INSTALL] $package is missing. Installing..."
    try {
        & $PYTHON_EXE -m pip install $package 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        return $true
    } catch {
        return $false
    }
}

# Check / install streamlit
if (-not (Test-Import "streamlit")) {
    if (-not (Install-Package "streamlit")) {
        Write-Host ""
        Write-Host "[ERROR] Failed to install streamlit."
        Write-Host ""
        Write-Host "Please run the following command manually:"
        Write-Host "    $PYTHON_EXE -m pip install streamlit"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] streamlit installed."
} else {
    Write-Host "[OK] streamlit already installed."
}

# Check / install pyperclip
if (-not (Test-Import "pyperclip")) {
    if (-not (Install-Package "pyperclip")) {
        Write-Host ""
        Write-Host "[ERROR] Failed to install pyperclip."
        Write-Host ""
        Write-Host "Please run the following command manually:"
        Write-Host "    $PYTHON_EXE -m pip install pyperclip"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] pyperclip installed."
} else {
    Write-Host "[OK] pyperclip already installed."
}

# Re-verify both packages
$verify = & $PYTHON_EXE -c "import streamlit; import pyperclip" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] One or more dependencies failed to import after installation."
    Write-Host ""
    Write-Host "Please run the following command manually:"
    Write-Host "    $PYTHON_EXE -m pip install streamlit pyperclip"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Ollama reachability on BOTH 127.0.0.1 and localhost
Write-Host ""
Write-Host "[CHECK] Verifying Ollama is running..."

$ollamaReachable = $false
$ollamaHost = ""
foreach ($hostName in @("127.0.0.1", "localhost")) {
    if ($ollamaReachable) { break }
    Write-Host "  Trying ${hostName}:11434 ..."
    try {
        $null = & $PYTHON_EXE -c "import urllib.request; urllib.request.urlopen('http://${hostName}:11434/api/tags', timeout=5).close(); print('OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Ollama responded on ${hostName}:11434"
            $ollamaReachable = $true
            $ollamaHost = $hostName
        } else {
            Write-Host "  [FAIL] No response on ${hostName}:11434"
        }
    } catch {
        Write-Host "  [FAIL] No response on ${hostName}:11434"
    }
}

if (-not $ollamaReachable) {
    Write-Host ""
    Write-Host "[ERROR] Ollama does not appear to be running on localhost or 127.0.0.1."
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "    1. Start Ollama:"
    Write-Host "       ollama serve"
    Write-Host "    2. Verify it is listening:"
    Write-Host "       curl http://127.0.0.1:11434/api/tags"
    Write-Host "       curl http://localhost:11434/api/tags"
    Write-Host "    3. Pull a model if needed:"
    Write-Host "       ollama pull llama3.2"
    Write-Host "    4. List installed models:"
    Write-Host "       ollama list"
    Write-Host ""
    Write-Host "Then run this launcher again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Ollama is reachable at ${ollamaHost}:11434."

# Set Ollama environment variables
$env:SECNAV_LLM_PROVIDER = "ollama"
$env:SECNAV_OLLAMA_MODEL = "llama3.2"

Write-Host ""
Write-Host "Provider mode: Ollama"
Write-Host "Model: llama3.2"
Write-Host "Endpoint: ${ollamaHost}:11434"
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
