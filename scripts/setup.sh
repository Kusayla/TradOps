#!/bin/bash
# Setup script for the trading bot

set -e

echo "=========================================="
echo "Trading Bot Setup Script"
echo "=========================================="

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "? Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "? Python version: $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data logs models config/grafana/dashboards config/grafana/datasources

# Copy environment file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "??  Please edit .env file with your API keys and configuration"
fi

# Create Grafana datasource config
cat > config/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

echo ""
echo "=========================================="
echo "? Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Start services: ./scripts/start.sh"
echo "3. Or use Docker: docker-compose up -d"
echo ""
