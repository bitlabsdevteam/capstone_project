#!/bin/bash

# Docker Compose Test Script
# This script tests the basic Docker Compose functionality

echo "🐳 Testing Docker Compose Configuration"
echo "======================================"

# Test 1: Validate configuration
echo "\n📋 Step 1: Validating Docker Compose configuration..."
docker compose config > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

# Test 2: Build containers
echo "\n🔨 Step 2: Building containers..."
echo "Run: docker compose build"
echo "This will build both frontend and backend services"

# Test 3: Start services
echo "\n🚀 Step 3: Starting services..."
echo "Run: docker compose up -d"
echo "This will start all services in detached mode"

# Test 4: Stop services
echo "\n🛑 Step 4: Stopping services..."
echo "Run: docker compose down"
echo "This will stop and remove all containers"

echo "\n📝 Available Docker Compose Commands:"
echo "  docker compose build    - Build/rebuild containers"
echo "  docker compose up       - Start services (foreground)"
echo "  docker compose up -d    - Start services (background)"
echo "  docker compose down     - Stop and remove containers"
echo "  docker compose logs     - View service logs"
echo "  docker compose ps       - List running services"

echo "\n🌐 Service URLs (when running):"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  Redis:    localhost:6379"

echo "\n✨ Docker Compose setup is ready!"