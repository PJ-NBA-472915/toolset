# Nebula CLI Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev clean test test-cli test-tools lint format check-deps run run-interactive run-headless run-tool show-help show-system-info show-toolset-info build package install-package uninstall-package docs clean-logs clean-venv setup-venv

# Default target
help:
	@echo "Nebula CLI - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install          - Install dependencies and CLI"
	@echo "  install-dev      - Install in development mode"
	@echo "  setup-venv       - Create and setup virtual environment"
	@echo "  clean-venv       - Remove virtual environment"
	@echo ""
	@echo "Testing:"
	@echo "  test             - Run all tests"
	@echo "  test-cli         - Test CLI functionality"
	@echo "  test-tools       - Test individual tools"
	@echo ""
	@echo "Running:"
	@echo "  run              - Run CLI in interactive mode"
	@echo "  run-interactive  - Run CLI in interactive mode"
	@echo "  run-headless     - Run CLI with --help (headless)"
	@echo "  run-tool         - Run a specific tool (usage: make run-tool TOOL=example_tool)"
	@echo ""
	@echo "Information:"
	@echo "  show-help        - Show CLI help"
	@echo "  show-system-info - Show system information"
	@echo "  show-toolset-info - Show available tools"
	@echo ""
	@echo "Development:"
	@echo "  lint             - Run linting checks"
	@echo "  format           - Format code with black"
	@echo "  check-deps       - Check dependency conflicts"
	@echo ""
	@echo "Build & Package:"
	@echo "  build            - Build the package"
	@echo "  package          - Create distribution packages"
	@echo "  install-package  - Install the built package"
	@echo "  uninstall-package - Uninstall the package"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            - Clean build artifacts and logs"
	@echo "  clean-logs       - Clean log files"
	@echo "  docs             - Generate documentation"
	@echo ""

# Variables
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
CLI_SCRIPT := src/nebula_cli/app.py
TOOLS_DIR := tools
REQUIREMENTS := requirements.txt
PYPROJECT := pyproject.toml

# Setup virtual environment
setup-venv:
	@echo "🔧 Setting up virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r $(REQUIREMENTS)
	@echo "✅ Virtual environment setup complete!"

# Install dependencies
install: setup-venv
	@echo "📦 Installing dependencies..."
	$(PIP) install -r $(REQUIREMENTS)
	@echo "✅ Dependencies installed!"

# Install in development mode
install-dev: setup-venv
	@echo "🔧 Installing in development mode..."
	$(PIP) install -e .
	@echo "✅ Development installation complete!"

# Clean virtual environment
clean-venv:
	@echo "🧹 Cleaning virtual environment..."
	rm -rf $(VENV)
	@echo "✅ Virtual environment removed!"

# Clean build artifacts and logs
clean: clean-logs
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf src/nebula_cli/__pycache__/
	rm -rf tools/*/__pycache__/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete!"

# Clean log files
clean-logs:
	@echo "🧹 Cleaning log files..."
	rm -rf ~/.nebula/cli_logs/*
	@echo "✅ Logs cleaned!"

# Test CLI functionality
test-cli:
	@echo "🧪 Testing CLI functionality..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@echo "Testing help command..."
	$(PYTHON_VENV) $(CLI_SCRIPT) --help > /dev/null && echo "✅ Help command works" || echo "❌ Help command failed"
	@echo "Testing system info..."
	$(PYTHON_VENV) $(CLI_SCRIPT) --system-info > /dev/null && echo "✅ System info works" || echo "❌ System info failed"
	@echo "Testing toolset info..."
	$(PYTHON_VENV) $(CLI_SCRIPT) --toolset-info > /dev/null && echo "✅ Toolset info works" || echo "❌ Toolset info failed"
	@echo "Testing tool execution..."
	$(PYTHON_VENV) $(CLI_SCRIPT) --run-tool example_tool > /dev/null && echo "✅ Tool execution works" || echo "❌ Tool execution failed"
	@echo "🎉 CLI tests completed!"

# Test individual tools
test-tools:
	@echo "🧪 Testing individual tools..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@for tool in $(TOOLS_DIR)/*; do \
		if [ -d "$$tool" ] && [ -f "$$tool/main.py" ]; then \
			tool_name=$$(basename "$$tool"); \
			echo "Testing tool: $$tool_name"; \
			$(PYTHON_VENV) "$$tool/main.py" > /dev/null && echo "✅ $$tool_name works" || echo "❌ $$tool_name failed"; \
		fi; \
	done
	@echo "🎉 Tool tests completed!"

# Run all tests
test: test-cli test-tools
	@echo "🎉 All tests completed!"

# Run CLI in interactive mode
run: run-interactive

# Run CLI in interactive mode
run-interactive:
	@echo "🚀 Starting Nebula CLI in interactive mode..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT)

# Run CLI in headless mode
run-headless:
	@echo "🚀 Running Nebula CLI in headless mode..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT) --help

# Run a specific tool
run-tool:
	@if [ -z "$(TOOL)" ]; then \
		echo "❌ Please specify a tool: make run-tool TOOL=example_tool"; \
		exit 1; \
	fi
	@echo "🚀 Running tool: $(TOOL)..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT) --run-tool $(TOOL)

# Show CLI help
show-help:
	@echo "🚀 Showing CLI help..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT) --help

# Show system information
show-system-info:
	@echo "🚀 Showing system information..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT) --system-info

# Show toolset information
show-toolset-info:
	@echo "🚀 Showing toolset information..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PYTHON_VENV) $(CLI_SCRIPT) --toolset-info

# Check dependencies
check-deps:
	@echo "🔍 Checking dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	$(PIP) check
	@echo "✅ Dependencies check complete!"

# Lint code
lint:
	@echo "🔍 Running linting checks..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@if $(PIP) show flake8 > /dev/null 2>&1; then \
		$(PYTHON_VENV) -m flake8 src/ tools/ --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "⚠️  flake8 not installed. Installing..."; \
		$(PIP) install flake8; \
		$(PYTHON_VENV) -m flake8 src/ tools/ --max-line-length=100 --ignore=E501,W503; \
	fi
	@echo "✅ Linting complete!"

# Format code
format:
	@echo "🎨 Formatting code..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@if $(PIP) show black > /dev/null 2>&1; then \
		$(PYTHON_VENV) -m black src/ tools/ --line-length=100; \
	else \
		echo "⚠️  black not installed. Installing..."; \
		$(PIP) install black; \
		$(PYTHON_VENV) -m black src/ tools/ --line-length=100; \
	fi
	@echo "✅ Code formatting complete!"

# Build the package
build:
	@echo "🔨 Building package..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@if $(PIP) show build > /dev/null 2>&1; then \
		$(PYTHON_VENV) -m build; \
	else \
		echo "⚠️  build not installed. Installing..."; \
		$(PIP) install build; \
		$(PYTHON_VENV) -m build; \
	fi
	@echo "✅ Package build complete!"

# Create distribution packages
package: build
	@echo "📦 Creating distribution packages..."
	@echo "✅ Distribution packages created in dist/ directory!"

# Install the built package
install-package:
	@echo "📦 Installing built package..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@if [ ! -f "dist/*.whl" ]; then \
		echo "❌ No wheel file found. Run 'make build' first."; \
		exit 1; \
	fi
	$(PIP) install dist/*.whl
	@echo "✅ Package installed!"

# Uninstall the package
uninstall-package:
	@echo "🗑️  Uninstalling package..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found."; \
		exit 1; \
	fi
	$(PIP) uninstall nebula-cli -y || echo "Package not installed or already removed"
	@echo "✅ Package uninstalled!"

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup-venv' first."; \
		exit 1; \
	fi
	@if $(PIP) show pdoc3 > /dev/null 2>&1; then \
		$(PYTHON_VENV) -m pdoc --html --output-dir docs src/nebula_cli; \
	else \
		echo "⚠️  pdoc3 not installed. Installing..."; \
		$(PIP) install pdoc3; \
		$(PYTHON_VENV) -m pdoc --html --output-dir docs src/nebula_cli; \
	fi
	@echo "✅ Documentation generated in docs/ directory!"

# Quick start - setup everything and run
quickstart: setup-venv install-dev test run

# Development workflow
dev: setup-venv install-dev lint format test

# Setup
setup-gemini:
	ln -s ../memory-bank/gemini/GEMINI.md ./GEMINI.md

setup-cursor-rules:
	mkdir -p .cursor
	@echo "Creating symbolic link from memory-bank/rules to .cursor/rules"
	ln -sf ../memory-bank/rules .cursor/rules
