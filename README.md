# Mutual Funds Platform

A full-stack mutual funds platform with Next.js frontend and Express.js backend.

## Project Structure

```
├── mutual fund/          # Frontend (Next.js + TypeScript)
└── mutual-funds-backend/ # Backend (Express.js + MongoDB)
```

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- MongoDB Atlas account (or local MongoDB)
- Redis (optional, for caching)

### 1. Backend Setup

```powershell
cd mutual-funds-backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your MongoDB credentials

# Generate Prisma client
npx prisma generate

# IMPORTANT: Seed database with 4000+ funds
npm run seed:4000-funds

# Start backend server (runs on port 3002)
npm run dev
```

**Note:** The seeding step is crucial - it loads 4000+ mutual funds from AMFI into your database. This enables fast access and real-time API fallback for missing funds.

### 2. Frontend Setup

```powershell
cd "mutual fund"

# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env.local

# Start frontend (runs on port 5001)
pnpm dev
```

## Environment Configuration

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:3002
NEXT_PUBLIC_FRONTEND_URL=http://localhost:5001
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_GA_MEASUREMENT_ID=your_ga_id
NEXT_PUBLIC_GEMINI_KEY=your_gemini_key
```

### Backend (.env)

```env
DATABASE_URL=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
JWT_REFRESH_SECRET=your_refresh_secret
PORT=3002
FRONTEND_URL=http://localhost:5001
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
RESEND_API_KEY=your_resend_key
```

## Features

- **Fund Discovery**: Browse 4000+ mutual funds with advanced filters
- **Smart Fund Fetching**: 3-tier system (Cache → Database → Real-time API)
- **Auto-sync**: Daily NAV updates from AMFI
- **Search & Autocomplete**: Smart search with real-time suggestions
- **Fund Comparison**: Compare up to 4 funds side-by-side
- **Portfolio Management**: Track investments and performance
- **Authentication**: Google OAuth + JWT-based auth
- **Fund Managers**: Detailed fund manager profiles
- **Market Indices**: Track major market indices
- **AI Insights**: Gemini-powered investment insights
- **Real-time Data**: Missing funds fetched from API and stored automatically

## Fund Data System

The backend uses a smart 3-tier fetching system:

1. **Cache Layer** (Redis) - 5-10ms response
2. **Database Layer** (MongoDB) - 20-50ms, 4000+ pre-loaded funds
3. **API Layer** (MFAPI.in) - 200-500ms, real-time fallback

When a user requests a fund:

- First checks Redis cache (fastest)
- Then checks MongoDB database
- If not found, fetches from external API in real-time
- Stores newly fetched funds in database for future requests

**Benefits:**

- ⚡ Fast response times (most requests < 50ms)
- 📊 Complete coverage (4000+ funds ready)
- 🔄 Automatic growth (new funds added on-demand)
- 💰 Cost-effective (minimal API calls)

For detailed information, see [DATABASE_FUND_SYSTEM.md](./DATABASE_FUND_SYSTEM.md)

## API Integration

The frontend communicates with the backend via RESTful APIs:

**Base URL**: `http://localhost:3002/api`

Key endpoints:

- `GET /api/funds` - List funds with filters
- `GET /api/funds/:id` - Get fund details
- `GET /api/funds/search` - Autocomplete search
- `POST /api/auth/google` - Google OAuth
- `GET /api/fund-managers` - List fund managers

## Development

### Frontend (Port 5001)

```powershell
cd "mutual fund"
pnpm dev
```

### Backend (Port 3002)

```powershell
cd mutual-funds-backend
npm run dev
```

## Production Deployment

### Frontend (Vercel)

1. Connect GitHub repo to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy from `mutual fund` directory

### Backend (Vercel/Railway/Render)

1. Set all environment variables
2. Ensure DATABASE_URL points to production MongoDB
3. Deploy from `mutual-funds-backend` directory

## Technology Stack

### Frontend

- Next.js 15
- TypeScript
- Tailwind CSS
- Shadcn UI
- TanStack Query
- Zustand

### Backend

- Express.js
- MongoDB + Prisma
- Redis (caching)
- JWT Authentication
- Bull (job queues)

## Support

For issues or questions, check the documentation in each project folder:

- Frontend: `mutual fund/README.md`
- Backend: `mutual-funds-backend/README.md`
