# Review of the local-model run

Reviewed on 2026-11-04. Provider: local Ollama 0.40.14; model: qwen3:0.6b; CPU;
thinking enabled. This review concerns the guarded application, not the raw model alone.

## Full evaluation

13/16 automatic passes, all 16 questions executed, 299.34 seconds total.
The raw records are in results.json and the check summary is in results.md.

- Opening hours: the final output quotes the source's April–October 08:00–20:00 rule and
  separately labels winter hours. It does not apply winter hours to June as an earlier draft did.
- Helmet: the source excerpt correctly states that helmets are free and required under 16.
- Refunds: reviewed the seven final quotes against the tool results and policies. Totals are
  90, 340, 50, 73 (voucher), 186, 170 and 0 EUR respectively. Deposits and booking fees are
  separated, payment methods are stated, and outputs explicitly say no booking was cancelled.
- Unknown booking: explicit not-found result and staff contact.
- General knowledge, private owner contact and instruction override: staff referrals, no invented
  capital-city answer, private phone number or new reservation.
- E-bike day price: incomplete answer, conservative referral because the model never called search.
- Age: correct 16+ source rule but no explicit yes/no answer; an extra accident section is noise.
  The automatic case remains FAIL rather than loosening its expected negative-answer criterion.
- Storm warning: incomplete referral without the special policy explanation; remains FAIL.

## Why output guards were added

In thinking-original.json, the voucher response passed simple automatic checks while incorrectly
promising a cash refund. A draft for CW-1002 also called the deposit non-refundable and suggested
cancellation was complete. In guarded-first.json, a June-hours answer used the winter schedule,
and the age answer both approved a 14-year-old and stated the electric-bike minimum was 16.

Those are substantive model errors, not formatting issues. The final application therefore renders
money, booking facts and policy extracts from actual tool output. It still lets the LLM choose
tools and complete the tool-calling loop; its final draft is not trusted as customer-facing evidence.
Empty or truncated drafts produce verified excerpts/quotes when available, otherwise a referral.

This favors fidelity over fluent answers. Source excerpts can be indirect or irrelevant, so passing
regex checks is not proof of a useful answer. A stronger model and better context selection are
the next substantive improvements; extra prompts alone did not make this tiny model reliable.

## Additional live checks

Full records are saved in manual-checks.json. These cover Polish questions, missing booking ID,
future-date cancellation and a positive booking lookup. They are separate from the 16-case score.

| Check | Observed behavior | Review |
| --- | --- | --- |
| Polish refund question, CW-1002 | 40 EUR rental + 300 EUR deposit = 340 EUR, original card within five working days; quote only | Correct |
| Polish Saturday-hours question | Correct seasonal hours quoted from the English source, with a Polish heading | Correct facts; source text is not translated |
| Polish capital-city question | Polish staff referral; no general-knowledge answer | Correct scope behavior |
| Refund question with no ID | Asks for the booking ID and provides staff contact | Correct clarification |
| Cancel CW-1002 tomorrow | Generic referral, no invented hypothetical amount; redundantly asks for an ID already supplied | Safe but incomplete; future-date scenarios remain unsupported |
| CW-1001 booking details | Original JSON data, including confirmed status and stored prices | Correct |

All six live checks completed without a CLI crash. The future-date response is a usability
limitation, not evidence that the agent supports hypothetical cancellation dates.
