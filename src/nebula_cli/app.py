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
import sys
import argparse
from pathlib import Path
import os
try:
    from .database import DatabaseManager
    from .auth import AuthenticationManager
    from .logger import log
except ImportError:
    # Handle case when running as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from database import DatabaseManager
    from auth import AuthenticationManager
    from logger import log

console = Console()

class NebulaCLI:
    def __init__(self):
        log.info("NebulaCLI initialized")
        
        # Initialize database and authentication
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager(self.db_manager)
        
        # Check authentication status on startup
        self._check_authentication()
    
    def _check_authentication(self):
        """Check authentication status on startup"""
        if not self.auth_manager.is_authenticated():
            log.info("User not authenticated")
            # Don't force authentication on startup, let individual features handle it
        else:
            log.info("User is authenticated")
            auth_info = self.auth_manager.get_auth_info()
            log.info(f"Authenticated as: {auth_info['user_id']} (Project: {auth_info['project_id']})")
        
    def show_system_info(self):
        """Display system information."""
        log.info("Displaying system info.")
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
        log.info("Displaying toolset info.")
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
        log.info(f"Running tool: {tool_name} with args: {tool_args}")
        console.print(f"[blue]Running tool: {tool_name}[/blue]")
        
        # Look for the tool in the tools directory
        toolset_path = Path(__file__).parent.parent.parent
        tool_path = toolset_path / "tools" / tool_name
        
        if not tool_path.exists():
            log.error(f"Tool '{tool_name}' not found at path: {tool_path}")
            console.print(f"[red]Tool '{tool_name}' not found[/red]")
            return False
        
        # Check if the tool has a main.py file
        main_file = tool_path / "main.py"
        if not main_file.exists():
            log.error(f"Tool '{tool_name}' does not have a main.py file.")
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
            # If no tool_args provided, run interactively (no output capture)
            if not tool_args:
                result = subprocess.run(
                    cmd,
                    cwd=tool_path
                )
                return result.returncode == 0
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=tool_path
                )
            
            if result.returncode == 0:
                log.info(f"Tool '{tool_name}' executed successfully.")
                console.print(f"[green]Tool '{tool_name}' executed successfully![/green]")
                if result.stdout:
                    console.print("\n[blue]Tool Output:[/blue]")
                    console.print(result.stdout)
            else:
                log.error(f"Tool '{tool_name}' failed with exit code {result.returncode}. Stderr: {result.stderr}")
                console.print(f"[red]Tool '{tool_name}' failed with exit code {result.returncode}[/red]")
                if result.stderr:
                    console.print("\n[red]Error Output:[/red]")
                    console.print(result.stderr)
                return False
                
        except Exception as e:
            log.error(f"Failed to execute tool '{tool_name}': {e}", exc_info=True)
            console.print(f"[red]Failed to execute tool '{tool_name}': {e}[/red]")
            return False
        
        return True
    
    def show_help(self):
        """Display help information."""
        log.info("Displaying help.")
        help_text = """
Nebula CLI - A powerful command-line interface for the Nebula toolset

Available Commands:
  - System Info: Display system information
  - Toolset Info: Show available tools in the toolset
  - Authentication: Manage user authentication and project settings
  - Configuration: View and manage CLI configuration settings
  - Instance Manager: Manage compute instances
  - Run Tool: Execute a specific tool
  - Help: Show this help message
  - Exit: Exit the CLI

Authentication Features:
  - Login with API key and project ID
  - View authentication status
  - Logout and clear credentials
  - Automatic authentication checking

Configuration Features:
  - Store and retrieve configuration values
  - View all configuration settings
  - Persistent storage using SQLite database

For more information, visit: https://github.com/nebula/toolset
        """
        
        console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def show_auth_status(self):
        """Display authentication status."""
        log.info("Displaying auth status.")
        self.auth_manager.show_auth_status()
    
    def authenticate_user(self):
        """Authenticate user."""
        log.info("Starting user authentication.")
        return self.auth_manager.authenticate_user()
    
    def logout_user(self):
        """Logout user."""
        log.info("Logging out user.")
        return self.auth_manager.logout()
    
    def show_config(self):
        """Display configuration settings."""
        log.info("Displaying configuration.")
        console.print("[yellow]Configuration Settings[/yellow]")
        
        config = self.db_manager.get_all_config()
        if not config:
            console.print("[yellow]No configuration settings found[/yellow]")
            return
        
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.items():
            # Truncate long values for display
            display_value = str(value)
            if len(display_value) > 50:
                display_value = display_value[:47] + "..."
            table.add_row(key, display_value)
        
        console.print(table)
    
    def set_config(self, key: str, value: str):
        """Set configuration value."""
        log.info(f"Setting config key: {key}")
        success = self.db_manager.set_config(key, value)
        if success:
            console.print(f"[green]Configuration '{key}' set successfully[/green]")
        else:
            console.print(f"[red]Failed to set configuration '{key}'[/red]")
    
    def get_config(self, key: str):
        """Get configuration value."""
        log.info(f"Getting config key: {key}")
        value = self.db_manager.get_config(key)
        if value is not None:
            console.print(f"[green]{key}: {value}[/green]")
        else:
            console.print(f"[yellow]Configuration '{key}' not found[/yellow]")


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
        epilog="""
Examples:
  # Interactive mode (default)
  python app.py
  
  # Show system info
  python app.py --system-info
  
  # Show toolset info
  python app.py --toolset-info
  
  # Authentication commands
  python app.py --auth-status
  python app.py --login
  python app.py --logout
  
  # Configuration commands
  python app.py --config
  python app.py --set-config key value
  python app.py --get-config key
  
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
    parser.add_argument('--auth-status', action='store_true',
                       help='Show authentication status')
    parser.add_argument('--login', action='store_true',
                       help='Authenticate user')
    parser.add_argument('--logout', action='store_true',
                       help='Logout user')
    parser.add_argument('--config', action='store_true',
                       help='Show configuration settings')
    parser.add_argument('--set-config', nargs=2, metavar=('KEY', 'VALUE'),
                       help='Set configuration value')
    parser.add_argument('--get-config', type=str,
                       help='Get configuration value')
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

def run_headless_mode(args, nebula_cli):
    """Run the CLI in headless mode based on arguments."""
    log.info(f"Running in headless mode with args: {vars(args)}")
    
    try:
        if args.system_info:
            nebula_cli.show_system_info()
            return 0
            
        elif args.toolset_info:
            nebula_cli.show_toolset_info()
            return 0
            
        elif args.auth_status:
            nebula_cli.show_auth_status()
            return 0
            
        elif args.login:
            success = nebula_cli.authenticate_user()
            return 0 if success else 1
            
        elif args.logout:
            success = nebula_cli.logout_user()
            return 0 if success else 1
            
        elif args.config:
            nebula_cli.show_config()
            return 0
            
        elif args.set_config:
            key, value = args.set_config
            nebula_cli.set_config(key, value)
            return 0
            
        elif args.get_config:
            nebula_cli.get_config(args.get_config)
            return 0
            
        elif args.run_tool:
            nebula_cli.run_tool(args.run_tool, args.tool_args)
            return 0
        
    except Exception as e:
        log.error(f"Headless mode error: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1
    
    return 0

def run_interactive_mode(nebula_cli):
    """Run the CLI in interactive mode."""
    log.info("Running in interactive mode")
    
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
                    'Authentication',
                    'Configuration',
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
            log.info(f"User selected action: {action}")
            
            if action == 'System Information':
                nebula_cli.show_system_info()
                
            elif action == 'Toolset Info':
                nebula_cli.show_toolset_info()
                
            elif action == 'Authentication':
                # Authentication submenu
                auth_menu = [
                    inquirer.List(
                        'auth_action',
                        message="Authentication Options:",
                        choices=[
                            'Show Status',
                            'Login',
                            'Logout',
                            'Back to Main Menu'
                        ],
                    ),
                ]
                
                while True:
                    auth_answers = inquirer.prompt(auth_menu)
                    if not auth_answers or auth_answers['auth_action'] == 'Back to Main Menu':
                        break
                    
                    auth_action = auth_answers['auth_action']
                    
                    if auth_action == 'Show Status':
                        nebula_cli.show_auth_status()
                    elif auth_action == 'Login':
                        nebula_cli.authenticate_user()
                    elif auth_action == 'Logout':
                        nebula_cli.logout_user()
                    
                    console.print()  # Add spacing
                
            elif action == 'Configuration':
                # Configuration submenu
                config_menu = [
                    inquirer.List(
                        'config_action',
                        message="Configuration Options:",
                        choices=[
                            'Show All Settings',
                            'Set Configuration',
                            'Get Configuration',
                            'Back to Main Menu'
                        ],
                    ),
                ]
                
                while True:
                    config_answers = inquirer.prompt(config_menu)
                    if not config_answers or config_answers['config_action'] == 'Back to Main Menu':
                        break
                    
                    config_action = config_answers['config_action']
                    
                    if config_action == 'Show All Settings':
                        nebula_cli.show_config()
                    elif config_action == 'Set Configuration':
                        key = inquirer.text("Enter configuration key:")
                        value = inquirer.text("Enter configuration value:")
                        if key and value:
                            nebula_cli.set_config(key, value)
                    elif config_action == 'Get Configuration':
                        key = inquirer.text("Enter configuration key:")
                        if key:
                            nebula_cli.get_config(key)
                    
                    console.print()  # Add spacing

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
                
                log.info(f"User selected tool: {tool_answer['tool']}")
                nebula_cli.run_tool(tool_answer['tool'])
                
            elif action == 'Help':
                nebula_cli.show_help()
            
            console.print()  # Add spacing
        
        console.print("[bold cyan]Thank you for using the Nebula CLI![/bold cyan]")
        return 0
        
    except KeyboardInterrupt:
        log.warning("Interactive mode cancelled by user.")
        console.print("\n\n[red]Operation cancelled by user.[/red]")
        return 1
    except Exception as e:
        log.error(f"Interactive mode error: {e}", exc_info=True)
        console.print(f"\n[red]An error occurred: {e}[/red]")
        return 1

def main():
    """Main CLI function with argument parsing and mode selection."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize logging
    log.info("Starting Nebula CLI")
    log.info(f"Command-line arguments: {vars(args)}")
    
    # Initialize Nebula CLI
    nebula_cli = NebulaCLI()
    
    # Determine if running in headless mode
    headless_mode = any([
        args.system_info,
        args.toolset_info,
        args.auth_status,
        args.login,
        args.logout,
        args.config,
        args.set_config,
        args.get_config,
        args.run_tool
    ])
    
    if headless_mode:
        return run_headless_mode(args, nebula_cli)
    else:
        return run_interactive_mode(nebula_cli)

if __name__ == "__main__":
    sys.exit(main())
