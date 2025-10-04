#!/usr/bin/env python3
"""
Simplified Nebula CLI - VM Management
Focused on 4 core actions: start-vm, list-vms, stop-vm, update-ssh-config
"""

import typer
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

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from api.ssh_config_manager import SSHConfigManager

console = Console()
app = typer.Typer(help="Simplified Nebula CLI for VM Management")

class SimplifiedVMManager:
    def __init__(self):
        self.console = Console()
        self.ssh_manager = SSHConfigManager()
        self.check_gcloud_auth()
    
    def check_gcloud_auth(self):
        """Check if gcloud is authenticated and configured."""
        try:
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=json'], 
                                  capture_output=True, text=True, check=True)
            accounts = json.loads(result.stdout)
            if not accounts:
                self.console.print("[red]❌ No active gcloud authentication found.[/red]")
                self.console.print("Please run: [bold]gcloud auth login[/bold]")
                sys.exit(1)
            self.console.print(f"[green]✅ Authenticated as: {accounts[0]['account']}[/green]")
        except subprocess.CalledProcessError:
            self.console.print("[red]❌ gcloud not found or not configured.[/red]")
            self.console.print("Please install Google Cloud SDK and run: [bold]gcloud auth login[/bold]")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[red]❌ Error checking gcloud authentication: {e}[/red]")
            sys.exit(1)
    
    def get_project_id(self) -> str:
        """Get the current GCP project ID."""
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            self.console.print("[red]❌ Could not get GCP project ID.[/red]")
            self.console.print("Please run: [bold]gcloud config set project YOUR_PROJECT_ID[/bold]")
            sys.exit(1)
    
    def list_instances(self, project_id: str, zone: Optional[str] = None) -> List[Dict[str, Any]]:
        """List GCP VM instances."""
        cmd = ['gcloud', 'compute', 'instances', 'list', '--project', project_id, '--format=json']
        if zone:
            cmd.extend(['--zones', zone])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)
            return instances
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error listing instances: {e.stderr}[/red]")
            return []
    
    def start_instance(self, project_id: str, instance_name: str, zone: str) -> bool:
        """Start a GCP VM instance."""
        cmd = ['gcloud', 'compute', 'instances', 'start', instance_name, '--project', project_id, '--zone', zone]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.console.print(f"[green]✅ Started instance '{instance_name}'[/green]")
            return True
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error starting instance: {e.stderr}[/red]")
            return False
    
    def stop_instance(self, project_id: str, instance_name: str, zone: str) -> bool:
        """Stop a GCP VM instance."""
        cmd = ['gcloud', 'compute', 'instances', 'stop', instance_name, '--project', project_id, '--zone', zone]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.console.print(f"[green]✅ Stopped instance '{instance_name}'[/green]")
            return True
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error stopping instance: {e.stderr}[/red]")
            return False
    
    def get_instance_external_ip(self, project_id: str, instance_name: str, zone: str) -> Optional[str]:
        """Get the external IP of a GCP VM instance."""
        cmd = ['gcloud', 'compute', 'instances', 'describe', instance_name, '--project', project_id, '--zone', zone, '--format=json']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            instance_data = json.loads(result.stdout)
            
            # Look for external IP in network interfaces
            for interface in instance_data.get('networkInterfaces', []):
                for access_config in interface.get('accessConfigs', []):
                    if 'natIP' in access_config:
                        return access_config['natIP']
            return None
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ Error getting instance IP: {e.stderr}[/red]")
            return None
    
    def update_ssh_config(self, instance_name: str, external_ip: str) -> bool:
        """Update SSH config for a VM instance."""
        try:
            # Check if we already have a mapping for this instance
            mappings = self.ssh_manager.get_mappings()
            hostname = mappings.get(instance_name)
            
            if hostname:
                # Update existing entry
                self.console.print(f"[blue]Updating SSH config for host '{hostname}'...[/blue]")
                user = "nebula"  # Default user
                key_path = f"~/.ssh/{instance_name}_key"  # Default key path
                self.ssh_manager.update_ssh_host(hostname, external_ip, user, key_path)
                self.console.print(f"[green]✅ SSH config updated for host '{hostname}'[/green]")
            else:
                # Create new entry
                self.console.print(f"[blue]Creating new SSH config entry for '{instance_name}'...[/blue]")
                user = "nebula"  # Default user
                key_path = f"~/.ssh/{instance_name}_key"  # Default key path
                self.ssh_manager.add_ssh_host(instance_name, external_ip, user, key_path)
                self.ssh_manager.set_hostname_for_instance(instance_name, instance_name)
                self.console.print(f"[green]✅ New SSH host '{instance_name}' created[/green]")
            
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Error updating SSH config: {e}[/red]")
            return False
    
    def display_instances_table(self, instances: List[Dict[str, Any]], title: str = "VM Instances"):
        """Display instances in a formatted table."""
        if not instances:
            self.console.print("[yellow]No instances found.[/yellow]")
            return
        
        table = Table(title=title)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Zone", style="blue")
        table.add_column("External IP", style="magenta")
        table.add_column("Machine Type", style="yellow")
        
        for instance in instances:
            name = instance.get('name', 'Unknown')
            status = instance.get('status', 'Unknown')
            zone = instance.get('zone', 'Unknown').split('/')[-1]
            
            # Get external IP
            external_ip = "None"
            for interface in instance.get('networkInterfaces', []):
                for access_config in interface.get('accessConfigs', []):
                    if 'natIP' in access_config:
                        external_ip = access_config['natIP']
                        break
                if external_ip != "None":
                    break
            
            machine_type = instance.get('machineType', 'Unknown').split('/')[-1]
            
            table.add_row(name, status, zone, external_ip, machine_type)
        
        self.console.print(table)

# Global manager instance
vm_manager = SimplifiedVMManager()

@app.command("list-vms")
def list_vms(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="GCP project ID"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z", help="GCP zone")
):
    """List all VM instances."""
    project_id = project or vm_manager.get_project_id()
    instances = vm_manager.list_instances(project_id, zone)
    vm_manager.display_instances_table(instances, "VM Instances")

@app.command("start-vm")
def start_vm(
    instance_name: str = typer.Argument(..., help="Name of the VM instance to start"),
    zone: str = typer.Option(..., "--zone", "-z", help="GCP zone where the instance is located"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="GCP project ID")
):
    """Start a VM instance."""
    project_id = project or vm_manager.get_project_id()
    success = vm_manager.start_instance(project_id, instance_name, zone)
    
    if success:
        # Get external IP and update SSH config
        external_ip = vm_manager.get_instance_external_ip(project_id, instance_name, zone)
        if external_ip:
            vm_manager.update_ssh_config(instance_name, external_ip)
        else:
            console.print("[yellow]⚠️  Could not get external IP for SSH config update[/yellow]")

@app.command("stop-vm")
def stop_vm(
    instance_name: str = typer.Argument(..., help="Name of the VM instance to stop"),
    zone: str = typer.Option(..., "--zone", "-z", help="GCP zone where the instance is located"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="GCP project ID")
):
    """Stop a VM instance."""
    project_id = project or vm_manager.get_project_id()
    vm_manager.stop_instance(project_id, instance_name, zone)

@app.command("update-ssh-config")
def update_ssh_config(
    instance_name: str = typer.Argument(..., help="Name of the VM instance"),
    zone: str = typer.Option(..., "--zone", "-z", help="GCP zone where the instance is located"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="GCP project ID")
):
    """Update SSH config to match the external IP of a VM instance."""
    project_id = project or vm_manager.get_project_id()
    external_ip = vm_manager.get_instance_external_ip(project_id, instance_name, zone)
    
    if external_ip:
        vm_manager.update_ssh_config(instance_name, external_ip)
    else:
        console.print("[red]❌ Could not get external IP for the instance[/red]")

def main():
    """Main entry point."""
    app()

if __name__ == "__main__":
    main()
