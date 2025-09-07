#!/usr/bin/env python3
"""
Service for managing SSH configurations
"""

import logging
from .ssh_config_manager import SSHConfigManager
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SSHConfigService:
    """Manages SSH configuration logic"""

    def __init__(self):
        self.ssh_config_manager = SSHConfigManager()

    def get_all_hosts(self):
        """Get all SSH hosts."""
        return self.ssh_config_manager.get_ssh_hosts()

    def add_host(self, host: str, hostname: str, user: str, key_path: str):
        """Add a new SSH host."""
        # Basic validation
        if not all([host, hostname, user, key_path]):
            raise HTTPException(status_code=400, detail="All fields are required")
        
        self.ssh_config_manager.add_ssh_host(host, hostname, user, key_path)
        return {"status": "success", "message": f"Host '{host}' added successfully."}

    def update_host(self, host: str, hostname: str, user: str, key_path: str):
        """Update an existing SSH host."""
        # Basic validation
        if not all([host, hostname, user, key_path]):
            raise HTTPException(status_code=400, detail="All fields are required")

        self.ssh_config_manager.update_ssh_host(host, hostname, user, key_path)
        return {"status": "success", "message": f"Host '{host}' updated successfully."}
