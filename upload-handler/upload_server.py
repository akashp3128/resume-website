#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import io
import tempfile
import mimetypes
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# Initialize mime types
mimetypes.init()
mimetypes.add_type('application/pdf', '.pdf')
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/jpeg', '.jpeg')
mimetypes.add_type('image/png', '.png')

# Configuration
PORT = 8001
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))  # Absolute path
SITE_URL = 'https://akashpatelresume.us'  # Base URL for file access
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']
MAX_SIZES = {
    'resume': 10 * 1024 * 1024,  # 10MB for resumes
    'eval': 20 * 1024 * 1024,    # 20MB for evals
    'photo': 10 * 1024 * 1024    # 10MB for photos
}
ALLOWED_FILE_TYPES = {
    'resume': ['application/pdf'],
    'eval': ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'],
    'photo': ['image/jpeg', 'image/jpg', 'image/png', 'text/plain']
}

print(f"Starting upload server on port {PORT}")
print(f"Upload directory: {UPLOAD_DIR}")
print(f"Site URL: {SITE_URL}")

# Create upload directory if it doesn't exist
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'resume'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'eval'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'photo'), exist_ok=True)
    print("Created upload directories successfully")
except Exception as e:
    print(f"Error creating directories: {e}", file=sys.stderr)
    sys.exit(1)

# Helper function to detect file type more accurately
def detect_file_type(filename, provided_type=None):
    # First check the provided type if available
    if provided_type and provided_type != 'application/octet-stream':
        # Special handling for JPEG files with inconsistent MIME types
        if provided_type in ['image/jpg', 'image/jpeg']:
            return 'image/jpeg'  # Normalize JPEG MIME types
        return provided_type
        
    # Try to determine from file extension
    file_type, encoding = mimetypes.guess_type(filename)
    if file_type:
        # Also normalize JPEG MIME types from extensions
        if file_type in ['image/jpg', 'image/jpeg']:
            return 'image/jpeg'
        return file_type
        
    # Default fallbacks based on extension
    ext = os.path.splitext(filename.lower())[1]
    if ext == '.pdf':
        return 'application/pdf'
    elif ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    
    # Last resort fallback
    return 'application/octet-stream'

class MultipartFormParser:
    def __init__(self, content_type, rfile, content_length):
        self.content_type = content_type
        self.rfile = rfile
        self.content_length = content_length
        self.boundary = None
        self.parse_content_type()
        
    def parse_content_type(self):
        # Extract boundary from content type
        if not self.content_type.startswith('multipart/form-data'):
            raise ValueError('Content type is not multipart/form-data')
            
        for part in self.content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                self.boundary = part[9:]
                if self.boundary.startswith('"') and self.boundary.endswith('"'):
                    self.boundary = self.boundary[1:-1]
                self.boundary = f'--{self.boundary}'.encode()
                return
                
        raise ValueError('No boundary found in content type')
    
    def parse(self):
        """Parse multipart form data and return a dictionary of field names to values"""
        result = {}
        temp_files = []
        
        # Read all data
        data = self.rfile.read(self.content_length)
        
        # Split by boundary
        parts = data.split(self.boundary)
        
        # Skip first part (empty) and last part (--\r\n)
        for part in parts[1:-1]:
            # Remove leading \r\n and trailing --\r\n
            part = part.strip(b'\r\n')
            
            # Split headers and body
            try:
                headers_raw, body = part.split(b'\r\n\r\n', 1)
                headers = {}
                for header in headers_raw.split(b'\r\n'):
                    name, value = header.split(b':', 1)
                    headers[name.strip().lower().decode()] = value.strip().decode()
                
                # Extract field name and filename from Content-Disposition
                content_disp = headers.get('content-disposition', '')
                field_name = None
                filename = None
                
                for item in content_disp.split(';'):
                    item = item.strip()
                    if item.startswith('name='):
                        field_name = item[5:].strip('"\'')
                    elif item.startswith('filename='):
                        filename = item[9:].strip('"\'')
                
                # Remove trailing boundary if present
                if body.endswith(b'\r\n'):
                    body = body[:-2]
                
                # If a filename is present, it's a file upload
                if filename:
                    content_type = headers.get('content-type', 'application/octet-stream')
                    # Create a temporary file to hold the data
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_file.write(body)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    
                    # Detect the correct mime type
                    detected_type = detect_file_type(filename, content_type)
                    
                    result[field_name] = {
                        'filename': filename,
                        'type': detected_type,
                        'size': len(body),
                        'tempfile': temp_file.name
                    }
                else:
                    # Regular form field
                    result[field_name] = body.decode('utf-8')
                    
            except Exception as e:
                print(f"Error parsing part: {e}")
                continue
        
        # Store temp files for later cleanup
        result['_temp_files'] = temp_files
        return result
    
    @staticmethod
    def cleanup_temp_files(form_data):
        """Clean up temporary files created during parsing"""
        if '_temp_files' in form_data:
            for temp_file in form_data['_temp_files']:
                try:
                    os.unlink(temp_file)
                except:
                    pass

class UploadHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to provide more detailed logging"""
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        
        # Add CORS headers
        origin = self.headers.get('Origin', '')
        print(f"Received request with origin: {origin}")
        
        # Always add CORS headers - allow from all origins for testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        self._set_headers(status_code)
        response = json.dumps(data).encode()
        print(f"Sending response: {data}")
        self.wfile.write(response)
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        print("Handling OPTIONS request (CORS preflight)")
        self._set_headers()
        self.wfile.write(b'')
    
    def do_POST(self):
        """Handle file uploads"""
        try:
            # Parse content type and length
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Parse multipart form data
            parser = MultipartFormParser(content_type, self.rfile, content_length)
            form_data = parser.parse()
            
            try:
                # Get upload type (resume, eval, photo)
                upload_type = form_data.get('type', 'photo')
                
                # Get file data
                file_data = form_data.get('file')
                if not file_data or not isinstance(file_data, dict):
                    return self._json_response({'error': 'No file uploaded'}, 400)
                
                # Validate file type
                if file_data['type'] not in ALLOWED_FILE_TYPES[upload_type]:
                    return self._json_response({
                        'error': f'Invalid file type. Allowed types for {upload_type}: {ALLOWED_FILE_TYPES[upload_type]}'
                    }, 400)
                
                # Validate file size
                if file_data['size'] > MAX_SIZES[upload_type]:
                    return self._json_response({
                        'error': f'File too large. Maximum size for {upload_type}: {MAX_SIZES[upload_type] // (1024*1024)}MB'
                    }, 400)
                
                # Generate safe filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                original_name = os.path.splitext(file_data['filename'])[0]
                ext = os.path.splitext(file_data['filename'])[1].lower()
                safe_filename = f"{upload_type}_{timestamp}_{original_name}{ext}"
                safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c in '._-')
                
                # Create upload path
                upload_path = os.path.join(UPLOAD_DIR, upload_type, safe_filename)
                
                # Move file from temp location
                os.rename(file_data['tempfile'], upload_path)
                
                # Generate public URL
                file_url = f"{SITE_URL}/uploads/{upload_type}/{safe_filename}"
                
                # Special handling for resume uploads
                if upload_type == 'resume':
                    # Create a symlink with a fixed name for the latest resume
                    latest_resume = os.path.join(UPLOAD_DIR, 'resume', 'latest_resume.pdf')
                    try:
                        if os.path.exists(latest_resume):
                            os.unlink(latest_resume)
                        os.symlink(upload_path, latest_resume)
                        print(f"Created symlink to latest resume: {latest_resume}")
                    except Exception as e:
                        print(f"Error creating resume symlink: {e}")
                
                # Return success with file URL
                return self._json_response({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'file': {
                        'name': safe_filename,
                        'type': file_data['type'],
                        'size': file_data['size'],
                        'url': file_url
                    }
                })
                
            finally:
                # Clean up temporary files
                MultipartFormParser.cleanup_temp_files(form_data)
                
        except Exception as e:
            print(f"Upload error: {e}")
            return self._json_response({'error': str(e)}, 500)
    
    def do_GET(self):
        """Handle file downloads and latest resume requests"""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Special handling for latest resume
            if path == '/uploads/resume/latest' or path == '/uploads/resume/latest_resume.pdf':
                latest_resume = os.path.join(UPLOAD_DIR, 'resume', 'latest_resume.pdf')
                if not os.path.exists(latest_resume):
                    return self._json_response({'error': 'No resume found'}, 404)
                    
                # Serve the latest resume
                try:
                    with open(latest_resume, 'rb') as f:
                        self._set_headers(content_type='application/pdf')
                        self.end_headers()
                        self.wfile.write(f.read())
                    return
                except Exception as e:
                    print(f"Error serving latest resume: {e}")
                    return self._json_response({'error': 'Error reading resume'}, 500)
            
            # Normal file serving
            if path.startswith('/uploads/'):
                # Remove /uploads/ prefix
                relative_path = path[8:]
                file_path = os.path.join(UPLOAD_DIR, relative_path)
                
                # Validate the path is within UPLOAD_DIR
                real_path = os.path.realpath(file_path)
                if not real_path.startswith(os.path.realpath(UPLOAD_DIR)):
                    return self._json_response({'error': 'Invalid file path'}, 403)
                
                if not os.path.exists(file_path):
                    return self._json_response({'error': 'File not found'}, 404)
                
                try:
                    # Determine content type
                    content_type, _ = mimetypes.guess_type(file_path)
                    if not content_type:
                        content_type = 'application/octet-stream'
                    
                    # Serve the file
                    with open(file_path, 'rb') as f:
                        self._set_headers(content_type=content_type)
                        self.end_headers()
                        self.wfile.write(f.read())
                    return
                except Exception as e:
                    print(f"Error serving file {file_path}: {e}")
                    return self._json_response({'error': 'Error reading file'}, 500)
            
            # Handle other paths
            return self._json_response({'error': 'Not found'}, 404)
            
        except Exception as e:
            print(f"Error handling GET request: {e}")
            return self._json_response({'error': str(e)}, 500)

def run_server():
    # Use ThreadingTCPServer for better handling of multiple requests
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
    
    try:
        httpd = ThreadedHTTPServer(("", PORT), UploadHandler)
        print(f"Upload server running at http://localhost:{PORT}")
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"ERROR: Port {PORT} is already in use. Try killing any existing processes on this port.")
            print("You can use 'lsof -i :{PORT}' to find processes using this port.")
            sys.exit(1)
        else:
            raise

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Server stopped")
        sys.exit(0) 