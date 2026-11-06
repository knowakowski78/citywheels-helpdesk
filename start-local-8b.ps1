# Run the default 8B profile; restore previous environment values on exit.
param([switch]$Evaluate, [string]$Question, [switch]$Trace, [switch]$NoThinking, [switch]$Thinking)
$ErrorActionPreference = 'Stop'
if ($Thinking -and $NoThinking) { throw 'Choose Thinking or NoThinking, not both.' }
$taskPreviousModel = $env:OLLAMA_MODEL
$taskPreviousGpu = $env:OLLAMA_NUM_GPU
$taskPreviousThink = $env:OLLAMA_THINK
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
Push-Location $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot 'start-ollama.ps1') -Cuda
    $env:OLLAMA_MODEL = 'qwen3:8b'
    $env:OLLAMA_NUM_GPU = '-1'
    $env:OLLAMA_THINK = if ($Thinking) { 'true' } else { 'false' }
    if ($Evaluate) {
        $taskReport = if ($Thinking) { 'eval/shared-8b-thinking-results.md' } else { 'eval/shared-8b-fast-results.md' }
        $taskArguments = @('-m', 'eval.run', '--output', $taskReport)
    } else {
        $taskArguments = @('-m', 'citywheels')
        if ($Question) { $taskArguments += $Question }
        if ($Trace) { $taskArguments += '--trace' }
    }
    & $taskPython @taskArguments
    if ($LASTEXITCODE -ne 0) { Write-Warning "Command exited with code $LASTEXITCODE; inspect the report or error." }
} finally {
    $env:OLLAMA_MODEL = $taskPreviousModel
    $env:OLLAMA_NUM_GPU = $taskPreviousGpu
    $env:OLLAMA_THINK = $taskPreviousThink
    Pop-Location
}
