# Resume Website

A minimalist personal resume website with a simple, elegant design and Cloudflare R2 file upload functionality.

## Features

- Clean, minimalist design
- Responsive layout for all devices
- File upload functionality:
  - Resume (PDF)
  - Navy evaluation documents (PDF)
  - Uniform photos (JPG/PNG)
- Sections for:
  - About Me
  - Navy Career
  - Resume/Experience
  - Contact

## Local Setup

1. Clone the repository
2. Run the local server:
   ```bash
   npm start
   ```
3. Open http://localhost:8080 in your browser

## Cloudflare Worker Setup

The website includes a Cloudflare Worker that handles file uploads to an R2 bucket.

### Prerequisites

1. A Cloudflare account with Workers and R2 enabled
2. An R2 bucket named "resume" created in your Cloudflare account

### Deployment

1. Install Wrangler CLI:
   ```bash
   npm install -g wrangler
   ```

2. Login to your Cloudflare account:
   ```bash
   wrangler login
   ```

3. Deploy the worker:
   ```bash
   npm run deploy
   ```

4. Set up public access for your R2 bucket in the Cloudflare dashboard

## Technologies

- HTML5
- CSS3
- JavaScript (Vanilla)
- Cloudflare Workers
- Cloudflare R2 Storage
- No external front-end dependencies

## License

MIT 