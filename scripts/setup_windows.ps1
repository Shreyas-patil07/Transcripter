param(
    [switch]$CpuOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== Transcripter Windows setup ==" -ForegroundColor Cyan

py -3.11 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 x64 is required. Install it and enable Add Python to PATH."
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "FFmpeg not found. Install it with: winget install Gyan.FFmpeg"
}
ffmpeg -version | Select-Object -First 1

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi
} elseif (-not $CpuOnly) {
    Write-Warning "nvidia-smi not found. Consider rerunning with -CpuOnly."
}

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

$Python = ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Base dependency installation failed." }

if (-not $CpuOnly) {
    Write-Host "Installing NVIDIA CUDA 12 runtime wheels (large one-time download; cached after install)..." -ForegroundColor Cyan
    & $Python -m pip install -r requirements-gpu-windows.txt
    if ($LASTEXITCODE -ne 0) { throw "NVIDIA runtime installation failed. Rerun with -CpuOnly for CPU mode." }
}

Write-Host ""
Write-Host "Checking Python packages..." -ForegroundColor Cyan
& $Python -c "import faster_whisper, uroman, ctranslate2; print('Faster-Whisper: import OK'); print('uroman: import OK'); print('CTranslate2:', ctranslate2.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Python package import check failed." }

if (-not $CpuOnly) {
    Write-Host ""
    Write-Host "Checking CUDA DLL loading and device access..." -ForegroundColor Cyan
    $CudaCheck = & $Python -c "import os,sysconfig,ctypes; from pathlib import Path; root=Path(sysconfig.get_paths()['platlib'])/'nvidia'; dirs=[root/p/'bin' for p in ('cublas','cuda_runtime','cuda_nvrtc','cudnn')]; handles=[os.add_dll_directory(str(p)) for p in dirs if p.is_dir()]; ctypes.WinDLL(str(root/'cublas'/'bin'/'cublas64_12.dll')); ctypes.WinDLL(str(root/'cudnn'/'bin'/'cudnn64_9.dll')); import ctranslate2; print('CUDA devices:', ctranslate2.get_cuda_device_count()); print('CUDA DLLs loaded successfully')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $CudaCheck -ForegroundColor Green
    } else {
        Write-Warning "CUDA runtime DLL check failed:"
        Write-Warning "$CudaCheck"
        Write-Warning "Check the Visual C++ 2015-2022 x64 runtime, then rerun setup."
        Write-Warning "CPU fallback: .\.venv\Scripts\python.exe .\transcribe.py <file> --device cpu --compute-type int8 --model medium"
    }
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Activate: .\.venv\Scripts\Activate.ps1"
Write-Host 'Run: python transcribe.py "D:\Videos\lecture.mp4"'
