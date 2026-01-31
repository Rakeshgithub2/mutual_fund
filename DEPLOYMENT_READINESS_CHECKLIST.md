# ✅ AWS Deployment Readiness Checklist

## What You Already Have vs What's Missing

---

## ✅ **ALREADY IN YOUR CODE** (Ready to Deploy)

### 1. **Market Indices Worker** ✅

**Location:** `mutual-funds-backend/workers/market-indices.worker.js`

- ✅ Production-grade worker with Redis locking
- ✅ Fetches from Yahoo Finance API
- ✅ Updates every 5 minutes during market hours
- ✅ Saves to MongoDB + Redis cache
- ✅ WebSocket broadcast support

**Status:** **READY** - Just run with PM2 on EC2

---

### 2. **NAV Updates** ✅

**Location:** `mutual-funds-backend/workers/missing-fund-worker.js`

- ✅ Daily NAV update at 8 PM IST
- ✅ Fetches from MFAPI.in
- ✅ Updates all 14,216 funds
- ✅ Calculates returns (1D, 7D, 30D, 1Y)

**Alternative:** `mutual-funds-backend/src/workers/background-jobs.ts` (BullMQ version)

**Status:** **READY** - Choose one approach

---

### 3. **News Fetching** ✅

**Location:** `mutual-funds-backend/src/jobs/news.job.js`

- ✅ Fetches from NewsData.io API
- ✅ Saves to MongoDB
- ✅ Top 20 finance news articles

**Also in:** `mutual-funds-backend/cron/scheduler.js` (scheduled for 6 AM IST)

**Status:** **READY** - Scheduler already configured

---

### 4. **Reminder System** ✅

**Location:** `mutual-funds-backend/src/jobs/reminder.job.js`

- ✅ Checks pending reminders
- ✅ Sends email notifications
- ✅ Supports recurring reminders
- ✅ Email templates ready

**Also:** `mutual-funds-backend/src/schedulers/reminder.scheduler.js`

**Status:** **READY** - Email service needs configuration

---

### 5. **Holdings & Sector Updates** ✅

**Location:** `automation/production_automation.py`

- ✅ Downloads factsheets from AMC websites
- ✅ Parses PDF files
- ✅ Extracts top holdings
- ✅ Updates sector allocation
- ✅ Saves to MongoDB

**Supporting files:**

- ✅ `pdf_parser.py`
- ✅ `mongodb_storage.py`
- ✅ `requirements.txt`

**Status:** **READY** - Run manually monthly

---

### 6. **Cron Scheduler** ✅

**Location:** `mutual-funds-backend/cron/scheduler.js`

- ✅ Master scheduler for all jobs
- ✅ NAV: Every hour
- ✅ News: Daily 6 AM IST
- ✅ Returns: Daily 6 PM IST
- ✅ Auto fund expansion: Daily 3 AM IST

**Status:** **READY** - Import in main server file

---

## ⚠️ **WHAT YOU NEED TO CREATE/FIX**

### 1. **Standalone Worker Scripts** ⚠️

You have the logic but need standalone PM2-compatible scripts:

**Create these files:**

#### `workers/nav-updater.js`

```javascript
/**
 * Standalone NAV Update Worker
 * Run with: pm2 start workers/nav-updater.js --name "nav-worker" --cron "0 20 * * *"
 */
require("dotenv").config();
const mongoose = require("mongoose");

// Import your existing NAV update logic
const updateAllNAV = require("../jobs/update-nav.job").updateAllNAV;

async function main() {
  try {
    await mongoose.connect(process.env.DATABASE_URL);
    console.log("🔄 Starting NAV update...");
    await updateAllNAV();
    console.log("✅ NAV update complete");
    process.exit(0);
  } catch (error) {
    console.error("❌ NAV update failed:", error);
    process.exit(1);
  }
}

main();
```

#### `workers/news-fetcher.js`

```javascript
/**
 * Standalone News Fetcher Worker
 * Run with: pm2 start workers/news-fetcher.js --name "news-worker" --cron "0 6 * * *"
 */
require("dotenv").config();
const mongoose = require("mongoose");
const NewsUpdateJob = require("../src/jobs/news.job");

async function main() {
  try {
    await mongoose.connect(process.env.DATABASE_URL);
    console.log("📰 Fetching news...");

    const newsJob = new NewsUpdateJob();
    const result = await newsJob.fetchAndSaveNews();

    console.log(`✅ News fetch complete: ${result.processed} articles`);
    process.exit(0);
  } catch (error) {
    console.error("❌ News fetch failed:", error);
    process.exit(1);
  }
}

main();
```

#### `workers/reminder-sender.js`

```javascript
/**
 * Standalone Reminder Sender Worker
 * Run with: pm2 start workers/reminder-sender.js --name "reminder-worker" --cron "0 * * * *"
 */
require("dotenv").config();
const mongoose = require("mongoose");
const ReminderJob = require("../src/jobs/reminder.job");

async function main() {
  try {
    await mongoose.connect(process.env.DATABASE_URL);
    console.log("🔔 Checking reminders...");

    const reminderJob = new ReminderJob();
    const result = await reminderJob.checkAndSendReminders();

    console.log(`✅ Reminders sent: ${result.sent}`);
    process.exit(0);
  } catch (error) {
    console.error("❌ Reminder check failed:", error);
    process.exit(1);
  }
}

main();
```

---

### 2. **Email Service Configuration** ⚠️

**What's needed:**

- Choose email provider (Resend, SendGrid, or AWS SES)
- Add API keys to `.env`
- Configure email templates

**Already have:** Email sending logic in `reminder.job.js`

**Add to `.env`:**

```bash
# Option 1: Resend (Recommended - 3000 free emails/month)
RESEND_API_KEY=re_xxxxxxxxxxxxx

# Option 2: SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx

# Option 3: AWS SES
AWS_SES_ACCESS_KEY=xxxxxxxxxxxxx
AWS_SES_SECRET_KEY=xxxxxxxxxxxxx
AWS_SES_REGION=ap-south-1
```

---

### 3. **Environment Variables** ⚠️

**Check your `.env` files have these:**

#### Backend `.env` (CRITICAL)

```bash
# Database
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/dbname

# JWT Secrets (USE THE GENERATED ONES!)
JWT_SECRET=f13287618aa9e50119e2e0a51a032576890ccb5f774b0fcffcc8298cae0fcbd5e62369dc393f731798c1bae42df9b2b88eb48ee09e07d0a328b9fd6f0c5c17c0
JWT_REFRESH_SECRET=12056458655c6e0fc31826519c9c7919e15d57d6bc587ba7af86d29691105f6585ae8ba3595db7d4eb624d79f39aa73857070f772225ece5158bd05d6fa856cc

# APIs
NEWSDATA_API_KEY=pub_xxxxxxxxxxxxx  # ⚠️ GET FROM newsdata.io
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx

# Redis (for caching + PM2)
REDIS_URL=redis://localhost:6379  # Or Upstash URL

# Email Service
RESEND_API_KEY=re_xxxxxxxxxxxxx  # ⚠️ GET FROM resend.com

# Server
PORT=3001
NODE_ENV=production
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
```

#### Frontend `.env.local`

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SOCKET_URL=https://api.yourdomain.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
```

---

## 📋 **Pre-Deployment Checklist**

### **Step 1: Get API Keys** (30 minutes)

- [ ] **NewsData.io** - Get free API key
  - Visit: https://newsdata.io/register
  - Free tier: 200 requests/day
  - Add to `.env`: `NEWSDATA_API_KEY=pub_xxxxx`

- [ ] **Resend** - Get free email API key
  - Visit: https://resend.com/signup
  - Free tier: 3000 emails/month
  - Add to `.env`: `RESEND_API_KEY=re_xxxxx`

- [ ] **Google OAuth** - Already have? Verify keys work

- [ ] **MongoDB Atlas** - Verify connection string

- [ ] **Redis** - Get Upstash free account or use EC2 local Redis
  - Visit: https://upstash.com (10K requests/day free)
  - Or install Redis on EC2: `sudo apt install redis-server`

---

### **Step 2: Create Missing Worker Files** (15 minutes)

- [ ] Create `workers/nav-updater.js` (copy code above)
- [ ] Create `workers/news-fetcher.js` (copy code above)
- [ ] Create `workers/reminder-sender.js` (copy code above)
- [ ] Test locally: `node workers/nav-updater.js`

---

### **Step 3: Update Environment Files** (10 minutes)

- [ ] Add all API keys to backend `.env`
- [ ] Add frontend URLs to frontend `.env.local`
- [ ] **IMPORTANT:** Use generated JWT secrets (not defaults!)
- [ ] Verify `DATABASE_URL` is correct

---

### **Step 4: Test Locally** (30 minutes)

```bash
# Test backend
cd mutual-funds-backend
pnpm install
pnpm run build
node dist/index.js

# Test workers
node workers/market-indices.worker.js
node workers/nav-updater.js
node workers/news-fetcher.js

# Test frontend
cd "mutual fund"
pnpm install
pnpm run build
pnpm start
```

---

### **Step 5: Deploy to AWS EC2** (Follow AWS deployment guide)

- [ ] Launch EC2 t3.micro instance
- [ ] Install Node.js, pnpm, PM2, Python
- [ ] Clone GitHub repo
- [ ] Setup environment variables
- [ ] Start backend with PM2
- [ ] Start frontend with PM2
- [ ] Start all workers with PM2 + cron
- [ ] Configure Nginx reverse proxy
- [ ] Setup SSL with Let's Encrypt
- [ ] Test all endpoints

---

## 🎯 **What Works After Deployment**

### ✅ **Fully Automated (Zero Manual Work)**

1. **Market Indices** - Updates every 5 min (9:15 AM - 3:30 PM IST)
2. **NAV Updates** - Daily at 8 PM IST
3. **News Fetching** - Daily at 6 AM IST
4. **Reminder Emails** - Every hour check + send
5. **Returns Calculation** - Daily at 6 PM IST

### ⚠️ **Semi-Automated (Monthly Manual Run)**

6. **Holdings & Sectors** - Run `python3 production_automation.py` on 15th of each month

---

## 🚨 **Critical Missing Pieces Summary**

### **MUST HAVE (before deployment):**

1. ❌ NewsData.io API key
2. ❌ Resend/SendGrid email API key
3. ❌ Create 3 standalone worker scripts (nav, news, reminder)
4. ❌ Verify all environment variables

### **NICE TO HAVE (can add later):**

- Redis/Upstash for better caching
- CloudWatch monitoring
- Error tracking (Sentry)
- Load balancer (for scaling)

---

## 📊 **Deployment Time Estimate**

| Task                | Time          |
| ------------------- | ------------- |
| Get API keys        | 30 min        |
| Create worker files | 15 min        |
| Update .env files   | 10 min        |
| Test locally        | 30 min        |
| Deploy to AWS EC2   | 2-3 hours     |
| **Total**           | **3-4 hours** |

---

## 🎓 **Next Steps**

**Option A: Deploy Now (Minimal Setup)**

1. Get NewsData.io API key
2. Get Resend API key
3. Create 3 worker files
4. Update .env with keys
5. Deploy to AWS EC2

**Option B: Test Everything Locally First**

1. Get API keys
2. Create worker files
3. Run all workers locally
4. Verify everything works
5. Then deploy to AWS

**I recommend Option B** - test locally first to catch issues early!

---

## 🆘 **Need Help?**

**For API Keys:**

- NewsData.io: https://newsdata.io/documentation
- Resend: https://resend.com/docs
- Upstash Redis: https://upstash.com/docs/redis

**For Workers:**

- PM2 Documentation: https://pm2.keymetrics.io/docs/usage/quick-start/
- Cron Syntax: https://crontab.guru

**For Deployment:**

- AWS EC2 Guide: See `AWS_FREE_TIER_DEPLOYMENT_GUIDE.md`
- Automation Schedule: See `AUTOMATION_SCHEDULE.md`

---

**BOTTOM LINE:** You have **80% of the code ready**. Just need:

1. 3 worker scripts (copy-paste 20 lines each)
2. 2 API keys (free sign-ups)
3. Environment variable updates
4. Deploy following the guide

**Estimated time to production: 3-4 hours!** 🚀
