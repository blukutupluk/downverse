"""Tests for the local faster-whisper transcription backend.

The real dependency is replaced with a small stub before ``transcribe`` is
imported: these tests exercise the CLI contract, not the model itself.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
import wave

BACKEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)


class _Segment:
    def __init__(self, start, end, text, avg_logprob=-0.1, no_speech_prob=0.0):
        self.start = start
        self.end = end
        self.text = text
        self.avg_logprob = avg_logprob
        self.no_speech_prob = no_speech_prob


class _Info:
    language = "id"
    duration = 12.3


class _WhisperModel:
    segments = []
    info = None
    init_calls = []
    transcribe_calls = []

    def __init__(self, model_size_or_path, **kwargs):
        self.model_size_or_path = model_size_or_path
        self.kwargs = kwargs
        type(self).init_calls.append((model_size_or_path, kwargs))

    def transcribe(self, audio, **kwargs):
        type(self).transcribe_calls.append((audio, kwargs))
        return (list(type(self).segments), type(self).info)


_fake_faster_whisper = types.ModuleType("faster_whisper")
_fake_faster_whisper.WhisperModel = _WhisperModel
sys.modules["faster_whisper"] = _fake_faster_whisper

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import transcribe  # noqa: E402  (stub must be installed first)


class TranscribeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

        self.model_dir = os.path.join(self.root, "model")
        os.makedirs(self.model_dir)
        with open(os.path.join(self.model_dir, "model.bin"), "wb") as handle:
            handle.write(b"fake-model")

        self.audio = os.path.join(self.root, "audio.wav")
        with wave.open(self.audio, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 1600)

        self.out_txt = os.path.join(self.root, "out.txt")

        _WhisperModel.segments = []
        _WhisperModel.info = _Info()
        _WhisperModel.init_calls = []
        _WhisperModel.transcribe_calls = []

    def run_cli(self, *extra_args):
        argv = [
            "--audio", self.audio,
            "--out-txt", self.out_txt,
            "--model-dir", self.model_dir,
        ] + list(extra_args)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            returncode = transcribe.main(argv)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(
            len(lines), 1,
            "stdout must contain exactly one JSON line, got: %r" % stdout.getvalue(),
        )
        return returncode, json.loads(lines[0])

    def read_out_txt(self):
        with open(self.out_txt, "r", encoding="utf-8") as handle:
            return handle.read()

    def test_segments_to_txt(self):
        _WhisperModel.segments = [
            _Segment(0.0, 1.0, "halo dunia"),
            _Segment(1.0, 2.5, "ini kedua"),
        ]
        returncode, payload = self.run_cli()

        self.assertEqual(returncode, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["language"], "id")
        self.assertEqual(payload["segments"], 2)
        self.assertGreater(payload["text_chars"], 0)
        self.assertEqual(payload["model"], "base")
        self.assertEqual(
            self.read_out_txt().strip().splitlines(),
            ["halo dunia", "ini kedua"],
        )

    def test_no_speech_no_txt(self):
        _WhisperModel.segments = []
        returncode, payload = self.run_cli()

        self.assertEqual(returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["reason"], "NO_SPEECH")
        self.assertEqual(payload["segments"], 0)
        self.assertEqual(payload["text_chars"], 0)
        self.assertFalse(os.path.exists(self.out_txt))

    def test_low_confidence_marker(self):
        _WhisperModel.segments = [
            _Segment(0.0, 1.0, "halo"),
            _Segment(1.0, 2.0, "RAHASIA", avg_logprob=-2.0),
            _Segment(2.0, 3.0, "Juga Rahasia", no_speech_prob=0.9),
        ]
        returncode, payload = self.run_cli()

        self.assertEqual(returncode, 0)
        self.assertTrue(payload["ok"])
        content = self.read_out_txt()
        self.assertEqual(
            content.strip().splitlines(),
            ["halo", "[tidak terdengar]", "[tidak terdengar]"],
        )
        self.assertNotIn("RAHASIA", content)

    def test_no_translation_and_auto_language(self):
        _WhisperModel.segments = [_Segment(0.0, 1.0, "halo")]
        returncode, payload = self.run_cli()

        self.assertEqual(returncode, 0)
        self.assertTrue(payload["ok"])

        init_path, init_kwargs = _WhisperModel.init_calls[0]
        self.assertEqual(init_path, self.model_dir)
        self.assertTrue(init_kwargs.get("local_files_only"))

        audio, kwargs = _WhisperModel.transcribe_calls[0]
        self.assertGreater(len(audio), 0)
        self.assertEqual(str(audio.dtype), "float32")
        self.assertIsNone(kwargs["language"])
        self.assertEqual(kwargs["task"], "transcribe")
        self.assertTrue(kwargs["vad_filter"])
        self.assertFalse(kwargs["condition_on_previous_text"])

    def test_timestamps_option(self):
        _WhisperModel.segments = [
            _Segment(61.0, 62.0, "halo"),
            _Segment(125.0, 126.0, "dunia"),
        ]
        returncode, payload = self.run_cli("--timestamps")

        self.assertEqual(returncode, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            self.read_out_txt().strip().splitlines(),
            ["[01:01 --> 01:02] halo", "[02:05 --> 02:06] dunia"],
        )


if __name__ == "__main__":
    unittest.main()
