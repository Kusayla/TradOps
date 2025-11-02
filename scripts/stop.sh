#!/bin/bash
# Stop the trading bot

set -e

echo "=========================================="
echo "Stopping Trading Bot"
echo "=========================================="

if command -v docker-compose &> /dev/null; then
    docker-compose down
    echo "? Services stopped"
else
    echo "? docker-compose not found"
    exit 1
fi
