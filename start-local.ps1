# Start Mutual Funds Platform (LOCAL MODE)
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  MUTUAL FUNDS PLATFORM - LOCAL DEVELOPMENT" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
$rootPath = "C:\MF root folder"
if (-not (Test-Path $rootPath)) {
    Write-Host "Error: Root folder not found at $rootPath" -ForegroundColor Red
    Write-Host "   Please update the script with correct path." -ForegroundColor Yellow
    pause
    exit 1
}

# Step 1: Start Backend Server
Write-Host "Step 1: Starting Backend Server (Port 3002)..." -ForegroundColor Yellow
Write-Host "   Location: mutual-funds-backend" -ForegroundColor Gray

$backendPath = Join-Path $rootPath "mutual-funds-backend"
if (Test-Path $backendPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; Write-Host 'BACKEND SERVER' -ForegroundColor Green; Write-Host '===================' -ForegroundColor Green; Write-Host 'Starting on http://localhost:3002...' -ForegroundColor Cyan; node src/app.js"
    Write-Host "Backend terminal opened" -ForegroundColor Green
} else {
    Write-Host "Backend folder not found!" -ForegroundColor Red
    pause
    exit 1
}

# Wait for backend to initialize
Write-Host ""
Write-Host "⏳ Waiting 3 seconds for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Step 2: Start Frontend
Write-Host ""
Write-Host "Step 2: Starting Frontend (Port 5001)..." -ForegroundColor Yellow
Write-Host "   Location: mutual fund" -ForegroundColor Gray

$frontendPath = Join-Path $rootPath "mutual fund"
if (Test-Path $frontendPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; Write-Host 'FRONTEND SERVER' -ForegroundColor Blue; Write-Host '===================' -ForegroundColor Blue; Write-Host 'Starting on http://localhost:5001...' -ForegroundColor Cyan; npm run dev"
    Write-Host "Frontend terminal opened" -ForegroundColor Green
} else {
    Write-Host "Frontend folder not found!" -ForegroundColor Red
    pause
    exit 1
}

# Summary
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  SERVERS STARTING..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:3002" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5001" -ForegroundColor White
Write-Host ""
Write-Host "Check the opened terminal windows for status" -ForegroundColor Yellow
Write-Host ""
Write-Host "Open your browser to: http://localhost:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
