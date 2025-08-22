# PowerShell helper to run the Streamlit app reliably
# Usage:  ./run_app.ps1  (from repository root)

$script:RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:AppDir = Join-Path $RepoRoot 'ai-keyword-tool'
$venv = Join-Path $AppDir 'venv'
$python = Join-Path $venv 'Scripts/python.exe'

if (-Not (Test-Path $python)) {
    Write-Host '❌ Could not find virtual environment at' $python -ForegroundColor Red
    Write-Host 'Create it first, e.g.: python -m venv ai-keyword-tool/venv; ai-keyword-tool/venv/Scripts/Activate.ps1; pip install -r ai-keyword-tool/requirements.txt'
    exit 1
}

Write-Host '✅ Using virtual environment:' $venv -ForegroundColor Green
Push-Location $AppDir
try {
    & $python -m streamlit run app.py
} finally {
    Pop-Location
}
