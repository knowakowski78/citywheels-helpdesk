# Last evaluation run

UTC run time: 2026-11-05T13:02:00.739289+00:00
Model: qwen3:8b; provider: ollama; mode: real model (no fake).

GPU layers option: -1 (0 = CPU, -1 = automatic). Thinking enabled; context 4096 tokens.

Passed: 14/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | PASS | 40.69 |  |
| ebike-price | PASS | 33.97 |  |
| age | FAIL | 71.03 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 35.02 |  |
| refund-full | PASS | 43.45 |  |
| refund-half | PASS | 65.75 |  |
| refund-late | PASS | 54.98 |  |
| voucher | PASS | 67.39 |  |
| boundary-48 | PASS | 47.14 |  |
| boundary-24 | PASS | 53.23 |  |
| in-progress | PASS | 59.56 |  |
| unknown-booking | PASS | 27.56 |  |
| unrelated | PASS | 34.33 |  |
| unsupported | PASS | 34.3 |  |
| storm | FAIL | 52.28 | Missing tool: search_policies; Missing expected pattern: decid\|approv\|case |
| injection | PASS | 49.64 |  |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
