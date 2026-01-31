# Vercel Deployment Guide - Complete Fix

## Problems Identified ✅

1. **Backend API returning empty data** - Filter by `isActive: true` but 0/14,216 funds have this field ✅ FIXED
2. **Frontend pointing to localhost** - Environment variables not set in Vercel ⚠️ NEEDS ACTION
3. **Google OAuth error** - Function import issue ✅ FIXED

---

## Backend Fixes Applied ✅

### 1. Fund Controller - Remove isActive Filter

**File**: `mutual-funds-backend/api/controllers/fund.controller.ts`

Changed from:

```typescript
const filter: any = { isActive: true }; // This returned 0 results!
```

To:

```typescript
const filter: any = {};
// Only filter by isActive if funds actually have this field
const sampleFund = await collection.findOne({});
if (sampleFund && "isActive" in sampleFund) {
  filter.isActive = true;
}
```

### 2. Google Auth Handler - Add Debug Info

**File**: `mutual-funds-backend/api/google.ts`

Added validation to check if `AuthController.googleAuth` exists before calling it.

---

## Frontend - Vercel Environment Variables ⚠️ ACTION REQUIRED

### Step 1: Go to Vercel Dashboard

1. Visit: https://vercel.com/dashboard
2. Select your project: **mutual-fun-frontend-osed**
3. Go to **Settings** → **Environment Variables**

### Step 2: Add/Update These Variables

**CRITICAL - These MUST be set:**

```bash
# Backend API URL (NO trailing slash)
NEXT_PUBLIC_API_URL=https://mutualfun-backend.vercel.app

# Google OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com

# Google Analytics (if you have it)
NEXT_PUBLIC_GA_MEASUREMENT_ID=your_ga_id_here
```

**Environment**: Select **Production, Preview, Development** (all three)

### Step 3: Verify Current Settings

Run this to check what your production build is using:

```bash
# Check .env.production file
cat "c:\MF root folder\mutual fund\.env.production"
```

Current .env.production:

```
NEXT_PUBLIC_API_URL=https://mutualfun-backend.vercel.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com
```

✅ Looks correct! But Vercel ignores local .env files - you MUST set them in Vercel dashboard.

---

## Backend - Vercel Environment Variables ⚠️ ACTION REQUIRED

### Step 1: Go to Backend Project

1. Visit: https://vercel.com/dashboard
2. Select: **mutualfun-backend**
3. Go to **Settings** → **Environment Variables**

### Step 2: Verify These Are Set

**CRITICAL:**

```bash
# MongoDB Atlas Connection
DATABASE_URL=mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority&appName=mutualfunds

# JWT Secrets
JWT_SECRET=84924af5b7ba7506e46ef5466c2fc37cb8bc0cb2511a496a027ff0a1d4649b0f9b89daa7888155d67a3e2fc371ce23b5848cf6d6a90358ba94956edca6eb12b8
JWT_REFRESH_SECRET=3980022e14191408a2270e41724c8416bb1a782e34986256519ffe3b1706b4c74cf79c938a0fb1870535b200ccbd8e74ae742560ca56910e99ae92746e961c14

# Frontend URL
FRONTEND_URL=https://mutual-fun-frontend-osed.vercel.app

# Allowed Origins
ALLOWED_ORIGINS=https://mutual-fun-frontend-osed.vercel.app,http://localhost:5001

# Google OAuth
GOOGLE_CLIENT_ID=336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://mutualfun-backend.vercel.app/api/auth/google/callback

# Redis (if using)
REDIS_URL=redis://default:HP9HMJuppPHiOKV5VGKf8Kpl6RZ7XlEU@redis-15749.c89.us-east-1-3.ec2.cloud.redislabs.com:15749

# Email (Resend)
RESEND_API_KEY=re_XeWNNhD8_2MX5QgyXSPUTkxUHRYKosddP
FROM_EMAIL=onboarding@resend.dev

# RapidAPI (Yahoo Finance)
RAPIDAPI_KEY=90c72add46mshb5e4256d7aaae60p10c1fejsn41e66ecee4ab
RAPIDAPI_HOST=apidojo-yahoo-finance-v1.p.rapidapi.com

# Node Environment
NODE_ENV=production
```

---

## Google OAuth Configuration ⚠️ ACTION REQUIRED

### Update Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID: `336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com`
3. Add these **Authorized JavaScript origins**:

   ```
   https://mutual-fun-frontend-osed.vercel.app
   http://localhost:5001
   ```

4. Add these **Authorized redirect URIs**:

   ```
   https://mutual-fun-frontend-osed.vercel.app/auth/callback
   https://mutualfun-backend.vercel.app/api/auth/google/callback
   http://localhost:5001/auth/callback
   ```

5. Click **Save**

---

## Deployment Steps

### 1. Deploy Backend (with fixes)

```bash
cd "c:\MF root folder\mutual-funds-backend"

# Commit the fixes
git add .
git commit -m "fix: Remove isActive filter and fix Google OAuth handler"
git push origin main
```

Vercel will auto-deploy when you push to main.

### 2. Verify Backend Deployment

```bash
# Test funds API (should return data now)
curl https://mutualfun-backend.vercel.app/api/funds?limit=3

# Should return:
# {"success":true,"data":[...14216 funds...],"pagination":{...}}
```

### 3. Deploy Frontend (no code changes needed, just env vars)

```bash
cd "c:\MF root folder\mutual fund"

# Trigger redeploy after setting env vars in Vercel dashboard
# Option 1: Make a small change and push
git commit --allow-empty -m "trigger redeploy with correct env vars"
git push origin main

# Option 2: Use Vercel CLI
vercel --prod
```

---

## Testing After Deployment

### Test 1: Backend Health

```bash
curl https://mutualfun-backend.vercel.app/api/health
```

Expected:

```json
{
  "message": "Minimal test working!",
  "env": {
    "hasDatabase": true,
    "hasJWT": true,
    "nodeEnv": "production"
  }
}
```

### Test 2: Backend Funds API

```bash
curl https://mutualfun-backend.vercel.app/api/funds?limit=5
```

Expected:

```json
{
  "success": true,
  "data": [
    {
      "schemeCode": "102885",
      "schemeName": "HDFC Balanced Advantage Fund...",
      ...
    }
  ],
  "pagination": {
    "total": 14216
  }
}
```

### Test 3: Frontend

1. Open: https://mutual-fun-frontend-osed.vercel.app
2. Should see funds listed on homepage
3. Click "Login" → Google OAuth should work
4. Navigate to any fund → should show details

---

## Common Issues & Solutions

### Issue 1: "No funds available"

**Cause**: Frontend still using localhost API
**Solution**: Set `NEXT_PUBLIC_API_URL` in Vercel dashboard and redeploy

### Issue 2: Google OAuth redirect error

**Cause**: Redirect URI not whitelisted
**Solution**: Add all URIs in Google Cloud Console (see above)

### Issue 3: "Database connection failed"

**Cause**: DATABASE_URL not set in Vercel
**Solution**: Add DATABASE_URL to backend environment variables

### Issue 4: CORS errors in browser console

**Cause**: Frontend domain not in ALLOWED_ORIGINS
**Solution**: Add frontend URL to backend's ALLOWED_ORIGINS env var

---

## Verification Checklist

- [ ] Backend environment variables set in Vercel
- [ ] Frontend environment variables set in Vercel
- [ ] Google OAuth URIs updated in Google Cloud Console
- [ ] Backend deployed with fixes (git push)
- [ ] Frontend redeployed (after env vars set)
- [ ] Backend API returns funds: `curl .../api/funds`
- [ ] Frontend loads: https://mutual-fun-frontend-osed.vercel.app
- [ ] Google login works
- [ ] Fund details page shows holdings

---

## Current Status

✅ **Backend fixes applied** - Ready to deploy
✅ **MongoDB Atlas has 14,216 funds** - Data is there
⚠️ **Vercel env vars** - Need to be set manually in dashboard
⚠️ **Google OAuth URIs** - Need to be updated in Google Console

**Next Step**: Set environment variables in Vercel dashboard, then push to trigger deployment.

---

## Quick Deploy Commands

```bash
# Backend
cd "c:\MF root folder\mutual-funds-backend"
git add .
git commit -m "fix: API filters and Google OAuth"
git push

# Frontend (after setting env vars in Vercel)
cd "c:\MF root folder\mutual fund"
git commit --allow-empty -m "redeploy with env vars"
git push
```

**Time to deploy**: ~5 minutes after env vars are set
