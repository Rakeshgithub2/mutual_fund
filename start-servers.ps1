# Start Both Servers - Mutual Funds Portal

Write-Host "`n=== STARTING MUTUAL FUNDS PORTAL ===" -ForegroundColor Cyan
Write-Host ""

# Kill any existing Node processes
Write-Host "Stopping existing servers..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Start Backend in new window
Write-Host "Starting Backend (Port 3002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\MF root folder\mutual-funds-backend'; npm run dev" -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 5

# Start Frontend in new window  
Write-Host "Starting Frontend (Port 5001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\MF root folder\mutual fund'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "✅ Both servers starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:3002" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
