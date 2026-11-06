import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from citywheels.config import load_groq_env
from citywheels.model import ModelError


class ConfigTests(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env.groq"
            path.write_text(text, encoding="utf-8-sig")
            load_groq_env(path)

    @patch.dict(os.environ, {}, clear=True)
    def test_file_with_bom_comments_and_quotes(self):
        self.load('# comment\nGROQ_API_KEY="dummy-secret"\nGROQ_MODEL=openai/gpt-oss-120b\n')
        self.assertEqual(os.environ["GROQ_API_KEY"], "dummy-secret")

    @patch.dict(os.environ, {"GROQ_API_KEY": "environment-secret"}, clear=True)
    def test_existing_nonempty_environment_wins(self):
        self.load("GROQ_API_KEY=file-secret")
        self.assertEqual(os.environ["GROQ_API_KEY"], "environment-secret")

    @patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True)
    def test_empty_environment_allows_file_value(self):
        self.load("GROQ_API_KEY=file-secret")
        self.assertEqual(os.environ["GROQ_API_KEY"], "file-secret")

    @patch.dict(os.environ, {}, clear=True)
    def test_unsupported_entries_and_bad_quotes_do_not_expose_values(self):
        for text in ('OTHER=sensitive-value', 'GROQ_API_KEY="sensitive-value', 'sensitive-value'):
            with self.subTest(text=text):
                with self.assertRaises(ModelError) as raised:
                    self.load(text)
                self.assertNotIn("sensitive-value", str(raised.exception))
