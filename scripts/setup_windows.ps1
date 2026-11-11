$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== Transcripter Windows setup ==" -ForegroundColor Cyan
py -3.11 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 x64 is required. Install it and enable Add Python to PATH."
}

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    ffmpeg -version | Select-Object -First 1
} else {
    Write-Warning "FFmpeg not found. Install with: winget install Gyan.FFmpeg"
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi
} else {
    Write-Warning "nvidia-smi not found. CUDA acceleration may not be available."
}

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Activate: .\.venv\Scripts\Activate.ps1"
Write-Host 'Run: python transcribe.py "D:\Videos\lecture.mp4"'
