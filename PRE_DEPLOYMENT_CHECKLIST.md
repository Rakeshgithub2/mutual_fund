# 🚨 PRE-DEPLOYMENT CHECKLIST - DO NOT DEPLOY UNTIL ALL ✅

**Last Updated:** January 31, 2026  
**Status:** ❌ **NOT READY FOR PRODUCTION**

---

## 🔴 CRITICAL BLOCKERS (MUST FIX BEFORE DEPLOYMENT)

### 1. Security Issues

- [ ] **JWT_SECRET is weak or using default value**
  - Current: Fallback to 'your-secret-key' in code
  - Required: 256-bit random string
  - Generate: `node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"`
  - File: `mutual-funds-backend/.env` (must add)

- [ ] **JWT_REFRESH_SECRET is weak or using default**
  - Same issue as JWT_SECRET
  - Must be different from JWT_SECRET
  - File: `mutual-funds-backend/.env` (must add)

- [ ] **No rate limiting on auth endpoints**
  - Risk: Brute force attacks on `/api/auth/login`
  - Fix: Add express-rate-limit to auth routes
  - File: `src/routes/auth.routes.ts`

- [ ] **No TTL index on refresh_tokens collection**
  - Expired tokens accumulate forever
  - Fix: Add MongoDB TTL index
  - Command: `db.refresh_tokens.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })`

- [ ] **CORS allows all origins in production**
  - Current: `callback(null, true)` for any origin
  - File: `api/index.ts` line 37
  - Fix: Strictly validate allowedOrigins in production

---

## 🟡 HIGH PRIORITY (PRODUCTION QUALITY)

### 2. Authentication & Authorization

- [ ] **Email verification not enforced**
  - Users can login without verifying email
  - Fix: Add check in auth middleware
  - File: `src/middleware/auth.middleware.ts`

- [ ] **No password reset email sending**
  - Routes exist but no actual email sent
  - Need: Configure nodemailer or Resend API
  - Files to add: Email service configuration

- [ ] **Google OAuth redirect URI mismatch risk**
  - Must configure in Google Console for production domain
  - Add both frontend and backend URLs

### 3. Database Indexes

- [ ] **Verify all critical indexes exist**

  ```bash
  # Run this script to create indexes
  npm run create-indexes
  ```

  - fund_master: fundId, schemeCode, category, amc
  - users: email (unique)
  - refresh_tokens: token (unique), userId, expiresAt (TTL)
  - watchlist: userId + fundId (compound unique)
  - goals: userId
  - reminders: userId + scheduledDate

- [ ] **Add text search indexes for fund search**
  - Collection: fund_master
  - Fields: name, amc, keywords (weighted)

### 4. Environment Variables

- [ ] **Backend .env must have ALL required variables**

  ```bash
  # Verify these exist and are NOT defaults:
  DATABASE_URL=mongodb+srv://...  ✓ (exists)
  JWT_SECRET=                     ❌ (missing or weak)
  JWT_REFRESH_SECRET=             ❌ (missing or weak)
  GOOGLE_CLIENT_ID=               ? (check if valid)
  GOOGLE_CLIENT_SECRET=           ? (check if valid)
  FRONTEND_URL=                   ? (production domain)
  NODE_ENV=production             ✓
  ```

- [ ] **Frontend .env.local must have**
  ```bash
  NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
  NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
  NEXT_PUBLIC_FRONTEND_URL=https://your-frontend.vercel.app
  ```

### 5. API Performance

- [ ] **Test fund list loading performance**
  - Load first 500 funds: Target < 1 second
  - Test with: `curl https://backend/api/funds?limit=500`
  - If > 2 seconds, add caching

- [ ] **Test single fund detail page**
  - Target: < 500ms
  - Test with: `curl https://backend/api/funds/:id`

- [ ] **Add Redis caching for frequently accessed data**
  - Cache fund lists for 5 minutes
  - Cache fund details for 15 minutes
  - Cache market indices for 2 minutes

---

## 🟢 RECOMMENDED (BEST PRACTICES)

### 6. Monitoring & Logging

- [ ] **Add error logging service**
  - Options: Sentry, LogRocket, Datadog
  - Track: API errors, auth failures, DB connection issues

- [ ] **Add uptime monitoring**
  - Options: UptimeRobot (free), Pingdom, StatusCake
  - Monitor: Backend health endpoint, frontend homepage

- [ ] **Add analytics**
  - Google Analytics or Plausible
  - Track: Page views, user flows, conversions

### 7. Database Backup

- [ ] **Enable MongoDB Atlas automated backups**
  - Frequency: Daily
  - Retention: 7 days minimum
  - Enable point-in-time restore

- [ ] **Test backup restoration**
  - Create test backup
  - Restore to new cluster
  - Verify data integrity

### 8. API Documentation

- [ ] **Document all API endpoints**
  - Use Swagger/OpenAPI
  - Include: Request/response examples, auth requirements
  - File: Create `swagger.yaml`

### 9. Load Testing

- [ ] **Simulate concurrent users**
  - Tool: k6, Artillery, or ab
  - Test: 100 concurrent users browsing funds
  - Verify: No 500 errors, response time < 3s

### 10. Error Handling

- [ ] **Add global error handler in backend**
  - File: `src/middleware/errorHandler.ts`
  - Handle: DB connection errors, validation errors, auth errors
  - Never expose internal errors to clients

- [ ] **Add error boundaries in frontend**
  - Use React Error Boundary
  - Graceful fallback UI
  - Log errors to monitoring service

---

## 📋 DEPLOYMENT STEPS (WHEN READY)

### Backend Deployment (Vercel)

1. [ ] Push code to GitHub
2. [ ] Go to Vercel dashboard
3. [ ] Add environment variables
4. [ ] Deploy
5. [ ] Test health endpoint: `/health`
6. [ ] Test auth endpoints: `/api/auth/login`
7. [ ] Test fund endpoints: `/api/funds`

### Frontend Deployment (Vercel)

1. [ ] Update `NEXT_PUBLIC_API_URL` to backend URL
2. [ ] Push code to GitHub
3. [ ] Deploy via Vercel
4. [ ] Test homepage loads
5. [ ] Test fund browsing
6. [ ] Test login/signup

### Database Setup (MongoDB Atlas)

1. [ ] Verify connection string works
2. [ ] Whitelist Vercel IPs (if needed)
3. [ ] Enable network access for 0.0.0.0/0 (or specific IPs)
4. [ ] Create database user with read/write permissions
5. [ ] Run index creation scripts

### Post-Deployment Verification

1. [ ] Visit frontend URL
2. [ ] Create test account
3. [ ] Login with email/password
4. [ ] Login with Google OAuth
5. [ ] Browse funds (equity, debt, commodity)
6. [ ] Add funds to watchlist
7. [ ] Create investment goal
8. [ ] Use SIP calculator
9. [ ] Check market indices update
10. [ ] Submit feedback

---

## 🚫 THINGS THAT WILL BREAK IN PRODUCTION

### MongoDB Atlas Free Tier Limits

- **Storage:** 512 MB total
- **Connections:** 500 concurrent max
- **Queries:** No hard limit but throttled
- **Network Transfer:** 10 GB/month

**Current Data Size:**

- 14,216 funds ≈ 50-100 MB
- Holdings data ≈ 20-30 MB
- User data (1000 users) ≈ 5 MB
- **Total:** ~80-135 MB ✅ Safe

**Concurrent Users Supported:**

- With proper indexing: 200-300 users
- Without indexes: 50-100 users

### Vercel Free Tier Limits

**Backend:**

- Execution time: 10 seconds max per request
- Memory: 1024 MB
- Deployments: 100/day
- Bandwidth: 100 GB/month

**Frontend:**

- Build time: 45 minutes max
- Deployments: Unlimited
- Bandwidth: 100 GB/month

**What breaks first:**

- Long-running automation jobs (> 10s) ❌
- Market indices worker (if > 10s) ❌
- NAV updates (if > 10s) ❌

**Solution:**

- Move automation to AWS Lambda (15 min limit)
- Or use free Oracle Cloud VM for workers

---

## 🏗️ ARCHITECTURE FIXES NEEDED

### Current Problem: Automation in Backend

```
mutual-funds-backend/
  ├── automation/          ❌ WRONG LOCATION
  ├── workers/             ❌ Won't work on Vercel
  └── cron/                ❌ Vercel can't run cron jobs
```

**Why this is wrong:**

- Vercel serverless has 10-second timeout
- NAV updates take 2-5 minutes
- Market worker takes 1-2 minutes
- Cannot run background jobs

**Correct Architecture:**

```
C:\MF root folder\
  ├── automation/              ✅ Python scripts for data extraction
  │   ├── daily_nav_update.py
  │   └── holdings_updater.py
  │
  ├── aws-lambdas/             ✅ NEW - Create this
  │   ├── nav-updater/
  │   │   ├── index.js         (Node.js Lambda)
  │   │   └── package.json
  │   └── market-worker/
  │       ├── index.js
  │       └── package.json
  │
  ├── mutual-funds-backend/    ✅ API only (no automation)
  │   └── src/
  │       ├── routes/
  │       ├── controllers/
  │       └── services/
  │
  └── mutual fund/             ✅ Frontend
      └── app/
```

**What needs to move to AWS Lambda:**

1. Daily NAV updates (8 PM daily)
2. Market indices worker (every 5 min during market hours)
3. News fetcher (6 AM daily)
4. Reminder sender (check every hour)

---

## 📝 DEPLOYMENT SEQUENCE

### Phase 1: Fix Critical Issues (2-3 days)

1. Generate strong JWT secrets
2. Add rate limiting to auth routes
3. Add TTL index to refresh_tokens
4. Enforce email verification
5. Fix CORS to validate origins

### Phase 2: Database Optimization (1 day)

1. Run index creation script
2. Test query performance
3. Add text search indexes
4. Verify backup is enabled

### Phase 3: Setup AWS Lambda (2-3 days)

1. Create Lambda functions for automation
2. Setup EventBridge cron triggers
3. Test NAV update flow
4. Test market indices worker
5. Move automation code out of backend

### Phase 4: Testing (2 days)

1. Load test with 100 concurrent users
2. Test all user flows (signup, login, browse, calculate)
3. Test OAuth flows
4. Test error scenarios
5. Verify monitoring works

### Phase 5: Deploy (1 day)

1. Deploy backend to Vercel
2. Deploy frontend to Vercel
3. Deploy Lambdas to AWS
4. Configure cron jobs
5. Final smoke test

**Total Time: 8-10 days**

---

## ✅ READY TO DEPLOY WHEN:

- [ ] All 🔴 CRITICAL items are fixed
- [ ] All 🟡 HIGH PRIORITY items are addressed
- [ ] Load testing passes with 100 users
- [ ] Automation moved to AWS Lambda
- [ ] Monitoring is setup and working
- [ ] Backup/restore tested successfully
- [ ] Production environment variables are set
- [ ] At least 2 people have tested the platform end-to-end

---

## 🎯 FINAL VERDICT

**Current State:** The platform has a solid foundation but is NOT production-ready.

**Main Issues:**

1. **Security**: Weak JWT secrets, no rate limiting
2. **Architecture**: Automation in wrong place (won't work on Vercel)
3. **Reliability**: No monitoring, error handling gaps
4. **Performance**: No caching, indexes may be incomplete

**Estimated Launch Date:** February 10, 2026 (10 days from now)

**Recommendation:**

- ✅ Core features are solid (auth, funds, calculators, watchlist)
- ❌ Security must be hardened before launch
- ❌ Automation must be moved to AWS Lambda
- ⚠️ Free tier will support 200-300 users safely
- ⚠️ Plan upgrade path when user base grows

**Go/No-Go Decision:** **NO-GO** until critical security issues are fixed.
