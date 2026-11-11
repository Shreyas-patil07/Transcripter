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

# Register NVIDIA wheel DLL folders before importing CTranslate2 on Windows.
_DLL_DIRECTORY_HANDLES = []
if os.name == "nt":
    nvidia_root = Path(sysconfig.get_paths()["platlib"]) / "nvidia"
    for package in ("cublas", "cuda_runtime", "cuda_nvrtc", "cudnn"):
        dll_dir = nvidia_root / package / "bin"
        if dll_dir.is_dir():
            _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(dll_dir)))

from faster_whisper import WhisperModel

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
}
MODEL_CHOICES = ("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local audio/video to a plain-text Hindi transcript."
    )
    parser.add_argument("input", type=Path, help="Input video or audio file")
    parser.add_argument("-o", "--output", type=Path, help="Output TXT path (defaults beside the input)")
    parser.add_argument("--model", choices=MODEL_CHOICES, default="large-v3-turbo")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--compute-type", default=None, help="Defaults to int8_float16 on CUDA or int8 on CPU")
    parser.add_argument(
        "--language",
        default="hi",
        help="Whisper language code (default: hi); use 'auto' for detection",
    )
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument(
        "--romanize",
        choices=("none", "auto"),
        default="none",
        help="Keep Devanagari by default; use 'auto' for Roman-script output",
    )
    return parser.parse_args()


def extract_audio(source: Path, destination: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH. Install FFmpeg and reopen PowerShell.")

    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(destination),
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{process.stderr.strip()}")


def romanize_hindi(text: str) -> str:
    """Convert Devanagari text to Latin script; uroman leaves existing Latin text readable."""
    if not re.search(r"[\u0900-\u097F]", text):
        return text

    try:
        import uroman
    except ImportError as exc:
        raise RuntimeError(
            "uroman is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    return uroman.Uroman().romanize_string(text, lcode="hin")


def format_progress(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()

    if not source.is_file():
        print(f"Input file does not exist: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Unsupported file type: {source.suffix or '(no extension)'}", file=sys.stderr)
        return 2
    if args.beam_size < 1:
        print("--beam-size must be at least 1.", file=sys.stderr)
        return 2

    output = (args.output or source.with_name(f"{source.stem}_transcript.txt")).expanduser().resolve()
    if output.suffix.lower() != ".txt":
        print("Output file must use the .txt extension.", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    compute_type = args.compute_type or ("int8_float16" if args.device == "cuda" else "int8")
    language = None if args.language.strip().lower() == "auto" else args.language.strip().lower()
    temporary_output = output.with_name(output.name + ".tmp")

    try:
        with tempfile.TemporaryDirectory(prefix="transcripter_") as temp_dir:
            audio_path = Path(temp_dir) / "audio_16khz_mono.wav"
            print("Extracting audio...")
            extract_audio(source, audio_path)

            print(f"Loading {args.model} on {args.device} ({compute_type})...")
            model = WhisperModel(args.model, device=args.device, compute_type=compute_type)

            language_label = "automatic detection" if language is None else language
            print(f"Transcribing with language setting: {language_label}...")
            segments, info = model.transcribe(
                str(audio_path),
                language=language,
                beam_size=args.beam_size,
                vad_filter=True,
                condition_on_previous_text=True,
            )

            transcript_parts: list[str] = []
            segment_count = 0

            # Segment positions are shown only as console progress, never written to the transcript.
            for segment in segments:
                segment_text = segment.text.strip()
                if segment_text:
                    transcript_parts.append(segment_text)

                segment_count += 1
                if segment_count % 20 == 0:
                    print(f"Processed audio: {format_progress(segment.end)}")

            transcript = re.sub(r"\s+", " ", " ".join(transcript_parts)).strip()
            if args.romanize == "auto":
                transcript = romanize_hindi(transcript)

            temporary_output.write_text(transcript + "\n", encoding="utf-8")
            temporary_output.replace(output)

            print(f"Whisper language result: {info.language} ({info.language_probability:.0%})")
            print(f"Saved transcript (plain TXT, no timestamps): {output}")

        return 0
    except KeyboardInterrupt:
        print("Interrupted. The final transcript was not replaced.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary_output.exists():
            temporary_output.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
