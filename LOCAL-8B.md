# Local model options

Qwen3 8B is the default. Download it with `ollama pull qwen3:8b`, then run:

```powershell
.\start-local-8b.ps1
.\start-local-8b.ps1 -Question 'What is my refund for CW-1002?' -Trace
.\start-local-8b.ps1 -Evaluate
```

The launcher selects automatic GPU offload and disables thinking. Add `-Thinking` to try the
slower reasoning mode. It restores the previous model, GPU and thinking settings on exit.
Backend selection applies when starting Ollama; it does not reconfigure an existing server.

For the smaller CPU profile:

```powershell
ollama pull qwen3:0.6b
.\start-local-small.ps1
.\start-local-small.ps1 -Evaluate
```

This selects 0.6B, CPU execution and thinking enabled. Both profiles use the same policy checks.
Evaluation writes separate `shared-8b-fast-results.*` and `shared-small-results.*` reports.
The generic `python -m eval.run` command writes `eval/results.*` by default.

## Test machine

The recorded 8B run used an RTX 3060 Laptop GPU with 6 GB VRAM. CUDA 12 worked, with 27 of
37 layers on the GPU. CUDA 13 failed during warm-up. Runtime libraries and model weights are
outside the source folder and are not part of the submission; no GPU driver was changed.

`start-ollama.ps1` supports either an installed Ollama or the portable runtime in this workspace's
`work` folder. Reviewers should use their own Ollama installation. `-Pull` downloads the selected
model; `-Vulkan` is an optional server startup setting.
