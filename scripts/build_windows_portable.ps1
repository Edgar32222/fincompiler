$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Run scripts\setup.ps1 before building the Windows package."
}

$distDir = Join-Path $projectRoot "dist-windows"
$workDir = Join-Path $projectRoot "build-windows"
$specDir = Join-Path $projectRoot "desktop"

& $pythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name FinCompiler `
    --distpath $distDir `
    --workpath $workDir `
    --specpath $specDir `
    --icon (Join-Path $projectRoot "assets\brand\fincompiler-avatar.png") `
    --add-data "$projectRoot\apps;apps" `
    --add-data "$projectRoot\demo;demo" `
    --add-data "$projectRoot\.streamlit;.streamlit" `
    --collect-all fincompiler `
    --collect-all streamlit `
    --collect-all altair `
    --collect-all pydeck `
    --collect-all openpyxl `
    --copy-metadata fincompiler `
    --copy-metadata streamlit `
    (Join-Path $projectRoot "desktop\launcher.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$portableDir = Join-Path $distDir "FinCompiler"
Copy-Item -LiteralPath (Join-Path $projectRoot "desktop\README-FIRST.txt") -Destination (Join-Path $portableDir "README-FIRST.txt") -Force
Write-Host "Portable build ready at $portableDir"
