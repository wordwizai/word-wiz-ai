#!/usr/bin/env pwsh
# Startup script for the backend server

Write-Host "🚀 Starting Phoneme Assistant Backend..." -ForegroundColor Cyan

# Change to backend directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

# Start the server
Write-Host "🔥 Starting uvicorn server on http://localhost:8000" -ForegroundColor Cyan
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
