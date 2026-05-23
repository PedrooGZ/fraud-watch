$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Resolve-Path (Join-Path $scriptDir "..")

Set-Location $backendDir
.\.venv\Scripts\python -m alembic -c alembic.ini upgrade head
