#!/usr/bin/env node

/**
 * CRITICAL SECURITY FIXES
 * Run this before deploying to production
 */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

console.log("🔒 CRITICAL SECURITY FIX SCRIPT\n");

// Generate strong secrets
const jwtSecret = crypto.randomBytes(64).toString("hex");
const jwtRefreshSecret = crypto.randomBytes(64).toString("hex");

console.log("✅ Generated strong JWT secrets\n");
console.log("Add these to your .env file in mutual-funds-backend folder:\n");
console.log("JWT_SECRET=" + jwtSecret);
console.log("JWT_REFRESH_SECRET=" + jwtRefreshSecret);
console.log("\n");

// Check if .env exists
const envPath = path.join(__dirname, "mutual-funds-backend", ".env");
const envExamplePath = path.join(
  __dirname,
  "mutual-funds-backend",
  ".env.example",
);

if (!fs.existsSync(envPath)) {
  console.log("⚠️  .env file not found. Creating from .env.example...\n");

  if (fs.existsSync(envExamplePath)) {
    let envContent = fs.readFileSync(envExamplePath, "utf8");

    // Replace placeholder secrets
    envContent = envContent.replace(
      'JWT_SECRET="your_jwt_secret_here"',
      `JWT_SECRET="${jwtSecret}"`,
    );
    envContent = envContent.replace(
      'JWT_REFRESH_SECRET="your_jwt_refresh_secret_here"',
      `JWT_REFRESH_SECRET="${jwtRefreshSecret}"`,
    );

    fs.writeFileSync(envPath, envContent);
    console.log("✅ Created .env file with strong secrets\n");
  } else {
    console.log("❌ .env.example not found. Please create .env manually.\n");
  }
} else {
  console.log(
    "⚠️  .env file already exists. Please manually update JWT secrets.\n",
  );
}

// Create rate limiter middleware if it doesn't exist
const rateLimiterPath = path.join(
  __dirname,
  "mutual-funds-backend",
  "src",
  "middleware",
  "auth.rateLimiter.ts",
);

if (!fs.existsSync(rateLimiterPath)) {
  const rateLimiterCode = `import rateLimit from 'express-rate-limit';

/**
 * Rate limiter for authentication endpoints
 * Prevents brute force attacks
 */
export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: {
    success: false,
    message: 'Too many login attempts. Please try again after 15 minutes.',
  },
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true, // Don't count successful requests
});

/**
 * Stricter rate limiter for registration
 */
export const registrationRateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // 3 registrations per hour per IP
  message: {
    success: false,
    message: 'Too many accounts created. Please try again later.',
  },
  standardHeaders: true,
  legacyHeaders: false,
});
`;

  fs.writeFileSync(rateLimiterPath, rateLimiterCode);
  console.log(
    "✅ Created rate limiter middleware: src/middleware/auth.rateLimiter.ts\n",
  );
} else {
  console.log("✅ Rate limiter middleware already exists\n");
}

// Create MongoDB index setup script
const indexScriptPath = path.join(
  __dirname,
  "mutual-funds-backend",
  "scripts",
  "setup-production-indexes.js",
);

if (!fs.existsSync(path.dirname(indexScriptPath))) {
  fs.mkdirSync(path.dirname(indexScriptPath), { recursive: true });
}

const indexScript = `#!/usr/bin/env node

/**
 * Setup critical production indexes
 * Run this before deploying to production
 */

const { MongoClient } = require('mongodb');
require('dotenv').config();

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL not set in .env file');
  process.exit(1);
}

async function setupIndexes() {
  console.log('🔧 Setting up critical production indexes...');
  
  const client = new MongoClient(DATABASE_URL);
  
  try {
    await client.connect();
    console.log('✅ Connected to MongoDB\\n');
    
    const db = client.db();
    
    // 1. Users collection
    console.log('📝 Setting up users indexes...');
    await db.collection('users').createIndex({ email: 1 }, { unique: true });
    await db.collection('users').createIndex({ googleId: 1 }, { sparse: true });
    console.log('   ✅ users indexes created\\n');
    
    // 2. Refresh tokens with TTL
    console.log('📝 Setting up refresh_tokens indexes (with TTL)...');
    await db.collection('refresh_tokens').createIndex({ token: 1 }, { unique: true });
    await db.collection('refresh_tokens').createIndex({ userId: 1 });
    await db.collection('refresh_tokens').createIndex(
      { expiresAt: 1 },
      { expireAfterSeconds: 0 }
    );
    console.log('   ✅ refresh_tokens indexes created (auto-delete enabled)\\n');
    
    // 3. Fund master collection
    console.log('📝 Setting up fund_master indexes...');
    await db.collection('fund_master').createIndex({ fundId: 1 }, { unique: true });
    await db.collection('fund_master').createIndex({ schemeCode: 1 }, { sparse: true });
    await db.collection('fund_master').createIndex({ category: 1 });
    await db.collection('fund_master').createIndex({ amc: 1 });
    await db.collection('fund_master').createIndex({ name: 'text', amc: 'text' });
    console.log('   ✅ fund_master indexes created\\n');
    
    // 4. Watchlist
    console.log('📝 Setting up watchlist indexes...');
    await db.collection('watchlist').createIndex(
      { userId: 1, fundId: 1 },
      { unique: true }
    );
    await db.collection('watchlist').createIndex({ userId: 1 });
    console.log('   ✅ watchlist indexes created\\n');
    
    // 5. Goals
    console.log('📝 Setting up goals indexes...');
    await db.collection('goals').createIndex({ userId: 1 });
    await db.collection('goals').createIndex({ userId: 1, createdAt: -1 });
    console.log('   ✅ goals indexes created\\n');
    
    // 6. Reminders
    console.log('📝 Setting up reminders indexes...');
    await db.collection('reminders').createIndex({ userId: 1 });
    await db.collection('reminders').createIndex({ scheduledDate: 1 });
    await db.collection('reminders').createIndex({ status: 1, scheduledDate: 1 });
    console.log('   ✅ reminders indexes created\\n');
    
    console.log('\\n🎉 All critical indexes created successfully!');
    console.log('\\n📊 Index Summary:');
    
    const collections = ['users', 'refresh_tokens', 'fund_master', 'watchlist', 'goals', 'reminders'];
    
    for (const collName of collections) {
      const indexes = await db.collection(collName).indexes();
      console.log(\`   \${collName}: \${indexes.length} indexes\`);
    }
    
  } catch (error) {
    console.error('❌ Error setting up indexes:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

setupIndexes();
`;

fs.writeFileSync(indexScriptPath, indexScript);
fs.chmodSync(indexScriptPath, "755");
console.log(
  "✅ Created index setup script: scripts/setup-production-indexes.js\n",
);

// Summary
console.log("═══════════════════════════════════════════════════════\n");
console.log("✅ CRITICAL FIXES PREPARED\n");
console.log("NEXT STEPS:\n");
console.log("1. Review and update .env file in mutual-funds-backend/");
console.log("2. Add DATABASE_URL if not already set");
console.log("3. Add other required environment variables (see .env.example)");
console.log("4. Run index setup script:");
console.log("   cd mutual-funds-backend");
console.log("   node ../scripts/setup-production-indexes.js\n");
console.log("5. Update src/routes/auth.routes.ts to use rate limiters:");
console.log(
  '   import { authRateLimiter, registrationRateLimiter } from "../middleware/auth.rateLimiter";',
);
console.log('   router.post("/login", authRateLimiter, emailLogin);');
console.log(
  '   router.post("/register", registrationRateLimiter, emailRegister);\n',
);
console.log("6. Review PRE_DEPLOYMENT_CHECKLIST.md for remaining items\n");
console.log("═══════════════════════════════════════════════════════\n");
