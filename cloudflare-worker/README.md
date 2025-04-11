# Resume File Uploader - Cloudflare Worker

This Cloudflare Worker handles file uploads from your resume website to your Cloudflare R2 bucket.

## Prerequisites

1. A Cloudflare account with Workers and R2 enabled
2. Cloudflare CLI (Wrangler) installed
3. An R2 bucket named "resume" created in your Cloudflare account

## Setup and Deployment

1. Install Wrangler CLI if you haven't already:
   ```bash
   npm install -g wrangler
   ```

2. Login to your Cloudflare account:
   ```bash
   wrangler login
   ```

3. Create your R2 bucket if you haven't already:
   ```bash
   wrangler r2 bucket create resume
   ```

4. Deploy the worker:
   ```bash
   cd cloudflare-worker
   wrangler deploy
   ```

5. Set up a custom domain for your worker (optional):
   - Go to your Cloudflare Workers dashboard
   - Navigate to your worker
   - Click on "Triggers" and then "Custom Domains"
   - Add a custom domain like `api.akashpatelresume.us`

## How It Works

The worker:
1. Receives file uploads (PDF for resumes and evaluations, images for photos)
2. Validates file types, sizes, and request origin
3. Stores files in your R2 bucket with organized paths
4. Returns a URL to the uploaded file

## Configuration

Edit the following variables in `index.js` as needed:

- `ALLOWED_ORIGINS`: Update with your website domains
- `MAX_SIZE`: Adjust file size limits if needed
- `ALLOWED_FILE_TYPES`: Change allowed file types if needed

## Setting Up R2 Public Access

To make uploaded files publicly accessible:

1. Go to your Cloudflare R2 dashboard
2. Click on your "resume" bucket
3. Go to "Settings" > "Public Access"
4. Enable public access and set up a custom domain (e.g., `assets.akashpatelresume.us`)
5. Update the `fileUrl` variable in the worker code to match your custom domain

## Testing

You can test the worker using tools like `curl`:

```bash
curl -X POST \
  -F "file=@/path/to/test.pdf" \
  -F "type=resume" \
  https://resume-file-uploader.YOUR-ACCOUNT.workers.dev/upload
``` 