param([int]$Port = 8511)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot ".fincompiler\web-$Port.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "FinCompiler is not running."
    exit 0
}

$savedPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
if ($savedPid -notmatch "^\d+$") {
    throw "The FinCompiler process record is invalid."
}

$process = Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue
if ($process) {
    $expectedPython = (Resolve-Path -LiteralPath (Join-Path $projectRoot ".venv\Scripts\python.exe")).Path
    $actualPath = $process.Path
    if ($actualPath -ne $expectedPython) {
        throw "The recorded process is not FinCompiler; it was not stopped."
    }
    Stop-Process -Id $process.Id
}

Remove-Item -LiteralPath $pidFile -Force
Write-Host "FinCompiler has stopped."
