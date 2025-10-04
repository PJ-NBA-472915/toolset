#!/usr/bin/env python3
"""
Simplified Nebula CLI - VM Management
Focused on 4 core actions: start-vm, list-vms, stop-vm, update-ssh-config
"""

import sys
from pathlib import Path

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the simplified app
from cli.simplified_app import app, main

if __name__ == "__main__":
    main()
