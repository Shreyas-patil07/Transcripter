# Transcripter

Offline video/audio transcription to plain-text Roman Hinglish (no timestamps).

## Target hardware

Windows 11, Intel i5-12450H, NVIDIA RTX 3050 Laptop GPU (4 GB VRAM), 16 GB RAM.

## Features

- MP4, MKV, MOV, AVI, WebM, MP3, WAV, M4A, AAC, FLAC and OGG input.
- Local audio extraction with FFmpeg.
- Transcription with Faster-Whisper.
- Plain UTF-8 TXT output only; no timestamps or subtitle files.
- Hindi Devanagari is romanized locally; existing English/Latin words are preserved.
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

The script creates the virtual environment, installs dependencies, and tests CUDA DLL loading. The application automatically registers the NVIDIA wheel DLL directories with Python's Windows DLL loader before importing CTranslate2. You do not need to edit the system PATH or copy DLLs manually.

Manual setup:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-gpu-windows.txt
```

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python transcribe.py "D:\Videos\lecture.mp4"
```

Output: `lecture_transcript.txt` beside the input file. To choose a destination:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --output "D:\Transcripts\lecture.txt"
```

## Model and hardware settings

Default model is `large-v3-turbo`, CUDA, `int8_float16`. A 4 GB GPU may still run out of VRAM depending on other GPU use and audio/model settings. If the default model runs out of memory, try:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --model medium
```

CPU fallback:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --device cpu --compute-type int8 --model medium
```

For mostly Hindi audio, specify Hindi with `--language hi`; for mostly English use `--language en`. Leave language unset for automatic detection. Whisper selects one primary language, so sentence-by-sentence Hindi-English code-switching will not always be recognized perfectly.

## Roman Hinglish output

Whisper may output Hindi in Devanagari. Transcripter uses **uroman** to convert Devanagari text into Latin script while preserving existing ASCII/English words. This is script conversion, not translation. It is lightweight and does not require Fairseq, PyTorch, a separate GPU model, or a cloud API.

Romanization is not guaranteed to match every person's preferred informal spelling. Proper nouns, technical vocabulary, and code-switched phrases may need manual correction.

To retain Whisper's original script instead:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --romanize none
```

## Long videos

Two-hour files are supported. FFmpeg extracts a temporary 16 kHz mono WAV; Faster-Whisper then processes the audio in segments. Processing time depends on model, audio quality and hardware. Ensure sufficient free disk space for temporary audio. The script deletes temporary WAV data after completion.

## Troubleshooting

- **FFmpeg not found:** install it and reopen PowerShell.
- **CUDA DLL error:** rerun the GPU setup script. It installs the CUDA 12 runtime wheels and the application registers their DLL directories.
- **CUDA out of memory:** use `--model medium`; if that fails, use CPU INT8.
- **uroman import error:** activate `.venv` and run `python -m pip install -r requirements.txt`.

## Privacy

Audio processing and romanization are local. No audio is uploaded and no API key is used. The first run downloads the Whisper model weights; subsequent runs can use the cached model offline.
