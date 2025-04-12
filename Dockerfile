FROM python:3.11-slim

WORKDIR /app

# Install MongoDB client and other dependencies
RUN apt-get update && apt-get install -y \
    mongodb-clients \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh crypto-data-server.py

# Set environment variables
ENV PORT=3003
ENV MONGO_HOST=mongo
ENV MONGO_URI=mongodb://root:example@mongo:27017/
ENV CACHE_DURATION=300
ENV RETRY_ATTEMPTS=5
ENV RETRY_DELAY=5
ENV LOG_LEVEL=INFO
# This should be overridden at runtime
ENV CMC_API_KEY=""

# Expose the server port
EXPOSE 3003

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"] 