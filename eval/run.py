"""Run with python -m eval.run; never substitutes a fake for an unavailable LLM."""
import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from citywheels.agent import Agent
from citywheels.model import ModelError, ModelOutputError, create_model
from citywheels.config import load_groq_env
from citywheels.policy_checks import policy_options

ROOT = Path(__file__).resolve().parent


def check(case, answer):
    problems = []
    called = {entry["tool"] for entry in answer.trace}
    for name in case.get("tools", []):
        if name not in called:
            problems.append(f"Missing tool: {name}")
    for pattern in case.get("patterns", []):
        if not re.search(pattern, answer.text, re.I):
            problems.append(f"Missing expected pattern: {pattern}")
    for pattern in case.get("forbidden", []):
        if re.search(pattern, answer.text, re.I):
            problems.append(f"Forbidden pattern: {pattern}")
    if "refund" in case:
        results = [entry["result"] for entry in answer.trace if entry["tool"] == "calculate_refund"]
        if not any(result.get("total_refund_eur") == case["refund"]
                   and ("booking_id" not in case or result.get("booking_id") == case["booking_id"])
                   for result in results):
            problems.append("Expected amount for the requested booking not present in refund tool output")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Defaults to results.md for Ollama and groq-results.md for the API backup.")
    parser.add_argument("--provider", choices=["ollama", "groq"], default="ollama")
    parser.add_argument("--env-file", help="Optional local Groq env file.")
    parser.add_argument("--request-interval", type=float, help="Groq request spacing in seconds; default 30 for free-plan evaluation.")
    parser.add_argument("--case", action="append", help="Run only this case ID; repeat to select multiple cases.")
    args = parser.parse_args()
    if args.env_file and args.provider != "groq":
        parser.error("--env-file is only for the explicit Groq backup.")
    if args.env_file:
        try:
            load_groq_env(args.env_file)
        except ModelError as exc:
            parser.error(str(exc))
    if args.output is None:
        args.output = ROOT / ("results.md" if args.provider == "ollama" else "groq-results.md")
    if args.provider == "groq" and {args.output.resolve(), args.output.with_suffix(".json").resolve()} & {(ROOT / "results.md").resolve(), (ROOT / "results.json").resolve()}:
        parser.error("The Groq backup must not overwrite the saved local evaluation. Choose another --output path.")
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    if args.case:
        unknown = set(args.case) - {case["id"] for case in cases}
        if unknown:
            parser.error("Unknown evaluation case ID.")
        cases = [case for case in cases if case["id"] in args.case]
    interval = args.request_interval if args.request_interval is not None else 30 if args.provider == "groq" else 0
    try:
        model = create_model(args.provider, interval)
    except ModelError as exc:
        parser.error(str(exc))
    options = policy_options()
    agent = Agent(model, **options)
    results = []
    unavailable = None
    for case in cases:
        item = {"id": case["id"], "question": case["question"]}
        started = time.monotonic()
        if unavailable:
            item.update(status="NOT RUN", errors=["Previous model request failed; evaluation stopped."])
        else:
            print(f"RUN: {case['id']}", flush=True)
            try:
                answer = agent.ask(case["question"])
                problems = check(case, answer)
                item.update(status="FAIL" if problems else "PASS", errors=problems,
                            answer=answer.text, trace=answer.trace)
            except ModelOutputError as exc:
                item.update(status="ERROR", errors=[str(exc)])
            except ModelError as exc:
                unavailable = str(exc)
                item.update(status="ERROR", errors=[unavailable])
        item["duration_seconds"] = round(time.monotonic() - started, 2)
        results.append(item)
        print(f"{item['status']}: {item['id']} ({item['duration_seconds']}s)", flush=True)
    passed = sum(r["status"] == "PASS" for r in results)
    evaluated = sum(r["status"] in {"PASS", "FAIL"} for r in results)
    report = ["# Last evaluation run", "", f"UTC run time: {datetime.now(timezone.utc).isoformat()}",
              f"Model: {model.model}; provider: {args.provider}; mode: real model (no fake).", "",
              (f"GPU layers option: {model.num_gpu} (0 = CPU, -1 = automatic). Thinking: {model.think}; context 4096 tokens." if args.provider == "ollama" else f"Optional hosted API backup. Minimum request interval: {interval}s. Tools still execute locally."), "",
              f"Passed: {passed}/{len(cases)} planned cases. Model answers evaluated: {evaluated}/{len(cases)}.", "",
              "Automated checks are smoke checks of tool selection and answer content, not proof of correctness.",
              "Refusals, unsupported claims and amount context still require human review.", ""]
    if unavailable:
        report += [f"Infrastructure blocker: {unavailable}", "This run is incomplete. Resolve the provider configuration/connectivity/quota issue and rerun.", ""]
    report += ["| Case | Status | Seconds | Issues |", "| --- | --- | --- | --- |"]
    for item in results:
        issues = "; ".join(item["errors"]).replace("|", "\\|")
        report.append(f"| {item['id']} | {item['status']} | {item['duration_seconds']} | {issues} |")
    report += ["", "## Answers and tool traces", "", f"See the accompanying {args.output.with_suffix('.json').name} file for full question, answer and tool output per case.", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(report), encoding="utf-8")
    args.output.with_suffix(".json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Passed: {passed}/{len(cases)}; evaluated: {evaluated}/{len(cases)}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
