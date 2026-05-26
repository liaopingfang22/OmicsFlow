#!/bin/bash

set -e

docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Checking backend health..."
curl -f http://localhost:8000/health || echo "Backend not ready yet"

echo ""
echo "==================================="
echo "  Pipeline Test Platform Ready!"
echo "==================================="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "==================================="
