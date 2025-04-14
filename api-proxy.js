const httpProxy = require('http-proxy');
const http = require('http');
const url = require('url');

// Create a proxy server with custom router
const proxy = httpProxy.createProxyServer({});

// Target API URL - CoinGecko/MongoDB backend
const TARGET_API = 'http://localhost:3000';

// Handle proxy errors
proxy.on('error', function(err, req, res) {
  console.error('Proxy error:', err);
  res.writeHead(500, {
    'Content-Type': 'text/plain'
  });
  res.end('Proxy error: ' + err.message);
});

// Create the server
const server = http.createServer(function(req, res) {
  // Parse the request URL
  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  
  // Add CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  console.log(`Proxying request to: ${path}`);

  // Forward the request to the target API
  proxy.web(req, res, {
    target: TARGET_API,
    changeOrigin: true
  });
});

// Server port - Use a different port than the main web server (8000)
const PORT = process.env.PORT || 8002;

// Start the server
server.listen(PORT, function() {
  console.log(`API Proxy Server running on port ${PORT}`);
  console.log(`Proxying requests to ${TARGET_API}`);
}); 