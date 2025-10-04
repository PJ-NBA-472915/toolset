# Nebula Simplified CLI Makefile

.PHONY: help list-vms start-vm stop-vm update-ssh-config cli-help devbox-setup container-build container-run container-api container-cli container-shell container-clean container-help

# Variables
PID_FILE := .api.pid
LOG_DIR := .logs
IMAGE_NAME := nebula-toolset
IMAGE_TAG := latest
CONTAINER_NAME := nebula-service
API_PORT := 8000

# Default target
help:
	@echo "Nebula Simplified CLI - VM Management"
	@echo "====================================="
	@echo ""
	@echo "VM Management Commands (using devbox):"
	@echo "  list-vms         - List all VM instances"
	@echo "  start-vm         - Start a VM instance (auto-updates SSH config)"
	@echo "  stop-vm          - Stop a VM instance"
	@echo "  update-ssh-config - Update SSH config for a VM instance"
	@echo "  cli-help         - Show detailed CLI help"
	@echo ""
	@echo "Setup:"
	@echo "  devbox-setup     - Setup devbox environment"
	@echo ""
	@echo "Container Commands:"
	@echo "  container-build  - Build the container image"
	@echo "  container-api    - Run API service in container"
	@echo "  container-cli    - Run CLI interactively in container"
	@echo "  container-shell  - Start shell in container"
	@echo "  container-clean  - Clean up containers and images"
	@echo "  container-help   - Show detailed container help"
	@echo ""

start:
	@bash -c "nohup venv/bin/python src/cli/app.py start > /dev/null 2>&1 & echo \$$! > .api.pid"
	@echo "✅ API service started with PID: `cat $(PID_FILE)`"

stop:
	@kill `cat $(PID_FILE)` && rm $(PID_FILE)
	@echo "✅ API service stopped."

tail:
	@tail -f $(LOG_DIR)/nebula_cli_*.log

# Container Commands

# Build the container image
container-build:
	@echo "🔨 Building container image: $(IMAGE_NAME):$(IMAGE_TAG)"
	@chmod +x container-entrypoint.sh
	@podman build -t $(IMAGE_NAME):$(IMAGE_TAG) -f Containerfile .
	@echo "✅ Container image built successfully"
	@podman images $(IMAGE_NAME)

# Run API service in container
container-api:
	@echo "🚀 Starting API service in container..."
	@mkdir -p $(HOME)/.nebula-container/{nebula,logs,storage,secrets}
	@podman run --rm -d \
		--name $(CONTAINER_NAME) \
		-p $(API_PORT):8000 \
		-v $(HOME)/.nebula-container/nebula:/home/nebula/.nebula:Z \
		-v $(HOME)/.nebula-container/logs:/app/.logs:Z \
		-v $(HOME)/.nebula-container/storage:/app/.storage:Z \
		-v $(HOME)/.nebula-container/secrets:/app/.secrets:Z \
		$(IMAGE_NAME):$(IMAGE_TAG) api
	@echo "✅ API service started in container"
	@echo "📡 API available at: http://localhost:$(API_PORT)"
	@echo "🔍 View logs: podman logs -f $(CONTAINER_NAME)"

# Run CLI interactively in container
container-cli:
	@echo "💻 Starting CLI in container..."
	@mkdir -p $(HOME)/.nebula-container/{nebula,logs,storage,secrets}
	@podman run --rm -it \
		--name $(CONTAINER_NAME)-cli \
		-v $(HOME)/.nebula-container/nebula:/home/nebula/.nebula:Z \
		-v $(HOME)/.nebula-container/logs:/app/.logs:Z \
		-v $(HOME)/.nebula-container/storage:/app/.storage:Z \
		-v $(HOME)/.nebula-container/secrets:/app/.secrets:Z \
		$(IMAGE_NAME):$(IMAGE_TAG) cli

# Start shell in container for debugging
container-shell:
	@echo "🐚 Starting shell in container..."
	@mkdir -p $(HOME)/.nebula-container/{nebula,logs,storage,secrets}
	@podman run --rm -it \
		--name $(CONTAINER_NAME)-shell \
		-v $(HOME)/.nebula-container/nebula:/home/nebula/.nebula:Z \
		-v $(HOME)/.nebula-container/logs:/app/.logs:Z \
		-v $(HOME)/.nebula-container/storage:/app/.storage:Z \
		-v $(HOME)/.nebula-container/secrets:/app/.secrets:Z \
		$(IMAGE_NAME):$(IMAGE_TAG) shell

# Clean up containers and images
container-clean:
	@echo "🧹 Cleaning up containers and images..."
	@podman stop $(CONTAINER_NAME) || true
	@podman rm $(CONTAINER_NAME) || true
	@podman stop $(CONTAINER_NAME)-cli || true
	@podman rm $(CONTAINER_NAME)-cli || true
	@podman stop $(CONTAINER_NAME)-shell || true
	@podman rm $(CONTAINER_NAME)-shell || true
	@echo "🗑️  Remove image? (y/N): "; \
	read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		podman rmi $(IMAGE_NAME):$(IMAGE_TAG) || true; \
		echo "✅ Container image removed"; \
	else \
		echo "📦 Container image kept"; \
	fi
	@echo "✅ Cleanup completed"

# Show detailed container help
container-help:
	@echo "Nebula Toolset Container Usage"
	@echo "=============================="
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make container-build     # Build the image"
	@echo "  2. make container-api       # Run API service"
	@echo "  3. Visit http://localhost:$(API_PORT)"
	@echo ""
	@echo "Available Commands:"
	@echo "  make container-build        Build container image"
	@echo "  make container-api          Run API service (background)"
	@echo "  make container-cli          Run CLI interactively"
	@echo "  make container-shell        Debug shell access"
	@echo "  make container-clean        Clean up containers/images"
	@echo ""
	@echo "Manual Commands:"
	@echo "  podman run $(IMAGE_NAME):$(IMAGE_TAG) system-info"
	@echo "  podman run $(IMAGE_NAME):$(IMAGE_TAG) toolset-info"
	@echo "  podman run $(IMAGE_NAME):$(IMAGE_TAG) tool <name> [args]"
	@echo ""
	@echo "Data Persistence:"
	@echo "  Data is stored in: $(HOME)/.nebula-container/"
	@echo "  - nebula/     User configuration and database"
	@echo "  - logs/       Application logs"
	@echo "  - storage/    Application storage"
	@echo "  - secrets/    Secrets and credentials"
	@echo ""
	@echo "Container Management:"
	@echo "  podman ps                   # List running containers"
	@echo "  podman logs $(CONTAINER_NAME)       # View API logs"
	@echo "  podman stop $(CONTAINER_NAME)       # Stop API service"
	@echo "  podman images $(IMAGE_NAME)         # List built images"
