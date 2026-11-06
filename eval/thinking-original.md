# Last evaluation run

UTC run time: 2026-11-04T16:40:17.434954+00:00
Model: qwen3:0.6b; provider: Ollama; mode: real model (no fake).

GPU layers option: 0 (0 = CPU, -1 = automatic). Thinking enabled; context 4096 tokens.

Passed: 2/16 planned cases. Model answers evaluated: 11/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

Infrastructure blocker: Model returned an empty answer.
This run does not measure model quality. Start/configure Ollama and rerun.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | FAIL | 7.97 | Missing tool: search_policies; Missing expected pattern: 08:00; Missing expected pattern: 20:00 |
| ebike-price | FAIL | 9.78 | Missing tool: search_policies; Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: EUR\|euro\|€ |
| age | FAIL | 6.22 | Missing tool: search_policies; Missing expected pattern: \b16\b; Missing expected pattern: cannot\|can't\|not allowed\|no\b\|minimum |
| helmet | FAIL | 5.94 | Missing tool: search_policies; Missing expected pattern: required\|must\|mandatory; Missing expected pattern: \b16\b |
| refund-full | FAIL | 18.17 | Missing expected pattern: \b40(?:[.,]00)?\b; Missing expected pattern: \b50(?:[.,]00)?\b |
| refund-half | FAIL | 7.38 | Missing tool: calculate_refund; Missing expected pattern: \b340(?:[.,]00)?\b; Missing expected pattern: \b300(?:[.,]00)?\b; Missing expected pattern: card; Missing expected pattern: 5\|five; Expected amount for the requested booking not present in refund tool output |
| refund-late | FAIL | 16.91 | Missing expected pattern: \b0(?:[.,]00)?\b\|zero\|no rental |
| voucher | PASS | 26.09 |  |
| boundary-48 | FAIL | 10.19 | Missing tool: calculate_refund; Missing expected pattern: \b186(?:[.,]00)?\b; Expected amount for the requested booking not present in refund tool output |
| boundary-24 | PASS | 21.69 |  |
| in-progress | FAIL | 8.09 | Missing tool: calculate_refund; Missing expected pattern: nothing\|no refund\|\b0(?:[.,]00)?\b; Expected amount for the requested booking not present in refund tool output |
| unknown-booking | ERROR | 12.73 | Model returned an empty answer. |
| unrelated | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| unsupported | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| storm | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| injection | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
