# GCP VM Manager Tool

Interactive tool for managing Google Cloud Platform VM instances with support for both interactive and headless modes.

## Features

- **Interactive Mode**: Navigate through menus to manage instances
- **Headless Mode**: Command-line interface for automation
- **Instance Selection**: Use arrow keys to select instances from lists
- **Status Filtering**: View instances by status (running, terminated, all)
- **Bulk Operations**: Start all instances or stop all instances at once
- **Safe Operations**: Confirmation prompts for destructive actions
- **Wait Support**: Wait for operations to complete before returning

## Prerequisites

- Google Cloud SDK installed and configured
- Authenticated with `gcloud auth login`
- Appropriate permissions to manage VM instances

## Usage

### Interactive Mode (Default)

```bash
python main.py
```

This will launch an interactive menu where you can:
- List all instances
- List running instances only
- List terminated instances only
- Start terminated instances (with arrow key selection)
- Stop running instances (with arrow key selection and confirmation)
- Start all terminated instances at once
- Stop all running instances at once

### Headless Mode

#### List Instances

```bash
# List all instances
python main.py --list-all

# List running instances
python main.py --list-running

# List terminated instances
python main.py --list-terminated

# Specify project and zone
python main.py --list-all --project my-project --zone us-central1-a
```

#### Manage Instances

```bash
# Start an instance
python main.py --start-instance my-instance --zone us-central1-a

# Stop an instance (with confirmation)
python main.py --stop-instance my-instance --zone us-central1-a

# Stop an instance (skip confirmation)
python main.py --stop-instance my-instance --zone us-central1-a --yes

# Start all terminated instances
python main.py --start-all --wait

# Stop all running instances
python main.py --stop-all --yes --wait

# Wait for operation to complete
python main.py --start-instance my-instance --zone us-central1-a --wait
```

## Command Line Options

- `--project`: GCP project ID (default: current project)
- `--zone`: GCP zone to filter instances
- `--list-all`: List all instances
- `--list-running`: List running instances only
- `--list-terminated`: List terminated instances only
- `--start-instance`: Start a specific instance by name
- `--stop-instance`: Stop a specific instance by name
- `--start-all`: Start all terminated instances
- `--stop-all`: Stop all running instances
- `--yes`: Skip confirmation prompts
- `--wait`: Wait for operation to complete before returning

## Interactive Features

### Instance Selection
When starting or stopping instances in interactive mode, you'll see a list of available instances with:
- Instance name
- Current status
- Zone
- Machine type

Use arrow keys to navigate and Enter to select.

### Safety Confirmations
When stopping instances, you'll be prompted to confirm the action to prevent accidental shutdowns.

## Error Handling

The tool provides clear error messages for common issues:
- Authentication problems
- Missing instances
- Permission errors
- Network timeouts

## Integration with Nebula CLI

This tool is designed to be run through the Nebula CLI's "Run Tool" feature:

```bash
# From the Nebula CLI
python app.py --run-tool gcp_vm_manager

# Or with arguments
python app.py --run-tool gcp_vm_manager --list-running
```
