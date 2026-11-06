# Run from PowerShell: .\start-ollama.ps1
# Supports an installed Ollama or the portable runtime prepared beside outputs/.
param([switch]$Pull, [string]$Model = 'qwen3:8b', [switch]$Cuda, [switch]$Vulkan)
$ErrorActionPreference = 'Stop'
if ($Cuda -and $Vulkan) { throw 'Choose CUDA or Vulkan, not both.' }
$taskWorkspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskPortableExe = Join-Path $taskWorkspace 'work\ollama-runtime\ollama.exe'
$taskInstalled = Get-Command ollama -ErrorAction SilentlyContinue
$taskUsingPortable = Test-Path -LiteralPath $taskPortableExe
if ($taskUsingPortable) {
    $taskExe = $taskPortableExe
    $env:OLLAMA_MODELS = Join-Path $taskWorkspace 'work\ollama-models'
} elseif ($taskInstalled) {
    $taskExe = $taskInstalled.Source
} else {
    throw 'Ollama is missing. Install it from https://ollama.com/download/windows first.'
}

$taskLogDir = if ($taskUsingPortable) { Join-Path $taskWorkspace 'work\ollama-logs' } else { Join-Path $PSScriptRoot 'work\ollama-logs' }
New-Item -ItemType Directory -Force -Path $taskLogDir | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_VULKAN = if ($Vulkan) { '1' } else { '0' }
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
try {
    $taskVersion = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 3
    Write-Host "Ollama is already running: $($taskVersion.version)"
} catch {
    $taskServer = Start-Process -FilePath $taskExe -ArgumentList 'serve' -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $taskLogDir 'server.stdout.log') `
        -RedirectStandardError (Join-Path $taskLogDir 'server.stderr.log')
    $taskReady = $false
    for ($taskAttempt = 0; $taskAttempt -lt 15; $taskAttempt++) {
        Start-Sleep -Seconds 1
        if ($taskServer.HasExited) { throw "Ollama exited. See $taskLogDir" }
        try {
            $taskVersion = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
            $taskReady = $true
            break
        } catch { }
    }
    if (-not $taskReady) { throw "Ollama did not become ready. See $taskLogDir" }
    Write-Host "Started Ollama $($taskVersion.version), PID $($taskServer.Id). Logs: $taskLogDir"
}
Write-Host "Executable: $taskExe"
if ($Pull) {
    & $taskExe pull $Model
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
} else {
    Write-Host 'To download the model too: .\start-ollama.ps1 -Pull'
}
