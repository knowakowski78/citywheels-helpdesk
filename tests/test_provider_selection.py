import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from citywheels.__main__ import main as cli_main
from citywheels.agent import Answer
from eval.run import main as eval_main


class ProviderSelectionTests(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "dummy-key"}, clear=True)
    @patch("citywheels.__main__.Agent")
    @patch("citywheels.__main__.create_model")
    def test_cli_defaults_to_local(self, factory, agent):
        agent.return_value.ask.return_value = Answer("test answer", [])
        with patch.object(sys, "argv", ["citywheels", "Hello"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli_main(), 0)
        factory.assert_called_once_with("ollama", 0)

    @patch("citywheels.__main__.load_groq_env")
    @patch("citywheels.__main__.Agent")
    @patch("citywheels.__main__.create_model")
    def test_explicit_cli_backup_loads_requested_file(self, factory, agent, loader):
        agent.return_value.ask.return_value = Answer("test answer", [])
        with patch.object(sys, "argv", ["citywheels", "Hello", "--provider", "groq", "--env-file", ".env.groq"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli_main(), 0)
        loader.assert_called_once_with(".env.groq")
        factory.assert_called_once_with("groq", 0)

    def test_api_evaluation_cannot_overwrite_local_json_through_another_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = root / "results.json"
            saved.write_text('{"saved_local_result":true}', encoding="utf-8")
            with patch("eval.run.ROOT", root), patch.object(sys, "argv", ["eval.run", "--provider", "groq", "--output", str(root / "results.txt")]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    eval_main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(json.loads(saved.read_text()), {"saved_local_result": True})

    @patch("eval.run.create_model")
    @patch("eval.run.Agent")
    def test_api_evaluation_defaults_to_separate_files(self, agent, factory):
        factory.return_value.model = "dummy-model"
        agent.return_value.ask.return_value = Answer("safe answer", [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cases.json").write_text('[{"id":"test","question":"Hello","patterns":["safe"]}]')
            (root / "results.md").write_text("local baseline")
            with patch("eval.run.ROOT", root), patch.object(sys, "argv", ["eval.run", "--provider", "groq"]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(eval_main(), 0)
            self.assertTrue((root / "groq-results.json").exists())
            self.assertEqual((root / "results.md").read_text(), "local baseline")
            factory.assert_called_once_with("groq", 30)
