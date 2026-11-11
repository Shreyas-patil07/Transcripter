import sys
import unittest
from unittest.mock import patch

from transcribe import format_progress, parse_args, romanize_hindi


class TranscripterTests(unittest.TestCase):
    def test_defaults_to_hindi_devanagari_and_turbo(self):
        with patch.object(sys, "argv", ["transcribe.py", "sample.mp4"]):
            args = parse_args()

        self.assertEqual(args.language, "hi")
        self.assertEqual(args.romanize, "none")
        self.assertEqual(args.model, "large-v3-turbo")
        self.assertEqual(args.device, "cuda")

    def test_auto_language_is_exposed(self):
        with patch.object(sys, "argv", ["transcribe.py", "sample.mp4", "--language", "auto"]):
            args = parse_args()

        self.assertEqual(args.language, "auto")

    def test_romanizer_converts_devanagari_and_keeps_latin_phrase(self):
        result = romanize_hindi("आज machine learning")

        self.assertTrue(result.isascii())
        self.assertIn("machine learning", result)

    def test_romanizer_leaves_latin_only_text_unchanged(self):
        text = "Only existing English text."
        self.assertEqual(romanize_hindi(text), text)

    def test_progress_format(self):
        self.assertEqual(format_progress(3723), "01:02:03")


if __name__ == "__main__":
    unittest.main()
