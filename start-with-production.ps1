# 🚀 Start Mutual Funds Platform (PRODUCTION BACKEND MODE)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  MUTUAL FUNDS PLATFORM - PRODUCTION BACKEND MODE" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  This mode runs:" -ForegroundColor Yellow
Write-Host "   - Frontend: LOCAL (http://localhost:5001)" -ForegroundColor White
Write-Host "   - Backend:  PRODUCTION (Vercel)" -ForegroundColor White
Write-Host ""

# Check if in correct directory
$rootPath = "C:\MF root folder"
$frontendPath = Join-Path $rootPath "mutual fund"
$envFile = Join-Path $frontendPath ".env"

if (-not (Test-Path $rootPath)) {
    Write-Host "❌ Error: Root folder not found at $rootPath" -ForegroundColor Red
    Write-Host "   Please update the script with correct path." -ForegroundColor Yellow
    pause
    exit 1
}

# Check if .env exists
if (-not (Test-Path $envFile)) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "   Expected at: $envFile" -ForegroundColor Yellow
    Write-Host "   Please create .env file first." -ForegroundColor Yellow
    pause
    exit 1
}

# Verify environment configuration
Write-Host "🔍 Checking environment configuration..." -ForegroundColor Yellow
$envContent = Get-Content $envFile -Raw

# Check for localhost in API URL
if ($envContent -match "NEXT_PUBLIC_API_URL=http://localhost") {
    Write-Host ""
    Write-Host "⚠️  WARNING: API URL is still pointing to localhost!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Current: NEXT_PUBLIC_API_URL=http://localhost:3002" -ForegroundColor White
    Write-Host "   Expected: NEXT_PUBLIC_API_URL=https://your-backend.vercel.app" -ForegroundColor Green
    Write-Host ""
    Write-Host "   This means the frontend will try to connect to LOCAL backend," -ForegroundColor Yellow
    Write-Host "   not the production Vercel backend." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Continue anyway (if you want local backend)" -ForegroundColor White
    Write-Host "  2. Exit and update .env file with Vercel URL" -ForegroundColor White
    Write-Host ""
    Write-Host "Continue with localhost backend? (Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host ""
        Write-Host "📝 To update, edit this file:" -ForegroundColor Cyan
        Write-Host "   $envFile" -ForegroundColor White
        Write-Host ""
        Write-Host "   Change NEXT_PUBLIC_API_URL to your Vercel backend URL" -ForegroundColor Gray
        pause
        exit 0
    }
    
    Write-Host ""
    Write-Host "⚠️  Continuing with LOCALHOST backend..." -ForegroundColor Yellow
    Write-Host "   Make sure backend server is running on port 3002!" -ForegroundColor Red
    Write-Host ""
    Start-Sleep -Seconds 2
} else {
    # Extract the Vercel URL
    if ($envContent -match "NEXT_PUBLIC_API_URL=(https://[^\s]+)") {
        $backendUrl = $matches[1]
        Write-Host "✅ Production backend configured: $backendUrl" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not detect backend URL in .env" -ForegroundColor Yellow
    }
}

# Start Frontend
Write-Host ""
Write-Host "🌐 Starting Frontend (Port 5001)..." -ForegroundColor Yellow
Write-Host "   Location: mutual fund" -ForegroundColor Gray
Write-Host ""

if (Test-Path $frontendPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
        `$host.UI.RawUI.WindowTitle = 'Frontend Server - Port 5001 (Production Backend)'
        Write-Host '💻 FRONTEND SERVER - PRODUCTION BACKEND MODE' -ForegroundColor Blue
        Write-Host '=============================================' -ForegroundColor Blue
        Write-Host ''
        cd '$frontendPath'
        
        # Show backend URL
        `$env:content = Get-Content .env -Raw
        if (`$env:content -match 'NEXT_PUBLIC_API_URL=([^\r\n]+)') {
            Write-Host 'Backend URL: ' -NoNewline -ForegroundColor Yellow
            Write-Host `$matches[1] -ForegroundColor White
        }
        
        Write-Host 'Frontend URL: http://localhost:5001' -ForegroundColor Cyan
        Write-Host ''
        npm run dev
"@
    Write-Host "✅ Frontend terminal opened" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend folder not found!" -ForegroundColor Red
    pause
    exit 1
}

# Summary
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  ✅ FRONTEND STARTING (PRODUCTION BACKEND MODE)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Configuration:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5001 (Local)" -ForegroundColor White
Write-Host "   Backend:  [Check .env file for Vercel URL]" -ForegroundColor White
Write-Host ""
Write-Host "📝 Check the opened terminal window for:" -ForegroundColor Yellow
Write-Host "   - Backend URL being used" -ForegroundColor Gray
Write-Host "   - Frontend startup status" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Open your browser to: http://localhost:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
