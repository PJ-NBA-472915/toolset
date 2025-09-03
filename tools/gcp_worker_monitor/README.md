# GCP Worker Monitor Tool

A tool for monitoring Google Cloud Platform worker instances, providing detailed information about resource usage, network configuration, and instance status.

## Features

- **Worker Instance Discovery**: Automatically finds instances with "worker" in the name
- **Resource Monitoring**: Shows CPU, memory, and disk usage information
- **Network Details**: Displays internal and external IP addresses
- **Rich Output**: Beautiful terminal formatting with colors and tables
- **Data Export**: Export results to JSON format
- **Zone Filtering**: Filter instances by specific GCP zones

## Prerequisites

- Google Cloud SDK (gcloud CLI) installed and authenticated
- Python 3.11+
- Access to GCP Compute Engine and Monitoring APIs

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install via the main CLI
make run-tool TOOL=gcp_worker_monitor
```

## Usage

### Basic Usage
```bash
# List all worker instances
python main.py

# Show detailed information
python main.py --detailed

# Filter by zone
python main.py --zone us-central1-a
```

### Advanced Options
```bash
# Export to JSON
python main.py --export workers.json

# Show all instances (not just workers)
python main.py --all-instances

# Specify project ID
python main.py --project my-project-id

# Enable verbose output
python main.py --verbose
```

## Output

The tool provides both summary and detailed views:

- **Summary**: Table with key instance information
- **Detailed**: Individual panels for each instance with comprehensive data

## Integration with Nebula CLI

This tool integrates seamlessly with the Nebula CLI:

```bash
# Run via CLI
make run-tool TOOL=gcp_worker_monitor

# Or directly
python src/nebula_cli/app.py --run-tool gcp_worker_monitor
```
