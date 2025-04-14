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
BANNER_TEXT="Made by DDT,Cathay"  # Custom banner text - change this as needed

# Function to print fancy banner with custom message
print_banner() {
  local message="${1:-Infinity Installation}"
  
  echo -e "${CYAN}________       _____            __________              _____             ${NC}"
  echo -e "${CYAN}___  __ \_____ __  /______ _    ___  ____/_____________ ___(_)___________ ${NC}"
  echo -e "${CYAN}__  / / /  __ \`/  __/  __ \`/    __  __/  __  __ \\_  __ \`/_  /__  __ \\  _ \\${NC}"
  echo -e "${CYAN}_  /_/ // /_/ // /_ / /_/ /     _  /___  _  / / /  /_/ /_  / _  / / /  __/${NC}"
  echo -e "${CYAN}/_____/ \\__,_/ \\__/ \\__,_/      /_____/  /_/ /_/_\\__, / /_/  /_/ /_/\\___/ ${NC}"
  echo -e "${CYAN}                                                /____/                    ${NC}"
  echo
  
  # Center the message
  local term_width=$(tput cols 2>/dev/null || echo 80)
  local msg_length=${#message}
  local padding=$(( (term_width - msg_length) / 2 ))
  
  printf "%${padding}s" ""  # Print padding spaces
  echo -e "${YELLOW}${BOLD}${message}${NC}"
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
  
  printf "\n"
  printf "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}\n"
  printf "${BLUE}║ ${BOLD}%-56s${BLUE}║${NC}\n" "INSTALLATION REPORT"
  printf "${BLUE}╠════════════════════════════════════════════════════════════╣${NC}\n"
  printf "${BLUE}║ ${CYAN}%-15s${NC} %-40s${BLUE}║${NC}\n" "Install dir:" "$INSTALL_DIR"
  printf "${BLUE}║ ${CYAN}%-15s${NC} %-40s${BLUE}║${NC}\n" "Configuration:" "$(basename $CONFIG_FILE)"
  printf "${BLUE}║ ${CYAN}%-15s${NC} %-40s${BLUE}║${NC}\n" "Repository:" "$(basename $REPO_URL .git)"
  printf "${BLUE}║ ${CYAN}%-15s${NC} %-40s${BLUE}║${NC}\n" "Time elapsed:" "$duration seconds"
  printf "${BLUE}║ ${CYAN}%-15s${NC} ${GREEN}%-40s${NC}${BLUE}║${NC}\n" "Status:" "Installation successful"
  printf "${BLUE}║ ${CYAN}%-15s${NC} %-40s${BLUE}║${NC}\n" "Next steps:" "Run 'docker-compose up -d --build'"
  printf "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

# Start the installation process
clear
print_banner "$BANNER_TEXT"
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