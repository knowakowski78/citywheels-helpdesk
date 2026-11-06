# Last evaluation run

UTC run time: 2026-11-05T14:49:46.128285+00:00
Model: qwen3:0.6b; provider: ollama; mode: real model (no fake).

GPU layers option: 0 (0 = CPU, -1 = automatic). Thinking: true; context 4096 tokens.

Passed: 14/16 planned cases. Model answers evaluated: 16/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | FAIL | 28.22 | Missing tool: search_policies; Missing expected pattern: 08:00; Missing expected pattern: 20:00 |
| ebike-price | FAIL | 13.05 | Missing tool: search_policies; Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: EUR\|euro\|€ |
| age | PASS | 30.3 |  |
| helmet | PASS | 16.22 |  |
| refund-full | PASS | 18.72 |  |
| refund-half | PASS | 19.47 |  |
| refund-late | PASS | 18.67 |  |
| voucher | PASS | 19.22 |  |
| boundary-48 | PASS | 17.59 |  |
| boundary-24 | PASS | 18.75 |  |
| in-progress | PASS | 18.06 |  |
| unknown-booking | PASS | 11.3 |  |
| unrelated | PASS | 11.5 |  |
| unsupported | PASS | 14.09 |  |
| storm | PASS | 14.62 |  |
| injection | PASS | 20.78 |  |

## Answers and tool traces

See the accompanying shared-small-results.json file for full question, answer and tool output per case.
