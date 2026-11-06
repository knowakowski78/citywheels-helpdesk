# Evaluation records

Start with `results.md` and `results.json`: the selected Qwen3 8B run, with all 16 cases
passed. The JSON contains each question, answer and tool trace. The original run time is
retained; this pair was copied from `shared-8b-fast-results.*`.

`cases.json` defines the questions and checks. From the project root, with Ollama running:

```powershell
.\.venv\Scripts\python.exe -m eval.run --output eval/new-run.md
```

`--case voucher` selects one case. The runner uses a real model and reports errors rather
than substituting a fake model.

## Other records

| Files | What they record |
| --- | --- |
| `shared-small-results.*` | Final 0.6B comparison: 14/16 |
| `shared-8b-fast-results.*` | Final 8B comparison: 16/16 |
| `shared-policy-paraphrases.json` | Three live age/guardian/weather checks |
| `groq-results.*`, `groq-before-policy-fix.*` | Earlier full API run: 14/16 |
| `policy-fix-smoke.*` | Targeted API rerun of the two failures: 2/2 |
| `shared-small-before-precedence-fix.*` | Run that exposed the failed-tool precedence bug |
| `legacy-*`, `ollama8b-*` | Local runs before shared checks; some are duplicate copies |
| `baseline.*`, `thinking-original.*`, `guarded-first.*`, `groq-first-attempt.*` | Early or incomplete runs |
| `manual-*`, `baseline-prompt.txt`, `*-unit-tests.txt`, `unit-tests.txt` | Development notes and historical test logs |

Old reports describe the code at the time of each run. Their unit-test counts are historical;
the current suite has 82 tests. They are retained to show failures and changes.

After the latest saved model run, the voucher check was tightened to require a no-cash statement
and reject common cash promises. All 16 saved default-model answers passed an offline recheck.
This did not change the model-run timestamp or constitute a new live run.

Checks cover tool calls, answer patterns, and refund amounts tied to booking IDs. They remain
smoke checks: regexes can miss errors or reject valid phrasing. Validation calls from Python count
toward application results and are marked `origin: output_validation` in traces.
