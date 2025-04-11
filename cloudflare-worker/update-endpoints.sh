#!/bin/bash
# Script to update endpoint URLs after deployment

echo "===== Update Endpoint URLs ====="
echo "This script will help you update the endpoint URLs in your code after deployment"

# Get the worker URL
read -p "Enter your Worker URL (e.g., https://resume-file-uploader.your-account.workers.dev): " WORKER_URL

# Get the public bucket URL
read -p "Enter your Public R2 Bucket URL (e.g., https://assets.akashpatelresume.us or https://pub-xxx.r2.dev): " BUCKET_URL

# Validate URLs
if [[ ! $WORKER_URL =~ ^https:// ]]; then
    echo "Worker URL must start with https://"
    exit 1
fi

if [[ ! $BUCKET_URL =~ ^https:// ]]; then
    echo "Bucket URL must start with https://"
    exit 1
fi

# Update the worker code
echo "Updating worker code..."
sed -i '' "s|const PUBLIC_BUCKET_URL = '.*';|const PUBLIC_BUCKET_URL = '$BUCKET_URL';|" index.js

# Update the website code
echo "Updating index.html..."
cd ../
sed -i '' "s|const UPLOAD_ENDPOINT = '.*';|const UPLOAD_ENDPOINT = '$WORKER_URL';|" index.html

echo "===== URLs Updated Successfully ====="
echo "Worker URL: $WORKER_URL"
echo "Public Bucket URL: $BUCKET_URL"
echo ""
echo "Next steps:"
echo "1. Commit your changes to Git"
echo "2. Redeploy your worker: cd cloudflare-worker && ./deploy.sh"
echo "3. Test the file upload functionality" 