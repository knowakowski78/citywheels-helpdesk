import argparse
import json
import sys

from .agent import Agent
from .model import ModelError, create_model
from .config import load_groq_env
from .policy_checks import policy_options


def main():
    parser = argparse.ArgumentParser(description="CityWheels help desk (fixed date: 2026-06-10 09:00 +02)")
    parser.add_argument("question", nargs="?", help="Omit for an interactive prompt; each question is independent.")
    parser.add_argument("--trace", action="store_true", help="Show tool calls and results on stderr.")
    parser.add_argument("--provider", choices=["ollama", "groq"], default="ollama", help="Ollama is the local default; Groq is an explicit API backup.")
    parser.add_argument("--env-file", help="Optional local Groq key file, e.g. .env.groq; values are never printed.")
    parser.add_argument("--request-interval", type=float, default=0, help="Minimum seconds between Groq requests (0–60).")
    args = parser.parse_args()
    if args.env_file and args.provider != "groq":
        parser.error("--env-file is for the Groq backup. Local Ollama uses environment variables as before.")

    def answer(question):
        result = agent.ask(question)
        print(result.text)
        if args.trace:
            print(json.dumps(result.trace, ensure_ascii=False, indent=2), file=sys.stderr)

    try:
        if args.env_file:
            load_groq_env(args.env_file)
        options = policy_options()
        agent = Agent(create_model(args.provider, args.request_interval), **options)
        if args.question:
            answer(args.question)
        else:
            print("CityWheels — wpisz pytanie; /exit kończy. Każde pytanie jest niezależne.")
            while True:
                question = input("> ").strip()
                if question in {"/exit", "/quit"}:
                    break
                if question:
                    answer(question)
    except ModelError as exc:
        print(f"Model error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
