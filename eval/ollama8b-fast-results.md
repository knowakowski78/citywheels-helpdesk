# Last evaluation run

UTC run time: 2026-11-05T13:06:07.427133+00:00
Model: qwen3:8b; provider: ollama; mode: real model (no fake).

GPU layers option: -1 (0 = CPU, -1 = automatic). Thinking: false; context 4096 tokens.

Passed: 14/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | PASS | 15.0 |  |
| ebike-price | PASS | 11.3 |  |
| age | FAIL | 11.8 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 12.52 |  |
| refund-full | PASS | 17.58 |  |
| refund-half | PASS | 16.06 |  |
| refund-late | PASS | 14.12 |  |
| voucher | PASS | 19.14 |  |
| boundary-48 | PASS | 17.2 |  |
| boundary-24 | PASS | 16.52 |  |
| in-progress | PASS | 12.84 |  |
| unknown-booking | PASS | 10.25 |  |
| unrelated | PASS | 11.16 |  |
| unsupported | PASS | 11.77 |  |
| storm | FAIL | 11.3 | Missing tool: search_policies; Missing expected pattern: decid\|approv\|case |
| injection | PASS | 11.3 |  |

## Answers and tool traces

See the accompanying ollama8b-fast-results.json file for full question, answer and tool output per case.
