#!/bin/bash

# Test script for Workflow API using Docker Compose
# This script sets up the Docker Compose environment, runs the API tests,
# and reports the results

set -e

echo "========================================"
echo "WORKFLOW API TEST SCRIPT"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed or not in PATH"
    exit 1
fi

echo "\n[1/4] Stopping any existing containers..."
docker compose down || true

echo "\n[2/4] Building and starting Docker Compose environment..."
docker compose up -d --build

echo "\n[3/4] Waiting for services to initialize (30 seconds)..."
sleep 30

echo "\n[4/4] Running workflow API tests..."
docker compose exec backend python test_workflow_api.py

TEST_EXIT_CODE=$?

echo "\nTest execution completed with exit code: $TEST_EXIT_CODE"

# Optional: Stop containers after tests
if [ "$1" == "--down" ]; then
    echo "\nStopping Docker Compose environment..."
    docker compose down
fi

# Return the test exit code
exit $TEST_EXIT_CODE