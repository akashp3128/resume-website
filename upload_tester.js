/**
 * Upload Endpoint Tester
 * 
 * This script tests both primary and fallback upload endpoints.
 * Usage: node upload_tester.js
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// Configuration - same as in index.html
const PRIMARY_ENDPOINTS = [
  'https://resume-file-uploader.akashp3128.workers.dev',
  'https://5a889531-a525-4b10-bb97-be32b4f9dfd1.workers.dev',
  'https://resume-file-uploader.akashpatelresume.us'
];
const FALLBACK_ENDPOINT = 'http://localhost:8001';
const ORIGIN = 'https://akashpatelresume.us'; // Simulate coming from your site
const R2_PUBLIC_URL = 'https://pub-4370dc249c9e4ccc96ec4e03c63a3c4a.r2.dev';

// Helper function to send an OPTIONS request
function sendOptionsRequest(endpoint) {
  return new Promise((resolve, reject) => {
    console.log(`Testing OPTIONS request to: ${endpoint}`);
    
    const url = new URL(endpoint);
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'OPTIONS',
      headers: {
        'Origin': ORIGIN
      }
    };
    
    const req = (url.protocol === 'https:' ? https : http).request(options, (res) => {
      console.log(`STATUS: ${res.statusCode}`);
      console.log(`HEADERS: ${JSON.stringify(res.headers, null, 2)}`);
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (data) {
          console.log(`BODY: ${data}`);
        }
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', (error) => {
      console.error(`Error with ${endpoint}: ${error.message}`);
      reject(error);
    });
    
    req.end();
  });
}

// Helper function to create a test file
function createTestFile(type = 'text') {
  let testFilePath;
  
  if (type === 'text') {
    testFilePath = path.join(__dirname, 'test_upload.txt');
    fs.writeFileSync(testFilePath, 'This is a test file for upload testing');
  } else if (type === 'image') {
    // Create a simple base64-encoded JPEG image (1x1 pixel)
    testFilePath = path.join(__dirname, 'test_image.jpg');
    const simpleJpegBase64 = '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==';
    const imageBuffer = Buffer.from(simpleJpegBase64, 'base64');
    fs.writeFileSync(testFilePath, imageBuffer);
  }
  
  return testFilePath;
}

// Helper function to send a POST request with a file
function sendFileUpload(endpoint, filePath, overrideContentType = null) {
  return new Promise((resolve, reject) => {
    console.log(`Testing file upload to: ${endpoint}`);
    
    const url = new URL(endpoint);
    const fileName = path.basename(filePath);
    const fileData = fs.readFileSync(filePath);
    
    // Generate a boundary for multipart/form-data
    const boundary = `----WebKitFormBoundary${Math.random().toString(16).substr(2)}`;
    
    // Determine content type
    let contentType = overrideContentType;
    if (!contentType) {
      if (fileName.endsWith('.txt')) {
        contentType = 'text/plain';
      } else if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg')) {
        contentType = 'image/jpeg';
      } else if (fileName.endsWith('.png')) {
        contentType = 'image/png';
      } else {
        contentType = 'application/octet-stream';
      }
    }
    
    // Prepare form data
    const formData = Buffer.concat([
      // File field
      Buffer.from(`--${boundary}\r\n`),
      Buffer.from(`Content-Disposition: form-data; name="file"; filename="${fileName}"\r\n`),
      Buffer.from(`Content-Type: ${contentType}\r\n\r\n`),
      fileData,
      Buffer.from('\r\n'),
      
      // Type field
      Buffer.from(`--${boundary}\r\n`),
      Buffer.from('Content-Disposition: form-data; name="type"\r\n\r\n'),
      Buffer.from('photo\r\n'),
      
      // End of form data
      Buffer.from(`--${boundary}--\r\n`)
    ]);
    
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': formData.length,
        'Origin': ORIGIN
      }
    };
    
    const req = (url.protocol === 'https:' ? https : http).request(options, (res) => {
      console.log(`STATUS: ${res.statusCode}`);
      console.log(`HEADERS: ${JSON.stringify(res.headers, null, 2)}`);
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          if (data) {
            console.log(`BODY: ${data}`);
            // Try to parse JSON response
            try {
              const jsonData = JSON.parse(data);
              console.log('Parsed response:', jsonData);
            } catch (e) {
              console.log('Response is not JSON');
            }
          }
          
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data
          });
        } catch (error) {
          reject(error);
        }
      });
    });
    
    req.on('error', (error) => {
      console.error(`Error with ${endpoint}: ${error.message}`);
      reject(error);
    });
    
    req.write(formData);
    req.end();
  });
}

// Helper function to validate a URL is accessible
function testUrlAccess(url) {
  return new Promise((resolve, reject) => {
    console.log(`Testing URL access: ${url}`);
    
    const parsedUrl = new URL(url);
    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'HEAD'
    };
    
    const req = (parsedUrl.protocol === 'https:' ? https : http).request(options, (res) => {
      console.log(`URL STATUS: ${res.statusCode}`);
      
      if (res.statusCode >= 200 && res.statusCode < 400) {
        resolve({
          accessible: true,
          statusCode: res.statusCode
        });
      } else {
        resolve({
          accessible: false,
          statusCode: res.statusCode,
          message: `Received status code ${res.statusCode}`
        });
      }
    });
    
    req.on('error', (error) => {
      console.error(`Error accessing URL ${url}: ${error.message}`);
      resolve({
        accessible: false,
        message: error.message
      });
    });
    
    req.end();
  });
}

// Main function to run the tests
async function runTests() {
  console.log('Starting upload endpoint tests...');
  console.log('===============================');
  console.log('File size limits:');
  console.log('- Resume: 10MB (increased from 5MB)');
  console.log('- Eval: 20MB (increased from 10MB)');
  console.log('- Photo: 10MB (increased from 5MB)');
  console.log('JPEG support added (both image/jpeg and image/jpg mime types)');
  
  // Test all primary endpoints
  console.log('\n=== Testing All Primary Endpoints ===');
  let primarySuccess = false;
  let workingPrimaryEndpoint = null;
  
  for (const endpoint of PRIMARY_ENDPOINTS) {
    console.log(`\nTesting endpoint: ${endpoint}`);
    try {
      console.log('OPTIONS request:');
      await sendOptionsRequest(endpoint);
      console.log(`✅ ${endpoint} OPTIONS request successful`);
      
      console.log('File upload:');
      // Create test file
      const testFilePath = createTestFile();
      await sendFileUpload(endpoint, testFilePath);
      console.log(`✅ ${endpoint} file upload successful`);
      
      primarySuccess = true;
      workingPrimaryEndpoint = endpoint;
      console.log(`\n🟢 Found working primary endpoint: ${endpoint}`);
      break;
    } catch (error) {
      console.log(`❌ ${endpoint} failed: ${error.message}`);
    }
  }
  
  if (!primarySuccess) {
    console.log('\n🔴 None of the primary endpoints worked.');
  }
  
  // Test fallback endpoint OPTIONS
  console.log('\n=== Testing Fallback Endpoint ===');
  try {
    console.log('OPTIONS request:');
    await sendOptionsRequest(FALLBACK_ENDPOINT);
    console.log('✅ Fallback endpoint OPTIONS request successful');
    
    const testFilePath = createTestFile();
    console.log('File upload:');
    await sendFileUpload(FALLBACK_ENDPOINT, testFilePath);
    console.log('✅ Fallback endpoint file upload successful');
  } catch (error) {
    console.log(`❌ Fallback endpoint failed: ${error.message}`);
  }
  
  // Test with a JPEG image
  if (workingPrimaryEndpoint) {
    console.log('\n=== Testing JPEG Upload to Primary Endpoint ===');
    try {
      const imageFilePath = createTestFile('image');
      console.log(`Created test JPEG image at: ${imageFilePath}`);
      const uploadResponse = await sendFileUpload(workingPrimaryEndpoint, imageFilePath, 'image/jpeg');
      console.log('✅ JPEG upload test successful');
      
      // Check if we can extract the uploaded file URL from the response
      try {
        const jsonResponse = JSON.parse(uploadResponse.body);
        if (jsonResponse.url && jsonResponse.success) {
          console.log(`\n=== Testing R2 Bucket URL Access ===`);
          console.log(`Uploaded file URL: ${jsonResponse.url}`);
          
          // Verify the URL contains the correct R2 bucket URL
          if (jsonResponse.url.startsWith(R2_PUBLIC_URL)) {
            console.log(`✅ URL correctly uses the R2 public bucket URL: ${R2_PUBLIC_URL}`);
          } else {
            console.log(`❌ URL does not use the expected R2 public bucket URL. Using: ${jsonResponse.url.split('/')[2]}`);
          }
          
          // Try to access the URL
          const urlAccess = await testUrlAccess(jsonResponse.url);
          if (urlAccess.accessible) {
            console.log(`✅ Uploaded file is publicly accessible!`);
          } else {
            console.log(`❌ Cannot access uploaded file: ${urlAccess.message}`);
          }
        }
      } catch (error) {
        console.log(`❌ Failed to parse upload response: ${error.message}`);
      }
    } catch (error) {
      console.log(`❌ JPEG upload test failed: ${error.message}`);
    }
  }
  
  console.log('\n=== Tests Completed ===');
  if (workingPrimaryEndpoint) {
    console.log(`\nRECOMMENDATION: Use ${workingPrimaryEndpoint} as your PRIMARY_UPLOAD_ENDPOINT in index.html`);
  } else {
    console.log('\nRECOMMENDATION: Continue using the fallback endpoint until one of the primary endpoints works');
  }
}

// Run the tests
runTests().catch(console.error); 