#!/bin/bash
set -e

# Nebula Toolset Container Entrypoint Script
# Supports multiple modes: api, cli, tool execution, and custom commands

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Initialize application directories and permissions
initialize_app() {
    info "Initializing Nebula application..."
    
    # Ensure required directories exist
    mkdir -p /home/nebula/.nebula/cli_logs
    mkdir -p /app/.logs
    mkdir -p /app/.storage
    mkdir -p /app/.secrets
    
    # Set proper permissions
    chmod 755 /home/nebula/.nebula
    chmod 755 /home/nebula/.nebula/cli_logs
    
    success "Application initialized successfully"
}

# Start the API service
start_api() {
    info "Starting Nebula API service..."
    info "API will be available at http://0.0.0.0:8000"
    
    # Start with uvicorn for better container compatibility
    exec python -m uvicorn src.api.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info \
        --access-log
}

# Start the CLI in interactive mode
start_cli() {
    info "Starting Nebula CLI in interactive mode..."
    exec python src/cli/app.py
}

# Run a specific tool
run_tool() {
    local tool_name="$1"
    shift
    info "Running tool: $tool_name"
    exec python src/cli/app.py --run-tool "$tool_name" "$@"
}

# Show help information
show_help() {
    cat << EOF
Nebula Toolset Container

USAGE:
    container-entrypoint.sh [COMMAND] [ARGS...]

COMMANDS:
    api                     Start the API service (default)
    cli                     Start CLI in interactive mode
    tool <name> [args]      Run a specific tool
    system-info             Show system information
    toolset-info            Show toolset information
    bash                    Start bash shell
    help                    Show this help

EXAMPLES:
    # Start API service
    podman run -p 8000:8000 nebula-toolset

    # Start CLI interactively
    podman run -it nebula-toolset cli

    # Run a specific tool
    podman run nebula-toolset tool gcp_vm_manager --list-all

    # Get system info
    podman run nebula-toolset system-info

    # Get shell access
    podman run -it nebula-toolset bash

ENVIRONMENT VARIABLES:
    NEBULA_CLI_DEBUG        Set to 1 to enable debug logging
    PYTHONPATH              Python module search path (set to /app/src)

PORTS:
    8000                    API service port

VOLUMES:
    /home/nebula/.nebula    User data and configuration
    /app/.logs              Application logs
    /app/.storage           Application storage
    /app/.secrets           Secrets (mount with proper permissions)

For more information, see the README.md file or visit:
https://github.com/nebula/toolset
EOF
}

# Main entrypoint logic
main() {
    # Initialize the application
    initialize_app
    
    # Parse command line arguments
    case "${1:-api}" in
        "api")
            start_api
            ;;
        "cli")
            start_cli
            ;;
        "tool")
            if [ -z "$2" ]; then
                error "Tool name is required"
                echo "Usage: $0 tool <tool_name> [args...]"
                exit 1
            fi
            shift
            run_tool "$@"
            ;;
        "system-info")
            python src/cli/app.py --system-info
            ;;
        "toolset-info")
            python src/cli/app.py --toolset-info
            ;;
        "bash"|"shell")
            info "Starting bash shell..."
            exec /bin/bash
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            # If it's a python file or looks like a command, execute it directly
            if [[ "$1" == *.py ]] || command -v "$1" > /dev/null 2>&1; then
                info "Executing command: $*"
                exec "$@"
            else
                error "Unknown command: $1"
                echo ""
                show_help
                exit 1
            fi
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
