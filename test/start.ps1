# Chatumba PowerShell Launcher
param([switch]$SkipChecks)

Clear-Host

Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "                         CHATUMBA                              " -ForegroundColor Magenta
Write-Host "                AI-companion with soul                         " -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

if (-not $SkipChecks) {
    Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
    $pythonCheck = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python not found! Install Python 3.10+" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
    Write-Host "Python found" -ForegroundColor Green

    Write-Host ""
    Write-Host "[2/4] Checking dependencies..." -ForegroundColor Cyan
    python -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installation failed" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit
        }
    }
    Write-Host "Dependencies ready" -ForegroundColor Green

    Write-Host ""
    Write-Host "[3/4] Checking .env..." -ForegroundColor Cyan
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env template..." -ForegroundColor Yellow
        "OPENROUTER_API_KEY=your_key`nEMBEDDING_API_KEY=your_key`nTELEGRAM_BOT_TOKEN=your_token" | Out-File ".env"
        Write-Host "Configure API keys in .env file" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
    Write-Host ".env file found" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/4] Starting Chatumba..." -ForegroundColor Cyan
Write-Host "Server starting..." -ForegroundColor Green
Write-Host "Web interface: http://localhost:6666" -ForegroundColor Blue
Write-Host "Soul panel: http://localhost:6666/soul.html" -ForegroundColor Magenta
Write-Host ""

if (Test-Path "backend") {
    Set-Location backend
    python main.py
} else {
    Write-Host "Backend folder not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
