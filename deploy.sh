#!/bin/bash

# Bulgarian Legal AI Assistant - Deployment Script
# This script builds and deploys the application using Docker

set -e  # Exit on any error

echo "🏛️ Bulgarian Legal AI Assistant - Deployment Script"
echo "=================================================="

# Check if .env file exists
if [[ ! -f .env ]]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create a .env file based on .env.example"
    echo "   Required variables:"
    echo "   - OPENAI_API_KEY"
    echo "   - GOOGLE_CSE_ID"
    echo "   - GOOGLE_CSE_API_KEY"
    exit 1
fi

# Check if required environment variables are set
echo "🔍 Checking environment variables..."
source .env

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ Error: OPENAI_API_KEY not set in .env file"
    exit 1
fi

if [[ -z "$GOOGLE_CSE_ID" ]]; then
    echo "❌ Error: GOOGLE_CSE_ID not set in .env file"
    exit 1
fi

if [[ -z "$GOOGLE_CSE_API_KEY" ]]; then
    echo "❌ Error: GOOGLE_CSE_API_KEY not set in .env file"
    exit 1
fi

echo "✅ Environment variables are configured"

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t bulgarian-legal-ai:latest .

if [[ $? -eq 0 ]]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Stop existing container if running
echo "🛑 Stopping existing container (if any)..."
docker-compose down 2>/dev/null || true

# Start the application
echo "🚀 Starting Bulgarian Legal AI Assistant..."
docker-compose up -d

if [[ $? -eq 0 ]]; then
    echo "✅ Application started successfully!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   • Main Interface: http://localhost:8000"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/api/health"
    echo ""
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
else
    echo "❌ Failed to start application"
    echo "📊 Check logs: docker-compose logs"
    exit 1
fi

# Wait a moment and check if container is healthy
echo "⏳ Checking application health..."
sleep 10

if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Application is healthy and ready!"
else
    echo "⚠️  Application may still be starting up..."
    echo "   Check status: docker-compose ps"
    echo "   View logs: docker-compose logs -f"
fi 