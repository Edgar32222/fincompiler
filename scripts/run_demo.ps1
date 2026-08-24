$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = ".\.venv\Scripts\python.exe"

& $pythonExe -m fincompiler.cli generate-demo "demo\generated-local" --seed 7301 --invoices 100 --anomalies split_posting amount_mismatch missing_gl unmatched_gl credit_note
& $pythonExe -m fincompiler.cli run "demo\generated-local" --output "output\demo-run" --memory "mappings\demo-memory.json"
& $pythonExe -m streamlit run "apps\web.py"

