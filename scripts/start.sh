#!/bin/bash
# Start the trading bot

set -e

echo "=========================================="
echo "Starting Trading Bot"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "? .env file not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Start with Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Starting services with Docker Compose..."
    docker-compose up -d
    
    echo ""
    echo "? Services started!"
    echo ""
    echo "Access points:"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - MLflow: http://localhost:5000"
    echo "  - Redpanda Console: http://localhost:19644"
    echo ""
    echo "View logs: docker-compose logs -f trading_bot"
    echo "Stop services: docker-compose down"
else
    echo "? docker-compose not found. Please install Docker and Docker Compose."
    exit 1
fi
