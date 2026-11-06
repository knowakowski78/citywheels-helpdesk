# Last evaluation run

UTC run time: 2026-11-04T17:35:45.813385+00:00
Model: openai/gpt-oss-120b; provider: groq; mode: real model (no fake).

Optional hosted API backup. Minimum request interval: 20.0s. Tools still execute locally.

Passed: 1/16 planned cases. Model answers evaluated: 1/16.

Automated checks are smoke checks of tool selection and answer content, not proof of correctness.
Refusals, unsupported claims and amount context still require human review.

Infrastructure blocker: Cannot reach Groq. Check the network; local Ollama remains available.
This run is incomplete. Resolve the provider configuration/connectivity/quota issue and rerun.

| Case | Status | Seconds | Issues |
| --- | --- | --- | --- |
| hours | PASS | 22.28 |  |
| ebike-price | ERROR | 57.92 | Cannot reach Groq. Check the network; local Ollama remains available. |
| age | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| helmet | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| refund-full | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| refund-half | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| refund-late | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| voucher | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| boundary-48 | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| boundary-24 | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| in-progress | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| unknown-booking | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| unrelated | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| unsupported | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| storm | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |
| injection | NOT RUN | 0.0 | Previous model request failed; evaluation stopped. |

## Answers and tool traces

See the accompanying results.json file for full question, answer and tool output per case.
