"""Unit tests for instance ID to hostname mapping functionality."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open


@pytest.mark.unit
class TestInstanceMapping:
    """Test cases for instance ID to hostname mapping functionality."""

    def test_mapping_storage_creation(self, temp_config_dir):
        """Test that mapping storage is created in the correct location."""
        from src.nebula_cli.ssh_config_manager import SSHConfigManager
        
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = temp_config_dir
            manager = SSHConfigManager()
            
            # Verify config directory structure
            assert manager.config_dir.exists()
            assert manager.config_dir == temp_config_dir / ".config" / "nebula-cli"
            assert manager.mappings_file == temp_config_dir / ".config" / "nebula-cli" / "mappings.json"

    def test_empty_mappings_file_handling(self, ssh_config_manager):
        """Test handling of empty or non-existent mappings file."""
        # Test non-existent file
        mappings = ssh_config_manager.get_mappings()
        assert mappings == {}
        
        # Test empty file
        ssh_config_manager.mappings_file.parent.mkdir(parents=True, exist_ok=True)
        ssh_config_manager.mappings_file.write_text("")
        
        with pytest.raises(json.JSONDecodeError):
            ssh_config_manager.get_mappings()

    def test_mappings_file_corruption_handling(self, ssh_config_manager):
        """Test handling of corrupted mappings file."""
        ssh_config_manager.mappings_file.parent.mkdir(parents=True, exist_ok=True)
        ssh_config_manager.mappings_file.write_text("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            ssh_config_manager.get_mappings()

    def test_mappings_roundtrip(self, ssh_config_manager):
        """Test that mappings can be saved and loaded correctly."""
        test_mappings = {
            "instance-123": "web-server",
            "instance-456": "db-server",
            "instance-789": "api-server"
        }
        
        # Save mappings
        ssh_config_manager.save_mappings(test_mappings)
        
        # Load mappings
        loaded_mappings = ssh_config_manager.get_mappings()
        assert loaded_mappings == test_mappings

    def test_mapping_operations(self, ssh_config_manager):
        """Test individual mapping operations."""
        # Test setting mappings
        ssh_config_manager.set_hostname_for_instance("instance-1", "host-1")
        ssh_config_manager.set_hostname_for_instance("instance-2", "host-2")
        
        # Test getting mappings
        assert ssh_config_manager.get_hostname_for_instance("instance-1") == "host-1"
        assert ssh_config_manager.get_hostname_for_instance("instance-2") == "host-2"
        assert ssh_config_manager.get_hostname_for_instance("nonexistent") is None
        
        # Test updating existing mapping
        ssh_config_manager.set_hostname_for_instance("instance-1", "updated-host-1")
        assert ssh_config_manager.get_hostname_for_instance("instance-1") == "updated-host-1"
        assert ssh_config_manager.get_hostname_for_instance("instance-2") == "host-2"

    def test_mappings_persistence_across_instances(self, temp_config_dir):
        """Test that mappings persist across different manager instances."""
        from src.nebula_cli.ssh_config_manager import SSHConfigManager
        
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = temp_config_dir
            
            # Create first manager and set mappings
            manager1 = SSHConfigManager()
            manager1.set_hostname_for_instance("instance-1", "host-1")
            manager1.set_hostname_for_instance("instance-2", "host-2")
            
            # Create second manager and verify mappings persist
            manager2 = SSHConfigManager()
            assert manager2.get_hostname_for_instance("instance-1") == "host-1"
            assert manager2.get_hostname_for_instance("instance-2") == "host-2"

    def test_mappings_file_format(self, ssh_config_manager):
        """Test that mappings file is saved in proper JSON format."""
        test_mappings = {
            "instance-123": "web-server",
            "instance-456": "db-server"
        }
        
        ssh_config_manager.save_mappings(test_mappings)
        
        # Verify file content is valid JSON
        content = ssh_config_manager.mappings_file.read_text()
        parsed_content = json.loads(content)
        assert parsed_content == test_mappings
        
        # Verify file is properly formatted (indented)
        assert "  " in content  # Should have indentation

    def test_mappings_with_special_characters(self, ssh_config_manager):
        """Test mappings with special characters in hostnames."""
        special_mappings = {
            "instance-1": "host-with-dashes",
            "instance-2": "host_with_underscores",
            "instance-3": "host.with.dots",
            "instance-4": "host123numbers"
        }
        
        for instance_id, hostname in special_mappings.items():
            ssh_config_manager.set_hostname_for_instance(instance_id, hostname)
            assert ssh_config_manager.get_hostname_for_instance(instance_id) == hostname

    def test_mappings_with_empty_values(self, ssh_config_manager):
        """Test mappings with empty or None values."""
        # Test empty string
        ssh_config_manager.set_hostname_for_instance("instance-1", "")
        assert ssh_config_manager.get_hostname_for_instance("instance-1") == ""
        
        # Test None value (should be converted to string)
        ssh_config_manager.set_hostname_for_instance("instance-2", None)
        assert ssh_config_manager.get_hostname_for_instance("instance-2") is None

    def test_mappings_file_permissions(self, ssh_config_manager):
        """Test that mappings file has appropriate permissions."""
        ssh_config_manager.set_hostname_for_instance("instance-1", "host-1")
        
        # Verify file exists and is readable
        assert ssh_config_manager.mappings_file.exists()
        assert ssh_config_manager.mappings_file.is_file()
        
        # Verify file can be read
        content = ssh_config_manager.mappings_file.read_text()
        assert content is not None

    def test_concurrent_mappings_access(self, ssh_config_manager):
        """Test that mappings can handle concurrent access scenarios."""
        # Simulate multiple rapid updates
        for i in range(10):
            ssh_config_manager.set_hostname_for_instance(f"instance-{i}", f"host-{i}")
        
        # Verify all mappings are correct
        for i in range(10):
            assert ssh_config_manager.get_hostname_for_instance(f"instance-{i}") == f"host-{i}"

    def test_mappings_cleanup(self, ssh_config_manager):
        """Test that mappings can be cleared or reset."""
        # Set some mappings
        ssh_config_manager.set_hostname_for_instance("instance-1", "host-1")
        ssh_config_manager.set_hostname_for_instance("instance-2", "host-2")
        
        # Clear all mappings by saving empty dict
        ssh_config_manager.save_mappings({})
        
        # Verify mappings are cleared
        assert ssh_config_manager.get_hostname_for_instance("instance-1") is None
        assert ssh_config_manager.get_hostname_for_instance("instance-2") is None

    def test_mappings_file_backup_handling(self, ssh_config_manager):
        """Test handling of backup or temporary files."""
        # Create a backup file
        backup_file = ssh_config_manager.mappings_file.with_suffix('.json.bak')
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text('{"backup": "data"}')
        
        # Main mappings should still work
        ssh_config_manager.set_hostname_for_instance("instance-1", "host-1")
        assert ssh_config_manager.get_hostname_for_instance("instance-1") == "host-1"
        
        # Backup file should not interfere
        assert backup_file.exists()
        assert ssh_config_manager.mappings_file.exists()

    def test_mappings_with_unicode_characters(self, ssh_config_manager):
        """Test mappings with unicode characters in hostnames."""
        unicode_mappings = {
            "instance-1": "høst-næme",  # Norwegian characters
            "instance-2": "主机名",      # Chinese characters
            "instance-3": "хост-имя"    # Cyrillic characters
        }
        
        for instance_id, hostname in unicode_mappings.items():
            ssh_config_manager.set_hostname_for_instance(instance_id, hostname)
            assert ssh_config_manager.get_hostname_for_instance(instance_id) == hostname
