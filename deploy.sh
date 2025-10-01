#!/bin/bash

# Aurora Pro AI - One-Click Deployment Script
set -e

echo "🚀 Aurora Pro AI - Deployment Script"
echo "====================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
}

# Create .env file if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from template...${NC}"
        cp .env.example .env
        
        # Generate random secret key
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/your-secret-key-here-change-in-production/${SECRET_KEY}/g" .env
        
        echo -e "${GREEN}✓ .env file created${NC}"
        echo -e "${YELLOW}⚠ Please review and update .env with your settings${NC}"
    else
        echo -e "${GREEN}✓ .env file exists${NC}"
    fi
}

# Create necessary directories
setup_directories() {
    echo -e "${YELLOW}Creating directories...${NC}"
    mkdir -p data logs plugins config/grafana
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build
    echo -e "${GREEN}✓ Images built successfully${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
}

# Wait for services to be healthy
wait_for_services() {
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8000/health/ready > /dev/null; then
            echo -e "${GREEN}✓ API is healthy${NC}"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}Error: Services failed to become healthy${NC}"
        echo "Check logs with: docker-compose logs"
        exit 1
    fi
}

# Show service status
show_status() {
    echo ""
    echo "====================================="
    echo -e "${GREEN}✓ Aurora Pro AI deployed successfully!${NC}"
    echo "====================================="
    echo ""
    echo "Access the services:"
    echo "  🔹 FastAPI Backend:    http://localhost:8000"
    echo "  🔹 API Documentation:  http://localhost:8000/docs"
    echo "  🔹 Streamlit GUI:      http://localhost:8501"
    echo "  🔹 Prometheus:         http://localhost:9090"
    echo "  🔹 Grafana:           http://localhost:3000"
    echo "  🔹 Ollama:            http://localhost:11434"
    echo ""
    echo "Credentials:"
    echo "  Grafana - admin/admin"
    echo ""
    echo "Useful commands:"
    echo "  View logs:       docker-compose logs -f"
    echo "  Stop services:   docker-compose down"
    echo "  Restart:         docker-compose restart"
    echo "  View status:     docker-compose ps"
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    setup_env
    setup_directories
    build_images
    start_services
    wait_for_services
    show_status
}

# Run deployment
main
