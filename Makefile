# Nebula Simplified CLI Makefile

.PHONY: help list start stop setup-ssh devbox-setup

# Allow targets to be used as arguments
%:
	@:

# Default target
help:
	@echo "Nebula Simplified CLI - VM Management"
	@echo "====================================="
	@echo ""
	@echo "VM Management Commands:"
	@echo "  list             - List all VM instances"
	@echo "  start name       - Start a VM instance (auto-updates SSH config)"
	@echo "  stop name        - Stop a VM instance"
	@echo "  setup-ssh name   - Update SSH config for a VM instance"
	@echo ""
	@echo "Setup:"
	@echo "  devbox-setup     - Setup devbox environment"
	@echo ""

# Devbox Setup
devbox-setup:
	@echo "🔧 Setting up devbox environment..."
	@echo "✅ Devbox environment is ready. All Make commands use the virtual environment directly."

# VM Management Commands
list:
	@echo "📋 Listing VM instances..."
	@source venv/bin/activate && python src/cli/app.py list-vms

start:
	@echo "🚀 Starting VM instance..."
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then echo "❌ Error: Instance name is required. Usage: make start name"; exit 1; fi
	@source venv/bin/activate && python src/cli/app.py start-vm $(filter-out $@,$(MAKECMDGOALS)) --zone europe-west1-d

stop:
	@echo "⏹️  Stopping VM instance..."
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then echo "❌ Error: Instance name is required. Usage: make stop name"; exit 1; fi
	@source venv/bin/activate && python src/cli/app.py stop-vm $(filter-out $@,$(MAKECMDGOALS)) --zone europe-west1-d

setup-ssh:
	@echo "🔑 Updating SSH config for VM instance..."
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then echo "❌ Error: Instance name is required. Usage: make setup-ssh name"; exit 1; fi
	@source venv/bin/activate && python src/cli/app.py update-ssh-config $(filter-out $@,$(MAKECMDGOALS)) --zone europe-west1-d