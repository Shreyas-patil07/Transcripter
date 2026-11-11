# Transcripter

A small local helper for turning long videos and audio files into plain-text transcripts. It uses Faster-Whisper, defaults to Hindi transcription in Devanagari, and does not add timestamps or subtitle formatting.

[![CI](https://github.com/Shreyas-patil07/Transcripter/actions/workflows/ci.yml/badge.svg)](https://github.com/Shreyas-patil07/Transcripter/actions/workflows/ci.yml)

## Features

- Local MP4, MKV, MOV, AVI, WebM, MP3, WAV, M4A, AAC, FLAC and OGG processing.
- Faster-Whisper models, including Large-v3-Turbo.
- Hindi (hi) and Devanagari output by default.
- Optional automatic language detection or another Whisper language code.
- Optional Devanagari-to-Roman transliteration for Roman Hinglish.
- Plain UTF-8 TXT output with no timestamps.
- No audio upload, API key or cloud transcription service.

## Quick start — Windows 10/11

### Requirements

- Python 3.11 x64.
- FFmpeg installed and available on PATH.
- An NVIDIA GPU and current driver for GPU mode. CPU mode is also supported.

Install FFmpeg, for example:

    winget install Gyan.FFmpeg

Close and reopen PowerShell, then verify:

    py -3.11 --version
    ffmpeg -version
    nvidia-smi

### Get the repository

    git clone https://github.com/Shreyas-patil07/Transcripter.git
    cd Transcripter
    Set-ExecutionPolicy -Scope Process Bypass

### GPU setup (recommended when using NVIDIA)

    .\scripts\setup_windows.ps1

The setup script installs the Python dependencies and pinned CUDA 12/cuDNN 9 runtime wheels, then checks that Windows can load the required DLLs and CTranslate2 can see the GPU. The NVIDIA wheel download is large and is needed only once per environment.

### CPU-only setup

    .\scripts\setup_windows.ps1 -CpuOnly

The CPU setup skips NVIDIA packages. Use the CPU command shown at the end of setup.

## Transcribe a file

Hindi in Devanagari is the default:

    .\.venv\Scripts\python.exe .\transcribe.py "D:\Videos\lecture.mp4"

The transcript is saved beside the source file as lecture_transcript.txt.

Choose an output path:

    .\.venv\Scripts\python.exe .\transcribe.py "D:\Videos\lecture.mp4" --output "D:\Transcripts\lecture.txt"

Use a different model:

    # Recommended starting point for supported NVIDIA GPUs
    python transcribe.py "D:\Videos\lecture.mp4" --model large-v3-turbo

    # Lower VRAM requirement
    python transcribe.py "D:\Videos\lecture.mp4" --model medium

Use CPU:

    python transcribe.py "D:\Videos\lecture.mp4" --device cpu --compute-type int8 --model medium

## Language and script options

| Goal | Command option |
|---|---|
| Hindi source audio, Devanagari output (default) | --language hi --romanize none |
| Automatic language detection | --language auto |
| English source audio | --language en |
| Roman Hinglish output | --language hi --romanize auto |

**Transcription is not translation.** Setting --language hi tells Whisper to recognize Hindi speech; it does not translate English or Punjabi speech into Hindi. Hindi-English code-switching, names, poetry, singing, background noise and overlapping speakers can still cause recognition errors. Whisper's reported language and confidence are printed after processing.

## How long videos are handled

The script extracts a temporary 16 kHz mono WAV file with FFmpeg and passes it to Faster-Whisper. Two-hour recordings are supported; processing time depends on the model, audio and hardware. Temporary audio is deleted after the run. Console progress shows processed audio time, but timestamps are never written into the transcript.

Keep enough free disk space for the temporary WAV. A two-hour mono WAV at 16 kHz uses roughly 230 MB.

## Troubleshooting

**FFmpeg not found**

Install FFmpeg, ensure its bin directory is on PATH, then reopen PowerShell.

**CUDA DLL missing or cannot be loaded**

Rerun .\scripts\setup_windows.ps1. The setup installs the CUDA runtime wheels and runs scripts/check_cuda.py. If validation still fails, verify the NVIDIA driver and the Microsoft Visual C++ 2015–2022 x64 Redistributable. Do not download individual DLLs from third-party DLL sites.

**CUDA out of memory**

Close other GPU-heavy applications and retry with --model medium. If GPU inference remains unavailable, use CPU INT8.

**Hugging Face unauthenticated warning**

Public model downloads do not require a token. The warning is about download rate limits, not transcription correctness.

**Poor recognition or unexpected language**

Try --language auto to let Whisper detect the source language. Do not force Hindi for audio that is actually English or Punjabi. Transcription quality is content-dependent; a larger model cannot guarantee correct lyrics or names.

## Development checks

Install the core dependencies, then run:

    python -m compileall -q transcribe.py scripts tests
    python -m unittest discover -s tests -v

The GitHub Actions workflow runs these checks on Windows and Ubuntu.

## Project layout

    Transcripter/
    ├── scripts/
    │   ├── check_cuda.py
    │   └── setup_windows.ps1
    ├── tests/
    │   └── test_transcribe.py
    ├── .github/workflows/ci.yml
    ├── requirements.txt
    ├── requirements-gpu-windows.txt
    └── transcribe.py

## License

MIT. See LICENSE.
