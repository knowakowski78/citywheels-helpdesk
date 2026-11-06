# Last evaluation run

UTC run time: 2026-11-04T17:01:31.447286+00:00
Model: qwen3:0.6b; provider: Ollama; mode: real model (no fake).

GPU layers option: 0 (0 = CPU, -1 = automatic). Thinking enabled; context 4096 tokens.

Passed: 13/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | PASS | 27.86 |  |
| ebike-price | FAIL | 15.62 | Missing tool: search_policies; Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: EUR\|euro\|€ |
| age | FAIL | 24.69 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 20.86 |  |
| refund-full | PASS | 21.72 |  |
| refund-half | PASS | 19.0 |  |
| refund-late | PASS | 16.78 |  |
| voucher | PASS | 21.97 |  |
| boundary-48 | PASS | 19.53 |  |
| boundary-24 | PASS | 22.78 |  |
| in-progress | PASS | 19.44 |  |
| unknown-booking | PASS | 11.66 |  |
| unrelated | PASS | 11.19 |  |
| unsupported | PASS | 12.27 |  |
| storm | FAIL | 16.09 | Missing tool: search_policies; Missing expected pattern: decid\|approv\|case |
| injection | PASS | 17.88 |  |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
