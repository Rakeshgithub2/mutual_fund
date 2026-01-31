# 📅 Monthly Holdings Update - Manual Process Guide

## What is This?

Once a month (around 15th), AMCs release updated **factsheets** containing:

- Top 10 holdings
- Sector allocation
- Fund manager names
- Expense ratio
- Asset allocation (Equity/Debt/Cash)

You need to run a Python script to download, parse, and update this data.

---

## ⏰ When to Do It

**On the 15th of every month** (or when AMCs release factsheets - usually 10th-20th of month)

Set a **calendar reminder** or check this checklist:

- [ ] January 15
- [ ] February 15
- [ ] March 15
- [ ] April 15
- [ ] May 15
- [ ] June 15
- [ ] July 15
- [ ] August 15
- [ ] September 15
- [ ] October 15
- [ ] November 15
- [ ] December 15

---

## 🚀 How to Do It (3 Easy Steps)

### **Option A: On AWS EC2 (After Deployment)**

#### Step 1: SSH into your EC2 instance

```bash
# Windows PowerShell:
ssh -i "path\to\your-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>

# Example:
ssh -i "C:\AWS\mutual-funds-key.pem" ubuntu@13.234.56.789
```

#### Step 2: Run the automation script

```bash
# Navigate to automation folder
cd /home/ubuntu/automation

# Activate Python virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the holdings update
python3 production_automation.py
```

#### Step 3: Check the output

```
Expected output:
📥 Downloading factsheets from AMCs...
  ✅ Axis Mutual Fund: 28 factsheets downloaded
  ✅ HDFC Mutual Fund: 45 factsheets downloaded
  ✅ ICICI Prudential: 52 factsheets downloaded
  ... (continues for all AMCs)

📄 Parsing PDFs...
  ✅ Parsed: Axis Bluechip Fund
  ✅ Parsed: HDFC Top 100 Fund
  ... (continues)

💾 Updating MongoDB...
  ✅ Updated 1,245 funds with holdings
  ✅ Updated sector allocations
  ✅ Updated fund managers

✅ COMPLETE! Updated 1,245 out of 1,500 funds (83.3%)
⏱️  Time taken: 2 hours 15 minutes
```

---

### **Option B: From Your Local Machine (Before Deployment)**

#### Step 1: Open PowerShell

```powershell
cd "C:\MF root folder\automation"
```

#### Step 2: Setup Python environment (first time only)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Run the script

```powershell
python production_automation.py
```

#### Step 4: Wait for completion (2-3 hours)

The script will:

1. Download ~500 PDF factsheets from AMC websites
2. Parse PDFs to extract holdings, sectors, managers
3. Update MongoDB with new data
4. Delete old month's data

---

## 🤖 How to Automate It (Make It Fully Automatic)

### **On AWS EC2:**

Add a **cron job** that runs on the 15th of every month:

```bash
# SSH into EC2
ssh -i "your-key.pem" ubuntu@<EC2_IP>

# Open crontab editor
crontab -e

# Add this line (runs at 2 AM on 15th of every month)
0 2 15 * * cd /home/ubuntu/automation && /home/ubuntu/automation/venv/bin/python3 production_automation.py >> /home/ubuntu/logs/holdings-update.log 2>&1

# Save and exit (Ctrl+X, then Y, then Enter)
```

**What this does:**

- `0 2 15 * *` = At 2:00 AM on the 15th day of every month
- `cd /home/ubuntu/automation` = Go to automation folder
- `venv/bin/python3 production_automation.py` = Run the script
- `>> /home/ubuntu/logs/holdings-update.log` = Save output to log file

**Verify cron is running:**

```bash
crontab -l  # Lists all cron jobs
```

**Now it's fully automatic!** ✅

---

## 📊 What Gets Updated

After running the script, these fields update for each fund:

```javascript
// MongoDB Collection: holdings
{
  schemeCode: "119551",
  month: "2026-02",  // Current month

  // Top 10 holdings
  holdings: [
    { name: "HDFC Bank Ltd", sector: "Financials", weightage: 8.5 },
    { name: "Reliance Industries", sector: "Energy", weightage: 7.2 },
    ...
  ],

  // Sector allocation
  sectorAllocation: {
    "Financials": 25.3,
    "IT": 22.1,
    "Energy": 15.8,
    "Healthcare": 12.4,
    ...
  },

  // Fund manager
  fundManager: "Shreyash Devalkar",

  // Expense ratio
  expenseRatio: 0.52,

  // Asset allocation
  assetAllocation: {
    equity: 95.2,
    debt: 3.5,
    cash: 1.3
  },

  lastUpdated: ISODate("2026-02-15T02:15:43Z")
}
```

---

## ⏱️ Time Expectations

| Task                | Time          |
| ------------------- | ------------- |
| Download factsheets | 45-60 min     |
| Parse PDFs          | 60-90 min     |
| Update MongoDB      | 5-10 min      |
| **Total**           | **2-3 hours** |

**Note:** Script runs in background, you can close terminal after starting it.

---

## 🔍 How to Verify It Worked

### Check MongoDB:

```javascript
// Connect to MongoDB
mongosh "mongodb+srv://your-connection-string"

// Switch to database
use mutualfunds

// Check latest holdings update
db.holdings.find().sort({ lastUpdated: -1 }).limit(5)

// Expected output:
{
  schemeCode: "119551",
  month: "2026-02",
  holdings: [...],
  lastUpdated: ISODate("2026-02-15T02:15:43Z")
}
```

### Check Frontend:

1. Open your website: `https://yourdomain.com`
2. Go to any fund page (e.g., Axis Bluechip Fund)
3. Scroll to **"Holdings & Allocation"** section
4. Verify:
   - ✅ Top 10 holdings show current data
   - ✅ Sector allocation pie chart updated
   - ✅ Fund manager name correct
   - ✅ "Last updated" shows current month

---

## ❌ Troubleshooting

### Issue 1: Script fails with "No module named 'pymongo'"

**Solution:**

```bash
cd /home/ubuntu/automation
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 2: "MongoDB connection timeout"

**Solution:**
Check your `.env` file has correct `DATABASE_URL`:

```bash
nano /home/ubuntu/mutual-funds-backend/.env
# Verify DATABASE_URL is correct
```

### Issue 3: "PDF download failed for AMC"

**Solution:**
AMC website might be down. Script will skip and continue with others. Check logs:

```bash
cat /home/ubuntu/logs/holdings-update.log
```

### Issue 4: Script running too long (>4 hours)

**Solution:**
Normal first time. Subsequent runs are faster (only downloads new factsheets).

---

## 📋 Quick Reference Commands

### **Manual Run (EC2):**

```bash
ssh ubuntu@<EC2_IP>
cd /home/ubuntu/automation
source venv/bin/activate
python3 production_automation.py
```

### **Automate with Cron:**

```bash
crontab -e
# Add: 0 2 15 * * cd /home/ubuntu/automation && venv/bin/python3 production_automation.py
```

### **Check Logs:**

```bash
tail -f /home/ubuntu/logs/holdings-update.log
```

### **Stop Running Script:**

```bash
# Find process ID
ps aux | grep production_automation

# Kill it
kill <PID>
```

---

## 💡 Pro Tips

1. **First Run:** Do it manually to ensure everything works
2. **Second Month:** Automate with cron so you never forget
3. **Monitor:** Check logs on 16th to ensure cron ran successfully
4. **Backup:** MongoDB auto-backs up, but verify before big updates
5. **Time It:** Run at 2 AM when server is idle (no user traffic)

---

## 🎯 Summary

**What:** Update fund holdings, sectors, managers monthly  
**When:** 15th of every month (or when AMCs release factsheets)  
**How:** Run `python3 production_automation.py` in automation folder  
**Time:** 2-3 hours  
**Automate:** Add cron job (5 min setup, then forget it forever)

**After automation:** You'll never have to think about this again! ✅

---

## 📞 Need Help?

If script fails or takes too long:

1. **Check logs:** `tail -f /home/ubuntu/logs/holdings-update.log`
2. **Test MongoDB connection:** `mongosh "your-connection-string"`
3. **Verify Python dependencies:** `pip list`
4. **Re-run:** Safe to run multiple times (idempotent)

---

**Remember:** This is the **ONLY** manual task in your entire platform. Everything else is fully automated! 🚀
