# Simplified Nebula CLI

A streamlined command-line interface for VM management with Google Cloud Platform. This simplified version focuses on exactly 4 core actions that you need for VM management.

## Features

- **4 Core Commands**: `list-vms`, `start-vm`, `stop-vm`, `update-ssh-config`
- **GCP Integration**: Direct integration with Google Cloud Platform
- **SSH Config Management**: Automatic SSH configuration updates
- **Simple Interface**: No complex menus or unnecessary features
- **Rich Output**: Beautiful terminal formatting with colors and tables

## Installation

### Prerequisites

- Python 3.11 or higher
- Google Cloud SDK installed and configured
- Authenticated with `gcloud auth login`

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd toolset

# Activate virtual environment (if using one)
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Test the CLI
python test_simplified_cli.py
```

## Usage

The simplified CLI provides exactly 4 commands:

### 1. List VMs

```bash
# List all VM instances
python src/cli/app.py list-vms

# List VMs in a specific project
python src/cli/app.py list-vms --project my-project-id

# List VMs in a specific zone
python src/cli/app.py list-vms --zone us-central1-a
```

### 2. Start VM

```bash
# Start a VM instance
python src/cli/app.py start-vm my-instance --zone us-central1-a

# Start a VM in a specific project
python src/cli/app.py start-vm my-instance --zone us-central1-a --project my-project-id
```

**Note**: When starting a VM, the CLI automatically updates your SSH config with the instance's external IP.

### 3. Stop VM

```bash
# Stop a VM instance
python src/cli/app.py stop-vm my-instance --zone us-central1-a

# Stop a VM in a specific project
python src/cli/app.py stop-vm my-instance --zone us-central1-a --project my-project-id
```

### 4. Update SSH Config

```bash
# Update SSH config for a specific VM
python src/cli/app.py update-ssh-config my-instance --zone us-central1-a

# Update SSH config in a specific project
python src/cli/app.py update-ssh-config my-instance --zone us-central1-a --project my-project-id
```

## SSH Configuration

The CLI automatically manages your SSH configuration:

- **Location**: `~/.ssh/config`
- **Mapping Storage**: `~/.config/nebula-cli/mappings.json`
- **Default User**: `nebula`
- **Default Key Path**: `~/.ssh/{instance-name}_key`

When you start a VM or update SSH config, the CLI will:
1. Get the instance's external IP address
2. Create or update an SSH host entry
3. Store the mapping for future reference

## Authentication

The CLI requires Google Cloud Platform authentication:

```bash
# Authenticate with GCP
gcloud auth login

# Set your project (optional, uses current project by default)
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
python src/cli/app.py list-vms
```

## Examples

### Complete Workflow

```bash
# 1. List all your VMs
python src/cli/app.py list-vms

# 2. Start a VM (automatically updates SSH config)
python src/cli/app.py start-vm my-worker-vm --zone us-central1-a

# 3. SSH into the VM (SSH config is already updated)
ssh my-worker-vm

# 4. Stop the VM when done
python src/cli/app.py stop-vm my-worker-vm --zone us-central1-a
```

### Project-Specific Operations

```bash
# Work with VMs in a specific project
python src/cli/app.py list-vms --project my-dev-project
python src/cli/app.py start-vm dev-vm --zone us-central1-a --project my-dev-project
python src/cli/app.py stop-vm dev-vm --zone us-central1-a --project my-dev-project
```

## Help

Get help for any command:

```bash
# General help
python src/cli/app.py --help

# Command-specific help
python src/cli/app.py list-vms --help
python src/cli/app.py start-vm --help
python src/cli/app.py stop-vm --help
python src/cli/app.py update-ssh-config --help
```

## What Was Simplified

This simplified version removes:
- ❌ API service management (start/stop API server)
- ❌ Complex tool system and discovery
- ❌ Interactive menus and prompts
- ❌ Authentication management UI
- ❌ Database operations
- ❌ Logging and debugging features
- ❌ Bulk operations (start-all, stop-all)

This simplified version keeps:
- ✅ Core VM management (start, stop, list)
- ✅ SSH config management
- ✅ GCP integration
- ✅ Rich terminal output
- ✅ Project and zone filtering

## Testing

Run the test suite to verify everything works:

```bash
python test_simplified_cli.py
```

This will test all 4 commands and verify they're working correctly.

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate with GCP
gcloud auth login

# Check current authentication
gcloud auth list

# Set correct project
gcloud config set project YOUR_PROJECT_ID
```

### SSH Config Issues

```bash
# Check SSH config file
cat ~/.ssh/config

# Check instance mappings
cat ~/.config/nebula-cli/mappings.json

# Manually update SSH config for a VM
python src/cli/app.py update-ssh-config my-instance --zone us-central1-a
```

### Permission Issues

Make sure your GCP account has the necessary permissions:
- `compute.instances.list`
- `compute.instances.start`
- `compute.instances.stop`
- `compute.instances.get`

## Support

This simplified CLI is designed to be straightforward and reliable. If you encounter issues:

1. Check your GCP authentication: `gcloud auth list`
2. Verify your project: `gcloud config get-value project`
3. Test with the test script: `python test_simplified_cli.py`
4. Check the help: `python src/cli/app.py --help`
