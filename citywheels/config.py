"""Explicit, small env-file loader for the optional Groq backup."""
import os
from pathlib import Path

from .model import ModelError


def load_groq_env(path):
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        raise ModelError("Cannot read the Groq env file. Check its path and UTF-8 encoding.") from None
    values = {}
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in {"GROQ_API_KEY", "GROQ_MODEL"}:
            raise ModelError(f"Unsupported Groq env-file entry on line {number}; expected GROQ_API_KEY or GROQ_MODEL.")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ModelError(f"Unclosed quote in Groq env file on line {number}.")
            value = value[1:-1]
        values[key] = value
    # A real environment variable wins over the optional local file.
    for key, value in values.items():
        if not os.environ.get(key):
            os.environ[key] = value
