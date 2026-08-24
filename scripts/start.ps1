param(
    [int]$Port = 8511,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Host "Preparing FinCompiler for first use. This can take a few minutes..."
    & (Join-Path $PSScriptRoot "setup.ps1")
}

$runtimeDir = Join-Path $projectRoot ".fincompiler"
$pidFile = Join-Path $runtimeDir "web-$Port.pid"
$url = "http://127.0.0.1:$Port"
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

function Test-FinCompilerReady {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

$running = $null
if (Test-Path -LiteralPath $pidFile) {
    $savedPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if ($savedPid -match "^\d+$") {
        $running = Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue
    }
}

if (-not $running -and (Test-FinCompilerReady)) {
    throw "Port $Port is already in use by an untracked local app. Close it or run scripts\start.ps1 -Port 8514."
}

if (-not $running) {
    $arguments = @("-m", "streamlit", "run", "apps\web.py", "--server.headless", "true", "--server.port", "$Port")
    $running = Start-Process -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
    Set-Content -LiteralPath $pidFile -Value $running.Id -Encoding ascii
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-FinCompilerReady) {
        $ready = $true
        break
    }
    Start-Sleep -Milliseconds 500
}

if (-not $ready) {
    throw "FinCompiler did not start. Run scripts\setup.ps1 and try again."
}

if (-not $NoBrowser) { Start-Process $url }
Write-Host "FinCompiler is open. Use 'Stop FinCompiler.cmd' when you are finished."
