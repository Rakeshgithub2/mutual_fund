# Quick script to generate secure secrets for production

Write-Host "==================================="
Write-Host "🔐 Generating Secure Secrets"
Write-Host "==================================="
Write-Host ""

Write-Host "JWT_SECRET (for authentication):"
$jwt_secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host $jwt_secret
Write-Host ""

Write-Host "JWT_REFRESH_SECRET (for refresh tokens):"
$jwt_refresh = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host $jwt_refresh
Write-Host ""

Write-Host "==================================="
Write-Host "✅ Copy these values to Vercel"
Write-Host "Dashboard → Settings → Environment Variables"
Write-Host "==================================="
