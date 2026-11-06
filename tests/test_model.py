import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from citywheels.model import ModelError, OllamaModel


class ModelTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_default_is_tested_larger_fast_profile(self):
        model = OllamaModel()
        self.assertEqual((model.model,model.num_gpu,model.think),("qwen3:8b","-1","false"))

    @patch.dict(os.environ, {"OLLAMA_MODEL":"qwen3:0.6b"}, clear=True)
    def test_small_profile_is_still_available_with_reasoning(self):
        model = OllamaModel()
        self.assertEqual((model.model,model.num_gpu,model.think),("qwen3:0.6b","0","true"))

    @patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434/", "OLLAMA_MODEL": "test-model", "OLLAMA_API_KEY": "dummy-test-key"})
    @patch("citywheels.model.urlopen")
    def test_http_contract(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"message":{"role":"assistant","content":"hello"}}')
        model = OllamaModel()
        result = model.chat([{"role": "user", "content": "hi"}], [])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        self.assertEqual(request.get_header("Authorization"), "Bearer dummy-test-key")
        payload = json.loads(request.data)
        self.assertFalse(payload["stream"])
        self.assertTrue(payload["think"])
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertEqual(payload["options"]["num_predict"], 2048)
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"][0]["content"], "hi")
        self.assertEqual(result["content"], "hello")

    @patch("citywheels.model.urlopen")
    def test_network_errors_have_safe_messages(self, urlopen):
        for error in (URLError("sensitive details"), HTTPError("url", 401, "sensitive details", {}, None), TimeoutError()):
            with self.subTest(error=type(error)):
                urlopen.side_effect = error
                with self.assertRaises(ModelError) as raised:
                    OllamaModel().chat([], [])
                self.assertNotIn("sensitive details", str(raised.exception))

    @patch("citywheels.model.urlopen")
    def test_invalid_json_and_missing_message(self, urlopen):
        for body in (b"not json", b"{}", b"[]", b'{"message":null}'):
            with self.subTest(body=body):
                urlopen.return_value = io.BytesIO(body)
                with self.assertRaises(ModelError):
                    OllamaModel().chat([], [])

    @patch("citywheels.model.urlopen")
    def test_truncated_response_is_not_accepted_as_complete(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"message":{"content":"partial answer"},"done_reason":"length"}')
        with self.assertRaisesRegex(ModelError, "generation limit"):
            OllamaModel().chat([], [])

    @patch.dict(os.environ, {"OLLAMA_NUM_GPU": "not-an-integer"})
    def test_invalid_gpu_setting_has_clear_error(self):
        with self.assertRaisesRegex(ModelError, "OLLAMA_NUM_GPU"):
            OllamaModel().chat([], [])

    @patch.dict(os.environ, {"OLLAMA_THINK": "false"})
    @patch("citywheels.model.urlopen")
    def test_optional_thinking_override(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"message":{"content":"OK"}}')
        OllamaModel().chat([], [])
        self.assertFalse(json.loads(urlopen.call_args.args[0].data)["think"])

    @patch.dict(os.environ, {"OLLAMA_THINK": "invalid"})
    def test_invalid_thinking_setting_fails_clearly(self):
        with self.assertRaisesRegex(ModelError, "OLLAMA_THINK"):
            OllamaModel().chat([], [])


if __name__ == "__main__":
    unittest.main()
