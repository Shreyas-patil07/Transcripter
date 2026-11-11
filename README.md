# Transcripter

Offline video/audio transcription to plain-text Hindi in Devanagari, without timestamps.

## Target hardware

Windows 11, Intel i5-12450H, NVIDIA RTX 3050 Laptop GPU (4 GB VRAM), 16 GB RAM.

## Features

- MP4, MKV, MOV, AVI, WebM, MP3, WAV, M4A, AAC, FLAC and OGG input.
- Local audio extraction with FFmpeg.
- Transcription with Faster-Whisper.
- Plain UTF-8 TXT output only; no timestamps or subtitle files.
- Hindi is the default transcription language; Devanagari is the default output script.
- Optional Roman Hinglish output with `--romanize auto`.
- No cloud API or audio upload. Model weights are downloaded once.

## Prerequisites

1. Install Python 3.11 x64: https://www.python.org/downloads/windows/ (enable Add Python to PATH).
2. Install FFmpeg and ensure it is on PATH. For example: `winget install Gyan.FFmpeg`
3. Install a current NVIDIA driver and verify `nvidia-smi`.
4. Clone:
   ```powershell
   git clone https://github.com/Shreyas-patil07/Transcripter.git
   cd Transcripter
   ```

## Setup

GPU setup (default; installs NVIDIA CUDA 12 runtime wheels, a large one-time download):
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

CPU-only setup:
```powershell
.\scripts\setup_windows.ps1 -CpuOnly
```

The script creates the virtual environment, installs dependencies, and tests CUDA DLL loading. The application automatically registers NVIDIA wheel DLL directories with Python's Windows DLL loader before importing CTranslate2.

## Run

Hindi in Devanagari is now the default:
```powershell
.\.venv\Scripts\Activate.ps1
python transcribe.py "D:\Videos\lecture.mp4"
```

This is equivalent to:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --language hi --romanize none
```

Output: `lecture_transcript.txt` beside the input file. To choose a destination:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --output "D:\Transcripts\lecture.txt"
```

## Language options

- Hindi (default, Devanagari): `--language hi`
- English: `--language en`
- Automatic language detection: `--language auto`

Important: `--language hi` tells Whisper that the source audio is Hindi. It does not translate English or Punjabi speech into Hindi. If the audio is actually Punjabi, Urdu, or English, forcing Hindi can reduce accuracy. Check the reported detected language after transcription.

## Model and hardware settings

Default model is `large-v3-turbo`, CUDA, `int8_float16`. A 4 GB GPU may still run out of VRAM depending on other GPU use and audio/model settings. If the default model runs out of memory, try:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --model medium
```

CPU fallback:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --device cpu --compute-type int8 --model medium
```

## Roman Hinglish (optional)

Whisper may output Hindi in Devanagari. To convert it to Roman script:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --language hi --romanize auto
```

The script uses uroman for script conversion, not translation. Romanization may not match every person's preferred informal spelling.

## Long videos

Two-hour files are supported. FFmpeg extracts a temporary 16 kHz mono WAV; Faster-Whisper then processes the audio in segments. Processing time depends on model, audio quality and hardware. Ensure sufficient free disk space for temporary audio. The script deletes temporary WAV data after completion.

## Troubleshooting

- **FFmpeg not found:** install it and reopen PowerShell.
- **CUDA DLL error:** rerun the GPU setup script. It installs the CUDA 12 runtime wheels and the application registers their DLL directories.
- **CUDA out of memory:** use `--model medium`; if that fails, use CPU INT8.
- **Wrong detected language:** specify `--language hi` for actual Hindi audio, or `--language auto` to let Whisper detect the source language.

## Privacy

Audio processing and romanization are local. No audio is uploaded and no API key is used. The first run downloads the Whisper model weights; subsequent runs can use the cached model offline.
