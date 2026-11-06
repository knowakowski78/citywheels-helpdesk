# CityWheels help desk agent

A Python CLI for a fictional bike rental shop. It answers questions using the supplied policies
and bookings. The model calls tools to look up facts; Python calculates refunds.

Requires Python 3.11+ and Ollama. There are no third-party Python dependencies.
The default model is **Qwen3 8B**, running locally with thinking disabled.

## Quick start

Install [Ollama](https://ollama.com/download), then run these commands from the project folder.
The examples use Windows PowerShell:

```powershell
git clone https://github.com/knowakowski78/citywheels-helpdesk.git
cd citywheels-helpdesk
python -m venv .venv
ollama pull qwen3:8b
.\.venv\Scripts\python.exe -m citywheels
```

Ollama must be running. If needed, run `ollama serve` in another terminal.
The model download is about 5.2 GB; speed depends on available RAM and GPU memory.
On macOS/Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

On Windows, `./setup.ps1` creates the environment and runs the offline tests.
With Ollama installed, `./setup.ps1 -DownloadModel` also starts the server if needed and downloads
the default model. No API key is needed for local mode.

Ask one question and show the tool calls:

```powershell
.\.venv\Scripts\python.exe -m citywheels "What is my refund for CW-1002?" --trace
```

Use `/exit` to leave interactive mode. Each question is independent, so repeat the booking ID
in a follow-up. Tools only read data: they do not cancel bookings or issue payments.
Refunds use the assignment's fixed time: **10 June 2026, 09:00 UTC+02:00**.

## Tests and evaluation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m eval.run --output eval/new-run.md
```

All **82 unit tests** pass without a model server, network access or credentials.
GitHub Actions runs the same tests on Linux and Windows on each push and pull request.
Evaluation uses a real model and saves Markdown results plus JSON answers and tool traces.
It exits with code 1 if any case fails or cannot run.

| Local model | Passed | Total time |
| --- | --- | --- |
| Qwen3 8B, thinking off, partial GPU offload | 16/16 | 229.69 s |
| Qwen3 0.6B, thinking on, CPU | 14/16 | 290.56 s |

The smaller model missed opening hours and e-bike prices because it did not retrieve policies.
These are results from a small application evaluation, including the checks in Python.
They do not establish general model accuracy. See [eval/results.md](eval/results.md) for the
saved default-model run and [eval/README.md](eval/README.md) for the other records.

## Code map

| File | Purpose |
| --- | --- |
| `citywheels/agent.py` | Tool-calling loop and argument checks |
| `citywheels/tools.py` | Policy search, booking lookup and refund calculations |
| `citywheels/answers.py` | Answers built from verified tool results |
| `citywheels/policy_checks.py` | Age and weather checks shared by both providers |
| `citywheels/model.py`, `groq.py` | HTTP adapters for Ollama and the optional Groq backup |
| `tests/`, `eval/` | Unit tests and real-model evaluation |

The model chooses from three tools: `search_policies`, `get_booking` and `calculate_refund`.
Python executes each call and returns its result to the model. Before showing an answer,
the application uses verified facts to prevent invented amounts and unsupported promises.
Extra validation calls are marked `origin: output_validation` in the trace.

## Other ways to run

The PowerShell launchers select a profile and restore the previous model settings on exit:

```powershell
.\start-local-8b.ps1
.\start-local-small.ps1
.\start-api.ps1
```

The small profile needs `ollama pull qwen3:0.6b`. The API profile requires a Groq key and is
always selected explicitly; local requests never fall back to the cloud automatically.
See [API-BACKUP.md](API-BACKUP.md) for key setup and [LOCAL-8B.md](LOCAL-8B.md) for local options.
`.env.example` lists settings. Ollama reads environment variables; `.env` is not loaded automatically.
Keep keys in the environment or the ignored `.env.groq` file.

[SOLUTION.md](SOLUTION.md) explains the design, findings, limitations and AI assistance.
[DATA.md](DATA.md) describes the unchanged assignment data.
