#!/bin/bash
# Cloudflare Worker deployment script for Resume Website

echo "===== Resume File Uploader Deployment ====="
echo "This script will deploy your Cloudflare Worker for handling file uploads"

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

# Create the R2 bucket if it doesn't exist
echo "Checking if R2 bucket exists..."
if ! wrangler r2 bucket list | grep -q "resume"; then
    echo "Creating 'resume' R2 bucket..."
    wrangler r2 bucket create resume
    echo "Remember to set up public access for your bucket in the Cloudflare dashboard"
else
    echo "R2 bucket 'resume' already exists"
fi

# Deploy the worker
echo "Deploying the worker..."
wrangler deploy

echo "===== Deployment Complete ====="
echo "Next steps:"
echo "1. Set up public access for your R2 bucket in the Cloudflare dashboard"
echo "2. Configure a custom domain for your worker (optional)"
echo "3. Test the file upload functionality on your website"
echo ""
echo "Your worker is now available at: https://resume-file-uploader.$(wrangler whoami | grep 'Account:' | awk '{print $2}').workers.dev" 