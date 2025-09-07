# Multi-stage Containerfile for Nebula Toolset Service
# Supports both API and CLI modes

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install build hatchling

# Copy source code
COPY src/ ./src/
COPY tools/ ./tools/
COPY memory-bank/ ./memory-bank/

# Build the package
RUN python -m build

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    NEBULA_CLI_DEBUG=0

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash nebula

# Create app directory and required directories
WORKDIR /app
RUN mkdir -p /app/.logs /app/.storage /app/.secrets && \
    chown -R nebula:nebula /app

# Copy built application from builder stage
COPY --from=builder /app/src ./src
COPY --from=builder /app/tools ./tools
COPY --from=builder /app/memory-bank ./memory-bank
COPY --from=builder /app/requirements.txt .

# Copy additional files
COPY Makefile ./
COPY README.md ./
COPY LICENSE ./

# Install Python dependencies as nebula user
USER nebula
RUN pip install --user -r requirements.txt

# Create .nebula directory for user data
RUN mkdir -p /home/nebula/.nebula/cli_logs

# Copy entrypoint script
COPY --chown=nebula:nebula container-entrypoint.sh /app/
RUN chmod +x /app/container-entrypoint.sh

# Expose the API port (default FastAPI port)
EXPOSE 8000

# Health check for the API service
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/container-entrypoint.sh"]

# Default command (can be overridden)
CMD ["api"]
