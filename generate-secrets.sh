#!/bin/bash
# Quick script to generate secure secrets for production

echo "==================================="
echo "🔐 Generating Secure Secrets"
echo "==================================="
echo ""

echo "JWT_SECRET (for authentication):"
openssl rand -hex 64
echo ""

echo "JWT_REFRESH_SECRET (for refresh tokens):"
openssl rand -hex 64
echo ""

echo "==================================="
echo "✅ Copy these values to Vercel"
echo "Dashboard → Settings → Environment Variables"
echo "==================================="
