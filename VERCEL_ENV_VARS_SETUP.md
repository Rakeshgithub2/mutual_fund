# Vercel Environment Variables - Copy & Paste Guide

## 🎯 Frontend (mutual-fun-frontend-osed)

**Dashboard URL**: https://vercel.com/dashboard
**Project**: mutual-fun-frontend-osed → Settings → Environment Variables

### Variables to Add:

```bash
# Variable 1
Name: NEXT_PUBLIC_API_URL
Value: https://mutualfun-backend.vercel.app
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 2
Name: NEXT_PUBLIC_GOOGLE_CLIENT_ID
Value: 336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com
Environments: ✅ Production ✅ Preview ✅ Development
```

---

## 🎯 Backend (mutualfun-backend)

**Dashboard URL**: https://vercel.com/dashboard
**Project**: mutualfun-backend → Settings → Environment Variables

### Variables to Add:

```bash
# Variable 1 - Database
Name: DATABASE_URL
Value: mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority&appName=mutualfunds
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 2 - JWT Secret
Name: JWT_SECRET
Value: 84924af5b7ba7506e46ef5466c2fc37cb8bc0cb2511a496a027ff0a1d4649b0f9b89daa7888155d67a3e2fc371ce23b5848cf6d6a90358ba94956edca6eb12b8
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 3 - JWT Refresh Secret
Name: JWT_REFRESH_SECRET
Value: 3980022e14191408a2270e41724c8416bb1a782e34986256519ffe3b1706b4c74cf79c938a0fb1870535b200ccbd8e74ae742560ca56910e99ae92746e961c14
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 4 - Frontend URL
Name: FRONTEND_URL
Value: https://mutual-fun-frontend-osed.vercel.app
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 5 - Allowed Origins
Name: ALLOWED_ORIGINS
Value: https://mutual-fun-frontend-osed.vercel.app,http://localhost:5001
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 6 - Google Client ID
Name: GOOGLE_CLIENT_ID
Value: 336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 7 - Google Client Secret (YOU NEED TO GET THIS FROM GOOGLE CLOUD CONSOLE)
Name: GOOGLE_CLIENT_SECRET
Value: YOUR_SECRET_HERE
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 8 - Google Redirect URI
Name: GOOGLE_REDIRECT_URI
Value: https://mutualfun-backend.vercel.app/api/auth/google/callback
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 9 - Redis URL
Name: REDIS_URL
Value: redis://default:HP9HMJuppPHiOKV5VGKf8Kpl6RZ7XlEU@redis-15749.c89.us-east-1-3.ec2.cloud.redislabs.com:15749
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 10 - Resend API Key
Name: RESEND_API_KEY
Value: re_XeWNNhD8_2MX5QgyXSPUTkxUHRYKosddP
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 11 - From Email
Name: FROM_EMAIL
Value: onboarding@resend.dev
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 12 - RapidAPI Key
Name: RAPIDAPI_KEY
Value: 90c72add46mshb5e4256d7aaae60p10c1fejsn41e66ecee4ab
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 13 - RapidAPI Host
Name: RAPIDAPI_HOST
Value: apidojo-yahoo-finance-v1.p.rapidapi.com
Environments: ✅ Production ✅ Preview ✅ Development

# Variable 14 - Node Environment
Name: NODE_ENV
Value: production
Environments: ✅ Production ✅ Preview ✅ Development
```

---

## 🔑 Get Google Client Secret

1. Go to: https://console.cloud.google.com/apis/credentials
2. Find OAuth 2.0 Client ID: `336417139932-cofv6fogqqch4uub4k19krimj1mhoslc.apps.googleusercontent.com`
3. Click on it
4. Copy the **Client Secret** value
5. Paste it as `GOOGLE_CLIENT_SECRET` in Vercel

---

## ✅ Verification Steps

After setting all variables:

1. **Redeploy Backend**:

   ```bash
   cd "c:\MF root folder\mutual-funds-backend"
   git commit --allow-empty -m "trigger redeploy with env vars"
   git push
   ```

2. **Redeploy Frontend**:

   ```bash
   cd "c:\MF root folder\mutual fund"
   git commit --allow-empty -m "trigger redeploy with env vars"
   git push
   ```

3. **Test Backend** (wait 2-3 min after deploy):

   ```bash
   curl https://mutualfun-backend.vercel.app/api/funds?limit=3
   ```

   Should return: `{"success":true,"data":[...],"pagination":{"total":14216}}`

4. **Test Frontend**:
   - Open: https://mutual-fun-frontend-osed.vercel.app
   - Should see funds listed
   - Login with Google should work

---

## 🚨 Important Notes

1. **NEVER commit .env files to git** - These are already in .gitignore
2. **Set all three environments** - Production, Preview, Development
3. **Google Client Secret** - You MUST get this from Google Cloud Console
4. **After setting env vars** - Always redeploy (push or use "Redeploy" button)
5. **Vercel ignores local .env files** - Must set in dashboard

---

## 📋 Quick Checklist

**Frontend:**

- [ ] NEXT_PUBLIC_API_URL set to backend URL
- [ ] NEXT_PUBLIC_GOOGLE_CLIENT_ID set
- [ ] Redeployed after setting variables

**Backend:**

- [ ] DATABASE_URL set (MongoDB Atlas)
- [ ] JWT_SECRET and JWT_REFRESH_SECRET set
- [ ] GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET set
- [ ] GOOGLE_REDIRECT_URI set
- [ ] FRONTEND_URL set
- [ ] ALLOWED_ORIGINS includes frontend URL
- [ ] All API keys set (Redis, Resend, RapidAPI)
- [ ] Redeployed after setting variables

**Google Cloud Console:**

- [ ] Added https://mutual-fun-frontend-osed.vercel.app to Authorized JavaScript origins
- [ ] Added https://mutualfun-backend.vercel.app/api/auth/google/callback to Authorized redirect URIs
- [ ] Copied Client Secret to Vercel

---

## 🎉 After Everything is Set

Your app should work perfectly:

- ✅ Funds load from API (14,216 funds)
- ✅ Google login works
- ✅ Fund details show holdings
- ✅ No CORS errors
- ✅ No "localhost" connection errors
