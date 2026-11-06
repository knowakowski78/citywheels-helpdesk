"""Optional hosted Groq adapter; local tools still execute in the existing agent."""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .model import ModelError, ModelOutputError

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class _GroqNetworkError(ModelError):
    pass


def api_messages(history):
    """Map the agent's tool_name messages to Groq's required tool_call_id format."""
    result = []
    pending = []
    for message in history:
        role = message["role"]
        if role == "assistant":
            if pending:
                raise ModelOutputError("Missing tool results in API conversation history.")
            converted = {"role": role, "content": message.get("content") or ""}
            calls = message.get("tool_calls") or []
            if calls:
                normalized = []
                for call in calls:
                    function = call.get("function", {})
                    call_id = call.get("id")
                    name = function.get("name")
                    if not isinstance(call_id, str) or not call_id or not isinstance(name, str) or not name:
                        raise ModelOutputError("Groq tool call is missing its ID or function name.")
                    if any(identifier == call_id for identifier, _ in pending):
                        raise ModelOutputError("Groq returned duplicate tool-call IDs.")
                    arguments = function.get("arguments", {})
                    normalized.append({"id": call_id, "type": "function", "function": {
                        "name": name, "arguments": arguments if isinstance(arguments, str) else json.dumps(arguments),
                    }})
                    pending.append((call_id, name))
                converted["tool_calls"] = normalized
            result.append(converted)
        elif role == "tool":
            name = message.get("tool_name")
            index = next((i for i, (_, function_name) in enumerate(pending) if function_name == name), None)
            if index is None:
                raise ModelOutputError("Tool result has no matching Groq tool call.")
            call_id, _ = pending.pop(index)
            result.append({"role": "tool", "tool_call_id": call_id, "content": message["content"]})
        elif role in {"system", "user"}:
            result.append({"role": role, "content": message["content"]})
        else:
            raise ModelOutputError("Unsupported conversation role.")
    if pending:
        raise ModelOutputError("Missing tool results in API conversation history.")
    return result


class GroqModel:
    def __init__(self, request_interval=0):
        if not 0 <= request_interval <= 60:
            raise ModelError("Request interval must be between 0 and 60 seconds.")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.request_interval = request_interval
        self._last_request = None

    def chat(self, messages, tools):
        if not self.api_key or self.api_key in {"paste_your_key_here", "YOUR_GROQ_API_KEY"}:
            raise ModelError("Groq backup needs GROQ_API_KEY. Set it locally or use --env-file .env.groq. Local Ollama remains available.")
        payload = {"model": self.model, "messages": api_messages(messages), "temperature": 0,
                   "max_completion_tokens": 2048, "stream": False}
        if tools:
            payload.update(tools=tools, tool_choice="auto", parallel_tool_calls=False)
        if self.model in {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}:
            payload["reasoning_effort"] = "low"
        request = Request(ENDPOINT, data=json.dumps(payload).encode(), headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "CityWheelsHelpdesk/0.1 (Python)",
        })
        for attempt in range(2):
            if self._last_request is not None:
                delay = self.request_interval - (time.monotonic() - self._last_request)
                if delay > 0:
                    time.sleep(delay)
            self._last_request = time.monotonic()
            try:
                data = self._request(request)
                break
            except _GroqNetworkError:
                if attempt:
                    raise
                time.sleep(2)
        try:
            choice = data["choices"][0]
            message = choice["message"]
            if not isinstance(message, dict):
                raise TypeError()
        except (KeyError, IndexError, TypeError):
            raise ModelOutputError("Groq response has no assistant message.") from None
        if choice.get("finish_reason") == "length":
            raise ModelOutputError("Groq reached the generation limit before finishing.")
        result = {"role": "assistant", "content": message.get("content") or ""}
        calls = message.get("tool_calls") or []
        if calls:
            if not isinstance(calls, list):
                raise ModelOutputError("Groq returned invalid tool calls.")
            seen = set()
            for call in calls:
                if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
                    raise ModelOutputError("Groq returned an invalid tool call.")
                identifier = call.get("id")
                if not isinstance(identifier, str) or not identifier or identifier in seen:
                    raise ModelOutputError("Groq returned missing or duplicate tool-call IDs.")
                seen.add(identifier)
            result["tool_calls"] = calls
        return result

    def _request(self, request):
        try:
            with urlopen(request, timeout=120) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 429:
                raise ModelError("Groq free-plan rate limit or quota reached. Wait, check account limits, or increase --request-interval. No automatic provider switch was made.") from None
            if exc.code in {401, 403}:
                raise ModelError(f"Groq HTTP {exc.code}: check GROQ_API_KEY and model access on your account.") from None
            raise ModelError(f"Groq HTTP {exc.code}. Check model availability and account settings.") from None
        except (URLError, TimeoutError, OSError):
            raise _GroqNetworkError("Cannot reach Groq after a transport failure. Check the network; local Ollama remains available.") from None
        except (ValueError, UnicodeError):
            raise ModelOutputError("Groq returned invalid JSON.") from None
