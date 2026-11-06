# Solution notes

## Setup and model choice

Use Python 3.11+ and Ollama; no Python packages need to be installed. Commands are in
[README.md](README.md). The default is Qwen3 8B with thinking disabled, temperature 0,
a 4096-token context and a 2048-token generation limit.

Qwen3 0.6B was the initial choice because it was small enough to download and run on CPU.
It missed basic retrieval questions. With the same application checks, 8B answered more cases
and finished the full evaluation faster, so it became the default. The smaller model remains available.

Groq's `openai/gpt-oss-120b` is an optional hosted backup. It uses the same loop and local tools,
with a key from the environment or an explicitly selected `.env.groq` file.
The application never switches providers automatically.

## How a question is handled

1. Start a new history with the system instructions and the customer's question.
2. Send it to the model with the three tool definitions.
3. Validate and execute the requested calls, then return their JSON results to the model.
4. Repeat until the model returns a final draft, up to eight rounds.
5. Build the displayed answer from verified results and apply shared policy checks.

Dispatch accepts only known tools and valid arguments. Booking IDs must come from the customer.
If the model skips tools, it gets one corrective turn. Missing evidence leads to a staff referral;
provider failures are reported to the user.

The three tools are handwritten:

- `search_policies` ranks the small Markdown documents by keyword and synonym overlap, with
  extra weight for headings. Answers quote relevant sections rather than freely paraphrasing rules.
- `get_booking` returns stored details or a not-found result.
- `calculate_refund` uses `Decimal` and the fixed assignment time. For confirmed bookings,
  rental refunds are 100% at 48 hours or more, 50% at 24 hours or more, and zero below 24 hours.
  The deposit is returned in full; the booking fee is not refunded. Other statuses return zero.
  Card and voucher refunds retain their respective payment rules.

The model routes questions and calls tools, but its draft cannot override financial facts,
booking details or an age decision. This trades some conversational flexibility for predictable
answers. Age limits and guardian requirements come from the FAQ. Recognized weather-exception
questions get a focused lookup if the model omitted it. These extra calls have
`origin: output_validation` in traces, distinguishing them from the model's calls.
Both providers use these checks; `api_backup.py` only keeps compatibility imports.

## What was tested and fixed

All **82 unit tests** pass offline. They cover refund rules and boundaries, rounding, booking
lookup, invalid calls, fake-model conversations, provider formats and shared policy checks.
The 16-question real-model evaluation includes seven refund cases, unknown bookings, policies
and refusals. Saved local runs scored **14/16** for 0.6B and **16/16** for 8B.
The 8B run took 229.69 seconds on an RTX 3060 laptop with 6 GB VRAM, using CUDA 12 and partial
GPU offload. These timings describe this machine, not a general performance guarantee.

Testing led to several fixes:

- Correct age-policy quotes did not always answer the yes/no question. Shared validation now
  checks a clearly stated age and bike type against the FAQ.
- Storm requests sometimes skipped retrieval. A focused lookup now supplies the actual rule:
  an exception requires staff approval, not a guaranteed refund.
- A failed refund call hid a valid age answer. Booking precedence now requires a lookup result.
- A voucher answer could pass an amount-only check while promising cash. Financial output now
  comes from the tool result; evaluation also requires a no-cash statement and rejects common
  cash promises. Regression tests include contradictory answers.

All saved local answers still pass the stricter voucher check. This was an offline recheck,
not a new model run. The earlier full API run scored 14/16, followed by two successful targeted
checks. There has been no full API run since the shared-rule refactor.
See [eval/README.md](eval/README.md) for report locations and historical records.

## AI assistance

Codex helped write and revise the code, tests and documentation. One concrete mistake in the
AI-generated evaluator was checking the refund amount without checking the booking ID. A negative
test exposed this; the checker now requires the expected amount for the requested booking.
The supplied policies and bookings were kept unchanged.

## Limitations and next steps

Each question stands alone. There is no memory, live availability or weather check, identity
verification, booking update or payment execution. Refunds use the fixed assignment time;
future-date quotes are unsupported. The data is fictional.

Age recognition covers a limited set of English phrases and the supplied FAQ format. Comparisons,
multiple bookings or riders, and combined requests can produce incomplete answers. Policy excerpts
may include extra sections. Changes to cancellation rules require code and test updates.

The evaluation is a smoke check, not proof that every answer is correct. It includes Python
validation as well as model behavior, and regex checks can miss errors or reject valid wording.
The next useful step would be unseen questions, especially ambiguous requests, before expanding
the feature set.
