#!/bin/bash
# Production deployment script for FinanceY

set -e

echo "🚀 Deploying FinanceY to Production..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with required environment variables."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Build and start services
echo "📦 Building production images..."
$DOCKER_COMPOSE -f docker-compose.prod.yml build --no-cache

echo ""
echo "🚀 Starting production services..."
$DOCKER_COMPOSE -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check backend health
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend health check failed"
    else
        sleep 2
    fi
done

# Check frontend health
echo "Checking frontend health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend health check failed (may still be starting)"
fi

echo ""
echo "✅ FinanceY deployed successfully!"
echo ""
echo "📍 Access your application:"
echo "   • Frontend: http://localhost"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""

