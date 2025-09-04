# Nebula CLI

A powerful command-line interface for the Nebula toolset, providing an intuitive way to interact with various tools and utilities. The CLI features comprehensive authentication, database management, and a modular tool system for managing cloud resources and development workflows.

## Features

- **Interactive Menu System**: Easy-to-use arrow key navigation with rich terminal UI
- **Authentication Management**: GCP OAuth integration with project ID management
- **Database Management**: SQLite-based storage for authentication and configuration data
- **Tool System**: Modular architecture for running and managing various tools
- **Instance Management**: Start, stop, and list compute instances
- **Rich Output**: Beautiful terminal output with colors, tables, and formatting
- **System Information**: Display system details and environment information
- **Toolset Discovery**: Automatically discover and list available tools
- **Tool Execution**: Run specific tools from the command line or interactively
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Headless Mode**: Support for automation and scripting
- **Development Tools**: Integrated testing, linting, and build system

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- make (for using the Makefile)
- Google Cloud SDK (for GCP authentication features)
- SQLite3 (included with Python)

### Quick Start with Makefile

```bash
# Setup everything and run (recommended for first time)
make quickstart

# Or step by step:
make setup-venv    # Create virtual environment
make install-dev   # Install in development mode
make run           # Run the CLI
```

### Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Using uv
uv pip install -r requirements.txt

# Using make
make install
```

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd toolset

# Install in development mode
pip install -e .

# Or using make
make install-dev
```

## Usage

### Interactive Mode (Default)

Run the CLI without arguments to enter interactive mode:

```bash
python src/nebula_cli/app.py
# or
make run
```

The interactive mode provides:
- **Authentication Management**: Login/logout, project selection
- **Database Operations**: View and manage stored data
- **Tool Execution**: Run available tools interactively
- **System Information**: View system and environment details

### Command Line Arguments

```bash
# Show system information
python src/nebula_cli/app.py --system-info

# Show toolset information
python src/nebula_cli/app.py --toolset-info

# Run a specific tool
python src/nebula_cli/app.py --run-tool <tool-name>

# Instance management
python src/nebula_cli/app.py --list-instances
python src/nebula_cli/app.py --start-instance <instance-name>
python src/nebula_cli/app.py --stop-instance <instance-name>

# Show help
python src/nebula_cli/app.py --help
```

### Authentication

The CLI supports Google Cloud Platform authentication:

```bash
# Authenticate with GCP (interactive)
python src/nebula_cli/app.py
# Select "Authentication" from the menu

# Check authentication status
python src/nebula_cli/app.py --system-info
```

### Database Management

The CLI uses SQLite for storing authentication and configuration data:

- **Location**: `~/.nebula/nebula_cli.db`
- **Tables**: Authentication, configuration, and tool data
- **Management**: Through interactive menu or programmatic API

### As a Module

```python
from nebula_cli import NebulaCLI
from nebula_cli.auth import AuthenticationManager
from nebula_cli.database import DatabaseManager

# Initialize CLI
cli = NebulaCLI()

# Authentication
auth_manager = AuthenticationManager()
if not auth_manager.is_authenticated():
    auth_manager.authenticate_user()

# Database operations
db_manager = DatabaseManager()
auth_data = db_manager.get_auth_data()

# Tool execution
cli.show_system_info()
cli.show_toolset_info()
```

## Project Structure

```
toolset/
├── src/
│   └── nebula_cli/
│       ├── __init__.py
│       ├── app.py              # Main CLI application
│       ├── auth.py             # Authentication manager
│       └── database.py         # Database manager
├── tools/                      # Modular tool system
│   ├── example_tool/
│   │   ├── __init__.py
│   │   └── main.py
│   └── list_gcp_workers/
│       ├── __init__.py
│       ├── main.py
│       ├── README.md
│       └── requirements.txt
├── memory-bank/                # Documentation and context
│   ├── context/
│   ├── docs/
│   ├── rules/
│   └── scripts/
├── tasks/                      # Task management system
│   ├── _blank_task.json
│   ├── _schema.json
│   └── _status.json
├── pyproject.toml
├── requirements.txt
├── Makefile                    # Development workflow
└── README.md
```

## Tools System

The CLI includes a modular tool system located in the `tools/` directory:

### Available Tools

- **list_gcp_workers**: Monitor and list Google Cloud Platform worker instances
  - Features: Resource monitoring, network details, data export
  - Usage: `make run-tool TOOL=list_gcp_workers`

- **example_tool**: Template for creating new tools
  - Demonstrates tool structure and integration patterns

### Creating New Tools

1. Create a new directory in `tools/`
2. Add `__init__.py` and `main.py` files
3. Implement the tool logic in `main.py`
4. Add `requirements.txt` if needed
5. The CLI will automatically discover and list your tool

### Tool Structure

```
tools/your_tool/
├── __init__.py
├── main.py              # Tool implementation
├── README.md            # Tool documentation
└── requirements.txt     # Tool dependencies (optional)
```

## Configuration

The CLI automatically creates a `.nebula` directory in your home folder for:
- **Database**: `nebula_cli.db` (SQLite database)
- **Log files**: `cli_logs/` (daily rotated logs)
- **Configuration**: Future configuration files
- **Cache data**: Future cache storage

## Logging

Logs are stored in `~/.nebula/cli_logs/` with daily rotation. Enable debug output by setting:

```bash
export NEBULA_CLI_DEBUG=1
```

## Development

### Development Workflow

The project includes a comprehensive Makefile for development tasks:

```bash
# Setup and Installation
make setup-venv       # Create virtual environment
make install-dev      # Install in development mode
make clean-venv       # Remove virtual environment

# Testing and Quality
make test             # Run all tests
make test-cli         # Test CLI functionality
make test-tools       # Test individual tools
make lint             # Run linting checks
make format           # Format code with black
make check-deps       # Check dependency conflicts

# Running and Information
make run              # Run CLI in interactive mode
make run-headless     # Run CLI with --help
make run-tool TOOL=name # Run specific tool
make show-help        # Show CLI help
make show-system-info # Show system information
make show-toolset-info # Show available tools

# Build and Package
make build            # Build the package
make package          # Create distribution packages
make install-package  # Install the built package
make uninstall-package # Uninstall the package

# Maintenance
make clean            # Clean build artifacts and logs
make clean-logs       # Clean log files
make docs             # Generate documentation
```

### Adding New Commands

1. Extend the `NebulaCLI` class in `app.py`
2. Add new menu options in the interactive mode
3. Update argument parsing for headless mode
4. Add appropriate logging

### Adding New Tools

1. Create a new directory in `tools/`
2. Follow the tool structure pattern
3. Add to the CLI's tool discovery system
4. Update documentation

### Testing

```bash
# Run basic tests
make test

# Run specific test suites
make test-cli
make test-tools

# Run with coverage
python -m pytest --cov=nebula_cli tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Documentation and Context

The repository includes comprehensive documentation and context management:

- **Memory Bank**: Located in `memory-bank/`, contains project specifications, guides, and context
- **Task Management**: JSON-based task system in `tasks/` for project tracking
- **Tool Documentation**: Individual README files for each tool
- **Development Guides**: Local testing and development procedures

## Support

For support and questions:
- Create an issue on GitHub
- Contact the team at team@nebula.dev
- Check the documentation in `memory-bank/docs/`
- Review task status in `tasks/_status.json`
