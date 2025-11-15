#!/bin/bash
# Test script for Docker deployment

set -e

echo "🧪 Testing FinanceY Docker Deployment..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Use docker compose (v2) if available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Test backend build
echo "1. Testing backend build..."
docker build -f Dockerfile.backend -t financey-backend-test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Backend build successful"
else
    echo "   ❌ Backend build failed"
    exit 1
fi

# Test frontend-react build
echo "2. Testing React frontend build..."
docker build -f Dockerfile.frontend-react -t financey-frontend-react-test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ React frontend build successful"
else
    echo "   ❌ React frontend build failed"
    exit 1
fi

# Test frontend-streamlit build
echo "3. Testing Streamlit frontend build..."
docker build -f Dockerfile.frontend -t financey-frontend-streamlit-test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Streamlit frontend build successful"
else
    echo "   ❌ Streamlit frontend build failed"
    exit 1
fi

# Test docker-compose config
echo "4. Testing docker-compose configuration..."
$DOCKER_COMPOSE config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ docker-compose.yml is valid"
else
    echo "   ❌ docker-compose.yml has errors"
    exit 1
fi

# Test production compose config
echo "5. Testing production docker-compose configuration..."
$DOCKER_COMPOSE -f docker-compose.prod.yml config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ docker-compose.prod.yml is valid"
else
    echo "   ❌ docker-compose.prod.yml has errors"
    exit 1
fi

echo ""
echo "✅ All tests passed!"
echo ""
echo "You can now deploy with:"
echo "  ./docker-start.sh"
echo "  or"
echo "  docker-compose up -d"

