# Run the smaller model on CPU with the same policy checks.
param([switch]$Evaluate, [string]$Question, [switch]$Trace)
$ErrorActionPreference = 'Stop'
$taskPreviousModel = $env:OLLAMA_MODEL
$taskPreviousGpu = $env:OLLAMA_NUM_GPU
$taskPreviousThink = $env:OLLAMA_THINK
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
Push-Location $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot 'start-ollama.ps1')
    $env:OLLAMA_MODEL = 'qwen3:0.6b'
    $env:OLLAMA_NUM_GPU = '0'
    $env:OLLAMA_THINK = 'true'
    $taskArguments = if ($Evaluate) { @('-m','eval.run','--output','eval/shared-small-results.md') } else { @('-m','citywheels') }
    if (-not $Evaluate) {
        if ($Question) { $taskArguments += $Question }
        if ($Trace) { $taskArguments += '--trace' }
    }
    & $taskPython @taskArguments
    if ($LASTEXITCODE -ne 0) { Write-Warning "Command exited with code $LASTEXITCODE; inspect its output/report." }
} finally {
    $env:OLLAMA_MODEL = $taskPreviousModel
    $env:OLLAMA_NUM_GPU = $taskPreviousGpu
    $env:OLLAMA_THINK = $taskPreviousThink
    Pop-Location
}
