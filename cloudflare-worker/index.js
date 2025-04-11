/**
 * Cloudflare Worker for handling file uploads to R2 storage
 * This worker accepts file uploads and stores them in a Cloudflare R2 bucket
 */

// Configuration
const ALLOWED_ORIGINS = [
  'https://akashpatelresume.us',
  'http://akashpatelresume.us', 
  'http://localhost:8000', 
  'http://localhost:3000'
];
const BUCKET_NAME = 'resume';
const R2_PUBLIC_URL = 'https://pub-4370dc249c9e4ccc96ec4e03c63a3c4a.r2.dev';
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
    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return handleCORS(request);
    }

    // Only allow POST requests for uploads
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
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
        return jsonResponse({ 
          error: `Invalid file type. Allowed types: ${ALLOWED_FILE_TYPES[type].join(', ')}` 
        }, 400, origin);
      }

      // Generate a unique filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `${type}/${timestamp}-${file.name}`;

      // Upload file to R2
      await env.RESUME_BUCKET.put(filename, file.stream(), {
        httpMetadata: {
          contentType: file.type,
        },
      });

      // Generate a URL for the uploaded file using the correct public bucket URL
      const fileUrl = `${R2_PUBLIC_URL}/${filename}`;

      // Return success response
      return jsonResponse({
        success: true,
        message: 'File uploaded successfully',
        filename,
        url: fileUrl
      }, 200, origin);

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
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
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
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    }
  });
} 