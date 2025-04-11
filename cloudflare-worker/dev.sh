#!/bin/bash
# Cloudflare Worker local development script

echo "===== Running Resume File Uploader Locally ====="
echo "This script will start your Cloudflare Worker for local testing"

# Check if Wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Wrangler not found. Installing globally..."
    npm install -g wrangler
fi

# Log in to Cloudflare if needed
echo "Checking Cloudflare login status..."
if ! wrangler whoami &> /dev/null; then
    echo "Please log in to your Cloudflare account:"
    wrangler login
else
    echo "Already logged in to Cloudflare"
fi

# Run the worker locally
echo "Starting worker in development mode..."
echo "Your worker will be available at: http://localhost:8787"
echo "Press Ctrl+C to stop the worker"
echo ""

wrangler dev --local 