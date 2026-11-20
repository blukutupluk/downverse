#!/usr/bin/env python3
"""Transcribe audio locally with faster-whisper.

This script is copied next to the audio at runtime, so it must work from any
working directory. Models are always loaded from --model-dir; nothing is ever
downloaded here. Exactly one JSON line is written to stdout.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys

MARKER = "[tidak terdengar]"
LOW_CONFIDENCE_LOGPROB = -1.0
HIGH_NO_SPEECH_PROB = 0.6
INSTALL_SCRIPT = "downloader/backend/install_whisper_model.sh"


def _format_time(seconds):
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        total = 0
    return f"{max(total, 0) // 60:02d}:{max(total, 0) % 60:02d}"


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _is_low_confidence(segment):
    """True when a segment is too uncertain to keep its recognized text."""
    try:
        avg_logprob = getattr(segment, "avg_logprob", None)
        no_speech_prob = getattr(segment, "no_speech_prob", None)
        too_quiet = (
            avg_logprob is not None
            and float(avg_logprob) < LOW_CONFIDENCE_LOGPROB
        )
        noisy = (
            no_speech_prob is not None
            and float(no_speech_prob) > HIGH_NO_SPEECH_PROB
        )
    except (TypeError, ValueError):
        return False
    return too_quiet or noisy


def load_model(model_dir, model_size):
    """Load WhisperModel strictly from the local directory.

    Raises a clear error (including the installer path) when model.bin is
    missing; faster-whisper is never allowed to fetch a model at this point.
    """
    if not model_dir:
        raise ValueError(
            f"Model lokal belum ditentukan. Jalankan {INSTALL_SCRIPT} terlebih dahulu."
        )
    if not model_size:
        raise ValueError("model_size harus berupa nama model yang valid.")

    directory = os.path.abspath(os.path.expanduser(str(model_dir)))
    if not os.path.isfile(os.path.join(directory, "model.bin")):
        raise FileNotFoundError(
            f"Model lokal '{model_size}' tidak ditemukan di {directory} "
            f"(model.bin tidak ada). Jalankan {INSTALL_SCRIPT} terlebih dahulu; "
            "proses transkripsi tidak mengunduh model."
        )

    from faster_whisper import WhisperModel

    return WhisperModel(
        directory,
        device="cpu",
        compute_type="int8",
        local_files_only=True,
    )


def _decode_audio(audio):
    """Decode audio into a mono 16 kHz float32 array for faster-whisper.

    faster-whisper's built-in decoder calls av.open(..., metadata_errors=...),
    an argument removed in PyAV 19. Decoding here avoids that version mismatch
    and also avoids invoking ffmpeg at transcription time.
    """
    import av
    import numpy as np

    if isinstance(audio, np.ndarray):
        return audio.astype(np.float32, copy=False).reshape(-1)

    if not isinstance(audio, (str, bytes, os.PathLike)):
        raise TypeError("audio harus berupa path file atau array audio.")
    path = os.path.abspath(os.path.expanduser(os.fsdecode(audio)))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File audio tidak ditemukan: {path}")

    container = av.open(path, mode="r")
    resampler = av.audio.resampler.AudioResampler(
        format="s16", layout="mono", rate=16000
    )
    chunks = []
    try:
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                array = np.asarray(resampled.to_ndarray()).reshape(-1)
                if array.size:
                    chunks.append(array)
        for resampled in resampler.resample(None):
            array = np.asarray(resampled.to_ndarray()).reshape(-1)
            if array.size:
                chunks.append(array)
    finally:
        container.close()

    if not chunks:
        return np.empty(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def render_text(segments, timestamps):
    """Render segments to one line each, in the original order."""
    lines = []
    for segment in segments:
        text = (getattr(segment, "text", "") or "").strip()
        if _is_low_confidence(segment):
            text = MARKER
        if timestamps:
            start = _format_time(getattr(segment, "start", 0.0))
            end = _format_time(getattr(segment, "end", 0.0))
            text = f"[{start} --> {end}] {text}"
        lines.append(text)
    return "\n".join(lines)


def transcribe(audio, model, language, timestamps):
    """Run transcription and return rendered text plus result metadata."""
    stripped = str(language).strip().lower() if language is not None else ""
    language_arg = None if stripped in ("", "auto") else language

    audio_data = _decode_audio(audio)
    segments, info = model.transcribe(
        audio_data,
        language=language_arg,
        task="transcribe",
        vad_filter=True,
        condition_on_previous_text=False,
    )
    segments = list(segments)
    has_speech = any(
        not _is_low_confidence(segment)
        and bool((getattr(segment, "text", "") or "").strip())
        for segment in segments
    )

    return {
        "segments": segments,
        "language": getattr(info, "language", None) or language_arg,
        "duration": _safe_float(getattr(info, "duration", 0.0)),
        "text": render_text(segments, timestamps),
        "has_speech": has_speech,
    }


def _emit(payload):
    print(json.dumps(payload, ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Transcribe audio with a local faster-whisper model."
    )
    parser.add_argument("--audio", required=True, help="Path to the audio file.")
    parser.add_argument("--out-txt", required=True, help="Path of the TXT output.")
    parser.add_argument(
        "--model-dir", required=True, help="Directory containing model.bin."
    )
    parser.add_argument("--model-size", default="base", help="Model name for reports.")
    parser.add_argument(
        "--language", default="auto", help="Language code, or 'auto' for detection."
    )
    parser.add_argument(
        "--timestamps", action="store_true", help="Prefix each line with [mm:ss --> mm:ss]."
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            return 0
        _emit({"ok": False, "reason": "ERROR", "message": "invalid command-line arguments"})
        return 1

    try:
        # Third-party imports/prints must never pollute the JSON stdout line.
        with contextlib.redirect_stdout(sys.stderr):
            model = load_model(args.model_dir, args.model_size)
            result = transcribe(args.audio, model, args.language, args.timestamps)

        language = result["language"]
        duration = result["duration"]
        if not result["has_speech"]:
            _emit({
                "ok": False,
                "reason": "NO_SPEECH",
                "language": language,
                "duration": duration,
                "segments": 0,
                "text_chars": 0,
                "model": args.model_size,
            })
            return 0

        text = result["text"]
        out_path = os.path.abspath(os.path.expanduser(args.out_txt))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")

        _emit({
            "ok": True,
            "language": language,
            "duration": duration,
            "segments": len(result["segments"]),
            "text_chars": len(text),
            "model": args.model_size,
        })
        return 0
    except Exception as exc:
        message = str(exc).strip() or exc.__class__.__name__
        _emit({"ok": False, "reason": "ERROR", "message": message})
        return 1


if __name__ == "__main__":
    sys.exit(main())
