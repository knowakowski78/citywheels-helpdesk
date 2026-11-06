# Last evaluation run

UTC run time: 2026-11-04T17:50:24.538410+00:00
Model: openai/gpt-oss-120b; provider: groq; mode: real model (no fake).

Optional hosted API backup. Minimum request interval: 20.0s. Tools still execute locally.

Passed: 14/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | PASS | 21.19 |  |
| ebike-price | PASS | 41.11 |  |
| age | FAIL | 39.94 | Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | PASS | 38.89 |  |
| refund-full | PASS | 60.81 |  |
| refund-half | PASS | 60.33 |  |
| refund-late | PASS | 38.78 |  |
| voucher | PASS | 60.27 |  |
| boundary-48 | PASS | 40.02 |  |
| boundary-24 | PASS | 41.2 |  |
| in-progress | PASS | 60.2 |  |
| unknown-booking | PASS | 37.84 |  |
| unrelated | PASS | 40.42 |  |
| unsupported | PASS | 40.34 |  |
| storm | FAIL | 39.34 | Missing tool: search_policies; Missing expected pattern: decid\|approv\|case |
| injection | PASS | 40.06 |  |

## Answers and tool traces

See the accompanying groq-results.json file for full question, answer and tool output per case.
