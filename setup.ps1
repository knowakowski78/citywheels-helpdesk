# Prepare Python and run offline tests. Model download is optional.
param([switch]$DownloadModel)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or newer is required.' }

    $taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $taskPython)) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
    }
    & $taskPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Check the output above.' }

    if ($DownloadModel) {
        & (Join-Path $PSScriptRoot 'start-ollama.ps1') -Pull
    }
    Write-Host 'Ready. With Ollama running, start the agent:'
    Write-Host '.\.venv\Scripts\python.exe -m citywheels'
} finally {
    Pop-Location
}
