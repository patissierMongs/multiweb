#!/bin/bash

# MultiWeb Quick Start Script
# Starts the entire stack with Docker Compose

set -e

echo "=========================================="
echo "MultiWeb Quick Start"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if containers are already running
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  Some containers are already running"
    read -p "Stop and restart? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing containers..."
        docker-compose down
    else
        echo "Aborted"
        exit 0
    fi
fi

# Start services
echo "Starting services..."
echo ""
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U multiweb > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "⚠️  Redis is not ready yet"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is ready"
else
    echo "⚠️  API is not ready yet (may still be starting)"
fi

# Initialize database
echo ""
read -p "Initialize database with demo data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Initializing database..."
    docker-compose exec -T api python /app/../scripts/init_db.py || true
fi

echo ""
echo "=========================================="
echo "✓ MultiWeb is running!"
echo "=========================================="
echo ""
echo "Access the services:"
echo "  • API Docs:    http://localhost:8000/docs"
echo "  • API Health:  http://localhost:8000/health"
echo "  • Grafana:     http://localhost:3000 (admin/admin)"
echo "  • Prometheus:  http://localhost:9090"
echo ""
echo "Demo credentials:"
echo "  • Email:    demo@multiweb.com"
echo "  • Password: demo123!"
echo ""
echo "View logs:"
echo "  docker-compose logs -f api"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
echo "=========================================="
