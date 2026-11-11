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
    throw "FFmpeg not found. Install it with: winget install Gyan.FFmpeg"
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi
} else {
    Write-Warning "nvidia-smi not found. CUDA acceleration will not be available."
}

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

$Python = ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

Write-Host ""
Write-Host "Checking Python packages..." -ForegroundColor Cyan
& $Python -c "import faster_whisper, uroman, ctranslate2; print('Faster-Whisper:', faster_whisper.__version__ if hasattr(faster_whisper, '__version__') else 'import OK'); print('uroman: import OK'); print('CTranslate2:', ctranslate2.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Python package import check failed." }

Write-Host ""
Write-Host "Checking CTranslate2 CUDA runtime..." -ForegroundColor Cyan
$CudaCheck = & $Python -c "import ctranslate2; print(sorted(ctranslate2.get_supported_compute_types('cuda')))" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "CUDA compute types: $CudaCheck" -ForegroundColor Green
} else {
    Write-Warning "Python packages installed, but the CTranslate2 CUDA runtime is not ready."
    Write-Warning "$CudaCheck"
    Write-Warning "Install CUDA 12.x and cuDNN 9 for CUDA 12, then reopen PowerShell."
    Write-Warning "CPU mode remains available: python transcribe.py <file> --device cpu --compute-type int8 --model medium"
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Activate: .\.venv\Scripts\Activate.ps1"
Write-Host 'Run: python transcribe.py "D:\Videos\lecture.mp4"'
