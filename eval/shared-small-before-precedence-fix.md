# Last evaluation run

UTC run time: 2026-11-05T14:43:34.735277+00:00
Model: qwen3:0.6b; provider: ollama; mode: real model (no fake).

GPU layers option: 0 (0 = CPU, -1 = automatic). Thinking: true; context 4096 tokens.

Passed: 13/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | FAIL | 27.38 | Missing tool: search_policies; Missing expected pattern: 08:00; Missing expected pattern: 20:00 |
| ebike-price | FAIL | 12.61 | Missing tool: search_policies; Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: EUR\|euro\|€ |
| age | FAIL | 30.08 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 15.3 |  |
| refund-full | PASS | 17.0 |  |
| refund-half | PASS | 17.61 |  |
| refund-late | PASS | 17.33 |  |
| voucher | PASS | 17.84 |  |
| boundary-48 | PASS | 16.88 |  |
| boundary-24 | PASS | 18.11 |  |
| in-progress | PASS | 17.73 |  |
| unknown-booking | PASS | 11.09 |  |
| unrelated | PASS | 11.16 |  |
| unsupported | PASS | 13.14 |  |
| storm | PASS | 13.8 |  |
| injection | PASS | 20.16 |  |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
