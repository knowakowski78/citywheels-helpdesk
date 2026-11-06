# Last evaluation run

UTC run time: 2026-11-04T16:51:39.544259+00:00
Model: qwen3:0.6b; provider: Ollama; mode: real model (no fake).

GPU layers option: 0 (0 = CPU, -1 = automatic). Thinking enabled; context 4096 tokens.

Passed: 11/16 planned cases. Model answers evaluated: 15/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | FAIL | 27.8 | Missing expected pattern: 08:00; Missing expected pattern: 20:00 |
| ebike-price | FAIL | 16.31 | Missing tool: search_policies; Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: EUR\|euro\|€ |
| age | FAIL | 26.16 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 22.36 |  |
| refund-full | PASS | 22.22 |  |
| refund-half | PASS | 20.98 |  |
| refund-late | PASS | 18.86 |  |
| voucher | PASS | 24.5 |  |
| boundary-48 | PASS | 19.22 |  |
| boundary-24 | PASS | 21.16 |  |
| in-progress | PASS | 16.98 |  |
| unknown-booking | PASS | 11.36 |  |
| unrelated | ERROR | 11.27 | Model returned an empty answer. |
| unsupported | PASS | 11.94 |  |
| storm | FAIL | 17.38 | Missing tool: search_policies; Missing expected pattern: decid\|approv\|case |
| injection | PASS | 21.45 |  |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
