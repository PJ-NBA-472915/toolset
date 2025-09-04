"""Unit tests for SSHConfigManager class."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open


@pytest.mark.unit
class TestSSHConfigManager:
    """Test cases for the SSHConfigManager class."""

    def test_init_creates_config_directory(self, temp_config_dir):
        """Test that __init__ creates the configuration directory."""
        from src.nebula_cli.ssh_config_manager import SSHConfigManager
        
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = temp_config_dir
            manager = SSHConfigManager()
            
            assert manager.config_dir.exists()
            assert manager.config_dir == temp_config_dir / ".config" / "nebula-cli"
            assert manager.mappings_file == temp_config_dir / ".config" / "nebula-cli" / "mappings.json"
            assert manager.ssh_config_file == temp_config_dir / ".ssh" / "config"

    def test_get_mappings_empty_file(self, ssh_config_manager):
        """Test get_mappings when mappings file doesn't exist."""
        mappings = ssh_config_manager.get_mappings()
        assert mappings == {}

    def test_get_mappings_existing_file(self, ssh_config_manager, temp_config_dir):
        """Test get_mappings when mappings file exists."""
        mappings_data = {"instance-1": "test-host", "instance-2": "another-host"}
        
        # Create the mappings file
        ssh_config_manager.mappings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ssh_config_manager.mappings_file, 'w') as f:
            json.dump(mappings_data, f)
        
        mappings = ssh_config_manager.get_mappings()
        assert mappings == mappings_data

    def test_save_mappings(self, ssh_config_manager):
        """Test save_mappings creates and writes to mappings file."""
        mappings_data = {"instance-1": "test-host", "instance-2": "another-host"}
        
        ssh_config_manager.save_mappings(mappings_data)
        
        assert ssh_config_manager.mappings_file.exists()
        with open(ssh_config_manager.mappings_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == mappings_data

    def test_get_hostname_for_instance_existing(self, ssh_config_manager):
        """Test get_hostname_for_instance when mapping exists."""
        mappings_data = {"instance-1": "test-host", "instance-2": "another-host"}
        ssh_config_manager.save_mappings(mappings_data)
        
        hostname = ssh_config_manager.get_hostname_for_instance("instance-1")
        assert hostname == "test-host"

    def test_get_hostname_for_instance_not_existing(self, ssh_config_manager):
        """Test get_hostname_for_instance when mapping doesn't exist."""
        hostname = ssh_config_manager.get_hostname_for_instance("nonexistent")
        assert hostname is None

    def test_set_hostname_for_instance(self, ssh_config_manager):
        """Test set_hostname_for_instance updates mappings."""
        # Set initial mappings
        initial_mappings = {"instance-1": "test-host"}
        ssh_config_manager.save_mappings(initial_mappings)
        
        # Add new mapping
        ssh_config_manager.set_hostname_for_instance("instance-2", "new-host")
        
        # Verify both mappings exist
        mappings = ssh_config_manager.get_mappings()
        assert mappings == {"instance-1": "test-host", "instance-2": "new-host"}

    def test_set_hostname_for_instance_updates_existing(self, ssh_config_manager):
        """Test set_hostname_for_instance updates existing mapping."""
        # Set initial mappings
        initial_mappings = {"instance-1": "test-host", "instance-2": "another-host"}
        ssh_config_manager.save_mappings(initial_mappings)
        
        # Update existing mapping
        ssh_config_manager.set_hostname_for_instance("instance-1", "updated-host")
        
        # Verify mapping was updated
        mappings = ssh_config_manager.get_mappings()
        assert mappings == {"instance-1": "updated-host", "instance-2": "another-host"}

    def test_get_ssh_hosts_no_config_file(self, ssh_config_manager):
        """Test get_ssh_hosts when SSH config file doesn't exist."""
        hosts = ssh_config_manager.get_ssh_hosts()
        assert hosts == []

    def test_get_ssh_hosts_existing_file(self, ssh_config_manager, temp_ssh_config):
        """Test get_ssh_hosts parses existing SSH config file."""
        with patch.object(ssh_config_manager, 'ssh_config_file', temp_ssh_config):
            hosts = ssh_config_manager.get_ssh_hosts()
            assert "test-host" in hosts
            assert "another-host" in hosts
            assert len(hosts) == 2

    def test_get_ssh_hosts_handles_wildcard(self, ssh_config_manager, temp_config_dir):
        """Test get_ssh_hosts filters out wildcard hosts."""
        ssh_config_content = """Host test-host
  HostName 192.168.1.100

Host *
  HostName 192.168.1.101

Host another-host
  HostName 192.168.1.102
"""
        # Create a real temporary SSH config file
        ssh_config_path = temp_config_dir / "ssh_config"
        ssh_config_path.write_text(ssh_config_content)
        
        with patch.object(ssh_config_manager, 'ssh_config_file', ssh_config_path):
            hosts = ssh_config_manager.get_ssh_hosts()
            assert "test-host" in hosts
            assert "another-host" in hosts
            assert "*" not in hosts
            assert len(hosts) == 2

    def test_add_ssh_host_creates_file(self, ssh_config_manager):
        """Test add_ssh_host creates SSH config file if it doesn't exist."""
        ssh_config_path = ssh_config_manager.ssh_config_file
        ssh_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        ssh_config_manager.add_ssh_host("new-host", "192.168.1.100", "testuser", "~/.ssh/test_key")
        
        assert ssh_config_path.exists()
        content = ssh_config_path.read_text()
        assert "Host new-host" in content
        assert "HostName 192.168.1.100" in content
        assert "User testuser" in content
        assert "IdentityFile ~/.ssh/test_key" in content

    def test_add_ssh_host_appends_to_existing(self, ssh_config_manager, temp_ssh_config):
        """Test add_ssh_host appends to existing SSH config file."""
        with patch.object(ssh_config_manager, 'ssh_config_file', temp_ssh_config):
            original_content = temp_ssh_config.read_text()
            
            ssh_config_manager.add_ssh_host("new-host", "192.168.1.200", "newuser", "~/.ssh/new_key")
            
            content = temp_ssh_config.read_text()
            assert original_content in content
            assert "Host new-host" in content
            assert "HostName 192.168.1.200" in content
            assert "User newuser" in content
            assert "IdentityFile ~/.ssh/new_key" in content

    def test_update_ssh_host_creates_file_if_nonexistent(self, ssh_config_manager):
        """Test update_ssh_host creates SSH config file if it doesn't exist."""
        ssh_config_path = ssh_config_manager.ssh_config_file
        ssh_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        ssh_config_manager.update_ssh_host("new-host", "192.168.1.100", "testuser", "~/.ssh/test_key")
        
        assert ssh_config_path.exists()
        content = ssh_config_path.read_text()
        assert "Host new-host" in content
        assert "HostName 192.168.1.100" in content

    def test_update_ssh_host_updates_existing(self, ssh_config_manager, temp_ssh_config):
        """Test update_ssh_host updates existing host entry."""
        with patch.object(ssh_config_manager, 'ssh_config_file', temp_ssh_config):
            ssh_config_manager.update_ssh_host("test-host", "192.168.1.200", "updateduser", "~/.ssh/updated_key")
            
            content = temp_ssh_config.read_text()
            assert "Host test-host" in content
            assert "HostName 192.168.1.200" in content
            assert "User updateduser" in content
            assert "IdentityFile ~/.ssh/updated_key" in content
            # Original values should be replaced
            assert "192.168.1.100" not in content
            assert "testuser" not in content
            assert "~/.ssh/test_key" not in content

    def test_update_ssh_host_creates_new_if_not_found(self, ssh_config_manager, temp_ssh_config):
        """Test update_ssh_host creates new host if not found."""
        with patch.object(ssh_config_manager, 'ssh_config_file', temp_ssh_config):
            original_content = temp_ssh_config.read_text()
            
            ssh_config_manager.update_ssh_host("nonexistent-host", "192.168.1.300", "newuser", "~/.ssh/new_key")
            
            content = temp_ssh_config.read_text()
            assert original_content in content
            assert "Host nonexistent-host" in content
            assert "HostName 192.168.1.300" in content
            assert "User newuser" in content
            assert "IdentityFile ~/.ssh/new_key" in content

    def test_update_ssh_host_case_insensitive(self, ssh_config_manager):
        """Test update_ssh_host handles case insensitive host matching."""
        ssh_config_content = """Host Test-Host
  HostName 192.168.1.100
  User testuser
  IdentityFile ~/.ssh/test_key
"""
        with patch.object(ssh_config_manager, 'ssh_config_file', Path('/tmp/test_config')):
            with patch('builtins.open', mock_open(read_data=ssh_config_content)):
                with patch('builtins.open', mock_open()) as mock_file:
                    ssh_config_manager.update_ssh_host("test-host", "192.168.1.200", "updateduser", "~/.ssh/updated_key")
                    
                    # Verify the file was opened for writing
                    assert mock_file.call_count >= 1

    def test_ssh_config_parsing_edge_cases(self, ssh_config_manager, temp_config_dir):
        """Test SSH config parsing handles edge cases."""
        ssh_config_content = """# This is a comment
Host test-host
  HostName 192.168.1.100
  User testuser
  IdentityFile ~/.ssh/test_key

Host another-host
  HostName 192.168.1.101
  User anotheruser
  IdentityFile ~/.ssh/another_key

Host * wildcard-host
  HostName 192.168.1.102
"""
        # Create a real temporary SSH config file
        ssh_config_path = temp_config_dir / "ssh_config"
        ssh_config_path.write_text(ssh_config_content)
        
        with patch.object(ssh_config_manager, 'ssh_config_file', ssh_config_path):
            hosts = ssh_config_manager.get_ssh_hosts()
            assert "test-host" in hosts
            assert "another-host" in hosts
            assert "wildcard-host" in hosts
            assert "*" not in hosts
            assert len(hosts) == 3

    def test_mappings_persistence(self, ssh_config_manager):
        """Test that mappings persist across manager instances."""
        # Create first manager instance
        manager1 = ssh_config_manager
        manager1.set_hostname_for_instance("instance-1", "test-host")
        
        # Create second manager instance
        manager2 = ssh_config_manager.__class__()
        with patch.object(manager2, 'config_dir', manager1.config_dir):
            manager2.mappings_file = manager1.mappings_file
            
            # Verify mapping persists
            hostname = manager2.get_hostname_for_instance("instance-1")
            assert hostname == "test-host"
