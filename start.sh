#!/bin/bash

echo "Starting Authenticated WebSocket Services..."
echo ""

# Check if docker compose is available
if command -v docker &> /dev/null; then
    # Try docker compose (newer version)
    if docker compose version &> /dev/null; then
        echo "Using 'docker compose'..."
        docker compose up -d --build
    # Try docker-compose (older version)
    elif command -v docker-compose &> /dev/null; then
        echo "Using 'docker-compose'..."
        docker-compose up -d --build
    else
        echo "Error: docker compose not found. Please install Docker Compose."
        exit 1
    fi
else
    echo "Error: Docker not found. Please install Docker first."
    exit 1
fi

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "Checking service health..."
curl -s http://localhost:8001/health || echo "Service not yet ready. Wait a few more seconds and try: curl http://localhost:8001/health"

echo ""
echo "Services started!"
echo "FastAPI is available at: http://localhost:8001"
echo "Test token endpoint: http://localhost:8001/auth/token?username=user1&user_id=user1"

