#!/bin/bash

# Nebula CLI Installation Script

set -e

echo "🚀 Installing Nebula CLI..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.11" ]]; then
    echo "❌ Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

echo "✅ Dependencies installed successfully"

# Make the CLI executable
chmod +x src/nebula_cli/app.py

# Create a symlink for easy access (optional)
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Create ~/.local/bin if it doesn't exist
    mkdir -p ~/.local/bin
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo "📝 Added ~/.local/bin to PATH in shell config files"
    fi
    
    # Create symlink
    ln -sf "$(pwd)/src/nebula_cli/app.py" ~/.local/bin/nebula
    echo "🔗 Created symlink: ~/.local/bin/nebula"
fi

echo ""
echo "🎉 Nebula CLI installed successfully!"
echo ""
echo "Usage:"
echo "  python3 src/nebula_cli/app.py          # Run in interactive mode"
echo "  python3 src/nebula_cli/app.py --help   # Show help"
echo ""

if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "After restarting your terminal, you can also run:"
    echo "  nebula                              # Run the CLI"
    echo "  nebula --help                       # Show help"
fi

echo ""
echo "For more information, see README.md"
