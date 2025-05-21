#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
NC='\033[0m' # No Color
CHECK_MARK="${GREEN}✓${NC}"

# Function to print status with checkmark
print_status() {
    local package=$1
    local version=$2
    echo -e "${package} ${version} ${CHECK_MARK}"
}

# Update repositories
echo "Updating repositories..."
apt update && print_status "apt update" "completed"

# Install Docker
echo "Installing Docker..."
curl -sSL https://get.docker.com | sh && print_status "Docker" "latest"

# Install btop and python3-pip
echo "Installing btop and python3-pip..."
apt install btop python3-pip -y && print_status "btop" "latest" && print_status "python3-pip" "latest"

# Install Docker Compose
echo "Installing Docker Compose..."
VERSION=$(curl --silent https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*\d')
DESTINATION=/usr/bin/docker-compose
sudo curl -L https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m) -o $DESTINATION
sudo chmod 755 $DESTINATION && print_status "Docker Compose" "${VERSION}"

echo -e "\n${GREEN}All installations completed successfully!${NC}"