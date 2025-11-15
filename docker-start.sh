#!/bin/bash
# Quick start script for Docker deployment of FinanceY

set -e

echo "🐳 Starting FinanceY with Docker..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "⚠️  Please edit .env and add your OPENAI_API_KEY before continuing!"
        echo ""
        read -p "Press Enter to continue after adding your API key, or Ctrl+C to cancel..."
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose."
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "📦 Building Docker images..."
$DOCKER_COMPOSE build

echo ""
echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check backend health
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend health check failed after 30 attempts"
    else
        echo "   Waiting for backend... ($i/30)"
        sleep 2
    fi
done

# Check frontend health (Streamlit)
echo "Checking Streamlit frontend health..."
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Streamlit frontend is healthy"
else
    echo "⚠️  Streamlit frontend health check failed (may still be starting)"
fi

# Check React frontend health
echo "Checking React frontend health..."
if curl -f http://localhost:3000/health > /dev/null 2>&1 || curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ React frontend is healthy"
else
    echo "⚠️  React frontend health check failed (may still be starting)"
fi

echo ""
echo "✅ FinanceY is running!"
echo ""
echo "📍 Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Streamlit Frontend: http://localhost:8501"
echo "   • React Frontend: http://localhost:3000"
echo ""
echo "📊 View logs:"
echo "   • All services: $DOCKER_COMPOSE logs -f"
echo "   • Backend only: $DOCKER_COMPOSE logs -f backend"
echo "   • Streamlit frontend: $DOCKER_COMPOSE logs -f frontend-streamlit"
echo "   • React frontend: $DOCKER_COMPOSE logs -f frontend-react"
echo ""
echo "🛑 Stop services:"
echo "   $DOCKER_COMPOSE down"
echo ""
