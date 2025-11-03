#!/bin/bash
# Clara Infrastructure - Quick Setup Script (Linux/Mac)

set -e

echo "========================================"
echo "Clara Infrastructure Setup"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.docker..."
    cp .env.docker .env
    echo "✅ .env file created"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

echo "🚀 Starting Clara infrastructure services..."
echo ""
docker-compose up -d

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "📊 Services started:"
docker-compose ps

echo ""
echo "🔗 Connection URLs for clara-agent/.env.local:"
echo ""
echo "  REDIS_URL=redis://localhost:6379"
echo "  DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara"
echo "  TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics"
echo ""
echo "💾 Storage backends:"
echo "  CACHE_STORAGE_BACKEND=redis"
echo "  ANALYTICS_STORAGE_BACKEND=timescale"
echo "  PREFERENCES_STORAGE_BACKEND=database"
echo ""
echo "========================================"
echo ""
echo "📝 Useful commands:"
echo "  make status        - Check status"
echo "  make logs          - View logs"
echo "  make stop          - Stop services"
echo "  make restart       - Restart services"
echo "  make redis-cli     - Connect to Redis"
echo "  make psql          - Connect to PostgreSQL"
echo ""
echo "Or use docker-compose directly:"
echo "  docker-compose ps         - Check status"
echo "  docker-compose logs -f    - View logs"
echo "  docker-compose stop       - Stop services"
echo ""
