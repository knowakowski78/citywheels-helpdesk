# Shared policy checks

The CLI and evaluator configure `Agent` with `policy_options()` from
`citywheels/policy_checks.py`. Ollama and Groq therefore use the same business rules.
Provider adapters only handle HTTP requests and message formats.

The model chooses from the original three tools. Before showing an answer, validation can add
an age check or a focused weather-policy lookup. These calls have `origin: output_validation`
in the trace. Direct callers constructing `Agent` should pass `**policy_options()` for the
same behavior.

## Age questions

After retrieving the FAQ, an explicit age and bike type can produce a yes/no decision.
Minimum ages and guardian requirements come from the FAQ lines. If the format cannot be parsed,
the application falls back to source evidence or staff contact.

Recognized English phrases include “14-year-old”, “age 14”, “aged twenty-one” and
“my daughter is fourteen”. Missing, negated, multiple or unsupported ages are not guessed.
Months, weeks, days, decimal ages, dates and “hundred” forms are excluded.
This is limited phrase matching; comparisons and combined requests can still be misinterpreted.

## Weather questions

Recognized phrases include storm warnings, thunderstorm alerts, bad/severe weather and weather
exceptions. If the model skipped a relevant lookup, validation retrieves the cancellation policy.
The answer quotes the conditional staff-decision rule. It does not verify live weather or promise
an exception.

## Answer selection

Booking and refund results take priority in combined requests. Failed unrelated calls do not
suppress a valid age decision. The common renderer takes financial facts from tools, quotes
policy sections and refers unsupported questions to staff. Multi-intent answers remain limited.

Unit tests exercise these checks with fake models. Real-model results include the checks as part
of the application; they are not measurements of the LLM alone. See [SOLUTION.md](SOLUTION.md)
for results and limitations.
