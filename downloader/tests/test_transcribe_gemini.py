#!/usr/bin/env python3
"""Unit test backend transkripsi Gemini — tanpa jaringan dan tanpa key asli."""

from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import transcribe_gemini as g  # noqa: E402


class FakeHeaders:
    def __init__(self, values):
        self._values = {str(k).lower(): v for k, v in (values or {}).items()}

    def get(self, name, default=None):
        return self._values.get(str(name).lower(), default)


class FakeResponse:
    def __init__(self, body, status=200, headers=None):
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.status = status
        self.headers = FakeHeaders(headers)

    def read(self):
        return self._body

    def close(self):
        pass


class FakeOpener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def header(request, name):
    return {str(k).lower(): v for k, v in request.headers.items()}.get(name.lower())


class GeminiBackendTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.audio = os.path.join(self.dir, "sample.mp3")
        with open(self.audio, "wb") as handle:
            handle.write(b"ID3\x03fake-audio-bytes")
        self.key = os.path.join(self.dir, "gemini.key")
        with open(self.key, "w", encoding="utf-8") as handle:
            handle.write("  test-key-123  \n")
        self.out = os.path.join(self.dir, "out.txt")
        self.text_payload = {
            "outputs": [{"type": "text", "text": "Halo dunia.\nKedua kalimat."}]
        }

    def opener(self, *responses):
        return FakeOpener(*responses)

    def test_inline_audio_request(self):
        op = self.opener(FakeResponse(self.text_payload))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertTrue(payload["ok"])
        self.assertEqual(len(op.calls), 1)
        request = op.calls[0]
        self.assertIn("/v1beta/interactions", request.full_url)
        self.assertEqual(request.method, "POST")
        body = json.loads(request.data)
        with open(self.audio, "rb") as handle:
            expected = base64.b64encode(handle.read()).decode("ascii")
        self.assertEqual(body["input"][1]["data"], expected)
        self.assertEqual(body["input"][1]["mime_type"], "audio/mp3")
        self.assertEqual(header(request, "x-goog-api-key"), "test-key-123")
        self.assertNotIn("upload", [call.full_url for call in op.calls])

    def test_large_audio_uses_files_api(self):
        with patch.object(g, "INLINE_LIMIT_BYTES", 4):
            op = self.opener(
                FakeResponse({}, headers={"x-goog-upload-url": "https://upload.local/session"}),
                FakeResponse({"file": {"uri": "https://files.local/abc", "name": "files/abc"}}),
                FakeResponse(self.text_payload),
                FakeResponse({}, status=200),
            )
            payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        urls = [call.full_url for call in op.calls]
        self.assertTrue(payload["ok"])
        self.assertIn("/upload/v1beta/files", urls[0])
        self.assertEqual(urls[1], "https://upload.local/session")
        self.assertIn("upload, finalize", header(op.calls[1], "x-goog-upload-command"))
        self.assertEqual(
            json.loads(op.calls[2].data)["input"][1]["uri"],
            "https://files.local/abc",
        )
        self.assertTrue(any(call.method == "DELETE" for call in op.calls))

    def test_success_writes_txt_and_json(self):
        op = self.opener(FakeResponse(self.text_payload))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        with open(self.out, encoding="utf-8") as handle:
            written = handle.read()
        self.assertEqual(written, "Halo dunia.\nKedua kalimat.\n")
        self.assertEqual(payload["segments"], 2)
        self.assertEqual(payload["text_chars"], len(written.rstrip("\n")))
        self.assertEqual(payload["model"], g.MODEL)
        self.assertTrue(payload["ok"])

    def test_no_speech_writes_nothing(self):
        op = self.opener(FakeResponse({"outputs": [{"type": "text", "text": "NO_SPEECH"}]}))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(payload["reason"], "NO_SPEECH")

    def test_empty_or_placeholder_response_rejected(self):
        for text in ("", "[tidak terdengar]"):
            with self.subTest(text=text):
                if os.path.exists(self.out):
                    os.remove(self.out)
                op = self.opener(FakeResponse({"outputs": [{"type": "text", "text": text}]}))
                payload = g.transcribe(self.audio, self.key, self.out, opener=op)
                self.assertFalse(os.path.exists(self.out))
                self.assertEqual(payload["reason"], "BAD_RESPONSE")

    def test_quota_error_message(self):
        body = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}}
        op = self.opener(FakeResponse(body, status=429))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertEqual(payload["reason"], "QUOTA_EXHAUSTED")
        self.assertIn("kuota", payload["message"].lower())
        self.assertIn("key", payload["message"].lower())
        self.assertFalse(os.path.exists(self.out))

    def test_invalid_key_error(self):
        body = {"error": {"code": 400, "status": "API_KEY_INVALID"}}
        op = self.opener(FakeResponse(body, status=400))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertEqual(payload["reason"], "INVALID_KEY")
        self.assertIn("key", payload["message"].lower())
        self.assertFalse(os.path.exists(self.out))

    def test_network_error(self):
        op = self.opener(URLError("no internet"))
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertEqual(payload["reason"], "NETWORK")
        self.assertFalse(os.path.exists(self.out))

    def test_missing_key_short_circuits(self):
        os.remove(self.key)
        op = self.opener()
        payload = g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertEqual(payload["reason"], "NO_KEY")
        self.assertEqual(op.calls, [])
        self.assertFalse(os.path.exists(self.out))

    def test_response_text_extraction(self):
        steps = {"steps": [{"content": [{"type": "text", "text": "Dari steps."}]}]}
        self.assertEqual(g.read_text_response(steps), "Dari steps.")
        self.assertEqual(g.read_text_response(self.text_payload), "Halo dunia.\nKedua kalimat.")

    def test_key_is_trimmed(self):
        with open(self.key, "w", encoding="utf-8") as handle:
            handle.write("\n   ai-studio-key-xyz \t\n")
        op = self.opener(FakeResponse(self.text_payload))
        g.transcribe(self.audio, self.key, self.out, opener=op)

        self.assertEqual(header(op.calls[0], "x-goog-api-key"), "ai-studio-key-xyz")

    def test_main_prints_single_json_line(self):
        argv = [
            "transcribe_gemini.py",
            "--audio", self.audio,
            "--key-file", self.key,
            "--out-txt", self.out,
        ]
        stdout = io.StringIO()
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            code = g.main(opener=self.opener(FakeResponse(self.text_payload)))

        lines = stdout.getvalue().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 1)
        self.assertTrue(json.loads(lines[0])["ok"])


if __name__ == "__main__":
    unittest.main()
