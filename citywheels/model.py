"""Small Ollama HTTP adapter; no SDK or framework required."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelError(RuntimeError):
    pass


class ModelOutputError(ModelError):
    """A single model answer failed, rather than the provider being unreachable."""


class OllamaModel:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.api_key = os.getenv("OLLAMA_API_KEY", "")
        self.num_gpu = os.getenv("OLLAMA_NUM_GPU", "0" if self.model == "qwen3:0.6b" else "-1")
        self.think = os.getenv("OLLAMA_THINK", "false" if self.model == "qwen3:8b" else "true").strip().lower()

    def chat(self, messages, tools):
        if self.think not in {"true", "false"}:
            raise ModelError("OLLAMA_THINK must be true or false.")
        payload = {"model": self.model, "messages": messages, "tools": tools,
                   "stream": False, "think": self.think == "true",
                   "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 2048}}
        try:
            payload["options"]["num_gpu"] = int(self.num_gpu)
        except ValueError:
            raise ModelError("OLLAMA_NUM_GPU must be an integer (0 for CPU, -1 for automatic).") from None
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.base_url + "/api/chat", data=json.dumps(payload).encode(), headers=headers)
        try:
            with urlopen(request, timeout=120) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise ModelError(f"Ollama HTTP {exc.code}. Check the model name, server and API key.") from None
        except (URLError, TimeoutError, OSError):
            raise ModelError(f"Cannot reach Ollama. Start Ollama and run: ollama pull {self.model}") from None
        except (ValueError, UnicodeError):
            raise ModelError("Ollama returned invalid JSON.") from None
        if not isinstance(result, dict) or not isinstance(result.get("message"), dict):
            raise ModelOutputError("Ollama response has no message.")
        if result.get("done_reason") == "length":
            raise ModelOutputError("Model reached the generation limit before finishing.")
        return result["message"]


def create_model(provider="ollama", request_interval=0):
    """Provider selection is explicit; never automatically sends local requests to the cloud."""
    if provider == "ollama":
        return OllamaModel()
    if provider == "groq":
        from .groq import GroqModel
        return GroqModel(request_interval=request_interval)
    raise ModelError("Unknown provider. Choose ollama or groq.")
