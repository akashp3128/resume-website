# Resume Website

A personal website for displaying professional information and uploading documents such as resume and evaluations.

## Features

- Responsive design
- Admin login functionality
- File upload capability for:
  - Profile photo
  - Resume
  - Evaluations
- Content editing for logged-in admins
- Light/dark theme toggle

## Setup

### Quick Start

1. Make the start script executable:
   ```
   chmod +x start_server.sh
   ```

2. Run the server:
   ```
   ./start_server.sh
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

### File Upload System

The website uses a dual-system approach for file uploads:

1. **Primary Upload System**: Cloudflare Worker + R2 Storage
   - Production environment uses a Cloudflare Worker at `https://resume-file-uploader.akashpatelresume.us`
   - Files are stored in Cloudflare R2 storage

2. **Fallback Upload System**: Local Python HTTP Server
   - Development/backup system runs on `http://localhost:8001`
   - Files are stored in the `uploads/` directory
   - Automatically used if the primary system is unavailable

### Admin Access

To access admin functionality:
1. Click the dot (•) at the bottom of the page
2. Enter the password (`admin123`)
3. Once logged in, you can:
   - Upload files
   - Edit content sections
   - Logout using the admin controls at the top

## Troubleshooting

### Upload Issues

If uploads are failing, check the following:

1. **Browser Console**: Check for errors by opening your browser's developer tools
2. **Endpoint Status**: The system will automatically try both the primary and fallback endpoints
3. **Local Server**: Ensure the local server is running if using the fallback system
4. **File Types**: Ensure you're uploading allowed file types:
   - Resume: PDF only (max 5MB)
   - Evaluations: PDF only (max 10MB)
   - Photos: JPEG, PNG (max 5MB)

### Server Issues

If the server won't start:

1. Check that both scripts are executable:
   ```
   chmod +x start_server.sh
   chmod +x upload-handler/upload_server.py
   ```

2. Check that you have Python 3 installed:
   ```
   python3 --version
   ```

3. Try running the servers individually:
   ```
   python3 -m http.server 8000
   ```
   ```
   cd upload-handler && python3 upload_server.py
   ```

## Architecture

- `index.html`: Main webpage with HTML, CSS, and JavaScript
- `cloudflare-worker/`: Contains the Cloudflare Worker code for production uploads
- `upload-handler/`: Contains the local fallback upload server
- `uploads/`: Directory where local uploads are stored
- `start_server.sh`: Script to start both the main HTTP server and upload server

## Local Setup

1. Clone the repository
2. Open `index.html` in your browser

## Technologies

- HTML5
- CSS3
- JavaScript (Vanilla)
- No external dependencies

## Deployment

This site is static and can be deployed on any web hosting service.

## License

MIT

## Cloudflare Deployment

### Deploying to Cloudflare Pages

To deploy this website to Cloudflare Pages:

1. Log in to your Cloudflare Dashboard.
2. Go to **Workers & Pages** > **Create application** > **Pages**.
3. Connect your GitHub repository.
4. Configure the build settings:
   - Build command: (leave empty, as this is a static site)
   - Build output directory: `public`
   - Root directory: (leave empty)
5. Click **Save and Deploy**.

### Custom Domain Setup

To add your custom domain:

1. Go to the **Custom domains** tab in your Pages project.
2. Click **Set up a custom domain**.
3. Enter your domain name (e.g., `akashpatelresume.us`).
4. Follow the DNS configuration instructions.

### File Upload Functionality

The website uses a Cloudflare Worker to handle file uploads. To deploy the worker:

1. Navigate to the `cloudflare-worker` directory.
2. Make sure you have [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) installed.
3. Run:
   ```bash
   cd cloudflare-worker
   wrangler login
   wrangler deploy
   ```
4. Create an R2 bucket named "resume" in your Cloudflare dashboard.

## Stock Ticker Feature

The website includes a real-time stock ticker at the top of the page, which:

- Displays stock information for various symbols including crypto
- Fetches data from Alpha Vantage API with graceful fallback
- Automatically enters a fallback mode with mock data if API calls fail
- Features smooth scrolling animations

If you need to customize the stock symbols, edit the `STOCK_SYMBOLS` array in `public/js/isolated-stock-ticker.js`. 