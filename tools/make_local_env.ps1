# PowerShell script to set up local development environment
# Author: Marcus A. Sanchez
# Date: 2025-11-12

Write-Host "Setting up Oraculus DI Auditor local environment..." -ForegroundColor Green

# Create virtual environment
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Cyan
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Create data directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\sources" | Out-Null
New-Item -ItemType Directory -Force -Path "data\cases" | Out-Null
New-Item -ItemType Directory -Force -Path "data\statutes" | Out-Null
New-Item -ItemType Directory -Force -Path "data\vectors" | Out-Null

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Run tests: pytest" -ForegroundColor White
Write-Host "2. Run linter: black . && ruff check ." -ForegroundColor White
Write-Host "3. Import examples: .\tools\import_examples.sh" -ForegroundColor White
Write-Host "4. Run ingestion: python -m oraculus_di_auditor.cli ingest" -ForegroundColor White
