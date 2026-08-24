$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath ".venv")) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if ($launcher) {
        & $launcher.Source -3.12 -m venv .venv
    } elseif (Test-Path -LiteralPath $codexPython) {
        & $codexPython -m venv .venv
    } elseif ($pythonCommand -and -not $pythonCommand.Source.Contains("WindowsApps")) {
        & $pythonCommand.Source -m venv .venv
    } else {
        throw "Python 3.11+ was not found. Install Python and run this script again."
    }
}

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    throw "The virtual environment could not be created. Remove an incomplete .venv folder and retry."
}

$venvPython = ".\.venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed with exit code $LASTEXITCODE" }
& $venvPython -m pip install ".[dev,excel,web]"
if ($LASTEXITCODE -ne 0) { throw "FinCompiler installation failed with exit code $LASTEXITCODE" }
& $venvPython -m pytest -q -p no:cacheprovider --basetemp ".setup-test-temp"
if ($LASTEXITCODE -ne 0) { throw "FinCompiler tests failed with exit code $LASTEXITCODE" }
Write-Host "FinCompiler is ready. Run scripts\run_demo.ps1"
