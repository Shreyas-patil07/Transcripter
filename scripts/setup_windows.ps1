param(
    [switch]$CpuOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== Transcripter setup ==" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher not found. Install Python 3.11 x64 and enable Add Python to PATH."
}

$PythonVersion = & py -3.11 -c "import struct,sys; print(sys.version.split()[0] + (' x64' if struct.calcsize('P') == 8 else ' x86'))"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 was not found. Install Python 3.11 x64."
}
if ($PythonVersion -notmatch "x64$") {
    throw "64-bit Python is required. Detected: $PythonVersion"
}
Write-Host "Python: $PythonVersion" -ForegroundColor Green

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "FFmpeg was not found. Install it with: winget install Gyan.FFmpeg"
}
Write-Host (ffmpeg -version | Select-Object -First 1)

if (-not $CpuOnly) {
    if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
        throw "NVIDIA driver/GPU not detected. Use -CpuOnly for CPU mode."
    }
    nvidia-smi
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
}

$Python = ".venv\Scripts\python.exe"
& $Python -c "import struct,sys; assert sys.version_info[:2] == (3, 11) and struct.calcsize('P') == 8"
if ($LASTEXITCODE -ne 0) {
    throw "The existing .venv is not Python 3.11 x64. Remove .venv and rerun setup."
}

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Base dependency installation failed." }

if (-not $CpuOnly) {
    Write-Host ""
    Write-Host "Installing pinned NVIDIA CUDA 12 runtime wheels. This is a large one-time download." -ForegroundColor Cyan
    & $Python -m pip install -r requirements-gpu-windows.txt
    if ($LASTEXITCODE -ne 0) { throw "NVIDIA runtime installation failed." }

    Write-Host ""
    Write-Host "Validating CUDA DLL loading and GPU access..." -ForegroundColor Cyan
    & $Python .\scripts\check_cuda.py
    if ($LASTEXITCODE -ne 0) {
        throw "CUDA validation failed. Check the NVIDIA driver and Microsoft Visual C++ x64 runtime."
    }
} else {
    Write-Host ""
    Write-Host "CPU-only setup selected. Use --device cpu when transcribing." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Activate: .\.venv\Scripts\Activate.ps1"
if ($CpuOnly) {
    Write-Host 'Run: .\.venv\Scripts\python.exe .\transcribe.py "D:\Videos\lecture.mp4" --device cpu --compute-type int8 --model medium'
} else {
    Write-Host 'Run: .\.venv\Scripts\python.exe .\transcribe.py "D:\Videos\lecture.mp4"'
}
