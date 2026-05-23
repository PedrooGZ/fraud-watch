$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Resolve-Path (Join-Path $scriptDir "..")

Set-Location $backendDir
$env:PYTHONPATH = $backendDir.Path

& ".\.venv\Scripts\python.exe" "scripts\init_db.py"