#!/bin/bash

# Simple script to start Python HTTP server for the static HTML site
echo "Starting HTTP server at http://localhost:8000"
python3 -m http.server 8000 &
SERVER_PID=$!

echo "Starting backup upload handler at http://localhost:8001"
cd upload-handler
python3 upload_server.py &
UPLOAD_PID=$!

echo "Servers running. Press Ctrl+C to stop both servers."
trap "kill $SERVER_PID $UPLOAD_PID; exit" INT
wait 