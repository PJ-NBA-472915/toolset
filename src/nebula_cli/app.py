#!/usr/bin/env python3
"""
Nebula CLI - A powerful command-line interface for the Nebula toolset
"""

import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
import os

console = Console()

# Setup logging
def setup_logging():
    """Setup comprehensive logging for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = Path.home() / '.nebula' / 'cli_logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = logs_dir / f'nebula_cli_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout) if os.getenv('NEBULA_CLI_DEBUG') else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Nebula CLI started - Log file: {log_file}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"User: {os.getenv('USER', 'unknown')}")
    
    return logger

class NebulaCLI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("NebulaCLI initialized")
        
    def show_system_info(self):
        """Display system information."""
        console.print("[yellow]Fetching system information...[/yellow]")
        
        table = Table(title="System Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Python Version", sys.version.split()[0])
        table.add_row("Working Directory", os.getcwd())
        table.add_row("User", os.getenv('USER', 'unknown'))
        table.add_row("Platform", sys.platform)
        
        console.print(table)
    
    def show_toolset_info(self):
        """Display information about the Nebula toolset."""
        console.print("[yellow]Nebula Toolset Information[/yellow]")
        
        toolset_path = Path(__file__).parent.parent.parent
        console.print(f"Toolset Path: {toolset_path}")
        
        # List available tools from the tools directory
        tools_dir = toolset_path / "tools"
        tools = []
        
        if tools_dir.exists():
            for item in tools_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if the tool has a main.py file
                    if (item / "main.py").exists():
                        tools.append(f"{item.name} (executable)")
                    else:
                        tools.append(f"{item.name} (incomplete)")
        
        if tools:
            table = Table(title="Available Tools")
            table.add_column("Tool Name", style="cyan")
            table.add_column("Status", style="green")
            for tool in tools:
                if "(executable)" in tool:
                    name = tool.replace(" (executable)", "")
                    status = "✅ Ready"
                else:
                    name = tool.replace(" (incomplete)", "")
                    status = "⚠️  Incomplete"
                table.add_row(name, status)
            console.print(table)
        else:
            console.print("[yellow]No tools found in tools directory[/yellow]")
        
        # Show other directories
        other_dirs = []
        for item in toolset_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['tools', 'src', 'venv']:
                other_dirs.append(item.name)
        
        if other_dirs:
            console.print("\n[yellow]Other Directories:[/yellow]")
            for dir_name in other_dirs:
                console.print(f"  - {dir_name}")
    
    def run_tool(self, tool_name, tool_args=None):
        """Run a specific tool from the toolset."""
        console.print(f"[blue]Running tool: {tool_name}[/blue]")
        
        # Look for the tool in the tools directory
        toolset_path = Path(__file__).parent.parent.parent
        tool_path = toolset_path / "tools" / tool_name
        
        if not tool_path.exists():
            console.print(f"[red]Tool '{tool_name}' not found[/red]")
            return False
        
        # Check if the tool has a main.py file
        main_file = tool_path / "main.py"
        if not main_file.exists():
            console.print(f"[red]Tool '{tool_name}' does not have a main.py file[/red]")
            return False
        
        try:
            # Execute the tool
            import subprocess
            import sys
            
            # Build command with arguments
            cmd = [sys.executable, str(main_file)]
            if tool_args:
                cmd.extend(tool_args)
            
            # Run the tool in a subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=tool_path
            )
            
            if result.returncode == 0:
                console.print(f"[green]Tool '{tool_name}' executed successfully![/green]")
                if result.stdout:
                    console.print("\n[blue]Tool Output:[/blue]")
                    console.print(result.stdout)
            else:
                console.print(f"[red]Tool '{tool_name}' failed with exit code {result.returncode}[/red]")
                if result.stderr:
                    console.print("\n[red]Error Output:[/red]")
                    console.print(result.stderr)
                return False
                
        except Exception as e:
            console.print(f"[red]Failed to execute tool '{tool_name}': {e}[/red]")
            return False
        
        return True
    
    def show_help(self):
        """Display help information."""
        help_text = """
Nebula CLI - A powerful command-line interface for the Nebula toolset

Available Commands:
  - System Info: Display system information
  - Toolset Info: Show available tools in the toolset
  - Run Tool: Execute a specific tool
  - Help: Show this help message
  - Exit: Exit the CLI

For more information, visit: https://github.com/nebula/toolset
        """
        
        console.print(Panel(help_text, title="Help", border_style="blue"))

def welcome_message():
    """Display welcome message."""
    welcome_text = Text("Nebula CLI", style="bold blue")
    subtitle = Text("Powerful command-line interface for the Nebula toolset", style="italic")
    
    console.print(Panel(welcome_text, subtitle=subtitle, expand=False, border_style="blue"))
    console.print("\nWelcome to the Nebula CLI! Use the menu below to navigate.\n")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Nebula CLI - A powerful command-line interface for the Nebula toolset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Interactive mode (default)
  python app.py
  
  # Show system info
  python app.py --system-info
  
  # Show toolset info
  python app.py --toolset-info
  
  # Run specific tool
  python app.py --run-tool <tool-name> [tool arguments...]
  
  # Show help
  python app.py --help
"""
    )
    
    # Action flags
    parser.add_argument('--system-info', action='store_true',
                       help='Show system information')
    parser.add_argument('--toolset-info', action='store_true',
                       help='Show toolset information')
    parser.add_argument('--run-tool', type=str,
                       help='Run a specific tool')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress non-essential output')
    parser.add_argument('--json-output', action='store_true',
                       help='Output results in JSON format')
    
    # Parse known args to get tool arguments
    args, tool_args = parser.parse_known_args()
    args.tool_args = tool_args
    
    return args

def run_headless_mode(args, nebula_cli, logger):
    """Run the CLI in headless mode based on arguments."""
    logger.info(f"Running in headless mode with args: {vars(args)}")
    
    try:
        if args.system_info:
            nebula_cli.show_system_info()
            return 0
            
        elif args.toolset_info:
            nebula_cli.show_toolset_info()
            return 0
            
        elif args.run_tool:
            nebula_cli.run_tool(args.run_tool, args.tool_args)
            return 0
        
    except Exception as e:
        logger.error(f"Headless mode error: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return 1
    
    return 0

def run_interactive_mode(nebula_cli, logger):
    """Run the CLI in interactive mode."""
    logger.info("Running in interactive mode")
    
    try:
        welcome_message()
        
        # Main menu
        main_menu = [
            inquirer.List(
                'action',
                message="What would you like to do?",
                choices=[
                    'System Information',
                    'Toolset Information',
                    'Run Tool',
                    'Help',
                    'Exit'
                ],
            ),
        ]
        
        while True:
            answers = inquirer.prompt(main_menu)
            if not answers or answers['action'] == 'Exit':
                break
            
            action = answers['action']
            logger.info(f"User selected action: {action}")
            
            if action == 'System Information':
                nebula_cli.show_system_info()
                
            elif action == 'Toolset Info':
                nebula_cli.show_toolset_info()
                
            elif action == 'Run Tool':
                # Get available tools from the tools directory
                toolset_path = Path(__file__).parent.parent.parent
                tools_dir = toolset_path / "tools"
                tools = []
                
                if tools_dir.exists():
                    for item in tools_dir.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            # Only show tools that have a main.py file
                            if (item / "main.py").exists():
                                tools.append(item.name)
                
                if not tools:
                    console.print("[yellow]No executable tools found in tools directory[/yellow]")
                    continue
                
                # Let user select a tool
                tool_q = inquirer.List(
                    'tool',
                    message="Select a tool to run:",
                    choices=tools
                )
                
                tool_answer = inquirer.prompt([tool_q])
                if not tool_answer:
                    continue
                
                logger.info(f"User selected tool: {tool_answer['tool']}")
                nebula_cli.run_tool(tool_answer['tool'])
                
            elif action == 'Help':
                nebula_cli.show_help()
            
            console.print()  # Add spacing
        
        console.print("[bold cyan]Thank you for using the Nebula CLI![/bold cyan]")
        return 0
        
    except KeyboardInterrupt:
        console.print("\n\n[red]Operation cancelled by user.[/red]")
        logger.info("Interactive mode cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Interactive mode error: {e}")
        console.print(f"\n[red]An error occurred: {e}[/red]")
        return 1

def main():
    """Main CLI function with argument parsing and mode selection."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize logging
    logger = setup_logging()
    logger.info("Starting Nebula CLI")
    logger.info(f"Command-line arguments: {vars(args)}")
    
    # Initialize Nebula CLI
    nebula_cli = NebulaCLI()
    
    # Determine if running in headless mode
    headless_mode = any([
        args.system_info,
        args.toolset_info,
        args.run_tool
    ])
    
    if headless_mode:
        return run_headless_mode(args, nebula_cli, logger)
    else:
        return run_interactive_mode(nebula_cli, logger)

if __name__ == "__main__":
    sys.exit(main())
