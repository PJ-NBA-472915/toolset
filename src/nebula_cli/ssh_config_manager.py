import json
import os
from pathlib import Path

class SSHConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "nebula-cli"
        self.mappings_file = self.config_dir / "mappings.json"
        self.ssh_config_file = Path.home() / ".ssh" / "config"
        self._ensure_config_dir_exists()

    def _ensure_config_dir_exists(self):
        """Ensures the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_mappings(self):
        """Reads the instance ID to hostname mappings."""
        if not self.mappings_file.exists():
            return {}
        with open(self.mappings_file, "r") as f:
            return json.load(f)

    def save_mappings(self, mappings):
        """Saves the instance ID to hostname mappings."""
        with open(self.mappings_file, "w") as f:
            json.dump(mappings, f, indent=2)

    def get_hostname_for_instance(self, instance_id):
        """Gets the hostname for a given instance ID."""
        mappings = self.get_mappings()
        return mappings.get(instance_id)

    def set_hostname_for_instance(self, instance_id, hostname):
        """Sets the hostname for a given instance ID."""
        mappings = self.get_mappings()
        mappings[instance_id] = hostname
        self.save_mappings(mappings)

    def get_ssh_hosts(self):
        """Parses the SSH config file and returns a list of hosts."""
        if not self.ssh_config_file.exists():
            return []
        
        hosts = []
        with open(self.ssh_config_file, "r") as f:
            for line in f:
                if line.strip().lower().startswith("host "):
                    parts = line.strip().split()
                    if len(parts) > 1:
                        hosts.extend(p for p in parts[1:] if p != "*")
        return hosts

    def update_ssh_host(self, host, hostname, user, key_path):
        """Updates an existing host in the SSH config file."""
        if not self.ssh_config_file.exists():
            self.add_ssh_host(host, hostname, user, key_path)
            return

        with open(self.ssh_config_file, "r") as f:
            lines = f.readlines()

        new_lines = []
        in_host_block = False
        host_found = False
        for line in lines:
            if line.strip().lower().startswith(f"host {host.lower()}"):
                in_host_block = True
                host_found = True
                new_lines.append(line)
            elif in_host_block and line.strip().lower().startswith("host "):
                in_host_block = False
                new_lines.append(line)
            elif in_host_block:
                if "hostname" in line.lower():
                    new_lines.append(f"  HostName {hostname}\n")
                elif "user" in line.lower():
                    new_lines.append(f"  User {user}\n")
                elif "identityfile" in line.lower():
                    new_lines.append(f"  IdentityFile {key_path}\n")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if not host_found:
            self.add_ssh_host(host, hostname, user, key_path)
            return

        with open(self.ssh_config_file, "w") as f:
            f.writelines(new_lines)

    def add_ssh_host(self, host, hostname, user, key_path):
        """Adds a new host to the SSH config file."""
        with open(self.ssh_config_file, "a") as f:
            f.write(f"\nHost {host}\n")
            f.write(f"  HostName {hostname}\n")
            f.write(f"  User {user}\n")
            f.write(f"  IdentityFile {key_path}\n")
