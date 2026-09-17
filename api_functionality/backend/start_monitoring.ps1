$ErrorActionPreference = "Stop"

$backendRoot = $PSScriptRoot
$pythonPath = Join-Path $backendRoot "..\.venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Python virtual environment was not found at $pythonPath"
}

Push-Location -LiteralPath $backendRoot

try {
    Write-Host "Starting PostgreSQL and Redis..."
    & docker compose up -d postgres redis

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose could not start PostgreSQL and Redis."
    }

    Write-Host "Applying database migrations..."
    & $pythonPath -m alembic upgrade head

    if ($LASTEXITCODE -ne 0) {
        throw "Alembic could not apply the database migrations."
    }

    Write-Host "Starting the scheduler and one monitor worker..."
    Write-Host "Keep this terminal open. Press Ctrl+C to stop monitoring."
    & $pythonPath -u -m app.monitoring_main

    if ($LASTEXITCODE -ne 0) {
        throw "The monitoring engine exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
    Write-Host "Monitoring engine stopped."
}
