#!/usr/bin/env python3
"""
GCP VM Manager Tool
Interactive tool for managing Google Cloud Platform VM instances
"""

import sys
import json
import subprocess
import argparse
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
import inquirer
from pathlib import Path

# Add src to path to import nebula_cli modules
# sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
# from nebula_cli.ssh_config_manager import SSHConfigManager

console = Console()

# def handle_ssh_config_update(instance_id: str, instance_name: str, external_ip: str, args: argparse.Namespace):
#     """Handles the SSH config update process."""
#     ssh_manager = SSHConfigManager()
#     hostname = ssh_manager.get_hostname_for_instance(instance_id)

#     if hostname:
#         # Update existing entry
#         console.print(f"[blue]Updating SSH config for host '{hostname}'...[/blue]")
#         user = args.ssh_user if args.ssh_user else inquirer.text("Enter user for SSH connection:")
#         key_path = args.ssh_key_path if args.ssh_key_path else inquirer.text("Enter path to private key for SSH connection:")
#         ssh_manager.update_ssh_host(hostname, external_ip, user, key_path)
#         console.print(f"[green]SSH config updated for host '{hostname}'.[/green]")
#     else:
#         if args.yes:
#             new_host = instance_name
#             user = args.ssh_user if args.ssh_user else "nebula"
#             key_path = args.ssh_key_path if args.ssh_key_path else f"~/.ssh/{instance_name}_key"
#             ssh_manager.add_ssh_host(new_host, external_ip, user, key_path)
#             ssh_manager.set_hostname_for_instance(instance_id, new_host)
#             console.print(f"[green]New SSH host '{new_host}' created.[/green]")
#             return

#         # Prompt user to create a new entry or update an existing one
#         console.print("[blue]SSH configuration for this instance is not set up.[/blue]")
#         hosts = ssh_manager.get_ssh_hosts()
#         choices = hosts + ["Create a new host"]
        
#         questions = [
#             inquirer.List('host_choice',
#                           message="Choose an existing SSH host to update or create a new one:",
#                           choices=choices)
#         ]
#         answers = inquirer.prompt(questions)
        
#         if not answers:
#             return

#         choice = answers['host_choice']
        
#         if choice == "Create a new host":
#             new_host = inquirer.text("Enter a name for the new SSH host:")
#             user = inquirer.text("Enter user for SSH connection:")
#             key_path = inquirer.text("Enter path to private key for SSH connection:")
#             ssh_manager.add_ssh_host(new_host, external_ip, user, key_path)
#             ssh_manager.set_hostname_for_instance(instance_id, new_host)
#             console.print(f"[green]New SSH host '{new_host}' created.[/green]")
#         else:
#             user = inquirer.text("Enter user for SSH connection:")
#             key_path = inquirer.text("Enter path to private key for SSH connection:")
#             ssh_manager.update_ssh_host(choice, external_ip, user, key_path)
#             ssh_manager.set_hostname_for_instance(instance_id, choice)
#             console.print(f"[green]SSH host '{choice}' updated.[/green]")


class GCPVMManager:
    def __init__(self):
        self.console = Console()
        self.check_gcloud_auth()
    
    def check_gcloud_auth(self):
        """Check if gcloud is authenticated and configured."""
        try:
            result = subprocess.run(
                ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0 or not result.stdout.strip():
                self.console.print("[red]❌ gcloud not authenticated. Please run 'gcloud auth login' first.[/red]")
                sys.exit(1)
            
            account = result.stdout.strip()
            self.console.print(f"[green]✅ Authenticated as: {account}[/green]")
            
        except FileNotFoundError:
            self.console.print("[red]❌ gcloud CLI not found. Please install Google Cloud SDK first.[/red]")
            self.console.print("[yellow]Install from: https://cloud.google.com/sdk/docs/install[/yellow]")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ gcloud command timed out. Please check your configuration.[/red]")
            sys.exit(1)
    
    def get_project_id(self) -> str:
        """Get the current GCP project ID."""
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                project_id = result.stdout.strip()
                if project_id:
                    return project_id
        except Exception:
            pass
        
        # Fallback: prompt user for project ID
        self.console.print("[yellow]⚠️  Could not determine project ID automatically.[/yellow]")
        project_id = input("Please enter your GCP project ID: ").strip()
        if not project_id:
            self.console.print("[red]❌ No project ID provided. Exiting.[/red]")
            sys.exit(1)
        return project_id
    
    def list_instances(self, project_id: str, zone: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all VM instances in the project."""
        try:
            cmd = [
                "gcloud", "compute", "instances", "list",
                "--project", project_id,
                "--format", "json"
            ]
            
            if zone:
                cmd.extend(["--zones", zone])
            
            if status:
                cmd.extend(["--filter", f"status={status}"])
            
            print("gcloud command:", " ".join(cmd))
            self.console.print("[blue]🔍 Fetching VM instances...[/blue]")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.console.print(f"[red]❌ Failed to list instances: {result.stderr}[/red]")
                return []
            
            instances = json.loads(result.stdout)
            
            self.console.print(f"[green]✅ Found {len(instances)} instances[/green]")
            return instances
            
        except json.JSONDecodeError:
            self.console.print("[red]❌ Failed to parse instance data[/red]")
            return []
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Command timed out[/red]")
            return []
        except Exception as e:
            self.console.print(f"[red]❌ Error listing instances: {e}[/red]")
            return []
    
    def display_instances_table(self, instances: List[Dict[str, Any]], title: str = "VM Instances"):
        """Display instances in a formatted table."""
        if not instances:
            self.console.print("[yellow]⚠️  No instances found.[/yellow]")
            return
        
        table = Table(title=title)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Zone", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Machine Type", style="yellow")
        table.add_column("Internal IP", style="magenta")
        table.add_column("External IP", style="red")
        
        for instance in instances:
            status = instance.get('status', 'UNKNOWN')
            status_color = "green" if status == 'RUNNING' else "red" if status == 'TERMINATED' else "yellow"
            
            # Extract zone from full zone path
            zone = instance.get('zone', '').split('/')[-1] if instance.get('zone') else 'N/A'
            
            # Extract machine type from full path
            machine_type = instance.get('machineType', '').split('/')[-1] if instance.get('machineType') else 'N/A'
            
            # Get IP addresses
            internal_ip = 'N/A'
            external_ip = 'N/A'
            
            for network_interface in instance.get('networkInterfaces', []):
                if not internal_ip or internal_ip == 'N/A':
                    internal_ip = network_interface.get('networkIP', 'N/A')
                if not external_ip or external_ip == 'N/A':
                    access_configs = network_interface.get('accessConfigs', [])
                    if access_configs:
                        external_ip = access_configs[0].get('natIP', 'N/A')
            
            table.add_row(
                instance.get('name', 'N/A'),
                zone,
                f"[{status_color}]{status}[/{status_color}]",
                machine_type,
                internal_ip,
                external_ip
            )
        
        self.console.print(table)
    
    def get_instance_details(self, instance_name: str, zone: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific VM instance."""
        try:
            cmd = [
                "gcloud", "compute", "instances", "describe",
                instance_name,
                "--zone", zone,
                "--project", project_id,
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.console.print(f"[red]❌ Failed to get instance details: {result.stderr}[/red]")
                return None
            
            return json.loads(result.stdout)
            
        except json.JSONDecodeError:
            self.console.print("[red]❌ Failed to parse instance data[/red]")
            return None
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Command timed out[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]❌ Error getting instance details: {e}[/red]")
            return None

    def select_instance_interactive(self, instances: List[Dict[str, Any]], action: str) -> Optional[Dict[str, Any]]:
        """Allow user to select an instance interactively."""
        if not instances:
            self.console.print("[yellow]No instances available for selection.[/yellow]")
            return None
        
        # Create choices for inquirer
        choices = []
        for i, instance in enumerate(instances):
            name = instance.get('name', 'Unknown')
            zone = instance.get('zone', '').split('/')[-1] if instance.get('zone') else 'Unknown'
            status = instance.get('status', 'Unknown')
            machine_type = instance.get('machineType', '').split('/')[-1] if instance.get('machineType') else 'Unknown'
            
            choice_text = f"{name} ({status}) - {zone} - {machine_type}"
            choices.append((choice_text, instance))
        
        # Add back option
        choices.append(("← Back to main menu", None))
        
        question = inquirer.List(
            'instance',
            message=f"Select an instance to {action.lower()}:",
            choices=choices
        )
        
        try:
            answer = inquirer.prompt([question])
            if answer and answer['instance']:
                return answer['instance']
        except Exception as e:
            self.console.print(f"[red]❌ Error in interactive selection: {e}[/red]")
        
        return None
    
    def start_instance(self, instance_name: str, zone: str, project_id: str, wait: bool = False, args: argparse.Namespace = None) -> bool:
        """Start a VM instance."""
        try:
            self.console.print(f"[yellow]🚀 Starting instance '{instance_name}' in zone '{zone}'...[/yellow]")
            
            cmd = [
                "gcloud", "compute", "instances", "start",
                instance_name,
                "--zone", zone,
                "--project", project_id
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.console.print(f"[green]✅ Instance '{instance_name}' started successfully![/green]")
                
                if wait:
                    self.wait_for_instance_status(instance_name, zone, project_id, "RUNNING")

                # Get instance details to find the external IP
                # instance_details = self.get_instance_details(instance_name, zone, project_id)
                # if instance_details:
                #     external_ip = None
                #     for network_interface in instance_details.get('networkInterfaces', []):
                #         access_configs = network_interface.get('accessConfigs', [])
                #         if access_configs:
                #             external_ip = access_configs[0].get('natIP')
                #             break
                    
                #     if external_ip:
                #         handle_ssh_config_update(instance_details['id'], instance_name, external_ip, args)
                #     else:
                #         self.console.print("[yellow]⚠️  Could not find external IP for the instance.[/yellow]")
                
                return True
            else:
                self.console.print(f"[red]❌ Failed to start instance: {result.stderr}[/red]")
                return False
                
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Start operation timed out[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error starting instance: {e}[/red]")
            return False
    
    def stop_instance(self, instance_name: str, zone: str, project_id: str, wait: bool = False) -> bool:
        """Stop a VM instance."""
        try:
            self.console.print(f"[yellow]🛑 Stopping instance '{instance_name}' in zone '{zone}'...[/yellow]")
            
            cmd = [
                "gcloud", "compute", "instances", "stop",
                instance_name,
                "--zone", zone,
                "--project", project_id
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.console.print(f"[green]✅ Instance '{instance_name}' stopped successfully![/green]")
                
                if wait:
                    self.wait_for_instance_status(instance_name, zone, project_id, "TERMINATED")
                
                return True
            else:
                self.console.print(f"[red]❌ Failed to stop instance: {result.stderr}[/red]")
                return False
                
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Stop operation timed out[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error stopping instance: {e}[/red]")
            return False
    
    def wait_for_instance_status(self, instance_name: str, zone: str, project_id: str, target_status: str, max_wait: int = 300):
        """Wait for instance to reach target status."""
        self.console.print(f"[blue]⏳ Waiting for instance to reach status '{target_status}'...[/blue]")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                cmd = [
                    "gcloud", "compute", "instances", "describe",
                    instance_name,
                    "--zone", zone,
                    "--project", project_id,
                    "--format", "value(status)"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    current_status = result.stdout.strip()
                    if current_status.upper() == target_status.upper():
                        self.console.print(f"[green]✅ Instance is now {target_status}[/green]")
                        return True
                    else:
                        self.console.print(f"[blue]Current status: {current_status} (waiting for {target_status})[/blue]")
                
                time.sleep(5)
                
            except Exception as e:
                self.console.print(f"[yellow]⚠️  Error checking status: {e}[/yellow]")
                time.sleep(5)
        
        self.console.print(f"[yellow]⚠️  Timeout waiting for instance to reach {target_status}[/yellow]")
        return False
    
    def create_instance(self, project_id: str, zone: str, instance_name: str = None, machine_type: str = "e2-micro", image_family: str = "ubuntu-2004-lts", image_project: str = "ubuntu-os-cloud", args: argparse.Namespace = None) -> bool:
        """Create a new VM instance."""
        try:
            if not instance_name:
                instance_name = f"nebula-instance-{int(time.time())}"
            
            self.console.print(f"[yellow]🚀 Creating instance '{instance_name}' in zone '{zone}'...[/yellow]")
            
            cmd = [
                "gcloud", "compute", "instances", "create", instance_name,
                "--zone", zone,
                "--project", project_id,
                "--machine-type", machine_type,
                "--image-family", image_family,
                "--image-project", image_project,
                "--boot-disk-size", "10GB",
                "--boot-disk-type", "pd-standard",
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.console.print(f"[green]✅ Instance '{instance_name}' created successfully![/green]")
                
                # Wait for instance to be running
                self.wait_for_instance_status(instance_name, zone, project_id, "RUNNING")
                
                # Get instance details to find the external IP
                # instance_details = self.get_instance_details(instance_name, zone, project_id)
                # if instance_details:
                #     external_ip = None
                #     for network_interface in instance_details.get('networkInterfaces', []):
                #         access_configs = network_interface.get('accessConfigs', [])
                #         if access_configs:
                #             external_ip = access_configs[0].get('natIP')
                #             break
                    
                #     if external_ip:
                #         handle_ssh_config_update(instance_details['id'], instance_name, external_ip, args)
                #     else:
                #         self.console.print("[yellow]⚠️  Could not find external IP for the instance.[/yellow]")
                
                return True
            else:
                self.console.print(f"[red]❌ Failed to create instance: {result.stderr}[/red]")
                return False
                
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Create operation timed out[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error creating instance: {e}[/red]")
            return False

    def confirm_action(self, action: str, instance_name: str, zone: str) -> bool:
        """Ask for confirmation before performing destructive actions."""
        if action.lower() in ['stop', 'terminate']:
            self.console.print(f"[red]⚠️  You are about to {action.upper()} instance '{instance_name}' in zone '{zone}'.[/red]")
            self.console.print("[yellow]This will power off the instance. Are you sure?[/yellow]")
            
            try:
                question = inquirer.Confirm('confirm', message="Do you want to continue?")
                answer = inquirer.prompt([question])
                return answer and answer.get('confirm', False)
            except Exception:
                # Fallback to simple input if inquirer fails
                response = input("Type 'yes' to confirm: ").strip().lower()
                return response == 'yes'
        
        return True
    
    def start_all_instances(self, project_id: str, zone: Optional[str] = None, wait: bool = False) -> Dict[str, bool]:
        """Start all terminated instances."""
        instances = self.list_instances(project_id, zone, "TERMINATED")
        
        if not instances:
            self.console.print("[yellow]No terminated instances found to start.[/yellow]")
            return {}
        
        self.console.print(f"[blue]🚀 Starting {len(instances)} terminated instances...[/blue]")
        
        results = {}
        successful_starts = 0
        
        for instance in instances:
            instance_name = instance.get('name')
            instance_zone = instance.get('zone', '').split('/')[-1]
            
            self.console.print(f"[yellow]Starting {instance_name} in {instance_zone}...[/yellow]")
            
            success = self.start_instance(instance_name, instance_zone, project_id, wait)
            results[instance_name] = success
            
            if success:
                successful_starts += 1
        
        self.console.print(f"[green]✅ Successfully started {successful_starts}/{len(instances)} instances[/green]")
        return results
    
    def stop_all_instances(self, project_id: str, zone: Optional[str] = None, wait: bool = False) -> Dict[str, bool]:
        """Stop all running instances."""
        instances = self.list_instances(project_id, zone, "RUNNING")
        
        if not instances:
            self.console.print("[yellow]No running instances found to stop.[/yellow]")
            return {}
        
        self.console.print(f"[blue]🛑 Stopping {len(instances)} running instances...[/blue]")
        
        results = {}
        successful_stops = 0
        
        for instance in instances:
            instance_name = instance.get('name')
            instance_zone = instance.get('zone', '').split('/')[-1]
            
            self.console.print(f"[yellow]Stopping {instance_name} in {instance_zone}...[/yellow]")
            
            success = self.stop_instance(instance_name, instance_zone, project_id, wait)
            results[instance_name] = success
            
            if success:
                successful_stops += 1
        
        self.console.print(f"[green]✅ Successfully stopped {successful_stops}/{len(instances)} instances[/green]")
        return results
    
    def run_interactive_mode(self, project_id: str, zone: Optional[str] = None):
        """Run the tool in interactive mode."""
        while True:
            # Main menu
            main_menu = [
                inquirer.List(
                    'action',
                    message="What would you like to do?",
                    choices=[
                        'List All Instances',
                        'List Running Instances',
                        'List Terminated Instances',
                        'Create Instance',
                        'Start Instance',
                        'Stop Instance',
                        'Start All Instances',
                        'Stop All Instances',
                        'Exit'
                    ],
                ),
            ]
            
            try:
                answers = inquirer.prompt(main_menu)
                if not answers or answers['action'] == 'Exit':
                    break
                
                action = answers['action']
                
                if action == 'List All Instances':
                    instances = self.list_instances(project_id, zone)
                    self.display_instances_table(instances, "All VM Instances")
                
                elif action == 'List Running Instances':
                    instances = self.list_instances(project_id, zone, "RUNNING")
                    self.display_instances_table(instances, "Running VM Instances")
                
                elif action == 'List Terminated Instances':
                    instances = self.list_instances(project_id, zone, "TERMINATED")
                    self.display_instances_table(instances, "Terminated VM Instances")
                
                elif action == 'Create Instance':
                    # Prompt for instance creation parameters
                    instance_name = inquirer.text("Enter instance name (or press Enter for auto-generated):")
                    if not instance_name.strip():
                        instance_name = None
                    
                    zone_choice = inquirer.text("Enter zone (e.g., us-central1-a):")
                    if not zone_choice.strip():
                        self.console.print("[red]❌ Zone is required for instance creation.[/red]")
                        continue
                    
                    machine_type = inquirer.text("Enter machine type (default: e2-micro):")
                    if not machine_type.strip():
                        machine_type = "e2-micro"
                    
                    if self.create_instance(project_id, zone_choice, instance_name, machine_type):
                        self.console.print(f"[green]🎉 Instance created successfully![/green]")
                
                elif action == 'Start Instance':
                    # Show only terminated instances for starting
                    instances = self.list_instances(project_id, zone, "TERMINATED")
                    if not instances:
                        self.console.print("[yellow]No terminated instances available to start.[/yellow]")
                        continue
                    
                    selected_instance = self.select_instance_interactive(instances, "start")
                    if selected_instance:
                        instance_name = selected_instance.get('name')
                        instance_zone = selected_instance.get('zone', '').split('/')[-1]
                        
                        if self.start_instance(instance_name, instance_zone, project_id, wait=True):
                            self.console.print(f"[green]🎉 Instance '{instance_name}' is now running![/green]")
                
                elif action == 'Stop Instance':
                    # Show only running instances for stopping
                    instances = self.list_instances(project_id, zone, "RUNNING")
                    if not instances:
                        self.console.print("[yellow]No running instances available to stop.[/yellow]")
                        continue
                    
                    selected_instance = self.select_instance_interactive(instances, "stop")
                    if selected_instance:
                        instance_name = selected_instance.get('name')
                        instance_zone = selected_instance.get('zone', '').split('/')[-1]
                        
                        if self.confirm_action("stop", instance_name, instance_zone):
                            if self.stop_instance(instance_name, instance_zone, project_id, wait=True):
                                self.console.print(f"[green]🎉 Instance '{instance_name}' has been stopped![/green]")
                        else:
                            self.console.print("[yellow]Operation cancelled.[/yellow]")
                
                elif action == 'Start All Instances':
                    # Start all terminated instances
                    instances = self.list_instances(project_id, zone, "TERMINATED")
                    if not instances:
                        self.console.print("[yellow]No terminated instances available to start.[/yellow]")
                        continue
                    
                    self.console.print(f"[blue]Found {len(instances)} terminated instances to start.[/blue]")
                    self.display_instances_table(instances, "Instances to Start")
                    
                    if self.confirm_action("start all", f"{len(instances)} instances", "all zones"):
                        results = self.start_all_instances(project_id, zone, wait=True)
                        successful = sum(1 for success in results.values() if success)
                        self.console.print(f"[green]🎉 Successfully started {successful}/{len(instances)} instances![/green]")
                    else:
                        self.console.print("[yellow]Operation cancelled.[/yellow]")
                
                elif action == 'Stop All Instances':
                    # Stop all running instances
                    instances = self.list_instances(project_id, zone, "RUNNING")
                    if not instances:
                        self.console.print("[yellow]No running instances available to stop.[/yellow]")
                        continue
                    
                    self.console.print(f"[blue]Found {len(instances)} running instances to stop.[/blue]")
                    self.display_instances_table(instances, "Instances to Stop")
                    
                    if self.confirm_action("stop all", f"{len(instances)} instances", "all zones"):
                        results = self.stop_all_instances(project_id, zone, wait=True)
                        successful = sum(1 for success in results.values() if success)
                        self.console.print(f"[green]🎉 Successfully stopped {successful}/{len(instances)} instances![/green]")
                    else:
                        self.console.print("[yellow]Operation cancelled.[/yellow]")
                
                self.console.print()  # Add spacing
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operation cancelled by user.[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error in interactive mode: {e}[/red]")
                break
    
    def run_headless_mode(self, args):
        """Run the tool in headless mode."""
        project_id = args.project or self.get_project_id()
        zone = args.zone
        
        if args.list_all:
            instances = self.list_instances(project_id, zone)
            self.display_instances_table(instances, "All VM Instances")
        
        elif args.list_running:
            instances = self.list_instances(project_id, zone, "RUNNING")
            self.display_instances_table(instances, "Running VM Instances")
        
        elif args.list_terminated:
            instances = self.list_instances(project_id, zone, "TERMINATED")
            self.display_instances_table(instances, "Terminated VM Instances")
        
        elif args.create_instance:
            if not zone:
                self.console.print("[red]❌ Zone is required for instance creation. Use --zone option.[/red]")
                return False
            
            return self.create_instance(
                project_id, 
                zone, 
                args.create_instance, 
                args.machine_type, 
                args.image_family, 
                args.image_project, 
                args
            )
        
        elif args.start_instance:
            # Find the instance to start
            all_instances = self.list_instances(project_id, zone)
            instances = [inst for inst in all_instances if inst.get('status', '').upper() == "TERMINATED"]
            print("Terminated instances:", instances)
            target_instance = None
            
            for instance in instances:
                if instance.get('name') == args.start_instance:
                    target_instance = instance
                    break
            
            if not target_instance:
                self.console.print(f"[red]❌ Instance '{args.start_instance}' not found in terminated instances.[/red]")
                return False
            
            instance_zone = target_instance.get('zone', '').split('/')[-1]
            return self.start_instance(args.start_instance, instance_zone, project_id, args.wait, args)
        
        elif args.stop_instance:
            # Find the instance to stop
            all_instances = self.list_instances(project_id, zone)
            instances = [inst for inst in all_instances if inst.get('status', '').upper() == "RUNNING"]
            print("Running instances:", instances)
            target_instance = None
            
            for instance in instances:
                if instance.get('name') == args.stop_instance:
                    target_instance = instance
                    break
            
            if not target_instance:
                self.console.print(f"[red]❌ Instance '{args.stop_instance}' not found in running instances.[/red]")
                return False
            
            instance_zone = target_instance.get('zone', '').split('/')[-1]
            
            if args.yes or self.confirm_action("stop", args.stop_instance, instance_zone):
                return self.stop_instance(args.stop_instance, instance_zone, project_id, args.wait)
            else:
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return False
        
        elif args.start_all:
            # Start all terminated instances
            instances = self.list_instances(project_id, zone, "TERMINATED")
            if not instances:
                self.console.print("[yellow]No terminated instances found to start.[/yellow]")
                return True
            
            self.console.print(f"[blue]Found {len(instances)} terminated instances to start.[/blue]")
            self.display_instances_table(instances, "Instances to Start")
            
            if args.yes or self.confirm_action("start all", f"{len(instances)} instances", "all zones"):
                results = self.start_all_instances(project_id, zone, args.wait)
                successful = sum(1 for success in results.values() if success)
                self.console.print(f"[green]✅ Successfully started {successful}/{len(instances)} instances[/green]")
                return successful == len(instances)
            else:
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return False
        
        elif args.stop_all:
            # Stop all running instances
            instances = self.list_instances(project_id, zone, "RUNNING")
            if not instances:
                self.console.print("[yellow]No running instances found to stop.[/yellow]")
                return True
            
            self.console.print(f"[blue]Found {len(instances)} running instances to stop.[/blue]")
            self.display_instances_table(instances, "Instances to Stop")
            
            if args.yes or self.confirm_action("stop all", f"{len(instances)} instances", "all zones"):
                results = self.stop_all_instances(project_id, zone, args.wait)
                successful = sum(1 for success in results.values() if success)
                self.console.print(f"[green]✅ Successfully stopped {successful}/{len(instances)} instances[/green]")
                return successful == len(instances)
            else:
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return False
        
        return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GCP VM Manager - Interactive tool for managing Google Cloud Platform VM instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python main.py
  
  # List all instances
  python main.py --list-all
  
  # List running instances
  python main.py --list-running
  
  # List terminated instances
  python main.py --list-terminated
  
  # Create a new instance
  python main.py --create-instance my-new-instance --zone us-central1-a
  
  # Start a specific instance
  python main.py --start-instance my-instance --zone us-central1-a
  
  # Stop a specific instance
  python main.py --stop-instance my-instance --zone us-central1-a --yes
  
  # Start all terminated instances
  python main.py --start-all --wait
  
  # Stop all running instances
  python main.py --stop-all --yes --wait
  
  # Wait for operation to complete
  python main.py --start-instance my-instance --wait
        """
    )
    
    # Project and zone options
    parser.add_argument('--project', help='GCP project ID (default: current project)')
    parser.add_argument('--zone', help='GCP zone to filter instances')
    
    # List options
    parser.add_argument('--list-all', action='store_true', help='List all instances')
    parser.add_argument('--list-running', action='store_true', help='List running instances')
    parser.add_argument('--list-terminated', action='store_true', help='List terminated instances')
    
    # Instance management options
    parser.add_argument('--create-instance', type=str, help='Create a new instance with specified name')
    parser.add_argument('--machine-type', type=str, default='e2-micro', help='Machine type for new instance (default: e2-micro)')
    parser.add_argument('--image-family', type=str, default='ubuntu-2004-lts', help='Image family for new instance (default: ubuntu-2004-lts)')
    parser.add_argument('--image-project', type=str, default='ubuntu-os-cloud', help='Image project for new instance (default: ubuntu-os-cloud)')
    parser.add_argument('--start-instance', type=str, help='Start a specific instance')
    parser.add_argument('--stop-instance', type=str, help='Stop a specific instance')
    parser.add_argument('--start-all', action='store_true', help='Start all terminated instances')
    parser.add_argument('--stop-all', action='store_true', help='Stop all running instances')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--wait', action='store_true', help='Wait for operation to complete')
    parser.add_argument('--ssh-user', type=str, help='User for SSH connection')
    parser.add_argument('--ssh-key-path', type=str, help='Path to private key for SSH connection')
    
    args = parser.parse_args()
    
    # Determine if running in headless mode
    headless_mode = any([
        args.list_all,
        args.list_running,
        args.list_terminated,
        args.create_instance,
        args.start_instance,
        args.stop_instance,
        args.start_all,
        args.stop_all
    ])
    
    # Create and run the manager
    manager = GCPVMManager()
    
    if headless_mode:
        success = manager.run_headless_mode(args)
        sys.exit(0 if success else 1)
    else:
        project_id = args.project or manager.get_project_id()
        # Show available instances and usage instructions
        print("🔍 GCP VM Manager - Available Instances")
        print("=" * 50)
        instances = manager.list_instances(project_id, args.zone)
        manager.display_instances_table(instances, "Available VM Instances")
        
        print("\n📋 Available Operations:")
        print("  --list-all          List all instances")
        print("  --list-running      List running instances")
        print("  --list-terminated   List terminated instances")
        print("  --create-instance   Create a new instance")
        print("  --start-all         Start all terminated instances")
        print("  --stop-all          Stop all running instances")
        print("  --start-instance    Start a specific instance")
        print("  --stop-instance     Stop a specific instance")
        print("  --help              Show all options")
        print("\n💡 Examples:")
        print("  python main.py --create-instance my-instance --zone us-central1-a")
        print("  python main.py --start-all --wait")
        print("  python main.py --stop-all --yes --wait")
        print("  python main.py --list-running")
        
        # Try interactive mode as fallback
        try:
            print("\n🔄 Starting interactive mode...")
            manager.run_interactive_mode(project_id, args.zone)
        except Exception as e:
            print(f"\n⚠️  Interactive mode unavailable: {e}")
            print("Please use command-line arguments for operations.")

if __name__ == "__main__":
    main()
