#!/bin/bash
set -e

# Nebula Toolset Podman Build Script
# Builds the container image with appropriate tags and options

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
IMAGE_NAME="nebula-toolset"
VERSION="latest"
CONTAINERFILE="Containerfile"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -f|--file)
            CONTAINERFILE="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --platform)
            PLATFORM="--platform $2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Nebula Toolset Podman Build Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -t, --tag NAME          Image name (default: nebula-toolset)
    -v, --version VERSION   Image version/tag (default: latest)
    -f, --file FILE         Containerfile path (default: Containerfile)
    --no-cache              Build without cache
    --platform PLATFORM     Target platform (e.g., linux/amd64, linux/arm64)
    -h, --help              Show this help

EXAMPLES:
    # Basic build
    $0

    # Build with custom tag
    $0 --tag my-nebula --version v1.0.0

    # Build for specific platform
    $0 --platform linux/amd64

    # Build without cache
    $0 --no-cache
EOF
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Full image tag
FULL_TAG="${IMAGE_NAME}:${VERSION}"

info "Building Nebula Toolset container image..."
info "Image tag: $FULL_TAG"
info "Containerfile: $CONTAINERFILE"

# Check if Containerfile exists
if [[ ! -f "$CONTAINERFILE" ]]; then
    error "Containerfile not found: $CONTAINERFILE"
    exit 1
fi

# Build the image
info "Starting build process..."
if podman build \
    ${NO_CACHE} \
    ${PLATFORM} \
    -t "$FULL_TAG" \
    -f "$CONTAINERFILE" \
    .; then
    success "Container image built successfully: $FULL_TAG"
else
    error "Build failed"
    exit 1
fi

# Show image info
info "Image information:"
podman images "$IMAGE_NAME"

success "Build completed successfully!"
echo ""
info "Next steps:"
echo "  1. Run the API service:"
echo "     podman run -p 8000:8000 $FULL_TAG"
echo ""
echo "  2. Run CLI interactively:"
echo "     podman run -it $FULL_TAG cli"
echo ""
echo "  3. Run a specific tool:"
echo "     podman run $FULL_TAG tool gcp_vm_manager --list-all"
echo ""
echo "  4. Use the run script:"
echo "     ./podman-run.sh --help"
