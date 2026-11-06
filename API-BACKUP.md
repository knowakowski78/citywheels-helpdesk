# Optional Groq backup

The default runs locally with Ollama. To use the hosted backup, select Groq explicitly.
It uses `openai/gpt-oss-120b`, the same tool-calling loop and the same policy checks.

## Key setup

Create a key in the [Groq console](https://console.groq.com/keys), then create `.env.groq`
in the project folder:

```dotenv
GROQ_API_KEY=your_actual_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

This file is ignored by Git. Do not commit it or include it in an archive.
The loader accepts only these two names; non-empty environment variables take precedence.
Do not copy the whole `.env.example` here, since it also contains Ollama settings.

## Run

```powershell
.\start-api.ps1
.\start-api.ps1 -Question 'How much is an e-bike for a whole day?' -Trace
.\start-api.ps1 -Evaluate
```

Or call Python directly:

```powershell
.\.venv\Scripts\python.exe -m citywheels --provider groq --env-file .env.groq "What is my refund for CW-1002?" --trace
```

Evaluation writes `eval/groq-results.md` and `.json`, leaving the local report intact.
It spaces requests by 30 seconds by default. Use `-RequestInterval` with the evaluation launcher,
or `--request-interval` with Python, to choose a value from 0 to 60 seconds.

Check model access, plan and quotas in the [Groq console](https://console.groq.com/docs/rate-limits).
A question can require several API requests. Quota and authentication errors stop the run;
transport failures get one retry. There is no automatic provider or paid-model switch.

When Groq is selected, the prompt, question, tool definitions and tool results go to Groq.
Tools and refund calculations still run locally. The key goes in the HTTPS authorization header.
The supplied bookings are fictional; real customer data would need a separate privacy review.

The saved full API run scored 14/16 before the age/weather fixes. Both failed cases passed a
targeted rerun. A full run after the shared-policy refactor has not been recorded.
See [eval/README.md](eval/README.md) for reports.
