# Nebula Toolset Container Guide

This guide explains how to build and run the Nebula toolset service using Podman containers.

## Quick Start

```bash
# Build the container image
make container-build

# Run the API service
make container-api

# Access the API at http://localhost:8000
curl http://localhost:8000
```

## Container Architecture

The containerized Nebula toolset includes:

- **Multi-stage build** for optimized image size
- **Non-root user** (`nebula`) for security
- **Persistent data** storage via volume mounts
- **Health checks** for the API service
- **Flexible entrypoint** supporting multiple modes

## Available Commands

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make container-build` | Build the container image |
| `make container-api` | Run API service in background |
| `make container-cli` | Run CLI interactively |
| `make container-shell` | Start debug shell |
| `make container-clean` | Clean up containers/images |
| `make container-help` | Show detailed help |

### Manual Podman Commands

```bash
# Build the image
podman build -t nebula-toolset:latest -f Containerfile .

# Run API service
podman run -d --name nebula-service \
  -p 8000:8000 \
  -v ~/.nebula-container/nebula:/home/nebula/.nebula:Z \
  nebula-toolset:latest api

# Run CLI interactively
podman run -it --rm \
  -v ~/.nebula-container/nebula:/home/nebula/.nebula:Z \
  nebula-toolset:latest cli

# Run a specific tool
podman run --rm \
  nebula-toolset:latest tool gcp_vm_manager --list-all

# Get system information
podman run --rm \
  nebula-toolset:latest system-info
```

## Service Modes

The container supports multiple operation modes via the entrypoint script:

### API Mode (Default)
```bash
# Start the FastAPI service
podman run -p 8000:8000 nebula-toolset:latest api

# Or using make
make container-api
```

### CLI Mode
```bash
# Interactive CLI
podman run -it nebula-toolset:latest cli

# Or using make
make container-cli
```

### Tool Execution
```bash
# Run specific tools
podman run nebula-toolset:latest tool <tool_name> [args]

# Examples
podman run nebula-toolset:latest tool gcp_vm_manager --list-all
podman run nebula-toolset:latest tool list_gcp_workers
```

### System Information
```bash
# Get system info
podman run nebula-toolset:latest system-info

# Get toolset info
podman run nebula-toolset:latest toolset-info
```

### Debug Shell
```bash
# Access shell for debugging
podman run -it nebula-toolset:latest shell

# Or using make
make container-shell
```

## Data Persistence

The container uses volume mounts for persistent data storage:

### Default Data Directory
- **Host location**: `~/.nebula-container/`
- **Automatic creation**: Created by Makefile commands

### Volume Mappings

| Host Directory | Container Directory | Purpose |
|----------------|-------------------|---------|
| `~/.nebula-container/nebula` | `/home/nebula/.nebula` | User config and database |
| `~/.nebula-container/logs` | `/app/.logs` | Application logs |
| `~/.nebula-container/storage` | `/app/.storage` | Application storage |
| `~/.nebula-container/secrets` | `/app/.secrets` | Secrets and credentials |

### Custom Data Directory
```bash
# Use custom data directory
podman run -v /path/to/data:/home/nebula/.nebula:Z \
  nebula-toolset:latest api
```

## Networking

### API Service
- **Container port**: 8000
- **Default mapping**: 8000:8000 (host:container)
- **Access URL**: http://localhost:8000

### Custom Port Mapping
```bash
# Use different host port
podman run -p 9000:8000 nebula-toolset:latest api

# Access at http://localhost:9000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEBULA_CLI_DEBUG` | 0 | Enable debug logging (set to 1) |
| `PYTHONPATH` | /app/src | Python module search path |
| `PYTHONDONTWRITEBYTECODE` | 1 | Prevent .pyc file creation |
| `PYTHONUNBUFFERED` | 1 | Force stdout/stderr unbuffered |

### Setting Environment Variables
```bash
# Set debug mode
podman run -e NEBULA_CLI_DEBUG=1 nebula-toolset:latest api

# Multiple environment variables
podman run \
  -e NEBULA_CLI_DEBUG=1 \
  -e CUSTOM_VAR=value \
  nebula-toolset:latest api
```

## Container Management

### Monitoring
```bash
# List running containers
podman ps

# View API service logs
podman logs -f nebula-service

# Check container health
podman inspect nebula-service
```

### Lifecycle Management
```bash
# Stop API service
podman stop nebula-service

# Remove container
podman rm nebula-service

# Remove image
podman rmi nebula-toolset:latest
```

## Build Configuration

### Multi-stage Build
The Containerfile uses a multi-stage build:

1. **Builder stage**: Installs build dependencies and builds the application
2. **Production stage**: Creates minimal runtime image

### Build Arguments
```bash
# Build with specific Python version
podman build --build-arg PYTHON_VERSION=3.12-slim \
  -t nebula-toolset:latest .

# Build for specific platform
podman build --platform linux/amd64 \
  -t nebula-toolset:latest .
```

### Build Cache
```bash
# Build without cache
podman build --no-cache -t nebula-toolset:latest .

# Force rebuild
make container-clean
make container-build
```

## Security

### Non-root User
- Container runs as user `nebula` (UID 1000)
- Home directory: `/home/nebula`
- No sudo access

### Volume Security
- Uses SELinux labels (`:Z`) for proper file permissions
- Secrets directory has restricted permissions (700)

### Network Security
- Only exposes port 8000 for API service
- No privileged access required

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Fix file permissions
   sudo chown -R $USER ~/.nebula-container
   chmod -R 755 ~/.nebula-container
   ```

2. **Port Already in Use**
   ```bash
   # Use different port
   podman run -p 8080:8000 nebula-toolset:latest api
   ```

3. **Container Won't Start**
   ```bash
   # Check logs
   podman logs nebula-service
   
   # Debug with shell
   make container-shell
   ```

4. **Build Failures**
   ```bash
   # Clean and rebuild
   make container-clean
   make container-build
   ```

### Debug Mode
```bash
# Enable debug logging
podman run -e NEBULA_CLI_DEBUG=1 \
  nebula-toolset:latest api
```

### Health Checks
The container includes health checks for the API service:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start period**: 60 seconds
- **Retries**: 3

Check health status:
```bash
podman inspect --format='{{.State.Health.Status}}' nebula-service
```

## Integration Examples

### Development Workflow
```bash
# 1. Build and test
make container-build
make container-cli

# 2. Start API service
make container-api

# 3. Test API endpoints
curl http://localhost:8000/system/info
curl http://localhost:8000/toolset/info

# 4. Clean up
make container-clean
```

### CI/CD Pipeline
```bash
# Build stage
podman build -t nebula-toolset:${VERSION} .

# Test stage
podman run --rm nebula-toolset:${VERSION} system-info

# Deploy stage
podman run -d --name nebula-prod \
  -p 8000:8000 \
  -v /data/nebula:/home/nebula/.nebula:Z \
  nebula-toolset:${VERSION} api
```

### Production Deployment
```bash
# Run with resource limits
podman run -d \
  --name nebula-service \
  --memory=512m \
  --cpus=1.0 \
  -p 8000:8000 \
  -v /opt/nebula/data:/home/nebula/.nebula:Z \
  --restart=unless-stopped \
  nebula-toolset:latest api
```

## Next Steps

1. **Customize the build** by modifying the `Containerfile`
2. **Add more tools** by extending the `tools/` directory
3. **Configure persistent storage** for production use
4. **Set up monitoring** with container health checks
5. **Create deployment scripts** for your environment

For more information, see the main [README.md](README.md) file.
