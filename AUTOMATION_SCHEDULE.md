# Automation Schedule - AWS Deployment

## 🤖 How Automation Works After AWS Deployment

Once you deploy to AWS EC2, all automations run **automatically in the background** using PM2 (process manager). No manual intervention needed!

---

## 📅 Automation Schedule

### 1. **Market Indices (Real-Time Updates)**

**File:** `mutual-funds-backend/workers/market-indices.worker.js`

**Frequency:** Every 5 minutes during market hours (9:15 AM - 3:30 PM IST, Monday-Friday)

**What It Updates:**

- NIFTY 50
- SENSEX
- NIFTY Bank
- NIFTY IT
- NIFTY Midcap 100
- NIFTY Smallcap 100

**Data Source:** Yahoo Finance API (free, 2000 requests/hour limit)

**How It Works:**

```javascript
// Runs automatically every 5 minutes
setInterval(
  async () => {
    const indices = ["%5ENSEI", "%5EBSESN", "%5ENSEBANK", "%5ECNXIT"];
    for (const symbol of indices) {
      const data = await fetchFromYahooFinance(symbol);
      await saveToDatabase(data);
      // Broadcast to frontend via WebSocket
      io.emit("market-update", data);
    }
  },
  5 * 60 * 1000,
); // 5 minutes
```

**PM2 Setup Command (Already in deployment guide):**

```bash
pm2 start workers/market-indices.worker.js --name "market-worker" --cron "*/5 * * * *"
```

**Result:** Your frontend shows **live market data** that updates automatically every 5 minutes

---

### 2. **NAV Updates (Daily)**

**File:** `mutual-funds-backend/workers/nav-updater.js`

**Frequency:** Once per day at 8:00 PM IST (after markets close and NAVs are published)

**What It Updates:**

- Daily NAV for all 14,216 mutual funds
- 1-day return percentage
- 7-day, 30-day, 90-day, 1-year returns
- Historical NAV data (maintains 5-year history)

**Data Source:** MFAPI.in (free, no rate limit)

**How It Works:**

```javascript
// Runs automatically at 8 PM IST daily
const updateAllFundNAVs = async () => {
  const funds = await prisma.fundMaster.findMany();

  for (const fund of funds) {
    const navData = await fetch(`https://api.mfapi.in/mf/${fund.schemeCode}`);
    const latestNav = navData.data[0];

    await prisma.fundMaster.update({
      where: { id: fund.id },
      data: {
        currentNav: latestNav.nav,
        navDate: new Date(latestNav.date),
        dayChange: calculateDayChange(latestNav, previousNav),
        weekReturn: calculateWeekReturn(navData.data),
        monthReturn: calculateMonthReturn(navData.data),
        yearReturn: calculateYearReturn(navData.data),
      },
    });
  }
};
```

**PM2 Setup Command:**

```bash
pm2 start workers/nav-updater.js --name "nav-worker" --cron "0 20 * * *"
```

**Cron Syntax:** `0 20 * * *` = At 20:00 (8 PM) every day

**Result:** All fund NAVs update automatically every evening. Users see fresh data next day.

---

### 3. **Holdings & Sector Updates (Monthly)**

**Files:**

- `automation/production_automation.py`
- `automation/pdf_parser.py`

**Frequency:** Once per month (typically 15th of each month when AMCs publish factsheets)

**What It Updates:**

- Top 10 equity holdings for each fund
- Sector allocation (Financials, IT, Healthcare, etc.)
- Asset allocation (Equity %, Debt %, Cash %)
- Fund manager names
- Expense ratio

**Data Source:** AMC websites (PDF factsheets)

**How It Works:**

```python
# Run this manually or schedule with cron
def update_monthly_holdings():
    # 1. Download latest factsheets from AMC websites
    download_factsheets_from_amcs()

    # 2. Parse PDFs to extract holdings
    holdings = parse_pdf_factsheets()

    # 3. Update MongoDB
    for fund in holdings:
        update_fund_holdings(
            scheme_code=fund['code'],
            holdings=fund['top_holdings'],
            sectors=fund['sector_allocation'],
            asset_allocation=fund['asset_mix']
        )
```

**Setup Options:**

**Option A: Manual Run (Recommended for monthly updates)**

```bash
# SSH into EC2 instance
cd /home/ubuntu/automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run manually on 15th of each month
python3 production_automation.py
```

**Option B: Automated with Cron**

```bash
# Edit crontab on EC2
crontab -e

# Add this line (runs on 15th of every month at 2 AM)
0 2 15 * * cd /home/ubuntu/automation && /home/ubuntu/automation/venv/bin/python3 production_automation.py
```

**Result:** Fund holdings and sectors stay current, updated monthly automatically.

---

### 4. **News Updates (Daily)**

**File:** `mutual-funds-backend/workers/news-fetcher.js`

**Frequency:** Once per day at 6:00 AM IST

**What It Updates:**

- Latest mutual fund news articles
- Market insights
- Regulatory changes (SEBI announcements)

**Data Source:** NewsData.io API (free tier: 200 requests/day)

**How It Works:**

```javascript
const fetchMutualFundNews = async () => {
  const news = await fetch(
    "https://newsdata.io/api/1/news?q=mutual+funds+india&apikey=YOUR_KEY",
  );

  for (const article of news.results) {
    await prisma.newsArticle.create({
      data: {
        title: article.title,
        description: article.description,
        url: article.link,
        publishedAt: new Date(article.pubDate),
        source: article.source_id,
      },
    });
  }
};
```

**PM2 Setup Command:**

```bash
pm2 start workers/news-fetcher.js --name "news-worker" --cron "0 6 * * *"
```

**Result:** Fresh news articles every morning for users to read.

---

### 5. **Reminder Notifications (Hourly)**

**File:** `mutual-funds-backend/workers/reminder-sender.js`

**Frequency:** Every hour (checks for pending reminders)

**What It Does:**

- Checks user reminders (SIP dates, rebalancing alerts, goal reviews)
- Sends email notifications via Resend/Nodemailer
- Marks reminders as sent

**How It Works:**

```javascript
const sendPendingReminders = async () => {
  const now = new Date();
  const pendingReminders = await prisma.reminder.findMany({
    where: {
      scheduledAt: { lte: now },
      status: "PENDING",
    },
    include: { user: true },
  });

  for (const reminder of pendingReminders) {
    await sendEmail({
      to: reminder.user.email,
      subject: reminder.title,
      body: reminder.message,
    });

    await prisma.reminder.update({
      where: { id: reminder.id },
      data: { status: "SENT", sentAt: now },
    });
  }
};
```

**PM2 Setup Command:**

```bash
pm2 start workers/reminder-sender.js --name "reminder-worker" --cron "0 * * * *"
```

**Result:** Users get timely email reminders for their investments.

---

## 🚀 One-Time Setup on AWS EC2

After you deploy your code to EC2, run this **once**:

```bash
# Navigate to backend folder
cd /home/ubuntu/mutual-funds-backend

# Start all workers with PM2
pm2 start workers/market-indices.worker.js --name "market-worker" --cron "*/5 * * * *" --no-autorestart
pm2 start workers/nav-updater.js --name "nav-worker" --cron "0 20 * * *" --no-autorestart
pm2 start workers/news-fetcher.js --name "news-worker" --cron "0 6 * * *" --no-autorestart
pm2 start workers/reminder-sender.js --name "reminder-worker" --cron "0 * * * *" --no-autorestart

# Save PM2 configuration (auto-restart after server reboot)
pm2 save
pm2 startup
```

**That's it!** Everything runs automatically from now on.

---

## 📊 Monitoring & Logs

### Check if workers are running:

```bash
pm2 list
```

Output:

```
┌─────┬────────────────┬─────────┬─────────┬─────────┬──────────┐
│ id  │ name           │ status  │ restart │ uptime  │ memory   │
├─────┼────────────────┼─────────┼─────────┼─────────┼──────────┤
│ 0   │ backend-api    │ online  │ 0       │ 5d      │ 180 MB   │
│ 1   │ frontend       │ online  │ 0       │ 5d      │ 150 MB   │
│ 2   │ market-worker  │ stopped │ 45      │ 0       │ 0 MB     │
│ 3   │ nav-worker     │ stopped │ 1       │ 0       │ 0 MB     │
│ 4   │ news-worker    │ stopped │ 1       │ 0       │ 0 MB     │
│ 5   │ reminder-worker│ stopped │ 24      │ 0       │ 0 MB     │
└─────┴────────────────┴─────────┴─────────┴─────────┴──────────┘
```

**Note:** Workers show "stopped" because they run on cron schedule (only active when triggered)

### Check worker logs:

```bash
# View last 100 lines
pm2 logs market-worker --lines 100

# Real-time logs
pm2 logs market-worker --follow

# Check when workers last ran
pm2 logs nav-worker --lines 50
```

### Check database to verify updates:

```bash
# Connect to MongoDB and check latest NAV
mongosh "mongodb+srv://your-connection-string"

use mutual-funds-prod

# Check latest market indices
db.market_index_history.find().sort({timestamp: -1}).limit(5)

# Check latest NAV update
db.fund_master.findOne({}, {currentNav: 1, navDate: 1}).sort({navDate: -1})

# Check holdings updates
db.holdings.find().sort({updatedAt: -1}).limit(5)
```

---

## ⏰ Complete Schedule Summary

| Automation           | Frequency   | Time (IST)        | Worker File                | Status         |
| -------------------- | ----------- | ----------------- | -------------------------- | -------------- |
| **Market Indices**   | Every 5 min | 9:15 AM - 3:30 PM | `market-indices.worker.js` | ✅ Automated   |
| **NAV Updates**      | Daily       | 8:00 PM           | `nav-updater.js`           | ✅ Automated   |
| **News Fetching**    | Daily       | 6:00 AM           | `news-fetcher.js`          | ✅ Automated   |
| **Reminders**        | Hourly      | Every hour        | `reminder-sender.js`       | ✅ Automated   |
| **Holdings/Sectors** | Monthly     | 15th (manual)     | `production_automation.py` | ⚠️ Manual/Cron |

---

## 🔧 Troubleshooting

### Worker not running?

```bash
pm2 restart market-worker
pm2 logs market-worker --lines 200
```

### NAV not updating?

```bash
# Check if MFAPI.in is accessible
curl https://api.mfapi.in/mf/119551

# Test manually
node workers/nav-updater.js
```

### Market indices stuck?

```bash
# Check Yahoo Finance API
curl "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"

# Restart worker
pm2 restart market-worker
```

### Holdings not updating?

```bash
# Run Python automation manually
cd /home/ubuntu/automation
source venv/bin/activate
python3 production_automation.py
```

---

## 💡 Best Practices

1. **Check logs weekly** to ensure workers are running smoothly
2. **Monitor MongoDB storage** (free tier = 512 MB)
3. **Run holdings update manually** on 15th of each month (takes 2-3 hours)
4. **Set up CloudWatch alarms** (optional) to get alerts if workers fail
5. **Backup database monthly** before running holdings update

---

## 🎯 Expected Results

After deployment:

- ✅ **Market data** updates automatically every 5 minutes (live on frontend)
- ✅ **NAVs** update daily at 8 PM (all 14,216 funds)
- ✅ **News** refreshes daily at 6 AM (latest articles)
- ✅ **Reminders** sent hourly (users get timely notifications)
- ⚠️ **Holdings** updated monthly (manual run on 15th)

**Zero manual intervention needed** for daily operations. Just run holdings update once a month!

---

## 🚨 Important Notes

1. **PM2 cron workers** restart automatically after server reboot
2. **Workers run in background** - they don't consume resources when idle
3. **Logs are stored** in `~/.pm2/logs/` folder
4. **Free tier limits:**
   - Yahoo Finance: 2000 req/hour (you use ~288/day)
   - MFAPI.in: Unlimited
   - NewsData.io: 200 req/day (you use 1/day)
   - MongoDB: 512 MB storage (you use ~135 MB)

All limits are well within safe zones! 🎉
