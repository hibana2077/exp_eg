# Function to print report
# Function to print report
print_report() {
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
  local width=56
  
  echo
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║ ${BOLD}INSTALLATION REPORT$(printf '%*s' $((width-20)) "")${BLUE}║${NC}"
  echo -e "${BLUE}╠════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${BLUE}║ ${CYAN}Installation directory:${NC} $INSTALL_DIR$(printf '%*s' $((width-24-${#INSTALL_DIR})) "")${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Configuration:${NC} $(basename $CONFIG_FILE)$(printf '%*s' $((width-15-${#CONFIG_FILE})) "")${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Resource repository:${NC} $(basename $REPO_URL .git)$(printf '%*s' $((width-20-${#REPO_URL}+4)) "")${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Time elapsed:${NC} $duration seconds$(printf '%*s' $((width-15-${#duration}-8)) "")${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Status:${NC} ${GREEN}Installation successful${NC}$(printf '%*s' $((width-8-22)) "")${BLUE}║${NC}"
  echo -e "${BLUE}║ ${CYAN}Next steps:${NC} Run 'docker-compose up -d --build'$(printf '%*s' $((width-11-33)) "")${BLUE}║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

# test function
print_report