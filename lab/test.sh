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

print_banner "超酷"