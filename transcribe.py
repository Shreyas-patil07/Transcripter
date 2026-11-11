from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

# Windows Python 3.8+ does not reliably resolve dependent DLLs from PATH.
# Register NVIDIA wheel DLL directories before importing CTranslate2/Faster-Whisper.
_WINDOWS_DLL_HANDLES = []
if os.name == "nt":
    nvidia_root = Path(sysconfig.get_paths()["platlib"]) / "nvidia"
    for package in ("cublas", "cuda_runtime", "cuda_nvrtc", "cudnn"):
        dll_dir = nvidia_root / package / "bin"
        if dll_dir.is_dir():
            _WINDOWS_DLL_HANDLES.append(os.add_dll_directory(str(dll_dir)))

from faster_whisper import WhisperModel

EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local video/audio to plain Roman Hinglish TXT without timestamps."
    )
    parser.add_argument("input", type=Path, help="Input video/audio file")
    parser.add_argument("-o", "--output", type=Path, help="Output TXT path")
    parser.add_argument(
        "--model",
        default="large-v3-turbo",
        choices=["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"],
    )
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--compute-type", default=None)
    parser.add_argument("--language", default=None, help="Optional language code such as hi or en")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--romanize", choices=["auto", "none"], default="auto")
    return parser.parse_args()


def extract_audio(source: Path, destination: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is missing from PATH. Install it and reopen PowerShell.")

    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(destination),
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(f"FFmpeg extraction failed:\\n{process.stderr.strip()}")


def romanize_hindi(text: str) -> str:
    """Romanize Devanagari Hindi while leaving existing Latin/English text unchanged."""
    if not re.search(r"[\\u0900-\\u097F]", text):
        return text

    try:
        import uroman
    except ImportError as exc:
        raise RuntimeError(
            "uroman is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    romanizer = uroman.Uroman()
    return romanizer.romanize_string(text, lcode="hin")


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()

    if not source.is_file():
        print(f"Input file does not exist: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() not in EXTENSIONS:
        print(f"Unsupported input extension: {source.suffix}", file=sys.stderr)
        return 2

    output = (args.output or source.with_name(f"{source.stem}_transcript.txt")).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    compute_type = args.compute_type or ("int8_float16" if args.device == "cuda" else "int8")

    try:
        with tempfile.TemporaryDirectory(prefix="transcripter_") as temp_dir:
            audio_path = Path(temp_dir) / "audio_16khz_mono.wav"
            print("Extracting audio...")
            extract_audio(source, audio_path)

            print(f"Loading {args.model} on {args.device} ({compute_type})...")
            model = WhisperModel(args.model, device=args.device, compute_type=compute_type)

            print("Transcribing. Model weights download on first run...")
            segments, info = model.transcribe(
                str(audio_path),
                language=args.language,
                beam_size=args.beam_size,
                vad_filter=True,
                condition_on_previous_text=True,
            )

            # Iterating over segments performs the actual transcription.
            transcript_parts = [segment.text.strip() for segment in segments if segment.text.strip()]
            transcript = re.sub(r"\\s+", " ", " ".join(transcript_parts)).strip()

            if args.romanize == "auto":
                transcript = romanize_hindi(transcript)

            output.write_text(transcript + "\\n", encoding="utf-8")
            print(f"Detected language: {info.language} ({info.language_probability:.0%})")
            print(f"Saved plain TXT without timestamps: {output}")

        return 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
