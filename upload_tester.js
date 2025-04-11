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
function createTestFile() {
  const testFilePath = path.join(__dirname, 'test_upload.txt');
  fs.writeFileSync(testFilePath, 'This is a test file for upload testing');
  return testFilePath;
}

// Helper function to send a POST request with a file
function sendFileUpload(endpoint, filePath) {
  return new Promise((resolve, reject) => {
    console.log(`Testing file upload to: ${endpoint}`);
    
    const url = new URL(endpoint);
    const fileName = path.basename(filePath);
    const fileData = fs.readFileSync(filePath);
    
    // Generate a boundary for multipart/form-data
    const boundary = `----WebKitFormBoundary${Math.random().toString(16).substr(2)}`;
    
    // Prepare form data
    const formData = Buffer.concat([
      // File field
      Buffer.from(`--${boundary}\r\n`),
      Buffer.from(`Content-Disposition: form-data; name="file"; filename="${fileName}"\r\n`),
      Buffer.from('Content-Type: text/plain\r\n\r\n'),
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

// Main function to run the tests
async function runTests() {
  console.log('Starting upload endpoint tests...');
  console.log('===============================');
  
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
  
  console.log('\n=== Tests Completed ===');
  if (workingPrimaryEndpoint) {
    console.log(`\nRECOMMENDATION: Use ${workingPrimaryEndpoint} as your PRIMARY_UPLOAD_ENDPOINT in index.html`);
  } else {
    console.log('\nRECOMMENDATION: Continue using the fallback endpoint until one of the primary endpoints works');
  }
}

// Run the tests
runTests().catch(console.error); 