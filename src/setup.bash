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
INSTALL_DIR="/var/infinity"
REPO_URL="https://github.com/infiniflow/resource.git"
CONFIG_FILE="./infinity_conf.toml"
START_TIME=$(date +%s)

# Function to print fancy banner
print_banner() {
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║                                                            ║${NC}"
  echo -e "${BLUE}║  ${CYAN}█ █▄░█ █▀▀ █ █▄░█ █ ▀█▀ █▄█   ${YELLOW}█ █▄░█ █▀ ▀█▀ ▄▀█ █   █   ${BLUE}║${NC}"
  echo -e "${BLUE}║  ${CYAN}█ █░▀█ █▀░ █ █░▀█ █ ░█░ ░█░   ${YELLOW}█ █░▀█ ▄█ ░█░ █▀█ █▄▄ █▄▄ ${BLUE}║${NC}"
  echo -e "${BLUE}║                                                            ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
  echo
}

# Function to print step with animation
print_step() {
  echo -ne "${YELLOW}⟳${NC} $1... "
  sleep 0.5
}

# Function to print success with checkmark
print_success() {
  echo -e "\r${GREEN}✓${NC} $1"
}

# Function to print failure with cross
print_failure() {
  echo -e "\r${RED}✗${NC} $1"
  exit 1
}

# Function to print report
print_report() {
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
  
  echo
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║ ${BOLD}INSTALLATION REPORT${NC}                                        ${BLUE}║${NC}"
  echo -e "${BLUE}╠════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${BLUE}║ ${CYAN}Installation directory:${NC} $INSTALL_DIR                        ${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Configuration:${NC} $(basename $CONFIG_FILE)                         ${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Resource repository:${NC} $(basename $REPO_URL .git)                ${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Time elapsed:${NC} $duration seconds                             ${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Status:${NC} ${GREEN}Installation successful${NC}                          ${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Next steps:${NC} Run 'docker-compose up -d --build' ${BLUE}║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

# Start the installation process
clear
print_banner
echo -e "${BOLD}Starting Infinity installation process...${NC}"
echo

# Create directory structure
print_step "Creating main directory"
mkdir -p $INSTALL_DIR
if [ $? -eq 0 ]; then
  print_success "Created directory $INSTALL_DIR"
else
  print_failure "Failed to create directory $INSTALL_DIR"
fi

# Check if resources and config already exist
if [ -d "$INSTALL_DIR/resource" ] && [ -f "$INSTALL_DIR/infinity_conf.toml" ]; then
  print_success "Resources already installed in $INSTALL_DIR"
else
  # Copy config file
  print_step "Copying configuration file"
  cp $CONFIG_FILE $INSTALL_DIR/infinity_conf.toml
  if [ $? -eq 0 ]; then
    print_success "Configuration file deployed to $INSTALL_DIR"
  else
    print_failure "Failed to copy configuration file"
  fi
  
  # Clone the repository
  print_step "Cloning resource repository"
  git clone --quiet $REPO_URL
  if [ $? -eq 0 ]; then
    print_success "Resource repository cloned successfully"
  else
    print_failure "Failed to clone repository"
  fi
  
  # Move resource directory to destination
  print_step "Moving resources to installation directory"
  mv resource $INSTALL_DIR/
  if [ $? -eq 0 ]; then
    print_success "Resources deployed to $INSTALL_DIR"
  else
    print_failure "Failed to move resources"
  fi
  
  echo
  echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}${GREEN}✓ All installation steps completed successfully! ${NC}"
  echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
fi

# Print the final report
print_report