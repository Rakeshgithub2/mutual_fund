# Start both frontend and backend servers
# Run this from the root folder

Write-Host "Starting Mutual Funds Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if ports are available
$backendPort = 3002
$frontendPort = 5001

Write-Host "Checking ports..." -ForegroundColor Yellow
$backendInUse = Get-NetTCPConnection -LocalPort $backendPort -ErrorAction SilentlyContinue
$frontendInUse = Get-NetTCPConnection -LocalPort $frontendPort -ErrorAction SilentlyContinue

if ($backendInUse) {
    Write-Host "Port $backendPort (backend) is already in use" -ForegroundColor Red
    Write-Host "   Kill the process or use a different port" -ForegroundColor Yellow
    exit 1
}

if ($frontendInUse) {
    Write-Host "Port $frontendPort (frontend) is already in use" -ForegroundColor Red
    Write-Host "   Kill the process or use a different port" -ForegroundColor Yellow
    exit 1
}

Write-Host "Ports are available" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "Starting Backend (Port $backendPort)..." -ForegroundColor Cyan
$backendPath = Join-Path $PSScriptRoot "mutual-funds-backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host 'Backend Server' -ForegroundColor Green; npm run dev"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting Frontend (Port $frontendPort)..." -ForegroundColor Cyan
$frontendPath = Join-Path $PSScriptRoot "mutual fund"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host 'Frontend Server' -ForegroundColor Blue; pnpm dev"

Write-Host ""
Write-Host "Servers starting..." -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:$backendPort" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "   - Frontend and backend are running in separate windows" -ForegroundColor White
Write-Host "   - Close each window to stop the respective server" -ForegroundColor White
Write-Host "   - Check logs in each window for errors" -ForegroundColor White
Write-Host ""
Write-Host "Ready! Open http://localhost:$frontendPort in your browser" -ForegroundColor Green
