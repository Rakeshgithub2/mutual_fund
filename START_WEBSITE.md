# 🚀 Website Startup Guide

Quick guide to run the Mutual Funds website in **LOCAL** or **PRODUCTION** mode.

---

## 📋 Prerequisites

- Node.js 18+ installed
- MongoDB connection configured
- Backend service available (local or Vercel)

---

## 🏠 Option 1: Run Locally (Development)

### **Uses:**

- Frontend: `http://localhost:5001`
- Backend: `http://localhost:3002`

### **Steps:**

1. **Configure Environment (One-time)**

   ```powershell
   cd "c:\MF root folder\mutual fund"

   # Update .env file to use localhost
   # NEXT_PUBLIC_API_URL=http://localhost:3002
   # NEXT_PUBLIC_BACKEND_URL=http://localhost:3002
   # NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001
   ```

2. **Start Backend Server**

   ```powershell
   cd "c:\MF root folder\mutual-funds-backend"
   node server.js
   ```

   ✅ Backend should be running on port 3002

3. **Start Frontend (New Terminal)**

   ```powershell
   cd "c:\MF root folder\mutual fund"
   npm run dev
   ```

   ✅ Frontend should be running on port 5001

4. **Access Website**
   ```
   🌐 Open: http://localhost:5001
   ```

---

## ☁️ Option 2: Run with Production Backend (Vercel)

### **Uses:**

- Frontend: `http://localhost:5001` (local)
- Backend: `https://your-backend.vercel.app` (production)

### **Steps:**

1. **Update Environment Variables**

   ```powershell
   cd "c:\MF root folder\mutual fund"

   # Edit .env file and change:
   # NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
   # NEXT_PUBLIC_BACKEND_URL=https://your-backend.vercel.app
   # NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001
   ```

2. **Start Frontend Only**

   ```powershell
   cd "c:\MF root folder\mutual fund"
   npm run dev
   ```

   ✅ Frontend connects to production backend

3. **Access Website**
   ```
   🌐 Open: http://localhost:5001
   ```

---

## 🎯 Quick Start Scripts

### PowerShell Script for Local Development

```powershell
# Save as: start-local.ps1
Write-Host "🚀 Starting Mutual Funds Platform (LOCAL MODE)" -ForegroundColor Cyan

# Start Backend
Write-Host "`n📡 Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\MF root folder\mutual-funds-backend'; node server.js"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "`n🌐 Starting Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\MF root folder\mutual fund'; npm run dev"

Write-Host "`n✅ Both servers starting..." -ForegroundColor Green
Write-Host "   Backend:  http://localhost:3002" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5001" -ForegroundColor White
Write-Host "`nPress any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

### PowerShell Script for Production Backend

```powershell
# Save as: start-with-production.ps1
Write-Host "🚀 Starting Mutual Funds Platform (PRODUCTION BACKEND)" -ForegroundColor Cyan

# Check if .env is configured for production
$envFile = Get-Content "c:\MF root folder\mutual fund\.env" -Raw
if ($envFile -match "localhost:3002") {
    Write-Host "`n⚠️  WARNING: .env still points to localhost!" -ForegroundColor Red
    Write-Host "   Update NEXT_PUBLIC_API_URL to your Vercel backend URL" -ForegroundColor Yellow
    Write-Host "`nContinue anyway? (Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "Y" -and $response -ne "y") {
        exit
    }
}

# Start Frontend only
Write-Host "`n🌐 Starting Frontend (connecting to production backend)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\MF root folder\mutual fund'; npm run dev"

Write-Host "`n✅ Frontend starting..." -ForegroundColor Green
Write-Host "   Frontend: http://localhost:5001" -ForegroundColor White
Write-Host "   Backend:  [Production Vercel URL]" -ForegroundColor White
Write-Host "`nPress any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

---

## 🔧 Environment Variables Reference

### For Local Development:

```env
NEXT_PUBLIC_API_URL=http://localhost:3002
NEXT_PUBLIC_BACKEND_URL=http://localhost:3002
NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001
```

### For Production Backend:

```env
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
NEXT_PUBLIC_BACKEND_URL=https://your-backend.vercel.app
NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001
```

### For Full Production Deployment:

```env
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
NEXT_PUBLIC_BACKEND_URL=https://your-backend.vercel.app
NEXT_PUBLIC_FRONTEND_URL=https://your-frontend.vercel.app
```

---

## 🐛 Troubleshooting

### Backend Not Responding

```powershell
# Check if port 3002 is in use
netstat -ano | findstr :3002

# Kill process if needed
taskkill /PID <PID> /F
```

### Frontend Can't Connect to Backend

1. Verify `.env` file has correct `NEXT_PUBLIC_API_URL`
2. Check backend is running (visit `http://localhost:3002/health`)
3. Clear Next.js cache: `rm -rf .next`
4. Restart frontend: `npm run dev`

### CORS Errors

- Ensure backend CORS is configured to allow frontend origin
- Check `FRONTEND_URL` in backend `.env` matches frontend URL

---

## 📝 Quick Reference

| Mode           | Frontend       | Backend        | Use Case               |
| -------------- | -------------- | -------------- | ---------------------- |
| **Local Dev**  | localhost:5001 | localhost:3002 | Full local development |
| **Hybrid**     | localhost:5001 | Vercel URL     | Test with prod data    |
| **Production** | Vercel URL     | Vercel URL     | Live deployment        |

---

## 🎬 One-Command Startup

### Local Mode:

```powershell
.\start-local.ps1
```

### Production Backend Mode:

```powershell
.\start-with-production.ps1
```

---

**Need help?** Check the main [README.md](README.md) for detailed setup instructions.
