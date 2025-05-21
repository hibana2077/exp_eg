#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Variables
START_TIME=$(date +%s)
BANNER_TEXT="Made by DDT,Cathay"  # Custom banner text - change this as needed

# Function to print fancy banner with custom message
print_banner() {
  local message="${1:-Qdrant Setup}"
  local length=${#message}
  local border=$(printf '%*s' "$length" '' | tr ' ' '=')
  
  echo -e "\n${BLUE}${border}${NC}"
  echo -e "${CYAN}${BOLD}${message}${NC}"
  echo -e "${BLUE}${border}${NC}\n"
}

# Function to print step headers
print_step() {
  echo -e "\n${BLUE}=== ${CYAN}${1}${BLUE} ===${NC}"
}

# Function to check command status and print status message
check_status() {
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ $1${NC}"
  else
    echo -e "${RED}✗ $1${NC}"
    exit 1
  fi
}

# Main banner
clear
print_banner "${BANNER_TEXT}"

# Check if Docker is installed
print_step "Checking Docker installation"
if command -v docker &> /dev/null; then
  echo -e "${GREEN}✓ Docker is installed${NC}"
else
  echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
  exit 1
fi

# Check if Docker Compose is installed
print_step "Checking Docker Compose installation"
if command -v docker-compose &> /dev/null; then
  echo -e "${GREEN}✓ Docker Compose is installed${NC}"
else
  echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
  exit 1
fi

# Create data directories
print_step "Creating data directories"
sudo mkdir -p /data/qdrant-data /data/minio-data /data/mongo-data
sudo chmod -R 777 /data
check_status "Data directories created"

# Set up environment variables
print_step "Setting up environment variables"
if [ ! -f .env ]; then
  cat > .env << EOL
MINIO_ROOT_USER=root
MINIO_ROOT_PASSWORD=password
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=example
OPENROUTE_API_KEY=
LLM_MODEL=qwen:7b
EOL
  check_status "Created .env file"
else
  echo -e "${YELLOW}⚠ .env file already exists, skipping${NC}"
fi

# Start the services
print_step "Starting services with Docker Compose"
docker-compose up -d
check_status "Services started"

# Calculate and display time taken
END_TIME=$(date +%s)
TIME_TAKEN=$((END_TIME - START_TIME))
print_step "Setup Complete!"
echo -e "${GREEN}Setup completed in ${TIME_TAKEN} seconds.${NC}"
echo -e "${YELLOW}Access the web interface at http://localhost:4321${NC}"