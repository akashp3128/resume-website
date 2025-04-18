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
UPLOAD_DIR = '../uploads'  # Store uploads in the root directory
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
print(f"Upload directory: {os.path.abspath(UPLOAD_DIR)}")

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
        print("Handling POST request")
        content_length = int(self.headers.get('Content-Length', 0))
        print(f"Content length: {content_length}")
        
        # Check origin for CORS
        origin = self.headers.get('Origin', '')
        print(f"Request origin: {origin}")
        
        # Print all headers for debugging
        print("Headers:")
        for header, value in self.headers.items():
            print(f"  {header}: {value}")
        
        # Check content type for multipart/form-data
        content_type = self.headers.get('Content-Type', '')
        print(f"Content type: {content_type}")
        
        if not content_type.startswith('multipart/form-data'):
            print("Invalid content type")
            self._json_response({'error': 'Invalid content type. Expected multipart/form-data'}, 400)
            return
        
        try:
            # Parse multipart form data
            print("Parsing form data")
            parser = MultipartFormParser(content_type, self.rfile, content_length)
            form = parser.parse()
            
            print(f"Form fields: {[key for key in form.keys() if not key.startswith('_')]}")
            
            # Get file and type
            if 'file' not in form or 'type' not in form:
                print("Missing file or type in form data")
                parser.cleanup_temp_files(form)
                self._json_response({'error': 'Missing file or type'}, 400)
                return
            
            file_item = form['file']
            file_type = form['type']
            
            print(f"Received file: {file_item['filename']} of type {file_type}")
            print(f"File content type detected as: {file_item['type']}")
            
            # Validate file type
            if file_type not in ['resume', 'eval', 'photo']:
                print(f"Invalid file type: {file_type}")
                parser.cleanup_temp_files(form)
                self._json_response({'error': 'Invalid file type'}, 400)
                return
            
            # Validate file size
            file_size = file_item['size']
            print(f"File size: {file_size} bytes")
            
            if file_size > MAX_SIZES[file_type]:
                print(f"File exceeds maximum size of {MAX_SIZES[file_type]} bytes")
                parser.cleanup_temp_files(form)
                self._json_response({
                    'error': f'File exceeds maximum size ({MAX_SIZES[file_type] // (1024 * 1024)}MB)'
                }, 400)
                return
            
            # Validate content type
            print(f"File content type: {file_item['type']}")
            
            # Special handling for image files due to inconsistent MIME types
            is_valid_type = False
            if file_type == 'eval' or file_type == 'photo':
                # For images, check file extension as well
                file_ext = os.path.splitext(file_item['filename'].lower())[1]
                content_type = file_item['type'].lower()
                
                # More permissive check for JPEG files which can have inconsistent MIME types
                if file_ext in ['.jpg', '.jpeg'] or content_type in ['image/jpeg', 'image/jpg'] or \
                   file_ext == '.png' or content_type == 'image/png' or \
                   (file_type == 'eval' and file_ext == '.pdf') or \
                   content_type in ALLOWED_FILE_TYPES[file_type]:
                    is_valid_type = True
                    # Normalize JPEG MIME type for consistent handling
                    if file_ext in ['.jpg', '.jpeg'] or content_type in ['image/jpeg', 'image/jpg']:
                        file_item['type'] = 'image/jpeg'
            else:
                # For PDFs, rely on the detected content type
                if file_item['type'] in ALLOWED_FILE_TYPES[file_type]:
                    is_valid_type = True
            
            if not is_valid_type:
                print(f"Invalid content type. Expected one of: {ALLOWED_FILE_TYPES[file_type]}")
                parser.cleanup_temp_files(form)
                self._json_response({
                    'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_FILE_TYPES[file_type])}'
                }, 400)
                return
            
            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            filename = f"{timestamp}-{file_item['filename']}"
            filepath = os.path.join(UPLOAD_DIR, file_type, filename)
            
            print(f"Saving file to: {filepath}")
            
            # Save the file
            try:
                with open(filepath, 'wb') as dest_file:
                    with open(file_item['tempfile'], 'rb') as src_file:
                        dest_file.write(src_file.read())
                print(f"File saved successfully")
            except Exception as e:
                print(f"Error saving file: {e}", file=sys.stderr)
                parser.cleanup_temp_files(form)
                self._json_response({'error': f'Error saving file: {str(e)}'}, 500)
                return
            
            # Generate a URL for the uploaded file
            # Determine the appropriate base URL
            host = self.headers.get('Host', f'localhost:{PORT}')
            
            # Create a reliable URL that will work from both the browser and local server
            if 'localhost' in host or '127.0.0.1' in host:
                base_url = f"http://{host}"
            else:
                # For production, use the origin if available
                origin = self.headers.get('Origin', '')
                if origin:
                    base_url = origin
                else:
                    base_url = f"http://{host}"
            
            # Remove trailing slash if present
            if base_url.endswith('/'):
                base_url = base_url[:-1]
            
            file_url = f"{base_url}/uploads/{file_type}/{filename}"
            
            print(f"File URL: {file_url}")
            
            # Clean up temporary files
            parser.cleanup_temp_files(form)
            
            # Return success response
            self._json_response({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename,
                'url': file_url
            })
            
        except Exception as e:
            print(f"Error handling upload: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self._json_response({'error': f'Upload failed: {str(e)}'}, 500)
    
    def do_GET(self):
        print(f"Handling GET request for: {self.path}")
        
        # Serve uploaded files
        if self.path.startswith('/uploads/'):
            try:
                # Adjust path to match our directory structure
                relative_path = self.path[1:]  # Remove leading slash
                filepath = os.path.join('..', relative_path)  # Go up one level since we're in upload-handler
                
                print(f"Attempting to serve file: {filepath}")
                
                # Check if file exists
                if not os.path.isfile(filepath):
                    print(f"File not found: {filepath}")
                    self.send_error(404, 'File not found')
                    return
                
                # Determine content type using the helper function
                content_type = detect_file_type(filepath)
                print(f"Serving file with content type: {content_type}")
                
                # Add CORS headers for file serving
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'public, max-age=86400')  # Cache for one day
                
                # Get the file size for Content-Length header
                file_size = os.path.getsize(filepath)
                self.send_header('Content-Length', str(file_size))
                
                self.end_headers()
                
                # Send the file in chunks to avoid memory issues with large files
                with open(filepath, 'rb') as f:
                    chunk_size = 8192  # 8KB chunks
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                
                print("File served successfully")
                
            except Exception as e:
                print(f"Error serving file: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                self.send_error(500, 'Internal server error')
        else:
            # Add simple health check endpoint
            if self.path == '/health' or self.path == '/':
                self._json_response({
                    'status': 'up',
                    'message': 'Upload server is running',
                    'timestamp': datetime.now().isoformat()
                })
                return
                
            print(f"Path not found: {self.path}")
            self.send_error(404, 'Not found')

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