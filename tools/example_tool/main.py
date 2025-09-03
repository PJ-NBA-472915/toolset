#!/usr/bin/env python3
"""
Example Tool Main Module
This demonstrates how tools can be structured and executed by the Nebula CLI
"""

import sys
import os
from pathlib import Path

def main():
    """Main function for the example tool."""
    print("🔧 Example Tool - Nebula CLI Integration Demo")
    print("=" * 50)
    
    # Get tool information
    tool_path = Path(__file__).parent
    tool_name = tool_path.name
    
    print(f"Tool Name: {tool_name}")
    print(f"Tool Path: {tool_path}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    print("\nThis is an example tool that demonstrates:")
    print("- How tools can be structured in the Nebula toolset")
    print("- How the CLI can discover and execute tools")
    print("- How tools can provide their own functionality")
    
    print("\n✅ Example tool executed successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

