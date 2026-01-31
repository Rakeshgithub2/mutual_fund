# Quick Deployment Guide

## 🚀 Pre-Deployment (Run Once)

### 1. Create Search Indexes

```bash
cd mutual-funds-backend

# Set DATABASE_URL environment variable
export DATABASE_URL="mongodb+srv://user:pass@cluster.mongodb.net/mutual_funds_db"

# Create indexes (takes 30-60 seconds)
npm run create-indexes
```

**Output should show:**

```
✅ Text index created on fund_master
✅ Compound index created for filtering
✅ SchemeCode index created
✅ NAV date index created
```

### 2. Configure Environment Variables

**Backend (.env):**

```env
DATABASE_URL=mongodb+srv://...
ORACLE_VM_URL=http://your-oracle-vm:8080
ORACLE_API_KEY=your_key
RAPIDAPI_KEY=your_rapidapi_key (optional)
```

**Frontend (.env.local):**

```env
DATABASE_URL=mongodb+srv://...
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

### 3. Add to Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Select your backend project → Settings → Environment Variables
3. Add all variables from step 2

### 4. MongoDB Atlas Setup

1. Go to MongoDB Atlas → Network Access
2. Click "Add IP Address"
3. Select "Allow Access From Anywhere" → `0.0.0.0/0`
4. Click Confirm

---

## 📦 Deployment

### Backend

```bash
cd mutual-funds-backend
vercel --prod
```

### Frontend

```bash
cd "mutual fund"
vercel --prod
```

---

## ✅ Verification

### 1. Test Search API

```bash
# Replace with your actual backend URL
curl "https://your-backend.vercel.app/api/search/funds?q=HDFC"
```

**Expected:**

```json
{
  "success": true,
  "data": [...],
  "source": "database",
  "count": 15
}
```

### 2. Check Data Source Health

```bash
curl "https://your-backend.vercel.app/api/search/health"
```

**Expected:**

```json
{
  "success": true,
  "database": {
    "connected": true,
    "fundCount": 12450
  },
  "dataSources": {
    "oracle": true,
    "mfapi": true,
    "rapidapi": false
  }
}
```

### 3. Test Real-Time Fallback

```bash
# Search for a fund NOT in your database
curl "https://your-backend.vercel.app/api/search/funds?q=XYZ_NEW_FUND"
```

Should return results from Oracle/MFAPI if available.

---

## 🐛 Troubleshooting

### "Text index not found"

**Solution:**

```bash
npm run create-indexes
```

### Vercel Timeout

**Check:**

1. MongoDB Atlas IP allowlist includes `0.0.0.0/0`
2. `DATABASE_URL` is set in Vercel environment variables
3. Connection string includes `?retryWrites=true`

### Oracle VM Not Responding

**Verify:**

```bash
curl -H "Authorization: Bearer your_key" \
  "http://your-oracle-vm:8080/health"
```

---

## 📊 Performance Expectations

After deployment:

- Search latency: **<200ms** (was 5+ min)
- MongoDB connection: **<50ms** (was 5-10 sec)
- Timeout rate: **0%** (was 80%)
- Data freshness: **Always current** (was stale)

---

## 📖 Full Documentation

See:

- [PRODUCTION_FIXES_COMPLETE.md](./PRODUCTION_FIXES_COMPLETE.md)
- [ORACLE_VM_CONNECTION_GUIDE.md](./ORACLE_VM_CONNECTION_GUIDE.md)
