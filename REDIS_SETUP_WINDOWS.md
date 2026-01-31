# Redis Setup for Windows

## ⚡ Quick Solution: Use Redis Cloud (FREE - No Installation)

Since you're on Windows, the easiest solution is to use **Redis Cloud** (free tier):

### Step 1: Sign Up for Redis Cloud (2 minutes)

1. Go to: https://redis.com/try-free/
2. Click "Get Started Free"
3. Sign up with Google/GitHub/Email
4. Create a database (select free tier)

### Step 2: Get Connection URL

After creating the database, you'll see:

```
redis://default:YOUR_PASSWORD@redis-12345.cloud.redislabs.com:12345
```

### Step 3: Update .env File

Open `mutual-funds-backend/.env` and add:

```env
REDIS_URL=redis://default:YOUR_PASSWORD@redis-12345.cloud.redislabs.com:12345
```

### Step 4: Test Connection

```powershell
cd mutual-funds-backend
npm run dev:direct
```

You should see:

```
✅ Redis connected successfully
```

---

## Alternative: Install Redis on Windows

### Option A: Memurai (Redis for Windows)

1. Download: https://www.memurai.com/get-memurai
2. Install Memurai (free for development)
3. Start Memurai service
4. Update `.env`: `REDIS_URL=redis://localhost:6379`

### Option B: Docker Desktop

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
2. Run Redis container:
   ```powershell
   docker run -d -p 6379:6379 --name redis redis:latest
   ```
3. Update `.env`: `REDIS_URL=redis://localhost:6379`

### Option C: WSL2 + Ubuntu + Redis

1. Install Ubuntu on WSL:
   ```powershell
   wsl --install Ubuntu
   ```
2. Start Ubuntu and run:
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```
3. Update `.env`: `REDIS_URL=redis://localhost:6379`

---

## 🎯 Recommended: Redis Cloud

For quickest setup, use **Redis Cloud** (no installation needed, works immediately).

Your backend will work without Redis (it's optional), but you'll lose:

- ⚡ Sub-millisecond NAV queries
- 💰 99% cost savings
- 📈 High performance caching

---

## 🔍 Verify Redis Connection

```powershell
cd mutual-funds-backend
npm run dev:direct
```

Look for:

```
✅ Redis connected successfully
```

Or check manually:

```powershell
# If using Redis Cloud, test connection
# (Install redis-cli or use Redis Insight GUI)
```

---

## ⚠️ Backend Works Without Redis

The backend will still work if Redis is unavailable:

- NAV queries will use MongoDB (slower but functional)
- Cache misses will fetch from external APIs
- System logs warning: "⚠️ Redis connection failed, will continue without caching"

---

**Quickest Path**: Use Redis Cloud (takes 2 minutes, completely free)
