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