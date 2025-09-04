#!/usr/bin/env python3
"""
Authentication manager for Nebula CLI
Handles user authentication, project ID management, and auth flows
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import subprocess
import json
import os
try:
    from .database import DatabaseManager
except ImportError:
    # Handle case when running as standalone script
    from database import DatabaseManager

console = Console()
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Manages authentication for the Nebula CLI"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize authentication manager"""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
        self.current_user = None
        self.current_project_id = None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.db_manager.is_authenticated()
    
    def get_current_auth_data(self) -> Optional[Dict[str, Any]]:
        """Get current authentication data"""
        return self.db_manager.get_auth_data()
    
    def authenticate_user(self) -> bool:
        """Interactive authentication flow"""
        console.print("\n[bold blue]Authentication Required[/bold blue]")
        console.print("Please authenticate to continue using the Nebula CLI.\n")
        
        # Get authentication method
        auth_methods = [
            'Google Cloud OAuth (gcloud)',
            'API Key Authentication',
            'Skip Authentication (Limited Features)'
        ]
        
        auth_choice = inquirer.list_input(
            "Select authentication method:",
            choices=auth_methods
        )
        
        if auth_choice == 'Skip Authentication (Limited Features)':
            console.print("[yellow]Skipping authentication. Some features may be limited.[/yellow]")
            return False
        
        if auth_choice == 'Google Cloud OAuth (gcloud)':
            return self._authenticate_with_gcloud()
        elif auth_choice == 'API Key Authentication':
            return self._authenticate_with_api_key()
        
        return False
    
    def _authenticate_with_gcloud(self) -> bool:
        """Authenticate using Google Cloud OAuth via gcloud CLI"""
        try:
            console.print("[yellow]Authenticating with Google Cloud...[/yellow]")
            
            # Check if gcloud is available
            if not self._check_gcloud_available():
                console.print("[red]gcloud CLI is not available. Please install Google Cloud SDK.[/red]")
                return False
            
            # Check if user is already authenticated and token is valid
            if self._is_gcloud_authenticated() and self._is_gcloud_token_valid():
                console.print("[green]Already authenticated with gcloud![/green]")
                return self._get_gcloud_credentials()
            elif self._is_gcloud_authenticated():
                console.print("[yellow]gcloud authentication found but token expired. Refreshing...[/yellow]")
                return self._get_gcloud_credentials()
            
            # Start gcloud authentication
            console.print("[blue]Starting gcloud authentication...[/blue]")
            console.print("This will open your browser for Google Cloud authentication.")
            
            # Run gcloud auth login
            result = subprocess.run(
                ['gcloud', 'auth', 'login', '--no-launch-browser'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                console.print(f"[red]gcloud authentication failed: {result.stderr}[/red]")
                return False
            
            console.print("[green]gcloud authentication successful![/green]")
            
            # Get credentials and project info
            return self._get_gcloud_credentials()
            
        except subprocess.TimeoutExpired:
            console.print("[red]gcloud authentication timed out. Please try again.[/red]")
            return False
        except KeyboardInterrupt:
            console.print("\n[yellow]Authentication cancelled by user[/yellow]")
            return False
        except Exception as e:
            self.logger.error(f"gcloud authentication error: {e}")
            console.print(f"[red]gcloud authentication error: {e}[/red]")
            return False
    
    def _check_gcloud_available(self) -> bool:
        """Check if gcloud CLI is available"""
        try:
            result = subprocess.run(
                ['gcloud', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _is_gcloud_authenticated(self) -> bool:
        """Check if user is already authenticated with gcloud"""
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _is_gcloud_token_valid(self) -> bool:
        """Check if gcloud access token is valid"""
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'print-access-token'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_gcloud_credentials(self) -> bool:
        """Get gcloud credentials and project information"""
        try:
            # Get current account
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'account'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                console.print("[red]Failed to get gcloud account information[/red]")
                return False
            
            user_email = result.stdout.strip()
            if not user_email:
                console.print("[red]No active gcloud account found[/red]")
                return False
            
            # Get current project
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'project'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            current_project = result.stdout.strip() if result.returncode == 0 else None
            
            # Handle project selection
            if not current_project:
                console.print("[yellow]No default project set. Please select a project:[/yellow]")
                project_id = self._select_gcloud_project()
                if not project_id:
                    console.print("[red]No project selected[/red]")
                    return False
            else:
                # Ask if user wants to change the current project
                console.print(f"[green]Current project: {current_project}[/green]")
                change_project = inquirer.confirm(
                    "Would you like to change the project?",
                    default=False
                )
                
                if change_project:
                    project_id = self._select_gcloud_project()
                    if not project_id:
                        console.print("[yellow]Keeping current project[/yellow]")
                        project_id = current_project
                else:
                    project_id = current_project
            
            # Get access token
            result = subprocess.run(
                ['gcloud', 'auth', 'print-access-token'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                if "Reauthentication required" in result.stderr or "Reauthentication failed" in result.stderr:
                    console.print("[yellow]gcloud reauthentication required.[/yellow]")
                    console.print("[blue]Please run one of the following commands:[/blue]")
                    console.print("  [cyan]gcloud auth login[/cyan] - Interactive authentication")
                    console.print("  [cyan]gcloud auth application-default login[/cyan] - Application default credentials")
                    console.print("  [cyan]gcloud config set account ACCOUNT[/cyan] - Switch to different account")
                else:
                    console.print(f"[red]Failed to get gcloud access token: {result.stderr}[/red]")
                return False
            
            access_token = result.stdout.strip()
            
            # Store authentication data
            success = self.db_manager.store_auth_data(
                user_id=user_email,
                project_id=project_id,
                auth_provider='gcloud_oauth',
                access_token=access_token,
                token_expires_at=datetime.now() + timedelta(hours=1)  # gcloud tokens typically last 1 hour
            )
            
            if success:
                self.current_user = user_email
                self.current_project_id = project_id
                
                # Log the authentication
                self.db_manager.log_action(
                    user_id=user_email,
                    action='login',
                    details=f'gcloud OAuth authentication for project {project_id}'
                )
                
                console.print(f"[green]Successfully authenticated as {user_email}[/green]")
                console.print(f"[green]Project ID: {project_id}[/green]")
                return True
            else:
                console.print("[red]Failed to store authentication data[/red]")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to get gcloud credentials: {e}")
            console.print(f"[red]Failed to get gcloud credentials: {e}[/red]")
            return False
    
    def _select_gcloud_project(self) -> Optional[str]:
        """Let user select a gcloud project"""
        try:
            console.print("[blue]Fetching available projects...[/blue]")
            
            # Get list of projects with more detailed information
            result = subprocess.run(
                ['gcloud', 'projects', 'list', '--format=table(projectId,name,projectNumber,lifecycleState)'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                console.print(f"[red]Failed to list gcloud projects: {result.stderr}[/red]")
                return None
            
            # Parse the table output
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:  # Header + at least one project
                console.print("[yellow]No projects found[/yellow]")
                console.print("[blue]You may need to create a project first:[/blue]")
                console.print("  [cyan]gcloud projects create PROJECT_ID[/cyan]")
                return None
            
            # Skip header line and parse projects
            projects = []
            project_map = {}
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    # Parse the table format more carefully
                    # The format is: PROJECT_ID NAME PROJECT_NUMBER LIFECYCLE_STATE
                    # We need to handle cases where NAME might be empty
                    parts = line.split()
                    if len(parts) >= 3:
                        project_id = parts[0]
                        project_number = parts[-2]  # Second to last is project number
                        lifecycle_state = parts[-1]  # Last is lifecycle state
                        
                        # Extract project name (everything between project_id and project_number)
                        if len(parts) > 3:
                            project_name = ' '.join(parts[1:-2])
                        else:
                            project_name = "Unnamed Project"
                        
                        # Only show ACTIVE projects
                        if lifecycle_state == "ACTIVE":
                            display_name = f"{project_id} ({project_name})"
                            projects.append(display_name)
                            project_map[display_name] = project_id
            
            if not projects:
                console.print("[yellow]No active projects found[/yellow]")
                console.print("[blue]You may need to create a project first:[/blue]")
                console.print("  [cyan]gcloud projects create PROJECT_ID[/cyan]")
                return None
            
            # Show project count
            console.print(f"[green]Found {len(projects)} active project(s)[/green]")
            
            # Let user select project
            project_choice = inquirer.list_input(
                "Select a project:",
                choices=projects
            )
            
            # Get project ID from choice
            project_id = project_map[project_choice]
            
            # Set as default project
            console.print(f"[blue]Setting project to {project_id}...[/blue]")
            result = subprocess.run(
                ['gcloud', 'config', 'set', 'project', project_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                console.print(f"[green]Successfully set project to {project_id}[/green]")
            else:
                console.print(f"[yellow]Warning: Failed to set default project: {result.stderr}[/yellow]")
            
            return project_id
            
        except Exception as e:
            self.logger.error(f"Failed to select gcloud project: {e}")
            console.print(f"[red]Failed to select gcloud project: {e}[/red]")
            return None
    
    def _refresh_gcloud_token(self) -> bool:
        """Refresh gcloud access token"""
        try:
            # Check if still authenticated with gcloud
            if not self._is_gcloud_authenticated():
                console.print("[yellow]gcloud authentication lost. Please re-authenticate.[/yellow]")
                return self.authenticate_user()
            
            # Get fresh credentials
            return self._get_gcloud_credentials()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh gcloud token: {e}")
            console.print(f"[red]Failed to refresh gcloud token: {e}[/red]")
            return False
    
    def _authenticate_with_api_key(self) -> bool:
        """Authenticate using API key"""
        try:
            # Get user details
            user_id = inquirer.text("Enter your user ID or email:")
            if not user_id:
                console.print("[red]User ID is required[/red]")
                return False
            
            # Get project ID
            project_id = inquirer.text("Enter your project ID:")
            if not project_id:
                console.print("[red]Project ID is required[/red]")
                return False
            
            # Get API key
            api_key = inquirer.password("Enter your API key:")
            if not api_key:
                console.print("[red]API key is required[/red]")
                return False
            
            # Validate API key (placeholder - replace with actual validation)
            if not self._validate_api_key(api_key):
                console.print("[red]Invalid API key[/red]")
                return False
            
            # Store authentication data
            success = self.db_manager.store_auth_data(
                user_id=user_id,
                project_id=project_id,
                auth_provider='api_key',
                access_token=api_key,
                token_expires_at=datetime.now() + timedelta(days=30)  # 30 days expiry
            )
            
            if success:
                self.current_user = user_id
                self.current_project_id = project_id
                
                # Log the authentication
                self.db_manager.log_action(
                    user_id=user_id,
                    action='login',
                    details=f'API key authentication for project {project_id}'
                )
                
                console.print(f"[green]Successfully authenticated as {user_id}[/green]")
                console.print(f"[green]Project ID: {project_id}[/green]")
                return True
            else:
                console.print("[red]Failed to store authentication data[/red]")
                return False
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Authentication cancelled by user[/yellow]")
            return False
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            console.print(f"[red]Authentication error: {e}[/red]")
            return False
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key (placeholder implementation)"""
        # TODO: Implement actual API key validation
        # For now, just check if it's not empty and has reasonable length
        return len(api_key) >= 10
    
    def logout(self) -> bool:
        """Logout current user"""
        try:
            auth_data = self.get_current_auth_data()
            if not auth_data:
                console.print("[yellow]No active authentication to logout[/yellow]")
                return False
            
            user_id = auth_data['user_id']
            
            # Log the logout action
            self.db_manager.log_action(
                user_id=user_id,
                action='logout',
                details='User logged out'
            )
            
            # Deactivate authentication
            success = self.db_manager.logout(user_id)
            
            if success:
                self.current_user = None
                self.current_project_id = None
                console.print("[green]Successfully logged out[/green]")
                return True
            else:
                console.print("[red]Failed to logout[/red]")
                return False
                
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            console.print(f"[red]Logout error: {e}[/red]")
            return False
    
    def get_project_id(self) -> Optional[str]:
        """Get current project ID"""
        if self.current_project_id:
            return self.current_project_id
        
        auth_data = self.get_current_auth_data()
        if auth_data and auth_data.get('project_id'):
            self.current_project_id = auth_data['project_id']
            return self.current_project_id
        
        return None
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.current_user:
            return self.current_user
        
        auth_data = self.get_current_auth_data()
        if auth_data and auth_data.get('user_id'):
            self.current_user = auth_data['user_id']
            return self.current_user
        
        return None
    
    def refresh_authentication(self) -> bool:
        """Refresh authentication if needed"""
        try:
            auth_data = self.get_current_auth_data()
            if not auth_data:
                return False
            
            # Check if token is expired
            if auth_data.get('token_expires_at'):
                try:
                    expires_at = datetime.fromisoformat(auth_data['token_expires_at'])
                    if datetime.now() >= expires_at:
                        self.logger.info("Authentication token expired, attempting refresh")
                        
                        # For API key auth, we can't refresh, need to re-authenticate
                        if auth_data.get('auth_provider') == 'api_key':
                            console.print("[yellow]Your API key has expired. Please re-authenticate.[/yellow]")
                            return self.authenticate_user()
                        
                        # For gcloud OAuth, try to refresh the token
                        elif auth_data.get('auth_provider') == 'gcloud_oauth':
                            console.print("[yellow]Your gcloud token has expired. Refreshing...[/yellow]")
                            return self._refresh_gcloud_token()
                        
                        return False
                except ValueError:
                    self.logger.warning("Invalid token expiration format")
            
            return True
        except Exception as e:
            self.logger.error(f"Authentication refresh error: {e}")
            return False
    
    def show_auth_status(self):
        """Display current authentication status"""
        auth_data = self.get_current_auth_data()
        
        if not auth_data:
            console.print("[red]Not authenticated[/red]")
            return
        
        # Create status panel
        status_text = f"""
[bold]User ID:[/bold] {auth_data.get('user_id', 'N/A')}
[bold]Project ID:[/bold] {auth_data.get('project_id', 'N/A')}
[bold]Auth Provider:[/bold] {auth_data.get('auth_provider', 'N/A')}
[bold]Last Updated:[/bold] {auth_data.get('updated_at', 'N/A')}
        """
        
        if auth_data.get('token_expires_at'):
            try:
                expires_at = datetime.fromisoformat(auth_data['token_expires_at'])
                status_text += f"\n[bold]Token Expires:[/bold] {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
            except ValueError:
                status_text += f"\n[bold]Token Expires:[/bold] {auth_data.get('token_expires_at', 'N/A')}"
        
        # Add gcloud status if using gcloud OAuth
        if auth_data.get('auth_provider') == 'gcloud_oauth':
            gcloud_status = self._get_gcloud_status()
            status_text += f"\n[bold]gcloud Status:[/bold] {gcloud_status}"
        
        console.print(Panel(status_text, title="Authentication Status", border_style="blue"))
    
    def _get_gcloud_status(self) -> str:
        """Get gcloud authentication status"""
        try:
            if not self._check_gcloud_available():
                return "gcloud CLI not available"
            
            if not self._is_gcloud_authenticated():
                return "Not authenticated with gcloud"
            
            # Get current account
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'account'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return f"Authenticated as {result.stdout.strip()}"
            else:
                return "gcloud authentication unknown"
                
        except Exception as e:
            return f"Error checking gcloud status: {e}"
    
    def require_authentication(self) -> bool:
        """Require authentication, prompt if not authenticated"""
        if self.is_authenticated():
            return True
        
        console.print("\n[bold red]Authentication Required[/bold red]")
        console.print("This feature requires authentication.\n")
        
        choice = inquirer.list_input(
            "Would you like to authenticate now?",
            choices=['Yes', 'No']
        )
        
        if choice == 'Yes':
            return self.authenticate_user()
        else:
            console.print("[yellow]Authentication cancelled. Some features may be limited.[/yellow]")
            return False
    
    def get_auth_info(self) -> Dict[str, Any]:
        """Get authentication information for display"""
        auth_data = self.get_current_auth_data()
        if not auth_data:
            return {
                'authenticated': False,
                'user_id': None,
                'project_id': None,
                'auth_provider': None
            }
        
        return {
            'authenticated': True,
            'user_id': auth_data.get('user_id'),
            'project_id': auth_data.get('project_id'),
            'auth_provider': auth_data.get('auth_provider'),
            'last_updated': auth_data.get('updated_at'),
            'token_expires': auth_data.get('token_expires_at')
        }
