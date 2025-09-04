"""Shared fixtures and configuration for all tests."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_ssh_config():
    """Create a temporary SSH config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as f:
        f.write("""Host test-host
  HostName 192.168.1.100
  User testuser
  IdentityFile ~/.ssh/test_key

Host another-host
  HostName 192.168.1.101
  User anotheruser
  IdentityFile ~/.ssh/another_key
""")
        temp_file = Path(f.name)
    
    yield temp_file
    
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def mock_home_dir(temp_config_dir):
    """Mock the home directory to use a temporary directory."""
    with patch('pathlib.Path.home') as mock_home:
        mock_home.return_value = temp_config_dir
        yield temp_config_dir


@pytest.fixture
def ssh_config_manager(mock_home_dir):
    """Create an SSHConfigManager instance with mocked home directory."""
    from src.nebula_cli.ssh_config_manager import SSHConfigManager
    return SSHConfigManager()
