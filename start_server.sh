#!/bin/bash

# Kill any processes using port 8080 (just in case)
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start the HTTP server on port 8080
python3 -m http.server 8080

echo "Server started on http://localhost:8080" 