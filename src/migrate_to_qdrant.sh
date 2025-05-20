#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print step header
print_step() {
  echo -e "${BLUE}[STEP]${NC} ${BOLD}$1${NC}"
}

# Function to print success message
print_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to print error message
print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print warning message
print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
  echo -e "\n${CYAN}==========================================================${NC}"
  echo -e "${CYAN}= ${BOLD}$1${NC} ${CYAN}=${NC}"
  echo -e "${CYAN}==========================================================${NC}\n"
}

# Check if docker-compose is running
check_docker_status() {
  local container_name=$1
  if docker ps | grep -q $container_name; then
    return 0 # Container is running
  else
    return 1 # Container is not running
  fi
}

# Main function
main() {
  print_header "Infinity to Qdrant Migration Tool"
  echo -e "This script helps you migrate from Infinity DB to Qdrant vector database."
  echo -e "Make sure your docker-compose is running before proceeding.\n"
  
  # Check if required containers are running
  print_step "Checking if required containers are running..."
  
  if ! check_docker_status "qdrant"; then
    print_error "Qdrant container is not running. Please start it with 'docker-compose up -d db_qdrant'"
    exit 1
  fi
  
  if ! check_docker_status "db_mongo"; then
    print_error "MongoDB container is not running. Please start it with 'docker-compose up -d db_mongo'"
    exit 1
  fi
  
  print_success "Required containers are running."

  # Menu options
  echo -e "\nPlease select an option:"
  echo -e "  ${BOLD}1${NC}. Update main.py to use Qdrant"
  echo -e "  ${BOLD}2${NC}. Migrate data from Infinity to Qdrant"
  echo -e "  ${BOLD}3${NC}. Run both steps (Update and Migrate)"
  echo -e "  ${BOLD}q${NC}. Quit"
  
  read -p "Enter your choice [1-3/q]: " choice
  
  case $choice in
    1)
      update_main_file
      ;;
    2)
      migrate_data
      ;;
    3)
      update_main_file
      migrate_data
      ;;
    q|Q)
      echo -e "\nExiting migration tool."
      exit 0
      ;;
    *)
      print_error "Invalid option. Exiting."
      exit 1
      ;;
  esac
}

update_main_file() {
  print_header "Updating main.py to use Qdrant"
  
  # Backup original main.py
  print_step "Creating backup of main.py..."
  if cp ./core/main.py ./core/main.py.infinity.bak; then
    print_success "Backup created at ./core/main.py.infinity.bak"
  else
    print_error "Failed to create backup. Aborting update."
    return 1
  fi
  
  # Copy the new main file
  print_step "Updating main.py to use Qdrant..."
  if cp ./core/main_with_qdrant.py ./core/main.py; then
    print_success "main.py updated successfully."
  else
    print_error "Failed to update main.py. Please check file permissions."
    return 1
  fi
  
  # Set USE_QDRANT to True
  print_step "Setting USE_QDRANT to True in main.py..."
  if sed -i '' 's/USE_QDRANT = False/USE_QDRANT = True/g' ./core/main.py 2>/dev/null || sed -i 's/USE_QDRANT = False/USE_QDRANT = True/g' ./core/main.py; then
    print_success "USE_QDRANT set to True."
  else
    print_warning "Could not automatically set USE_QDRANT to True. Please edit main.py manually."
  fi
  
  print_step "Rebuilding core container..."
  if docker-compose up -d --build core; then
    print_success "Core container rebuilt successfully."
  else
    print_error "Failed to rebuild core container. Please check docker logs."
    return 1
  fi
  
  echo -e "\n${GREEN}main.py has been updated to use Qdrant.${NC}"
  echo -e "You can test the system with the new configuration."
  echo -e "If you encounter issues, you can restore the backup with:"
  echo -e "  ${BOLD}cp ./core/main.py.infinity.bak ./core/main.py${NC}"
  echo -e "  ${BOLD}docker-compose up -d --build core${NC}\n"
  
  return 0
}

migrate_data() {
  print_header "Migrating Data from Infinity to Qdrant"
  
  # Check if Infinity is running
  print_step "Checking if Infinity container is running..."
  if ! check_docker_status "infinity"; then
    print_warning "Infinity container is not running. This may cause migration to fail."
    read -p "Do you want to continue anyway? [y/N]: " continue_choice
    if [[ ! $continue_choice =~ ^[Yy]$ ]]; then
      print_error "Aborting migration."
      return 1
    fi
  else
    print_success "Infinity container is running."
  fi
  
  # Run the migration script
  print_step "Running migration script in core container..."
  if docker-compose exec core python -c "from utils.migration_helper import migrate_all_kbs; migrate_all_kbs()"; then
    print_success "Migration script executed successfully."
  else
    print_error "Migration script execution failed. Please check logs for details."
    return 1
  fi
  
  echo -e "\n${GREEN}Data migration process has been completed.${NC}"
  echo -e "Please verify that your data is accessible through the Qdrant backend."
  
  return 0
}

# Run the main function
main
