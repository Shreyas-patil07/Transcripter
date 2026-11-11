from __future__ import annotations
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from faster_whisper import WhisperModel

EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

def args_parser():
    p = argparse.ArgumentParser(description="Local transcription to plain Roman Hinglish TXT; no timestamps.")
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--model", default="large-v3-turbo",
                   choices=["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"])
    p.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    p.add_argument("--compute-type", default=None)
    p.add_argument("--language", default=None, help="Optional language code such as hi or en.")
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument("--romanize", choices=["auto", "none"], default="auto")
    return p.parse_args()

def extract_audio(src: Path, dst: Path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg missing from PATH. Install FFmpeg, then reopen PowerShell.")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
           "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError("FFmpeg failed: " + proc.stderr.strip())

def romanize_hindi(text: str) -> str:
    if not re.search(r"[\u0900-\u097F]", text):
        return text
    try:
        from ai4bharat.transliteration import XlitEngine
    except ImportError:
        print("WARNING: IndicXlit unavailable; Devanagari will be left unchanged.", file=sys.stderr)
        return text
    engine = XlitEngine("hi", beam_width=1, src_script_type="indic")
    result = []
    # Transliterate only contiguous Devanagari words; preserve English and punctuation.
    for part in re.split(r"([\u0900-\u097F]+)", text):
        if not part:
            continue
        if re.search(r"[\u0900-\u097F]", part):
            try:
                converted = engine.translit_word(part, topk=1)
                if isinstance(converted, dict):
                    converted = converted.get("hi", [part])
                if isinstance(converted, list):
                    converted = converted[0] if converted else part
                result.append(str(converted))
            except Exception:
                result.append(part)
        else:
            result.append(part)
    return "".join(result)

def main():
    a = args_parser()
    src = a.input.expanduser().resolve()
    if not src.is_file():
        print(f"Input not found: {src}", file=sys.stderr)
        return 2
    if src.suffix.lower() not in EXTENSIONS:
        print(f"Unsupported extension: {src.suffix}", file=sys.stderr)
        return 2
    dst = (a.output or src.with_name(src.stem + "_transcript.txt")).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    compute = a.compute_type or ("int8_float16" if a.device == "cuda" else "int8")
    try:
        with tempfile.TemporaryDirectory(prefix="transcripter_") as tmp:
            wav = Path(tmp) / "audio_16khz_mono.wav"
            print("Extracting audio...")
            extract_audio(src, wav)
            print(f"Loading {a.model} on {a.device} ({compute})...")
            model = WhisperModel(a.model, device=a.device, compute_type=compute)
            print("Transcribing. The first run downloads model weights...")
            segments, info = model.transcribe(str(wav), language=a.language,
                beam_size=a.beam_size, vad_filter=True, condition_on_previous_text=True)
            text_parts = [s.text.strip() for s in segments if s.text.strip()]
            transcript = re.sub(r"\s+", " ", " ".join(text_parts)).strip()
            if a.romanize == "auto":
                transcript = romanize_hindi(transcript)
            dst.write_text(transcript + "\n", encoding="utf-8")
            print(f"Detected language: {info.language} ({info.language_probability:.0%})")
            print(f"Saved plain TXT without timestamps: {dst}")
        return 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
