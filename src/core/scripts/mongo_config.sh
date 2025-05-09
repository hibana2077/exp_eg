#!/bin/bash

# MongoDB Configuration Script
# This script helps switch between using MongoDB Atlas and local MongoDB

# Default values
ENV_FILE="../.env"
CONFIG_ACTION="show"
TARGET="local"

# Display help information
show_help() {
    echo "MongoDB Configuration Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -a, --action ACTION     Action to perform: show, use-atlas, use-local"
    echo "  -e, --env FILE          Path to .env file (default: ../.env)"
    echo ""
    echo "Examples:"
    echo "  $0 --action show                 Show current MongoDB configuration"
    echo "  $0 --action use-atlas            Switch to using MongoDB Atlas"
    echo "  $0 --action use-local            Switch to using local MongoDB"
    echo ""
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -a|--action)
                CONFIG_ACTION="$2"
                shift 2
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# Check if the environment file exists
check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "Error: Environment file $ENV_FILE does not exist"
        echo "Create the file or specify a different file with --env"
        exit 1
    fi
}

# Show current MongoDB configuration
show_config() {
    echo "Current MongoDB Configuration:"
    
    # Check if MongoDB Atlas is enabled
    ATLAS_ENABLED=$(grep "MONGO_ATLAS_ENABLED" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
    
    if [[ "$ATLAS_ENABLED" == "true" ]]; then
        echo "Using: MongoDB Atlas"
        ATLAS_URI=$(grep "MONGO_ATLAS_URI" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
        ATLAS_USER=$(grep "MONGO_ATLAS_USERNAME" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
        echo "URI: $ATLAS_URI"
        echo "Username: $ATLAS_USER"
    else
        echo "Using: Local MongoDB"
        MONGO_SERVER=$(grep "MONGO_SERVER" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
        MONGO_USER=$(grep "MONGO_INITDB_ROOT_USERNAME" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"')
        echo "Server: $MONGO_SERVER"
        echo "Username: $MONGO_USER"
    fi
}

# Switch to using MongoDB Atlas
use_atlas() {
    echo "Switching to MongoDB Atlas..."
    
    # Update the MONGO_ATLAS_ENABLED flag
    sed -i.bak 's/MONGO_ATLAS_ENABLED="false"/MONGO_ATLAS_ENABLED="true"/g' "$ENV_FILE"
    
    # Check if the substitution was successful
    if grep -q 'MONGO_ATLAS_ENABLED="true"' "$ENV_FILE"; then
        echo "MongoDB Atlas enabled successfully"
        echo ""
        echo "Please make sure your MongoDB Atlas credentials are set properly:"
        echo "- MONGO_ATLAS_URI"
        echo "- MONGO_ATLAS_USERNAME"
        echo "- MONGO_ATLAS_PASSWORD"
        echo ""
        echo "You will need to restart your services for the changes to take effect."
    else
        echo "Error: Failed to enable MongoDB Atlas. Please check your .env file."
        exit 1
    fi
}

# Switch to using local MongoDB
use_local() {
    echo "Switching to local MongoDB..."
    
    # Update the MONGO_ATLAS_ENABLED flag
    sed -i.bak 's/MONGO_ATLAS_ENABLED="true"/MONGO_ATLAS_ENABLED="false"/g' "$ENV_FILE"
    
    # Check if the substitution was successful
    if grep -q 'MONGO_ATLAS_ENABLED="false"' "$ENV_FILE"; then
        echo "Local MongoDB enabled successfully"
        echo ""
        echo "Please make sure your local MongoDB credentials are set properly:"
        echo "- MONGO_SERVER"
        echo "- MONGO_INITDB_ROOT_USERNAME"
        echo "- MONGO_INITDB_ROOT_PASSWORD"
        echo ""
        echo "You will need to restart your services for the changes to take effect."
    else
        echo "Error: Failed to enable local MongoDB. Please check your .env file."
        exit 1
    fi
}

# Main function
main() {
    parse_args "$@"
    check_env_file
    
    case "$CONFIG_ACTION" in
        show)
            show_config
            ;;
        use-atlas)
            use_atlas
            ;;
        use-local)
            use_local
            ;;
        *)
            echo "Unknown action: $CONFIG_ACTION"
            show_help
            ;;
    esac
}

# Run the script
main "$@"
