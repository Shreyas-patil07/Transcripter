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
2. Install FFmpeg and ensure it is on PATH. For example:
   ```powershell
   winget install Gyan.FFmpeg
   ```
   Reopen PowerShell and verify `ffmpeg -version`.
3. Install a current NVIDIA driver and verify `nvidia-smi`.
4. Clone:
   ```powershell
   git clone https://github.com/Shreyas-patil07/Transcripter.git
   cd Transcripter
   ```

## Setup

Run:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

Or set up manually:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
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

Default model is `large-v3-turbo`, CUDA, `int8_float16`, batch size 1. A 4 GB GPU may still run out of VRAM depending on runtime libraries and other GPU use. If loading the default model runs out of memory, try:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --model medium --batch-size 1
```

CPU fallback:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --device cpu --compute-type int8 --model medium
```

For mostly Hindi audio, specify Hindi:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --language hi
```

For mostly English audio:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --language en
```

Leave language unset for automatic detection. Whisper's language selection is not perfect for sentence-by-sentence code-switching between Hindi and English. Automatic detection is a sensible starting point for Hinglish.

## Roman Hinglish output

Whisper may output Hindi in Devanagari. Transcripter uses **uroman** to convert Devanagari text into Latin script and leaves existing ASCII/English text intact. This is script conversion, not translation. It is a lightweight romanizer and does not require Fairseq, PyTorch, a separate GPU model, or a cloud API.

Romanization is not guaranteed to match every person's preferred informal spelling (for example, "hai"/"he"). Proper nouns, technical terms, and code-switched phrases may need manual correction.

To retain Whisper's original script instead:
```powershell
python transcribe.py "D:\Videos\lecture.mp4" --romanize none
```

## Long videos

Two-hour files are supported. FFmpeg extracts a temporary 16 kHz mono WAV; Faster-Whisper then processes the audio in segments. Processing time depends on model, audio quality and hardware. Ensure sufficient free disk space for temporary audio. The script deletes temporary WAV data after completion.

## Troubleshooting

- **FFmpeg not found:** install it, add its `bin` folder to PATH and reopen PowerShell.
- **CUDA/cuDNN DLL error:** Faster-Whisper uses CTranslate2 and needs compatible CUDA/cuDNN runtime DLLs. Follow the CTranslate2 installation guidance for the installed version. An NVIDIA display driver alone may not be sufficient.
- **CUDA out of memory:** use `--model medium --batch-size 1`; if that fails, use CPU INT8.
- **uroman import error:** activate `.venv` and run `python -m pip install -r requirements.txt`.

## Privacy

Audio processing and romanization are local. No audio is uploaded and no API key is used. The first run downloads the Whisper model weights; subsequent runs can use the cached model offline.
