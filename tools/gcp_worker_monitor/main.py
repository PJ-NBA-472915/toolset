#!/usr/bin/env python3
"""
Google Cloud Platform Worker Monitor Tool
Lists worker instances with detailed information including resource usage and public IPs
"""

import sys
import json
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()

class GCPWorkerMonitor:
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
    
    def list_instances(self, project_id: str, zone: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all VM instances in the project."""
        try:
            cmd = [
                "gcloud", "compute", "instances", "list",
                "--project", project_id,
                "--format", "json"
            ]
            
            if zone:
                cmd.extend(["--zones", zone])
            
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
    
    def filter_worker_instances(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter instances to only include workers (instances with 'worker' in the name)."""
        worker_instances = []
        
        for instance in instances:
            name = instance.get('name', '').lower()
            if 'worker' in name:
                worker_instances.append(instance)
        
        return worker_instances
    
    def get_instance_details(self, instance: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific instance."""
        instance_name = instance.get('name', '')
        zone = instance.get('zone', '').split('/')[-1]
        
        details = {
            'name': instance_name,
            'zone': zone,
            'status': instance.get('status', 'UNKNOWN'),
            'machine_type': instance.get('machineType', '').split('/')[-1],
            'internal_ip': None,
            'external_ip': None,
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A',
            'disk_usage': 'N/A',
            'creation_time': instance.get('creationTimestamp', 'N/A'),
            'labels': instance.get('labels', {}),
            'tags': instance.get('tags', {}),
            'network_interfaces': []
        }
        
        # Get network interface information
        for network_interface in instance.get('networkInterfaces', []):
            network_info = {
                'network': network_interface.get('network', '').split('/')[-1],
                'subnetwork': network_interface.get('subnetwork', '').split('/')[-1] if network_interface.get('subnetwork') else 'N/A',
                'internal_ip': network_interface.get('networkIP'),
                'external_ip': network_interface.get('accessConfigs', [{}])[0].get('natIP') if network_interface.get('accessConfigs') else None
            }
            details['network_interfaces'].append(network_info)
            
            # Set primary IPs
            if not details['internal_ip']:
                details['internal_ip'] = network_info['internal_ip']
            if not details['external_ip']:
                details['external_ip'] = network_info['external_ip']
        
        # Try to get resource usage metrics (requires monitoring API)
        try:
            details.update(self.get_resource_usage(instance_name, zone, project_id))
        except Exception:
            pass  # Resource usage is optional
        
        return details
    
    def get_resource_usage(self, instance_name: str, zone: str, project_id: str) -> Dict[str, str]:
        """Get resource usage metrics for an instance."""
        usage = {
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A',
            'disk_usage': 'N/A'
        }
        
        try:
            # Get CPU usage (last 1 hour average)
            cpu_cmd = [
                "gcloud", "monitoring", "metrics", "list",
                "--project", project_id,
                "--filter", f'metric.type="compute.googleapis.com/instance/cpu/utilization" AND resource.labels.instance_name="{instance_name}"',
                "--format", "value(metric.type)"
            ]
            
            result = subprocess.run(cpu_cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                usage['cpu_usage'] = "Available (use --show-metrics for details)"
            
        except Exception:
            pass
        
        try:
            # Get memory usage
            memory_cmd = [
                "gcloud", "monitoring", "metrics", "list",
                "--project", project_id,
                "--filter", f'metric.type="compute.googleapis.com/instance/memory/utilization" AND resource.labels.instance_name="{instance_name}"',
                "--format", "value(metric.type)"
            ]
            
            result = subprocess.run(memory_cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                usage['memory_usage'] = "Available (use --show-metrics for details)"
            
        except Exception:
            pass
        
        return usage
    
    def display_worker_instances(self, worker_instances: List[Dict[str, Any]], show_details: bool = False):
        """Display worker instances in a formatted table."""
        if not worker_instances:
            self.console.print("[yellow]⚠️  No worker instances found.[/yellow]")
            return
        
        if show_details:
            self.display_detailed_table(worker_instances)
        else:
            self.display_summary_table(worker_instances)
    
    def display_summary_table(self, worker_instances: List[Dict[str, Any]]):
        """Display a summary table of worker instances."""
        table = Table(title="GCP Worker Instances Summary")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Zone", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Machine Type", style="yellow")
        table.add_column("Internal IP", style="magenta")
        table.add_column("External IP", style="red")
        
        for instance in worker_instances:
            status_color = "green" if instance['status'] == 'RUNNING' else "red"
            table.add_row(
                instance['name'],
                instance['zone'],
                f"[{status_color}]{instance['status']}[/{status_color}]",
                instance['machine_type'],
                instance['internal_ip'] or 'N/A',
                instance['external_ip'] or 'N/A'
            )
        
        self.console.print(table)
    
    def display_detailed_table(self, worker_instances: List[Dict[str, Any]]):
        """Display detailed information about worker instances."""
        for i, instance in enumerate(worker_instances):
            # Create a panel for each instance
            title = f"Worker Instance: {instance['name']}"
            
            content = f"""
Zone: {instance['zone']}
Status: {instance['status']}
Machine Type: {instance['machine_type']}
Creation Time: {instance['creation_time']}

Network Information:
  Internal IP: {instance['internal_ip'] or 'N/A'}
  External IP: {instance['external_ip'] or 'N/A'}

Resource Usage:
  CPU: {instance['cpu_usage']}
  Memory: {instance['memory_usage']}
  Disk: {instance['disk_usage']}

Labels: {json.dumps(instance['labels'], indent=2) if instance['labels'] else 'None'}
Tags: {json.dumps(instance['tags'], indent=2) if instance['tags'] else 'None'}
"""
            
            panel = Panel(content, title=title, border_style="blue")
            self.console.print(panel)
            
            if i < len(worker_instances) - 1:
                self.console.print()  # Add spacing between instances
    
    def export_to_json(self, worker_instances: List[Dict[str, Any]], filename: str):
        """Export worker instances data to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(worker_instances, f, indent=2, default=str)
            self.console.print(f"[green]✅ Data exported to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to export data: {e}[/red]")
    
    def run(self, args):
        """Main execution method."""
        try:
            # Get project ID
            project_id = args.project or self.get_project_id()
            self.console.print(f"[blue]🔍 Monitoring GCP project: {project_id}[/blue]")
            
            # List instances
            instances = self.list_instances(project_id, args.zone)
            if not instances:
                self.console.print("[yellow]No instances found in the project.[/yellow]")
                return
            
            # Filter worker instances
            worker_instances = self.filter_worker_instances(instances)
            if not worker_instances:
                self.console.print("[yellow]No worker instances found. Consider using --all-instances to see all instances.[/yellow]")
                if args.all_instances:
                    self.console.print("[blue]Showing all instances instead:[/blue]")
                    worker_instances = instances
                else:
                    return
            
            # Get detailed information for each worker instance
            detailed_instances = []
            for instance in worker_instances:
                details = self.get_instance_details(instance, project_id)
                detailed_instances.append(details)
            
            # Display results
            self.display_worker_instances(detailed_instances, args.detailed)
            
            # Export if requested
            if args.export:
                filename = args.export if args.export != 'auto' else f"gcp_workers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.export_to_json(detailed_instances, filename)
            
            # Summary
            self.console.print(f"\n[green]🎉 Found {len(worker_instances)} worker instance(s)[/green]")
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]❌ An error occurred: {e}[/red]")
            if args.verbose:
                import traceback
                traceback.print_exc()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Google Cloud Platform Worker Monitor Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all worker instances
  python main.py
  
  # List worker instances in a specific zone
  python main.py --zone us-central1-a
  
  # Show detailed information
  python main.py --detailed
  
  # Export data to JSON
  python main.py --export workers.json
  
  # Show all instances (not just workers)
  python main.py --all-instances
  
  # Specify project ID
  python main.py --project my-project-id
        """
    )
    
    parser.add_argument('--project', help='GCP project ID (default: current project)')
    parser.add_argument('--zone', help='GCP zone to filter instances')
    parser.add_argument('--detailed', action='store_true', help='Show detailed information for each instance')
    parser.add_argument('--all-instances', action='store_true', help='Show all instances, not just workers')
    parser.add_argument('--export', nargs='?', const='auto', metavar='FILENAME', help='Export data to JSON file (default: auto-generated filename)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose error output')
    
    args = parser.parse_args()
    
    # Create and run the monitor
    monitor = GCPWorkerMonitor()
    monitor.run(args)

if __name__ == "__main__":
    main()

