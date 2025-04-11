#!/usr/bin/env python3
import http.server
import socketserver
import json
import cgi
import os
import sys
from datetime import datetime
from urllib.parse import parse_qs

# Configuration
PORT = 8001
UPLOAD_DIR = 'uploads'
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000']
MAX_SIZES = {
    'resume': 5 * 1024 * 1024,  # 5MB for resumes
    'eval': 10 * 1024 * 1024,   # 10MB for evals
    'photo': 5 * 1024 * 1024    # 5MB for photos
}
ALLOWED_FILE_TYPES = {
    'resume': ['application/pdf'],
    'eval': ['application/pdf'],
    'photo': ['image/jpeg', 'image/png']
}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'resume'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'eval'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'photo'), exist_ok=True)

class UploadHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        
        # Add CORS headers
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Max-Age', '86400')
        
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self._set_headers()
        self.wfile.write(b'')
    
    def do_POST(self):
        # Check origin for CORS
        origin = self.headers.get('Origin', '')
        if origin not in ALLOWED_ORIGINS:
            self._json_response({'error': 'Forbidden'}, 403)
            return
        
        # Check content type for multipart/form-data
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self._json_response({'error': 'Invalid content type'}, 400)
            return
        
        try:
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # Get file and type
            if 'file' not in form or 'type' not in form:
                self._json_response({'error': 'Missing file or type'}, 400)
                return
            
            file_item = form['file']
            file_type = form['type'].value
            
            # Validate file type
            if file_type not in ['resume', 'eval', 'photo']:
                self._json_response({'error': 'Invalid file type'}, 400)
                return
            
            # Check if the item is a file
            if not file_item.file:
                self._json_response({'error': 'No file uploaded'}, 400)
                return
            
            # Validate file size
            file_data = file_item.file.read()
            file_size = len(file_data)
            file_item.file.seek(0)
            
            if file_size > MAX_SIZES[file_type]:
                self._json_response({
                    'error': f'File exceeds maximum size ({MAX_SIZES[file_type] // (1024 * 1024)}MB)'
                }, 400)
                return
            
            # Validate content type
            if file_item.type not in ALLOWED_FILE_TYPES[file_type]:
                self._json_response({
                    'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_FILE_TYPES[file_type])}'
                }, 400)
                return
            
            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            filename = f"{timestamp}-{file_item.filename}"
            filepath = os.path.join(UPLOAD_DIR, file_type, filename)
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            # Generate a URL for the uploaded file
            file_url = f"http://localhost:8001/uploads/{file_type}/{filename}"
            
            # Return success response
            self._json_response({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename,
                'url': file_url
            })
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            self._json_response({'error': f'Upload failed: {str(e)}'}, 500)
    
    def do_GET(self):
        # Serve uploaded files
        if self.path.startswith('/uploads/'):
            try:
                filepath = self.path[1:]  # Remove leading slash
                
                # Check if file exists
                if not os.path.isfile(filepath):
                    self.send_error(404, 'File not found')
                    return
                
                # Determine content type
                if filepath.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif filepath.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'
                
                # Serve the file
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                
            except Exception as e:
                print(f"Error serving file: {e}", file=sys.stderr)
                self.send_error(500, 'Internal server error')
        else:
            self.send_error(404, 'Not found')

def run_server():
    handler = UploadHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Upload server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Server stopped")
        sys.exit(0) 