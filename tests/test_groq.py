import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from citywheels.agent import Agent
from citywheels.groq import GroqModel, api_messages
from citywheels.model import ModelError, ModelOutputError, OllamaModel, create_model
from citywheels.tools import TOOL_SCHEMAS


def response(message, finish_reason="stop"):
    return io.BytesIO(json.dumps({"choices": [{"message": message, "finish_reason": finish_reason}]}).encode())


@patch.dict(os.environ, {"GROQ_API_KEY": "dummy-test-key", "GROQ_MODEL": "openai/gpt-oss-120b"}, clear=True)
class GroqTests(unittest.TestCase):
    def test_default_provider_stays_local_even_when_groq_key_exists(self):
        self.assertIsInstance(create_model(), OllamaModel)
        self.assertIsInstance(create_model("groq"), GroqModel)

    @patch("citywheels.groq.urlopen")
    def test_request_contract_and_secret_only_in_header(self, urlopen):
        urlopen.return_value = response({"role": "assistant", "content": "OK"})
        answer = GroqModel().chat([{"role": "user", "content": "Hello"}], TOOL_SCHEMAS)
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer dummy-test-key")
        self.assertNotIn("dummy-test-key", request.data.decode())
        self.assertEqual(request.get_header("User-agent"), "CityWheelsHelpdesk/0.1 (Python)")
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(answer["content"], "OK")

    @patch("citywheels.groq.urlopen")
    def test_real_agent_loop_translates_tool_ids_and_preserves_financial_guard(self, urlopen):
        urlopen.side_effect = [
            response({"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "calculate_refund", "arguments": '{"booking_id":"CW-1002"}'}}]}),
            response({"role": "assistant", "content": "Your refund is 999 EUR, paid in cash."}),
        ]
        answer = Agent(create_model("groq")).ask("Refund for CW-1002?")
        self.assertIn("340.00 EUR", answer.text)
        self.assertNotIn("999", answer.text)
        second = json.loads(urlopen.call_args_list[1].args[0].data)
        self.assertEqual(second["messages"][-1]["tool_call_id"], "call_1")
        self.assertNotIn("tool_name", second["messages"][-1])
        self.assertEqual(json.loads(second["messages"][-1]["content"])["total_refund_eur"], "340.00")

    @patch("citywheels.groq.urlopen")
    def test_missing_key_fails_before_network(self, urlopen):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            with self.assertRaisesRegex(ModelError, "GROQ_API_KEY"):
                GroqModel().chat([], [])
        urlopen.assert_not_called()

    @patch("citywheels.groq.urlopen")
    def test_errors_do_not_echo_provider_body_or_key(self, urlopen):
        for code in (401, 403, 404, 429, 500):
            with self.subTest(code=code):
                urlopen.side_effect = HTTPError("url", code, "dummy-test-key", {}, io.BytesIO(b"private provider body"))
                with self.assertRaises(ModelError) as raised:
                    GroqModel().chat([], [])
                self.assertNotIn("dummy-test-key", str(raised.exception))
                self.assertNotIn("private provider body", str(raised.exception))

    @patch("citywheels.groq.time.sleep")
    @patch("citywheels.groq.urlopen")
    def test_network_failure(self, urlopen, sleep):
        urlopen.side_effect = URLError("private details")
        with self.assertRaisesRegex(ModelError, "Cannot reach Groq"):
            GroqModel().chat([], [])
        self.assertEqual(urlopen.call_count, 2)

    @patch("citywheels.groq.time.sleep")
    @patch("citywheels.groq.urlopen")
    def test_one_transient_transport_failure_can_recover(self, urlopen, sleep):
        urlopen.side_effect = [URLError("connection reset"), response({"content": "OK"})]
        self.assertEqual(GroqModel().chat([], [])["content"], "OK")
        self.assertEqual(urlopen.call_count, 2)

    @patch("citywheels.groq.urlopen")
    def test_invalid_and_truncated_output(self, urlopen):
        for body in (b"invalid json", b"{}", b'{"choices":[]}', b'{"choices":[{"message":null}]}'):
            with self.subTest(body=body):
                urlopen.return_value = io.BytesIO(body)
                with self.assertRaises(ModelOutputError):
                    GroqModel().chat([], [])
        urlopen.return_value = response({"content": "partial"}, "length")
        with self.assertRaises(ModelOutputError):
            GroqModel().chat([], [])

    @patch("citywheels.groq.time.sleep")
    @patch("citywheels.groq.time.monotonic", side_effect=[10, 12, 40])
    @patch("citywheels.groq.urlopen")
    def test_request_pacing(self, urlopen, monotonic, sleep):
        urlopen.side_effect = [response({"content": "one"}), response({"content": "two"})]
        model = GroqModel(request_interval=30)
        model.chat([], [])
        model.chat([], [])
        sleep.assert_called_once_with(28)

    def test_bad_request_intervals(self):
        for value in (-1, 61):
            with self.assertRaises(ModelError):
                GroqModel(value)

    def test_two_calls_of_same_function_keep_distinct_ids(self):
        history = [
            {"role": "assistant", "content": "", "thinking": "not transmitted", "tool_calls": [
                {"id": "one", "function": {"name": "get_booking", "arguments": {"booking_id": "CW-1001"}}},
                {"id": "two", "function": {"name": "get_booking", "arguments": {"booking_id": "CW-1002"}}},
            ]},
            {"role": "tool", "tool_name": "get_booking", "content": "first"},
            {"role": "tool", "tool_name": "get_booking", "content": "second"},
        ]
        converted = api_messages(history)
        self.assertEqual([m["tool_call_id"] for m in converted[1:]], ["one", "two"])
        self.assertNotIn("thinking", converted[0])

    def test_unmatched_or_missing_tool_ids_are_rejected(self):
        for history in ([{"role": "tool", "tool_name": "unknown", "content": "bad"}],
                        [{"role": "assistant", "tool_calls": [{"function": {"name": "get_booking"}}]}],
                        [{"role": "assistant", "tool_calls": [{"id": "one", "function": {"name": "get_booking"}}]}]):
            with self.subTest(history=history):
                with self.assertRaises(ModelOutputError):
                    api_messages(history)
