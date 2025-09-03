# Nebula CLI

A powerful command-line interface for the Nebula toolset, providing an intuitive way to interact with various tools and utilities.

## Features

- **Interactive Menu System**: Easy-to-use arrow key navigation
- **Rich Output**: Beautiful terminal output with colors and formatting
- **System Information**: Display system details and environment information
- **Toolset Discovery**: Automatically discover and list available tools
- **Tool Execution**: Run specific tools from the command line
- **Logging**: Comprehensive logging for debugging and monitoring
- **Headless Mode**: Support for automation and scripting

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- make (for using the Makefile)

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
```

### Command Line Arguments

```bash
# Show system information
python src/nebula_cli/app.py --system-info

# Show toolset information
python src/nebula_cli/app.py --toolset-info

# Run a specific tool
python src/nebula_cli/app.py --run-tool <tool-name>

# Show help
python src/nebula_cli/app.py --help
```

### As a Module

```python
from nebula_cli import NebulaCLI

cli = NebulaCLI()
cli.show_system_info()
cli.show_toolset_info()
```

## Project Structure

```
toolset/
├── src/
│   └── nebula_cli/
│       ├── __init__.py
│       └── app.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Configuration

The CLI automatically creates a `.nebula` directory in your home folder for:
- Log files (`cli_logs/`)
- Configuration files (future)
- Cache data (future)

## Logging

Logs are stored in `~/.nebula/cli_logs/` with daily rotation. Enable debug output by setting:

```bash
export NEBULA_CLI_DEBUG=1
```

## Development

### Adding New Commands

1. Extend the `NebulaCLI` class in `app.py`
2. Add new menu options in the interactive mode
3. Update argument parsing for headless mode
4. Add appropriate logging

### Testing

```bash
# Run basic tests
python -m pytest tests/

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

## Support

For support and questions:
- Create an issue on GitHub
- Contact the team at team@nebula.dev
- Check the documentation at [docs.nebula.dev](https://docs.nebula.dev)
