# Complete Setup Guide

This guide will help you set up and run the Mutual Funds Platform locally.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **pnpm** - Install with: `npm install -g pnpm`
- **Git** - [Download](https://git-scm.com/)
- **MongoDB Atlas Account** - [Sign up](https://www.mongodb.com/cloud/atlas/register) (free tier available)

## Step 1: Clone and Setup Directory

```powershell
# Navigate to your workspace
cd "c:\MF root folder"

# Verify both folders exist
dir
# You should see: mutual fund/ and mutual-funds-backend/
```

## Step 2: Setup Backend

### 2.1 Install Dependencies

```powershell
cd mutual-funds-backend
npm install
```

### 2.2 Configure Environment

```powershell
# Copy the example file
cp .env.example .env

# Open .env in your editor
code .env
```

Update these required variables:

```env
# REQUIRED: Get from MongoDB Atlas
DATABASE_URL="mongodb+srv://username:password@cluster.mongodb.net/mutual-funds"

# REQUIRED: Generate random secrets
JWT_SECRET="your_64_char_random_string"
JWT_REFRESH_SECRET="your_64_char_random_string"

# REQUIRED: Get from Google Console
GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_client_secret"

# REQUIRED: Server settings
PORT=3002
FRONTEND_URL=http://localhost:5001
```

**How to generate JWT secrets:**

```powershell
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```

### 2.3 Setup MongoDB

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a new cluster (free tier is fine)
3. Create a database user
4. Whitelist your IP (or use 0.0.0.0/0 for development)
5. Get connection string and update DATABASE_URL

### 2.4 Generate Prisma Client

```powershell
npx prisma generate
```

### 2.5 (Optional) Seed Database

```powershell
# Import funds data
npm run import:comprehensive-amfi
```

### 2.6 Start Backend

```powershell
npm run dev
```

Backend should now be running on http://localhost:3002

Test it:

```powershell
curl http://localhost:3002/api/health
```

## Step 3: Setup Frontend

### 3.1 Install Dependencies

```powershell
cd "../mutual fund"
pnpm install
```

### 3.2 Configure Environment

```powershell
# Copy the example file
cp .env.example .env.local

# Open .env.local in your editor
code .env.local
```

Update these variables:

```env
# Backend API URL (NO trailing slash)
NEXT_PUBLIC_API_URL=http://localhost:3002

# Frontend URL
NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001

# Same Google Client ID as backend
NEXT_PUBLIC_GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"

# Optional: Add these later
# NEXT_PUBLIC_GA_MEASUREMENT_ID=your_ga_id
# NEXT_PUBLIC_GEMINI_KEY=your_gemini_key
```

### 3.3 Start Frontend

```powershell
pnpm dev
```

Frontend should now be running on http://localhost:5001

## Step 4: Setup Google OAuth (Required for Sign In)

### 4.1 Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**

### 4.2 Configure URLs

**Authorized JavaScript origins:**

- `http://localhost:5001`
- `http://localhost:3002`

**Authorized redirect URIs:**

- `http://localhost:3002/api/auth/google/callback`
- `http://localhost:5001/auth/success`

### 4.3 Update Environment Variables

Copy the Client ID and Client Secret to:

- Backend `.env` → `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Frontend `.env.local` → `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

## Step 5: Verify Integration

### 5.1 Test Backend APIs

```powershell
# From root folder
.\test-integration.ps1
```

This will test:

- ✅ Backend health
- ✅ Funds API
- ✅ Search API
- ✅ Autocomplete
- ✅ Fund Managers
- ✅ CORS configuration

### 5.2 Test in Browser

1. Open http://localhost:5001
2. You should see the home page
3. Try browsing funds
4. Try searching for a fund
5. Try signing in with Google

## Step 6: Start Both Servers (Quick Start)

For future use, start both servers at once:

```powershell
# From root folder
.\start-dev.ps1
```

This will:

- ✅ Check if ports are available
- ✅ Start backend (port 3002)
- ✅ Start frontend (port 5001)
- ✅ Open both in separate terminal windows

## Common Issues and Solutions

### Issue: Port Already in Use

**Error:** `EADDRINUSE: address already in use :::3002`

**Solution:**

```powershell
# Find process using port
Get-Process -Id (Get-NetTCPConnection -LocalPort 3002).OwningProcess

# Kill the process
Stop-Process -Id <PID> -Force
```

### Issue: MongoDB Connection Failed

**Error:** `MongoServerError: bad auth`

**Solutions:**

1. Check username/password in DATABASE_URL
2. Verify database user exists in MongoDB Atlas
3. Check IP whitelist in MongoDB Atlas
4. Ensure connection string format is correct

### Issue: Module Not Found

**Error:** `Cannot find module '@prisma/client'`

**Solution:**

```powershell
cd mutual-funds-backend
npx prisma generate
npm install
```

### Issue: CORS Error in Browser

**Error:** `Access to fetch at 'http://localhost:3002/api/funds' has been blocked by CORS policy`

**Solutions:**

1. Verify `FRONTEND_URL` in backend `.env` is `http://localhost:5001`
2. Restart backend server after changing .env
3. Clear browser cache
4. Check browser console for actual frontend URL

### Issue: Google OAuth Not Working

**Error:** `redirect_uri_mismatch`

**Solutions:**

1. Add exact redirect URIs to Google Console:
   - `http://localhost:3002/api/auth/google/callback`
   - `http://localhost:5001/auth/success`
2. Verify GOOGLE_CLIENT_ID matches in both frontend and backend
3. Check GOOGLE_CLIENT_SECRET is correct in backend
4. Restart both servers

### Issue: No Funds Data

**Error:** Empty funds list

**Solution:**

```powershell
cd mutual-funds-backend

# Import funds from AMFI
npm run import:comprehensive-amfi

# Or import sample data
npm run db:seed
```

## Optional Services

### Redis (Caching)

Redis improves performance but is optional.

**Install Redis (Windows):**

1. Download from [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
2. Install and start Redis
3. Add to backend `.env`: `REDIS_URL=redis://localhost:6379`

### Google Analytics

Get your tracking ID from [Google Analytics](https://analytics.google.com/)

Add to frontend `.env.local`:

```env
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### Gemini AI (Investment Insights)

Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

Add to frontend `.env.local`:

```env
NEXT_PUBLIC_GEMINI_KEY=your_gemini_key_here
```

## Production Deployment

### Frontend (Vercel)

1. Push code to GitHub
2. Connect repo to Vercel
3. Configure environment variables in Vercel dashboard
4. Deploy

### Backend (Vercel/Railway/Render)

1. Push code to GitHub
2. Connect repo to hosting service
3. Set all environment variables
4. Ensure DATABASE_URL points to production MongoDB
5. Deploy

### Update Google OAuth for Production

Add production URLs to Google Console:

- `https://your-backend.com/api/auth/google/callback`
- `https://your-frontend.com/auth/success`

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Run integration tests: `.\test-integration.ps1`
3. ✅ Test all features in browser
4. ✅ Configure optional services (Redis, GA, Gemini)
5. ✅ Deploy to production

## Getting Help

- Check logs in terminal windows
- Run integration tests
- Review [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for API details
- Check backend logs for detailed errors

## Summary Checklist

- [ ] Node.js 18+ installed
- [ ] pnpm installed
- [ ] MongoDB Atlas account created
- [ ] Backend dependencies installed
- [ ] Backend .env configured
- [ ] Prisma client generated
- [ ] Frontend dependencies installed
- [ ] Frontend .env.local configured
- [ ] Google OAuth credentials created
- [ ] Both servers running
- [ ] Integration tests passing
- [ ] Can browse funds in browser
- [ ] Can sign in with Google

Congratulations! Your Mutual Funds Platform is now running! 🎉
