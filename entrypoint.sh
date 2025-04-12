#!/bin/bash
set -e

# Set default values for environment variables
export PORT=${PORT:-3003}
export MONGO_HOST=${MONGO_HOST:-mongo}
export MONGO_URI=${MONGO_URI:-mongodb://root:example@$MONGO_HOST:27017/}
export CACHE_DURATION=${CACHE_DURATION:-300}
export RETRY_ATTEMPTS=${RETRY_ATTEMPTS:-5}
export RETRY_DELAY=${RETRY_DELAY:-5}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Starting with configuration:"
echo "PORT: $PORT"
echo "MONGO_HOST: $MONGO_HOST"
echo "CACHE_DURATION: $CACHE_DURATION"
echo "RETRY_ATTEMPTS: $RETRY_ATTEMPTS"
echo "LOG_LEVEL: $LOG_LEVEL"

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
for i in {1..30}; do
  if mongo --host ${MONGO_HOST} --eval "print(\"MongoDB connection established\")" > /dev/null 2>&1; then
    echo "MongoDB is ready!"
    break
  fi
  
  if [ $i -eq 30 ]; then
    echo "MongoDB not available after 30 attempts. Starting without MongoDB persistence."
    # Continue anyway - the application will use in-memory cache
  else
    echo "MongoDB not ready yet - sleeping 2s (attempt $i/30)"
    sleep 2
  fi
done

# Make script executable (in case of permission issues)
chmod +x crypto-data-server.py

# Start the crypto data server
echo "Starting Crypto Data Server on port $PORT..."
exec python crypto-data-server.py 