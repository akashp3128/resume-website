#!/bin/bash

# Simple script to start Python HTTP server for the static HTML site
echo "Starting HTTP server at http://localhost:8000"
python3 -m http.server 8000 