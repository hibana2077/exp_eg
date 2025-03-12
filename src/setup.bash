#!/bin/bash

# ANSI color codes for green checkmark
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print green checkmark and message
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

# Create directory structure
mkdir -p /var/infinity
print_success "Created directory /var/infinity"

# Check if resources and config already exist
if [ -d "/var/infinity/resource" ] && [ -f "/var/infinity/infinity_conf.toml" ]; then
  print_success "Resources already installed"
else
  # Copy config file
  cp ./infinity_conf.toml /var/infinity/infinity_conf.toml
  if [ $? -eq 0 ]; then
    print_success "Copied configuration file"
  else
    echo "Failed to copy configuration file"
    exit 1
  fi
  
  # Clone the repository
  git clone https://github.com/infiniflow/resource.git
  if [ $? -eq 0 ]; then
    print_success "Cloned resource repository"
  else
    echo "Failed to clone repository"
    exit 1
  fi
  
  # Move resource directory to destination
  mv resource /var/infinity/
  if [ $? -eq 0 ]; then
    print_success "Moved resources to /var/infinity/"
  else
    echo "Failed to move resources"
    exit 1
  fi
  
  print_success "Setup completed successfully"
fi