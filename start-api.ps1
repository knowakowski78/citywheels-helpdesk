# Explicit hosted backup. The normal python -m citywheels command stays local.
param([switch]$Evaluate, [string]$Question, [switch]$Trace, [double]$RequestInterval = 30)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
$taskEnvFile = Join-Path $PSScriptRoot '.env.groq'
if (-not (Test-Path -LiteralPath $taskEnvFile)) {
    throw 'Create .env.groq with GROQ_API_KEY and GROQ_MODEL first; see API-BACKUP.md.'
}
if ($Evaluate) {
    $taskArguments = @('-m', 'eval.run', '--provider', 'groq', '--env-file', $taskEnvFile,
                       '--request-interval', $RequestInterval.ToString([Globalization.CultureInfo]::InvariantCulture))
} else {
    $taskArguments = @('-m', 'citywheels', '--provider', 'groq', '--env-file', $taskEnvFile)
    if ($Question) { $taskArguments += $Question }
    if ($Trace) { $taskArguments += '--trace' }
}
Push-Location $PSScriptRoot
try {
    & $taskPython @taskArguments
    $taskExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($taskExitCode -ne 0) { Write-Warning "The command finished with exit code $taskExitCode. Inspect its output and evaluation report." }
