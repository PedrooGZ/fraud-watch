$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Resolve-Path (Join-Path $scriptDir "..")
$rootDir = Resolve-Path (Join-Path $backendDir "..")
$composeFile = Join-Path $rootDir "docker-compose.yml"

if (-not (Test-Path $composeFile)) {
    Write-Error "No se encontro docker-compose.yml en $rootDir"
    exit 1
}

docker compose -f $composeFile up -d postgres
