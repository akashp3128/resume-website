/**
 * Cloudflare Worker for handling file uploads to R2 storage
 * This worker accepts file uploads and stores them in a Cloudflare R2 bucket
 */

// Configuration
const ALLOWED_ORIGINS = [
  'https://akashpatelresume.us',
  'http://akashpatelresume.us', 
  'http://localhost:8000', 
  'http://localhost:3000',
  'https://localhost:8000',
  'https://localhost:3000'
];
const BUCKET_NAME = 'resume';
// We'll serve files directly from the worker instead of using the public bucket URL
const WORKER_URL = 'https://resume-file-uploader.akashp3128.workers.dev';
const MAX_SIZE = {
  resume: 10 * 1024 * 1024, // 10MB for resumes (increased from 5MB)
  eval: 20 * 1024 * 1024,   // 20MB for evals (increased from 10MB)
  photo: 10 * 1024 * 1024   // 10MB for photos (increased from 5MB)
};
const ALLOWED_FILE_TYPES = {
  resume: ['application/pdf'],
  eval: ['application/pdf'],
  photo: ['image/jpeg', 'image/jpg', 'image/png'] // Added image/jpg for JPEG support
};

export default {
  async fetch(request, env, ctx) {
    // Get the URL and pathname
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    
    console.log(`Request received: ${method} ${path}`);
    
    // Handle CORS preflight requests
    if (method === 'OPTIONS') {
      return handleCORS(request);
    }
    
    // Handle file serving for GET and HEAD requests
    if ((method === 'GET' || method === 'HEAD') && path !== '/') {
      // Remove the leading slash
      const key = path.substring(1);
      console.log(`Retrieving file: ${key} with method: ${method}`);
      
      try {
        // Get the object from R2
        const object = await env.RESUME_BUCKET.get(key);
        
        // If the object doesn't exist, return 404
        if (object === null) {
          console.error(`File not found: ${key}`);
          return new Response('File Not Found', { 
            status: 404,
            headers: {
              'Content-Type': 'text/plain',
              'Access-Control-Allow-Origin': '*'
            }
          });
        }
        
        // Log the retrieved file details
        console.log(`File found: ${key}, size: ${object.size}, metadata:`, object.httpMetadata);
        
        // Determine content type based on filename or use the stored metadata
        let contentType = object.httpMetadata?.contentType || 'application/octet-stream';
        if (key.endsWith('.pdf')) {
          contentType = 'application/pdf';
        } else if (key.endsWith('.jpg') || key.endsWith('.jpeg')) {
          contentType = 'image/jpeg';
        } else if (key.endsWith('.png')) {
          contentType = 'image/png';
        }
        
        console.log(`Serving file with content type: ${contentType}`);
        
        // Set common headers
        const headers = {
          'Content-Type': contentType,
          'Content-Length': object.size,
          'Cache-Control': 'public, max-age=31536000',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS',
          'Access-Control-Max-Age': '86400'
        };
        
        // For HEAD requests, just return the headers without the body
        if (method === 'HEAD') {
          return new Response(null, { headers });
        }
        
        // For GET requests, return the file with headers
        return new Response(object.body, { headers });
      } catch (error) {
        console.error('Error serving file:', error);
        return new Response('Internal Server Error: ' + error.message, { 
          status: 500,
          headers: {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS'
          }
        });
      }
    }

    // Only allow POST requests for uploads
    if (method !== 'POST') {
      return new Response('Method not allowed', { 
        status: 405,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS'
        }
      });
    }

    // Validate the request origin
    const origin = request.headers.get('Origin');
    if (!ALLOWED_ORIGINS.includes(origin)) {
      return new Response('Forbidden', { status: 403 });
    }

    try {
      // Parse the multipart form data
      const formData = await request.formData();
      const file = formData.get('file');
      const type = formData.get('type'); // 'resume', 'eval', or 'photo'

      // Validate file and type
      if (!file || !type) {
        return jsonResponse({ error: 'Missing file or type' }, 400, origin);
      }

      // Validate file type
      if (!type || !['resume', 'eval', 'photo'].includes(type)) {
        return jsonResponse({ error: 'Invalid file type' }, 400, origin);
      }

      // Validate file size
      if (file.size > MAX_SIZE[type]) {
        return jsonResponse({ 
          error: `File exceeds maximum size (${MAX_SIZE[type] / (1024 * 1024)}MB)` 
        }, 400, origin);
      }

      // Validate content type
      if (!ALLOWED_FILE_TYPES[type].includes(file.type)) {
        console.error(`Invalid file type: ${file.type} for type ${type}. Allowed types: ${ALLOWED_FILE_TYPES[type].join(', ')}`);
        return jsonResponse({ 
          error: `Invalid file type: ${file.type}. Allowed types: ${ALLOWED_FILE_TYPES[type].join(', ')}` 
        }, 400, origin);
      }

      // Generate a unique filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `${type}/${timestamp}-${file.name}`;
      
      console.log(`Uploading file: ${filename}, type: ${file.type}, size: ${file.size} bytes`);

      try {
        // Upload file to R2
        await env.RESUME_BUCKET.put(filename, file.stream(), {
          httpMetadata: {
            contentType: file.type,
          },
        });
        
        // Generate a URL for the uploaded file using the worker URL instead of the public R2 URL
        const fileUrl = `${WORKER_URL}/${filename}`;
        console.log(`File uploaded successfully: ${fileUrl}`);

        // Return success response
        return jsonResponse({
          success: true,
          message: 'File uploaded successfully',
          filename,
          url: fileUrl
        }, 200, origin);
      } catch (uploadError) {
        console.error('Error uploading to R2:', uploadError);
        return jsonResponse({ 
          error: 'Upload to storage failed: ' + uploadError.message 
        }, 500, origin);
      }

    } catch (error) {
      console.error('Upload error:', error);
      return jsonResponse({ 
        error: 'Upload failed: ' + error.message 
      }, 500, origin);
    }
  }
};

// Helper function for CORS preflight requests
function handleCORS(request) {
  const origin = request.headers.get('Origin');
  
  // Check if the origin is allowed
  if (!ALLOWED_ORIGINS.includes(origin)) {
    return new Response('Forbidden', { status: 403 });
  }

  // Return CORS preflight response
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    }
  });
}

// Helper function to create a JSON response with CORS headers
function jsonResponse(data, status = 200, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, HEAD, POST, OPTIONS',
    }
  });
} 