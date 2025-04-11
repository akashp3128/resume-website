# Setting Up Public Access for Your R2 Bucket

This guide provides step-by-step instructions for configuring public access to your Cloudflare R2 bucket, which is essential for making uploaded files viewable on your resume website.

## Step 1: Deploy Your Worker First

Before configuring public access, make sure your worker is deployed using the provided `deploy.sh` script:

```bash
cd cloudflare-worker
chmod +x deploy.sh
./deploy.sh
```

## Step 2: Access the Cloudflare Dashboard

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Log in with your Cloudflare account credentials
3. Once logged in, look for the R2 service in the left navigation menu

## Step 3: Configure Public Access

1. In the R2 dashboard, click on the "resume" bucket
2. Navigate to the "Settings" tab
3. Find and click on the "Public Access" option

## Step 4: Set Up a Custom Domain

1. Toggle "Enable public access" to ON
2. You'll be prompted to set up a custom domain for public access. You have two options:

   a) **Use a Cloudflare-provided domain (Easier)**:
      - Select "Use a Cloudflare-provided domain"
      - This will generate a URL like `https://pub-[random-string].r2.dev`
   
   b) **Use your own custom domain (Recommended)**:
      - Select "Use a custom domain"
      - Enter your desired subdomain, e.g., `assets.akashpatelresume.us`
      - Follow the instructions to add the required DNS records to your domain
      - Verify the domain ownership

3. Click "Save" to finalize the public access configuration

## Step 5: Update Your Worker Code

After setting up public access, you need to update the `PUBLIC_BUCKET_URL` constant in your worker code:

1. Open `cloudflare-worker/index.js`
2. Locate the `PUBLIC_BUCKET_URL` constant at the top of the file
3. Replace the URL with your actual public bucket URL:

```javascript
// Update this URL to your public R2 bucket URL after setting up public access
const PUBLIC_BUCKET_URL = 'https://your-actual-public-bucket-url';
```

## Step 6: Update Your Website

Make sure to update the `UPLOAD_ENDPOINT` in your `index.html` file to point to your deployed worker:

```javascript
const UPLOAD_ENDPOINT = 'https://resume-file-uploader.your-account-name.workers.dev';
```

## Step 7: Redeploy Your Worker

After updating the worker code, redeploy it:

```bash
cd cloudflare-worker
./deploy.sh
```

## Testing Public Access

1. Upload a file using your website
2. Check the returned URL in the success message
3. Try accessing the file directly using the URL to verify it's publicly accessible

## Troubleshooting

- **File Not Found Errors**: Make sure the file path in the R2 bucket matches the path in the URL
- **CORS Errors**: Check if your website's domain is included in the `ALLOWED_ORIGINS` list
- **403 Forbidden**: Verify that public access is correctly enabled for your bucket
- **File Upload Fails**: Check the worker logs in the Cloudflare dashboard for specific errors

## Additional Configuration

- You can configure cache control headers to optimize file delivery
- Set up a firewall or access rules to restrict access based on geography or other factors
- Monitor usage and set up alerts to avoid unexpected costs

Remember that public R2 buckets are accessible to anyone with the URL, so never store sensitive or private data in them. 