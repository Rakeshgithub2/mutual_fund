# AWS Free Tier Deployment Guide

**Mutual Fund Investment Platform - Complete AWS Architecture**

---

## 🎯 Executive Summary

**GOOD NEWS:** AWS Free Tier is **PERFECT** for your mutual fund platform and **SOLVES** all the Vercel limitations!

### Why AWS Free Tier is Better Than Vercel:

✅ **No 10-second timeout** - Workers can run for 15 minutes (Lambda) or indefinitely (EC2)  
✅ **Keep automation in backend** - No need to separate into Lambda functions  
✅ **24/7 running server** - EC2 t2.micro/t3.micro runs continuously  
✅ **Full Node.js environment** - Can run Python scripts, background jobs, cron  
✅ **Better for real-time** - WebSocket support without serverless cold starts  
✅ **Free for 12 months** - Then ~$15-25/month for small t3.micro

---

## 📊 AWS Free Tier Services You'll Use

### 1. **EC2 (Elastic Compute Cloud)** - Backend API Server

- **Free Tier:** 750 hours/month of t2.micro or t3.micro (enough for 1 instance 24/7)
- **Instance Type:** t3.micro (2 vCPU, 1 GB RAM, burst performance)
- **OS:** Ubuntu 22.04 LTS (free)
- **Use Case:** Run your Express backend + workers continuously
- **Benefits:** No timeouts, can run background jobs, full control

### 2. **Lambda** - Automation Functions (Optional)

- **Free Tier:** 1 million requests/month + 400,000 GB-seconds compute
- **Use Case:** NAV updates (daily), market indices (every 5 min), news fetching
- **Benefits:** Zero maintenance, auto-scaling, perfect for scheduled jobs
- **Your Current Usage:** ~12,000 requests/month (well within limits)

### 3. **S3 + CloudFront** - Frontend Hosting

- **S3 Free Tier:** 5 GB storage + 20,000 GET requests/month
- **CloudFront Free Tier:** 50 GB data transfer out + 2 million HTTP/HTTPS requests
- **Use Case:** Host Next.js static export or run Next.js on separate EC2
- **Benefits:** Global CDN, fast loading, cheap storage

### 4. **EventBridge** - Cron Job Scheduler

- **Free Tier:** All event publishing and custom events are FREE
- **Use Case:** Trigger Lambda functions or EC2 scripts on schedule
- **Benefits:** Reliable cron without managing servers

### 5. **API Gateway** (Optional)

- **Free Tier:** 1 million API calls/month for 12 months
- **Use Case:** REST API endpoint in front of Lambda (if you separate automation)
- **Benefits:** Built-in rate limiting, API keys, usage plans

### 6. **MongoDB Atlas** (Keep Current)

- **Free Tier:** 512 MB storage (M0 cluster)
- **Current Usage:** ~135 MB (you're fine)
- **Benefits:** Managed MongoDB, no server maintenance

### 7. **Redis Labs/Upstash** (For Caching)

- **Upstash Free Tier:** 10,000 requests/day
- **Use Case:** Cache fund lists, reduce MongoDB load
- **Benefits:** Serverless Redis, pay-per-request

---

## 🏗️ Architecture Design

### Option A: **Single EC2 Instance (RECOMMENDED FOR FREE TIER)**

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS FREE TIER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              EC2 t3.micro (1 GB RAM)                     │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Port 3001: Express Backend API                    │  │ │
│  │  │  - JWT auth, fund CRUD, market indices             │  │ │
│  │  │  - WebSocket server (Socket.IO)                    │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Port 3000: Next.js Frontend (Production Build)    │  │ │
│  │  │  - Server-side rendering                           │  │ │
│  │  │  - Static assets served by Nginx                   │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Background Workers (PM2)                          │  │ │
│  │  │  - market-indices.worker.js (every 5 min)          │  │ │
│  │  │  - nav-updater.js (daily 8 PM IST)                 │  │ │
│  │  │  - news-fetcher.js (daily 6 AM IST)                │  │ │
│  │  │  - reminder-sender.js (every hour)                 │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Nginx Reverse Proxy (Port 80/443)                 │  │ │
│  │  │  - api.yourdomain.com → localhost:3001             │  │ │
│  │  │  - yourdomain.com → localhost:3000                 │  │ │
│  │  │  - SSL/TLS with Let's Encrypt (free)               │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ▲                                   │
│                             │ HTTPS (443)                       │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                     ┌────────┴────────┐
                     │   CloudFlare    │ (Optional CDN + DDoS)
                     │  Free DNS + WAF │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │   End Users     │
                     └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
├─────────────────────────────────────────────────────────────────┤
│  MongoDB Atlas (512 MB)  │  Free Tier - M0 Cluster             │
│  Upstash Redis (10K/day) │  Cache layer for fund lists         │
│  MFAPI.in               │  Daily NAV updates (no limit)        │
│  Yahoo Finance API      │  Market indices (2K req/hour)        │
│  NewsData.io            │  Daily news (200 req/day)            │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**

- ✅ Simple deployment (everything on one server)
- ✅ No timeout issues (workers run indefinitely)
- ✅ Lower latency (no Lambda cold starts)
- ✅ Can run Python automation directly
- ✅ 750 hours/month = FREE for 1 instance 24/7

**Cons:**

- ❌ Single point of failure (but acceptable for MVP)
- ❌ 1 GB RAM limit (need careful memory management)
- ❌ Manual scaling (but not needed for 200-300 users)

---

### Option B: **Hybrid (EC2 + Lambda)**

```
┌─────────────────────────────────────────────────────────────────┐
│                      EC2 t3.micro (Backend)                     │
│  - Express API (Port 3001)                                      │
│  - WebSocket server                                             │
│  - Real-time market updates                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│                   S3 + CloudFront (Frontend)                    │
│  - Next.js static export                                        │
│  - Global CDN distribution                                      │
│  - Faster initial load                                          │
└─────────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│                   Lambda Functions (Automation)                 │
│  - nav-updater (daily 8 PM)  - 5 min execution                  │
│  - market-indices (every 5 min) - 30 sec execution              │
│  - news-fetcher (daily 6 AM) - 2 min execution                  │
│  - reminder-sender (hourly) - 1 min execution                   │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**

- ✅ Better separation of concerns
- ✅ Auto-scaling automation
- ✅ Frontend CDN benefits
- ✅ Lower EC2 memory usage

**Cons:**

- ❌ More complex deployment
- ❌ Lambda cold starts (1-3 sec)
- ❌ Need to manage multiple services

---

## 🚀 Deployment Steps - Option A (RECOMMENDED)

### Phase 1: EC2 Instance Setup (30 minutes)

#### 1.1 Launch EC2 Instance

```bash
# AWS Console Steps:
1. Go to EC2 Dashboard → Launch Instance
2. Name: "mutual-funds-production"
3. AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
4. Instance type: t3.micro (1 GB RAM, 2 vCPU)
5. Key pair: Create new → Download .pem file
6. Network: Default VPC, Auto-assign public IP: Enable
7. Storage: 30 GB gp3 (free tier gives 30 GB)
8. Launch instance
```

#### 1.2 Configure Security Group

```bash
# Inbound Rules:
- SSH (22) from Your IP (for management)
- HTTP (80) from Anywhere (0.0.0.0/0)
- HTTPS (443) from Anywhere (0.0.0.0/0)
- Custom TCP (3001) from EC2 instance itself (backend API)
- Custom TCP (3000) from EC2 instance itself (frontend)

# Outbound Rules:
- All traffic to 0.0.0.0/0 (allow external API calls)
```

#### 1.3 Connect to EC2 Instance

```bash
# Windows (PowerShell):
ssh -i "C:\path\to\your-key.pem" ubuntu@<EC2_PUBLIC_IP>

# If permission denied:
icacls "C:\path\to\your-key.pem" /inheritance:r
icacls "C:\path\to\your-key.pem" /grant:r "%username%:R"
```

---

### Phase 2: Server Environment Setup (20 minutes)

```bash
# 2.1 Update system
sudo apt update && sudo apt upgrade -y

# 2.2 Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 2.3 Install pnpm
sudo npm install -g pnpm pm2

# 2.4 Install Nginx (reverse proxy)
sudo apt install -y nginx

# 2.5 Install Python 3 (for automation scripts)
sudo apt install -y python3 python3-pip python3-venv

# 2.6 Install Certbot (for free SSL)
sudo apt install -y certbot python3-certbot-nginx

# 2.7 Install Git
sudo apt install -y git

# Verify installations:
node -v  # Should show v20.x.x
pnpm -v  # Should show 8.x.x
python3 --version  # Should show 3.10+
nginx -v  # Should show nginx/1.x.x
```

---

### Phase 3: Deploy Backend (30 minutes)

```bash
# 3.1 Clone your backend repository
cd /home/ubuntu
git clone https://github.com/yourusername/mutual-funds-backend.git
cd mutual-funds-backend

# 3.2 Install dependencies
pnpm install

# 3.3 Create production .env file
nano .env
```

**Copy this .env template:**

```bash
# Database
DATABASE_URL="mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/mutual-funds-prod?retryWrites=true&w=majority"

# JWT Secrets (CRITICAL - USE THE GENERATED ONES)
JWT_SECRET=f13287618aa9e50119e2e0a51a032576890ccb5f774b0fcffcc8298cae0fcbd5e62369dc393f731798c1bae42df9b2b88eb48ee09e07d0a328b9fd6f0c5c17c0
JWT_REFRESH_SECRET=12056458655c6e0fc31826519c9c7919e15d57d6bc587ba7af86d29691105f6585ae8ba3595db7d4eb624d79f39aa73857070f772225ece5158bd05d6fa856cc

# API Keys
MFAPI_BASE_URL=https://api.mfapi.in/mf
YAHOO_FINANCE_API_URL=https://query1.finance.yahoo.com/v8/finance/chart
NEWSDATA_API_KEY=your_newsdata_api_key
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Redis (Upstash)
REDIS_URL=redis://:password@endpoint.upstash.io:6379

# Server Config
PORT=3001
NODE_ENV=production
FRONTEND_URL=https://yourdomain.com

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

```bash
# 3.4 Build the backend
pnpm run build

# 3.5 Setup Prisma
pnpm prisma generate
pnpm prisma db push

# 3.6 Start backend with PM2 (process manager)
pm2 start dist/index.js --name "backend-api"

# 3.7 Setup PM2 to restart on server reboot
pm2 startup systemd
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu
pm2 save

# 3.8 Monitor logs
pm2 logs backend-api
```

---

### Phase 4: Deploy Workers (20 minutes)

```bash
# 4.1 Start background workers with PM2
cd /home/ubuntu/mutual-funds-backend

# Market indices worker (runs every 5 minutes)
pm2 start workers/market-indices.worker.js --name "market-worker" --cron "*/5 * * * *" --no-autorestart

# NAV updater (runs daily at 8 PM IST)
pm2 start workers/nav-updater.js --name "nav-worker" --cron "0 20 * * *" --no-autorestart

# News fetcher (runs daily at 6 AM IST)
pm2 start workers/news-fetcher.js --name "news-worker" --cron "0 6 * * *" --no-autorestart

# Reminder sender (runs every hour)
pm2 start workers/reminder-sender.js --name "reminder-worker" --cron "0 * * * *" --no-autorestart

# Save PM2 process list
pm2 save

# View all running processes
pm2 list
```

---

### Phase 5: Deploy Frontend (30 minutes)

```bash
# 5.1 Clone frontend repository
cd /home/ubuntu
git clone https://github.com/yourusername/mutual-fund-frontend.git
cd mutual-fund-frontend

# 5.2 Install dependencies
pnpm install

# 5.3 Create production .env.local
nano .env.local
```

**Frontend .env.local:**

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SOCKET_URL=https://api.yourdomain.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

```bash
# 5.4 Build Next.js for production
pnpm run build

# 5.5 Start Next.js with PM2
pm2 start npm --name "frontend" -- start

# Alternative: Use standalone mode (smaller memory footprint)
# Edit next.config.mjs and add: output: 'standalone'
# Then: pm2 start node --name "frontend" -- .next/standalone/server.js

pm2 save
```

---

### Phase 6: Nginx Configuration (20 minutes)

```bash
# 6.1 Create Nginx config for your domain
sudo nano /etc/nginx/sites-available/mutual-funds
```

**Nginx Configuration:**

```nginx
# Backend API server
server {
    listen 80;
    server_name api.yourdomain.com;

    # Increase body size for PDF uploads
    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for Socket.IO
    location /socket.io/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Frontend server
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location /_next/static {
        proxy_pass http://localhost:3000;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# 6.2 Enable the site
sudo ln -s /etc/nginx/sites-available/mutual-funds /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx

# 6.3 Setup SSL with Let's Encrypt (FREE)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Certbot will automatically:
# - Generate SSL certificates
# - Update Nginx config to use HTTPS
# - Setup auto-renewal (certificates expire every 90 days)

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Phase 7: Domain Setup (10 minutes)

```bash
# In your domain registrar (GoDaddy, Namecheap, Cloudflare):

# A Records:
yourdomain.com → <EC2_PUBLIC_IP>
www.yourdomain.com → <EC2_PUBLIC_IP>
api.yourdomain.com → <EC2_PUBLIC_IP>

# Wait 5-10 minutes for DNS propagation
# Test with: ping yourdomain.com
```

---

## 🔐 Security Hardening (CRITICAL - 30 minutes)

### 1. Apply Security Fixes

```bash
# On your local machine, apply the generated security fixes:

# 1.1 Update .env files with generated JWT secrets
# (Already done in Phase 3)

# 1.2 Add rate limiting to auth routes
cd "c:\MF root folder\mutual-funds-backend"
# Edit src/routes/auth.routes.ts and add:
```

```typescript
import {
  authRateLimiter,
  registrationRateLimiter,
} from "../middleware/auth.rateLimiter";

// Add to login route:
router.post("/login", authRateLimiter, emailLogin);

// Add to register route:
router.post("/register", registrationRateLimiter, emailRegister);

// Add to refresh route:
router.post("/refresh", authRateLimiter, refreshAccessToken);
```

```bash
# 1.3 Run database index setup
node scripts/setup-production-indexes.js

# 1.4 Commit and push changes
git add .
git commit -m "Apply production security fixes"
git push origin main

# 1.5 Pull changes on EC2 and restart
# On EC2:
cd /home/ubuntu/mutual-funds-backend
git pull origin main
pnpm run build
pm2 restart backend-api
```

### 2. Setup Firewall (UFW)

```bash
# On EC2:
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
sudo ufw status
```

### 3. Install Fail2Ban (Prevent Brute Force)

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 4. Setup Monitoring

```bash
# Install PM2 monitoring (free tier)
pm2 register  # Follow prompts to create PM2.io account
pm2 link <SECRET_KEY> <PUBLIC_KEY>

# Now you can monitor all processes at: https://app.pm2.io
```

---

## 📊 Monitoring & Maintenance

### Daily Checks

```bash
# Check PM2 processes
pm2 list
pm2 logs --lines 100

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
htop
```

### Auto-Deploy Script (Optional)

```bash
# Create deploy script on EC2:
nano /home/ubuntu/deploy.sh
```

```bash
#!/bin/bash

echo "🚀 Deploying updates..."

# Backend
cd /home/ubuntu/mutual-funds-backend
git pull origin main
pnpm install
pnpm run build
pm2 restart backend-api

# Frontend
cd /home/ubuntu/mutual-fund-frontend
git pull origin main
pnpm install
pnpm run build
pm2 restart frontend

echo "✅ Deployment complete!"
```

```bash
chmod +x /home/ubuntu/deploy.sh

# Now you can deploy by running:
./deploy.sh
```

---

## 💰 Cost Breakdown

### Free Tier (First 12 Months)

| Service                | Free Tier            | Your Usage           | Cost          |
| ---------------------- | -------------------- | -------------------- | ------------- |
| EC2 t3.micro           | 750 hrs/month        | 720 hrs/month (24/7) | **$0**        |
| Data Transfer Out      | 100 GB/month         | ~10 GB/month         | **$0**        |
| MongoDB Atlas          | 512 MB storage       | 135 MB               | **$0**        |
| Upstash Redis          | 10K req/day          | ~3K req/day          | **$0**        |
| SSL Certificate        | Free (Let's Encrypt) | 1 cert               | **$0**        |
| Domain Name            | N/A                  | 1 domain             | **~$12/year** |
| **TOTAL (First Year)** |                      |                      | **~$12/year** |

### After Free Tier (Month 13+)

| Service                   | Cost               |
| ------------------------- | ------------------ |
| EC2 t3.micro (24/7)       | ~$9/month          |
| Data Transfer Out (10 GB) | ~$1/month          |
| EBS Storage (30 GB)       | ~$3/month          |
| Elastic IP (if stopped)   | $0 if running 24/7 |
| **TOTAL**                 | **~$13-15/month**  |

**Grand Total:** $12 for first year, then ~$15/month

---

## 🎯 Performance Expectations

### t3.micro Capacity (1 GB RAM):

- **Concurrent Users:** 200-300 users comfortably
- **API Requests:** 50-100 req/sec peak
- **Database Queries:** 500-1000/min
- **WebSocket Connections:** 100-200 simultaneous

### When to Upgrade:

- **500+ concurrent users** → Upgrade to t3.small (2 GB RAM) - $16/month
- **1000+ users** → t3.medium (4 GB RAM) + Load Balancer - $40/month
- **5000+ users** → Auto-scaling group with multiple t3.medium instances

---

## 🔄 CI/CD Setup (Optional - GitHub Actions)

Create `.github/workflows/deploy.yml` in your repositories:

```yaml
name: Deploy to AWS EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/mutual-funds-backend
            git pull origin main
            pnpm install
            pnpm run build
            pm2 restart backend-api
```

Add secrets to GitHub:

- `EC2_HOST`: Your EC2 public IP
- `EC2_SSH_KEY`: Content of your .pem file

---

## ✅ Final Checklist

Before going live:

- [ ] EC2 instance running and accessible
- [ ] Backend API responding at `https://api.yourdomain.com/api/health`
- [ ] Frontend loading at `https://yourdomain.com`
- [ ] SSL certificates active (green padlock in browser)
- [ ] JWT secrets updated (not using defaults)
- [ ] Rate limiting active on auth routes
- [ ] Database indexes created
- [ ] PM2 workers running (check `pm2 list`)
- [ ] Nginx logs showing no errors
- [ ] MongoDB Atlas connection working
- [ ] Redis cache connected (if using Upstash)
- [ ] Google OAuth working
- [ ] API external calls working (MFAPI, Yahoo Finance, NewsData)
- [ ] WebSocket connection working (test market indices live updates)
- [ ] Mobile responsive (test on phone)
- [ ] Load test with 50 concurrent users (use Apache Bench or Locust)

---

## 🚨 Common Issues & Solutions

### Issue 1: PM2 process crashes

```bash
# Check logs
pm2 logs backend-api --lines 200

# Common causes:
# - Out of memory (upgrade to t3.small)
# - Unhandled promise rejection (check error logs)
# - MongoDB connection timeout (check DATABASE_URL)

# Restart with more memory:
pm2 restart backend-api --max-memory-restart 800M
```

### Issue 2: Nginx 502 Bad Gateway

```bash
# Check if backend is running
pm2 list

# Check backend logs
pm2 logs backend-api

# Restart backend
pm2 restart backend-api

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Issue 3: Workers not running

```bash
# Check cron syntax
pm2 list

# Manually test worker
node workers/market-indices.worker.js

# Restart worker
pm2 delete market-worker
pm2 start workers/market-indices.worker.js --name "market-worker" --cron "*/5 * * * *"
pm2 save
```

### Issue 4: Out of memory

```bash
# Check memory usage
free -h

# Identify memory hog
pm2 list

# Options:
# 1. Set memory limit per process
pm2 restart backend-api --max-memory-restart 600M

# 2. Enable swap memory
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. Upgrade to t3.small (2 GB RAM)
```

---

## 📚 Next Steps

1. **Week 1:** Deploy backend + frontend on EC2, get SSL working
2. **Week 2:** Apply security fixes, setup monitoring, load testing
3. **Week 3:** Optimize performance, add Redis caching, monitor logs
4. **Week 4:** Launch to beta users (50-100 users), collect feedback

---

## 🆘 Support Resources

- **AWS EC2 Documentation:** https://docs.aws.amazon.com/ec2/
- **PM2 Documentation:** https://pm2.keymetrics.io/docs/
- **Nginx Documentation:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **MongoDB Atlas:** https://www.mongodb.com/docs/atlas/

---

**DEPLOYMENT STATUS:** ✅ **READY TO DEPLOY ON AWS FREE TIER**

This architecture is **MUCH BETTER** than Vercel for your use case because:

1. No timeout limitations
2. Can run background workers natively
3. Full control over server environment
4. Better WebSocket support
5. Can run Python automation scripts directly
6. Lower cost ($12/year vs $20/month Vercel Pro)

**Estimated deployment time:** 2-3 hours for first-time setup, 30 minutes for subsequent deploys.
